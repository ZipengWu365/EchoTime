"""Explicitly approximate candidate selection for exact reranking.

Inputs are already oriented as (time, channels).  Every representation uses
the complete time range; spectra and event extrema also inspect every retained
observation.  These descriptors are not lower bounds on elastic distances and
provide no recall guarantee.  A caller must evaluate retrieval recall against
an exhaustive reference on its own data.

Feature construction is cached lazily.  Multiview and binary selection still
scan the corpus; they are not sublinear indexes.  Optional ``faiss`` uses
IndexFlatL2 over float32 features; ``faiss_hnsw`` adds approximate graph
traversal with IndexHNSWFlat.  The official API is documented at
https://github.com/facebookresearch/faiss/wiki/Getting-started .  Flat vector
search is exhaustive, but both candidate sets approximate the target metric.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import importlib
from operator import index
from time import perf_counter
from typing import Any

import numpy as np


_STRATEGIES = {"multiview", "pyramid", "binary", "faiss", "faiss_hnsw"}
_MULTIVIEW = ("level", "events", "diff", "spectrum", "trend")
_FEATURE_CLIP = 1e6
_INPUT_CLIP = 1e12
_POPCOUNT = np.array([i.bit_count() for i in range(256)], dtype=np.uint8)


def _integer(name: str, value: Any, minimum: int) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be an integer >= {minimum}.")
    try:
        result = index(value)
    except TypeError:
        raise ValueError(f"{name} must be an integer >= {minimum}.") from None
    if result < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}.")
    return result


def _snapshot(values: Any) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.ndim != 2:
        raise ValueError("candidate series must be 1-D or already oriented (time, channels) arrays.")
    # Never apply the legacy short/wide transpose heuristic a second time.
    arr = np.array(arr[np.all(np.isfinite(arr), axis=1)], order="C", copy=True)
    arr.setflags(write=False)
    return arr


def _row_mean(values: np.ndarray) -> np.ndarray:
    # A mean of finite, near-maximum doubles need not overflow its sum.
    scale = np.max(np.abs(values), axis=1, keepdims=True)
    scale = np.where(scale > 0, scale, 1.0)
    return np.mean(values / scale, axis=1, keepdims=True) * scale


def _resample(values: np.ndarray, points: int, channels: int) -> np.ndarray:
    if not len(values):
        return np.zeros((points, channels), dtype=np.float64)
    if len(values) == points:
        return values.copy()
    old = np.arange(len(values), dtype=np.float64)
    grid = np.linspace(0.0, len(values) - 1, points)
    return np.column_stack([np.interp(grid, old, values[:, c]) for c in range(channels)])


def _paa(values: np.ndarray, points: int) -> np.ndarray:
    if points == len(values):
        return values.copy()
    return np.stack([np.mean(block, axis=0) for block in np.array_split(values, points)], axis=0)


def _finite_clip(values: np.ndarray, limit: float) -> np.ndarray:
    return np.clip(np.nan_to_num(values, nan=0.0, posinf=limit, neginf=-limit), -limit, limit)


def _smallest(scores: np.ndarray, count: int, ids: np.ndarray | None = None) -> np.ndarray:
    """Partial selection with deterministic corpus-ID tie breaking."""
    if ids is None:
        ids = np.arange(len(scores), dtype=np.int64)
    count = min(count, len(ids))
    if count <= 0:
        return np.empty(0, dtype=np.int64)
    local = scores[ids]
    if count < len(ids):
        boundary = np.partition(local, count - 1)[count - 1]
        below = ids[local < boundary]
        tied = np.sort(ids[local == boundary])[: count - len(below)]
        ids = np.concatenate((below, tied))
    return ids[np.lexsort((ids, scores[ids]))].astype(np.int64, copy=False)


@dataclass
class _Feature:
    matrix: np.ndarray
    mean: np.ndarray
    scale: np.ndarray


@dataclass
class _Cache:
    channels: int
    value_scale: np.ndarray
    samples: np.ndarray
    valid: np.ndarray
    features: dict[str, _Feature] = field(default_factory=dict)
    binary: tuple[np.ndarray, np.ndarray] | None = None
    faiss: dict[str, tuple[Any, np.ndarray]] = field(default_factory=dict)


class CandidateEngine:
    """Select a bounded candidate set; all returned IDs index the input corpus.

    ``multiview`` reserves quotas for level, event, first-difference, derivative
    spectrum, and coarse-trend features, then fills duplicate quota slots using
    their mean standardized squared distance.  At least five slots are needed
    to give every view a nonzero quota.

    ``pyramid`` narrows 16/32/64/128-point representations (up to ``n_points``),
    while reserving event and high-frequency spectrum slots from the full
    corpus.  ``binary`` uses 128 seeded random hyperplanes over the entire
    standardized level representation, packed into 16 bytes per series.

    ``faiss`` is a flat vector-search baseline.  ``faiss_hnsw`` uses M=32,
    efConstruction=80, and per-query efSearch=max(64, budget).  HNSW can omit
    vector neighbors as well as target-metric neighbors.  Its graph receives
    an explicit seed, but parallel graph construction need not reproduce the
    same graph across rebuilds.  Ties are stable within the retrieved subset.

    Channels are retained when corpus and query dimensions agree.  Otherwise
    candidate features use per-time channel means.  This aggregation, index
    time resampling, feature standardization, numerical clipping, and candidate
    truncation are approximation layers, not changes to the final metric.
    Timestamps and application-specific channel weights are not used here.

    Inputs are copied on construction.  Subsequent caller mutation cannot
    invalidate cached features.  The arrays passed here must already have the
    intended orientation; no automatic transpose is performed.
    """

    def __init__(self, series: Sequence[np.ndarray], *, n_points: int = 128, seed: int = 0):
        self.n_points = _integer("n_points", n_points, 8)
        self.seed = _integer("seed", seed, 0)
        self._series = tuple(_snapshot(item) for item in series)
        dimensions = {a.shape[1] for a in self._series if len(a) and a.shape[1]}
        self._mixed = len(dimensions) > 1
        self._channels = next(iter(dimensions)) if len(dimensions) == 1 else 1
        self._caches: dict[str, _Cache] = {}

    def _values(self, values: np.ndarray, mode: str) -> np.ndarray:
        if not len(values) or not values.shape[1]:
            return np.empty((0, 1 if mode == "mean" else self._channels))
        return _row_mean(values) if mode == "mean" and values.shape[1] != 1 else values

    def _scaled(self, values: np.ndarray, mode: str, cache: _Cache) -> np.ndarray:
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            return _finite_clip(self._values(values, mode) / cache.value_scale, _INPUT_CLIP)

    def _cache(self, mode: str) -> _Cache:
        if mode in self._caches:
            return self._caches[mode]
        channels = 1 if mode == "mean" else self._channels
        scale = np.zeros(channels, dtype=np.float64)
        valid = np.array([bool(len(a) and a.shape[1]) for a in self._series], dtype=bool)
        for item in self._series:
            values = self._values(item, mode)
            if len(values):
                scale = np.maximum(scale, np.max(np.abs(values), axis=0))
        scale = np.where(scale > 0, scale, 1.0)
        cache = _Cache(channels, scale, np.empty((len(self._series), self.n_points, channels)), valid)
        for i, item in enumerate(self._series):
            cache.samples[i] = _resample(self._scaled(item, mode, cache), self.n_points, channels)
        for array in (cache.value_scale, cache.samples, cache.valid):
            array.setflags(write=False)
        self._caches[mode] = cache
        return cache

    def _raw_feature(self, name: str, sampled: np.ndarray, full: np.ndarray | None) -> np.ndarray:
        if name == "level":
            return sampled.reshape(-1)
        if name == "diff":
            return np.diff(sampled, axis=0).reshape(-1)
        if name.startswith("paa"):
            return _paa(sampled, int(name[3:])).reshape(-1)
        if name == "trend":
            t = np.linspace(-0.5, 0.5, len(sampled))
            slope = (t @ sampled) / float(t @ t)
            return np.concatenate((_paa(sampled, min(16, self.n_points)).reshape(-1), slope))
        assert full is not None
        if name == "spectrum":
            points = max(8, self.n_points // 2 + 1)
            if len(full) < 2:
                return np.zeros(points * sampled.shape[1])
            differences = np.diff(full, axis=0)
            amplitude = np.abs(np.fft.rfft(differences, axis=0)) / len(differences)
            frequencies = np.fft.rfftfreq(len(differences))
            grid = np.linspace(0.0, 0.5, points)
            return np.column_stack([
                np.interp(grid, frequencies, amplitude[:, c], right=0.0)
                for c in range(sampled.shape[1])
            ]).reshape(-1)
        if name == "events":
            bins = min(16, self.n_points)
            channels = sampled.shape[1]
            if not len(full):
                return np.zeros((3 * bins + 2) * channels)
            edges = np.linspace(0, len(full), bins + 1, dtype=int)
            minima, maxima, jumps = [], [], []
            differences = np.abs(np.diff(full, axis=0, prepend=full[:1]))
            for lo, hi in zip(edges[:-1], edges[1:]):
                if lo == hi:
                    lo, hi = min(lo, len(full) - 1), min(lo, len(full) - 1) + 1
                minima.append(np.min(full[lo:hi], axis=0))
                maxima.append(np.max(full[lo:hi], axis=0))
                jumps.append(np.max(differences[lo:hi], axis=0))
            positions = np.concatenate((np.argmin(full, axis=0), np.argmax(full, axis=0))) / max(1, len(full) - 1)
            return np.concatenate((np.asarray(minima).reshape(-1), np.asarray(maxima).reshape(-1), np.asarray(jumps).reshape(-1), positions))
        raise ValueError(f"unknown candidate view: {name}")

    def _feature(self, name: str, mode: str, cache: _Cache) -> _Feature:
        if name in cache.features:
            return cache.features[name]
        if name == "level":
            raw = cache.samples.reshape(len(self._series), -1)
        elif name == "diff":
            raw = np.diff(cache.samples, axis=1).reshape(len(self._series), -1)
        else:
            raw = np.stack([
                self._raw_feature(name, cache.samples[i], self._scaled(item, mode, cache) if name in {"spectrum", "events"} else None)
                for i, item in enumerate(self._series)
            ])
        if np.any(cache.valid):
            mean = np.mean(raw[cache.valid], axis=0)
            scale = np.std(raw[cache.valid], axis=0)
            scale = np.where(scale > 0.0, scale, 1.0)
        else:
            mean, scale = np.zeros(raw.shape[1]), np.ones(raw.shape[1])
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            matrix = _finite_clip((raw - mean) / scale, _FEATURE_CLIP)
        for array in (matrix, mean, scale):
            array.setflags(write=False)
        feature = _Feature(matrix, mean, scale)
        cache.features[name] = feature
        return feature

    def _distance(self, feature: _Feature, query: np.ndarray, valid: np.ndarray, ids: np.ndarray | None = None) -> np.ndarray:
        selected = feature.matrix if ids is None else feature.matrix[ids]
        difference = selected - query
        values = np.mean(difference * difference, axis=1)
        values[~(valid if ids is None else valid[ids])] = np.inf
        if ids is None:
            return values
        scores = np.full(len(valid), np.inf)
        scores[ids] = values
        return scores

    @staticmethod
    def _union_fill(groups: Sequence[np.ndarray], scores: np.ndarray, budget: int) -> np.ndarray:
        chosen: dict[int, None] = {}
        for group in groups:
            for item in group:
                chosen.setdefault(int(item), None)
        for item in _smallest(scores, budget):
            if len(chosen) >= budget:
                break
            chosen.setdefault(int(item), None)
        ids = np.fromiter(chosen, dtype=np.int64)
        return ids[np.lexsort((ids, scores[ids]))][:budget]

    def select(self, query: np.ndarray, budget: int, strategy: str = "multiview") -> tuple[np.ndarray, dict[str, Any]]:
        """Return exactly ``min(budget, corpus_size)`` distinct corpus IDs.

        Invalid/empty corpus entries are ranked after valid ones and remain
        available for deterministic filling if the budget requires them.  The
        caller's exact reranker decides whether they yield a defined distance.
        Timing separates feature/index preparation from candidate ranking;
        no recall estimate is inferred from these timings or representations.
        HNSW retrieval depends on the built graph; the other strategies also
        reproduce their selection after rebuilding with the same inputs.
        """
        started = perf_counter()
        budget = _integer("budget", budget, 0)
        if strategy not in _STRATEGIES:
            raise ValueError(f"strategy must be one of {sorted(_STRATEGIES)}.")
        faiss = None
        if strategy in {"faiss", "faiss_hnsw"}:
            try:
                faiss = importlib.import_module("faiss")
            except ImportError:
                raise ImportError(f"strategy={strategy!r} requires the optional FAISS package; the core installation does not include it.") from None
        values = _snapshot(query)
        count = len(self._series)
        budget = min(budget, count)
        stats: dict[str, Any] = {
            "strategy": strategy, "candidate_count": budget,
            "corpus_size": count, "candidate_prep_seconds": 0.0,
            "candidate_ranking_seconds": 0.0, "approximation_layers": [],
        }
        if faiss is not None:
            # Report FAISS's own configuration; EchoTime n_jobs does not set
            # this process-global OpenMP limit or imply active thread usage.
            stats["faiss_omp_max_threads"] = int(faiss.omp_get_max_threads())
            stats["faiss_version"] = str(getattr(faiss, "__version__", "unknown"))
        if budget == 0 or budget == count:
            stats["candidate_prep_seconds"] = perf_counter() - started
            stats["exhaustive_candidates"] = budget == count
            return np.arange(budget, dtype=np.int64), stats

        mode = "mean" if self._mixed or values.shape[1] != self._channels else "channels"
        cache = self._cache(mode)
        stats["feature_channels"] = cache.channels
        stats["invalid_series"] = int(np.sum(~cache.valid))
        layers = ["full_span_index_time_resampling", "corpus_feature_standardization_and_clipping", "candidate_budget"]
        if mode == "mean":
            layers.append("channel_mean_aggregation")
        levels = sorted({n for n in (16, 32, 64, 128, self.n_points) if n <= self.n_points})
        if strategy == "multiview":
            names = list(_MULTIVIEW)
            layers.extend(("derivative_spectrum_without_phase", "multiview_quota_union"))
        elif strategy == "pyramid":
            names = [f"paa{n}" for n in levels] + ["events", "spectrum"]
            layers.extend(("coarse_to_fine_candidate_narrowing", "event_and_spectrum_protection"))
        else:
            names = ["level"]
        stats["feature_cache_hits"] = sum(name in cache.features for name in names)
        stats["feature_cache_misses"] = len(names) - stats["feature_cache_hits"]
        full = self._scaled(values, mode, cache)
        sampled = _resample(full, self.n_points, cache.channels)
        features = {name: self._feature(name, mode, cache) for name in names}
        queries: dict[str, np.ndarray] = {}
        for name, feature in features.items():
            raw = self._raw_feature(name, sampled, full if name in {"spectrum", "events"} else None)
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                queries[name] = _finite_clip((raw - feature.mean) / feature.scale, _FEATURE_CLIP)
        if strategy == "binary":
            if cache.binary is None:
                projection = np.random.default_rng(self.seed).standard_normal((features["level"].matrix.shape[1], 128), dtype=np.float32)
                codes = np.packbits(features["level"].matrix.astype(np.float32) @ projection >= 0, axis=1, bitorder="little")
                projection.setflags(write=False)
                codes.setflags(write=False)
                cache.binary = (projection, codes)
            projection, codes = cache.binary
            query_code = np.packbits(queries["level"].astype(np.float32) @ projection >= 0, bitorder="little")
            layers.extend(("float32_random_projection", "128_bit_sign_hash"))
        elif strategy in {"faiss", "faiss_hnsw"}:
            if strategy not in cache.faiss:
                valid_ids = np.flatnonzero(cache.valid).astype(np.int64)
                dimension = features["level"].matrix.shape[1]
                if strategy == "faiss_hnsw":
                    faiss_index = faiss.IndexHNSWFlat(dimension, 32, faiss.METRIC_L2)
                    faiss_index.hnsw.efConstruction = 80
                    faiss_index.hnsw.rng = faiss.RandomGenerator(self.seed % (2**63))
                else:
                    faiss_index = faiss.IndexFlatL2(dimension)
                faiss_index.add(np.ascontiguousarray(features["level"].matrix[valid_ids], dtype=np.float32))
                cache.faiss[strategy] = (faiss_index, valid_ids)
            faiss_index, valid_ids = cache.faiss[strategy]
            faiss_query = np.ascontiguousarray(queries["level"][None, :], dtype=np.float32)
            layers.append("float32_faiss_feature_distance")
            stats["faiss_index"] = "IndexHNSWFlat" if strategy == "faiss_hnsw" else "IndexFlatL2"
            if strategy == "faiss_hnsw":
                hnsw_params = faiss.SearchParametersHNSW()
                hnsw_params.efSearch = max(64, budget)
                layers.append("hnsw_graph_search_omissions")
                stats.update(hnsw_M=32, hnsw_ef_construction=80, hnsw_ef_search=hnsw_params.efSearch,
                             hnsw_seed=self.seed % (2**63), hnsw_rebuild_determinism_guaranteed=False)
        stats["approximation_layers"] = layers
        stats["candidate_prep_seconds"] = perf_counter() - started
        ranking_started = perf_counter()

        if strategy == "multiview":
            distances = {name: self._distance(features[name], queries[name], cache.valid) for name in names}
            scores = np.mean(np.stack(list(distances.values())), axis=0)
            quotas = {name: budget // len(names) + int(i < budget % len(names)) for i, name in enumerate(names)}
            ids = self._union_fill([_smallest(distances[name], quotas[name]) for name in names], scores, budget)
            stats["view_quotas"] = quotas
        elif strategy == "pyramid":
            event_scores = self._distance(features["events"], queries["events"], cache.valid)
            spectrum_scores = self._distance(features["spectrum"], queries["spectrum"], cache.valid)
            protected_quota = min(budget // 2, max(1, budget // 5))
            event_ids = _smallest(event_scores, protected_quota)
            spectrum_ids = _smallest(spectrum_scores, protected_quota)
            pool = np.arange(count, dtype=np.int64)
            pool_sizes = [count]
            for i, level in enumerate(levels):
                name = f"paa{level}"
                scores = self._distance(features[name], queries[name], cache.valid, pool)
                remaining = len(levels) - i - 1
                pool = _smallest(scores, min(len(pool), budget * (2**remaining)), pool)
                pool_sizes.append(len(pool))
            # Give protected IDs their fine-level scores even when the cascade
            # excluded them; they remain in the candidate union regardless.
            protected = np.unique(np.concatenate((event_ids, spectrum_ids)))
            scored = np.unique(np.concatenate((pool, protected)))
            name = f"paa{levels[-1]}"
            scores = self._distance(features[name], queries[name], cache.valid, scored)
            ids = self._union_fill([event_ids, spectrum_ids], scores, budget)
            stats.update(pyramid_pool_sizes=pool_sizes, event_protection_quota=protected_quota, spectrum_protection_quota=protected_quota)
        elif strategy == "binary":
            scores = _POPCOUNT[np.bitwise_xor(codes, query_code)].sum(axis=1, dtype=np.int64).astype(float)
            scores[~cache.valid] = np.inf
            ids = _smallest(scores, budget)
            stats["binary_bits"] = 128
        elif strategy == "faiss_hnsw":
            requested = min(len(valid_ids), budget)
            if requested:
                distances, local_ids = faiss_index.search(faiss_query, requested, params=hnsw_params)
                retained = local_ids[0] >= 0
                corpus_ids = valid_ids[local_ids[0, retained]]
                ordered = corpus_ids[np.lexsort((corpus_ids, distances[0, retained]))]
            else:
                ordered = np.empty(0, dtype=np.int64)
            chosen = dict.fromkeys(int(i) for i in ordered)
            stats["ann_returned_count"] = len(chosen)
            # Fill missing ANN entries deterministically; no unevaluated entry
            # is presented as if it had an actual vector or target distance.
            for group in (valid_ids, np.flatnonzero(~cache.valid)):
                for item in group:
                    if len(chosen) >= budget:
                        break
                    chosen.setdefault(int(item), None)
            ids = np.fromiter(chosen, dtype=np.int64)
            stats["ann_fill_count"] = len(ids) - stats["ann_returned_count"]
        else:
            scores = np.full(count, np.inf)
            requested = min(len(valid_ids), budget + 1)
            while requested:
                distances, local_ids = faiss_index.search(faiss_query, requested)
                corpus_ids = valid_ids[local_ids[0]]
                scores[corpus_ids] = distances[0]
                # Expand boundary ties so the global corpus ID, rather than
                # FAISS's internal heap order, determines a tied budget edge.
                if requested == len(valid_ids) or requested <= budget or distances[0, budget - 1] != distances[0, -1]:
                    break
                requested = min(len(valid_ids), requested * 2)
            ids = _smallest(scores, budget)
        stats["candidate_ranking_seconds"] = perf_counter() - ranking_started
        return ids, stats


__all__ = ["CandidateEngine"]
