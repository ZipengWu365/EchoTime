"""Reliability and evidence summaries for ontology scores."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from .axes import AXIS_ORDER, observed_proxy_fraction


@dataclass(slots=True)
class AxisReliability:
    score: float
    level: str
    proxy_coverage: float
    data_support: float
    bootstrap_std: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    caveats: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["caveats"] = list(self.caveats or [])
        return payload


@dataclass(slots=True)
class ReliabilitySummary:
    overall_score: float
    overall_level: str
    method: str
    axes: dict[str, AxisReliability]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": float(self.overall_score),
            "overall_level": self.overall_level,
            "method": self.method,
            "axes": {axis: info.to_dict() for axis, info in self.axes.items()},
            "notes": list(self.notes),
        }


@dataclass(slots=True)
class BootstrapIntervals:
    n_resamples: int
    per_axis_samples: dict[str, list[float]]

    def summary(self) -> dict[str, dict[str, float]]:
        out: dict[str, dict[str, float]] = {}
        for axis, samples in self.per_axis_samples.items():
            if not samples:
                continue
            arr = np.asarray(samples, dtype=float)
            out[axis] = {
                "ci_low": float(np.quantile(arr, 0.05)),
                "ci_high": float(np.quantile(arr, 0.95)),
                "bootstrap_std": float(np.std(arr)),
            }
        return out


@dataclass(slots=True)
class EvidenceSummary:
    length_median: int
    n_subjects: int
    n_channels_median: int
    n_series_units: int
    n_visit_units: int
    has_timestamps: bool
    has_sampling_rate: bool
    domain: str
    observation_mode: str
    longitudinal_mode: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _level(score: float) -> str:
    if score >= 0.85:
        return "very high"
    if score >= 0.65:
        return "high"
    if score >= 0.45:
        return "moderate"
    if score >= 0.25:
        return "low"
    return "very low"


def evidence_from_metadata(metadata: Mapping[str, Any]) -> EvidenceSummary:
    return EvidenceSummary(
        length_median=int(metadata.get("length_median", metadata.get("length", 0) or 0)),
        n_subjects=int(metadata.get("n_subjects", 1) or 1),
        n_channels_median=int(metadata.get("n_channels_median", 1) or 1),
        n_series_units=int(metadata.get("n_series_units", 1) or 1),
        n_visit_units=int(metadata.get("n_visit_units", metadata.get("n_series_units", 1) or 1)),
        has_timestamps=bool(metadata.get("has_timestamps", False)),
        has_sampling_rate=metadata.get("sampling_rate") is not None or metadata.get("tr") is not None,
        domain=str(metadata.get("domain", "generic")),
        observation_mode=str(metadata.get("observation_mode", "dense")),
        longitudinal_mode=bool(metadata.get("longitudinal_mode", False)),
    )


def _length_support(length: int) -> float:
    if length >= 256:
        return 1.0
    if length >= 128:
        return 0.9
    if length >= 64:
        return 0.75
    if length >= 32:
        return 0.55
    if length >= 16:
        return 0.35
    return 0.15


def _axis_data_support(axis: str, evidence: EvidenceSummary) -> float:
    length_support = _length_support(evidence.length_median)
    observation_mode = evidence.observation_mode.lower()
    if axis == "sampling_irregularity":
        return 1.0 if evidence.has_timestamps else 0.40
    if axis == "coupling_networkedness":
        if evidence.n_channels_median >= 8:
            return min(1.0, 0.55 + 0.45 * length_support)
        if evidence.n_channels_median >= 2:
            return min(0.85, 0.45 + 0.40 * length_support)
        return 0.12
    if axis == "heterogeneity":
        if evidence.longitudinal_mode and evidence.n_visit_units >= 6 and evidence.n_subjects >= 2:
            return 0.9
        if evidence.n_subjects >= 8:
            return 1.0
        if evidence.n_subjects >= 3:
            return 0.8
        if evidence.n_subjects >= 2:
            return 0.65
        if evidence.n_series_units >= 4:
            return 0.5
        if evidence.n_series_units >= 2:
            return 0.35
        return 0.12
    if axis == "regime_switching":
        return min(1.0, 0.15 + 0.95 * _length_support(max(evidence.length_median - 16, 0)))
    if axis in {"complexity", "nonlinearity_chaoticity", "drift_nonstationarity"}:
        support = min(1.0, 0.10 + 0.95 * length_support)
    elif axis in {"rhythmicity", "predictability", "trendness", "noise_contamination", "eventness_burstiness"}:
        support = min(1.0, 0.20 + 0.85 * length_support)
    else:
        support = length_support
    if observation_mode == "event_stream" and axis in {"rhythmicity", "predictability", "trendness", "noise_contamination"}:
        support *= 0.80
    elif observation_mode in {"irregular", "mixed"} and axis in {"rhythmicity", "predictability", "trendness", "noise_contamination"}:
        support *= 0.92
    return float(support)


def _bootstrap_precision(ci_low: float | None, ci_high: float | None) -> float | None:
    if ci_low is None or ci_high is None or not np.isfinite(ci_low) or not np.isfinite(ci_high):
        return None
    width = max(0.0, float(ci_high) - float(ci_low))
    return float(np.clip(1.0 - width / 0.60, 0.0, 1.0))


def _axis_caveats(axis: str, evidence: EvidenceSummary, coverage: float, ci_low: float | None, ci_high: float | None) -> list[str]:
    caveats: list[str] = []
    observation_mode = evidence.observation_mode.lower()
    if coverage < 0.5:
        caveats.append("Proxy coverage is partial for this axis under the current data and domain settings.")
    if axis == "sampling_irregularity" and not evidence.has_timestamps:
        caveats.append("Without explicit timestamps, irregularity is inferred mainly from missingness rather than from the observation grid.")
    if axis == "coupling_networkedness" and evidence.n_channels_median < 2:
        caveats.append("Cross-channel dependence is weakly supported for univariate data.")
    if axis == "heterogeneity" and evidence.n_subjects < 2 and evidence.n_series_units < 2:
        caveats.append("Heterogeneity is nearly trivial when only one unit is available.")
    if axis == "regime_switching" and evidence.length_median < 64:
        caveats.append("Regime-style metrics are length-sensitive and can be unstable on short series.")
    if axis in {"complexity", "nonlinearity_chaoticity"} and evidence.length_median < 64:
        caveats.append("Complexity and nonlinearity proxies are less stable on short sequences.")
    if observation_mode == "event_stream" and axis in {"rhythmicity", "predictability", "trendness", "noise_contamination"}:
        caveats.append("Event-timed observations still require conservative interpretation for frequency-aware axes because arrival processes are not equivalent to densely sampled amplitudes.")
    elif observation_mode in {"irregular", "mixed"} and axis in {"rhythmicity", "predictability", "trendness", "noise_contamination"}:
        caveats.append("Irregular observations use timestamp-aware spectral estimators when possible, but very sparse or highly gappy series still warrant conservative interpretation.")
    if evidence.longitudinal_mode and axis in {"heterogeneity", "sampling_irregularity"} and evidence.n_visit_units < max(4, evidence.n_subjects * 2):
        caveats.append("Longitudinal support is present but repeated visits are still limited, so follow-up and repeatability estimates may be noisy.")
    if ci_low is not None and ci_high is not None and (ci_high - ci_low) > 0.25:
        caveats.append("Bootstrap interval is wide relative to the axis scale, so uncertainty is non-trivial.")
    return caveats


def summarize_reliability(
    *,
    axes: Mapping[str, float],
    metrics: Mapping[str, float],
    metadata: Mapping[str, Any],
    bootstrap: BootstrapIntervals | None = None,
) -> tuple[ReliabilitySummary, EvidenceSummary]:
    evidence = evidence_from_metadata(metadata)
    bootstrap_summary = bootstrap.summary() if bootstrap is not None else {}

    axis_payload: dict[str, AxisReliability] = {}
    notes: list[str] = []
    method = "heuristic"
    if bootstrap is not None and bootstrap.n_resamples > 0:
        method = f"heuristic+bootstrap({bootstrap.n_resamples})"
        notes.append("Bootstrap intervals summarize resampling variability of subject- or unit-level axis profiles.")
        notes.append("Bootstrap uncertainty is approximate for cross-subject metrics such as synchrony and other dataset-level plugins.")
    else:
        notes.append("Reliability scores combine proxy coverage and data-support heuristics.")

    if evidence.observation_mode.lower() == "event_stream":
        notes.append("Event-timed inputs receive conservative reliability penalties for dense-grid spectral proxies.")
    elif evidence.observation_mode.lower() in {"irregular", "mixed"}:
        notes.append("Irregular inputs use timestamp-aware spectral estimators when timestamps are available, but frequency-aware axes remain conservative under heavy gaps or sparse support.")
    if evidence.longitudinal_mode:
        notes.append("Longitudinal mode is active: repeated-visit stability and follow-up irregularity can improve interpretability, but only when enough visits per subject are available.")

    for axis in AXIS_ORDER:
        coverage = observed_proxy_fraction(dict(metrics), axis)
        support = _axis_data_support(axis, evidence)
        ci_low = bootstrap_summary.get(axis, {}).get("ci_low")
        ci_high = bootstrap_summary.get(axis, {}).get("ci_high")
        std = bootstrap_summary.get(axis, {}).get("bootstrap_std")
        precision = _bootstrap_precision(ci_low, ci_high)
        if precision is None:
            reliability_score = 0.5 * coverage + 0.5 * support
        else:
            reliability_score = 0.35 * coverage + 0.35 * support + 0.30 * precision
        reliability_score = float(np.clip(reliability_score, 0.0, 1.0))
        axis_payload[axis] = AxisReliability(
            score=reliability_score,
            level=_level(reliability_score),
            proxy_coverage=float(coverage),
            data_support=float(support),
            bootstrap_std=None if std is None else float(std),
            ci_low=None if ci_low is None else float(ci_low),
            ci_high=None if ci_high is None else float(ci_high),
            caveats=_axis_caveats(axis, evidence, coverage, ci_low, ci_high),
        )

    overall = float(np.mean([info.score for info in axis_payload.values()])) if axis_payload else 0.0
    return (
        ReliabilitySummary(
            overall_score=overall,
            overall_level=_level(overall),
            method=method,
            axes=axis_payload,
            notes=notes,
        ),
        evidence,
    )


def bootstrap_axis_intervals(
    profiles: Sequence[Mapping[str, float]],
    *,
    n_resamples: int = 0,
    random_state: int | None = None,
) -> BootstrapIntervals | None:
    if n_resamples <= 0 or len(profiles) < 2:
        return None
    rng = np.random.default_rng(random_state)
    matrix = np.asarray([[float(p.get(axis, np.nan)) for axis in AXIS_ORDER] for p in profiles], dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] < 2:
        return None
    col_means = np.nanmean(matrix, axis=0)
    if np.any(np.isnan(col_means)):
        col_means = np.where(np.isnan(col_means), 0.0, col_means)
    idx = np.where(~np.isfinite(matrix))
    matrix[idx] = np.take(col_means, idx[1])

    samples: dict[str, list[float]] = {axis: [] for axis in AXIS_ORDER}
    for _ in range(int(n_resamples)):
        take = rng.integers(0, matrix.shape[0], size=matrix.shape[0])
        subset = matrix[take]
        mean_profile = np.mean(subset, axis=0)
        for col, axis in enumerate(AXIS_ORDER):
            samples[axis].append(float(np.clip(mean_profile[col], 0.0, 1.0)))
    return BootstrapIntervals(n_resamples=int(n_resamples), per_axis_samples=samples)
