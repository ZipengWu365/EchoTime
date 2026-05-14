"""Low-level similarity methods that complement EchoTime's report surface."""

from __future__ import annotations

from itertools import permutations
from typing import Any, Literal

import numpy as np

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
    return clean, ts[mask]


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


def _resolved_window(n: int, m: int, window: int | None, mode: Literal["exact", "fast"]) -> int | None:
    if window is None:
        if mode == "exact":
            return None
        window = int(np.ceil(_FAST_MODE_BAND_RATIO * max(n, m)))
    return max(int(window), abs(n - m))


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
    left, right, _, _ = _pair_series(x, y)
    xs = _z_normalize(left) if normalize else left
    ys = _z_normalize(right) if normalize else right
    corr = None
    for dim in range(xs.shape[1]):
        current = np.correlate(xs[:, dim], ys[:, dim], mode="full")
        corr = current if corr is None else corr + current
    assert corr is not None
    corr = corr / max(xs.shape[1], 1)
    denom = float(np.linalg.norm(xs) * np.linalg.norm(ys))
    if denom <= EPS:
        ncc = np.zeros_like(corr, dtype=float)
    else:
        ncc = corr / denom
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
    index = {pattern: idx for idx, pattern in enumerate(patterns)}
    counts = np.zeros(len(patterns), dtype=float)
    if n_vectors <= 0:
        return counts
    for idx in range(n_vectors):
        window = values[idx : idx + order * delay : delay]
        pattern = tuple(np.argsort(window, kind="mergesort"))
        counts[index[pattern]] += 1.0
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


def lcss_similarity(
    x: Any,
    y: Any,
    *,
    epsilon: float = 1.0,
    window: int | None = None,
    mode: Literal["exact", "fast"] = "exact",
) -> float:
    left, right, _, _, resolved_mode = _prepare_elastic_pair(x, y, mode=mode)
    n, m = len(left), len(right)
    if n == 0 or m == 0:
        return float("nan")
    resolved_window = _resolved_window(n, m, window, resolved_mode)
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


def edr_distance(
    x: Any,
    y: Any,
    *,
    epsilon: float = 1.0,
    normalized: bool = True,
    window: int | None = None,
    mode: Literal["exact", "fast"] = "exact",
) -> float:
    left, right, _, _, resolved_mode = _prepare_elastic_pair(x, y, mode=mode)
    n, m = len(left), len(right)
    if n == 0 or m == 0:
        return float("nan")
    resolved_window = _resolved_window(n, m, window, resolved_mode)
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
    gap = np.asarray(gap_value, dtype=float)
    if gap.ndim == 0:
        gap = np.full(left.shape[1], float(gap))
    if gap.shape != (left.shape[1],):
        raise ValueError(f"gap_value must broadcast to shape {(left.shape[1],)}.")
    left_gap_costs = _pointwise_l2_to_reference(left, gap)
    right_gap_costs = _pointwise_l2_to_reference(right, gap)
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
    tx = np.arange(1, n + 1, dtype=float) if left_ts is None else np.asarray(left_ts, dtype=float).reshape(-1)
    ty = np.arange(1, m + 1, dtype=float) if right_ts is None else np.asarray(right_ts, dtype=float).reshape(-1)
    if tx.size != n or ty.size != m:
        raise ValueError("Timestamp arrays must match the cleaned series lengths.")
    left_prev = _previous_rows(left)
    right_prev = _previous_rows(right)
    left_prev_ts = np.concatenate([[0.0], tx[:-1]])
    right_prev_ts = np.concatenate([[0.0], ty[:-1]])
    left_delete_costs = _consecutive_l2_costs(left, left_prev) + nu * np.abs(tx - left_prev_ts) + lambda_
    right_delete_costs = _consecutive_l2_costs(right, right_prev) + nu * np.abs(ty - right_prev_ts) + lambda_
    prev = np.full(m + 1, np.inf, dtype=float)
    curr = np.full(m + 1, np.inf, dtype=float)
    prev[0] = 0.0
    for j in range(1, m + 1):
        prev[j] = prev[j - 1] + right_delete_costs[j - 1]
    for i in range(1, n + 1):
        curr.fill(np.inf)
        curr[0] = prev[0] + left_delete_costs[i - 1]
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
]
