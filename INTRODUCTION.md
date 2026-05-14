# What is EchoTime?

**Structure-aware dataset profiling for time-series data.**

EchoTime converts a time-series dataset into a structural profile: ontology axis scores, subdimensions, proxy metrics, reliability summaries, archetypes, task hints, and dataset cards.

## What the package is

A dataset-characterization layer that sits between raw time-series data and downstream modelling. It helps researchers understand what kind of temporal structure they have before they pick models, compare benchmarks, or write dataset documentation.

## What the package is not

It is not a forecasting library, not a classifier, not a replacement for MNE/nilearn/pandas/xarray, and not just another bag-of-features extractor. It profiles datasets rather than training task models.

## Who should use it

Researchers and engineers working with fMRI, EEG, clinical monitoring, wearable longitudinal cohorts, environmental sensors, industrial telemetry, tabular time-series lakes, and event streams.

## Core outputs

- ontology axes
- subdimension scores
- raw proxy metrics
- archetype labels
- task hints
- reliability and evidence
- dataset card JSON/Markdown
- plain-language summary card
- narrative report
- case gallery
- similarity report
- rolling similarity diagnostics
- hot case gallery
- project homepage HTML
- agent-driven execution plan
- compact agent context bundle

## Supported input families

- dense NumPy-like arrays
- pandas DataFrame and tabular file paths
- FMRIInput and EEGInput typed wrappers
- irregular timestamped subjects
- event streams
- MNE-like and xarray-like objects

## The main question it answers

What kind of time-series dataset do I have, and what does that imply for analysis and modelling?

## Ontology axes

| axis | description |
|---|---|
| sampling_irregularity | Irregular timestamps, missingness, asynchrony, and observation-grid instability. |
| noise_contamination | High-frequency contamination, residual roughness, and noise-like spectra. |
| predictability | Extent to which the near future is recoverable from the recent past. |
| drift_nonstationarity | Temporal instability of distributional or spectral structure. |
| trendness | Strength of slow, directional, low-frequency movement. |
| rhythmicity | Strength of periodic, oscillatory, or quasi-periodic repetition. |
| complexity | Pattern richness, local unpredictability, and resistance to simple compression. |
| nonlinearity_chaoticity | Departure from linear-Gaussian dependence and time-symmetry. |
| eventness_burstiness | Dominance of sparse, bursty, or sharp episodic excursions. |
| regime_switching | Evidence for discrete structural shifts or switching dynamics. |
| coupling_networkedness | Strength and organization of cross-channel dependence. |
| heterogeneity | Variation in structure across subjects, conditions, or channels. |
