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
