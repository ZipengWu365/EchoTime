"""Heuristic archetype and task-hint inference from ontology axes."""

from __future__ import annotations

from typing import Any


def infer_archetypes(axes: dict[str, float], metadata: dict[str, Any], metrics: dict[str, float] | None = None) -> list[str]:
    tags: list[str] = []
    domain = str(metadata.get("domain", "generic")).lower()
    observation_mode = str(metadata.get("observation_mode", "dense")).lower()
    metrics = metrics or {}

    if axes.get("rhythmicity", 0.0) > 0.65 and axes.get("predictability", 0.0) > 0.55:
        tags.append("quasi_periodic")
    if axes.get("trendness", 0.0) > 0.55 and axes.get("drift_nonstationarity", 0.0) > 0.45:
        tags.append("drifting")
    elif axes.get("trendness", 0.0) > 0.55:
        tags.append("trend_dominated")
    if axes.get("eventness_burstiness", 0.0) > 0.60:
        tags.append("event_driven")
    if axes.get("regime_switching", 0.0) > 0.55:
        tags.append("regime_switching")
    if axes.get("complexity", 0.0) > 0.65 and axes.get("nonlinearity_chaoticity", 0.0) > 0.45:
        tags.append("complex_nonlinear")
    if axes.get("coupling_networkedness", 0.0) > 0.55 and metadata.get("n_channels_median", 1) > 1:
        tags.append("strongly_coupled_multivariate")
    if metrics.get("network_modularity_gap", 0.0) > 0.12 and metadata.get("n_channels_median", 1) > 1:
        tags.append("modular_networked")
    if axes.get("heterogeneity", 0.0) > 0.55 and metadata.get("n_subjects", 1) > 1:
        tags.append("heterogeneous_cohort")
    if axes.get("sampling_irregularity", 0.0) > 0.55:
        tags.append("irregularly_sampled")
    if bool(metadata.get("longitudinal_mode", False)):
        tags.append("longitudinal_cohort")
        if metrics.get("subject_fingerprintability", 0.0) > 0.30:
            tags.append("subject_specific_longitudinal")
    if axes.get("noise_contamination", 0.0) > 0.60:
        tags.append("noisy_observation")

    if observation_mode == "irregular":
        tags.append("sparse_monitoring")
        if metrics.get("channel_asynchrony", 0.0) > 0.55:
            tags.append("asynchronous_multichannel")
    elif observation_mode == "event_stream":
        tags.append("event_stream")
        if metrics.get("event_interval_burstiness", 0.0) > 0.60:
            tags.append("bursty_event_stream")

    if domain == "wearable":
        tags.append("wearable_monitoring")
    elif domain == "clinical":
        tags.append("clinical_longitudinal")

    if domain == "fmri":
        tags.append("networked_neurodynamic")
        if metrics.get("fmri_low_frequency_ratio", 0.0) > 0.45:
            tags.append("low_frequency_bold_dynamics")
    elif domain == "eeg":
        tags.append("oscillatory_neurophysiological")
        if metrics.get("eeg_alpha_ratio", 0.0) > 0.25:
            tags.append("alpha_dominant")

    deduped: list[str] = []
    for tag in tags:
        if tag not in deduped:
            deduped.append(tag)
    return deduped or ["mixed_structure"]


def infer_task_hints(axes: dict[str, float], metadata: dict[str, Any], metrics: dict[str, float] | None = None) -> list[str]:
    hints: list[str] = []
    domain = str(metadata.get("domain", "generic")).lower()
    observation_mode = str(metadata.get("observation_mode", "dense")).lower()
    metrics = metrics or {}

    if axes.get("predictability", 0.0) > 0.60 and axes.get("rhythmicity", 0.0) > 0.50 and axes.get("drift_nonstationarity", 0.0) < 0.40:
        hints.append("Classical forecasting baselines should be competitive; include seasonal-naive, harmonic, and linear autoregressive baselines.")
    if axes.get("drift_nonstationarity", 0.0) > 0.55 or axes.get("regime_switching", 0.0) > 0.55:
        hints.append("Prefer rolling evaluation and time-aware validation; online, state-space, or switching models are likely relevant.")
    if axes.get("coupling_networkedness", 0.0) > 0.50 and metadata.get("n_channels_median", 1) > 1:
        hints.append("Benchmark multivariate and graph-aware models; independent per-channel models will likely discard signal.")
    if metrics.get("network_modularity_gap", 0.0) > 0.12:
        hints.append("Community-aware representations may matter because within-network dependence appears stronger than between-network dependence.")
    if axes.get("heterogeneity", 0.0) > 0.50 and metadata.get("n_subjects", 1) > 1:
        hints.append("Use subject-aware splits or stratification; representation learning and personalization may matter.")
    if axes.get("eventness_burstiness", 0.0) > 0.60:
        hints.append("Event detection, anomaly detection, or point-process style summaries may be more informative than only point forecasting.")
    if axes.get("noise_contamination", 0.0) > 0.55:
        hints.append("Include denoising or robust preprocessing baselines and report sensitivity analyses.")

    if observation_mode == "irregular":
        hints.append("Benchmark irregular-time models or continuous-time/state-space baselines; avoid evaluating only on resampled regular grids.")
        if metrics.get("channel_asynchrony", 0.0) > 0.50:
            hints.append("Channels are observed asynchronously; models that treat missingness and observation timing as signal should be prioritized.")
        if metrics.get("irregular_spectral_support", 0.0) > 0.0:
            hints.append("Timestamp-aware spectral estimators are available; do not benchmark only order-based resampling baselines for frequency-sensitive tasks.")
    elif observation_mode == "event_stream":
        hints.append("Evaluate point-process, neural event, or set/sequence models alongside discretized baselines; event timing itself carries signal.")
        if metrics.get("event_type_entropy", 0.0) > 0.50:
            hints.append("Event-type diversity is substantial; report both timing performance and event-type discrimination or embedding quality.")

    if domain == "fmri":
        hints.append("For neuroimaging, report both node-level and connectivity-level results; time-series-only baselines can miss dynamic network structure.")
        if metadata.get("n_subjects", 1) > 1:
            hints.append("For cohort neuroimaging studies, separate within-subject dynamics from between-subject heterogeneity in evaluation and reporting.")
    if domain == "eeg":
        hints.append("For EEG-like data, compare generic sequence models with frequency-aware baselines and report sensitivity to sampling rate and preprocessing.")
        if metrics.get("eeg_alpha_ratio", 0.0) > 0.25:
            hints.append("Alpha-band structure is prominent; band-limited representations and oscillation-aware augmentations may be especially informative.")
    if not hints:
        hints.append("No single structure axis dominates; a balanced benchmark with strong classical and modern baselines is appropriate.")
    return hints
