"""Built-in metric plugins for multivariate, domain-aware, and irregular/event inputs."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .adapters import NormalizedDataset
from .context import ProfilingContext
from .metrics import (
    bandpower_ratio,
    channel_asynchrony,
    gap_fraction,
    interval_burstiness_from_timestamps,
    mark_cv,
    normalized_entropy,
    peak_prominence_ratio,
    simultaneity_fraction,
)
from .network import compute_inter_subject_similarity, compute_inter_subject_synchrony, compute_network_summary
from .registry import PluginResult


def _nanmean_dicts(dicts: Sequence[dict[str, float]]) -> dict[str, float]:
    if not dicts:
        return {}
    keys = sorted(set().union(*dicts))
    out: dict[str, float] = {}
    for key in keys:
        values = [d.get(key, np.nan) for d in dicts]
        finite = [float(v) for v in values if np.isfinite(v)]
        if finite:
            out[key] = float(np.mean(finite))
    return out


class NetworkMetricsPlugin:
    name = "network_metrics"

    def applies(self, normalized: NormalizedDataset, context: ProfilingContext) -> bool:
        return int(normalized.metadata.get("n_channels_median", 1)) > 1

    def compute(self, normalized: NormalizedDataset, context: ProfilingContext) -> PluginResult:
        labels = normalized.metadata.get("network_labels")
        per_subject: list[dict[str, float]] = []
        for subject in normalized.subjects:
            if subject.values.shape[1] < 2:
                continue
            usable_labels = None
            if labels is not None and len(labels) == subject.values.shape[1]:
                usable_labels = labels
            summary = compute_network_summary(subject.values, network_labels=usable_labels)
            per_subject.append(
                {
                    "graph_density_proxy": summary.graph_density_proxy,
                    "graph_clustering_proxy": summary.graph_clustering_proxy,
                    "network_state_transition_rate": summary.network_state_transition_rate,
                    "network_modularity_gap": summary.network_modularity_gap,
                    "network_modularity_volatility": summary.network_modularity_volatility,
                }
            )
        metrics = _nanmean_dicts(per_subject)
        inter_subject_similarity = compute_inter_subject_similarity(normalized.subjects)
        if np.isfinite(inter_subject_similarity):
            metrics["inter_subject_similarity"] = float(inter_subject_similarity)
        notes: list[str] = []
        if labels is not None:
            n_channels = int(normalized.metadata.get("n_channels_median", 0))
            if len(labels) != n_channels:
                notes.append("Network labels were provided but their length does not match the channel count, so modularity-style metrics were skipped.")
        return PluginResult(metrics=metrics, notes=notes)


class IrregularObservationPlugin:
    name = "irregular_observation"

    def applies(self, normalized: NormalizedDataset, context: ProfilingContext) -> bool:
        return str(normalized.metadata.get("observation_mode", "dense")).lower() in {"irregular", "mixed"}

    def compute(self, normalized: NormalizedDataset, context: ProfilingContext) -> PluginResult:
        coverage: list[float] = []
        gaps: list[float] = []
        asynchrony: list[float] = []
        count_cv: list[float] = []
        for subject in normalized.subjects:
            if subject.observation_mode != "irregular":
                continue
            mask = np.isfinite(subject.values)
            if mask.size:
                coverage.append(float(np.mean(mask)))
                counts = np.sum(mask, axis=0)
                if counts.size >= 2 and float(np.mean(counts)) > 0:
                    count_cv.append(float(np.std(counts) / (np.mean(counts) + 1e-12)))
                async_score = channel_asynchrony(mask)
                if np.isfinite(async_score):
                    asynchrony.append(float(async_score))
            channel_ts = subject.channel_timestamps or []
            channel_gap = [gap_fraction(ts) for ts in channel_ts if ts is not None]
            channel_gap = [float(value) for value in channel_gap if np.isfinite(value)]
            if channel_gap:
                gaps.append(float(np.mean(channel_gap)))

        metrics: dict[str, float] = {}
        if coverage:
            metrics["coverage_ratio"] = float(np.mean(coverage))
            metrics["coverage_inverse"] = float(np.clip(1.0 - np.mean(coverage), 0.0, 1.0))
        if gaps:
            metrics["gap_fraction"] = float(np.mean(gaps))
        if asynchrony:
            metrics["channel_asynchrony"] = float(np.mean(asynchrony))
        if count_cv:
            metrics["observation_count_cv"] = float(np.mean(count_cv))
        notes = [
            "Irregular inputs are profiled without interpolation; when explicit timestamps are available, spectral proxies use Lomb-Scargle style irregular-spectrum estimates.",
        ]
        return PluginResult(metrics=metrics, notes=notes)


class EventStreamPlugin:
    name = "event_stream"

    def applies(self, normalized: NormalizedDataset, context: ProfilingContext) -> bool:
        return str(normalized.metadata.get("observation_mode", "dense")).lower() == "event_stream"

    def compute(self, normalized: NormalizedDataset, context: ProfilingContext) -> PluginResult:
        burstiness: list[float] = []
        diversity: list[float] = []
        simultaneity: list[float] = []
        mark_variation: list[float] = []
        event_rate_per_span: list[float] = []
        for subject in normalized.subjects:
            if subject.observation_mode != "event_stream":
                continue
            b = interval_burstiness_from_timestamps(subject.event_timestamps)
            if np.isfinite(b):
                burstiness.append(float(b))
            labels: list[object] | None = None
            if subject.event_types:
                labels = list(subject.event_types)
            elif subject.event_channels is not None and subject.event_channels.size:
                labels = [int(x) for x in subject.event_channels.tolist()]
            e = normalized_entropy(labels)
            if np.isfinite(e):
                diversity.append(float(e))
            s = simultaneity_fraction(subject.event_timestamps)
            if np.isfinite(s):
                simultaneity.append(float(s))
            v = mark_cv(subject.event_values)
            if np.isfinite(v):
                mark_variation.append(float(v))
            if subject.event_timestamps is not None and subject.event_timestamps.size >= 2:
                span = float(np.max(subject.event_timestamps) - np.min(subject.event_timestamps))
                if span > 0:
                    event_rate_per_span.append(float(subject.event_timestamps.size / span))

        metrics: dict[str, float] = {}
        if burstiness:
            metrics["event_interval_burstiness"] = float(np.mean(burstiness))
        if diversity:
            metrics["event_type_entropy"] = float(np.mean(diversity))
        if simultaneity:
            metrics["event_simultaneity"] = float(np.mean(simultaneity))
        if mark_variation:
            metrics["event_mark_cv"] = float(np.mean(mark_variation))
        if event_rate_per_span:
            metrics["event_rate_per_span"] = float(np.mean(event_rate_per_span))
        notes = [
            "Event streams are lifted into sparse channel-wise count/value panels for generic ontology scoring; event-specific burstiness and diversity are reported separately.",
        ]
        return PluginResult(metrics=metrics, notes=notes)


class FMRIMetricsPlugin:
    name = "fmri_metrics"

    def applies(self, normalized: NormalizedDataset, context: ProfilingContext) -> bool:
        return str(normalized.metadata.get("domain", context.resolved_domain)).lower() == "fmri"

    def compute(self, normalized: NormalizedDataset, context: ProfilingContext) -> PluginResult:
        sampling_rate = normalized.metadata.get("sampling_rate")
        metrics: dict[str, float] = {}
        per_unit_lf: list[float] = []
        notes: list[str] = []

        if sampling_rate is None or not np.isfinite(float(sampling_rate)):
            notes.append("fMRI profiling ran without TR/sampling-rate information, so Hz-aware low-frequency metrics were skipped.")
        else:
            fs = float(sampling_rate)
            nyquist = fs / 2.0
            total_high = min(0.25, nyquist - 1e-6)
            if total_high > 0.011:
                for subject in normalized.subjects:
                    for idx in range(subject.values.shape[1]):
                        value = bandpower_ratio(subject.values[:, idx], fs=fs, low=0.01, high=min(0.1, nyquist - 1e-6), total_low=0.01, total_high=total_high, timestamps=subject.timestamps)
                        if np.isfinite(value):
                            per_unit_lf.append(float(value))
            else:
                notes.append("Sampling rate was too low to estimate the canonical fMRI low-frequency band.")

        if per_unit_lf:
            metrics["fmri_low_frequency_ratio"] = float(np.mean(per_unit_lf))

        synchrony = compute_inter_subject_synchrony(normalized.subjects)
        if np.isfinite(synchrony):
            metrics["inter_subject_synchrony"] = float(synchrony)

        labels = normalized.metadata.get("network_labels")
        if labels is None:
            notes.append("No network labels were provided, so within-vs-between network organization was estimated only from generic graph metrics.")

        return PluginResult(metrics=metrics, notes=notes)


class EEGBandpowerPlugin:
    name = "eeg_bandpower"

    def applies(self, normalized: NormalizedDataset, context: ProfilingContext) -> bool:
        return str(normalized.metadata.get("domain", context.resolved_domain)).lower() == "eeg"

    def compute(self, normalized: NormalizedDataset, context: ProfilingContext) -> PluginResult:
        sampling_rate = normalized.metadata.get("sampling_rate")
        if sampling_rate is None or not np.isfinite(float(sampling_rate)):
            return PluginResult(notes=["EEG profiling ran without sampling-rate information, so bandpower metrics were skipped."])
        fs = float(sampling_rate)
        nyquist = fs / 2.0
        total_high = min(45.0, nyquist - 1e-6)
        if total_high <= 1.0:
            return PluginResult(notes=["Sampling rate was too low for EEG bandpower metrics."])

        bands = {
            "eeg_delta_ratio": (1.0, min(4.0, total_high)),
            "eeg_theta_ratio": (4.0, min(8.0, total_high)),
            "eeg_alpha_ratio": (8.0, min(12.0, total_high)),
            "eeg_beta_ratio": (12.0, min(30.0, total_high)),
            "eeg_gamma_ratio": (30.0, min(45.0, total_high)),
        }
        values: dict[str, list[float]] = {name: [] for name in bands}
        alpha_peaks: list[float] = []

        for subject in normalized.subjects:
            for idx in range(subject.values.shape[1]):
                series = subject.values[:, idx]
                for name, (low, high) in bands.items():
                    if high > low:
                        value = bandpower_ratio(series, fs=fs, low=low, high=high, total_low=1.0, total_high=total_high, timestamps=subject.timestamps)
                        if np.isfinite(value):
                            values[name].append(float(value))
                alpha_peak = peak_prominence_ratio(series, fs=fs, low=8.0, high=min(12.0, total_high), timestamps=subject.timestamps)
                if np.isfinite(alpha_peak):
                    alpha_peaks.append(float(alpha_peak))

        metrics = {name: float(np.mean(v)) for name, v in values.items() if v}
        if alpha_peaks:
            metrics["alpha_peak_prominence"] = float(np.mean(alpha_peaks))
        return PluginResult(metrics=metrics)
