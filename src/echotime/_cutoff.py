"""Cutoff-aware elastic distances for exact search.

The cutoff has the units of the public distance, including its normalization.
An exceeded result deliberately has no numeric distance: callers must inspect
``exceeded_cutoff`` before using ``value``.  Empty/invalid series still produce
the legacy NaN with ``exceeded_cutoff=False``.

The optional native extension abandons a dynamic program only after a proven
row bound is strictly greater than the cutoff.  The Python fallback evaluates
the existing reference in full, then applies the same result protocol.  This
keeps one Python definition of every distance and never changes a process-wide
backend setting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from . import _native
from . import similarity_methods as sm


@dataclass(frozen=True, slots=True)
class CutoffResult:
    """A distance or a certificate that it is strictly above the cutoff.

    ``cells_visited`` counts evaluated interior DP cells, excluding boundaries
    and input preparation.  It can equal the full count for an exceeded result
    when the certificate becomes available only at the last row.
    """

    value: float
    exceeded_cutoff: bool
    cells_visited: int


_ALLOWED_PARAMS = {
    "dtw": {"window", "normalize"},
    "edr": {"epsilon", "normalized", "window", "mode"},
    "lcss": {"epsilon", "window", "mode"},
    "erp": {"gap_value", "window", "mode"},
    "twed": {"lambda_", "nu", "t_x", "t_y", "window", "mode"},
}


def _full_cell_count(n: int, m: int, window: int | None) -> int:
    if not n or not m:
        return 0
    if window is None:
        return n * m
    return sum(max(0, min(m, i + window) - max(1, i - window) + 1) for i in range(1, n + 1))


def _completed(value: float, cutoff: float, cells: int) -> CutoffResult:
    if value > cutoff:
        return CutoffResult(float("nan"), True, cells)
    return CutoffResult(float(value), False, cells)


def cutoff_distance(
    x: Any,
    y: Any,
    metric: str = "dtw",
    *,
    cutoff: float = float("inf"),
    backend: str | None = None,
    **params: Any,
) -> CutoffResult:
    """Evaluate an elastic distance, optionally stopping above ``cutoff``.

    Supported metrics are ``dtw``, ``erp``, ``twed``, ``edr`` and ``lcss``;
    their ``*_distance`` names are accepted too.  Parameters, row cleaning,
    mixed-channel aggregation, bands, and fast-mode resampling are identical
    to the corresponding functions in :mod:`echotime.similarity_methods`.
    In particular, DTW accepts ``window`` and ``normalize`` but has no ``mode``
    parameter.  LCSS returns a distance (one minus its matching similarity).

    Ties survive: the certificate uses strict ``>``.  A cutoff of positive
    infinity computes the full reference distance.  NaN cutoffs are rejected;
    negative cutoffs, including negative infinity, are allowed.  TWED accepts
    the original ``t_x`` and ``t_y`` timestamp arrays, before row cleaning.

    The Python backend performs the full dynamic program.  The native backend
    reuses two DP rows and can abandon after any complete row.  Neither path
    uses a cutoff sentinel as a reported distance.
    """

    metric = str(metric).lower()
    if metric.endswith("_distance"):
        metric = metric[: -len("_distance")]
    if metric not in _ALLOWED_PARAMS:
        raise ValueError("metric must be one of 'dtw', 'erp', 'twed', 'edr', or 'lcss'.")
    unexpected = set(params) - _ALLOWED_PARAMS[metric]
    if unexpected:
        raise TypeError(f"Unexpected parameters for {metric}: {', '.join(sorted(unexpected))}.")
    try:
        threshold = float(cutoff)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("cutoff must be a real number other than NaN.") from None
    if np.isnan(threshold):
        raise ValueError("cutoff must be a real number other than NaN.")

    effective_backend = _native.resolve_backend(backend)
    epsilon = sm._nonnegative_parameter("epsilon", params.get("epsilon", 1.0)) if metric in {"edr", "lcss"} else 0.0
    lambda_ = sm._nonnegative_parameter("lambda_", params.get("lambda_", 1.0)) if metric == "twed" else 0.0
    nu = sm._nonnegative_parameter("nu", params.get("nu", 0.001)) if metric == "twed" else 0.0
    if metric == "dtw":
        left, right, left_ts, right_ts = sm._pair_series(x, y)
        mode = "exact"
    else:
        left, right, left_ts, right_ts, mode = sm._prepare_elastic_pair(
            x,
            y,
            mode=params.get("mode", "exact"),
            left_timestamps=params.get("t_x"),
            right_timestamps=params.get("t_y"),
        )
    n, m = len(left), len(right)
    if not n or not m:
        return CutoffResult(float("nan"), False, 0)
    window = sm._resolved_window(n, m, params.get("window"), mode)
    normalize = bool(params.get("normalize", False))
    normalized = bool(params.get("normalized", True))

    if metric == "erp":
        gap = sm._erp_gap(params.get("gap_value", 0.0), left.shape[1])
        left_gap = sm._pointwise_l2_to_reference(left, gap)
        right_gap = sm._pointwise_l2_to_reference(right, gap)
    elif metric == "twed":
        left_side = sm._twed_side(left, left_ts, lambda_=lambda_, nu=nu)
        right_side = sm._twed_side(right, right_ts, lambda_=lambda_, nu=nu)

    native_fn = None
    if effective_backend == "native":
        native_fn = getattr(_native.ext(), f"{metric}_pairs_cutoff", None)
    if native_fn is not None:
        va, oa = sm._bank([left], left.shape[1])
        vb, ob = sm._bank([right], right.shape[1])
        cutoffs = np.asarray([threshold], dtype=float)
        # Arbitrarily large Python integers still denote the full matrix.
        # Clamp before conversion to the extension's int64 window argument.
        native_window = sm._native_window(None if window is None else min(window, max(n, m)))
        common = (va, oa, vb, ob, sm._ONE, sm._ONE, cutoffs)
        if metric == "dtw":
            result = native_fn(*common, native_window, normalize, 1)
        elif metric == "edr":
            result = native_fn(*common, epsilon, normalized, native_window, False, 1)
        elif metric == "lcss":
            result = native_fn(*common, epsilon, native_window, False, 1)
        elif metric == "erp":
            result = native_fn(
                va, oa, sm._rows([left_gap]), vb, ob, sm._rows([right_gap]),
                sm._ONE, sm._ONE, cutoffs, native_window, False, 1,
            )
        else:
            result = native_fn(
                va, sm._bank([left_side[1]], left.shape[1])[0], oa,
                sm._rows([left_side[2]]), sm._rows([left_side[3]]), sm._rows([left_side[4]]),
                vb, sm._bank([right_side[1]], right.shape[1])[0], ob,
                sm._rows([right_side[2]]), sm._rows([right_side[3]]), sm._rows([right_side[4]]),
                sm._ONE, sm._ONE, cutoffs, nu, native_window, False, 1,
            )
        values, exceeded, cells = result
        return CutoffResult(float(values[0]), bool(exceeded[0]), int(cells[0]))

    # The reference functions below do not consult the global backend.  This
    # also supports a previously built optional extension with no cutoff ABI.
    if metric == "dtw":
        value = sm._dtw_dp_python(left, right, window)
        if normalize:
            value /= n + m
    elif metric == "edr":
        value = sm._edr_dp_python(left, right, epsilon, normalized, window)
    elif metric == "lcss":
        similarity = sm._lcss_dp_python(left, right, epsilon, window)
        value = float(1.0 - similarity) if np.isfinite(similarity) else float("nan")
    elif metric == "erp":
        value = sm._erp_dp_python(left, right, left_gap, right_gap, window)
    else:
        value = sm._twed_dp_python(left_side, right_side, nu, window)
    return _completed(value, threshold, _full_cell_count(n, m, window))


__all__ = ["CutoffResult", "cutoff_distance"]
