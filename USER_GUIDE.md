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

# EchoTime API reference

## core profiling

### `profile_dataset`

**Signature:** `profile_dataset(data, *, domain=None, timestamps=None, time_axis=0, channel_axis=-1, subject_axis=0, sampling_rate=None, tr=None, channel_names=None, roi_names=None, network_labels=None, subject_ids=None, metadata=None, bootstrap=0, random_state=None) -> DatasetProfile`

**Purpose:** Primary entry point. Profile an entire dataset as a dataset.

**Why this API exists:** The core design choice of EchoTime is that the object of interest is the dataset, not just a single series. This function aggregates unit-level signals, multivariate structure, cohort variation, and observation characteristics into one profile.

**When to use it:** Use when you want the ontology axes, archetypes, task hints, reliability, and dataset-card outputs for a whole dataset or cohort.

**Returns:** DatasetProfile

**Accepted inputs / context:**

- 1D/2D/3D arrays
- pandas DataFrame or tabular file path
- FMRIInput / EEGInput
- IrregularTimeSeriesInput
- EventStreamInput
- MNE-like or xarray-like object

**Inspect these outputs:**

- profile.axes
- profile.subdimensions
- profile.archetypes
- profile.task_hints
- profile.reliability
- profile.to_card_json()

**Recommended environments:** notebook, python_script, cli_batch, pandas_pipeline, neuro_stack, ml_benchmark

### `profile_series`

**Signature:** `profile_series(series, *, timestamps=None, domain=None) -> SeriesProfile`

**Purpose:** Profile a single univariate series when a full dataset object is not needed.

**Why this API exists:** Users often want a lightweight sanity-check before moving to dataset-level profiling. This function keeps the interface simple for one series while still using the same ontology machinery.

**When to use it:** Use for quick checks, demos, or when your data truly consist of a single univariate stream.

**Returns:** SeriesProfile

**Accepted inputs / context:**

- 1D array-like series
- optional timestamps

**Inspect these outputs:**

- profile.axes
- profile.metrics
- profile.notes
- profile.to_markdown()

**Recommended environments:** notebook, python_script

## profile outputs

### `DatasetProfile`

**Signature:** `DatasetProfile(...)`

**Purpose:** Rich result object returned by profile_dataset.

**Why this API exists:** A structural profile has both machine-readable and human-readable uses. The result object keeps raw metrics, ontology scores, notes, evidence, and rendering helpers together.

**When to use it:** Use after profiling to export reports, cards, or JSON payloads for downstream pipelines.

**Returns:** Dataclass-like object with rendering methods

**Accepted inputs / context:**

- created by profile_dataset

**Inspect these outputs:**

- to_dict()
- to_json()
- to_markdown()
- to_card_json()
- to_card_markdown()
- to_summary_card_markdown()
- to_narrative_report()

**Recommended environments:** notebook, python_script, cli_batch, ml_benchmark

### `SeriesProfile`

**Signature:** `SeriesProfile(...)`

**Purpose:** Result object returned by profile_series.

**Why this API exists:** Mirrors DatasetProfile for single-series inspection while keeping the same rendering ergonomics.

**When to use it:** Use when a quick series-level inspection is enough.

**Returns:** Dataclass-like object with rendering methods

**Accepted inputs / context:**

- created by profile_series

**Inspect these outputs:**

- to_dict()
- to_json()
- to_markdown()
- to_card_json()
- to_summary_card_markdown()
- to_narrative_report()

**Recommended environments:** notebook, python_script

## typed semantic inputs

### `FMRIInput`

**Signature:** `FMRIInput(values, tr=None, timestamps=None, roi_names=None, network_labels=None, subject_ids=None, ...) `

**Purpose:** Typed wrapper for fMRI time-series collections.

**Why this API exists:** Neuroimaging arrays often lose semantic context such as TR, ROI names, and network labels. The wrapper preserves those pieces so fMRI-specific proxies and network summaries can run correctly.

**When to use it:** Use when you have subject × time × ROI data or ROI time-series and want neuro-aware profiling.

**Returns:** Typed input object for profile_dataset

**Accepted inputs / context:**

- NumPy-like fMRI arrays
- optional ROI names
- optional network labels
- optional TR

**Inspect these outputs:**

- fmri_metrics plugin
- coupling_networkedness
- heterogeneity
- task_hints

**Recommended environments:** notebook, python_script, neuro_stack, ml_benchmark

### `EEGInput`

**Signature:** `EEGInput(values, sampling_rate=None, timestamps=None, channel_names=None, subject_ids=None, montage_name=None, ...) `

**Purpose:** Typed wrapper for EEG/MEG-style multichannel recordings.

**Why this API exists:** Electrophysiology users need channel names and sampling rate to unlock bandpower and rhythmicity-aware proxies. A typed wrapper is cleaner than overloading raw arrays with ad-hoc kwargs.

**When to use it:** Use when you have dense multichannel neural recordings and want domain-aware spectral summaries.

**Returns:** Typed input object for profile_dataset

**Accepted inputs / context:**

- NumPy-like EEG arrays
- sampling rate
- channel names

**Inspect these outputs:**

- eeg_bandpower plugin
- rhythmicity
- noise_contamination
- alpha_peak_prominence

**Recommended environments:** notebook, python_script, neuro_stack, ml_benchmark

### `IrregularSubjectInput / IrregularTimeSeriesInput`

**Signature:** `IrregularSubjectInput(values, timestamps, channel_names=None, metadata=None); IrregularTimeSeriesInput(subjects, domain=None, ...) `

**Purpose:** Represent timestamped irregular or asynchronous observations explicitly.

**Why this API exists:** Irregular data should not be silently coerced into regular grids. These wrappers preserve real timestamps, per-channel asynchrony, and missing support so irregular-aware proxies and reliability caveats can be computed honestly.

**When to use it:** Use for ICU vitals, clinical monitoring, sparse observational cohorts, or any nonuniformly sampled series.

**Returns:** Typed input objects for profile_dataset

**Accepted inputs / context:**

- per-subject irregular value arrays
- parallel timestamp arrays
- optional channel names

**Inspect these outputs:**

- sampling_irregularity
- irregular_observation plugin
- reliability notes

**Recommended environments:** notebook, python_script, pandas_pipeline, cli_batch

### `EventStreamInput`

**Signature:** `EventStreamInput(timestamps, channels=None, values=None, subjects=None, event_types=None, ...) `

**Purpose:** Represent sparse event streams such as alarms, coded events, transactions, or interventions.

**Why this API exists:** A stream of timestamped events is not the same as a dense sampled signal. This wrapper lets echotime estimate burstiness, event-type diversity, and event-stream archetypes without pretending the data are regular arrays.

**When to use it:** Use for sparse operational events, treatment events, alarms, clicks, or transactional logs.

**Returns:** Typed input object for profile_dataset

**Accepted inputs / context:**

- event timestamps
- optional event labels/channels
- optional values/marks

**Inspect these outputs:**

- event_stream plugin
- eventness_burstiness
- archetypes

**Recommended environments:** notebook, python_script, cli_batch, pandas_pipeline

## ontology inspection

### `schema_dict / get_schema`

**Signature:** `schema_dict() -> dict; get_schema() -> tuple[AxisSpec, ...]`

**Purpose:** Expose the stable ontology schema programmatically.

**Why this API exists:** An ontology-driven library must make its schema inspectable and versioned. These functions let downstream tools, dataset cards, and documentation stay aligned with the real axis/subdimension/proxy map.

**When to use it:** Use when building dashboards, validators, reports, or benchmark cards around echotime.

**Returns:** Schema dictionary or typed schema tuple

**Accepted inputs / context:**

- none

**Inspect these outputs:**

- axes
- subdimensions
- proxy names
- schema_version

**Recommended environments:** notebook, python_script, cli_batch, ml_benchmark

## extensibility

### `register_adaptor / register_plugin / clear_custom_extensions`

**Signature:** `register_adaptor(adaptor); register_plugin(plugin); clear_custom_extensions()`

**Purpose:** Extend echotime to new data containers and domain-specific metrics.

**Why this API exists:** Cross-disciplinary infrastructure must be extensible. Adaptors let the package ingest new object types; plugins let communities add domain metrics without forking the ontology core.

**When to use it:** Use when integrating a local data object, a lab-specific pipeline, or new domain metrics.

**Returns:** Registry side-effects

**Accepted inputs / context:**

- custom adaptor objects
- custom plugin objects

**Inspect these outputs:**

- plugin_metrics
- metadata['native_adaptor']
- custom notes

**Recommended environments:** python_script, neuro_stack, ml_benchmark, pandas_pipeline

## plain-language communication

### `summary_card / narrative_report / profile.to_summary_card_* / profile.to_narrative_report`

**Signature:** `summary_card(profile, audience='general', format='markdown'); narrative_report(profile, audience='general', format='markdown'); DatasetProfile.to_summary_card_markdown(); DatasetProfile.to_narrative_report()`

**Purpose:** Turn a structural profile into something a non-method user can read quickly.

**Why this API exists:** A cross-disciplinary tool must explain itself to clinicians, operators, product teams, and collaborators who do not want to inspect raw proxy metrics. These APIs convert the same profile into a summary card and a prose narrative without hiding the underlying evidence.

**When to use it:** Use when presenting results to domain experts, attaching a profile to a dataset handoff, or writing methods-light project notes.

**Returns:** Markdown/JSON plain-language reports

**Accepted inputs / context:**

- DatasetProfile or SeriesProfile
- optional audience label such as general, clinical, product, or neuroscience

**Inspect these outputs:**

- executive summary
- top structure axes
- watchouts
- recommended next actions
- narrative report sections

**Recommended environments:** notebook, python_script, cli_batch

## built-in guidance

### `case_gallery`

**Signature:** `case_gallery(domain=None, audience=None, environment=None, format='markdown')`

**Purpose:** Browse high-visibility cross-disciplinary use cases where echotime fits naturally.

**Why this API exists:** New users often understand a tool fastest through concrete cases instead of abstract API descriptions. The case gallery shows popular time-series settings such as web traffic, retail demand, energy load, wearables, ICU monitoring, and fMRI.

**When to use it:** Use when onboarding collaborators, choosing demos, or matching the package to a real-world workflow.

**Returns:** Markdown/text/JSON case gallery

**Accepted inputs / context:**

- optional domain, audience, and environment filters

**Inspect these outputs:**

- popular cases
- recommended entrypoints
- what to show non-method users
- practical value

**Recommended environments:** notebook, python_script, cli_batch

### `about / api_reference / scenario_guide / environment_matrix / workflow_recommendation / user_guide`

**Signature:** `about(format='markdown'); api_reference(format='markdown'); scenario_guide(domain=None, environment=None, scenario=None, format='markdown'); environment_matrix(format='markdown'); workflow_recommendation(domain=None, environment=None, scenario=None, format='markdown'); user_guide(format='markdown')`

**Purpose:** In-package documentation and onboarding helpers.

**Why this API exists:** Community tools need a discoverable explanation layer. These functions let users ask the package itself what it does, when to use each API, and which workflows fit their domain or environment.

**When to use it:** Use when onboarding a new lab, writing docs, teaching users, or generating scenario-specific guidance from Python or the CLI.

**Returns:** Markdown/text/JSON guide content

**Accepted inputs / context:**

- optional domain/environment filters

**Inspect these outputs:**

- about
- API catalog
- scenario playbooks
- environment matrix
- workflow guide

**Recommended environments:** notebook, python_script, cli_batch

### `hot_case_gallery / similarity_playbook / project_homepage_html / project_playground_html`

**Signature:** `hot_case_gallery(...); similarity_playbook(...); project_homepage_html(version='0.17.0'); project_playground_html(version='0.17.0')`

**Purpose:** Provide shareable, high-attention case ideas plus a static project-homepage starting point.

**Why this API exists:** Community adoption grows faster when the package already knows how to explain itself through timely examples and a reusable project page.

**When to use it:** Use when you want demos that can travel on social, in blog posts, on GitHub Pages, or in onboarding decks.

**Returns:** Markdown/JSON guides and a self-contained HTML string

**Accepted inputs / context:**

- optional audience/window filters

**Inspect these outputs:**

- hot cases
- similarity guidance
- homepage HTML

**Recommended environments:** python_script, cli_batch, notebook

## similarity analysis

### `compare_series`

**Signature:** `compare_series(left, right, *, left_timestamps=None, right_timestamps=None, left_name='left', right_name='right', n_points=256) -> SimilarityReport`

**Purpose:** Compare two raw trajectories using shape, DTW, trend, derivative, and spectral similarity.

**Why this API exists:** Cross-disciplinary users often want to say 'does this curve look like that one?' before they want a full forecasting or classification model. This API gives that question a structured answer.

**When to use it:** Use for GitHub star growth, crypto or commodity price windows, launch-week traffic curves, and any pair of trajectories where shape matters.

**Returns:** SimilarityReport

**Accepted inputs / context:**

- univariate arrays
- multichannel arrays
- optional timestamps

**Inspect these outputs:**

- reference_metrics
- component_mean
- component_scores
- to_summary_card_markdown()
- to_narrative_report()

**Recommended environments:** notebook, python_script, cli_batch, pandas_pipeline

### `compare_profiles`

**Signature:** `compare_profiles(left, right, *, left_name='left profile', right_name='right profile') -> SimilarityReport`

**Purpose:** Compare two echotime profiles or raw datasets at the ontology-axis level.

**Why this API exists:** Sometimes raw units and scales differ too much for direct shape matching, but the datasets are still structurally analogous. Profile similarity answers that higher-level question.

**When to use it:** Use for cross-domain analogies, benchmark curation, or when you want to explain that two datasets are 'the same kind of temporal problem'.

**Returns:** SimilarityReport

**Accepted inputs / context:**

- DatasetProfile
- SeriesProfile
- or raw inputs accepted by profile_dataset

**Inspect these outputs:**

- overall_axis_similarity
- dynamic_similarity
- multivariate_similarity
- metadata['axis_similarity']

**Recommended environments:** notebook, python_script, ml_benchmark, pandas_pipeline

### `rolling_similarity`

**Signature:** `rolling_similarity(left, right, *, window, step=1, left_timestamps=None, right_timestamps=None, n_points=128) -> list[dict]`

**Purpose:** Track how similarity changes over aligned rolling windows.

**Why this API exists:** Many high-traffic stories are regime stories: BTC and gold are similar in some windows but not others, and launch-week growth patterns drift over time.

**When to use it:** Use for windowed market comparisons, launch tracking, and changing relationships over time.

**Returns:** list of per-window similarity summaries

**Accepted inputs / context:**

- pair of arrays or multichannel arrays
- window length
- optional timestamps

**Inspect these outputs:**

- component_mean
- pearson_r
- shape_similarity
- trend_similarity
- spectral_similarity

**Recommended environments:** notebook, python_script, pandas_pipeline

### `ncc_sequence / max_ncc / best_shift / sbd / independent_max_ncc / independent_sbd / acf_distance / periodogram_distance / trend_distance / ordinal_pattern_js_distance / linear_trend_model_distance / lcss_similarity / lcss_distance / edr_distance / erp_distance / twed_distance`

**Signature:** `ncc_sequence(x, y, *, normalize=True) -> tuple[np.ndarray, np.ndarray]; max_ncc(...) -> float; best_shift(...) -> int; sbd(...) -> float; independent_max_ncc(...) -> float; independent_sbd(...) -> float; acf_distance(x, y, *, max_lag=10) -> float; periodogram_distance(x, y, *, n_coeffs=32) -> float; trend_distance(x, y) -> float; ordinal_pattern_js_distance(x, y, *, order=3, delay=1) -> float; linear_trend_model_distance(x, y) -> float; lcss_similarity(x, y, *, epsilon=1.0, window=None, mode='exact') -> float; lcss_distance(x, y, *, epsilon=1.0, window=None, mode='exact') -> float; edr_distance(x, y, *, epsilon=1.0, normalized=True, window=None, mode='exact') -> float; erp_distance(x, y, *, gap_value=0.0, window=None, mode='exact') -> float; twed_distance(x, y, *, lambda_=1.0, nu=0.001, t_x=None, t_y=None, window=None, mode='exact') -> float`

**Purpose:** Expose the extracted low-level similarity primitives directly when you need one explicit metric instead of a report bundle, including a fast screening path for the elastic distances.

**Why this API exists:** EchoTime's main surface is intentionally report-first, but advanced users still need direct access to shift-aware, rhythm-aware, and elastic distances for retrieval, thresholding, and custom pipelines.

**When to use it:** Use when you already know which similarity family you need and want a scalar score or lag estimate to plug into downstream logic; use `mode='fast'` for shortlist screening and `mode='exact'` for final reporting.

**Returns:** NumPy arrays, scalar similarities, scalar distances, or a best-lag integer depending on the function

**Accepted inputs / context:**

- 1D arrays
- 2D multichannel arrays
- optional timestamps for TWED
- optional gap, tolerance, or band-width hyperparameters for elastic methods
- `mode='fast'` for shortlist screening, `mode='exact'` for final scoring

**Inspect these outputs:**

- the returned scalar score or distance
- the lag array from ncc_sequence
- best_shift for lead-lag interpretation

**Recommended environments:** notebook, python_script, ml_benchmark, pandas_pipeline

## agent driving

### `AgentDriver / agent_drive / agent_context`

**Signature:** `AgentDriver(goal='understand_dataset', budget='lean|balanced|deep', ...); agent_drive(data, reference=None, goal=..., budget=...); agent_context(profile_or_similarity_report, budget='lean')`

**Purpose:** Let an agent or application choose the cheapest useful EchoTime workflow and export a compact context bundle.

**Why this API exists:** LLM agents often waste tokens by running too many analyses and by carrying oversized intermediate reports. This API chooses a small workflow first, stops early when the signal is already clear, and compresses the result into a reusable context payload.

**When to use it:** Use when echotime sits inside an agent loop, a notebook assistant, a retrieval pipeline, or a batch report generator that needs compact summaries.

**Returns:** AgentDriveResult or compact context dict/markdown/json

**Accepted inputs / context:**

- the same raw inputs accepted by profile_dataset or compare_series
- optional reference trajectory for comparison goals
- a goal string that explains what the agent is trying to solve

**Inspect these outputs:**

- result.steps
- result.compact_context
- result.token_saving_rationale
- result.to_context_markdown()

**Recommended environments:** notebook, python_script, cli_batch, pandas_pipeline, ml_benchmark


# EchoTime environment matrix

| environment | title | best for | typical inputs | what echotime adds | usual outputs |
|---|---|---|---|---|---|
| notebook | Jupyter or interactive notebook | Exploration, teaching, hypothesis generation, and profile inspection. | arrays; DataFrames; typed wrappers | Lets you move from raw data to a readable structural profile in a few lines and inspect notes, cards, and reliability interactively. | profile.axes; Markdown report; dataset card; API guide functions |
| python_script | Plain Python script or package pipeline | Reusable profiling steps in research codebases or internal libraries. | arrays; typed wrappers; tables; custom adapted objects | Makes structural profiling reproducible and scriptable for data intake, QC, or benchmark preparation. | JSON payloads; card files; profile.to_dict() |
| cli_batch | CLI and shell batch jobs | Quick audits, CI checks, and dataset-card generation without writing Python glue. | .npy/.npz arrays; .csv/.json/.jsonl/.parquet tables | Turns profile generation into a shell-friendly step and now also exposes guide content from the command line. | stdout text; Markdown report; card JSON/Markdown; guide documents |
| pandas_pipeline | Pandas / parquet / tabular data pipeline | Clinical, wearable, and observational data already organized as long or wide tables. | DataFrame; parquet path; CSV/TSV/JSON/JSONL path; record lists | Keeps you in the same tabular ecosystem while adding structural profiling, longitudinal interpretation, and dataset cards. | profile axes; longitudinal plugin metrics; card exports |
| neuro_stack | Neuro stack (MNE-like / xarray-like / ROI arrays) | Neural time-series workflows that already use ecosystem-specific containers. | MNE-like objects; xarray-like objects; FMRIInput; EEGInput | Adds a structure-aware summary layer without forcing you to abandon domain-native containers. | domain-aware plugin metrics; network summaries; cards for publications/benchmarks |
| ml_benchmark | ML benchmark or evaluation pipeline | Benchmark curation, dataset coverage analysis, and metadata generation for model comparisons. | any adapted dataset form | Provides stable ontology axes, schema versioning, reliability summaries, and machine-readable cards that can travel with a benchmark suite. | card JSON; schema export; comparable axis vectors |

## Notes by environment

### Jupyter or interactive notebook (`notebook`)

- Best environment for first contact with a new dataset.
- Combine with about(), api_reference(), and scenario_guide() to onboard collaborators.

### Plain Python script or package pipeline (`python_script`)

- Good fit when you want deterministic artifact generation.
- The registry API is easiest to integrate from scripts.

### CLI and shell batch jobs (`cli_batch`)

- Useful for data release pipelines and benchmark registries.
- Parquet support depends on the runtime having a parquet engine installed.

### Pandas / parquet / tabular data pipeline (`pandas_pipeline`)

- Ideal when your storage layer is already tabular.
- Longitudinal columns such as subject, visit, time, and channel unlock richer interpretation.

### Neuro stack (MNE-like / xarray-like / ROI arrays) (`neuro_stack`)

- Use typed wrappers when you want explicit metadata such as TR or channel names.
- echotime complements, rather than replaces, domain packages.

### ML benchmark or evaluation pipeline (`ml_benchmark`)

- Best environment when you need repeatable cards across many datasets.
- The package is descriptive infrastructure, not a benchmark runner.


# EchoTime scenario guide

## Resting-state or task fMRI cohort profiling

**scenario key:** `fmri_resting_state`  
**domains:** fmri  
**environments:** notebook, python_script, neuro_stack, ml_benchmark

**Data shape:** subjects × time × ROI, ROI-wise tables, or xarray-like neuroimaging containers

**Typical inputs:**

- FMRIInput
- xarray-like object
- 3D NumPy array

**Where EchoTime helps:** Acts as a dataset-card and structure-audit layer before graph modelling, connectome analyses, or benchmark comparison.

**Best entrypoints:**

- `profile_dataset(FMRIInput(...))`
- `profile_dataset(xarray_like_obj)`
- `profile_dataset(array, domain='fmri', tr=...)`

**Outputs to inspect:**

- coupling_networkedness
- heterogeneity
- regime_switching
- plugin_metrics['fmri_metrics']
- plugin_metrics['network_metrics']
- task_hints

**What you can do with it:**

- Compare datasets or cohorts structurally before training models.
- Summarize how networked, heterogeneous, or low-frequency-dominated a dataset is.
- Export a dataset card for benchmark documentation or supplement material.

**Caveats:**

- Provide TR whenever possible for Hz-aware metrics.
- echotime does not replace neuroimaging preprocessing or connectome estimation packages.

## EEG or electrophysiology recording triage

**scenario key:** `eeg_recording_qc`  
**domains:** eeg  
**environments:** notebook, python_script, neuro_stack, ml_benchmark

**Data shape:** time × channel arrays, subject × time × channel cohorts, or MNE-like objects

**Typical inputs:**

- EEGInput
- MNE Raw/Epochs/Evoked-like object
- 2D/3D arrays

**Where EchoTime helps:** Provides a fast structural summary layer before decoding, spectral analysis, or representation learning.

**Best entrypoints:**

- `profile_dataset(EEGInput(...))`
- `profile_dataset(mne_like_obj)`

**Outputs to inspect:**

- rhythmicity
- noise_contamination
- nonlinearity_chaoticity
- plugin_metrics['eeg_bandpower']
- reliability

**What you can do with it:**

- Spot low-rhythmicity or high-noise recordings before downstream analysis.
- Compare cohorts by bandpower-heavy vs noise-heavy structure.
- Generate reproducible cards for datasets used in decoding benchmarks.

**Caveats:**

- Sampling rate is important for EEG-specific proxies.
- The package profiles structure; it does not perform artifact rejection or source reconstruction.

## Irregular clinical monitoring or sparse hospital telemetry

**scenario key:** `clinical_irregular_monitoring`  
**domains:** clinical  
**environments:** notebook, python_script, pandas_pipeline, cli_batch

**Data shape:** subject-wise irregular observations, asynchronous channels, long hospital tables, or CSV/parquet extracts

**Typical inputs:**

- IrregularTimeSeriesInput
- pandas DataFrame
- CSV/parquet path
- list of record dicts

**Where EchoTime helps:** Audits observation irregularity, eventness, drift, and cohort heterogeneity before modelling or cohort QC.

**Best entrypoints:**

- `profile_dataset(IrregularTimeSeriesInput(...), domain='clinical')`
- `profile_dataset(dataframe, domain='clinical')`
- `echotime cohort.parquet --input-mode table --domain clinical`

**Outputs to inspect:**

- sampling_irregularity
- drift_nonstationarity
- eventness_burstiness
- plugin_metrics['irregular_observation']
- reliability notes

**What you can do with it:**

- Decide whether timestamp irregularity is a primary modelling concern.
- Document missingness and follow-up instability for cohort reports.
- Feed dataset cards into benchmarking or data-governance workflows.

**Caveats:**

- For very sparse data, interpret frequency-aware metrics conservatively.
- echotime does not impute, resample, or fit clinical prediction models for you.

## Wearable or digital biomarker longitudinal cohort

**scenario key:** `wearable_longitudinal_cohort`  
**domains:** wearable, clinical  
**environments:** notebook, python_script, pandas_pipeline, ml_benchmark, cli_batch

**Data shape:** long tables with subject / visit / time / channel / value columns or wide wearable frames

**Typical inputs:**

- pandas DataFrame
- parquet/CSV path
- list of records

**Where EchoTime helps:** Profiles adherence, repeated-visit instability, subject fingerprintability, and cohort heterogeneity for longitudinal studies.

**Best entrypoints:**

- `profile_dataset(dataframe, domain='wearable')`
- `echotime study.parquet --input-mode table --domain wearable --format card-markdown`

**Outputs to inspect:**

- sampling_irregularity
- heterogeneity
- plugin_metrics['longitudinal_metrics']
- task_hints
- dataset card exports

**What you can do with it:**

- Understand whether your cohort is dominated by dropout, visit imbalance, or subject-specific structure.
- Decide whether leave-subject-out or leave-visit-out validation is more defensible.
- Generate methods-ready summaries for study documentation.

**Caveats:**

- Parquet reading requires a parquet engine such as pyarrow at runtime.
- The package reports longitudinal structure; it does not replace biostatistical mixed-effects analysis.

## Environmental or industrial multichannel sensor datasets

**scenario key:** `environmental_sensor_network`  
**domains:** generic  
**environments:** notebook, python_script, pandas_pipeline, ml_benchmark, cli_batch

**Data shape:** dense or mildly gappy multichannel series, station networks, or machine telemetry tables

**Typical inputs:**

- 2D/3D arrays
- pandas DataFrame
- xarray-like object

**Where EchoTime helps:** Provides trend, rhythmicity, drift, coupling, and noise summaries before forecasting or anomaly pipelines.

**Best entrypoints:**

- `profile_dataset(array)`
- `profile_dataset(dataframe)`
- `profile_dataset(xarray_like_obj)`

**Outputs to inspect:**

- trendness
- rhythmicity
- drift_nonstationarity
- coupling_networkedness
- task_hints

**What you can do with it:**

- Compare stations, machines, or datasets structurally.
- Screen for seasonality-heavy vs drift-heavy problems.
- Produce dataset cards for shared forecasting benchmarks.

**Caveats:**

- echotime does not replace forecasting model selection or domain simulators.
- If timestamps are absent, irregularity diagnostics are naturally weaker.

## Sparse event streams, alerts, clicks, or treatment logs

**scenario key:** `event_stream_operations`  
**domains:** generic, clinical  
**environments:** notebook, python_script, pandas_pipeline, cli_batch

**Data shape:** timestamped event records with optional event type, channel, subject, and mark/value columns

**Typical inputs:**

- EventStreamInput
- long tables
- JSON/JSONL/CSV records

**Where EchoTime helps:** Quantifies burstiness, event diversity, and dataset-level event archetypes before point-process or event modelling.

**Best entrypoints:**

- `profile_dataset(EventStreamInput(...))`
- `profile_dataset(records_or_table)`

**Outputs to inspect:**

- eventness_burstiness
- plugin_metrics['event_stream']
- sampling_irregularity
- archetypes

**What you can do with it:**

- Differentiate bursty alarm streams from more regular event streams.
- Summarize whether event labels are diverse or dominated by one code.
- Create machine-readable cards for event benchmark datasets.

**Caveats:**

- Sparse event streams are represented generically; detailed point-process inference remains out of scope.
- Interpret time-series axes together with event plugin metrics rather than in isolation.

## Benchmark curation and dataset-card generation

**scenario key:** `benchmark_dataset_card`  
**domains:** generic, fmri, eeg, clinical, wearable  
**environments:** python_script, cli_batch, ml_benchmark

**Data shape:** any dataset that echotime can adapt

**Typical inputs:**

- anything accepted by profile_dataset

**Where EchoTime helps:** Acts as a repeatable structural profiler and card generator for dataset governance and benchmark transparency.

**Best entrypoints:**

- `profile_dataset(data).to_card_json()`
- `echotime data.npy --format card-json`

**Outputs to inspect:**

- card JSON
- card Markdown
- axes
- reliability
- ontology_schema

**What you can do with it:**

- Track structural coverage across benchmark suites.
- Attach cards to releases, papers, or internal registries.
- Compare new datasets against existing benchmark structure profiles.

**Caveats:**

- A dataset card is descriptive, not a substitute for task-specific evaluation.
- Reliability scores should be reported alongside the axes.


# EchoTime recommended workflow

**domain:** generic  
**environment:** notebook

**Recommended input setup:** Start with arrays or DataFrames; move to typed wrappers if semantic metadata matter.

**Priority axes:** predictability, drift_nonstationarity, trendness, rhythmicity, complexity

## Suggested steps

1. Organize the dataset in the most semantically faithful input form rather than stripping metadata too early.
2. Run profile_dataset(...) with domain-specific metadata such as sampling_rate, TR, channel names, visit columns, or explicit timestamps whenever available.
3. Inspect the priority axes together with reliability, notes, and domain/plugin metrics rather than reading any single score in isolation.
4. Export a dataset card so the profile can travel into papers, benchmark registries, or internal data catalogs.
5. Use task hints and reliability notes to guide model-family choice, validation design, and communication of caveats.

**Export tip:** Use profile.to_markdown() or profile.to_card_markdown() while exploring interactively.

## Relevant scenarios

### Environmental or industrial multichannel sensor datasets

Provides trend, rhythmicity, drift, coupling, and noise summaries before forecasting or anomaly pipelines.

**Best entrypoints:**

- `profile_dataset(array)`
- `profile_dataset(dataframe)`
- `profile_dataset(xarray_like_obj)`

### Sparse event streams, alerts, clicks, or treatment logs

Quantifies burstiness, event diversity, and dataset-level event archetypes before point-process or event modelling.

**Best entrypoints:**

- `profile_dataset(EventStreamInput(...))`
- `profile_dataset(records_or_table)`


# EchoTime similarity guide

Similarity in EchoTime is not one thing. Sometimes you care about raw point-by-point shape, sometimes about shared rhythm, and sometimes about structural similarity at the dataset level.

## When to use raw-series similarity

Use raw-series similarity when two trajectories live on roughly compatible time scales and you want to ask whether the visible shape or timing is alike.

## When to use profile similarity

Use profile similarity when the datasets come from different scales, units, or observation modes, but you still want to compare their structural character.

## Best first moves

- Decide whether you are comparing levels, returns, increments, or z-scored shape.
- Preserve timestamps and event annotations instead of stripping them away.
- Use rolling similarity for regimes that probably change over time.
- Show both the numeric similarity report and a simple overlay plot.

## API pattern

- `compare_series(left, right) for direct shape comparison`
- `rolling_similarity(left, right, window=...) for changing relationships over time`
- `compare_profiles(left, right) for dataset-level structural analogies`

## How to explain the outputs to non-method users

- High shape similarity means the curves visibly move alike.
- High spectral similarity means the rhythms match even if peaks happen at slightly different times.
- High profile similarity means the datasets behave like the same kind of temporal problem even if the raw numbers differ.

# EchoTime agent-driving guide

Agent-driving is a lightweight orchestration layer that helps an LLM or application choose the smallest useful EchoTime workflow and export a compact context bundle.

## Token-saving principles

- Start with the cheapest informative move.
- Stop early when the signal is already clear.
- Upgrade to structural comparison only when raw shape is ambiguous or the question is structural.
- Render summary cards and narratives from existing profiles instead of recomputing analysis.
- Pass compact context bundles back into the agent instead of full raw reports when the next step only needs the gist.

## Main API

- `AgentDriver(goal=..., budget='lean|balanced|deep')`
- `agent_drive(data, reference=None, goal=..., budget=...)`
- `agent_context(profile_or_similarity_report, budget='lean')`

## Budget modes

- **lean:** Do the cheapest sufficient move and stop when the signal is clear.
- **balanced:** Add structural/profile comparison when ambiguity remains.
- **deep:** Allow rolling similarity and a fuller context bundle for regime-sensitive questions.

## Good goal prompts

- Explain this dataset to a non-technical collaborator
- Decide whether repo A's growth curve resembles repo B
- Compare these two assets but keep the context compact for another LLM step
- Find out whether two datasets are the same kind of temporal problem

# EchoTime case gallery

These are high-visibility, cross-disciplinary time-series cases where EchoTime is meant to be useful.

## Web/app traffic and product analytics

**case key:** `web_product_traffic`  
**domains:** generic, product, web, traffic  
**audiences:** general, product, operations, cross-disciplinary  
**environments:** notebook, python_script, pandas_pipeline, cli_batch

**Why people care:** Traffic, conversion, and usage metrics are easy to explain to broad audiences and are often the first time-series many teams operationalize.

**Typical data:** Hourly or daily sessions, clicks, conversions, campaign spikes, release-day shocks, and multi-metric product dashboards.

**Common questions:**

- Is this mostly trend plus seasonality, or is it dominated by launches and bursts?
- Should we trust simple forecasting baselines, or is the system drifting too much?
- Which metrics move together strongly enough to justify multivariate modelling?

**Where EchoTime helps:** It gives a plain-language structural readout before teams jump into forecasting, anomaly detection, or KPI attribution debates.

**Recommended entrypoints:**

- `profile_dataset(dataframe, domain='traffic')`
- `profile_dataset(array, domain='product')`
- `profile.to_summary_card_markdown()`

**What to show non-method users:**

- summary card with top axes and plain-language meanings
- narrative report explaining whether the data are steady, seasonal, bursty, or drifting
- dataset card attached to experiment or dashboard documentation

**Practical value:**

- Explain why weekly seasonality matters before model selection.
- Flag that campaign bursts can distort average-based summaries.
- Communicate when traffic is stable enough for lightweight baselines.

## Retail demand, inventory, and operations planning

**case key:** `retail_demand_operations`  
**domains:** generic, retail, operations, supply_chain  
**audiences:** general, operations, cross-disciplinary  
**environments:** notebook, python_script, pandas_pipeline, cli_batch

**Why people care:** Demand planning is a high-visibility time-series use case because it directly affects stockouts, staffing, and revenue.

**Typical data:** Store- or SKU-level sales, promotion calendars, replenishment signals, and holiday-driven demand waves.

**Common questions:**

- How strong is the predictable seasonality relative to promo shocks?
- How heterogeneous are stores or SKUs?
- Should validation split by time only, or by store/product group as well?

**Where EchoTime helps:** It clarifies whether the dataset is mostly rhythmic, drift-heavy, bursty, or highly heterogeneous across units.

**Recommended entrypoints:**

- `profile_dataset(dataframe, domain='operations')`
- `profile.to_summary_card_markdown()`
- `profile.to_narrative_report()`

**What to show non-method users:**

- one-page summary card for merchants or operators
- narrative report that translates axes into replenishment implications

**Practical value:**

- Separate seasonality-heavy planning problems from campaign-shock problems.
- Justify store-aware or SKU-aware validation.
- Document when heterogeneity makes one pooled model hard to trust.

## Energy load, smart metering, and grid operations

**case key:** `energy_load_and_smart_metering`  
**domains:** generic, energy, operations, environmental  
**audiences:** general, operations, cross-disciplinary  
**environments:** notebook, python_script, pandas_pipeline, ml_benchmark

**Why people care:** Energy load is a classic public-facing time-series use case with clear seasonality, weather sensitivity, and operational stakes.

**Typical data:** Building load curves, feeder demand, smart-meter cohorts, distributed sensors, and weather-linked covariates.

**Common questions:**

- How much of the signal is predictable daily/weekly rhythm?
- Do sites behave similarly enough to pool them?
- Are drifts or regime changes strong enough to break static models?

**Where EchoTime helps:** It turns those questions into a structured profile that is easy to compare across sites or benchmark datasets.

**Recommended entrypoints:**

- `profile_dataset(array, domain='energy')`
- `profile_dataset(dataframe, domain='energy')`
- `profile.to_card_json()`

**What to show non-method users:**

- plain-language summary of rhythm, drift, and heterogeneity
- dataset card for benchmark governance or site comparison

**Practical value:**

- Show when seasonality dominates enough for strong baseline models.
- Flag when regime changes or drifts make historic averages unreliable.

## Wearable, digital biomarker, or recovery cohort

**case key:** `wearable_longitudinal_cohort`  
**domains:** wearable, clinical  
**audiences:** general, clinical, cross-disciplinary  
**environments:** notebook, python_script, pandas_pipeline, cli_batch

**Why people care:** Wearables are one of the highest-traffic modern time-series domains because they connect research, product, health, and consumer reporting.

**Typical data:** Heart rate, activity, sleep, recovery, repeated visits, device adherence gaps, and subject-level timelines.

**Common questions:**

- Is the problem dominated by adherence gaps and irregular follow-up?
- Are people more different from each other than days are within each person?
- Should evaluation split by subject, visit, or time?

**Where EchoTime helps:** It exposes longitudinal instability, dropout imbalance, and heterogeneity in a way clinicians and product teams can both read.

**Recommended entrypoints:**

- `profile_dataset(dataframe, domain='wearable')`
- `profile.to_summary_card_markdown()`
- `profile.to_narrative_report()`

**What to show non-method users:**

- summary card for study coordinators or clinicians
- narrative report explaining adherence, subject differences, and validation implications

**Practical value:**

- Make longitudinal cohort quality visible before model building.
- Show whether individual fingerprint structure is strong enough to matter.

## ICU, hospital telemetry, and irregular monitoring

**case key:** `icu_irregular_monitoring`  
**domains:** clinical  
**audiences:** general, clinical, cross-disciplinary  
**environments:** notebook, python_script, pandas_pipeline, cli_batch

**Why people care:** Irregular clinical monitoring is high-impact because timestamp quality, sparsity, and bursts of interventions strongly affect downstream claims.

**Typical data:** Irregular vitals, labs, interventions, alarms, asynchronous channels, and mixed event-plus-signal timelines.

**Common questions:**

- Are timing irregularity and missingness the main difficulty?
- Does the dataset behave like a sparse event process or a dense physiological signal?
- How much do patients differ structurally?

**Where EchoTime helps:** It keeps observation structure honest and gives non-method collaborators a reasoned explanation for why naive regular-grid assumptions may fail.

**Recommended entrypoints:**

- `profile_dataset(IrregularTimeSeriesInput(...), domain='clinical')`
- `profile_dataset(records_or_dataframe, domain='clinical')`
- `profile.to_narrative_report()`

**What to show non-method users:**

- narrative report for clinicians, data stewards, or protocol teams
- summary card that highlights irregularity, burstiness, and reliability caveats

**Practical value:**

- Document why explicit timestamps must be preserved.
- Flag when event bursts dominate over smooth trends.

## Resting-state or task fMRI cohort

**case key:** `resting_state_fmri`  
**domains:** fmri, neuro  
**audiences:** general, neuroscience, cross-disciplinary  
**environments:** notebook, python_script, neuro_stack, ml_benchmark

**Why people care:** fMRI is a flagship scientific time-series setting where multivariate coupling and cohort heterogeneity matter as much as single-node signals.

**Typical data:** Subject × time × ROI matrices, network labels, resting-state or task blocks, and cohort-level comparisons.

**Common questions:**

- How networked is the dataset?
- How much do subjects differ in temporal organization?
- Should models be framed as multivariate/network-aware rather than independent ROI series?

**Where EchoTime helps:** It turns networked temporal structure into a dataset card that non-method collaborators can actually read.

**Recommended entrypoints:**

- `profile_dataset(FMRIInput(...))`
- `profile.to_summary_card_markdown()`
- `profile.to_narrative_report()`

**What to show non-method users:**

- plain-language summary of coupling, heterogeneity, and rhythmic low-frequency structure
- narrative report suitable for supplements, preregistration, or lab onboarding

**Practical value:**

- Communicate why multivariate structure cannot be ignored.
- Summarize cohort-level differences before benchmarking new models.


# EchoTime hot case gallery

**window:** next_90_days  
**audience:** general

These are high-attention cases chosen for shareability, public interest, and clear time-series storytelling.

## OpenClaw GitHub stars and star-velocity bursts

**case key:** `openclaw_star_velocity`  
**Likely attention window:** March–May 2026

**Why this can travel:** This is a classic hype-cycle time series: a fast open-source project with social amplification, release-driven bursts, and potential security/event shocks.

**Data to track:**

- daily star count
- daily new stars
- fork count
- release dates
- security/advisory dates
- docs traffic or install traffic if you have it

**Similarity questions worth asking:**

- Does the current 14-day growth curve look more like an organic climb or a short viral spike?
- Do post-release star surges resemble earlier release windows?
- How similar is OpenClaw's growth to another breakout GitHub project?

**Recommended API:**

- `compare_series(current_window, historical_window)`
- `rolling_similarity(repo_a_daily_stars, repo_b_daily_stars, window=14)`
- `compare_profiles(dataset_a, dataset_b)`

**What non-method users should see:**

- a similarity summary saying whether this looks like another sustainable growth window or just a spike
- a narrative report explaining whether rhythm, trend, or burstiness is driving the resemblance

**Notes:**

- Use cumulative stars and daily star increments side by side; they answer different questions.
- Keep event annotations such as releases, tweets, and advisories instead of only storing the numeric series.

## Breakout GitHub projects: compare star curves across launches

**case key:** `github_breakout_repo_benchmarks`  
**Likely attention window:** March–May 2026

**Why this can travel:** Developers, investors, and open-source founders all understand star-growth charts quickly, so they travel well across disciplines and social channels.

**Data to track:**

- daily stars for several repositories
- daily issues and pull requests
- release cadence
- referral traffic or docs sessions if available

**Similarity questions worth asking:**

- Which new repo most resembles a previous breakout launch in its first 30 days?
- Do two repos share the same long-tail decay pattern after the initial spike?
- Is a repo's community growth more similar to a consumer-product launch than to a typical open-source release?

**Recommended API:**

- `compare_series(repo_a_daily_stars, repo_b_daily_stars)`
- `compare_profiles(repo_a_panel, repo_b_panel)`
- `rolling_similarity(repo_a_daily_stars, repo_b_daily_stars, window=30)`

**What non-method users should see:**

- a leaderboard of nearest historical analogs
- a simple summary of whether two launches match in trend, timing, and volatility

**Notes:**

- Normalize by launch day or first 1,000 stars when comparing early-stage growth curves.

## BTC vs gold vs oil under shock and macro headlines

**case key:** `btc_vs_gold_vs_oil`  
**Likely attention window:** March–May 2026

**Why this can travel:** This is a high-traffic financial story because the three series often react differently to risk, inflation, liquidity, and geopolitical shocks.

**Data to track:**

- daily close or hourly close for BTC
- spot gold or gold ETF close
- Brent or WTI close
- major policy or geopolitical timestamps

**Similarity questions worth asking:**

- When does BTC move more like a risk asset and when does it resemble a stress-sensitive macro series?
- Do gold and oil share the same shock windows or only the same broad trend?
- Which pair becomes more similar during geopolitical escalation?

**Recommended API:**

- `compare_series(btc_returns, gold_returns)`
- `rolling_similarity(gold_returns, oil_returns, window=20)`
- `compare_profiles(window_a, window_b)`

**What non-method users should see:**

- a rolling similarity chart for pairs of assets
- a narrative report translating similarity changes into regime language

**Notes:**

- Use returns or z-scored prices when scales differ wildly.
- Rolling windows are usually more informative than one all-period average for the whole year.

## Launch-week traffic, signup bursts, and docs demand

**case key:** `launch_traffic_vs_signup_conversion`  
**Likely attention window:** Any 90-day launch or campaign window

**Why this can travel:** This is one of the fastest routes to a shareable time-series story because product teams, founders, and growth marketers immediately understand the plots.

**Data to track:**

- daily sessions
- daily signups
- docs traffic
- GitHub stars or waitlist growth
- campaign timestamps

**Similarity questions worth asking:**

- Did this launch behave more like a community release or a paid campaign burst?
- Are docs-traffic spikes synchronized with signup spikes?
- Which earlier launch is the nearest analog to the current one?

**Recommended API:**

- `compare_series(signups, docs_sessions)`
- `rolling_similarity(launch_a_sessions, launch_b_sessions, window=7)`
- `compare_profiles(product_a_dataset, product_b_dataset)`

**What non-method users should see:**

- a one-page launch summary with shared peaks, lagged peaks, and watchouts
- plain-language notes on whether the launch looks healthy or purely burst-driven

**Notes:**

- Keep campaign/event markers and channel labels if you want to explain the patterns later.
