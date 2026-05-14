"""Ontology axis specifications, transforms, and scoring."""

from __future__ import annotations

from typing import Callable

import numpy as np

from .schema import AXIS_DESCRIPTIONS, AXIS_ORDER, AXIS_SPECS as ONTOLOGY_AXIS_SPECS

AxisTransform = Callable[[float], float]


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _ratio01(value: float, scale: float = 1.0) -> float:
    value = max(0.0, float(value))
    return float(value / (value + scale))


def _abs_tanh(value: float, scale: float = 1.0) -> float:
    return float(np.tanh(abs(float(value)) / max(scale, 1e-12)))


def _inverse01(value: float) -> float:
    return float(np.clip(1.0 - value, 0.0, 1.0))


def _signed_gap(value: float) -> float:
    return float(np.clip((value + 1.0) / 2.0, 0.0, 1.0))


PROXY_TRANSFORMS: dict[str, AxisTransform] = {
    "delta_t_cv": _clip01,
    "gap_fraction": _clip01,
    "missing_fraction": _clip01,
    "channel_asynchrony": _clip01,
    "visit_gap_cv": lambda x: _ratio01(x, 0.5),
    "dropout_imbalance": _clip01,
    "noise_residual_ratio": _clip01,
    "high_freq_power_ratio": _clip01,
    "spectral_flatness": _clip01,
    "forecastability": _clip01,
    "ar1_r2": _clip01,
    "max_abs_acf": _clip01,
    "mean_drift_ratio": lambda x: _ratio01(x, 0.75),
    "variance_drift_ratio": lambda x: _ratio01(x, 0.75),
    "spectral_drift_js": _clip01,
    "trend_r2": _clip01,
    "slope_strength": lambda x: _ratio01(x, 0.5),
    "low_freq_power_ratio": _clip01,
    "spectral_peak_ratio": _clip01,
    "acf_periodic_peak": _clip01,
    "alpha_peak_prominence": _clip01,
    "permutation_entropy": _clip01,
    "sample_entropy": lambda x: _ratio01(x, 1.0),
    "lz_complexity": lambda x: _clip01(x / 1.5),
    "hurst_complexity_proxy": _clip01,
    "nonlinearity_gap": _clip01,
    "time_reversal_asymmetry": lambda x: _abs_tanh(x, 0.5),
    "burstiness": _clip01,
    "event_interval_burstiness": _clip01,
    "event_energy_concentration": _clip01,
    "event_type_entropy": _clip01,
    "event_rate": lambda x: _clip01(3.0 * x),
    "change_point_density": _clip01,
    "network_state_transition_rate": _clip01,
    "network_modularity_volatility": lambda x: _ratio01(x, 0.15),
    "mean_abs_correlation": _clip01,
    "dynamic_correlation_instability": lambda x: _ratio01(x, 0.2),
    "graph_density_proxy": _clip01,
    "graph_clustering_proxy": _clip01,
    "network_modularity_gap": _signed_gap,
    "heterogeneity_distance": _clip01,
    "inter_subject_similarity": _inverse01,
    "inter_subject_synchrony": _inverse01,
    "longitudinal_instability": lambda x: _ratio01(x, 0.35),
    "subject_fingerprintability": _clip01,
}


AXIS_SPECS: dict[str, tuple[tuple[str, AxisTransform], ...]] = {
    axis.name: tuple(
        (proxy.name, PROXY_TRANSFORMS[proxy.name])
        for subdim in axis.subdimensions
        for proxy in subdim.proxies
    )
    for axis in ONTOLOGY_AXIS_SPECS
}


def transform_proxy(proxy_name: str, value: float) -> float:
    transform = PROXY_TRANSFORMS[proxy_name]
    return float(transform(float(value)))


def compute_subdimensions(metrics: dict[str, float]) -> dict[str, dict[str, float]]:
    """Convert raw proxy metrics into per-axis subdimension scores."""
    results: dict[str, dict[str, float]] = {}
    for axis in ONTOLOGY_AXIS_SPECS:
        axis_out: dict[str, float] = {}
        for subdim in axis.subdimensions:
            transformed: list[float] = []
            for proxy in subdim.proxies:
                value = metrics.get(proxy.name, np.nan)
                if np.isfinite(value):
                    transformed.append(transform_proxy(proxy.name, float(value)))
            axis_out[subdim.name] = float(np.mean(transformed)) if transformed else 0.0
        results[axis.name] = axis_out
    return results


def compute_axes(metrics: dict[str, float]) -> dict[str, float]:
    """Convert raw proxy metrics into the ontology axes."""
    subdimensions = compute_subdimensions(metrics)
    axes: dict[str, float] = {}
    for axis in ONTOLOGY_AXIS_SPECS:
        observed = []
        for subdim in axis.subdimensions:
            has_any = any(np.isfinite(metrics.get(proxy.name, np.nan)) for proxy in subdim.proxies)
            if has_any:
                observed.append(float(subdimensions[axis.name][subdim.name]))
        axes[axis.name] = float(np.mean(observed)) if observed else 0.0
    return axes


def axis_contributors(metrics: dict[str, float]) -> dict[str, dict[str, float]]:
    """Return transformed proxy contributions for each axis."""
    details: dict[str, dict[str, float]] = {}
    for axis_name in AXIS_ORDER:
        contributions: dict[str, float] = {}
        for key, _transform in AXIS_SPECS[axis_name]:
            value = metrics.get(key, np.nan)
            if np.isfinite(value):
                contributions[key] = transform_proxy(key, float(value))
        details[axis_name] = contributions
    return details


def subdimension_contributors(metrics: dict[str, float]) -> dict[str, dict[str, dict[str, float]]]:
    """Return transformed proxy contributions grouped by subdimension."""
    nested: dict[str, dict[str, dict[str, float]]] = {}
    for axis in ONTOLOGY_AXIS_SPECS:
        axis_out: dict[str, dict[str, float]] = {}
        for subdim in axis.subdimensions:
            contrib: dict[str, float] = {}
            for proxy in subdim.proxies:
                value = metrics.get(proxy.name, np.nan)
                if np.isfinite(value):
                    contrib[proxy.name] = transform_proxy(proxy.name, float(value))
            axis_out[subdim.name] = contrib
        nested[axis.name] = axis_out
    return nested


def observed_proxy_fraction(metrics: dict[str, float], axis_name: str) -> float:
    total = 0
    observed = 0
    axis = next(axis for axis in ONTOLOGY_AXIS_SPECS if axis.name == axis_name)
    for subdim in axis.subdimensions:
        for proxy in subdim.proxies:
            total += 1
            if np.isfinite(metrics.get(proxy.name, np.nan)):
                observed += 1
    return float(observed / total) if total else 0.0
