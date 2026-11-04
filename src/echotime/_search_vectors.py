"""Reusable embedding banks with the exact native-batch reduction order.

This module caches per-series work only.  It deliberately uses the same
elementwise differences and row reductions as ``batch._embedding`` instead of
turning norms into a GEMM identity with a different rounding/cancellation path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from . import batch
from . import similarity_methods as sm
from .prepared import _readonly_array


_ALLOWED_PARAMS = {
    "acf": {"max_lag"},
    "periodogram": {"n_coeffs"},
    "trend": set(),
    "ordinal_js": {"order", "delay"},
    "linear_trend_model": set(),
}
_CHANNEL_PAIRING_TARGETS = {"acf", "periodogram", "trend"}


@dataclass(frozen=True, slots=True)
class PreparedVectorQuery:
    """An immutable query snapshot tied to the cache that prepared it."""

    raw: np.ndarray
    channels: int
    embedding: np.ndarray | None
    uses_reference: bool
    _owner: Any = field(repr=False, compare=False)


class VectorCache:
    """Cache the five native batch embedding families for an immutable bank.

    ``evaluate(query, ids)`` returns values in the requested ID order, including
    duplicate IDs.  Calling ``prepare_query`` once and passing its result to
    multiple ``evaluate`` calls also avoids recomputing the query embedding.

    The reference is one native ``one_vs_many`` call over the *entire* bank.
    Its channel policy therefore remains fixed across subsets and blocks:
    a mixed-channel bank, or a query with a different channel count, uses the
    existing pairwise reference path for every requested ID.  This is required
    because that path's scalar norms can differ by an ULP from vectorized row
    reductions, even for a pair whose own channels happen to match.
    """

    __slots__ = ("_series", "_metric", "_params", "_channels", "_bank_reference", "_features")

    def __init__(self, series: list[np.ndarray], metric: str, params: dict[str, Any]) -> None:
        name = batch._metric_name(metric)
        if name not in _ALLOWED_PARAMS:
            raise ValueError(f"VectorCache requires an embedding metric, got {metric!r}")
        options = dict(params)
        unknown = set(options).difference(_ALLOWED_PARAMS[name])
        if unknown:
            raise TypeError(f"{name} does not take {sorted(unknown)}.")
        if name == "acf" and int(options.get("max_lag", 10)) <= 0:
            raise ValueError("max_lag must be positive.")
        snapshot = tuple(_readonly_array(value) for value in series)
        channels = tuple(sm._to_time_series(value).shape[1] for value in snapshot)
        reference = name in _CHANNEL_PAIRING_TARGETS and len(set(channels)) > 1
        object.__setattr__(self, "_series", snapshot)
        object.__setattr__(self, "_metric", name)
        object.__setattr__(self, "_params", MappingProxyType(options))
        object.__setattr__(self, "_channels", channels)
        object.__setattr__(self, "_bank_reference", reference)
        object.__setattr__(self, "_features", None if reference else tuple(self._embed(raw) for raw in snapshot))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("VectorCache is immutable; build another cache to change its bank or parameters")

    @property
    def metric(self) -> str:
        return self._metric

    @property
    def params(self) -> Mapping[str, Any]:
        return self._params

    def _embed(self, raw: np.ndarray) -> np.ndarray | None:
        # Keep these operations in sync with batch._embedding.embed.  Tests
        # compare every family against the complete native batch call bitwise.
        if self.metric in {"ordinal_js", "linear_trend_model"}:
            values = sm._to_univariate_series(raw)
            if self.metric == "linear_trend_model":
                feature = sm._linear_trend_parameters(values)
            else:
                feature = sm._ordinal_pattern_distribution(
                    values, order=int(self.params.get("order", 3)), delay=int(self.params.get("delay", 1)),
                )
            return _readonly_array(feature)
        values, _ = sm._clean_series(sm._to_time_series(raw))
        if self.metric == "acf":
            max_lag = int(self.params.get("max_lag", 10))
            if not values.shape[1]:
                return None
            return _readonly_array(np.stack([
                sm._autocorrelation_vector(values[:, dim], max_lag=max_lag)
                for dim in range(values.shape[1])
            ]))
        if len(values) == 0:
            return None
        if self.metric == "periodogram":
            return _readonly_array(sm._periodogram_embedding(
                values, n_coeffs=int(self.params.get("n_coeffs", 32)), normalize=True,
            ))
        return _readonly_array(sm._trend_feature_vector(values))

    def prepare_query(self, query: Any) -> PreparedVectorQuery:
        raw = _readonly_array(query)
        channels = sm._to_time_series(raw).shape[1]
        reference = self._bank_reference or (
            self.metric in _CHANNEL_PAIRING_TARGETS
            and bool(self._channels) and channels != self._channels[0]
        )
        embedding = None if reference else self._embed(raw)
        return PreparedVectorQuery(raw, channels, embedding, reference, self)

    def _reference(self, query: PreparedVectorQuery, ids: np.ndarray) -> np.ndarray:
        name, params = self.metric, self.params
        functions = {
            "acf": lambda a, b: sm.acf_distance(a, b, **params),
            "periodogram": lambda a, b: sm.periodogram_distance(a, b, **params),
            "trend": sm.trend_distance,
            "ordinal_js": lambda a, b: sm.ordinal_pattern_js_distance(a, b, **params),
            "linear_trend_model": sm.linear_trend_model_distance,
        }
        return batch._reference_loop(
            [query.raw], self._series, np.zeros(ids.size, dtype=np.int64), ids, functions[name],
        )

    def evaluate(self, query: Any, ids: np.ndarray) -> np.ndarray:
        positions = np.asarray(ids)
        if positions.ndim != 1 or positions.dtype.kind not in "iu":
            raise ValueError("ids must be a one-dimensional integer array")
        if np.any(positions >= len(self._series)) or np.any(positions < 0):
            raise IndexError("candidate ID out of range")
        positions = positions.astype(np.int64, copy=False)
        if not positions.size:
            return np.empty(0, dtype=float)
        prepared = query if isinstance(query, PreparedVectorQuery) else self.prepare_query(query)
        if prepared._owner is not self:
            raise ValueError("Prepared query belongs to a different VectorCache")
        if prepared.uses_reference:
            return self._reference(prepared, positions)

        output = np.full(positions.size, np.nan, dtype=float)
        if prepared.embedding is None:
            return output
        assert self._features is not None
        valid = np.asarray([
            row for row, candidate in enumerate(positions) if self._features[int(candidate)] is not None
        ], dtype=np.int64)
        width = max(1, prepared.embedding.size)
        block_size = max(1, batch._EMBED_BLOCK_BYTES // (8 * width * 8))
        for start in range(0, valid.size, block_size):
            chunk = valid[start:start + block_size]
            left = np.broadcast_to(prepared.embedding, (chunk.size,) + prepared.embedding.shape)
            right = np.stack([self._features[int(positions[row])] for row in chunk])
            if self.metric == "acf":
                output[chunk] = np.mean(np.sqrt(np.sum((left - right) ** 2, axis=-1)), axis=-1)
            elif self.metric == "ordinal_js":
                output[chunk] = batch._js_rows(left, right)
            else:
                output[chunk] = np.sqrt(np.sum((left - right) ** 2, axis=-1))
        return output


__all__ = ["PreparedVectorQuery", "VectorCache"]
