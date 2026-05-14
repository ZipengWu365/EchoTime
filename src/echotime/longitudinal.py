"""Longitudinal cohort metrics for clinical and wearable time-series datasets."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence

import numpy as np

from .adapters import NormalizedDataset, SubjectData
from .axes import compute_axes
from .context import ProfilingContext
from .metrics import compute_multivariate_metrics, compute_series_metrics, normalized_entropy
from .registry import PluginResult


EPS = 1e-12


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


def _pairwise_distance(vectors: list[np.ndarray]) -> float:
    if len(vectors) < 2:
        return float("nan")
    arr = np.vstack(vectors).astype(float)
    if np.any(~np.isfinite(arr)):
        col_means = np.nanmean(arr, axis=0)
        col_means = np.where(np.isfinite(col_means), col_means, 0.0)
        inds = np.where(~np.isfinite(arr))
        arr[inds] = np.take(col_means, inds[1])
    distances: list[float] = []
    for i in range(arr.shape[0]):
        for j in range(i + 1, arr.shape[0]):
            distances.append(float(np.linalg.norm(arr[i] - arr[j]) / np.sqrt(arr.shape[1])))
    return float(np.mean(distances)) if distances else float("nan")


def _visit_axis_profile(subject: SubjectData) -> np.ndarray:
    channel_metrics: list[dict[str, float]] = []
    for channel_idx in range(subject.values.shape[1]):
        summary = compute_series_metrics(subject.values[:, channel_idx], timestamps=subject.timestamps, missing_fraction=subject.missing_fraction)
        channel_metrics.append(summary.metrics)
    summary_metrics = _nanmean_dicts(channel_metrics)
    coupling = compute_multivariate_metrics(subject.values)
    summary_metrics.update(
        {
            "mean_abs_correlation": coupling.mean_abs_correlation,
            "dynamic_correlation_instability": coupling.dynamic_correlation_instability,
        }
    )
    axes = compute_axes(summary_metrics)
    return np.asarray([float(axes[axis]) for axis in axes], dtype=float)


class LongitudinalMetricsPlugin:
    """Metrics for repeated-visit cohorts typical of clinical and wearable studies."""

    name = "longitudinal_metrics"

    def applies(self, normalized: NormalizedDataset, context: ProfilingContext) -> bool:
        if bool(normalized.metadata.get("longitudinal_mode", False)):
            return True
        parent_ids = normalized.metadata.get("longitudinal_parent_subject_ids")
        return bool(parent_ids and len(parent_ids) == len(normalized.subjects))

    def compute(self, normalized: NormalizedDataset, context: ProfilingContext) -> PluginResult:
        parent_ids = list(normalized.metadata.get("longitudinal_parent_subject_ids") or [])
        visit_ids = list(normalized.metadata.get("longitudinal_visit_ids") or [])
        visit_anchors = list(normalized.metadata.get("longitudinal_visit_anchors") or [])
        visit_devices = list(normalized.metadata.get("longitudinal_visit_devices") or [])
        visit_phases = list(normalized.metadata.get("longitudinal_visit_phases") or [])

        if len(parent_ids) != len(normalized.subjects):
            parent_ids = [f"subject_{idx}" for idx in range(len(normalized.subjects))]
        if len(visit_ids) != len(normalized.subjects):
            visit_ids = [f"visit_{idx}" for idx in range(len(normalized.subjects))]
        if len(visit_anchors) != len(normalized.subjects):
            visit_anchors = [float(idx) for idx in range(len(normalized.subjects))]

        groups: dict[str, list[int]] = defaultdict(list)
        for idx, parent in enumerate(parent_ids):
            groups[str(parent)].append(idx)

        counts = np.asarray([len(indices) for indices in groups.values()], dtype=float)
        visit_profiles = [_visit_axis_profile(subject) for subject in normalized.subjects]

        per_parent_mean: list[np.ndarray] = []
        within_distances: list[float] = []
        visit_gap_cvs: list[float] = []
        adherence_scores: list[float] = []

        for parent, indices in groups.items():
            sorted_indices = sorted(indices, key=lambda i: float(visit_anchors[i]) if np.isfinite(float(visit_anchors[i])) else float(i))
            parent_vectors = [visit_profiles[idx] for idx in sorted_indices]
            parent_mean = np.nanmean(np.vstack(parent_vectors), axis=0)
            per_parent_mean.append(parent_mean)

            if len(parent_vectors) >= 2:
                distance = _pairwise_distance(parent_vectors)
                if np.isfinite(distance):
                    within_distances.append(float(distance))
                anchors = np.asarray([float(visit_anchors[idx]) for idx in sorted_indices], dtype=float)
                anchors = anchors[np.isfinite(anchors)]
                if anchors.size >= 2:
                    gaps = np.diff(np.sort(anchors))
                    gaps = gaps[gaps > 0]
                    if gaps.size >= 2 and float(np.mean(gaps)) > 0:
                        visit_gap_cvs.append(float(np.std(gaps) / (np.mean(gaps) + EPS)))

            # observation-density / adherence proxy across repeated observations
            spans: list[float] = []
            observed_points: list[int] = []
            for idx in sorted_indices:
                subject = normalized.subjects[idx]
                ts = subject.timestamps
                if ts is None or ts.size < 2:
                    continue
                finite_ts = np.asarray(ts, dtype=float)
                finite_ts = finite_ts[np.isfinite(finite_ts)]
                if finite_ts.size < 2:
                    continue
                span = float(np.max(finite_ts) - np.min(finite_ts))
                if span > 0:
                    spans.append(span)
                    observed_points.append(int(np.sum(np.any(np.isfinite(subject.values), axis=1))))
            if spans and observed_points:
                density = float(np.mean(observed_points) / (np.mean(spans) + 1.0))
                adherence_scores.append(float(np.clip(density / (density + 1.0), 0.0, 1.0)))

        between_distance = _pairwise_distance(per_parent_mean)
        within_distance = float(np.mean(within_distances)) if within_distances else float("nan")
        if np.isfinite(within_distance) and np.isfinite(between_distance):
            fingerprintability = float(np.clip((between_distance - within_distance) / (between_distance + EPS), 0.0, 1.0))
        else:
            fingerprintability = float("nan")

        metrics: dict[str, float] = {
            "visit_count_cv": float(np.std(counts) / (np.mean(counts) + EPS)) if counts.size >= 2 and float(np.mean(counts)) > 0 else 0.0,
            "dropout_imbalance": float(np.clip(1.0 - (float(np.mean(counts)) / (float(np.max(counts)) + EPS)), 0.0, 1.0)) if counts.size else 0.0,
            "mean_visits_per_subject": float(np.mean(counts)) if counts.size else 1.0,
        }
        if visit_gap_cvs:
            metrics["visit_gap_cv"] = float(np.mean(visit_gap_cvs))
        if np.isfinite(within_distance):
            metrics["longitudinal_instability"] = float(within_distance)
        if np.isfinite(fingerprintability):
            metrics["subject_fingerprintability"] = float(fingerprintability)
        if adherence_scores:
            metrics["wearable_adherence_proxy"] = float(np.mean(adherence_scores))
        device_entropy = normalized_entropy([label for label in visit_devices if label])
        if np.isfinite(device_entropy):
            metrics["device_entropy"] = float(device_entropy)
        phase_entropy = normalized_entropy([label for label in visit_phases if label])
        if np.isfinite(phase_entropy):
            metrics["phase_entropy"] = float(phase_entropy)

        notes = [
            "Longitudinal metrics summarize repeated-visit stability, follow-up irregularity, and subject-level repeatability.",
        ]
        if len(groups) < 2:
            notes.append("Only one parent subject was available, so between-subject longitudinal comparisons are limited.")
        elif not within_distances:
            notes.append("Repeated visits per subject were scarce, so within-subject longitudinal stability is only weakly supported.")
        return PluginResult(metrics=metrics, notes=notes)
