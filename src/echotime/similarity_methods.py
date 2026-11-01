"""Low-level similarity methods that complement EchoTime's report surface."""

from __future__ import annotations

from itertools import permutations
from operator import index
from typing import Any, Literal

import numpy as np

from . import _native
from .metrics import EPS

_FAST_MODE_MAX_POINTS = 512
_FAST_MODE_BAND_RATIO = 0.10


def _to_time_series(data: Any) -> np.ndarray:
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 0:
        raise ValueError("A time series must contain at least one value.")
    if arr.ndim == 1:
        return arr.reshape(-1, 1)
    if arr.ndim == 2:
        if arr.shape[1] > arr.shape[0] and arr.shape[0] <= 16:
            return arr.T
        return arr
    raise ValueError("Time series inputs must be 1D or 2D.")


def _clean_series(values: np.ndarray, timestamps: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | None]:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 2:
        arr = _to_time_series(arr)
    mask = np.all(np.isfinite(arr), axis=1)
    clean = arr[mask]
    if timestamps is None:
        return clean, None
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    if ts.size != arr.shape[0]:
        raise ValueError("timestamps must match the time dimension of the input series.")
    clean_ts = ts[mask]
    if not np.all(np.isfinite(clean_ts)):
        raise ValueError("timestamps must be finite at every retained observation.")
    if np.any(np.diff(clean_ts) <= 0):
        raise ValueError("timestamps must be strictly increasing after removing nonfinite observations.")
    return clean, clean_ts


def _pair_series(
    left: Any,
    right: Any,
    *,
    left_timestamps: Any | None = None,
    right_timestamps: Any | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None]:
    left_arr, left_ts = _clean_series(_to_time_series(left), None if left_timestamps is None else np.asarray(left_timestamps, dtype=float))
    right_arr, right_ts = _clean_series(_to_time_series(right), None if right_timestamps is None else np.asarray(right_timestamps, dtype=float))
    if left_arr.shape[1] != right_arr.shape[1]:
        left_arr = np.nanmean(left_arr, axis=1, keepdims=True)
        right_arr = np.nanmean(right_arr, axis=1, keepdims=True)
    return left_arr, right_arr, left_ts, right_ts


def _z_normalize(x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=float)
    mean = np.mean(arr, axis=0, keepdims=True)
    std = np.std(arr, axis=0, keepdims=True)
    std = np.where(std <= EPS, 1.0, std)
    return (arr - mean) / std


def _local_l2(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def _validate_mode(mode: Literal["exact", "fast"] | str) -> Literal["exact", "fast"]:
    if mode not in {"exact", "fast"}:
        raise ValueError("mode must be 'exact' or 'fast'.")
    return mode


def _nonnegative_parameter(name: str, value: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be finite and nonnegative.") from None
    if not np.isfinite(result) or result < 0:
        raise ValueError(f"{name} must be finite and nonnegative.")
    return result


def _resolved_window(n: int, m: int, window: int | None, mode: Literal["exact", "fast"]) -> int | None:
    if window is None:
        if mode == "exact":
            return None
        window = int(np.ceil(_FAST_MODE_BAND_RATIO * max(n, m)))
    else:
        if isinstance(window, (bool, np.bool_)):
            raise ValueError("window must be a nonnegative integer or None.")
        try:
            window = index(window)
        except TypeError:
            raise ValueError("window must be a nonnegative integer or None.") from None
        if window < 0:
            raise ValueError("window must be a nonnegative integer or None.")
    return max(window, abs(n - m))


def _resample_series(
    values: np.ndarray,
    *,
    max_points: int,
    timestamps: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray | None]:
    if len(values) <= max_points:
        return values, timestamps
    old_grid = np.linspace(0.0, 1.0, len(values), dtype=float)
    new_grid = np.linspace(0.0, 1.0, max_points, dtype=float)
    out = np.empty((max_points, values.shape[1]), dtype=float)
    for dim in range(values.shape[1]):
        out[:, dim] = np.interp(new_grid, old_grid, values[:, dim])
    if timestamps is None:
        return out, None
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    return out, np.interp(new_grid, old_grid, ts)


def _prepare_elastic_pair(
    left: Any,
    right: Any,
    *,
    mode: Literal["exact", "fast"] | str,
    left_timestamps: Any | None = None,
    right_timestamps: Any | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None, Literal["exact", "fast"]]:
    resolved_mode = _validate_mode(mode)
    left_arr, right_arr, left_ts, right_ts = _pair_series(
        left,
        right,
        left_timestamps=left_timestamps,
        right_timestamps=right_timestamps,
    )
    if resolved_mode == "fast":
        left_arr, left_ts = _resample_series(left_arr, max_points=_FAST_MODE_MAX_POINTS, timestamps=left_ts)
        right_arr, right_ts = _resample_series(right_arr, max_points=_FAST_MODE_MAX_POINTS, timestamps=right_ts)
    return left_arr, right_arr, left_ts, right_ts, resolved_mode


def _to_univariate_series(data: Any) -> np.ndarray:
    arr, _ = _clean_series(_to_time_series(data))
    if arr.shape[1] != 1:
        raise ValueError("This method currently supports univariate series only.")
    return arr[:, 0]


def _row_match_mask(row: np.ndarray, candidates: np.ndarray, epsilon: float) -> np.ndarray:
    if candidates.size == 0:
        return np.zeros(0, dtype=bool)
    if row.size == 1:
        return np.abs(candidates[:, 0] - float(row[0])) <= epsilon
    diff = candidates - row[None, :]
    return np.sum(diff * diff, axis=1) <= epsilon * epsilon


def _row_l2_distances(row: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    if candidates.size == 0:
        return np.zeros(0, dtype=float)
    if row.size == 1:
        return np.abs(candidates[:, 0] - float(row[0]))
    diff = candidates - row[None, :]
    return np.sqrt(np.sum(diff * diff, axis=1))


def _pointwise_l2_to_reference(values: np.ndarray, ref: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return np.zeros(0, dtype=float)
    if values.shape[1] == 1:
        return np.abs(values[:, 0] - float(ref[0]))
    diff = values - ref[None, :]
    return np.sqrt(np.sum(diff * diff, axis=1))


def _previous_rows(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values.copy()
    zero = np.zeros((1, values.shape[1]), dtype=float)
    return np.vstack([zero, values[:-1]])


def _consecutive_l2_costs(values: np.ndarray, previous: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return np.zeros(0, dtype=float)
    if values.shape[1] == 1:
        return np.abs(values[:, 0] - previous[:, 0])
    diff = values - previous
    return np.sqrt(np.sum(diff * diff, axis=1))


def _autocorrelation_vector(x: np.ndarray, max_lag: int) -> np.ndarray:
    series = np.asarray(x, dtype=float).reshape(-1)
    series = series[np.isfinite(series)]
    if series.size < 2 or max_lag <= 0:
        return np.zeros(max_lag, dtype=float)
    centered = series - float(np.mean(series))
    variance = float(np.var(centered))
    if variance <= EPS:
        return np.zeros(max_lag, dtype=float)
    out = np.zeros(max_lag, dtype=float)
    for lag in range(1, max_lag + 1):
        if lag >= series.size:
            break
        out[lag - 1] = float(np.dot(centered[:-lag], centered[lag:]) / ((series.size - lag) * variance))
    return out


def ncc_sequence(x: Any, y: Any, *, normalize: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Return shift-wise correlation using a single joint channel normalization.

    Channels share one lag. With nonzero energy, an identical input has a
    zero-lag value of one regardless of the channel count. If either input
    has zero energy after optional z-normalization, the existing zero-score
    convention is retained; a correlation of a constant signal is undefined.
    """
    left, right, _, _ = _pair_series(x, y)
    if not len(left) or not len(right):
        return np.asarray([], dtype=float), np.asarray([], dtype=int)
    xs = _z_normalize(left) if normalize else left
    ys = _z_normalize(right) if normalize else right
    corr = None
    for dim in range(xs.shape[1]):
        current = np.correlate(xs[:, dim], ys[:, dim], mode="full")
        corr = current if corr is None else corr + current
    assert corr is not None
    denom = float(np.linalg.norm(xs) * np.linalg.norm(ys))
    if denom <= EPS:
        ncc = np.zeros_like(corr, dtype=float)
    else:
        ncc = np.clip(corr / denom, -1.0, 1.0)
    lags = np.arange(-(len(ys) - 1), len(xs), dtype=int)
    return ncc.astype(float), lags


def max_ncc(x: Any, y: Any, *, normalize: bool = True) -> float:
    values, _ = ncc_sequence(x, y, normalize=normalize)
    if values.size == 0:
        return float("nan")
    return float(np.max(values))


def best_shift(x: Any, y: Any, *, normalize: bool = True) -> int:
    values, lags = ncc_sequence(x, y, normalize=normalize)
    if values.size == 0:
        return 0
    return int(lags[int(np.argmax(values))])


def sbd(x: Any, y: Any, *, normalize: bool = True) -> float:
    value = max_ncc(x, y, normalize=normalize)
    if not np.isfinite(value):
        return float("nan")
    return float(1.0 - value)


def independent_max_ncc(x: Any, y: Any, *, normalize: bool = True) -> float:
    left, right, _, _ = _pair_series(x, y)
    if left.shape[1] == 0:
        return float("nan")
    values = [
        max_ncc(left[:, dim], right[:, dim], normalize=normalize)
        for dim in range(left.shape[1])
    ]
    finite = [value for value in values if np.isfinite(value)]
    if not finite:
        return float("nan")
    return float(np.mean(finite))


def independent_sbd(x: Any, y: Any, *, normalize: bool = True) -> float:
    value = independent_max_ncc(x, y, normalize=normalize)
    if not np.isfinite(value):
        return float("nan")
    return float(1.0 - value)


def acf_distance(x: Any, y: Any, *, max_lag: int = 10) -> float:
    left, right, _, _ = _pair_series(x, y)
    if max_lag <= 0:
        raise ValueError("max_lag must be positive.")
    distances = []
    for dim in range(left.shape[1]):
        ax = _autocorrelation_vector(left[:, dim], max_lag=max_lag)
        ay = _autocorrelation_vector(right[:, dim], max_lag=max_lag)
        distances.append(float(np.linalg.norm(ax - ay)))
    if not distances:
        return float("nan")
    return float(np.mean(distances))


def _periodogram_embedding(x: np.ndarray, *, n_coeffs: int = 32, normalize: bool = True) -> np.ndarray:
    parts = []
    for dim in range(x.shape[1]):
        power = np.abs(np.fft.rfft(x[:, dim])) ** 2
        if normalize and float(np.sum(power)) > EPS:
            power = power / float(np.sum(power))
        keep = min(n_coeffs, len(power))
        parts.append(power[:keep])
        if keep < n_coeffs:
            parts.append(np.zeros(n_coeffs - keep, dtype=float))
    return np.concatenate(parts).astype(float)


def periodogram_distance(x: Any, y: Any, *, n_coeffs: int = 32) -> float:
    left, right, _, _ = _pair_series(x, y)
    if len(left) == 0 or len(right) == 0:
        return float("nan")
    ex = _periodogram_embedding(left, n_coeffs=n_coeffs, normalize=True)
    ey = _periodogram_embedding(right, n_coeffs=n_coeffs, normalize=True)
    return float(np.linalg.norm(ex - ey))


def _trend_feature_vector(x: np.ndarray) -> np.ndarray:
    t = np.arange(len(x), dtype=float)
    feats = []
    for dim in range(x.shape[1]):
        values = x[:, dim]
        if len(values) < 2:
            feats.extend([float(values[0]) if len(values) else 0.0, 0.0, 0.0])
            continue
        slope, intercept = np.polyfit(t, values, 1)
        pred = slope * t + intercept
        feats.extend([float(intercept), float(slope), float(np.std(values - pred))])
    return np.asarray(feats, dtype=float)


def trend_distance(x: Any, y: Any) -> float:
    left, right, _, _ = _pair_series(x, y)
    if len(left) == 0 or len(right) == 0:
        return float("nan")
    return float(np.linalg.norm(_trend_feature_vector(left) - _trend_feature_vector(right)))


def _ordinal_pattern_distribution(x: Any, *, order: int = 3, delay: int = 1) -> np.ndarray:
    values = _to_univariate_series(x)
    if order < 2 or delay < 1:
        raise ValueError("order must be >= 2 and delay must be >= 1.")
    n_vectors = len(values) - (order - 1) * delay
    patterns = list(permutations(range(order)))
    counts = np.zeros(len(patterns), dtype=float)
    if n_vectors <= 0:
        return counts
    # Vectorised form of counting tuple(np.argsort(window, kind="mergesort"))
    # per window: the same stable sort per row, mapped to the index of that
    # permutation in itertools.permutations order (which is ascending in the
    # base-``order`` code), so the counts are identical.
    starts = np.arange(n_vectors)[:, None] + delay * np.arange(order)[None, :]
    ranks = np.argsort(values[starts], axis=1, kind="mergesort")
    weights = order ** np.arange(order - 1, -1, -1, dtype=np.int64)
    pattern_codes = np.asarray(patterns, dtype=np.int64) @ weights
    positions = np.searchsorted(pattern_codes, ranks.astype(np.int64) @ weights)
    counts += np.bincount(positions, minlength=len(patterns)).astype(float)
    if float(np.sum(counts)) > EPS:
        counts = counts / float(np.sum(counts))
    return counts


def _jensen_shannon_distance(p: np.ndarray, q: np.ndarray) -> float:
    if p.shape != q.shape:
        raise ValueError("Jensen-Shannon distance requires equal-length vectors.")
    if np.any(p < 0) or np.any(q < 0):
        raise ValueError("Jensen-Shannon distance requires nonnegative inputs.")
    px = p / float(np.sum(p) if float(np.sum(p)) > EPS else 1.0)
    py = q / float(np.sum(q) if float(np.sum(q)) > EPS else 1.0)
    m = 0.5 * (px + py)
    def _kl(a: np.ndarray, b: np.ndarray) -> float:
        mask = a > EPS
        return float(np.sum(a[mask] * np.log(a[mask] / b[mask])))
    js_div = 0.5 * _kl(px, m) + 0.5 * _kl(py, m)
    return float(np.sqrt(max(js_div, 0.0)))


def ordinal_pattern_js_distance(x: Any, y: Any, *, order: int = 3, delay: int = 1) -> float:
    px = _ordinal_pattern_distribution(x, order=order, delay=delay)
    py = _ordinal_pattern_distribution(y, order=order, delay=delay)
    return _jensen_shannon_distance(px, py)


def _linear_trend_parameters(x: np.ndarray) -> np.ndarray:
    t = np.arange(len(x), dtype=float)
    if len(x) < 2:
        return np.array([float(x[0]) if len(x) else 0.0, 0.0, 0.0], dtype=float)
    slope, intercept = np.polyfit(t, x, 1)
    pred = slope * t + intercept
    resid = np.std(x - pred)
    return np.array([float(intercept), float(slope), float(resid)], dtype=float)


def linear_trend_model_distance(x: Any, y: Any) -> float:
    left = _to_univariate_series(x)
    right = _to_univariate_series(y)
    return float(np.linalg.norm(_linear_trend_parameters(left) - _linear_trend_parameters(right)))


def _window_bounds(i: int, m: int, window: int | None) -> tuple[int, int]:
    if window is None:
        return 1, m + 1
    return max(1, i - window), min(m, i + window) + 1


def _match(a: np.ndarray, b: np.ndarray, epsilon: float) -> bool:
    return _local_l2(a, b) <= epsilon


# ---------------------------------------------------------------------------
# Elastic distances. Each public function prepares the pair exactly as before,
# then runs the dynamic programme either in the compiled kernel or in the
# pure-Python reference loop below (``_*_dp_python``), which defines the
# numbers. The native kernels reproduce the reference bit for bit.
# ---------------------------------------------------------------------------


def _bank(arrays: list[np.ndarray], d: int) -> tuple[np.ndarray, np.ndarray]:
    offsets = np.zeros(len(arrays) + 1, dtype=np.int64)
    if arrays:
        offsets[1:] = np.cumsum([len(a) for a in arrays])
    if offsets[-1]:
        values = np.concatenate([np.asarray(a, dtype=float).reshape(-1, d) for a in arrays], axis=0)
    else:
        values = np.zeros((0, d), dtype=float)
    return np.ascontiguousarray(values, dtype=float), offsets


def _rows(arrays: list[np.ndarray]) -> np.ndarray:
    if not arrays:
        return np.zeros(0, dtype=float)
    return np.ascontiguousarray(np.concatenate([np.asarray(a, dtype=float).reshape(-1) for a in arrays]), dtype=float)


def _native_window(window: int | None) -> int:
    return -1 if window is None else int(window)


_ONE = np.zeros(1, dtype=np.int64)


def _lcss_dp_python(left: np.ndarray, right: np.ndarray, epsilon: float, resolved_window: int | None) -> float:
    n, m = len(left), len(right)
    prev = np.zeros(m + 1, dtype=float)
    curr = np.zeros(m + 1, dtype=float)
    for i in range(1, n + 1):
        curr.fill(0.0)
        j_start, j_end = _window_bounds(i, m, resolved_window)
        matches = _row_match_mask(left[i - 1], right[j_start - 1 : j_end - 1], epsilon)
        for j in range(j_start, j_end):
            if matches[j - j_start]:
                curr[j] = prev[j - 1] + 1.0
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, prev
    return float(prev[m] / max(1, min(n, m)))


def _lcss_dp(left: np.ndarray, right: np.ndarray, epsilon: float, resolved_window: int | None) -> float:
    if _native.use_native():
        va, oa = _bank([left], left.shape[1])
        vb, ob = _bank([right], right.shape[1])
        out = _native.ext().lcss_pairs(va, oa, vb, ob, _ONE, _ONE, float(epsilon), _native_window(resolved_window), False, 1)
        return float(out[0])
    return _lcss_dp_python(left, right, epsilon, resolved_window)


def lcss_similarity(
    x: Any,
    y: Any,
    *,
    epsilon: float = 1.0,
    window: int | None = None,
    mode: Literal["exact", "fast"] = "exact",
) -> float:
    epsilon = _nonnegative_parameter("epsilon", epsilon)
    left, right, _, _, resolved_mode = _prepare_elastic_pair(x, y, mode=mode)
    n, m = len(left), len(right)
    if n == 0 or m == 0:
        return float("nan")
    resolved_window = _resolved_window(n, m, window, resolved_mode)
    return _lcss_dp(left, right, epsilon, resolved_window)


def lcss_distance(
    x: Any,
    y: Any,
    *,
    epsilon: float = 1.0,
    window: int | None = None,
    mode: Literal["exact", "fast"] = "exact",
) -> float:
    similarity = lcss_similarity(x, y, epsilon=epsilon, window=window, mode=mode)
    if not np.isfinite(similarity):
        return float("nan")
    return float(1.0 - similarity)


def _edr_dp_python(left: np.ndarray, right: np.ndarray, epsilon: float, normalized: bool, resolved_window: int | None) -> float:
    n, m = len(left), len(right)
    prev = np.arange(m + 1, dtype=float)
    curr = np.full(m + 1, np.inf, dtype=float)
    for i in range(1, n + 1):
        curr.fill(np.inf)
        curr[0] = float(i)
        j_start, j_end = _window_bounds(i, m, resolved_window)
        matches = _row_match_mask(left[i - 1], right[j_start - 1 : j_end - 1], epsilon)
        for j in range(j_start, j_end):
            sub = 0.0 if matches[j - j_start] else 1.0
            curr[j] = min(prev[j] + 1.0, curr[j - 1] + 1.0, prev[j - 1] + sub)
        prev, curr = curr, prev
    value = float(prev[m])
    if normalized:
        value /= max(1, max(n, m))
    return value


def _edr_dp(left: np.ndarray, right: np.ndarray, epsilon: float, normalized: bool, resolved_window: int | None) -> float:
    if _native.use_native():
        va, oa = _bank([left], left.shape[1])
        vb, ob = _bank([right], right.shape[1])
        out = _native.ext().edr_pairs(va, oa, vb, ob, _ONE, _ONE, float(epsilon), bool(normalized), _native_window(resolved_window), False, 1)
        return float(out[0])
    return _edr_dp_python(left, right, epsilon, normalized, resolved_window)


def edr_distance(
    x: Any,
    y: Any,
    *,
    epsilon: float = 1.0,
    normalized: bool = True,
    window: int | None = None,
    mode: Literal["exact", "fast"] = "exact",
) -> float:
    epsilon = _nonnegative_parameter("epsilon", epsilon)
    left, right, _, _, resolved_mode = _prepare_elastic_pair(x, y, mode=mode)
    n, m = len(left), len(right)
    if n == 0 or m == 0:
        return float("nan")
    resolved_window = _resolved_window(n, m, window, resolved_mode)
    return _edr_dp(left, right, epsilon, normalized, resolved_window)


def _erp_gap(gap_value: float | np.ndarray, d: int) -> np.ndarray:
    gap = np.asarray(gap_value, dtype=float)
    if gap.ndim == 0:
        gap = np.full(d, float(gap))
    if gap.shape != (d,):
        raise ValueError(f"gap_value must broadcast to shape {(d,)}.")
    if not np.all(np.isfinite(gap)):
        raise ValueError("gap_value must be finite.")
    return gap


def _erp_dp_python(
    left: np.ndarray,
    right: np.ndarray,
    left_gap_costs: np.ndarray,
    right_gap_costs: np.ndarray,
    resolved_window: int | None,
) -> float:
    n, m = len(left), len(right)
    prev = np.full(m + 1, np.inf, dtype=float)
    curr = np.full(m + 1, np.inf, dtype=float)
    prev[0] = 0.0
    for j in range(1, m + 1):
        prev[j] = prev[j - 1] + right_gap_costs[j - 1]
    for i in range(1, n + 1):
        curr.fill(np.inf)
        curr[0] = prev[0] + left_gap_costs[i - 1]
        j_start, j_end = _window_bounds(i, m, resolved_window)
        pair_costs = _row_l2_distances(left[i - 1], right[j_start - 1 : j_end - 1])
        for j in range(j_start, j_end):
            curr[j] = min(
                prev[j - 1] + pair_costs[j - j_start],
                prev[j] + left_gap_costs[i - 1],
                curr[j - 1] + right_gap_costs[j - 1],
            )
        prev, curr = curr, prev
    return float(prev[m])


def _erp_dp(
    left: np.ndarray,
    right: np.ndarray,
    left_gap_costs: np.ndarray,
    right_gap_costs: np.ndarray,
    resolved_window: int | None,
) -> float:
    if _native.use_native():
        va, oa = _bank([left], left.shape[1])
        vb, ob = _bank([right], right.shape[1])
        out = _native.ext().erp_pairs(
            va, oa, _rows([left_gap_costs]), vb, ob, _rows([right_gap_costs]), _ONE, _ONE, _native_window(resolved_window), False, 1
        )
        return float(out[0])
    return _erp_dp_python(left, right, left_gap_costs, right_gap_costs, resolved_window)


def erp_distance(
    x: Any,
    y: Any,
    *,
    gap_value: float | np.ndarray = 0.0,
    window: int | None = None,
    mode: Literal["exact", "fast"] = "exact",
) -> float:
    left, right, _, _, resolved_mode = _prepare_elastic_pair(x, y, mode=mode)
    n, m = len(left), len(right)
    if n == 0 or m == 0:
        return float("nan")
    resolved_window = _resolved_window(n, m, window, resolved_mode)
    gap = _erp_gap(gap_value, left.shape[1])
    left_gap_costs = _pointwise_l2_to_reference(left, gap)
    right_gap_costs = _pointwise_l2_to_reference(right, gap)
    return _erp_dp(left, right, left_gap_costs, right_gap_costs, resolved_window)


def _twed_side(values: np.ndarray, timestamps: np.ndarray | None, *, lambda_: float, nu: float) -> tuple[np.ndarray, ...]:
    """Per-series TWED terms: (values, previous rows, t, previous t, delete costs)."""

    n = len(values)
    t = np.arange(1, n + 1, dtype=float) if timestamps is None else np.asarray(timestamps, dtype=float).reshape(-1)
    if t.size != n:
        raise ValueError("Timestamp arrays must match the cleaned series lengths.")
    prev_rows = _previous_rows(values)
    prev_t = np.concatenate([[0.0], t[:-1]])
    delete_costs = _consecutive_l2_costs(values, prev_rows) + nu * np.abs(t - prev_t) + lambda_
    return values, prev_rows, t, prev_t, delete_costs


def _twed_dp_python(left_side: tuple[np.ndarray, ...], right_side: tuple[np.ndarray, ...], nu: float, resolved_window: int | None) -> float:
    left, left_prev, tx, left_prev_ts, left_delete_costs = left_side
    right, right_prev, ty, right_prev_ts, right_delete_costs = right_side
    n, m = len(left), len(right)
    prev = np.full(m + 1, np.inf, dtype=float)
    curr = np.full(m + 1, np.inf, dtype=float)
    prev[0] = 0.0
    for i in range(1, n + 1):
        curr.fill(np.inf)
        xi = left[i - 1]
        xim1 = left_prev[i - 1]
        ti = tx[i - 1]
        tim1 = left_prev_ts[i - 1]
        j_start, j_end = _window_bounds(i, m, resolved_window)
        pair_costs = _row_l2_distances(xi, right[j_start - 1 : j_end - 1])
        pair_prev_costs = _row_l2_distances(xim1, right_prev[j_start - 1 : j_end - 1])
        time_costs = nu * (
            np.abs(ti - ty[j_start - 1 : j_end - 1])
            + np.abs(tim1 - right_prev_ts[j_start - 1 : j_end - 1])
        )
        for j in range(j_start, j_end):
            curr[j] = min(
                prev[j] + left_delete_costs[i - 1],
                curr[j - 1] + right_delete_costs[j - 1],
                prev[j - 1] + pair_costs[j - j_start] + pair_prev_costs[j - j_start] + time_costs[j - j_start],
            )
        prev, curr = curr, prev
    return float(prev[m])


def _twed_dp(left_side: tuple[np.ndarray, ...], right_side: tuple[np.ndarray, ...], nu: float, resolved_window: int | None) -> float:
    if _native.use_native():
        d = left_side[0].shape[1]
        va, oa = _bank([left_side[0]], d)
        pva, _ = _bank([left_side[1]], d)
        vb, ob = _bank([right_side[0]], d)
        pvb, _ = _bank([right_side[1]], d)
        out = _native.ext().twed_pairs(
            va, pva, oa, _rows([left_side[2]]), _rows([left_side[3]]), _rows([left_side[4]]),
            vb, pvb, ob, _rows([right_side[2]]), _rows([right_side[3]]), _rows([right_side[4]]),
            _ONE, _ONE, float(nu), _native_window(resolved_window), False, 1,
        )
        return float(out[0])
    return _twed_dp_python(left_side, right_side, nu, resolved_window)


def twed_distance(
    x: Any,
    y: Any,
    *,
    lambda_: float = 1.0,
    nu: float = 0.001,
    t_x: Any | None = None,
    t_y: Any | None = None,
    window: int | None = None,
    mode: Literal["exact", "fast"] = "exact",
) -> float:
    """Compute TWED with the zero sentinel and infinite DP boundary.

    ``lambda_`` and ``nu`` must be finite and nonnegative. The metric claim
    from the original TWED definition requires positive ``nu``; ``nu=0`` is
    accepted as a nonmetric boundary case. Supplied timestamps must be finite
    and strictly increasing at retained observations. Both series use the
    same zero-time, zero-value sentinel, without separately shifting origins.

    Nonfinite observation rows are dropped. Supply timestamps to preserve
    elapsed time across such gaps. ``mode="fast"`` interpolates each series
    to at most 512 samples and applies a path band: it is an approximation,
    with no guaranteed error or retrieval-recall bound.
    """
    lambda_ = _nonnegative_parameter("lambda_", lambda_)
    nu = _nonnegative_parameter("nu", nu)
    left, right, left_ts, right_ts, resolved_mode = _prepare_elastic_pair(
        x,
        y,
        mode=mode,
        left_timestamps=t_x,
        right_timestamps=t_y,
    )
    n, m = len(left), len(right)
    if n == 0 or m == 0:
        return float("nan")
    resolved_window = _resolved_window(n, m, window, resolved_mode)
    left_side = _twed_side(left, left_ts, lambda_=lambda_, nu=nu)
    right_side = _twed_side(right, right_ts, lambda_=lambda_, nu=nu)
    return _twed_dp(left_side, right_side, nu, resolved_window)


def _dtw_dp_python(left: np.ndarray, right: np.ndarray, resolved_window: int | None) -> float:
    n, m = len(left), len(right)
    prev = np.full(m + 1, np.inf, dtype=float)
    curr = np.full(m + 1, np.inf, dtype=float)
    prev[0] = 0.0
    for i in range(1, n + 1):
        curr.fill(np.inf)
        j_start, j_end = _window_bounds(i, m, resolved_window)
        costs = _row_l2_distances(left[i - 1], right[j_start - 1 : j_end - 1])
        for j in range(j_start, j_end):
            curr[j] = costs[j - j_start] + min(prev[j], curr[j - 1], prev[j - 1])
        prev, curr = curr, prev
    return float(prev[m])


def _dtw_dp(left: np.ndarray, right: np.ndarray, resolved_window: int | None) -> float:
    if _native.use_native():
        va, oa = _bank([left], left.shape[1])
        vb, ob = _bank([right], right.shape[1])
        out = _native.ext().dtw_pairs(va, oa, vb, ob, _ONE, _ONE, _native_window(resolved_window), 1)
        return float(out[0])
    return _dtw_dp_python(left, right, resolved_window)


def dtw_distance(
    x: Any,
    y: Any,
    *,
    window: int | None = None,
    normalize: bool = False,
) -> float:
    """Classic dynamic time warping with an optional Sakoe-Chiba band.

    Local cost is ``|x_i - y_j|`` for univariate inputs and the Euclidean
    distance between rows for multichannel inputs. ``D[i, j] = cost(i, j) +
    min(D[i-1, j], D[i, j-1], D[i-1, j-1])`` with no slope constraint. A
    ``window`` restricts the path to ``|i - j| <= max(window, |n - m|)`` (the
    widening guarantees a path for unequal lengths, as in the other elastic
    distances). ``normalize=True`` divides by ``n + m``. Nonfinite rows are
    dropped. For equal-length univariate inputs this equals NeuroTime's
    ``dtw_distance`` with the same ``window``.
    """
    left, right, _, _ = _pair_series(x, y)
    n, m = len(left), len(right)
    if n == 0 or m == 0:
        return float("nan")
    resolved_window = _resolved_window(n, m, window, "exact")
    value = _dtw_dp(left, right, resolved_window)
    if normalize:
        value /= n + m
    return float(value)




__all__ = [
    "ncc_sequence",
    "max_ncc",
    "best_shift",
    "sbd",
    "independent_max_ncc",
    "independent_sbd",
    "acf_distance",
    "periodogram_distance",
    "trend_distance",
    "ordinal_pattern_js_distance",
    "linear_trend_model_distance",
    "lcss_similarity",
    "lcss_distance",
    "edr_distance",
    "erp_distance",
    "twed_distance",
    "dtw_distance",
]
