"""Core proxy metrics for structure-aware time-series profiling."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.signal import lombscargle, periodogram, savgol_filter

EPS = 1e-12


@dataclass(slots=True)
class MultivariateMetrics:
    mean_abs_correlation: float
    dynamic_correlation_instability: float


@dataclass(slots=True)
class SeriesSummary:
    metrics: dict[str, float]
    clean_values: np.ndarray
    clean_timestamps: np.ndarray | None


def _clean_series_and_timestamps(x: np.ndarray, timestamps: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | None]:
    arr = np.asarray(x, dtype=float).reshape(-1)
    mask = np.isfinite(arr)
    clean = arr[mask]
    if timestamps is None:
        return clean, None
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    if ts.shape[0] == arr.shape[0]:
        return clean, ts[mask]
    if ts.shape[0] == clean.shape[0]:
        return clean, ts
    raise ValueError("timestamps must either match the original series length or the cleaned series length.")


def _zscore(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    std = float(np.std(x))
    if std < EPS:
        return np.zeros_like(x)
    return (x - float(np.mean(x))) / std


def _mad(x: np.ndarray) -> float:
    median = float(np.median(x))
    return float(np.median(np.abs(x - median))) + EPS


def _safe_corr(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 3:
        return float("nan")
    x2 = x[mask]
    y2 = y[mask]
    sx = float(np.std(x2))
    sy = float(np.std(y2))
    if sx < EPS or sy < EPS:
        return 0.0
    return float(np.corrcoef(x2, y2)[0, 1])


def _window_length(n: int, fraction: float = 0.1, minimum: int = 16, maximum: int = 128) -> int:
    if n < minimum:
        return max(4, n // 3)
    raw = int(round(n * fraction))
    return int(np.clip(raw, minimum, min(maximum, n)))


def _window_summary(x: np.ndarray, stat: str = "mean") -> np.ndarray:
    n = len(x)
    w = _window_length(n)
    if w < 4 or n < w + 2:
        return np.asarray([], dtype=float)
    stride = max(1, w // 2)
    values: list[float] = []
    for start in range(0, n - w + 1, stride):
        segment = x[start : start + w]
        if stat == "mean":
            values.append(float(np.mean(segment)))
        elif stat == "var":
            values.append(float(np.var(segment)))
        else:
            raise ValueError(f"Unsupported stat: {stat}")
    return np.asarray(values, dtype=float)


def _normalized_periodogram(x: np.ndarray, *, fs: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    if len(x) < 8:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    freqs, power = periodogram(x, fs=fs, detrend="linear", scaling="spectrum")
    if len(freqs) > 1:
        freqs = freqs[1:]
        power = power[1:]
    total = float(np.sum(power))
    if total <= EPS:
        return freqs, np.zeros_like(power)
    return freqs, power / total


def _uses_irregular_spectrum(timestamps: np.ndarray | None) -> bool:
    if timestamps is None:
        return False
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    ts = ts[np.isfinite(ts)]
    if ts.size < 12:
        return False
    delta = np.diff(np.sort(ts))
    delta = delta[delta > 0]
    if delta.size < 4:
        return False
    cv = float(np.std(delta) / (np.mean(delta) + EPS))
    return bool(cv > 0.05)


def _normalized_irregular_spectrum(x: np.ndarray, timestamps: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(x, dtype=float).reshape(-1)
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    mask = np.isfinite(values) & np.isfinite(ts)
    values = values[mask]
    ts = ts[mask]
    if values.size < 12:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    order = np.argsort(ts, kind="mergesort")
    ts = ts[order]
    values = values[order]
    ts = ts - float(np.min(ts))
    span = float(np.max(ts) - np.min(ts))
    if span <= 0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    delta = np.diff(ts)
    delta = delta[delta > 0]
    if delta.size < 4:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    median_dt = float(np.median(delta))
    if median_dt <= 0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    fmin = max(1.0 / span, EPS)
    fmax = max(fmin * 2.0, 0.5 / median_dt)
    if not np.isfinite(fmax) or fmax <= fmin:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    n_freq = int(np.clip(values.size * 2, 64, 256))
    freqs = np.linspace(fmin, fmax, n_freq, dtype=float)
    centered = values - float(np.mean(values))
    angular = 2.0 * np.pi * freqs
    try:
        power = lombscargle(ts, centered, angular, floating_mean=True, normalize=False)
    except TypeError:  # pragma: no cover - older SciPy compatibility
        try:
            power = lombscargle(ts, centered, angular, precenter=True, normalize=False)
        except TypeError:  # pragma: no cover
            power = lombscargle(ts, centered, angular)
    if power.size < 2:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    power = np.asarray(power, dtype=float)
    power = np.clip(power, 0.0, None)
    total = float(np.sum(power))
    if total <= EPS:
        return freqs, np.zeros_like(power)
    return freqs, power / total


def _normalized_spectrum(x: np.ndarray, *, timestamps: np.ndarray | None = None, fs: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    if timestamps is not None and _uses_irregular_spectrum(timestamps):
        freqs, power = _normalized_irregular_spectrum(x, timestamps)
        if power.size >= 2:
            return freqs, power
    return _normalized_periodogram(x, fs=fs)


def _js_divergence(p: np.ndarray, q: np.ndarray) -> float:
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    if p.size == 0 or q.size == 0:
        return float("nan")
    m = 0.5 * (p + q)
    p = np.clip(p, EPS, None)
    q = np.clip(q, EPS, None)
    m = np.clip(m, EPS, None)
    kl_pm = np.sum(p * np.log(p / m))
    kl_qm = np.sum(q * np.log(q / m))
    return float(0.5 * (kl_pm + kl_qm) / math.log(2.0))


def spectral_entropy(x: np.ndarray, timestamps: np.ndarray | None = None) -> float:
    _, power = _normalized_spectrum(x, timestamps=timestamps)
    if power.size < 2:
        return float("nan")
    entropy = -np.sum(power * np.log(power + EPS)) / math.log(power.size)
    return float(np.clip(entropy, 0.0, 1.0))


def forecastability(x: np.ndarray, timestamps: np.ndarray | None = None) -> float:
    entropy = spectral_entropy(x, timestamps=timestamps)
    if not np.isfinite(entropy):
        return float("nan")
    return float(1.0 - entropy)


def ar1_r2(x: np.ndarray) -> float:
    if len(x) < 6:
        return float("nan")
    y = x[1:]
    X = np.column_stack([x[:-1], np.ones(len(x) - 1)])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ beta
    denom = float(np.sum((y - np.mean(y)) ** 2))
    if denom <= EPS:
        return 0.0
    score = 1.0 - float(np.sum((y - y_hat) ** 2) / denom)
    return float(np.clip(score, 0.0, 1.0))


def max_abs_acf(x: np.ndarray, max_lag: int | None = None) -> float:
    n = len(x)
    if n < 6:
        return float("nan")
    max_lag = min(max_lag or max(2, n // 10), n - 2)
    z = _zscore(x)
    values = []
    for lag in range(1, max_lag + 1):
        values.append(abs(_safe_corr(z[:-lag], z[lag:])))
    return float(np.nanmax(values)) if values else float("nan")


def rolling_mean_drift(x: np.ndarray) -> float:
    means = _window_summary(x, stat="mean")
    if means.size < 2:
        return float("nan")
    return float(np.mean(np.abs(means - np.mean(x))) / (np.std(x) + EPS))


def rolling_variance_drift(x: np.ndarray) -> float:
    variances = _window_summary(x, stat="var")
    if variances.size < 2:
        return float("nan")
    return float(np.std(variances) / (np.var(x) + EPS))


def spectral_drift(x: np.ndarray, timestamps: np.ndarray | None = None) -> float:
    if len(x) < 16:
        return float("nan")
    mid = len(x) // 2
    ts1 = None if timestamps is None else np.asarray(timestamps, dtype=float)[:mid]
    ts2 = None if timestamps is None else np.asarray(timestamps, dtype=float)[mid:]
    _, p1 = _normalized_spectrum(x[:mid], timestamps=ts1)
    _, p2 = _normalized_spectrum(x[mid:], timestamps=ts2)
    m = min(p1.size, p2.size)
    if m < 2:
        return float("nan")
    return _js_divergence(p1[:m], p2[:m])


def linear_trend_r2(x: np.ndarray) -> float:
    if len(x) < 5:
        return float("nan")
    t = np.linspace(-1.0, 1.0, len(x))
    X = np.column_stack([t, np.ones(len(t))])
    beta, *_ = np.linalg.lstsq(X, x, rcond=None)
    fitted = X @ beta
    denom = float(np.sum((x - np.mean(x)) ** 2))
    if denom <= EPS:
        return 0.0
    score = 1.0 - float(np.sum((x - fitted) ** 2) / denom)
    return float(np.clip(score, 0.0, 1.0))


def slope_strength(x: np.ndarray) -> float:
    if len(x) < 5:
        return float("nan")
    t = np.linspace(-1.0, 1.0, len(x))
    slope, intercept = np.polyfit(t, x, deg=1)
    total_change = abs((slope * t[-1] + intercept) - (slope * t[0] + intercept))
    return float(total_change / (np.std(x) + EPS))


def low_freq_power_ratio(x: np.ndarray, timestamps: np.ndarray | None = None) -> float:
    freqs, power = _normalized_spectrum(x, timestamps=timestamps)
    if power.size < 2:
        return float("nan")
    cutoff = np.quantile(freqs, 0.25)
    return float(np.sum(power[freqs <= cutoff]))


def spectral_peak_ratio(x: np.ndarray, timestamps: np.ndarray | None = None) -> float:
    _, power = _normalized_spectrum(x, timestamps=timestamps)
    if power.size < 2:
        return float("nan")
    return float(np.max(power))


def spectral_flatness(x: np.ndarray, timestamps: np.ndarray | None = None) -> float:
    _, power = _normalized_spectrum(x, timestamps=timestamps)
    if power.size < 2:
        return float("nan")
    power = np.clip(power, EPS, None)
    geometric = float(np.exp(np.mean(np.log(power))))
    arithmetic = float(np.mean(power))
    if arithmetic <= EPS:
        return float("nan")
    return float(np.clip(geometric / arithmetic, 0.0, 1.0))


def acf_periodic_peak(x: np.ndarray) -> float:
    n = len(x)
    if n < 10:
        return float("nan")
    max_lag = min(max(4, n // 3), 200)
    z = _zscore(x)
    peaks = []
    for lag in range(2, max_lag + 1):
        peaks.append(max(0.0, _safe_corr(z[:-lag], z[lag:])))
    return float(np.max(peaks)) if peaks else float("nan")


def _entropy_subsample(x: np.ndarray, max_points: int = 600) -> np.ndarray:
    if len(x) <= max_points:
        return x
    stride = max(1, int(np.ceil(len(x) / max_points)))
    return x[::stride]


def permutation_entropy(x: np.ndarray, order: int = 3, delay: int = 1) -> float:
    x = _entropy_subsample(np.asarray(x, dtype=float))
    n = len(x)
    if n < order * delay + 2:
        return float("nan")
    patterns: dict[tuple[int, ...], int] = {}
    for idx in range(n - delay * (order - 1)):
        window = x[idx : idx + delay * order : delay]
        pattern = tuple(np.argsort(window, kind="mergesort"))
        patterns[pattern] = patterns.get(pattern, 0) + 1
    counts = np.asarray(list(patterns.values()), dtype=float)
    probs = counts / counts.sum()
    entropy = -np.sum(probs * np.log(probs + EPS)) / math.log(math.factorial(order))
    return float(np.clip(entropy, 0.0, 1.0))


def sample_entropy(x: np.ndarray, m: int = 2, r_ratio: float = 0.2) -> float:
    x = _entropy_subsample(np.asarray(x, dtype=float))
    n = len(x)
    if n < m + 3:
        return float("nan")
    std = float(np.std(x))
    if std < EPS:
        return 0.0
    r = r_ratio * std

    def _phi(order: int) -> float:
        count = 0
        templates = 0
        for i in range(n - order):
            template = x[i : i + order]
            for j in range(i + 1, n - order + 1):
                compare = x[j : j + order]
                if np.max(np.abs(template - compare)) <= r:
                    count += 1
            templates += n - order - i
        if templates <= 0:
            return 0.0
        return count / templates

    phi_m = _phi(m)
    phi_m1 = _phi(m + 1)
    if phi_m <= EPS or phi_m1 <= EPS:
        return float("nan")
    return float(max(0.0, -np.log(phi_m1 / phi_m)))


def lz_complexity(x: np.ndarray) -> float:
    if len(x) < 8:
        return float("nan")
    binary = "".join("1" if value >= np.median(x) else "0" for value in x)
    phrases: set[str] = set()
    i = 0
    increment = 1
    while i < len(binary):
        fragment = binary[i : i + increment]
        if not fragment:
            break
        if fragment in phrases and i + increment <= len(binary):
            increment += 1
            if i + increment - 1 > len(binary):
                phrases.add(binary[i:])
                break
        else:
            phrases.add(fragment)
            i += increment
            increment = 1
    raw = len(phrases)
    norm = raw * math.log2(len(binary)) / len(binary)
    return float(max(0.0, norm))


def hurst_exponent_rs(x: np.ndarray) -> float:
    n = len(x)
    if n < 32:
        return float("nan")
    sizes = np.unique(np.clip(np.logspace(np.log10(8), np.log10(max(8, n // 2)), num=6).astype(int), 8, n // 2))
    rs_vals = []
    used_sizes = []
    for size in sizes:
        if size < 8 or size >= n:
            continue
        chunk_rs = []
        for start in range(0, n - size + 1, size):
            segment = x[start : start + size]
            centered = segment - np.mean(segment)
            cumulative = np.cumsum(centered)
            r = np.max(cumulative) - np.min(cumulative)
            s = np.std(segment)
            if s > EPS:
                chunk_rs.append(r / s)
        if chunk_rs:
            rs_vals.append(np.mean(chunk_rs))
            used_sizes.append(size)
    if len(used_sizes) < 2:
        return float("nan")
    slope, _ = np.polyfit(np.log(used_sizes), np.log(rs_vals), deg=1)
    return float(slope)


def hurst_complexity_proxy(x: np.ndarray) -> float:
    hurst = hurst_exponent_rs(x)
    if not np.isfinite(hurst):
        return float("nan")
    return float(np.clip(abs(hurst - 0.5) * 2.0, 0.0, 1.0))


def lagged_mutual_information(x: np.ndarray, lag: int = 1) -> float:
    if len(x) < lag + 8:
        return float("nan")
    x1 = x[:-lag]
    x2 = x[lag:]
    bins = int(np.clip(round(np.sqrt(len(x1) / 5.0)), 4, 16))
    hist, _, _ = np.histogram2d(x1, x2, bins=bins)
    pxy = hist / np.sum(hist)
    px = np.sum(pxy, axis=1, keepdims=True)
    py = np.sum(pxy, axis=0, keepdims=True)
    mask = pxy > 0
    mi = np.sum(pxy[mask] * np.log(pxy[mask] / (px @ py)[mask]))
    return float(max(0.0, mi))


def nonlinearity_gap(x: np.ndarray) -> float:
    if len(x) < 8:
        return float("nan")
    rho = _safe_corr(x[:-1], x[1:])
    if not np.isfinite(rho):
        return float("nan")
    empirical_mi = lagged_mutual_information(x, lag=1)
    gaussian_mi = 0.0 if abs(rho) >= 1 else float(max(0.0, -0.5 * np.log(max(1.0 - rho**2, EPS))))
    gap = max(0.0, empirical_mi - gaussian_mi)
    return float(gap / (empirical_mi + gaussian_mi + EPS))


def time_reversal_asymmetry(x: np.ndarray) -> float:
    if len(x) < 6:
        return float("nan")
    dx1 = x[1:-1] - x[:-2]
    dx2 = x[2:] - x[1:-1]
    stat = np.mean((dx2 - dx1) * (dx2 + dx1) * dx1)
    scale = (np.std(x) + EPS) ** 3
    return float(stat / scale)


def event_rate_and_burstiness(x: np.ndarray) -> tuple[float, float, float]:
    centered = np.abs(x - np.median(x)) / _mad(x)
    events = centered > 2.5
    rate = float(np.mean(events))
    idx = np.flatnonzero(events)
    burstiness = 0.0
    if idx.size > 2:
        intervals = np.diff(idx)
        mean_interval = float(np.mean(intervals))
        if mean_interval > EPS:
            cv = float(np.std(intervals) / mean_interval)
            burstiness = float(np.clip((cv - 1.0) / (cv + 1.0), -1.0, 1.0))
    burstiness01 = 0.5 * (burstiness + 1.0)
    abs_energy = np.square(np.abs(x))
    cutoff = np.quantile(abs_energy, 0.95)
    concentration = float(np.sum(abs_energy[abs_energy >= cutoff]) / (np.sum(abs_energy) + EPS))
    return rate, float(np.clip(burstiness01, 0.0, 1.0)), float(np.clip(concentration, 0.0, 1.0))


def noise_residual_ratio(x: np.ndarray) -> float:
    n = len(x)
    if n < 7:
        return float("nan")
    window = int(np.clip((n // 10) | 1, 5, min(51, n if n % 2 else n - 1)))
    if window < 5:
        return float("nan")
    polyorder = min(2, window - 2)
    smooth = savgol_filter(x, window_length=window, polyorder=polyorder, mode="interp")
    residual = x - smooth
    return float(np.var(residual) / (np.var(x) + EPS))


def high_freq_power_ratio(x: np.ndarray, timestamps: np.ndarray | None = None) -> float:
    freqs, power = _normalized_spectrum(x, timestamps=timestamps)
    if power.size < 2:
        return float("nan")
    threshold = np.quantile(freqs, 0.75)
    return float(np.sum(power[freqs >= threshold]))


def change_point_density(x: np.ndarray) -> float:
    mean_windows = _window_summary(x, stat="mean")
    var_windows = _window_summary(x, stat="var")
    if mean_windows.size < 3 or var_windows.size < 3:
        return float("nan")
    d_mean = np.abs(np.diff(mean_windows))
    d_var = np.abs(np.diff(var_windows))
    thr_mean = np.median(d_mean) + 2.5 * _mad(d_mean)
    thr_var = np.median(d_var) + 2.5 * _mad(d_var)
    cp = (d_mean > thr_mean) | (d_var > thr_var)
    return float(np.mean(cp))


def timestamp_irregularity(timestamps: np.ndarray | None) -> float:
    if timestamps is None:
        return float("nan")
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    ts = ts[np.isfinite(ts)]
    if ts.size < 3:
        return float("nan")
    delta = np.diff(ts)
    delta = delta[delta > 0]
    if delta.size < 2:
        return float("nan")
    return float(np.std(delta) / (np.mean(delta) + EPS))


def gap_fraction(timestamps: np.ndarray | None) -> float:
    if timestamps is None:
        return float("nan")
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    ts = ts[np.isfinite(ts)]
    if ts.size < 4:
        return float("nan")
    delta = np.diff(ts)
    delta = delta[delta > 0]
    if delta.size < 3:
        return float("nan")
    threshold = float(np.median(delta) + 2.5 * _mad(delta))
    return float(np.mean(delta > threshold))


def bandpower_ratio(
    x: np.ndarray,
    fs: float,
    low: float,
    high: float,
    total_low: float | None = None,
    total_high: float | None = None,
    timestamps: np.ndarray | None = None,
) -> float:
    if fs <= 0 and timestamps is None:
        return float("nan")
    freqs, power = _normalized_spectrum(x, timestamps=timestamps, fs=max(fs, EPS))
    if power.size < 2:
        return float("nan")
    band_mask = (freqs >= low) & (freqs < high)
    if total_low is None:
        total_low = float(np.min(freqs))
    if total_high is None:
        total_high = float(np.max(freqs) + EPS)
    total_mask = (freqs >= total_low) & (freqs <= total_high)
    denom = float(np.sum(power[total_mask]))
    if denom <= EPS:
        return float("nan")
    return float(np.sum(power[band_mask]) / denom)


def peak_prominence_ratio(x: np.ndarray, fs: float, low: float, high: float, timestamps: np.ndarray | None = None) -> float:
    if fs <= 0 and timestamps is None:
        return float("nan")
    freqs, power = _normalized_spectrum(x, timestamps=timestamps, fs=max(fs, EPS))
    if power.size < 2:
        return float("nan")
    band_mask = (freqs >= low) & (freqs < high)
    if not np.any(band_mask):
        return float("nan")
    total = float(np.sum(power))
    if total <= EPS:
        return float("nan")
    return float(np.max(power[band_mask]) / total)


def channel_asynchrony(mask_matrix: np.ndarray) -> float:
    mask = np.asarray(mask_matrix, dtype=bool)
    if mask.ndim != 2 or mask.shape[1] < 2 or mask.shape[0] == 0:
        return float("nan")
    row_counts = np.sum(mask, axis=1)
    score = 1.0 - np.mean((row_counts - 1.0) / max(mask.shape[1] - 1.0, 1.0))
    return float(np.clip(score, 0.0, 1.0))


def interval_burstiness_from_timestamps(timestamps: np.ndarray | None) -> float:
    if timestamps is None:
        return float("nan")
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    ts = ts[np.isfinite(ts)]
    if ts.size < 4:
        return float("nan")
    delta = np.diff(np.sort(ts))
    delta = delta[delta > 0]
    if delta.size < 3:
        return float("nan")
    mean_interval = float(np.mean(delta))
    if mean_interval <= EPS:
        return float("nan")
    cv = float(np.std(delta) / mean_interval)
    burstiness = float(np.clip((cv - 1.0) / (cv + 1.0), -1.0, 1.0))
    return float(np.clip(0.5 * (burstiness + 1.0), 0.0, 1.0))


def normalized_entropy(labels: Sequence[object] | None) -> float:
    if labels is None:
        return float("nan")
    arr = np.asarray(list(labels), dtype=object).reshape(-1)
    if arr.size < 2:
        return float("nan")
    uniques, counts = np.unique(arr.astype(str), return_counts=True)
    if uniques.size < 2:
        return 0.0
    probs = counts / counts.sum()
    entropy = -np.sum(probs * np.log(probs + EPS)) / np.log(len(uniques))
    return float(np.clip(entropy, 0.0, 1.0))


def simultaneity_fraction(timestamps: np.ndarray | None) -> float:
    if timestamps is None:
        return float("nan")
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    ts = ts[np.isfinite(ts)]
    if ts.size < 2:
        return float("nan")
    _, counts = np.unique(ts, return_counts=True)
    if counts.size == 0:
        return float("nan")
    return float(np.mean(counts > 1))


def mark_cv(values: np.ndarray | None) -> float:
    if values is None:
        return float("nan")
    arr = np.asarray(values, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size < 2:
        return float("nan")
    mean_abs = float(np.mean(np.abs(arr)))
    if mean_abs <= EPS:
        return 0.0
    return float(np.std(arr) / (mean_abs + EPS))


def compute_series_metrics(x: np.ndarray, timestamps: np.ndarray | None = None, missing_fraction: float = 0.0) -> SeriesSummary:
    clean, clean_ts = _clean_series_and_timestamps(x, timestamps)
    if clean.size < 8:
        metrics = {
            "n_points": float(clean.size),
            "missing_fraction": float(missing_fraction),
            "delta_t_cv": float(timestamp_irregularity(clean_ts)),
            "gap_fraction": float(gap_fraction(clean_ts)),
            "irregular_spectral_support": 1.0 if _uses_irregular_spectrum(clean_ts) else 0.0,
        }
        return SeriesSummary(metrics=metrics, clean_values=clean, clean_timestamps=clean_ts)

    rate, burstiness, concentration = event_rate_and_burstiness(clean)
    irregular_spectral = _uses_irregular_spectrum(clean_ts)
    metrics = {
        "n_points": float(clean.size),
        "missing_fraction": float(missing_fraction),
        "delta_t_cv": float(timestamp_irregularity(clean_ts)),
        "gap_fraction": float(gap_fraction(clean_ts)),
        "irregular_spectral_support": 1.0 if irregular_spectral else 0.0,
        "spectral_entropy": float(spectral_entropy(clean, timestamps=clean_ts)),
        "forecastability": float(forecastability(clean, timestamps=clean_ts)),
        "ar1_r2": float(ar1_r2(clean)),
        "max_abs_acf": float(max_abs_acf(clean)),
        "mean_drift_ratio": float(rolling_mean_drift(clean)),
        "variance_drift_ratio": float(rolling_variance_drift(clean)),
        "spectral_drift_js": float(spectral_drift(clean, timestamps=clean_ts)),
        "trend_r2": float(linear_trend_r2(clean)),
        "slope_strength": float(slope_strength(clean)),
        "low_freq_power_ratio": float(low_freq_power_ratio(clean, timestamps=clean_ts)),
        "spectral_peak_ratio": float(spectral_peak_ratio(clean, timestamps=clean_ts)),
        "spectral_flatness": float(spectral_flatness(clean, timestamps=clean_ts)),
        "acf_periodic_peak": float(acf_periodic_peak(clean)),
        "permutation_entropy": float(permutation_entropy(clean)),
        "sample_entropy": float(sample_entropy(clean)),
        "lz_complexity": float(lz_complexity(clean)),
        "hurst_exponent": float(hurst_exponent_rs(clean)),
        "hurst_complexity_proxy": float(hurst_complexity_proxy(clean)),
        "nonlinearity_gap": float(nonlinearity_gap(clean)),
        "time_reversal_asymmetry": float(time_reversal_asymmetry(clean)),
        "event_rate": float(rate),
        "burstiness": float(burstiness),
        "event_energy_concentration": float(concentration),
        "noise_residual_ratio": float(noise_residual_ratio(clean)),
        "high_freq_power_ratio": float(high_freq_power_ratio(clean, timestamps=clean_ts)),
        "change_point_density": float(change_point_density(clean)),
    }
    return SeriesSummary(metrics=metrics, clean_values=clean, clean_timestamps=clean_ts)


def compute_multivariate_metrics(matrix: np.ndarray) -> MultivariateMetrics:
    arr = np.asarray(matrix, dtype=float)
    if arr.ndim != 2 or arr.shape[1] < 2 or arr.shape[0] < 8:
        return MultivariateMetrics(mean_abs_correlation=float("nan"), dynamic_correlation_instability=float("nan"))

    corr_values: list[float] = []
    for i in range(arr.shape[1]):
        for j in range(i + 1, arr.shape[1]):
            corr = abs(_safe_corr(arr[:, i], arr[:, j]))
            if np.isfinite(corr):
                corr_values.append(corr)
    mean_abs = float(np.mean(corr_values)) if corr_values else float("nan")

    window = _window_length(arr.shape[0], fraction=0.15, minimum=12, maximum=96)
    if arr.shape[0] < window + 2 or not corr_values:
        return MultivariateMetrics(mean_abs_correlation=mean_abs, dynamic_correlation_instability=float("nan"))

    stride = max(1, window // 2)
    window_means: list[float] = []
    for start in range(0, arr.shape[0] - window + 1, stride):
        segment = arr[start : start + window]
        segment_values = []
        for i in range(segment.shape[1]):
            for j in range(i + 1, segment.shape[1]):
                corr = abs(_safe_corr(segment[:, i], segment[:, j]))
                if np.isfinite(corr):
                    segment_values.append(corr)
        if segment_values:
            window_means.append(float(np.mean(segment_values)))
    instability = float(np.std(window_means)) if len(window_means) >= 2 else float("nan")
    return MultivariateMetrics(mean_abs_correlation=mean_abs, dynamic_correlation_instability=instability)
