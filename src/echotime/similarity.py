"""Time-series similarity utilities for raw-shape and structure-aware comparisons."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np
from scipy.signal import savgol_filter
from scipy.stats import kendalltau, spearmanr

from .metrics import EPS, _js_divergence, _normalized_spectrum
from .profile import DatasetProfile, SeriesProfile, profile_dataset


def _level(score: float) -> str:
    score = float(score)
    if score >= 0.85:
        return "very high"
    if score >= 0.68:
        return "high"
    if score >= 0.48:
        return "moderate"
    if score >= 0.28:
        return "low"
    return "very low"


def _reference_metric_label(name: str) -> str:
    labels = {
        "pearson_r": "Pearson r",
        "spearman_rho": "Spearman rho",
        "kendall_tau": "Kendall tau",
        "best_lag_pearson_r": "Best-lag Pearson r",
        "normalized_mutual_information": "Mutual info",
        "first_difference_r": "First-difference r",
    }
    return labels.get(name, name.replace("_", " "))


@dataclass(slots=True)
class SimilarityReport:
    left_name: str
    right_name: str
    mode: str
    similarity_score: float
    qualitative_label: str
    component_scores: dict[str, float]
    interpretation: str
    reference_metrics: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def component_mean(self) -> float:
        values = [float(v) for v in self.component_scores.values() if np.isfinite(v)]
        if not values:
            return float("nan")
        return float(np.mean(values))

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_name": self.left_name,
            "right_name": self.right_name,
            "mode": self.mode,
            "similarity_score": float(self.similarity_score),
            "qualitative_label": self.qualitative_label,
            "component_scores": dict(self.component_scores),
            "component_mean": float(self.component_mean),
            "interpretation": self.interpretation,
            "reference_metrics": dict(self.reference_metrics),
            "notes": list(self.notes),
            "suggestions": list(self.suggestions),
            "metadata": dict(self.metadata),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        lines = [
            "# EchoTime similarity report",
            "",
            f"**left:** {self.left_name}  ",
            f"**right:** {self.right_name}  ",
            f"**mode:** {self.mode}  ",
            f"**component mean:** {self.component_mean:0.3f}",
            "",
            "## Interpretation",
            "",
            self.interpretation,
            "",
        ]
        if self.reference_metrics:
            lines.extend([
                "## Familiar statistics",
                "",
                "| metric | value |",
                "|---|---:|",
            ])
            for key, value in self.reference_metrics.items():
                lines.append(f"| {_reference_metric_label(key)} | {float(value):0.3f} |")
            lines.append("")
        lines.extend([
            "## Component scores",
            "",
            "| component | score | level |",
            "|---|---:|---|",
        ])
        for key, value in self.component_scores.items():
            lines.append(f"| {key} | {float(value):0.3f} | {_level(float(value))} |")
        if self.suggestions:
            lines.extend(["", "## Suggested next moves", ""])
            for item in self.suggestions:
                lines.append(f"- {item}")
        if self.notes:
            lines.extend(["", "## Notes", ""])
            for note in self.notes:
                lines.append(f"- {note}")
        if self.metadata:
            lines.extend(["", "## Metadata", "", "| field | value |", "|---|---|" ])
            for key, value in self.metadata.items():
                lines.append(f"| {key} | {value} |")
        return "\n".join(lines)

    def to_summary_card_markdown(self) -> str:
        lines = [
            "# EchoTime similarity summary",
            "",
            f"**Compared:** {self.left_name} vs {self.right_name}",
            "",
            "## Headline",
            "",
            self.interpretation,
            "",
        ]
        if self.reference_metrics:
            lines.extend([
                "## Familiar statistics",
                "",
                "| metric | value |",
                "|---|---:|",
            ])
            for key, value in self.reference_metrics.items():
                lines.append(f"| {_reference_metric_label(key)} | {float(value):0.3f} |")
            lines.append("")
        lines.extend([
            "## Time-series-specific metrics",
            "",
            "| plain-language label | score |",
            "|---|---:|",
        ])
        for key, value in sorted(self.component_scores.items(), key=lambda kv: kv[1], reverse=True)[:4]:
            label = key.replace("_", " ")
            lines.append(f"| {label} | {float(value):0.3f} |")
        if self.suggestions:
            lines.extend(["", "## Recommended next actions", ""])
            for item in self.suggestions[:5]:
                lines.append(f"- {item}")
        return "\n".join(lines)

    def to_narrative_report(self) -> str:
        lines = [
            "# EchoTime similarity narrative",
            "",
            "## What was compared",
            "",
            f"This report compares **{self.left_name}** with **{self.right_name}** using the **{self.mode}** similarity mode.",
            "",
            "## What the package thinks is going on",
            "",
            self.interpretation,
            "",
        ]
        if self.reference_metrics:
            metrics = ", ".join(
                f"{_reference_metric_label(key)} {float(value):0.2f}"
                for key, value in list(self.reference_metrics.items())[:4]
            )
            lines.extend(["## Familiar statistics", "", metrics, ""])
        lines.extend([
            "## Why this matters",
            "",
        ])
        top = sorted(self.component_scores.items(), key=lambda kv: kv[1], reverse=True)
        if top:
            best = top[0][0].replace("_", " ")
            lines.append(f"The strongest agreement appears in **{best}**, which means these two trajectories share an important part of their structure even if they are not identical point by point.")
            lines.append("")
        lines.extend(["## What to do next", ""])
        for item in self.suggestions[:6] or [
            "Inspect the raw trajectories and the aligned windows together.",
            "Check whether similarity is stable over time instead of relying on one aggregate number.",
        ]:
            lines.append(f"- {item}")
        if self.notes:
            lines.extend(["", "## Guardrails", ""])
            for note in self.notes:
                lines.append(f"- {note}")
        return "\n".join(lines)

    def to_html_report(self, *, title: str | None = None) -> str:
        from .visuals import similarity_html_report

        return similarity_html_report(self, title=title)

    def to_agent_context_dict(self, *, budget: str = "lean") -> dict[str, Any]:
        from .agent import agent_context

        return agent_context(self, budget=budget, format="dict")  # type: ignore[return-value]

    def to_agent_context_json(self, *, budget: str = "lean", indent: int = 2) -> str:
        import json as _json
        return _json.dumps(self.to_agent_context_dict(budget=budget), indent=indent)

    def to_agent_context_markdown(self, *, budget: str = "lean") -> str:
        from .agent import agent_context

        return agent_context(self, budget=budget, format="markdown")  # type: ignore[return-value]


def _as_matrix(data: Any) -> np.ndarray:
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    if arr.ndim == 1:
        return arr.reshape(-1, 1)
    if arr.ndim == 2:
        return arr
    if arr.ndim >= 3:
        # reduce higher dimensions conservatively; keep time first if likely dataset-shaped
        flat = arr.reshape(arr.shape[0], -1)
        return flat
    raise ValueError("Unsupported input dimensionality for similarity comparison.")


def _normalize_channel_layout(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr, dtype=float)
    if arr.ndim != 2:
        return _as_matrix(arr)
    # Prefer time x channels layout. If channels appear to exceed time, transpose.
    if arr.shape[1] > arr.shape[0] and arr.shape[0] <= 16:
        arr = arr.T
    return arr


def _valid_timestamps(timestamps: Any, expected_length: int) -> np.ndarray | None:
    if timestamps is None:
        return None
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    if ts.size != expected_length:
        return None
    mask = np.isfinite(ts)
    if int(mask.sum()) < 3:
        return None
    return ts


def _interpolate_series(values: np.ndarray, timestamps: np.ndarray | None, n_points: int) -> np.ndarray:
    values = np.asarray(values, dtype=float).reshape(-1)
    mask = np.isfinite(values)
    values = values[mask]
    if values.size < 3:
        return np.full(n_points, np.nan)
    if timestamps is None:
        x = np.linspace(0.0, 1.0, values.size)
    else:
        ts = np.asarray(timestamps, dtype=float).reshape(-1)
        ts = ts[mask]
        if ts.size < 3:
            x = np.linspace(0.0, 1.0, values.size)
        else:
            order = np.argsort(ts, kind="mergesort")
            ts = ts[order]
            values = values[order]
            ts = ts - float(np.min(ts))
            span = float(np.max(ts))
            if span <= EPS:
                x = np.linspace(0.0, 1.0, values.size)
            else:
                x = ts / span
    x = np.clip(x, 0.0, 1.0)
    x_new = np.linspace(0.0, 1.0, n_points)
    if np.unique(x).size < 3:
        return np.interp(x_new, np.linspace(0.0, 1.0, values.size), values)
    return np.interp(x_new, x, values)


def _zscore(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    mu = float(np.nanmean(x))
    sigma = float(np.nanstd(x))
    if sigma <= EPS:
        return np.zeros_like(x)
    return (x - mu) / sigma


def _safe_corr(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 3:
        return float("nan")
    x2 = x[mask]
    y2 = y[mask]
    sx = float(np.std(x2))
    sy = float(np.std(y2))
    if sx <= EPS or sy <= EPS:
        return 0.0
    return float(np.corrcoef(x2, y2)[0, 1])


def _safe_spearman_corr(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 3:
        return float("nan")
    x2 = x[mask]
    y2 = y[mask]
    if float(np.std(x2)) <= EPS or float(np.std(y2)) <= EPS:
        return 0.0
    result = spearmanr(x2, y2)
    value = getattr(result, "correlation", getattr(result, "statistic", result[0]))
    return float(value)


def _safe_kendall_tau(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 3:
        return float("nan")
    x2 = x[mask]
    y2 = y[mask]
    if float(np.std(x2)) <= EPS or float(np.std(y2)) <= EPS:
        return 0.0
    result = kendalltau(x2, y2)
    value = getattr(result, "correlation", getattr(result, "statistic", result[0]))
    return float(value)


def _corr_to_similarity(corr: float) -> float:
    if not np.isfinite(corr):
        return float("nan")
    return float(np.clip(corr, 0.0, 1.0))


def _geometric_similarity(*values: float) -> float:
    vals = [float(v) for v in values if np.isfinite(v)]
    if not vals:
        return float("nan")
    if any(v <= EPS for v in vals):
        return 0.0
    clipped = np.clip(np.asarray(vals, dtype=float), EPS, 1.0)
    return float(np.exp(np.mean(np.log(clipped))))


def _difference_view(x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=float).reshape(-1)
    if arr.size < 4:
        return np.asarray([], dtype=float)
    return _zscore(np.diff(arr))


def _monotonic_fraction(x: np.ndarray) -> float:
    arr = np.asarray(x, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size < 4:
        return float("nan")
    diff = np.diff(arr)
    if diff.size == 0:
        return float("nan")
    tol = 1e-6
    nondecreasing = float(np.mean(diff >= -tol))
    nonincreasing = float(np.mean(diff <= tol))
    return float(max(nondecreasing, nonincreasing))


def _best_lag_corr(x: np.ndarray, y: np.ndarray, max_lag: int | None = None) -> float:
    x = np.asarray(x, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    n = min(x.size, y.size)
    if n < 6:
        return float("nan")
    if max_lag is None:
        max_lag = max(1, min(24, n // 10))
    best = -np.inf
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            xl = x[:lag]
            yl = y[-lag:]
        elif lag > 0:
            xl = x[lag:]
            yl = y[:-lag]
        else:
            xl = x
            yl = y
        corr = _safe_corr(xl, yl)
        if np.isfinite(corr):
            best = max(best, corr)
    if not np.isfinite(best):
        return float("nan")
    return float(best)


def _normalized_mutual_information(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 12:
        return float("nan")
    x2 = np.asarray(x[mask], dtype=float)
    y2 = np.asarray(y[mask], dtype=float)
    if float(np.std(x2)) <= EPS or float(np.std(y2)) <= EPS:
        return 0.0
    bins = int(np.clip(round(np.sqrt(len(x2) / 4.0)), 4, 20))
    hist, _, _ = np.histogram2d(x2, y2, bins=bins)
    total = float(np.sum(hist))
    if total <= EPS:
        return float("nan")
    pxy = hist / total
    px = np.sum(pxy, axis=1)
    py = np.sum(pxy, axis=0)
    mask_xy = pxy > 0
    denom = px[:, None] * py[None, :]
    mi = float(np.sum(pxy[mask_xy] * np.log(pxy[mask_xy] / np.maximum(denom[mask_xy], EPS))))
    hx = float(-np.sum(px[px > 0] * np.log(px[px > 0])))
    hy = float(-np.sum(py[py > 0] * np.log(py[py > 0])))
    scale = max(np.sqrt(max(hx, 0.0) * max(hy, 0.0)), EPS)
    return float(np.clip(mi / scale, 0.0, 1.0))


def _smooth_trend(x: np.ndarray) -> np.ndarray:
    n = len(x)
    if n < 9:
        return x
    window = int(max(7, min(n - (1 - n % 2), (n // 6) * 2 + 1)))
    if window % 2 == 0:
        window += 1
    window = min(window, n if n % 2 == 1 else n - 1)
    if window < 5:
        return x
    return savgol_filter(x, window_length=window, polyorder=min(3, window - 2), mode="interp")


def _dtw_distance(x: np.ndarray, y: np.ndarray, window: int | None = None) -> float:
    x = np.asarray(x, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    n = x.size
    m = y.size
    if n == 0 or m == 0:
        return float("nan")
    if window is None:
        window = max(abs(n - m), max(5, min(n, m) // 8))
    window = max(window, abs(n - m))
    cost = np.full((n + 1, m + 1), np.inf, dtype=float)
    cost[0, 0] = 0.0
    for i in range(1, n + 1):
        j_start = max(1, i - window)
        j_stop = min(m + 1, i + window + 1)
        for j in range(j_start, j_stop):
            dist = abs(x[i - 1] - y[j - 1])
            cost[i, j] = dist + min(cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1])
    final = float(cost[n, m])
    if not np.isfinite(final):
        return float("nan")
    return final / (n + m)


def _distance_to_similarity(distance: float, scale: float = 1.0) -> float:
    if not np.isfinite(distance):
        return float("nan")
    return float(np.exp(-max(0.0, distance) / max(scale, EPS)))


def _strict_dtw_similarity(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    if min(x.size, y.size) < 6:
        return float("nan")
    level_window = max(3, min(18, min(x.size, y.size) // 20))
    level_score = _distance_to_similarity(_dtw_distance(x, y, window=level_window), scale=0.45)
    dx = _difference_view(x)
    dy = _difference_view(y)
    if min(dx.size, dy.size) < 6:
        return level_score
    diff_window = max(3, min(16, min(dx.size, dy.size) // 20))
    diff_score = _distance_to_similarity(_dtw_distance(dx, dy, window=diff_window), scale=0.35)
    return _geometric_similarity(level_score, diff_score)


def _spectral_similarity(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    _, px = _normalized_spectrum(x)
    _, py = _normalized_spectrum(y)
    m = min(px.size, py.size)
    if m < 4:
        return float("nan")
    px = px[:m]
    py = py[:m]
    base = float(np.clip(1.0 - _js_divergence(px, py), 0.0, 1.0))
    uniform = np.full(m, 1.0 / m, dtype=float)
    structure = _corr_to_similarity(_safe_corr(px - uniform, py - uniform))
    return _geometric_similarity(base, structure)


def _resampled_multichannel(data: Any, timestamps: Any | None = None, n_points: int = 256) -> np.ndarray:
    arr = _normalize_channel_layout(_as_matrix(data))
    ts = _valid_timestamps(timestamps, arr.shape[0])
    channels = []
    for idx in range(arr.shape[1]):
        channel = _interpolate_series(arr[:, idx], ts, n_points)
        channels.append(_zscore(channel))
    return np.column_stack(channels)


def _pair_multichannel(left: np.ndarray, right: np.ndarray) -> tuple[np.ndarray, np.ndarray, str]:
    if left.shape[1] == right.shape[1]:
        return left, right, "paired_channels"
    left_agg = np.nanmean(left, axis=1, keepdims=True)
    right_agg = np.nanmean(right, axis=1, keepdims=True)
    return left_agg, right_agg, "aggregate_channels"


def _mean_channel(values: np.ndarray) -> np.ndarray:
    if values.ndim == 1:
        return values
    return np.nanmean(values, axis=1)


def _series_interpretation(
    overall: float,
    components: Mapping[str, float],
    left_name: str,
    right_name: str,
    reference_metrics: Mapping[str, float],
) -> str:
    ranked = sorted(components.items(), key=lambda kv: kv[1], reverse=True)
    strong = [name.replace("_", " ") for name, value in ranked if value >= 0.65][:2]
    weak = [name.replace("_", " ") for name, value in ranked if value <= 0.4][:2]
    metrics_text = []
    for key in ("pearson_r", "spearman_rho", "kendall_tau"):
        value = float(reference_metrics.get(key, float("nan")))
        if np.isfinite(value):
            metrics_text.append(f"{_reference_metric_label(key)} {value:.2f}")
    pearson = float(reference_metrics.get("pearson_r", float("nan")))
    diff_r = float(reference_metrics.get("first_difference_r", float("nan")))
    if metrics_text:
        sentence = f"{left_name} vs {right_name}: " + ", ".join(metrics_text) + "."
    elif overall >= 0.75:
        sentence = f"{left_name} and {right_name} line up strongly across several metrics."
    elif overall >= 0.55:
        sentence = f"{left_name} and {right_name} share noticeable structure, but the match is not one-to-one."
    elif overall >= 0.35:
        sentence = f"{left_name} and {right_name} have some overlapping structure, but the relationship is mixed."
    else:
        sentence = f"{left_name} and {right_name} do not line up consistently."
    if strong:
        sentence += " The best agreement appears in " + " and ".join(strong) + "."
    if np.isfinite(pearson) and np.isfinite(diff_r) and pearson >= 0.75 and diff_r <= 0.35:
        sentence += " The levels line up much more than the day-to-day changes, so the relationship is easier to defend as a broad shape analogy than as a local-dynamics match."
    if weak:
        sentence += " The weakest agreement appears in " + " and ".join(weak) + ", so timing or regime differences probably matter."
    return sentence


def _profile_from_input(obj: Any, *, name: str | None = None) -> tuple[DatasetProfile | SeriesProfile, str]:
    if isinstance(obj, (DatasetProfile, SeriesProfile)):
        return obj, name or getattr(obj.metadata, "name", None) or obj.metadata.get("name", obj.kind)
    profile = profile_dataset(obj)
    return profile, name or "dataset"


def compare_series(
    left: Any,
    right: Any,
    *,
    left_timestamps: Any | None = None,
    right_timestamps: Any | None = None,
    left_name: str = "left",
    right_name: str = "right",
    n_points: int = 256,
) -> SimilarityReport:
    """Compare two raw time-series inputs and return a shape-aware similarity report.

    The comparison mixes pointwise agreement, dynamic-time-warping, trend similarity,
    derivative similarity, and spectral similarity. Inputs may be univariate or
    multichannel. When channel counts differ, the function falls back to aggregate
    trajectories instead of forcing an arbitrary channel pairing.
    """

    left_rs = _resampled_multichannel(left, timestamps=left_timestamps, n_points=n_points)
    right_rs = _resampled_multichannel(right, timestamps=right_timestamps, n_points=n_points)
    left_cmp, right_cmp, channel_mode = _pair_multichannel(left_rs, right_rs)

    correlations = []
    pearson_corrs = []
    spearman_corrs = []
    kendall_corrs = []
    best_lag_corrs = []
    nmi_scores = []
    dtw_scores = []
    trend_scores = []
    derivative_scores = []
    derivative_corrs = []
    monotonic_pairs = []
    spectral_scores = []
    for idx in range(left_cmp.shape[1]):
        xl = left_cmp[:, idx]
        xr = right_cmp[:, idx]
        pearson = _safe_corr(xl, xr)
        pearson_corrs.append(pearson)
        spearman_corrs.append(_safe_spearman_corr(xl, xr))
        kendall_corrs.append(_safe_kendall_tau(xl, xr))
        best_lag_corrs.append(_best_lag_corr(xl, xr))
        nmi_scores.append(_normalized_mutual_information(xl, xr))

        diff_l = _difference_view(xl)
        diff_r = _difference_view(xr)
        trend_l = _smooth_trend(xl)
        trend_r = _smooth_trend(xr)
        trend_corr = _safe_corr(trend_l, trend_r)
        trend_change_corr = _safe_corr(_difference_view(trend_l), _difference_view(trend_r))
        trend_scores.append(_geometric_similarity(_corr_to_similarity(trend_corr), _corr_to_similarity(trend_change_corr)))

        derivative_corr = _safe_corr(diff_l, diff_r)
        derivative_corrs.append(derivative_corr)
        derivative_scores.append(_corr_to_similarity(derivative_corr))

        correlations.append(_geometric_similarity(_corr_to_similarity(pearson), _corr_to_similarity(derivative_corr)))
        dtw_scores.append(_strict_dtw_similarity(xl, xr))
        spectral_scores.append(_spectral_similarity(diff_l, diff_r))
        monotonic_pairs.append(min(_monotonic_fraction(xl), _monotonic_fraction(xr)))

    components = {
        "shape_similarity": float(np.nanmean(correlations)),
        "dtw_similarity": float(np.nanmean(dtw_scores)),
        "trend_similarity": float(np.nanmean(trend_scores)),
        "derivative_similarity": float(np.nanmean(derivative_scores)),
        "spectral_similarity": float(np.nanmean(spectral_scores)),
    }
    reference_metrics = {
        "pearson_r": float(np.nanmean(pearson_corrs)),
        "spearman_rho": float(np.nanmean(spearman_corrs)),
        "kendall_tau": float(np.nanmean(kendall_corrs)),
        "best_lag_pearson_r": float(np.nanmean(best_lag_corrs)),
        "normalized_mutual_information": float(np.nanmean(nmi_scores)),
        "first_difference_r": float(np.nanmean(derivative_corrs)),
    }

    weights = {
        "shape_similarity": 0.20,
        "dtw_similarity": 0.20,
        "trend_similarity": 0.20,
        "derivative_similarity": 0.25,
        "spectral_similarity": 0.15,
    }
    valid = [(key, value) for key, value in components.items() if np.isfinite(value)]
    if valid:
        weight_sum = sum(weights[key] for key, _ in valid)
        overall = float(sum(weights[key] * value for key, value in valid) / max(weight_sum, EPS))
    else:
        overall = 0.0
    component_mean = float(np.nanmean(list(components.values()))) if components else float("nan")

    notes: list[str] = []
    if channel_mode == "aggregate_channels":
        notes.append("Channel counts did not match, so the comparison used aggregate trajectories rather than one-to-one channel pairing.")
    monotone_like = bool(monotonic_pairs and np.nanmean(monotonic_pairs) >= 0.9)
    if monotone_like:
        notes.append("Both inputs look strongly monotonic or cumulative, so EchoTime tightened the comparison around first differences, differenced DTW, and differenced spectra.")
    if np.isfinite(reference_metrics["pearson_r"]) and np.isfinite(reference_metrics["spearman_rho"]) and abs(reference_metrics["spearman_rho"] - reference_metrics["pearson_r"]) >= 0.15:
        notes.append("Spearman is noticeably higher than Pearson, so rank-order agreement is stronger than strict linear agreement.")
    if np.isfinite(reference_metrics["pearson_r"]) and np.isfinite(reference_metrics["first_difference_r"]) and reference_metrics["pearson_r"] >= 0.75 and reference_metrics["first_difference_r"] <= 0.35:
        notes.append("Levels or cumulative trajectories are much closer than the first differences, so local change-by-change agreement is weaker than the headline coefficients suggest.")
    if components["trend_similarity"] - components["shape_similarity"] >= 0.2:
        notes.append("Broad trend agreement is stronger than point-by-point alignment, which often means the stories match better than the exact timing.")
    if components["spectral_similarity"] - components["shape_similarity"] >= 0.2:
        notes.append("Rhythms or periodic structure match more closely than exact levels, so cycle-aware comparisons may be more informative than raw overlays.")
    if components["dtw_similarity"] - components["shape_similarity"] >= 0.15:
        notes.append("Dynamic-time-warping similarity is stronger than direct shape correlation, suggesting similar patterns with shifted timing.")

    suggestions = [
        "Plot both series after z-score normalization to show the shared shape without scale differences.",
        "Run rolling or windowed similarity if you expect the relationship to change over time.",
        "Use structural-profile similarity when scales, frequencies, or observation modes differ too much for raw-shape comparison.",
    ]
    if monotone_like:
        suggestions.append("For cumulative or monotonic inputs, compare first differences or daily increments before making an analog claim.")
    if components["spectral_similarity"] >= 0.65:
        suggestions.append("Inspect spectral or seasonality-aware models because the two series share rhythm strongly.")
    if components["dtw_similarity"] >= 0.65 and components["shape_similarity"] < 0.55:
        suggestions.append("Try lag-aware alignment or event-based anchoring because the main mismatch may be timing rather than mechanism.")

    return SimilarityReport(
        left_name=left_name,
        right_name=right_name,
        mode="raw_series",
        similarity_score=overall,
        qualitative_label=_level(overall),
        component_scores=components,
        interpretation=_series_interpretation(overall, components, left_name, right_name, reference_metrics),
        reference_metrics=reference_metrics,
        notes=notes,
        suggestions=suggestions,
        metadata={
            "aggregate_method": "strict weighted component average",
            "component_mean": component_mean,
            "strictness_profile": "local_change_aware",
            "monotonic_like_inputs": monotone_like,
            "channel_mode": channel_mode,
            "resample_points": int(n_points),
            "left_channels": int(left_rs.shape[1]),
            "right_channels": int(right_rs.shape[1]),
        },
    )


def compare_profiles(
    left: Any,
    right: Any,
    *,
    left_name: str = "left profile",
    right_name: str = "right profile",
) -> SimilarityReport:
    """Compare two echotime profiles or raw inputs at the ontology-axis level."""

    left_profile, left_resolved_name = _profile_from_input(left, name=left_name)
    right_profile, right_resolved_name = _profile_from_input(right, name=right_name)

    left_axes = {k: float(v) for k, v in left_profile.axes.items()}
    right_axes = {k: float(v) for k, v in right_profile.axes.items()}
    keys = sorted(set(left_axes) | set(right_axes))
    axis_similarity = {key: float(np.clip(1.0 - abs(left_axes.get(key, 0.0) - right_axes.get(key, 0.0)), 0.0, 1.0)) for key in keys}

    groups = {
        "observation_similarity": ["sampling_irregularity", "noise_contamination"],
        "dynamic_similarity": [
            "predictability",
            "drift_nonstationarity",
            "trendness",
            "rhythmicity",
            "complexity",
            "nonlinearity_chaoticity",
            "eventness_burstiness",
            "regime_switching",
        ],
        "multivariate_similarity": ["coupling_networkedness", "heterogeneity"],
    }
    components = {
        name: float(np.nanmean([axis_similarity[k] for k in members if k in axis_similarity]))
        for name, members in groups.items()
    }
    components["overall_axis_similarity"] = float(np.nanmean(list(axis_similarity.values())))
    overall = components["overall_axis_similarity"]

    ranked_diffs = sorted(((key, abs(left_axes.get(key, 0.0) - right_axes.get(key, 0.0))) for key in keys), key=lambda kv: kv[1], reverse=True)
    most_different = [key.replace("_", " ") for key, diff in ranked_diffs[:2] if diff >= 0.2]
    strongest = [name.replace("_", " ") for name, score in sorted(components.items(), key=lambda kv: kv[1], reverse=True)[:2]]
    interpretation = f"{left_resolved_name} and {right_resolved_name} are {_level(overall)}ly similar at the structural-profile level."
    if strongest:
        interpretation += " The strongest agreement is in " + " and ".join(strongest) + "."
    if most_different:
        interpretation += " The biggest differences appear in " + " and ".join(most_different) + "."

    suggestions = [
        "Use profile similarity when you want to compare datasets collected on different scales but with comparable structure.",
        "Inspect the axis-level differences to explain why two datasets need different validation or model choices.",
        "Attach both dataset cards and the similarity report when presenting cross-domain analogies to non-method collaborators.",
    ]
    notes = [
        "Profile similarity compares ontology structure rather than raw point-by-point alignment.",
    ]
    return SimilarityReport(
        left_name=left_resolved_name,
        right_name=right_resolved_name,
        mode="profile",
        similarity_score=float(overall),
        qualitative_label=_level(float(overall)),
        component_scores=components,
        interpretation=interpretation,
        notes=notes,
        suggestions=suggestions,
        metadata={
            "left_domain": left_profile.metadata.get("domain", "generic"),
            "right_domain": right_profile.metadata.get("domain", "generic"),
            "left_observation_mode": left_profile.metadata.get("observation_mode", "dense"),
            "right_observation_mode": right_profile.metadata.get("observation_mode", "dense"),
            "axis_similarity": axis_similarity,
        },
    )


def rolling_similarity(
    left: Any,
    right: Any,
    *,
    window: int,
    step: int = 1,
    left_timestamps: Any | None = None,
    right_timestamps: Any | None = None,
    n_points: int = 128,
) -> list[dict[str, float]]:
    """Compute raw-series similarity over aligned rolling windows.

    This is designed for quick exploratory work such as 'when did BTC and gold start
    moving more alike?' or 'which launch week looks most like the current one?'.
    """

    left_arr = _normalize_channel_layout(_as_matrix(left))
    right_arr = _normalize_channel_layout(_as_matrix(right))
    min_len = min(left_arr.shape[0], right_arr.shape[0])
    if min_len < window or window < 4:
        return []
    out: list[dict[str, float]] = []
    for start in range(0, min_len - window + 1, step):
        stop = start + window
        lt = None if left_timestamps is None else np.asarray(left_timestamps)[start:stop]
        rt = None if right_timestamps is None else np.asarray(right_timestamps)[start:stop]
        report = compare_series(
            left_arr[start:stop],
            right_arr[start:stop],
            left_timestamps=lt,
            right_timestamps=rt,
            left_name="left_window",
            right_name="right_window",
            n_points=n_points,
        )
        out.append({
            "start": float(start),
            "stop": float(stop),
            "similarity_score": float(report.similarity_score),
            "component_mean": float(report.component_mean),
            "pearson_r": float(report.reference_metrics.get("pearson_r", float("nan"))),
            "spearman_rho": float(report.reference_metrics.get("spearman_rho", float("nan"))),
            "normalized_mutual_information": float(report.reference_metrics.get("normalized_mutual_information", float("nan"))),
            "first_difference_r": float(report.reference_metrics.get("first_difference_r", float("nan"))),
            "shape_similarity": float(report.component_scores.get("shape_similarity", float("nan"))),
            "trend_similarity": float(report.component_scores.get("trend_similarity", float("nan"))),
            "spectral_similarity": float(report.component_scores.get("spectral_similarity", float("nan"))),
        })
    return out
