"""Public profiling API."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .adapters import EEGInput, FMRIInput, IrregularTimeSeriesInput, SubjectData
from .archetypes import infer_archetypes, infer_task_hints
from .axes import AXIS_ORDER, axis_contributors, compute_axes, compute_subdimensions, subdimension_contributors
from .context import ProfilingContext
from .metrics import (
    bandpower_ratio,
    channel_asynchrony,
    compute_multivariate_metrics,
    compute_series_metrics,
    gap_fraction,
    interval_burstiness_from_timestamps,
    mark_cv,
    normalized_entropy,
    peak_prominence_ratio,
    simultaneity_fraction,
)
from .network import compute_network_summary
from .registry import get_registry
from .reliability import bootstrap_axis_intervals, summarize_reliability
from .report import (
    BaseRenderableProfile,
    card_dict,
    format_card_json,
    format_card_markdown,
    format_markdown,
    format_text,
)
from .communication import (
    format_narrative_report,
    format_summary_card_json,
    format_summary_card_markdown,
    summary_card_dict,
)
from .schema import SCHEMA_VERSION

PACKAGE_VERSION = "0.17.0"


@dataclass(slots=True)
class SeriesProfile(BaseRenderableProfile):
    metadata: dict[str, Any]
    axes: dict[str, float]
    subdimensions: dict[str, dict[str, float]]
    axis_details: dict[str, dict[str, float]]
    subdimension_details: dict[str, dict[str, dict[str, float]]]
    metrics: dict[str, float]
    archetypes: list[str]
    task_hints: list[str]
    reliability: dict[str, Any]
    evidence: dict[str, Any]
    notes: list[str] = field(default_factory=list)
    plugin_metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    kind: str = "series"
    package_version: str = PACKAGE_VERSION
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "metadata": self.metadata,
            "axes": self.axes,
            "subdimensions": self.subdimensions,
            "axis_details": self.axis_details,
            "subdimension_details": self.subdimension_details,
            "metrics": self.metrics,
            "archetypes": self.archetypes,
            "task_hints": self.task_hints,
            "reliability": self.reliability,
            "evidence": self.evidence,
            "notes": self.notes,
            "plugin_metrics": self.plugin_metrics,
            "package_version": self.package_version,
            "schema_version": self.schema_version,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        return format_markdown(self)

    def to_text(self) -> str:
        return format_text(self)

    def to_card_dict(self) -> dict[str, object]:
        return card_dict(self)

    def to_card_json(self, *, indent: int = 2) -> str:
        return format_card_json(self, indent=indent)

    def to_card_markdown(self) -> str:
        return format_card_markdown(self)

    def to_summary_card_dict(self, *, audience: str = "general") -> dict[str, object]:
        return summary_card_dict(self, audience=audience)

    def to_summary_card_json(self, *, audience: str = "general", indent: int = 2) -> str:
        return format_summary_card_json(self, audience=audience, indent=indent)

    def to_summary_card_markdown(self, *, audience: str = "general") -> str:
        return format_summary_card_markdown(self, audience=audience)

    def to_narrative_report(self, *, audience: str = "general") -> str:
        return format_narrative_report(self, audience=audience)

    def to_html_report(self, *, audience: str = "general", title: str | None = None) -> str:
        from .visuals import profile_html_report

        return profile_html_report(self, audience=audience, title=title)

    def to_axis_radar_svg(self) -> str:
        from .visuals import profile_radar_svg

        return profile_radar_svg(self)


    def to_agent_context_dict(self, *, budget: str = "lean", audience: str = "general") -> dict[str, Any]:
        from .agent import agent_context

        return agent_context(self, budget=budget, audience=audience, format="dict")  # type: ignore[return-value]

    def to_agent_context_json(self, *, budget: str = "lean", audience: str = "general", indent: int = 2) -> str:
        import json as _json
        return _json.dumps(self.to_agent_context_dict(budget=budget, audience=audience), indent=indent)

    def to_agent_context_markdown(self, *, budget: str = "lean", audience: str = "general") -> str:
        from .agent import agent_context

        return agent_context(self, budget=budget, audience=audience, format="markdown")  # type: ignore[return-value]


@dataclass(slots=True)
class DatasetProfile(BaseRenderableProfile):
    metadata: dict[str, Any]
    axes: dict[str, float]
    subdimensions: dict[str, dict[str, float]]
    axis_details: dict[str, dict[str, float]]
    subdimension_details: dict[str, dict[str, dict[str, float]]]
    metrics: dict[str, float]
    archetypes: list[str]
    task_hints: list[str]
    reliability: dict[str, Any]
    evidence: dict[str, Any]
    per_subject_axes: list[dict[str, float]] = field(default_factory=list)
    per_unit_axes: list[dict[str, float]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    plugin_metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    kind: str = "dataset"
    package_version: str = PACKAGE_VERSION
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "metadata": self.metadata,
            "axes": self.axes,
            "subdimensions": self.subdimensions,
            "axis_details": self.axis_details,
            "subdimension_details": self.subdimension_details,
            "metrics": self.metrics,
            "archetypes": self.archetypes,
            "task_hints": self.task_hints,
            "reliability": self.reliability,
            "evidence": self.evidence,
            "per_subject_axes": self.per_subject_axes,
            "per_unit_axes": self.per_unit_axes,
            "notes": self.notes,
            "plugin_metrics": self.plugin_metrics,
            "package_version": self.package_version,
            "schema_version": self.schema_version,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        return format_markdown(self)

    def to_text(self) -> str:
        return format_text(self)

    def to_card_dict(self) -> dict[str, object]:
        return card_dict(self)

    def to_card_json(self, *, indent: int = 2) -> str:
        return format_card_json(self, indent=indent)

    def to_card_markdown(self) -> str:
        return format_card_markdown(self)

    def to_summary_card_dict(self, *, audience: str = "general") -> dict[str, object]:
        return summary_card_dict(self, audience=audience)

    def to_summary_card_json(self, *, audience: str = "general", indent: int = 2) -> str:
        return format_summary_card_json(self, audience=audience, indent=indent)

    def to_summary_card_markdown(self, *, audience: str = "general") -> str:
        return format_summary_card_markdown(self, audience=audience)

    def to_narrative_report(self, *, audience: str = "general") -> str:
        return format_narrative_report(self, audience=audience)

    def to_html_report(self, *, audience: str = "general", title: str | None = None) -> str:
        from .visuals import profile_html_report

        return profile_html_report(self, audience=audience, title=title)

    def to_axis_radar_svg(self) -> str:
        from .visuals import profile_radar_svg

        return profile_radar_svg(self)

    def to_agent_context_dict(self, *, budget: str = "lean", audience: str = "general") -> dict[str, Any]:
        from .agent import agent_context

        return agent_context(self, budget=budget, audience=audience, format="dict")  # type: ignore[return-value]

    def to_agent_context_json(self, *, budget: str = "lean", audience: str = "general", indent: int = 2) -> str:
        import json as _json
        return _json.dumps(self.to_agent_context_dict(budget=budget, audience=audience), indent=indent)

    def to_agent_context_markdown(self, *, budget: str = "lean", audience: str = "general") -> str:
        from .agent import agent_context

        return agent_context(self, budget=budget, audience=audience, format="markdown")  # type: ignore[return-value]


def _nanmean_dicts(dicts: list[dict[str, float]]) -> dict[str, float]:
    if not dicts:
        return {}
    keys = sorted(set().union(*dicts))
    out: dict[str, float] = {}
    for key in keys:
        values = [d.get(key, np.nan) for d in dicts]
        finite = [float(v) for v in values if np.isfinite(v)]
        out[key] = float(np.mean(finite)) if finite else float("nan")
    return out


def _pairwise_distance(profiles: list[dict[str, float]]) -> float:
    if len(profiles) < 2:
        return 0.0
    matrix = []
    for p in profiles:
        matrix.append([float(p.get(axis, np.nan)) for axis in AXIS_ORDER])
    arr = np.asarray(matrix, dtype=float)
    if arr.size == 0:
        return 0.0
    if np.any(~np.isfinite(arr)):
        col_means = np.nanmean(arr, axis=0)
        col_means = np.where(np.isfinite(col_means), col_means, 0.0)
        inds = np.where(~np.isfinite(arr))
        arr[inds] = np.take(col_means, inds[1])
    distances = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            distances.append(float(np.linalg.norm(arr[i] - arr[j]) / np.sqrt(arr.shape[1])))
    return float(np.mean(distances)) if distances else 0.0


def _build_context(
    *,
    domain: str | None,
    timestamps: Any | list[Any] | tuple[Any, ...] | None,
    time_axis: int,
    channel_axis: int | None,
    subject_axis: int,
    sampling_rate: float | None,
    tr: float | None,
    channel_names: list[str] | None,
    roi_names: list[str] | None,
    network_labels: list[str] | None,
    subject_ids: list[str] | None,
    metadata: dict[str, Any] | None,
) -> ProfilingContext:
    return ProfilingContext(
        domain=domain,
        timestamps=timestamps,
        time_axis=time_axis,
        channel_axis=channel_axis,
        subject_axis=subject_axis,
        sampling_rate=sampling_rate,
        tr=tr,
        channel_names=channel_names,
        roi_names=roi_names,
        network_labels=network_labels,
        subject_ids=subject_ids,
        extra_metadata=dict(metadata or {}),
    )


def _subject_network_metrics(subject: SubjectData, network_labels: list[str] | None) -> dict[str, float]:
    if subject.values.shape[1] < 2:
        return {}
    usable_labels = None
    if network_labels is not None and len(network_labels) == subject.values.shape[1]:
        usable_labels = network_labels
    summary = compute_network_summary(subject.values, network_labels=usable_labels)
    return {
        "graph_density_proxy": summary.graph_density_proxy,
        "graph_clustering_proxy": summary.graph_clustering_proxy,
        "network_state_transition_rate": summary.network_state_transition_rate,
        "network_modularity_gap": summary.network_modularity_gap,
        "network_modularity_volatility": summary.network_modularity_volatility,
    }


def _subject_domain_metrics(subject: SubjectData, metadata: dict[str, Any]) -> dict[str, float]:
    domain = str(metadata.get("domain", "generic")).lower()
    sampling_rate = metadata.get("sampling_rate")
    metrics: dict[str, float] = {}
    if sampling_rate is None or not np.isfinite(float(sampling_rate)):
        return metrics
    fs = float(sampling_rate)
    nyquist = fs / 2.0

    if domain == "fmri":
        total_high = min(0.25, nyquist - 1e-6)
        values: list[float] = []
        if total_high > 0.011:
            for idx in range(subject.values.shape[1]):
                value = bandpower_ratio(subject.values[:, idx], fs=fs, low=0.01, high=min(0.1, nyquist - 1e-6), total_low=0.01, total_high=total_high, timestamps=subject.timestamps)
                if np.isfinite(value):
                    values.append(float(value))
        if values:
            metrics["fmri_low_frequency_ratio"] = float(np.mean(values))
    elif domain == "eeg":
        total_high = min(45.0, nyquist - 1e-6)
        if total_high > 1.0:
            bands = {
                "eeg_delta_ratio": (1.0, min(4.0, total_high)),
                "eeg_theta_ratio": (4.0, min(8.0, total_high)),
                "eeg_alpha_ratio": (8.0, min(12.0, total_high)),
                "eeg_beta_ratio": (12.0, min(30.0, total_high)),
                "eeg_gamma_ratio": (30.0, min(45.0, total_high)),
            }
            values: dict[str, list[float]] = {name: [] for name in bands}
            alpha_peaks: list[float] = []
            for idx in range(subject.values.shape[1]):
                series = subject.values[:, idx]
                for name, (low, high) in bands.items():
                    if high > low:
                        value = bandpower_ratio(series, fs=fs, low=low, high=high, total_low=1.0, total_high=total_high, timestamps=subject.timestamps)
                        if np.isfinite(value):
                            values[name].append(float(value))
                peak = peak_prominence_ratio(series, fs=fs, low=8.0, high=min(12.0, total_high), timestamps=subject.timestamps)
                if np.isfinite(peak):
                    alpha_peaks.append(float(peak))
            metrics.update({name: float(np.mean(v)) for name, v in values.items() if v})
            if alpha_peaks:
                metrics["alpha_peak_prominence"] = float(np.mean(alpha_peaks))
    return metrics


def _subject_observation_metrics(subject: SubjectData) -> dict[str, float]:
    metrics: dict[str, float] = {}
    if subject.observation_mode == "irregular":
        mask = np.isfinite(subject.values)
        if mask.size:
            async_score = channel_asynchrony(mask)
            if np.isfinite(async_score):
                metrics["channel_asynchrony"] = float(async_score)
            counts = np.sum(mask, axis=0)
            if counts.size >= 2 and float(np.mean(counts)) > 0:
                metrics["observation_count_cv"] = float(np.std(counts) / (np.mean(counts) + 1e-12))
            metrics["coverage_ratio"] = float(np.mean(mask))
            metrics["coverage_inverse"] = float(np.clip(1.0 - np.mean(mask), 0.0, 1.0))
        gaps = [gap_fraction(ts) for ts in (subject.channel_timestamps or []) if ts is not None]
        gaps = [float(value) for value in gaps if np.isfinite(value)]
        if gaps:
            metrics["gap_fraction"] = float(np.mean(gaps))
    elif subject.observation_mode == "event_stream":
        gap = gap_fraction(subject.event_timestamps if subject.event_timestamps is not None else subject.timestamps)
        if np.isfinite(gap):
            metrics["gap_fraction"] = float(gap)
    return metrics


def _subject_event_metrics(subject: SubjectData) -> dict[str, float]:
    metrics: dict[str, float] = {}
    if subject.observation_mode != "event_stream":
        return metrics
    burst = interval_burstiness_from_timestamps(subject.event_timestamps)
    if np.isfinite(burst):
        metrics["event_interval_burstiness"] = float(burst)
    labels: list[object] | None = None
    if subject.event_types:
        labels = list(subject.event_types)
    elif subject.event_channels is not None and subject.event_channels.size:
        labels = [int(value) for value in subject.event_channels.tolist()]
    entropy = normalized_entropy(labels)
    if np.isfinite(entropy):
        metrics["event_type_entropy"] = float(entropy)
    simult = simultaneity_fraction(subject.event_timestamps)
    if np.isfinite(simult):
        metrics["event_simultaneity"] = float(simult)
    cv = mark_cv(subject.event_values)
    if np.isfinite(cv):
        metrics["event_mark_cv"] = float(cv)
    if subject.event_timestamps is not None and subject.event_timestamps.size >= 2:
        span = float(np.max(subject.event_timestamps) - np.min(subject.event_timestamps))
        if span > 0:
            metrics["event_rate_per_span"] = float(subject.event_timestamps.size / span)
    return metrics


def profile_series(
    series: Any,
    *,
    timestamps: Any | None = None,
    domain: str | None = None,
) -> SeriesProfile:
    """Profile a single univariate series.

    This is the lightweight entry point for quick checks and demos.
    It is intentionally narrower than :func:`profile_dataset`, which is the package's main dataset-level API.

    Parameters
    ----------
    series:
        One univariate sequence.
    timestamps:
        Optional timestamps for explicit observation support.
    domain:
        Optional domain label used only for light interpretation.
    """
    summary = compute_series_metrics(
        np.asarray(series, dtype=float),
        timestamps=None if timestamps is None else np.asarray(timestamps, dtype=float),
    )
    axes = compute_axes(summary.metrics)
    subdimensions = compute_subdimensions(summary.metrics)
    details = axis_contributors(summary.metrics)
    subdimension_details = subdimension_contributors(summary.metrics)
    metadata = {
        "length": int(summary.clean_values.size),
        "length_median": int(summary.clean_values.size),
        "n_subjects": 1,
        "n_channels_median": 1,
        "n_series_units": 1,
        "has_timestamps": timestamps is not None,
        "domain": (domain or "generic").lower(),
        "observation_mode": "dense" if timestamps is None else "dense",
    }
    archetypes = infer_archetypes(axes, metadata, summary.metrics)
    task_hints = infer_task_hints(axes, metadata, summary.metrics)
    reliability, evidence = summarize_reliability(axes=axes, metrics=summary.metrics, metadata=metadata)
    notes: list[str] = []
    if timestamps is None:
        notes.append("Sampling irregularity is estimated only from missingness because explicit timestamps were not provided.")
    return SeriesProfile(
        metadata=metadata,
        axes=axes,
        subdimensions=subdimensions,
        axis_details=details,
        subdimension_details=subdimension_details,
        metrics=summary.metrics,
        archetypes=archetypes,
        task_hints=task_hints,
        reliability=reliability.to_dict(),
        evidence=evidence.to_dict(),
        notes=notes,
    )


def profile_dataset(
    data: Any,
    *,
    domain: str | None = None,
    timestamps: Any | list[Any] | tuple[Any, ...] | None = None,
    time_axis: int = 0,
    channel_axis: int | None = -1,
    subject_axis: int = 0,
    sampling_rate: float | None = None,
    tr: float | None = None,
    channel_names: list[str] | None = None,
    roi_names: list[str] | None = None,
    network_labels: list[str] | None = None,
    subject_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    bootstrap: int = 0,
    random_state: int | None = None,
) -> DatasetProfile:
    """Profile a time-series dataset as a dataset rather than as isolated features.

    The function accepts dense arrays, domain-specific wrappers, irregular inputs,
    event streams, tabular data, and several duck-typed ecosystem objects. It
    returns a :class:`DatasetProfile` containing ontology axis scores,
    subdimensions, proxy metrics, archetypes, task hints, and reliability-aware
    dataset-card renderers.

    This is the main public entry point of echotime.
    """
    context = _build_context(
        domain=domain,
        timestamps=timestamps,
        time_axis=time_axis,
        channel_axis=channel_axis,
        subject_axis=subject_axis,
        sampling_rate=sampling_rate,
        tr=tr,
        channel_names=channel_names,
        roi_names=roi_names,
        network_labels=network_labels,
        subject_ids=subject_ids,
        metadata=metadata,
    )

    registry = get_registry()
    adaptor = registry.resolve_adaptor(data, context)
    normalized = adaptor.adapt(data, context)

    per_unit_axes: list[dict[str, float]] = []
    per_subject_axes: list[dict[str, float]] = []
    per_unit_metrics: list[dict[str, float]] = []
    subject_coupling: list[dict[str, float]] = []
    subject_network_metrics: list[dict[str, float]] = []
    subject_observation_metrics: list[dict[str, float]] = []
    subject_event_metrics: list[dict[str, float]] = []

    for subject in normalized.subjects:
        channel_profiles: list[dict[str, float]] = []
        channel_metrics: list[dict[str, float]] = []
        for channel_idx in range(subject.values.shape[1]):
            summary = compute_series_metrics(
                subject.values[:, channel_idx],
                timestamps=subject.timestamps,
                missing_fraction=subject.missing_fraction,
            )
            unit_axes = compute_axes(summary.metrics)
            channel_profiles.append(unit_axes)
            channel_metrics.append(summary.metrics)
            per_unit_axes.append(unit_axes)
            per_unit_metrics.append(summary.metrics)

        subject_metric = _nanmean_dicts(channel_metrics)
        coupling = compute_multivariate_metrics(subject.values)
        coupling_metrics = {
            "mean_abs_correlation": coupling.mean_abs_correlation,
            "dynamic_correlation_instability": coupling.dynamic_correlation_instability,
        }
        subject_coupling.append(coupling_metrics)
        subject_metric.update(coupling_metrics)
        network_metric = _subject_network_metrics(subject, normalized.metadata.get("network_labels"))
        if network_metric:
            subject_network_metrics.append(network_metric)
            subject_metric.update(network_metric)
        observation_metric = _subject_observation_metrics(subject)
        if observation_metric:
            subject_observation_metrics.append(observation_metric)
            subject_metric.update(observation_metric)
        event_metric = _subject_event_metrics(subject)
        if event_metric:
            subject_event_metrics.append(event_metric)
            subject_metric.update(event_metric)
        subject_metric.update(_subject_domain_metrics(subject, normalized.metadata))

        per_subject_axes.append(compute_axes(subject_metric))

    dataset_metrics = _nanmean_dicts(per_unit_metrics)
    dataset_metrics.update(_nanmean_dicts(subject_coupling))
    dataset_metrics.update(_nanmean_dicts(subject_network_metrics))
    dataset_metrics.update(_nanmean_dicts(subject_observation_metrics))
    dataset_metrics.update(_nanmean_dicts(subject_event_metrics))
    dataset_metrics["heterogeneity_distance"] = _pairwise_distance(per_subject_axes if len(per_subject_axes) > 1 else per_unit_axes)
    dataset_metrics["n_subjects"] = float(normalized.metadata["n_subjects"])
    dataset_metrics["n_channels_median"] = float(normalized.metadata["n_channels_median"])
    dataset_metrics["n_channels_max"] = float(normalized.metadata["n_channels_max"])
    dataset_metrics["mean_missing_fraction"] = float(normalized.metadata["mean_missing_fraction"])
    dataset_metrics["n_events_total"] = float(normalized.metadata.get("n_events_total", 0.0))

    plugin_metrics: dict[str, dict[str, float]] = {}
    notes: list[str] = []
    for plugin in registry.active_plugins(normalized, context):
        result = plugin.compute(normalized, context)
        if result.metrics:
            plugin_metrics[plugin.name] = result.metrics
            dataset_metrics.update(result.metrics)
        if result.notes:
            notes.extend(result.notes)

    axes = compute_axes(dataset_metrics)
    subdimensions = compute_subdimensions(dataset_metrics)
    details = axis_contributors(dataset_metrics)
    subdimension_details = subdimension_contributors(dataset_metrics)
    metadata_out = dict(normalized.metadata)
    metadata_out["n_series_units"] = int(len(per_unit_axes))
    metadata_out["dominant_axes"] = ", ".join(sorted(axes, key=axes.get, reverse=True)[:3])

    archetypes = infer_archetypes(axes, metadata_out, dataset_metrics)
    task_hints = infer_task_hints(axes, metadata_out, dataset_metrics)

    if metadata_out["n_subjects"] == 1 and metadata_out["n_channels_median"] == 1:
        notes.append("Heterogeneity is near-trivial for a single univariate series.")
    if metadata_out["n_channels_median"] <= 1:
        notes.append("Coupling/networkedness is only informative for multivariate data.")
    if metadata_out["has_timestamps"] is False and metadata_out.get("sampling_rate") is None:
        notes.append("Sampling irregularity is estimated only from missingness because explicit timestamps were not provided.")
    if metadata_out.get("domain") == "fmri" and metadata_out.get("tr") is None and metadata_out.get("sampling_rate") is None:
        notes.append("Provide TR to unlock Hz-aware fMRI proxies.")
    if metadata_out.get("domain") == "eeg" and metadata_out.get("sampling_rate") is None:
        notes.append("Provide sampling_rate to unlock EEG bandpower proxies.")
    if metadata_out.get("observation_mode") in {"irregular", "mixed"}:
        if float(dataset_metrics.get("irregular_spectral_support", 0.0)) > 0.0:
            notes.append("For irregularly sampled inputs with explicit timestamps, frequency-aware proxies use Lomb-Scargle style irregular-spectrum estimates; very sparse or strongly gappy series should still be interpreted conservatively.")
        else:
            notes.append("For irregularly sampled inputs without enough timestamp support, spectral interpretations remain conservative.")
    if metadata_out.get("observation_mode") == "event_stream":
        notes.append("Event streams are represented as sparse channel-wise count/value panels for generic ontology scoring; consult event-specific plugin metrics for arrival statistics.")

    bootstrap_source = per_subject_axes if len(per_subject_axes) >= 2 else per_unit_axes
    bootstrap_summary = bootstrap_axis_intervals(bootstrap_source, n_resamples=bootstrap, random_state=random_state)
    reliability, evidence = summarize_reliability(
        axes=axes,
        metrics=dataset_metrics,
        metadata=metadata_out,
        bootstrap=bootstrap_summary,
    )

    deduped_notes: list[str] = []
    for note in notes + reliability.notes:
        if note not in deduped_notes:
            deduped_notes.append(note)

    return DatasetProfile(
        metadata=metadata_out,
        axes=axes,
        subdimensions=subdimensions,
        axis_details=details,
        subdimension_details=subdimension_details,
        metrics=dataset_metrics,
        archetypes=archetypes,
        task_hints=task_hints,
        reliability=reliability.to_dict(),
        evidence=evidence.to_dict(),
        per_subject_axes=per_subject_axes,
        per_unit_axes=per_unit_axes,
        notes=deduped_notes,
        plugin_metrics=plugin_metrics,
    )
