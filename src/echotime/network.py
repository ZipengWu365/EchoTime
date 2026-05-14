"""Network-oriented summaries for multivariate and cohort time-series data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .adapters import SubjectData
from .metrics import EPS, _safe_corr, _window_length


@dataclass(slots=True)
class NetworkSummary:
    graph_density_proxy: float
    graph_clustering_proxy: float
    network_state_transition_rate: float
    network_modularity_gap: float
    network_modularity_volatility: float


def _fill_nan_columns(matrix: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=float).copy()
    if arr.ndim != 2:
        return arr
    for col in range(arr.shape[1]):
        mask = np.isfinite(arr[:, col])
        if not np.any(mask):
            arr[:, col] = 0.0
        else:
            mean = float(np.mean(arr[mask, col]))
            arr[~mask, col] = mean
    return arr


def _corr_matrix(matrix: np.ndarray) -> np.ndarray:
    arr = _fill_nan_columns(matrix)
    if arr.ndim != 2 or arr.shape[1] < 2 or arr.shape[0] < 2:
        return np.zeros((0, 0), dtype=float)
    corr = np.corrcoef(arr, rowvar=False)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    corr = np.abs(corr)
    np.fill_diagonal(corr, 0.0)
    return np.clip(corr, 0.0, 1.0)


def _windowed_corr_matrices(matrix: np.ndarray) -> list[np.ndarray]:
    arr = np.asarray(matrix, dtype=float)
    if arr.ndim != 2 or arr.shape[0] < 12 or arr.shape[1] < 2:
        return []
    window = _window_length(arr.shape[0], fraction=0.2, minimum=12, maximum=120)
    if arr.shape[0] < window + 2:
        return []
    stride = max(1, window // 2)
    matrices: list[np.ndarray] = []
    for start in range(0, arr.shape[0] - window + 1, stride):
        matrices.append(_corr_matrix(arr[start : start + window]))
    return matrices


def _upper_triangle_values(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] < 2:
        return np.asarray([], dtype=float)
    idx = np.triu_indices(matrix.shape[0], k=1)
    return matrix[idx]


def _graph_density(corr: np.ndarray, threshold: float = 0.30) -> float:
    upper = _upper_triangle_values(corr)
    if upper.size == 0:
        return float("nan")
    return float(np.mean(upper >= threshold))


def _graph_clustering(corr: np.ndarray, threshold: float = 0.30) -> float:
    if corr.size == 0:
        return float("nan")
    adjacency = (corr >= threshold).astype(float)
    np.fill_diagonal(adjacency, 0.0)
    degree = np.sum(adjacency, axis=0)
    if np.max(degree, initial=0.0) < 2:
        return 0.0
    cube = adjacency @ adjacency @ adjacency
    locals_: list[float] = []
    for idx, deg in enumerate(degree):
        if deg >= 2:
            locals_.append(float(cube[idx, idx] / (deg * (deg - 1))))
    return float(np.mean(locals_)) if locals_ else 0.0


def _consecutive_matrix_distances(matrices: Sequence[np.ndarray]) -> np.ndarray:
    if len(matrices) < 2:
        return np.asarray([], dtype=float)
    distances = []
    for prev, curr in zip(matrices[:-1], matrices[1:]):
        if prev.shape != curr.shape or prev.size == 0:
            continue
        diff = curr - prev
        distances.append(float(np.linalg.norm(diff) / np.sqrt(diff.size)))
    return np.asarray(distances, dtype=float)


def _network_modularity_gap(corr: np.ndarray, labels: Sequence[str] | None) -> float:
    if labels is None:
        return float("nan")
    labels = list(labels)
    if corr.shape[0] != len(labels):
        return float("nan")
    unique = sorted(set(labels))
    if len(unique) < 2:
        return float("nan")
    within: list[float] = []
    between: list[float] = []
    for i in range(corr.shape[0]):
        for j in range(i + 1, corr.shape[1]):
            value = float(corr[i, j])
            if labels[i] == labels[j]:
                within.append(value)
            else:
                between.append(value)
    if not within or not between:
        return float("nan")
    return float(np.mean(within) - np.mean(between))


def compute_network_summary(matrix: np.ndarray, network_labels: Sequence[str] | None = None) -> NetworkSummary:
    corr = _corr_matrix(matrix)
    windows = _windowed_corr_matrices(matrix)
    distances = _consecutive_matrix_distances(windows)

    modularity_gap = _network_modularity_gap(corr, network_labels)
    volatility = float("nan")
    if network_labels is not None and windows:
        gaps = [_network_modularity_gap(win, network_labels) for win in windows]
        finite = [value for value in gaps if np.isfinite(value)]
        if len(finite) >= 2:
            volatility = float(np.std(finite))

    transition_rate = float("nan")
    if distances.size:
        threshold = float(np.median(distances) + np.std(distances))
        transition_rate = float(np.mean(distances > threshold))

    return NetworkSummary(
        graph_density_proxy=float(_graph_density(corr)),
        graph_clustering_proxy=float(_graph_clustering(corr)),
        network_state_transition_rate=transition_rate,
        network_modularity_gap=modularity_gap,
        network_modularity_volatility=volatility,
    )


def compute_inter_subject_similarity(subjects: Sequence[SubjectData]) -> float:
    if len(subjects) < 2:
        return float("nan")
    min_length = min(subject.values.shape[0] for subject in subjects)
    min_channels = min(subject.values.shape[1] for subject in subjects)
    if min_length < 8 or min_channels < 1:
        return float("nan")

    flattened: list[np.ndarray] = []
    for subject in subjects:
        segment = subject.values[:min_length, :min_channels]
        segment = _fill_nan_columns(segment)
        flattened.append(segment.reshape(-1))

    sims: list[float] = []
    for i in range(len(flattened)):
        for j in range(i + 1, len(flattened)):
            corr = _safe_corr(flattened[i], flattened[j])
            if np.isfinite(corr):
                sims.append(abs(float(corr)))
    return float(np.mean(sims)) if sims else float("nan")


def compute_inter_subject_synchrony(subjects: Sequence[SubjectData]) -> float:
    if len(subjects) < 2:
        return float("nan")
    min_length = min(subject.values.shape[0] for subject in subjects)
    if min_length < 8:
        return float("nan")

    signals = []
    for subject in subjects:
        mean_signal = np.nanmean(subject.values[:min_length], axis=1)
        signals.append(np.asarray(mean_signal, dtype=float))
    sims: list[float] = []
    for i in range(len(signals)):
        for j in range(i + 1, len(signals)):
            corr = _safe_corr(signals[i], signals[j])
            if np.isfinite(corr):
                sims.append(abs(float(corr)))
    return float(np.mean(sims)) if sims else float("nan")
