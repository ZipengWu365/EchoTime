"""Bounds for search, with an explicit distinction between proof and priority.

The DTW/EDR/LCSS bounds use the reference's local arithmetic and reduction
order. Spectral NCC and ERP sum bounds are useful real-arithmetic bounds but
are deliberately priority-only until an implementation-specific rounding
analysis is available. An empirical epsilon is not a search certificate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import fft

from . import similarity_methods as sm
from .metrics import EPS


@dataclass(frozen=True)
class SearchBound:
    value: float
    certified: bool
    kind: str
    reason: str = ""


def _pair(x: Any, y: Any, params: dict[str, Any]):
    return sm._prepare_elastic_pair(x, y, mode=params.get("mode", "exact"))[:2]


def _finite_arithmetic(a: np.ndarray, b: np.ndarray) -> bool:
    # Outside this conservative range, delegate to the complete reference.
    # This avoids claiming a numeric inequality for reference NaN/overflow.
    limit = np.sqrt(np.finfo(float).max) / (4.0 * max(1, a.shape[1]))
    return bool(
        a.size and b.size and np.all(np.isfinite(a)) and np.all(np.isfinite(b))
        and np.max(np.abs(a)) <= limit and np.max(np.abs(b)) <= limit
    )


def _cost(row: np.ndarray, other: np.ndarray) -> float:
    # The public DTW uses _row_l2_distances, not np.linalg.norm's dot path.
    return float(sm._row_l2_distances(row, other.reshape(1, -1))[0])


def _ordered_sum(values: np.ndarray) -> float:
    # Never use np.sum here: the DP accumulates along a path sequentially.
    total = 0.0
    for value in values:
        total = total + float(value)
    return total


def dtw_endpoint_bound(
    x: Any, y: Any, *, window: int | None = None, normalize: bool = False,
) -> SearchBound:
    a, b = _pair(x, y, {})
    sm._resolved_window(len(a), len(b), window, "exact")
    if not _finite_arithmetic(a, b):
        return SearchBound(0.0, True, "dtw_endpoints", "degenerate arithmetic: trivial bound")
    value = _cost(a[0], b[0])
    if len(a) != 1 or len(b) != 1:
        value = value + _cost(a[-1], b[-1])
    if normalize:
        value = value / (len(a) + len(b))
    return SearchBound(value, True, "dtw_endpoints")


def _box_deltas(a: np.ndarray, b: np.ndarray, width: int | None) -> np.ndarray:
    """Distance to the exact clipped interval envelope, without row loops.

    Callers supply finite paired matrices and a resolved nonnegative width.
    Min/max filters only select existing float64 values, so they preserve the
    row-local envelope used by the bound's floating-point monotonicity proof.
    """
    if width is not None and not len(b):
        return np.zeros_like(a)
    if width is None or width >= max(len(a), len(b)) - 1:
        low, high = np.min(b, axis=0), np.max(b, axis=0)
        return np.maximum(np.maximum(low - a, a - high), 0.0)
    from scipy.ndimage import maximum_filter1d, minimum_filter1d

    # When a is longer, an envelope is needed beyond b's final row.  Padding
    # with +/-infinity makes those windows identical to clipping at len(b).
    if len(a) > len(b):
        low_input = np.full_like(a, np.inf)
        high_input = np.full_like(a, -np.inf)
        low_input[:len(b)] = b
        high_input[:len(b)] = b
    else:
        low_input = high_input = b
    size = 2 * width + 1
    low = minimum_filter1d(low_input, size=size, axis=0, mode="constant", cval=np.inf)[:len(a)]
    high = maximum_filter1d(high_input, size=size, axis=0, mode="constant", cval=-np.inf)[:len(a)]
    deltas = np.maximum(np.maximum(low - a, a - high), 0.0)
    # A resolved width normally makes every row reachable.  Preserve the old
    # zero fallback even when this private helper receives a narrower width.
    if len(b) + width < len(a):
        deltas[len(b) + width:] = 0.0
    return deltas


def _keogh_direction(a: np.ndarray, b: np.ndarray, width: int | None) -> float:
    delta = _box_deltas(a, b, width)
    costs = delta[:, 0] if a.shape[1] == 1 else np.sqrt(np.sum(delta * delta, axis=1))
    return _ordered_sum(costs)


def dtw_keogh_bound(
    x: Any, y: Any, *, window: int | None = None, normalize: bool = False,
    bidirectional: bool = True,
) -> SearchBound:
    """Ordered, L1/row-L2 Keogh bound for the audited DTW recurrence.

    Each box coordinate is no larger than the corresponding absolute local
    difference. The nonnegative square/sum/sqrt operations are monotone and
    use the same row reduction as the reference. A path visits every row in
    order; inserting extra nonnegative costs cannot lower an IEEE round-to-
    nearest sum. The sequential bound sum is therefore below every path sum.
    This argument also applies to the transposed direction; use max, not sum.
    """
    a, b = _pair(x, y, {})
    width = sm._resolved_window(len(a), len(b), window, "exact")
    if not _finite_arithmetic(a, b):
        return SearchBound(0.0, True, "dtw_keogh", "degenerate arithmetic: trivial bound")
    value = _keogh_direction(a, b, width)
    if bidirectional:
        value = max(value, _keogh_direction(b, a, width))
    if not np.isfinite(value):
        value = 0.0
    if normalize:
        value = value / (len(a) + len(b))
    return SearchBound(value, True, "dtw_keogh")


def match_envelope_bound(
    x: Any, y: Any, *, metric: str, epsilon: float = 1.0,
    window: int | None = None, mode: str = "exact", normalized: bool = True,
) -> SearchBound:
    """Integer match counts, using the reference's squared multi-channel test."""
    if metric not in {"lcss", "lcss_similarity", "edr"}:
        raise ValueError("match envelope supports lcss, lcss_similarity and edr")
    epsilon = sm._nonnegative_parameter("epsilon", epsilon)
    a, b = _pair(x, y, {"mode": mode})
    width = sm._resolved_window(len(a), len(b), window, mode)
    if not _finite_arithmetic(a, b):
        return SearchBound(1.0 if metric == "lcss_similarity" else 0.0, True, "match_envelope")
    def possible(left, right):
        delta = _box_deltas(left, right, width)
        if left.shape[1] == 1:
            return int(np.count_nonzero(delta[:, 0] <= epsilon))
        with np.errstate(over="ignore"):
            return int(np.count_nonzero(np.sum(delta * delta, axis=1) <= epsilon * epsilon))
    na, nb = possible(a, b), possible(b, a)
    if metric in {"lcss", "lcss_similarity"}:
        upper = float(min(na, nb) / min(len(a), len(b)))
        value = upper if metric == "lcss_similarity" else float(1.0 - upper)
    else:
        value = float(max(len(a) - na, len(b) - nb, abs(len(a) - len(b))))
        if normalized:
            value = value / max(len(a), len(b))
    return SearchBound(value, True, "match_envelope")


def erp_sum_bound(x: Any, y: Any, *, gap_value: Any = 0.0, mode: str = "exact", **_: Any) -> SearchBound:
    a, b = _pair(x, y, {"mode": mode})
    if not _finite_arithmetic(a, b):
        return SearchBound(0.0, False, "erp_sum", "priority only")
    gap = sm._erp_gap(gap_value, a.shape[1])
    value = abs(
        float(np.sum(sm._pointwise_l2_to_reference(a, gap)))
        - float(np.sum(sm._pointwise_l2_to_reference(b, gap)))
    )
    return SearchBound(value if np.isfinite(value) else 0.0, False, "erp_sum", "rounding not certified")


def ncc_spectral_bound(
    x: Any, y: Any, *, metric: str = "sbd", normalize: bool = True,
    n_coeffs: int | None = None,
) -> SearchBound:
    """Amplitude-spectrum bound, suitable for ordering/approximate retrieval.

    FFT error is implementation-dependent. This function never grants a
    floating-point certificate, even if the real-arithmetic inequality holds.
    Odd FFT lengths have no Nyquist singleton: all non-DC half-spectrum bins
    then carry weight two.
    """
    a, b, _, _ = sm._pair_series(x, y)
    independent = metric.startswith("independent")
    if not len(a) or not len(b):
        return SearchBound(1.0 if metric.endswith("ncc") else 0.0, False, "ncc_spectral")
    length = fft.next_fast_len(len(a) + len(b) - 1, real=True)
    weights = np.full(length // 2 + 1, 2.0)
    weights[0] = 1.0
    if length % 2 == 0:
        weights[-1] = 1.0
    def vector(values):
        spectrum = np.abs(fft.rfft(values, n=length, axis=0)) * np.sqrt(weights)[:, None]
        if n_coeffs is not None:
            if isinstance(n_coeffs, bool) or int(n_coeffs) != n_coeffs or n_coeffs < 1:
                raise ValueError("n_coeffs must be a positive integer")
            kept = min(int(n_coeffs), len(spectrum))
            if kept < len(spectrum):
                spectrum = np.vstack((spectrum[:kept], np.linalg.norm(spectrum[kept:], axis=0)))
        return spectrum
    bounds = []
    groups = [(a[:, i:i+1], b[:, i:i+1]) for i in range(a.shape[1])] if independent else [(a, b)]
    for left, right in groups:
        left = sm._z_normalize(left) if normalize else left
        right = sm._z_normalize(right) if normalize else right
        if float(np.linalg.norm(left) * np.linalg.norm(right)) <= EPS:
            bounds.append(0.0)
            continue
        fa, fb = vector(left).ravel(), vector(right).ravel()
        denom = float(np.linalg.norm(fa) * np.linalg.norm(fb))
        upper = float(np.dot(fa, fb) / denom) if denom > 0 else 1.0
        bounds.append(float(np.clip(upper, 0.0, 1.0)))
    upper = float(np.mean(bounds))
    value = upper if metric.endswith("ncc") else float(1.0 - upper)
    return SearchBound(value, False, "ncc_spectral", "FFT rounding not certified")


def component_upper_bound(components: dict[str, float], *, target: str = "similarity_score") -> float:
    """Max of the two possible DTW validity branches, in reference arithmetic.

    Fill unknown DTW with 1 for the valid branch and NaN for the invalid branch.
    Each valid branch is monotone in this one unknown component and retains
    exactly the reference's addition/division order. This avoids an empirical
    epsilon and handles weight renormalisation explicitly.
    """
    from .similarity import score_from_components
    if target not in {"similarity_score", "component_mean"}:
        raise ValueError("target must be similarity_score or component_mean")
    full = dict(components)
    outputs = []
    for value in (1.0, float("nan")):
        full["dtw_similarity"] = value
        score = score_from_components(full)
        # The helper's result is a SimilarityScore (see similarity.py).
        result = getattr(score, target, None)
        if result is None and isinstance(score, dict):
            result = score[target]
        if result is None:
            # Tuple compatibility is deliberately not implicit.
            raise TypeError("score_from_components must expose the requested score")
        if np.isfinite(result):
            outputs.append(float(result))
    return max(outputs) if outputs else float("nan")


__all__ = [
    "SearchBound", "dtw_endpoint_bound", "dtw_keogh_bound", "match_envelope_bound",
    "erp_sum_bound", "ncc_spectral_bound", "component_upper_bound",
]

