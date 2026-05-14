"""Stable ontology schema definitions for echotime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_VERSION = "0.8.0"


@dataclass(frozen=True, slots=True)
class ProxySpec:
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class SubdimensionSpec:
    name: str
    description: str
    proxies: tuple[ProxySpec, ...]


@dataclass(frozen=True, slots=True)
class AxisSpec:
    name: str
    description: str
    subdimensions: tuple[SubdimensionSpec, ...]


def _proxy(name: str, description: str) -> ProxySpec:
    return ProxySpec(name=name, description=description)


AXIS_SPECS: tuple[AxisSpec, ...] = (
    AxisSpec(
        name="sampling_irregularity",
        description="Irregular timestamps, missingness, asynchrony, and observation-grid instability.",
        subdimensions=(
            SubdimensionSpec(
                name="observation_grid_instability",
                description="How unstable the temporal observation grid appears.",
                proxies=(
                    _proxy("delta_t_cv", "Coefficient of variation of inter-sample time gaps."),
                    _proxy("gap_fraction", "Fraction of unusually large inter-sample gaps."),
                ),
            ),
            SubdimensionSpec(
                name="data_completeness",
                description="How much explicit missingness or broken observation support is present.",
                proxies=(
                    _proxy("missing_fraction", "Fraction of non-finite observations."),
                ),
            ),
            SubdimensionSpec(
                name="cross_channel_asynchrony",
                description="Whether channels are observed on misaligned time grids.",
                proxies=(
                    _proxy("channel_asynchrony", "Row-wise asynchrony of multichannel observation support."),
                ),
            ),
            SubdimensionSpec(
                name="longitudinal_follow_up_instability",
                description="Irregularity of repeated follow-up structure across visits or sessions.",
                proxies=(
                    _proxy("visit_gap_cv", "Coefficient of variation of within-subject gaps between repeated visits."),
                    _proxy("dropout_imbalance", "Imbalance in visit counts across subjects as a proxy for attrition or adherence breakdown."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="noise_contamination",
        description="High-frequency contamination, residual roughness, and noise-like spectra.",
        subdimensions=(
            SubdimensionSpec(
                name="residual_roughness",
                description="Variance left after smooth trend removal.",
                proxies=(
                    _proxy("noise_residual_ratio", "Residual variance ratio after Savitzky-Golay smoothing."),
                ),
            ),
            SubdimensionSpec(
                name="spectral_noisiness",
                description="How much power mass lives in high frequencies or flat spectra.",
                proxies=(
                    _proxy("high_freq_power_ratio", "Fraction of spectral mass in the top quartile of frequencies."),
                    _proxy("spectral_flatness", "Geometric-to-arithmetic mean spectral power ratio."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="predictability",
        description="Extent to which the near future is recoverable from the recent past.",
        subdimensions=(
            SubdimensionSpec(
                name="short_horizon_dependence",
                description="Lagged dependence available to simple autoregressive models.",
                proxies=(
                    _proxy("ar1_r2", "AR(1) explained-variance proxy."),
                    _proxy("max_abs_acf", "Maximum short-lag autocorrelation magnitude."),
                ),
            ),
            SubdimensionSpec(
                name="spectral_forecastability",
                description="How concentrated the spectrum is relative to white-noise-like spectra.",
                proxies=(
                    _proxy("forecastability", "One minus normalized spectral entropy."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="drift_nonstationarity",
        description="Temporal instability of distributional or spectral structure.",
        subdimensions=(
            SubdimensionSpec(
                name="moment_drift",
                description="How much mean and variance shift across rolling windows.",
                proxies=(
                    _proxy("mean_drift_ratio", "Normalized rolling-mean drift."),
                    _proxy("variance_drift_ratio", "Normalized rolling-variance drift."),
                ),
            ),
            SubdimensionSpec(
                name="spectral_drift",
                description="How much the spectral distribution changes across time.",
                proxies=(
                    _proxy("spectral_drift_js", "Jensen-Shannon divergence between first-half and second-half spectra."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="trendness",
        description="Strength of slow, directional, low-frequency movement.",
        subdimensions=(
            SubdimensionSpec(
                name="directional_trend",
                description="Global directional movement and linear fit quality.",
                proxies=(
                    _proxy("trend_r2", "R² of a linear trend fit."),
                    _proxy("slope_strength", "Total linear change normalized by signal scale."),
                ),
            ),
            SubdimensionSpec(
                name="low_frequency_bias",
                description="Concentration of spectral power at low frequencies.",
                proxies=(
                    _proxy("low_freq_power_ratio", "Power ratio below the first spectral quartile."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="rhythmicity",
        description="Strength of periodic, oscillatory, or quasi-periodic repetition.",
        subdimensions=(
            SubdimensionSpec(
                name="spectral_peakedness",
                description="Concentration of power around dominant oscillatory peaks.",
                proxies=(
                    _proxy("spectral_peak_ratio", "Largest normalized spectral peak."),
                    _proxy("alpha_peak_prominence", "Alpha-band peak prominence for EEG-like data."),
                ),
            ),
            SubdimensionSpec(
                name="periodic_recurrence",
                description="Recurrence of similar states at non-zero lags.",
                proxies=(
                    _proxy("acf_periodic_peak", "Largest positive periodic autocorrelation peak."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="complexity",
        description="Pattern richness, local unpredictability, and resistance to simple compression.",
        subdimensions=(
            SubdimensionSpec(
                name="ordinal_pattern_complexity",
                description="Diversity of local ordinal motifs.",
                proxies=(
                    _proxy("permutation_entropy", "Normalized permutation entropy."),
                ),
            ),
            SubdimensionSpec(
                name="irregularity",
                description="Pattern-level unpredictability beyond repeating templates.",
                proxies=(
                    _proxy("sample_entropy", "Sample entropy."),
                ),
            ),
            SubdimensionSpec(
                name="compressibility_and_scale",
                description="Resistance to symbolic compression and deviation from memoryless scaling.",
                proxies=(
                    _proxy("lz_complexity", "Binarized Lempel-Ziv complexity proxy."),
                    _proxy("hurst_complexity_proxy", "Distance of the Hurst exponent from 0.5."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="nonlinearity_chaoticity",
        description="Departure from linear-Gaussian dependence and time-symmetry.",
        subdimensions=(
            SubdimensionSpec(
                name="nonlinear_dependence",
                description="Dependence not explained by Gaussian lag-one correlation alone.",
                proxies=(
                    _proxy("nonlinearity_gap", "Mutual-information gap over a Gaussian AR baseline."),
                ),
            ),
            SubdimensionSpec(
                name="temporal_asymmetry",
                description="Evidence that forward and backward dynamics are not equivalent.",
                proxies=(
                    _proxy("time_reversal_asymmetry", "Time-reversal asymmetry statistic."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="eventness_burstiness",
        description="Dominance of sparse, bursty, or sharp episodic excursions.",
        subdimensions=(
            SubdimensionSpec(
                name="event_incidence",
                description="How often robust events occur.",
                proxies=(
                    _proxy("event_rate", "Fraction of robust outlier-like events."),
                ),
            ),
            SubdimensionSpec(
                name="burst_temporal_patterning",
                description="Whether events cluster in time rather than arrive regularly.",
                proxies=(
                    _proxy("burstiness", "Burstiness of inter-event intervals."),
                    _proxy("event_interval_burstiness", "Burstiness of event-stream inter-arrival intervals."),
                ),
            ),
            SubdimensionSpec(
                name="energy_concentration",
                description="How concentrated signal energy is within rare excursions.",
                proxies=(
                    _proxy("event_energy_concentration", "Fraction of total energy carried by the top 5% energy samples."),
                ),
            ),
            SubdimensionSpec(
                name="event_type_diversity",
                description="Diversity of event labels or event-channel assignments.",
                proxies=(
                    _proxy("event_type_entropy", "Normalized entropy of event types or event channels."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="regime_switching",
        description="Evidence for discrete structural shifts or switching dynamics.",
        subdimensions=(
            SubdimensionSpec(
                name="abrupt_shift_density",
                description="Density of abrupt rolling-window change points.",
                proxies=(
                    _proxy("change_point_density", "Rolling-window mean/variance change-point density."),
                ),
            ),
            SubdimensionSpec(
                name="global_instability",
                description="Broader spectral or moment drift consistent with changing regimes.",
                proxies=(
                    _proxy("spectral_drift_js", "Jensen-Shannon divergence between first-half and second-half spectra."),
                    _proxy("mean_drift_ratio", "Normalized rolling-mean drift."),
                ),
            ),
            SubdimensionSpec(
                name="network_reconfiguration",
                description="Time-varying multivariate reconfiguration consistent with state switches.",
                proxies=(
                    _proxy("network_state_transition_rate", "Rate of large window-to-window network changes."),
                    _proxy("network_modularity_volatility", "Volatility of within-vs-between network separation across windows."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="coupling_networkedness",
        description="Strength and organization of cross-channel dependence.",
        subdimensions=(
            SubdimensionSpec(
                name="pairwise_dependence",
                description="Average strength of pairwise dependence across channels.",
                proxies=(
                    _proxy("mean_abs_correlation", "Mean absolute cross-channel correlation."),
                ),
            ),
            SubdimensionSpec(
                name="dynamic_coupling",
                description="How much channel dependence changes over time.",
                proxies=(
                    _proxy("dynamic_correlation_instability", "Standard deviation of windowed mean cross-channel correlation."),
                ),
            ),
            SubdimensionSpec(
                name="graph_organization",
                description="Whether coupling forms structured network topology.",
                proxies=(
                    _proxy("graph_density_proxy", "Density of a thresholded absolute-correlation graph."),
                    _proxy("graph_clustering_proxy", "Triangle-based clustering proxy of a thresholded graph."),
                    _proxy("network_modularity_gap", "Within-network minus between-network coupling gap."),
                ),
            ),
        ),
    ),
    AxisSpec(
        name="heterogeneity",
        description="Variation in structure across subjects, conditions, or channels.",
        subdimensions=(
            SubdimensionSpec(
                name="structural_dispersion",
                description="Distance between subject-level or unit-level structure profiles.",
                proxies=(
                    _proxy("heterogeneity_distance", "Mean pairwise distance between structure vectors."),
                ),
            ),
            SubdimensionSpec(
                name="cross_subject_alignment",
                description="How aligned or synchronized different subjects appear.",
                proxies=(
                    _proxy("inter_subject_similarity", "Mean similarity across flattened subject representations."),
                    _proxy("inter_subject_synchrony", "Mean synchrony across subject-mean signals."),
                ),
            ),
            SubdimensionSpec(
                name="longitudinal_repeatability",
                description="How stable repeated visits are within subject and how distinct subjects remain across visits.",
                proxies=(
                    _proxy("longitudinal_instability", "Mean within-subject distance across repeated-visit structure profiles."),
                    _proxy("subject_fingerprintability", "Extent to which between-subject variation exceeds within-subject longitudinal drift."),
                ),
            ),
        ),
    ),
)

AXIS_SCHEMA_MAP: dict[str, AxisSpec] = {axis.name: axis for axis in AXIS_SPECS}
AXIS_ORDER: tuple[str, ...] = tuple(axis.name for axis in AXIS_SPECS)
AXIS_DESCRIPTIONS: dict[str, str] = {axis.name: axis.description for axis in AXIS_SPECS}


def schema_dict() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "axes": [asdict(axis) for axis in AXIS_SPECS],
    }


def get_axis_spec(axis_name: str) -> AxisSpec:
    return AXIS_SCHEMA_MAP[axis_name]


def get_schema() -> tuple[AxisSpec, ...]:
    return AXIS_SPECS
