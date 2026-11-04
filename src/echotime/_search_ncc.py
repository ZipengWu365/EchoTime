"""Reusable NCC input/FFT preparation with the unchanged batch refinement."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

import numpy as np

from . import _native, batch
from . import similarity_methods as sm
from .prepared import _readonly_array


# Limit persistent spectra across many different query lengths.  A block can
# temporarily hold additional spectra, just as the existing batch kernel does.
_SPECTRUM_CACHE_BYTES = 256 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class PreparedNCCQuery:
    """Immutable input/units; one lazily cached FFT per required padding length."""

    raw: np.ndarray
    clean: np.ndarray
    units: tuple[np.ndarray, ...]
    _owner: Any = field(repr=False, compare=False)
    _spectra: dict[int, tuple[np.ndarray, ...]] = field(default_factory=dict, repr=False, compare=False)


class NCCCache:
    """Cache native-batch NCC preparation without changing its score arithmetic.

    Cleaning and channel normalization are fixed at construction.  Each query
    is prepared once; a ragged bank can require several FFT padding lengths,
    and its query FFT is computed once for each such length.  Bank FFTs are
    reused across queries with the same padding length and stored in a bounded
    LRU cache.  Short and channel-mismatched pairs retain the original direct
    reference fallback.  The existing ``batch._ncc_group`` still performs all
    inverse FFTs, lag selection and exact dot-product refinement.
    """

    def __init__(self, series, metric: str, params: dict[str, Any], n_jobs: int | None = None):
        name = batch._metric_name(metric)
        if name not in batch._NCC:
            raise ValueError(f"NCCCache requires an NCC metric, got {metric!r}")
        unknown = set(params).difference({"normalize"})
        if unknown:
            raise TypeError(f"{name} does not take {sorted(unknown)}.")
        self.metric = name
        self.params = MappingProxyType({"normalize": bool(params.get("normalize", True))})
        self.independent = name.startswith("independent")
        self.threads = _native.default_threads(n_jobs)
        self.series = tuple(_readonly_array(raw) for raw in series)
        self.cleaned = tuple(_readonly_array(sm._clean_series(sm._to_time_series(raw))[0]) for raw in self.series)
        self.units = {i: self._units(values) for i, values in enumerate(self.cleaned)}
        self._spectra: OrderedDict[tuple[int, int], tuple[np.ndarray, ...]] = OrderedDict()
        self._spectrum_bytes = 0

    def _units(self, values: np.ndarray) -> tuple[np.ndarray, ...]:
        normalize = self.params["normalize"]
        if self.independent:
            result = []
            for dim in range(values.shape[1]):
                column = values[:, dim].reshape(-1, 1)
                xs = sm._z_normalize(column) if normalize else column
                result.append(_readonly_array(np.ascontiguousarray(xs[:, 0])))
            return tuple(result)
        xs = sm._z_normalize(values) if normalize else values
        return tuple(_readonly_array(np.ascontiguousarray(xs[:, dim])) for dim in range(xs.shape[1]))

    def prepare_query(self, raw: Any) -> PreparedNCCQuery:
        snapshot = _readonly_array(raw)
        clean = _readonly_array(sm._clean_series(sm._to_time_series(snapshot))[0])
        return PreparedNCCQuery(snapshot, clean, self._units(clean), self)

    def _query_spectra(self, query: PreparedNCCQuery, length: int) -> tuple[np.ndarray, ...]:
        if length not in query._spectra:
            query._spectra[length] = tuple(
                _readonly_array(value, dtype=value.dtype)
                for value in (batch.sp_fft.rfft(column, length, workers=self.threads) for column in query.units)
            )
        return query._spectra[length]

    def _bank_spectra(self, item: int, length: int) -> tuple[np.ndarray, ...]:
        key = (length, item)
        if key in self._spectra:
            self._spectra.move_to_end(key)
            return self._spectra[key]
        spectra = tuple(
            _readonly_array(value, dtype=value.dtype)
            for value in (
                np.conj(batch.sp_fft.rfft(column, length, workers=self.threads))
                for column in self.units[item]
            )
        )
        size = sum(value.nbytes for value in spectra)
        if size <= _SPECTRUM_CACHE_BYTES:
            while self._spectra and self._spectrum_bytes + size > _SPECTRUM_CACHE_BYTES:
                _, evicted = self._spectra.popitem(last=False)
                self._spectrum_bytes -= sum(value.nbytes for value in evicted)
            self._spectra[key] = spectra
            self._spectrum_bytes += size
        return spectra

    def evaluate(self, query: Any, ids: np.ndarray) -> np.ndarray:
        positions = np.asarray(ids)
        if positions.ndim != 1 or positions.dtype.kind not in "iu":
            raise ValueError("ids must be a one-dimensional integer array")
        if np.any(positions >= len(self.series)) or np.any(positions < 0):
            raise IndexError("candidate ID out of range")
        positions = positions.astype(np.int64, copy=False)
        dtype = np.int64 if self.metric == "best_shift" else float
        if not positions.size:
            return np.empty(0, dtype=dtype)
        prepared = query if isinstance(query, PreparedNCCQuery) else self.prepare_query(query)
        if prepared._owner is not self:
            raise ValueError("Prepared query belongs to a different NCCCache")
        output = np.empty(positions.size, dtype=dtype)
        groups: dict[tuple[int, int, int], list[int]] = {}
        fallback = []
        n, d = prepared.clean.shape
        for row, item in enumerate(positions):
            right = self.cleaned[int(item)]
            if d != right.shape[1] or min(n, len(right)) < batch._MIN_FFT_LENGTH:
                fallback.append(row)
            else:
                groups.setdefault((n, len(right), d), []).append(row)
        left_indices = np.zeros(positions.size, dtype=np.int64)
        if fallback:
            fn = {
                "max_ncc": sm.max_ncc, "sbd": sm.sbd, "best_shift": sm.best_shift,
                "independent_max_ncc": sm.independent_max_ncc, "independent_sbd": sm.independent_sbd,
            }[self.metric]
            output[fallback] = batch._reference_loop(
                [prepared.raw], self.series, left_indices[fallback], positions[fallback],
                lambda left, right: fn(left, right, normalize=self.params["normalize"]), dtype,
            )
        left_units = {0: prepared.units}
        for (n, m, d), members in groups.items():
            length = batch.sp_fft.next_fast_len(n + m - 1, real=True)
            selected_ids = sorted({int(positions[row]) for row in members})
            left_spectra = {0: self._query_spectra(prepared, length)}
            right_spectra = {item: self._bank_spectra(item, length) for item in selected_ids}
            batch._ncc_group(
                np.asarray(members), n, m, d, left_indices, positions, left_units, self.units,
                self.independent, self.metric, output, self.threads,
                spectra_left=left_spectra, spectra_right=right_spectra,
            )
        return output


__all__ = ["PreparedNCCQuery", "NCCCache"]
