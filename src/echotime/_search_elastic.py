"""Persistent elastic banks and blocked native cutoff evaluation.

The raw input, row cleaning, pair-dependent channel aggregation, fast-mode
resampling, and timestamp preparation follow the existing scalar reference.
Only the reusable work moves out of the query/candidate inner loop.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from . import _native
from . import similarity_methods as sm
from ._cutoff import cutoff_distance, _full_cell_count


@dataclass
class ElasticQuery:
    raw: Any
    timestamps: Any
    channels: int
    groups: list[tuple[np.ndarray, tuple, tuple, np.ndarray]]


class ElasticCache:
    """Cache cleaned rows, native banks and ERP/TWED side terms by channel policy."""
    def __init__(self, series, timestamps, metric, params):
        self.series, self.timestamps = tuple(series), tuple(timestamps)
        self.metric, self.params = metric, dict(params)
        for key in {"epsilon", "lambda_", "nu"}.intersection(self.params):
            self.params[key] = sm._nonnegative_parameter(key, self.params[key])
        self.mode = sm._validate_mode(params.get("mode", "exact"))
        self.cleaned = tuple(sm._clean_series(sm._to_time_series(raw), ts) for raw, ts in zip(self.series, self.timestamps))
        self.channels = np.asarray([data.shape[1] for data, _ in self.cleaned], dtype=np.int64)
        self.banks = {}

    def _variant(self, data, timestamps, aggregate):
        if aggregate:
            data = np.nanmean(data, axis=1, keepdims=True)
        if self.mode == "fast":
            data, timestamps = sm._resample_series(data, max_points=sm._FAST_MODE_MAX_POINTS, timestamps=timestamps)
        return data, timestamps

    def _pack(self, rows):
        d = rows[0][0].shape[1]
        values, offsets = sm._bank([data for data, _ in rows], d)
        if self.metric == "erp":
            gap = sm._erp_gap(self.params.get("gap_value", 0.0), d)
            gap_costs = sm._rows([sm._pointwise_l2_to_reference(data, gap) for data, _ in rows])
            return values, offsets, gap_costs
        if self.metric == "twed":
            sides = [sm._twed_side(data, ts, lambda_=self.params.get("lambda_", 1.0), nu=self.params.get("nu", .001)) for data, ts in rows]
            previous, _ = sm._bank([side[1] for side in sides], d)
            return values, previous, offsets, sm._rows([side[2] for side in sides]), sm._rows([side[3] for side in sides]), sm._rows([side[4] for side in sides])
        return values, offsets

    def prepare_query(self, raw, timestamps=None, *, backend=None):
        query, query_ts = sm._clean_series(sm._to_time_series(raw), timestamps)
        channels = query.shape[1]
        if _native.resolve_backend(backend) == "python":
            # Python's scalar ERP returns NaN for an empty side before it
            # validates a gap vector. Do not eagerly validate a native bank.
            if self.metric == "erp" and len(query):
                for data, _ in self.cleaned:
                    if len(data):
                        sm._erp_gap(self.params.get("gap_value", 0.), channels if channels == data.shape[1] else 1)
            return ElasticQuery(raw, timestamps, channels, [])
        groups = []
        scalar_empty_erp = self.metric == "erp" and bool(np.any(self.channels != channels))
        if scalar_empty_erp and not len(query):
            return ElasticQuery(raw, timestamps, channels, [])
        for aggregate in (False, True):
            ids = np.flatnonzero(self.channels != channels if aggregate else self.channels == channels)
            if scalar_empty_erp:
                # A globally mixed-channel original bank uses scalar pairs.
                # Empty ERP pairs return NaN before checking a pair's gap
                # dimension; do not validate an irrelevant aggregate gap.
                ids = np.asarray([i for i in ids if len(self.cleaned[int(i)][0])], dtype=np.int64)
            if not len(ids):
                continue
            key = (channels, aggregate)
            if key not in self.banks:
                rows = [self._variant(*self.cleaned[int(i)], aggregate) for i in ids]
                packed = self._pack(rows)
                position = np.full(len(self.series), -1, dtype=np.int64)
                position[ids] = np.arange(len(ids))
                lengths = np.asarray([len(data) for data, _ in rows], dtype=np.int64)
                self.banks[key] = (packed, position, lengths)
            bank, position, lengths = self.banks[key]
            q = self._pack([self._variant(query, query_ts, aggregate)])
            groups.append((position, q, bank, lengths))
        return ElasticQuery(raw, timestamps, channels, groups)

    def max_pair_work(self, query):
        """A conservative cell-times-channel cost estimate for dispatch only."""
        largest = 0
        for _, left, _, lengths in query.groups:
            n = int(left[2 if self.metric == "twed" else 1][-1])
            d = left[0].shape[1]
            width = self.params.get("window")
            if width is None and self.mode == "exact":
                work = n * lengths * d
            else:
                w = np.ceil(.1 * np.maximum(n, lengths)).astype(np.int64) if width is None else min(int(width), max(n, int(lengths.max(initial=0))))
                w = np.maximum(w, np.abs(n - lengths))
                work = n * np.minimum(lengths, 2 * w + 1) * d
            largest = max(largest, int(work.max(initial=0)))
        return largest

    def evaluate_full(self, query, ids, *, n_jobs=None, backend=None):
        """Use the existing native full-scan kernels, including their SIMD path.

        This is often faster than any Python bound for short/narrow tasks.
        Its values retain the native batch arithmetic and its work is reported
        as full DP cell counts; no pruning is credited to this dispatch.
        """
        if _native.resolve_backend(backend) == "python":
            return self.evaluate(query, ids, n_jobs=n_jobs, backend="python")
        ids = np.asarray(ids, dtype=np.int64)
        values = np.full(len(ids), np.nan, dtype=float)
        cells = np.zeros(len(ids), dtype=np.int64)
        threads = _native.default_threads(n_jobs)
        metric, ext = self.metric, _native.ext()
        for positions, left, right, lengths in query.groups:
            selected = np.flatnonzero(positions[ids] >= 0)
            if not len(selected):
                continue
            rj = positions[ids[selected]]
            li = np.zeros(len(selected), dtype=np.int64)
            n = int(left[2 if metric == "twed" else 1][-1])
            window = self.params.get("window")
            window = -1 if window is None else min(int(window), max(n, int(lengths.max(initial=0))))
            fast = self.mode == "fast"
            if metric == "dtw":
                result = ext.dtw_pairs(*left, *right, li, rj, window, threads)
                if self.params.get("normalize", False):
                    result = result / (n + lengths[rj])
            elif metric in {"lcss", "lcss_similarity"}:
                result = ext.lcss_pairs(*left, *right, li, rj, float(self.params.get("epsilon", 1.)), window, fast, threads)
                if metric == "lcss":
                    result = np.where(np.isfinite(result), 1.0 - result, np.nan)
            elif metric == "edr":
                result = ext.edr_pairs(*left, *right, li, rj, float(self.params.get("epsilon", 1.)), bool(self.params.get("normalized", True)), window, fast, threads)
            elif metric == "erp":
                result = ext.erp_pairs(*left, *right, li, rj, window, fast, threads)
            else:
                result = ext.twed_pairs(*left, *right, li, rj, float(self.params.get("nu", .001)), window, fast, threads)
            values[selected] = result
            counts = {}
            for p, j in zip(selected, rj):
                m = int(lengths[j])
                if m not in counts:
                    w = sm._resolved_window(n, m, self.params.get("window"), self.mode)
                    counts[m] = _full_cell_count(n, m, w)
                cells[p] = counts[m]
        return values, np.zeros(len(ids), dtype=bool), cells

    def evaluate(self, query: ElasticQuery, ids, cutoff=float("inf"), *, n_jobs=None, backend=None):
        ids = np.asarray(ids, dtype=np.int64)
        values = np.full(len(ids), np.nan, dtype=float)
        exceeded = np.zeros(len(ids), dtype=bool)
        cells = np.zeros(len(ids), dtype=np.int64)
        resolved = _native.resolve_backend(backend)
        metric = self.metric
        fn = getattr(_native.ext(), f"{metric}_pairs_cutoff", None) if resolved == "native" and metric != "lcss_similarity" else None
        if resolved == "python" or metric != "lcss_similarity" and fn is None:
            for pos, item in enumerate(ids):
                params = dict(self.params)
                if metric == "lcss_similarity":
                    # Integer matching counts have the same division in either
                    # backend; no 1-(1-score) conversion is introduced.
                    left, right, _, _, mode = sm._prepare_elastic_pair(query.raw, self.series[item], mode=self.mode)
                    window = sm._resolved_window(len(left), len(right), params.get("window"), mode)
                    values[pos] = sm._lcss_dp_python(left, right, params.get("epsilon", 1.), window) if len(left) and len(right) else float("nan")
                    cells[pos] = _full_cell_count(len(left), len(right), window)
                else:
                    if metric == "twed":
                        params.update(t_x=query.timestamps, t_y=self.timestamps[item])
                    result = cutoff_distance(query.raw, self.series[item], metric, cutoff=cutoff, backend=resolved, **params)
                    values[pos], exceeded[pos], cells[pos] = result.value, result.exceeded_cutoff, result.cells_visited
            return values, exceeded, cells
        threads = _native.default_threads(n_jobs)
        for positions, left, right, lengths in query.groups:
            selected = np.flatnonzero(positions[ids] >= 0)
            if not len(selected):
                continue
            rj = positions[ids[selected]]
            li = np.zeros(len(selected), dtype=np.int64)
            cuts = np.full(len(selected), cutoff, dtype=float)
            offsets_index = 2 if metric == "twed" else 1
            n = int(left[offsets_index][-1])
            window = self.params.get("window")
            # A band beyond either side is equivalent to the full matrix and
            # must not overflow the C++ int64 index arithmetic.
            window = -1 if window is None else min(int(window), max(n, int(lengths.max(initial=0))))
            fast = self.mode == "fast"
            if metric == "lcss_similarity":
                result = _native.ext().lcss_pairs(*left, *right, li, rj,
                    float(self.params.get("epsilon", 1.)), window, fast, threads)
                values[selected] = result
                for p, j in zip(selected, rj):
                    w = sm._resolved_window(n, int(lengths[j]), self.params.get("window"), self.mode)
                    cells[p] = _full_cell_count(n, int(lengths[j]), w)
                continue
            if metric == "dtw":
                result = fn(*left, *right, li, rj, cuts, window, bool(self.params.get("normalize", False)), threads)
            elif metric == "edr":
                result = fn(*left, *right, li, rj, cuts, float(self.params.get("epsilon", 1.)),
                            bool(self.params.get("normalized", True)), window, fast, threads)
            elif metric == "lcss":
                result = fn(*left, *right, li, rj, cuts, float(self.params.get("epsilon", 1.)), window, fast, threads)
            elif metric == "erp":
                result = fn(*left, *right, li, rj, cuts, window, fast, threads)
            else:
                result = fn(*left, *right, li, rj, cuts, float(self.params.get("nu", .001)), window, fast, threads)
            values[selected], exceeded[selected], cells[selected] = result
        return values, exceeded, cells


__all__ = ["ElasticCache", "ElasticQuery"]
