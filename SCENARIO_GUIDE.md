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
