"""Reusable exact and approximate retrieval over EchoTime's existing scores.

``certified`` means that every database item has either been evaluated or
excluded by an implemented conservative bound. It does not mean that all
metrics have an efficient bound: NCC currently uses a complete blocked scan.
The reference ranking is ascending distance / descending similarity, with NaN
last and database position as the tie breaker. Exact values are evaluated with
the selected batch backend; no vector-space surrogate is reported as a score.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
import json
import operator
import os
from pathlib import Path
import shutil
import tempfile
from time import perf_counter
from types import MappingProxyType
from typing import Any, Sequence

import numpy as np

from . import _native, batch
from . import similarity_methods as sm
from ._search_bounds import component_upper_bound, dtw_endpoint_bound, dtw_keogh_bound, match_envelope_bound
from .prepared import PreparedSeries
from .similarity import compare_series, compare_prepared_components, prepared_dtw_similarity, score_from_components

_HIGH_LEVEL = {"similarity_score", "component_mean"}
_SIMILARITIES = _HIGH_LEVEL | {"lcss_similarity", "max_ncc", "independent_max_ncc"}
_CUTOFF = {"dtw", "edr", "lcss", "erp", "twed"}
_FORMAT_VERSION = 1
_SCORE_SEMANTICS = "echotime-0.18-acceleration-v1"
_ALLOWED = {
    "dtw": {"window", "normalize"},
    "edr": {"epsilon", "normalized", "window", "mode"},
    "lcss": {"epsilon", "window", "mode"},
    "lcss_similarity": {"epsilon", "window", "mode"},
    "erp": {"gap_value", "window", "mode"},
    "twed": {"lambda_", "nu", "window", "mode"},
    "sbd": {"normalize"}, "max_ncc": {"normalize"},
    "independent_sbd": {"normalize"}, "independent_max_ncc": {"normalize"},
    "acf": {"max_lag"}, "periodogram": {"n_coeffs"}, "trend": set(),
    "ordinal_js": {"order", "delay"}, "linear_trend_model": set(),
    "similarity_score": {"n_points"}, "component_mean": {"n_points"},
}


def _snapshot(values: Any, dtype=float) -> np.ndarray:
    arr = np.asarray(values, dtype=dtype)
    # A flag on an owning array can be turned back on; a bytes buffer cannot.
    return np.frombuffer(arr.tobytes(order="C"), dtype=arr.dtype).reshape(arr.shape)


def _integer(value: Any, name: str, minimum: int = 0) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    try:
        result = operator.index(value)
    except TypeError:
        raise ValueError(f"{name} must be an integer >= {minimum}") from None
    if result < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return result


def _rank(value: float, item: int, descending: bool) -> tuple[int, float, int]:
    return (1, 0.0, item) if np.isnan(value) else (0, -value if descending else value, item)


class _TopK:
    def __init__(self, k: int, descending: bool):
        self.k, self.descending = k, descending
        self.heap: list[tuple[int, float, int, int, float]] = []

    def add(self, item: int, value: float) -> None:
        key = _rank(value, item, self.descending)
        entry = (-key[0], -key[1], -key[2], item, value)
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, entry)
        elif entry > self.heap[0]:
            heapq.heapreplace(self.heap, entry)

    @property
    def threshold(self) -> float | None:
        if len(self.heap) < self.k or not self.heap or np.isnan(self.heap[0][-1]):
            return None
        return self.heap[0][-1]

    def result(self) -> tuple[np.ndarray, np.ndarray]:
        rows = sorted(((entry[-2], entry[-1]) for entry in self.heap), key=lambda x: _rank(x[1], x[0], self.descending))
        return np.asarray([row[0] for row in rows], dtype=np.int64), np.asarray([row[1] for row in rows], dtype=float)


@dataclass(frozen=True)
class SearchResult:
    """Ranked database positions, original values, and auditable work counts.

    ``recall_estimate`` is None unless ``audit=True`` was requested. An audit
    evaluates the entire query exactly and reports its measured candidate
    recall, with ``audit_queries=1``. It is not a population confidence bound.
    """
    ids: np.ndarray
    values: np.ndarray
    certified: bool
    stats: dict[str, Any]
    recall_estimate: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"ids": self.ids.tolist(), "values": self.values.tolist(),
                "certified": self.certified, "stats": dict(self.stats),
                "recall_estimate": self.recall_estimate}


class PreparedCollection:
    """Immutable raw snapshots plus lazily cached high-level representations.

    Lists may be ragged. Array layout follows :func:`one_vs_many`. Each index
    retains the input orientation so the reference's small-matrix heuristics
    run exactly once when preparing a pair. The raw storage of a loaded index
    may be read-only memory mapped; feature caches are materialized on demand.
    """
    __slots__ = ("_series", "_timestamps", "_prepared", "_buckets", "_storage")

    def __init__(self, collection: Any, *, layout: str = "columns", timestamps: Any = None):
        raw = batch._as_collection(collection, layout)
        snapshots = tuple(_snapshot(value) for value in raw)
        if any(value.ndim not in (1, 2) for value in snapshots):
            raise ValueError("each series must be a one- or two-dimensional array")
        times = batch._timestamps_for(timestamps, len(raw))
        snapshots_ts = tuple(None if value is None else _snapshot(value) for value in times)
        if any(value is not None and value.ndim != 1 for value in snapshots_ts):
            raise ValueError("each timestamp array must be one-dimensional")
        self._init(snapshots, snapshots_ts)

    def _init(self, series, timestamps, storage=None):
        object.__setattr__(self, "_series", tuple(series))
        object.__setattr__(self, "_timestamps", tuple(timestamps))
        object.__setattr__(self, "_prepared", {})
        buckets: dict[tuple[int, int], list[int]] = {}
        for i, raw in enumerate(series):
            arr = sm._to_time_series(raw)
            buckets.setdefault(arr.shape, []).append(i)
        object.__setattr__(self, "_buckets", MappingProxyType({key: tuple(value) for key, value in buckets.items()}))
        object.__setattr__(self, "_storage", storage)

    def __setattr__(self, key, value):
        raise AttributeError("PreparedCollection is immutable; build a new snapshot")

    def __len__(self):
        return len(self._series)

    def __getitem__(self, item):
        return self._series[item]

    @property
    def timestamps(self):
        return self._timestamps

    @property
    def buckets(self):
        return self._buckets

    def prepared(self, item: int, n_points: int = 256) -> PreparedSeries:
        key = (int(item), n_points)
        if key not in self._prepared:
            self._prepared[key] = PreparedSeries(self[item], timestamps=self.timestamps[item], n_points=n_points)
        return self._prepared[key]


class SearchIndex:
    """A snapshot with fixed metric parameters and query-time search policy.

    The default policy is certified. Approximation is opt-in and only changes
    candidate selection, never the exact scoring function used for reranking.
    ``bounds='none'`` disables explicit bounds but retains DP cutoffs;
    ``'cheap'`` enables endpoint bounds. ``'auto'`` uses cached full native
    scans for short/narrow DPs (estimated work <= 65,536 cells x channels per
    pair), otherwise enabling envelope bounds for bands no wider than 64.
    ``'all'`` enables every implemented certified bound. The auto crossover is
    a provisional measured CPU heuristic, not a hardware-independent optimum.
    Whether a bound saves time depends on the data and must be measured.
    """
    def __init__(self, collection: PreparedCollection, target: str, params: dict[str, Any], *, backend: str | None, n_jobs: int | None):
        self.collection = collection
        self.target = target
        self.params = MappingProxyType({
            key: _snapshot(value) if key == "gap_value" else
                 value.item() if isinstance(value, np.ndarray) and value.ndim == 0 else
                 _snapshot(value, dtype=value.dtype) if isinstance(value, np.ndarray) else value
            for key, value in params.items()
        })
        self.backend = backend
        self.n_jobs = n_jobs
        self._candidate_engine = None
        self._vector_cache = None
        self._elastic_cache = None
        self._ncc_cache = None

    def __setattr__(self, name, value):
        if name in {"collection", "target", "params", "backend", "n_jobs"} and hasattr(self, name):
            raise AttributeError("SearchIndex configuration is fixed; build another index")
        object.__setattr__(self, name, value)

    @classmethod
    def build(cls, collection: Any, target: str = "dtw", *, layout: str = "columns", timestamps: Any = None,
              n_jobs: int | None = None, backend: str | None = None, **params: Any) -> "SearchIndex":
        target = str(target) if target in _HIGH_LEVEL else batch._metric_name(target)
        if target == "best_shift":
            raise ValueError("best_shift is a lag, not a retrieval distance or similarity")
        # The plan's DTW example uses mode='exact'; this harmless spelling is
        # accepted here, but fast DTW is not invented by the search layer.
        if target == "dtw" and params.get("mode") == "exact":
            params.pop("mode")
        unknown = set(params).difference(_ALLOWED[target])
        if unknown:
            raise TypeError(f"{target} does not take {sorted(unknown)}")
        _native.resolve_backend(backend)
        if n_jobs is not None:
            try:
                if isinstance(n_jobs, (bool, np.bool_)):
                    raise TypeError
                n_jobs = operator.index(n_jobs)
            except TypeError:
                raise ValueError("n_jobs must be a positive integer, -1 or None") from None
            if n_jobs != -1 and n_jobs < 1:
                raise ValueError("n_jobs must be a positive integer, -1 or None")
        if target in batch._ELASTIC:
            mode = sm._validate_mode(params.get("mode", "exact"))
            sm._resolved_window(1, 1, params.get("window"), mode)
        for key in {"epsilon", "lambda_", "nu"}.intersection(params):
            params[key] = sm._nonnegative_parameter(key, params[key])
        for key in {"normalize", "normalized"}.intersection(params):
            params[key] = bool(params[key])
        if target in _HIGH_LEVEL:
            params["n_points"] = _integer(params.get("n_points", 256), "n_points", 1)
        if target == "acf" and int(params.get("max_lag", 10)) <= 0:
            raise ValueError("max_lag must be positive")
        if isinstance(collection, PreparedCollection):
            if timestamps is not None:
                raise ValueError("a PreparedCollection already owns its timestamps")
            prepared = collection
        else:
            prepared = PreparedCollection(collection, layout=layout, timestamps=timestamps)
        return cls(prepared, target, params, backend=backend, n_jobs=n_jobs)

    def _query(self, query: Any, timestamps: Any):
        if self.target in _HIGH_LEVEL:
            points = self.params["n_points"]
            if isinstance(query, PreparedSeries):
                if query.n_points != points or timestamps is not None:
                    raise ValueError("prepared query configuration must match the index")
                return query
            return PreparedSeries(query, timestamps=timestamps, n_points=points)
        # Snapshot once: a user changing an input during a search cannot alter
        # its meaning between the bound and the exact scorer.
        raw = _snapshot(query)
        sm._to_time_series(raw)
        return raw

    def _ordered_ids(self, initial_candidates: Any) -> np.ndarray:
        n = len(self.collection)
        if initial_candidates is None:
            return np.arange(n, dtype=np.int64)
        seeds = self._ids(initial_candidates)
        mask = np.ones(n, dtype=bool)
        mask[seeds] = False
        return np.concatenate((seeds, np.flatnonzero(mask)))

    def _ids(self, values: Any) -> np.ndarray:
        ids = np.asarray(values)
        if ids.ndim != 1 or ids.dtype.kind not in "iu" and ids.size:
            raise ValueError("candidate IDs must be a one-dimensional integer array")
        ids = ids.astype(np.int64)
        if np.any(ids < 0) or np.any(ids >= len(self.collection)) or np.unique(ids).size != ids.size:
            raise ValueError("candidate IDs must be unique valid database positions")
        return ids

    def _candidate_ids(self, query, budget: int, strategy: str):
        from ._search_candidates import CandidateEngine
        if self._candidate_engine is None:
            if self.target in _HIGH_LEVEL:
                series = [self.collection.prepared(i, self.params["n_points"]).resampled for i in range(len(self.collection))]
            else:
                series = [sm._to_time_series(item) for item in self.collection]
            self._candidate_engine = CandidateEngine(series)
        values = query.resampled if isinstance(query, PreparedSeries) else sm._to_time_series(query)
        return self._candidate_engine.select(values, budget, strategy=strategy)

    def search(self, query: Any, k: int = 10, *, mode: str = "certified", candidates: int | None = None,
               strategy: str = "multiview", audit: bool = False, query_timestamps: Any = None,
               bounds: str = "auto", initial_candidates: Any = None, block_size: int = 256) -> SearchResult:
        """Find top-k with stable ties; ``audit`` explicitly pays for truth.

        ``initial_candidates`` only changes evaluation order in certified
        mode. All remaining positions are covered before certification. A
        candidate budget smaller than k is rejected instead of silently
        returning fewer potential neighbors.
        """
        k = min(_integer(k, "k"), len(self.collection))
        return self._run(query, k=k, radius=None, mode=mode, candidates=candidates, strategy=strategy,
                         audit=audit, query_timestamps=query_timestamps, bounds=bounds,
                         initial_candidates=initial_candidates, block_size=block_size)

    def range_search(self, query: Any, radius: float, *, query_timestamps: Any = None,
                     bounds: str = "auto", block_size: int = 256) -> SearchResult:
        """Return every finite/non-NaN distance <= radius, including ties.

        Only distance targets are accepted; score thresholds use different
        inequality semantics and are deliberately not overloaded here.
        """
        if self.target in _SIMILARITIES:
            raise ValueError("range_search is supported only for distance targets")
        radius = float(radius)
        if np.isnan(radius):
            raise ValueError("radius must not be NaN")
        return self._run(query, k=None, radius=radius, mode="certified", candidates=None,
                         strategy="multiview", audit=False, query_timestamps=query_timestamps,
                         bounds=bounds, initial_candidates=None, block_size=block_size)

    def _run(self, raw_query, *, k, radius, mode, candidates, strategy, audit, query_timestamps, bounds, initial_candidates, block_size):
        start = perf_counter()
        if mode not in {"certified", "approximate"}:
            raise ValueError("mode must be certified or approximate")
        if bounds not in {"none", "cheap", "auto", "all"}:
            raise ValueError("bounds must be none, cheap, auto or all")
        block_size = _integer(block_size, "block_size", 1)
        if mode == "certified" and (candidates is not None or audit):
            raise ValueError("candidates and audit are approximate-mode options")
        if mode == "approximate" and initial_candidates is not None:
            raise ValueError("initial_candidates is a certified-mode warm-start option")
        if query_timestamps is not None:
            query_timestamps = _snapshot(query_timestamps)
        query = self._query(raw_query, query_timestamps)
        resolved = _native.resolve_backend(self.backend)
        prepare_seconds = perf_counter() - start
        stats = {"total_candidates": len(self.collection), "candidates": 0,
                 "bounds_evaluated": 0, "endpoint_bounds": 0, "envelope_bounds": 0,
                 "component_bounds": 0, "pruned": 0, "exact_evaluations": 0,
                 "cutoff_abandoned": 0, "cells_visited": 0, "prepare_seconds": prepare_seconds,
                 "bound_seconds": 0.0, "exact_seconds": 0.0, "candidate_seconds": 0.0,
                 "backend": resolved, "target": self.target, "mode": mode,
                 "bounds_policy": bounds, "coverage_complete": mode == "certified",
                 "audit_queries": 0, "n_jobs_requested": self.n_jobs,
                 "reference": "compare_series" if self.target in _HIGH_LEVEL else "one_vs_many",
                 "score_error": "none: exact selected-backend reranking"}
        candidate_ids = None
        if mode == "approximate":
            budget = max(k or 0, min(256, len(self.collection))) if candidates is None else _integer(candidates, "candidates")
            if budget < (k or 0):
                raise ValueError("candidates must be at least min(k, collection size)")
            t = perf_counter()
            candidate_ids, candidate_stats = self._candidate_ids(query, min(budget, len(self.collection)), strategy)
            candidate_ids = self._ids(candidate_ids)
            stats["candidate_seconds"] = perf_counter() - t
            stats["candidate_selection"] = candidate_stats
            order = candidate_ids
        else:
            order = self._ordered_ids(initial_candidates)
        stats["candidates"] = len(order)
        descending = self.target in _SIMILARITIES
        top = _TopK(k, descending) if k is not None and k else None
        found: list[tuple[int, float]] = []

        def threshold():
            return radius if radius is not None else top.threshold

        def accept(item, value):
            if top is not None:
                top.add(int(item), float(value))
            elif radius is not None and not np.isnan(value) and value <= radius:
                found.append((int(item), float(value)))

        # A top-0 answer is vacuously complete without touching any distance.
        if k == 0:
            stats["pruned"] = len(order)
        elif self.target in _HIGH_LEVEL:
            for item in order:
                item = int(item)
                t = perf_counter()
                right = self.collection.prepared(item, self.params["n_points"])
                components = compare_prepared_components(query, right, include_dtw=False)
                tau = threshold()
                upper = component_upper_bound(components, target=self.target)
                stats["component_bounds"] += 1
                stats["bounds_evaluated"] += 1
                stats["bound_seconds"] += perf_counter() - t
                if bounds != "none" and tau is not None and upper < tau:
                    stats["pruned"] += 1
                    continue
                t = perf_counter()
                components["dtw_similarity"] = prepared_dtw_similarity(query, right, backend=resolved)
                value = getattr(score_from_components(components), self.target)
                stats["exact_evaluations"] += 1
                stats["exact_seconds"] += perf_counter() - t
                accept(item, value)
        elif self.target in _CUTOFF or self.target == "lcss_similarity":
            from ._search_elastic import ElasticCache
            t = perf_counter()
            if self._elastic_cache is None:
                self._elastic_cache = ElasticCache(list(self.collection), self.collection.timestamps,
                                                   self.target, dict(self.params))
            elastic_query = self._elastic_cache.prepare_query(query, query_timestamps, backend=resolved)
            stats["prepare_seconds"] += perf_counter() - t
            threads = _native.default_threads(self.n_jobs) if resolved == "native" else 1
            stats["n_jobs_effective"] = threads
            work = self._elastic_cache.max_pair_work(elastic_query) if resolved == "native" else None
            full_scan = bounds == "auto" and resolved == "native" and work <= 65536
            stats["max_pair_work_estimate"] = work
            stats["evaluation_policy"] = "cached_native_scan" if full_scan else "bounded_cutoff"
            stats["cutoff_backend"] = "native" if resolved == "native" and _native.similarity_backend_info()["cutoff_available"] else "python_reference"
            step = min(block_size, max(8, threads * 4))
            if full_scan:
                step = block_size
                stats["fallback_reason"] = "auto: short/narrow DP is cheaper than Python bound overhead on measured CPU workloads"
            pos = 0
            while pos < len(order):
                # Seed the heap before paying for a large speculative block.
                size = min(step, max(1, k)) if pos == 0 and k is not None and not full_scan else step
                chunk = order[pos:pos + size]
                pos += len(chunk)
                tau = threshold()
                pending = []
                t = perf_counter()
                for item in chunk:
                    item = int(item)
                    bound = None
                    if not full_scan and bounds != "none" and tau is not None:
                        if self.target == "dtw":
                            bound = dtw_endpoint_bound(query, self.collection[item], **self.params)
                            stats["endpoint_bounds"] += 1
                            stats["bounds_evaluated"] += 1
                        envelope = bounds == "all" or (bounds == "auto" and self.params.get("window") is not None and self.params["window"] <= 64)
                        if envelope and (bound is None or bound.value <= tau):
                            if self.target == "dtw":
                                bound = dtw_keogh_bound(query, self.collection[item], **self.params)
                            elif self.target in {"edr", "lcss", "lcss_similarity"}:
                                bound = match_envelope_bound(query, self.collection[item], metric=self.target, **self.params)
                            if bound is not None:
                                stats["envelope_bounds"] += 1
                                stats["bounds_evaluated"] += 1
                    if bound is not None and bound.certified and ((bound.value < tau) if descending else (bound.value > tau)):
                        stats["pruned"] += 1
                    else:
                        pending.append(item)
                stats["bound_seconds"] += perf_counter() - t
                if not pending:
                    continue
                t = perf_counter()
                if full_scan:
                    values, abandoned, cells = self._elastic_cache.evaluate_full(elastic_query, pending, n_jobs=threads, backend=resolved)
                else:
                    values, abandoned, cells = self._elastic_cache.evaluate(
                        elastic_query, pending, cutoff=float("inf") if tau is None or descending else tau,
                        n_jobs=threads, backend=resolved,
                    )
                stats["cells_visited"] += int(cells.sum())
                stats["cutoff_abandoned"] += int(abandoned.sum())
                stats["pruned"] += int(abandoned.sum())
                stats["exact_evaluations"] += len(pending) - int(abandoned.sum())
                stats["exact_seconds"] += perf_counter() - t
                for item, value, exceeded in zip(pending, values, abandoned):
                    if not exceeded:
                        accept(item, value)
        else:
            stats["n_jobs_effective"] = _native.default_threads(self.n_jobs)
            if self.target in batch._NCC:
                stats["fallback_reason"] = "FFT rounding bound is not certified; complete blocked exact scan"
            eval_query = query
            if resolved == "native" and self.target in batch._EMBED:
                from ._search_vectors import VectorCache
                t = perf_counter()
                if self._vector_cache is None:
                    self._vector_cache = VectorCache(list(self.collection), self.target, dict(self.params))
                eval_query = self._vector_cache.prepare_query(query)
                stats["prepare_seconds"] += perf_counter() - t
            elif resolved == "native" and self.target in batch._NCC:
                from ._search_ncc import NCCCache
                t = perf_counter()
                if self._ncc_cache is None:
                    self._ncc_cache = NCCCache(list(self.collection), self.target, dict(self.params), n_jobs=self.n_jobs)
                eval_query = self._ncc_cache.prepare_query(query)
                stats["prepare_seconds"] += perf_counter() - t
            for pos in range(0, len(order), block_size):
                ids = order[pos:pos + block_size]
                t = perf_counter()
                values = self._exact_block(eval_query, ids, resolved, query_timestamps)
                stats["exact_seconds"] += perf_counter() - t
                stats["exact_evaluations"] += len(ids)
                for item, value in zip(ids, values):
                    accept(item, value)
        if top is not None:
            ids, values = top.result()
        else:
            found.sort(key=lambda row: _rank(row[1], row[0], descending))
            ids = np.asarray([row[0] for row in found], dtype=np.int64)
            values = np.asarray([row[1] for row in found], dtype=float)
        recall = None
        stats["search_seconds"] = perf_counter() - start
        if mode == "approximate" and audit:
            t = perf_counter()
            truth = self.search(raw_query, k=k, query_timestamps=query_timestamps, bounds=bounds, block_size=block_size)
            recall = len(np.intersect1d(truth.ids, candidate_ids)) / len(truth.ids) if len(truth.ids) else 1.0
            stats.update(audit_queries=1, audit_seconds=perf_counter() - t,
                         candidate_recall_at_k=recall,
                         result_recall_at_k=len(np.intersect1d(truth.ids, ids)) / len(truth.ids) if len(truth.ids) else 1.0)
        stats["elapsed_seconds"] = perf_counter() - start
        stats["prune_fraction"] = stats["pruned"] / len(order) if len(order) else 0.0
        stats["covered_candidates"] = len(order)
        return SearchResult(_snapshot(ids, np.int64), _snapshot(values), mode == "certified", stats, recall)

    def _exact_block(self, query, ids, backend, query_timestamps):
        if backend == "native" and self.target in batch._EMBED:
            from ._search_vectors import VectorCache
            if self._vector_cache is None:
                self._vector_cache = VectorCache(list(self.collection), self.target, dict(self.params))
            return self._vector_cache.evaluate(query, ids)
        if backend == "native" and self.target in batch._NCC:
            return self._ncc_cache.evaluate(query, ids)
        return batch.one_vs_many(query, [self.collection[int(i)] for i in ids], metric=self.target,
                                 query_timestamps=query_timestamps,
                                 candidate_timestamps=[self.collection.timestamps[int(i)] for i in ids],
                                 n_jobs=self.n_jobs, backend=backend, **self.params)

    def search_batch(self, queries: Any, k: int = 10, *, layout: str = "columns", timestamps: Any = None, **kwargs) -> list[SearchResult]:
        """Reuse the collection across sequential queries without oversubscribing workers."""
        rows = batch._as_collection(queries, layout)
        times = batch._timestamps_for(timestamps, len(rows))
        return [self.search(query, k=k, query_timestamps=ts, **kwargs) for query, ts in zip(rows, times)]

    def refine(self, query: Any, hits: SearchResult, *, k: int | None = None, **kwargs) -> SearchResult:
        """Use provisional IDs as warm starts, then cover the entire database.

        Values and certificates in ``hits`` are never trusted as proof for a
        new query; the selected positions are recomputed with this index.
        """
        return self.search(query, k=len(hits.ids) if k is None else k, initial_candidates=hits.ids, **kwargs)

    def explain(self, query: Any, ids: Sequence[int], *, query_timestamps: Any = None, n_points: int | None = None):
        """Generate full SimilarityReports only for requested result positions."""
        points = self.params.get("n_points", 256) if n_points is None else _integer(n_points, "n_points", 1)
        return [compare_series(query, self.collection.prepared(int(item), points), left_timestamps=query_timestamps,
                               n_points=points, right_name=f"candidate_{int(item)}") for item in self._ids(ids)]

    def save(self, path: str | os.PathLike) -> Path:
        """Save a portable numeric snapshot without pickle or executable data.

        Existing destinations are refused. Derived caches and FAISS state are
        rebuilt under the current software; the manifest fixes the original
        target, parameters and snapshot format instead of serializing code.
        """
        dest = Path(path)
        if dest.exists():
            raise FileExistsError(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix=".echotime-index-", dir=dest.parent))
        try:
            shapes = np.ones((len(self.collection), 2), dtype=np.int64)
            ndims = np.empty(len(self.collection), dtype=np.uint8)
            offsets = [0]
            ts_offsets = [0]
            times, values, provided = [], [], []
            for i, raw in enumerate(self.collection):
                ndims[i] = raw.ndim
                shapes[i, :raw.ndim] = raw.shape
                values.append(raw.ravel())
                offsets.append(offsets[-1] + raw.size)
                ts = self.collection.timestamps[i]
                provided.append(ts is not None)
                times.append(np.empty(0) if ts is None else ts)
                ts_offsets.append(ts_offsets[-1] + (0 if ts is None else len(ts)))
            arrays = {"values": np.concatenate(values) if values else np.empty(0),
                      "offsets": np.asarray(offsets, dtype=np.int64), "shapes": shapes, "ndims": ndims,
                      "time_values": np.concatenate(times) if times else np.empty(0),
                      "time_offsets": np.asarray(ts_offsets, dtype=np.int64), "time_provided": np.asarray(provided, dtype=bool)}
            for key, value in arrays.items():
                np.save(temp / f"{key}.npy", value, allow_pickle=False)
            params = {key: value.tolist() if isinstance(value, np.ndarray) else value.item() if isinstance(value, np.generic) else value for key, value in self.params.items()}
            manifest = {"format": "echotime-search", "version": _FORMAT_VERSION, "target": self.target,
                        "score_semantics": _SCORE_SEMANTICS, "params": params,
                        "count": len(self.collection), "backend": self.backend, "n_jobs": self.n_jobs}
            (temp / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            os.rename(temp, dest)
        except BaseException:
            shutil.rmtree(temp, ignore_errors=True)
            raise
        return dest

    @classmethod
    def load(cls, path: str | os.PathLike, *, mmap: bool = True, backend: str | None = None, n_jobs: int | None = None) -> "SearchIndex":
        """Load fixed numeric filenames with shape/offset validation.

        ``backend=None`` resolves on the loading machine, so a snapshot from a
        native-enabled host remains usable on a Python-only installation.
        """
        source = Path(path)
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("format") != "echotime-search" or manifest.get("version") != _FORMAT_VERSION:
            raise ValueError("unsupported EchoTime search index format")
        if manifest.get("score_semantics") != _SCORE_SEMANTICS:
            raise ValueError("incompatible EchoTime score semantics; rebuild the index")
        n = _integer(manifest.get("count"), "count")
        keys = ("values", "offsets", "shapes", "ndims", "time_values", "time_offsets", "time_provided")
        arrays = {key: np.load(source / f"{key}.npy", mmap_mode="r" if mmap else None, allow_pickle=False) for key in keys}
        v, off, shapes, ndims, tv, toff, provided = (arrays[key] for key in keys)
        if (v.ndim != 1 or v.dtype != np.dtype(float) or tv.ndim != 1 or tv.dtype != np.dtype(float)
            or off.shape != (n + 1,) or off.dtype != np.dtype("int64")
            or toff.shape != (n + 1,) or toff.dtype != np.dtype("int64")
            or shapes.shape != (n, 2) or shapes.dtype != np.dtype("int64")
            or ndims.shape != (n,) or ndims.dtype != np.dtype("uint8")
            or provided.shape != (n,) or provided.dtype != np.dtype(bool)):
            raise ValueError("invalid index array schema")
        if (off[0] != 0 or toff[0] != 0 or off[-1] != len(v) or toff[-1] != len(tv)
            or np.any(off < 0) or np.any(toff < 0) or np.any(np.diff(off) < 0) or np.any(np.diff(toff) < 0)
            or np.any(shapes < 0) or np.any((ndims != 1) & (ndims != 2))):
            raise ValueError("invalid index offsets or shapes")
        series, times = [], []
        for i in range(n):
            shape = tuple(int(value) for value in shapes[i, :ndims[i]])
            size = int(shape[0]) * (int(shape[1]) if len(shape) == 2 else 1)
            if size != int(off[i + 1]) - int(off[i]):
                raise ValueError("index shape does not match its offsets")
            if not provided[i] and toff[i + 1] != toff[i]:
                raise ValueError("missing timestamp flag has stored values")
            raw = v[off[i]:off[i + 1]].reshape(shape)
            ts = tv[toff[i]:toff[i + 1]] if provided[i] else None
            series.append(raw if mmap else _snapshot(raw))
            times.append(ts if mmap or ts is None else _snapshot(ts))
        collection = object.__new__(PreparedCollection)
        collection._init(series, times, arrays)
        return cls.build(collection, target=manifest["target"], backend=backend, n_jobs=n_jobs, **manifest["params"])


__all__ = ["PreparedCollection", "SearchIndex", "SearchResult"]
