"""User-facing guidance, API handbook, and scenario playbooks for echotime."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

from .schema import AXIS_DESCRIPTIONS, AXIS_ORDER, SCHEMA_VERSION

GuideFormat = Literal["markdown", "text", "json"]


@dataclass(frozen=True, slots=True)
class ApiEntry:
    name: str
    category: str
    signature: str
    purpose: str
    why_exists: str
    when_to_use: str
    returns: str
    accepted_inputs: tuple[str, ...]
    outputs_to_inspect: tuple[str, ...]
    recommended_environments: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    key: str
    title: str
    domains: tuple[str, ...]
    environments: tuple[str, ...]
    data_shape: str
    typical_inputs: tuple[str, ...]
    echotime_role: str
    best_entrypoints: tuple[str, ...]
    outputs_to_inspect: tuple[str, ...]
    what_you_can_do: tuple[str, ...]
    caveats: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EnvironmentSpec:
    key: str
    title: str
    best_for: str
    typical_inputs: tuple[str, ...]
    echotime_value: str
    usual_outputs: tuple[str, ...]
    notes: tuple[str, ...]


PACKAGE_SUMMARY = {
    "name": "echotime",
    "tagline": "Structure-aware dataset profiling for time-series data.",
    "one_sentence": (
        "EchoTime converts a time-series dataset into a structural profile: ontology axis scores, "
        "subdimensions, proxy metrics, reliability summaries, archetypes, task hints, and dataset cards."
    ),
    "what_it_is": (
        "A dataset-characterization layer that sits between raw time-series data and downstream modelling. "
        "It helps researchers understand what kind of temporal structure they have before they pick models, compare benchmarks, or write dataset documentation."
    ),
    "what_it_is_not": (
        "It is not a forecasting library, not a classifier, not a replacement for MNE/nilearn/pandas/xarray, and not just another bag-of-features extractor. "
        "It profiles datasets rather than training task models."
    ),
    "who_it_is_for": (
        "Researchers and engineers working with fMRI, EEG, clinical monitoring, wearable longitudinal cohorts, environmental sensors, industrial telemetry, tabular time-series lakes, and event streams."
    ),
    "core_outputs": (
        "ontology axes",
        "subdimension scores",
        "raw proxy metrics",
        "archetype labels",
        "task hints",
        "reliability and evidence",
        "dataset card JSON/Markdown",
        "plain-language summary card",
        "narrative report",
        "case gallery",
    ),
    "supported_input_families": (
        "dense NumPy-like arrays",
        "pandas DataFrame and tabular file paths",
        "FMRIInput and EEGInput typed wrappers",
        "irregular timestamped subjects",
        "event streams",
        "MNE-like and xarray-like objects",
    ),
    "main_question": "What kind of time-series dataset do I have, and what does that imply for analysis and modelling?",
}


API_ENTRIES: tuple[ApiEntry, ...] = (
    ApiEntry(
        name="profile_dataset",
        category="core profiling",
        signature=(
            "profile_dataset(data, *, domain=None, timestamps=None, time_axis=0, channel_axis=-1, "
            "subject_axis=0, sampling_rate=None, tr=None, channel_names=None, roi_names=None, "
            "network_labels=None, subject_ids=None, metadata=None, bootstrap=0, random_state=None) -> DatasetProfile"
        ),
        purpose="Primary entry point. Profile an entire dataset as a dataset.",
        why_exists=(
            "The core design choice of EchoTime is that the object of interest is the dataset, not just a single series. "
            "This function aggregates unit-level signals, multivariate structure, cohort variation, and observation characteristics into one profile."
        ),
        when_to_use=(
            "Use when you want the ontology axes, archetypes, task hints, reliability, and dataset-card outputs for a whole dataset or cohort."
        ),
        returns="DatasetProfile",
        accepted_inputs=(
            "1D/2D/3D arrays",
            "pandas DataFrame or tabular file path",
            "FMRIInput / EEGInput",
            "IrregularTimeSeriesInput",
            "EventStreamInput",
            "MNE-like or xarray-like object",
        ),
        outputs_to_inspect=(
            "profile.axes",
            "profile.subdimensions",
            "profile.archetypes",
            "profile.task_hints",
            "profile.reliability",
            "profile.to_card_json()",
        ),
        recommended_environments=("notebook", "python_script", "cli_batch", "pandas_pipeline", "neuro_stack", "ml_benchmark"),
    ),
    ApiEntry(
        name="profile_series",
        category="core profiling",
        signature="profile_series(series, *, timestamps=None, domain=None) -> SeriesProfile",
        purpose="Profile a single univariate series when a full dataset object is not needed.",
        why_exists=(
            "Users often want a lightweight sanity-check before moving to dataset-level profiling. This function keeps the interface simple for one series while still using the same ontology machinery."
        ),
        when_to_use="Use for quick checks, demos, or when your data truly consist of a single univariate stream.",
        returns="SeriesProfile",
        accepted_inputs=("1D array-like series", "optional timestamps"),
        outputs_to_inspect=("profile.axes", "profile.metrics", "profile.notes", "profile.to_markdown()"),
        recommended_environments=("notebook", "python_script"),
    ),
    ApiEntry(
        name="DatasetProfile",
        category="profile outputs",
        signature="DatasetProfile(...)",
        purpose="Rich result object returned by profile_dataset.",
        why_exists=(
            "A structural profile has both machine-readable and human-readable uses. The result object keeps raw metrics, ontology scores, notes, evidence, and rendering helpers together."
        ),
        when_to_use="Use after profiling to export reports, cards, or JSON payloads for downstream pipelines.",
        returns="Dataclass-like object with rendering methods",
        accepted_inputs=("created by profile_dataset" ,),
        outputs_to_inspect=("to_dict()", "to_json()", "to_markdown()", "to_card_json()", "to_card_markdown()", "to_summary_card_markdown()", "to_narrative_report()"),
        recommended_environments=("notebook", "python_script", "cli_batch", "ml_benchmark"),
    ),
    ApiEntry(
        name="SeriesProfile",
        category="profile outputs",
        signature="SeriesProfile(...)",
        purpose="Result object returned by profile_series.",
        why_exists="Mirrors DatasetProfile for single-series inspection while keeping the same rendering ergonomics.",
        when_to_use="Use when a quick series-level inspection is enough.",
        returns="Dataclass-like object with rendering methods",
        accepted_inputs=("created by profile_series",),
        outputs_to_inspect=("to_dict()", "to_json()", "to_markdown()", "to_card_json()", "to_summary_card_markdown()", "to_narrative_report()"),
        recommended_environments=("notebook", "python_script"),
    ),
    ApiEntry(
        name="FMRIInput",
        category="typed semantic inputs",
        signature="FMRIInput(values, tr=None, timestamps=None, roi_names=None, network_labels=None, subject_ids=None, ...) ",
        purpose="Typed wrapper for fMRI time-series collections.",
        why_exists=(
            "Neuroimaging arrays often lose semantic context such as TR, ROI names, and network labels. The wrapper preserves those pieces so fMRI-specific proxies and network summaries can run correctly."
        ),
        when_to_use="Use when you have subject × time × ROI data or ROI time-series and want neuro-aware profiling.",
        returns="Typed input object for profile_dataset",
        accepted_inputs=("NumPy-like fMRI arrays", "optional ROI names", "optional network labels", "optional TR"),
        outputs_to_inspect=("fmri_metrics plugin", "coupling_networkedness", "heterogeneity", "task_hints"),
        recommended_environments=("notebook", "python_script", "neuro_stack", "ml_benchmark"),
    ),
    ApiEntry(
        name="EEGInput",
        category="typed semantic inputs",
        signature="EEGInput(values, sampling_rate=None, timestamps=None, channel_names=None, subject_ids=None, montage_name=None, ...) ",
        purpose="Typed wrapper for EEG/MEG-style multichannel recordings.",
        why_exists=(
            "Electrophysiology users need channel names and sampling rate to unlock bandpower and rhythmicity-aware proxies. A typed wrapper is cleaner than overloading raw arrays with ad-hoc kwargs."
        ),
        when_to_use="Use when you have dense multichannel neural recordings and want domain-aware spectral summaries.",
        returns="Typed input object for profile_dataset",
        accepted_inputs=("NumPy-like EEG arrays", "sampling rate", "channel names"),
        outputs_to_inspect=("eeg_bandpower plugin", "rhythmicity", "noise_contamination", "alpha_peak_prominence"),
        recommended_environments=("notebook", "python_script", "neuro_stack", "ml_benchmark"),
    ),
    ApiEntry(
        name="IrregularSubjectInput / IrregularTimeSeriesInput",
        category="typed semantic inputs",
        signature="IrregularSubjectInput(values, timestamps, channel_names=None, metadata=None); IrregularTimeSeriesInput(subjects, domain=None, ...) ",
        purpose="Represent timestamped irregular or asynchronous observations explicitly.",
        why_exists=(
            "Irregular data should not be silently coerced into regular grids. These wrappers preserve real timestamps, per-channel asynchrony, and missing support so irregular-aware proxies and reliability caveats can be computed honestly."
        ),
        when_to_use="Use for ICU vitals, clinical monitoring, sparse observational cohorts, or any nonuniformly sampled series.",
        returns="Typed input objects for profile_dataset",
        accepted_inputs=("per-subject irregular value arrays", "parallel timestamp arrays", "optional channel names"),
        outputs_to_inspect=("sampling_irregularity", "irregular_observation plugin", "reliability notes"),
        recommended_environments=("notebook", "python_script", "pandas_pipeline", "cli_batch"),
    ),
    ApiEntry(
        name="EventStreamInput",
        category="typed semantic inputs",
        signature="EventStreamInput(timestamps, channels=None, values=None, subjects=None, event_types=None, ...) ",
        purpose="Represent sparse event streams such as alarms, coded events, transactions, or interventions.",
        why_exists=(
            "A stream of timestamped events is not the same as a dense sampled signal. This wrapper lets echotime estimate burstiness, event-type diversity, and event-stream archetypes without pretending the data are regular arrays."
        ),
        when_to_use="Use for sparse operational events, treatment events, alarms, clicks, or transactional logs.",
        returns="Typed input object for profile_dataset",
        accepted_inputs=("event timestamps", "optional event labels/channels", "optional values/marks"),
        outputs_to_inspect=("event_stream plugin", "eventness_burstiness", "archetypes"),
        recommended_environments=("notebook", "python_script", "cli_batch", "pandas_pipeline"),
    ),
    ApiEntry(
        name="schema_dict / get_schema",
        category="ontology inspection",
        signature="schema_dict() -> dict; get_schema() -> tuple[AxisSpec, ...]",
        purpose="Expose the stable ontology schema programmatically.",
        why_exists=(
            "An ontology-driven library must make its schema inspectable and versioned. These functions let downstream tools, dataset cards, and documentation stay aligned with the real axis/subdimension/proxy map."
        ),
        when_to_use="Use when building dashboards, validators, reports, or benchmark cards around echotime.",
        returns="Schema dictionary or typed schema tuple",
        accepted_inputs=("none",),
        outputs_to_inspect=("axes", "subdimensions", "proxy names", "schema_version"),
        recommended_environments=("notebook", "python_script", "cli_batch", "ml_benchmark"),
    ),
    ApiEntry(
        name="register_adaptor / register_plugin / clear_custom_extensions",
        category="extensibility",
        signature=(
            "register_adaptor(adaptor); register_plugin(plugin); clear_custom_extensions()"
        ),
        purpose="Extend echotime to new data containers and domain-specific metrics.",
        why_exists=(
            "Cross-disciplinary infrastructure must be extensible. Adaptors let the package ingest new object types; plugins let communities add domain metrics without forking the ontology core."
        ),
        when_to_use="Use when integrating a local data object, a lab-specific pipeline, or new domain metrics.",
        returns="Registry side-effects",
        accepted_inputs=("custom adaptor objects", "custom plugin objects"),
        outputs_to_inspect=("plugin_metrics", "metadata['native_adaptor']", "custom notes"),
        recommended_environments=("python_script", "neuro_stack", "ml_benchmark", "pandas_pipeline"),
    ),
    ApiEntry(
        name="summary_card / narrative_report / profile.to_summary_card_* / profile.to_narrative_report",
        category="plain-language communication",
        signature=(
            "summary_card(profile, audience='general', format='markdown'); narrative_report(profile, audience='general', format='markdown'); DatasetProfile.to_summary_card_markdown(); DatasetProfile.to_narrative_report()"
        ),
        purpose="Turn a structural profile into something a non-method user can read quickly.",
        why_exists=(
            "A cross-disciplinary tool must explain itself to clinicians, operators, product teams, and collaborators who do not want to inspect raw proxy metrics. These APIs convert the same profile into a summary card and a prose narrative without hiding the underlying evidence."
        ),
        when_to_use="Use when presenting results to domain experts, attaching a profile to a dataset handoff, or writing methods-light project notes.",
        returns="Markdown/JSON plain-language reports",
        accepted_inputs=("DatasetProfile or SeriesProfile", "optional audience label such as general, clinical, product, or neuroscience"),
        outputs_to_inspect=("executive summary", "top structure axes", "watchouts", "recommended next actions", "narrative report sections"),
        recommended_environments=("notebook", "python_script", "cli_batch"),
    ),
    ApiEntry(
        name="case_gallery",
        category="built-in guidance",
        signature="case_gallery(domain=None, audience=None, environment=None, format='markdown')",
        purpose="Browse high-visibility cross-disciplinary use cases where echotime fits naturally.",
        why_exists=(
            "New users often understand a tool fastest through concrete cases instead of abstract API descriptions. The case gallery shows popular time-series settings such as web traffic, retail demand, energy load, wearables, ICU monitoring, and fMRI."
        ),
        when_to_use="Use when onboarding collaborators, choosing demos, or matching the package to a real-world workflow.",
        returns="Markdown/text/JSON case gallery",
        accepted_inputs=("optional domain, audience, and environment filters",),
        outputs_to_inspect=("popular cases", "recommended entrypoints", "what to show non-method users", "practical value"),
        recommended_environments=("notebook", "python_script", "cli_batch"),
    ),
    ApiEntry(
        name="about / api_reference / scenario_guide / environment_matrix / workflow_recommendation / user_guide",
        category="built-in guidance",
        signature=(
            "about(format='markdown'); api_reference(format='markdown'); scenario_guide(domain=None, environment=None, scenario=None, format='markdown'); "
            "environment_matrix(format='markdown'); workflow_recommendation(domain=None, environment=None, scenario=None, format='markdown'); user_guide(format='markdown')"
        ),
        purpose="In-package documentation and onboarding helpers.",
        why_exists=(
            "Community tools need a discoverable explanation layer. These functions let users ask the package itself what it does, when to use each API, and which workflows fit their domain or environment."
        ),
        when_to_use="Use when onboarding a new lab, writing docs, teaching users, or generating scenario-specific guidance from Python or the CLI.",
        returns="Markdown/text/JSON guide content",
        accepted_inputs=("optional domain/environment filters",),
        outputs_to_inspect=("about", "API catalog", "scenario playbooks", "environment matrix", "workflow guide"),
        recommended_environments=("notebook", "python_script", "cli_batch"),
    ),
)


SCENARIOS: tuple[ScenarioSpec, ...] = (
    ScenarioSpec(
        key="fmri_resting_state",
        title="Resting-state or task fMRI cohort profiling",
        domains=("fmri",),
        environments=("notebook", "python_script", "neuro_stack", "ml_benchmark"),
        data_shape="subjects × time × ROI, ROI-wise tables, or xarray-like neuroimaging containers",
        typical_inputs=("FMRIInput", "xarray-like object", "3D NumPy array"),
        echotime_role=(
            "Acts as a dataset-card and structure-audit layer before graph modelling, connectome analyses, or benchmark comparison."
        ),
        best_entrypoints=("profile_dataset(FMRIInput(...))", "profile_dataset(xarray_like_obj)", "profile_dataset(array, domain='fmri', tr=...)"),
        outputs_to_inspect=(
            "coupling_networkedness",
            "heterogeneity",
            "regime_switching",
            "plugin_metrics['fmri_metrics']",
            "plugin_metrics['network_metrics']",
            "task_hints",
        ),
        what_you_can_do=(
            "Compare datasets or cohorts structurally before training models.",
            "Summarize how networked, heterogeneous, or low-frequency-dominated a dataset is.",
            "Export a dataset card for benchmark documentation or supplement material.",
        ),
        caveats=(
            "Provide TR whenever possible for Hz-aware metrics.",
            "echotime does not replace neuroimaging preprocessing or connectome estimation packages.",
        ),
    ),
    ScenarioSpec(
        key="eeg_recording_qc",
        title="EEG or electrophysiology recording triage",
        domains=("eeg",),
        environments=("notebook", "python_script", "neuro_stack", "ml_benchmark"),
        data_shape="time × channel arrays, subject × time × channel cohorts, or MNE-like objects",
        typical_inputs=("EEGInput", "MNE Raw/Epochs/Evoked-like object", "2D/3D arrays"),
        echotime_role="Provides a fast structural summary layer before decoding, spectral analysis, or representation learning.",
        best_entrypoints=("profile_dataset(EEGInput(...))", "profile_dataset(mne_like_obj)"),
        outputs_to_inspect=(
            "rhythmicity",
            "noise_contamination",
            "nonlinearity_chaoticity",
            "plugin_metrics['eeg_bandpower']",
            "reliability",
        ),
        what_you_can_do=(
            "Spot low-rhythmicity or high-noise recordings before downstream analysis.",
            "Compare cohorts by bandpower-heavy vs noise-heavy structure.",
            "Generate reproducible cards for datasets used in decoding benchmarks.",
        ),
        caveats=(
            "Sampling rate is important for EEG-specific proxies.",
            "The package profiles structure; it does not perform artifact rejection or source reconstruction.",
        ),
    ),
    ScenarioSpec(
        key="clinical_irregular_monitoring",
        title="Irregular clinical monitoring or sparse hospital telemetry",
        domains=("clinical",),
        environments=("notebook", "python_script", "pandas_pipeline", "cli_batch"),
        data_shape="subject-wise irregular observations, asynchronous channels, long hospital tables, or CSV/parquet extracts",
        typical_inputs=("IrregularTimeSeriesInput", "pandas DataFrame", "CSV/parquet path", "list of record dicts"),
        echotime_role="Audits observation irregularity, eventness, drift, and cohort heterogeneity before modelling or cohort QC.",
        best_entrypoints=(
            "profile_dataset(IrregularTimeSeriesInput(...), domain='clinical')",
            "profile_dataset(dataframe, domain='clinical')",
            "echotime cohort.parquet --input-mode table --domain clinical",
        ),
        outputs_to_inspect=(
            "sampling_irregularity",
            "drift_nonstationarity",
            "eventness_burstiness",
            "plugin_metrics['irregular_observation']",
            "reliability notes",
        ),
        what_you_can_do=(
            "Decide whether timestamp irregularity is a primary modelling concern.",
            "Document missingness and follow-up instability for cohort reports.",
            "Feed dataset cards into benchmarking or data-governance workflows.",
        ),
        caveats=(
            "For very sparse data, interpret frequency-aware metrics conservatively.",
            "echotime does not impute, resample, or fit clinical prediction models for you.",
        ),
    ),
    ScenarioSpec(
        key="wearable_longitudinal_cohort",
        title="Wearable or digital biomarker longitudinal cohort",
        domains=("wearable", "clinical"),
        environments=("notebook", "python_script", "pandas_pipeline", "ml_benchmark", "cli_batch"),
        data_shape="long tables with subject / visit / time / channel / value columns or wide wearable frames",
        typical_inputs=("pandas DataFrame", "parquet/CSV path", "list of records"),
        echotime_role="Profiles adherence, repeated-visit instability, subject fingerprintability, and cohort heterogeneity for longitudinal studies.",
        best_entrypoints=(
            "profile_dataset(dataframe, domain='wearable')",
            "echotime study.parquet --input-mode table --domain wearable --format card-markdown",
        ),
        outputs_to_inspect=(
            "sampling_irregularity",
            "heterogeneity",
            "plugin_metrics['longitudinal_metrics']",
            "task_hints",
            "dataset card exports",
        ),
        what_you_can_do=(
            "Understand whether your cohort is dominated by dropout, visit imbalance, or subject-specific structure.",
            "Decide whether leave-subject-out or leave-visit-out validation is more defensible.",
            "Generate methods-ready summaries for study documentation.",
        ),
        caveats=(
            "Parquet reading requires a parquet engine such as pyarrow at runtime.",
            "The package reports longitudinal structure; it does not replace biostatistical mixed-effects analysis.",
        ),
    ),
    ScenarioSpec(
        key="environmental_sensor_network",
        title="Environmental or industrial multichannel sensor datasets",
        domains=("generic",),
        environments=("notebook", "python_script", "pandas_pipeline", "ml_benchmark", "cli_batch"),
        data_shape="dense or mildly gappy multichannel series, station networks, or machine telemetry tables",
        typical_inputs=("2D/3D arrays", "pandas DataFrame", "xarray-like object"),
        echotime_role="Provides trend, rhythmicity, drift, coupling, and noise summaries before forecasting or anomaly pipelines.",
        best_entrypoints=("profile_dataset(array)", "profile_dataset(dataframe)", "profile_dataset(xarray_like_obj)"),
        outputs_to_inspect=(
            "trendness",
            "rhythmicity",
            "drift_nonstationarity",
            "coupling_networkedness",
            "task_hints",
        ),
        what_you_can_do=(
            "Compare stations, machines, or datasets structurally.",
            "Screen for seasonality-heavy vs drift-heavy problems.",
            "Produce dataset cards for shared forecasting benchmarks.",
        ),
        caveats=(
            "echotime does not replace forecasting model selection or domain simulators.",
            "If timestamps are absent, irregularity diagnostics are naturally weaker.",
        ),
    ),
    ScenarioSpec(
        key="event_stream_operations",
        title="Sparse event streams, alerts, clicks, or treatment logs",
        domains=("generic", "clinical"),
        environments=("notebook", "python_script", "pandas_pipeline", "cli_batch"),
        data_shape="timestamped event records with optional event type, channel, subject, and mark/value columns",
        typical_inputs=("EventStreamInput", "long tables", "JSON/JSONL/CSV records"),
        echotime_role="Quantifies burstiness, event diversity, and dataset-level event archetypes before point-process or event modelling.",
        best_entrypoints=("profile_dataset(EventStreamInput(...))", "profile_dataset(records_or_table)"),
        outputs_to_inspect=(
            "eventness_burstiness",
            "plugin_metrics['event_stream']",
            "sampling_irregularity",
            "archetypes",
        ),
        what_you_can_do=(
            "Differentiate bursty alarm streams from more regular event streams.",
            "Summarize whether event labels are diverse or dominated by one code.",
            "Create machine-readable cards for event benchmark datasets.",
        ),
        caveats=(
            "Sparse event streams are represented generically; detailed point-process inference remains out of scope.",
            "Interpret time-series axes together with event plugin metrics rather than in isolation.",
        ),
    ),
    ScenarioSpec(
        key="benchmark_dataset_card",
        title="Benchmark curation and dataset-card generation",
        domains=("generic", "fmri", "eeg", "clinical", "wearable"),
        environments=("python_script", "cli_batch", "ml_benchmark"),
        data_shape="any dataset that echotime can adapt",
        typical_inputs=("anything accepted by profile_dataset",),
        echotime_role="Acts as a repeatable structural profiler and card generator for dataset governance and benchmark transparency.",
        best_entrypoints=("profile_dataset(data).to_card_json()", "echotime data.npy --format card-json"),
        outputs_to_inspect=("card JSON", "card Markdown", "axes", "reliability", "ontology_schema"),
        what_you_can_do=(
            "Track structural coverage across benchmark suites.",
            "Attach cards to releases, papers, or internal registries.",
            "Compare new datasets against existing benchmark structure profiles.",
        ),
        caveats=(
            "A dataset card is descriptive, not a substitute for task-specific evaluation.",
            "Reliability scores should be reported alongside the axes.",
        ),
    ),
)


ENVIRONMENTS: tuple[EnvironmentSpec, ...] = (
    EnvironmentSpec(
        key="notebook",
        title="Jupyter or interactive notebook",
        best_for="Exploration, teaching, hypothesis generation, and profile inspection.",
        typical_inputs=("arrays", "DataFrames", "typed wrappers"),
        echotime_value="Lets you move from raw data to a readable structural profile in a few lines and inspect notes, cards, and reliability interactively.",
        usual_outputs=("profile.axes", "Markdown report", "dataset card", "API guide functions"),
        notes=(
            "Best environment for first contact with a new dataset.",
            "Combine with about(), api_reference(), and scenario_guide() to onboard collaborators.",
        ),
    ),
    EnvironmentSpec(
        key="python_script",
        title="Plain Python script or package pipeline",
        best_for="Reusable profiling steps in research codebases or internal libraries.",
        typical_inputs=("arrays", "typed wrappers", "tables", "custom adapted objects"),
        echotime_value="Makes structural profiling reproducible and scriptable for data intake, QC, or benchmark preparation.",
        usual_outputs=("JSON payloads", "card files", "profile.to_dict()"),
        notes=(
            "Good fit when you want deterministic artifact generation.",
            "The registry API is easiest to integrate from scripts.",
        ),
    ),
    EnvironmentSpec(
        key="cli_batch",
        title="CLI and shell batch jobs",
        best_for="Quick audits, CI checks, and dataset-card generation without writing Python glue.",
        typical_inputs=(".npy/.npz arrays", ".csv/.json/.jsonl/.parquet tables"),
        echotime_value="Turns profile generation into a shell-friendly step and now also exposes guide content from the command line.",
        usual_outputs=("stdout text", "Markdown report", "card JSON/Markdown", "guide documents"),
        notes=(
            "Useful for data release pipelines and benchmark registries.",
            "Parquet support depends on the runtime having a parquet engine installed.",
        ),
    ),
    EnvironmentSpec(
        key="pandas_pipeline",
        title="Pandas / parquet / tabular data pipeline",
        best_for="Clinical, wearable, and observational data already organized as long or wide tables.",
        typical_inputs=("DataFrame", "parquet path", "CSV/TSV/JSON/JSONL path", "record lists"),
        echotime_value="Keeps you in the same tabular ecosystem while adding structural profiling, longitudinal interpretation, and dataset cards.",
        usual_outputs=("profile axes", "longitudinal plugin metrics", "card exports"),
        notes=(
            "Ideal when your storage layer is already tabular.",
            "Longitudinal columns such as subject, visit, time, and channel unlock richer interpretation.",
        ),
    ),
    EnvironmentSpec(
        key="neuro_stack",
        title="Neuro stack (MNE-like / xarray-like / ROI arrays)",
        best_for="Neural time-series workflows that already use ecosystem-specific containers.",
        typical_inputs=("MNE-like objects", "xarray-like objects", "FMRIInput", "EEGInput"),
        echotime_value="Adds a structure-aware summary layer without forcing you to abandon domain-native containers.",
        usual_outputs=("domain-aware plugin metrics", "network summaries", "cards for publications/benchmarks"),
        notes=(
            "Use typed wrappers when you want explicit metadata such as TR or channel names.",
            "echotime complements, rather than replaces, domain packages.",
        ),
    ),
    EnvironmentSpec(
        key="ml_benchmark",
        title="ML benchmark or evaluation pipeline",
        best_for="Benchmark curation, dataset coverage analysis, and metadata generation for model comparisons.",
        typical_inputs=("any adapted dataset form",),
        echotime_value="Provides stable ontology axes, schema versioning, reliability summaries, and machine-readable cards that can travel with a benchmark suite.",
        usual_outputs=("card JSON", "schema export", "comparable axis vectors"),
        notes=(
            "Best environment when you need repeatable cards across many datasets.",
            "The package is descriptive infrastructure, not a benchmark runner.",
        ),
    ),
)


DOMAIN_AXIS_PRIORITIES: dict[str, tuple[str, ...]] = {
    "generic": ("predictability", "drift_nonstationarity", "trendness", "rhythmicity", "complexity"),
    "fmri": ("coupling_networkedness", "heterogeneity", "regime_switching", "drift_nonstationarity", "rhythmicity"),
    "eeg": ("rhythmicity", "noise_contamination", "nonlinearity_chaoticity", "complexity", "coupling_networkedness"),
    "clinical": ("sampling_irregularity", "drift_nonstationarity", "eventness_burstiness", "heterogeneity", "predictability"),
    "wearable": ("sampling_irregularity", "heterogeneity", "rhythmicity", "drift_nonstationarity", "predictability"),
}


def _normalize_domain(domain: str | None) -> str | None:
    if domain is None:
        return None
    value = domain.strip().lower()
    return value or None


def _normalize_environment(environment: str | None) -> str | None:
    if environment is None:
        return None
    value = environment.strip().lower().replace("-", "_").replace(" ", "_")
    return value or None


def _match_domain(supported: tuple[str, ...], domain: str | None) -> bool:
    if domain is None:
        return True
    if domain in supported:
        return True
    if "generic" in supported and domain == "generic":
        return True
    return False


def _match_environment(supported: tuple[str, ...], environment: str | None) -> bool:
    if environment is None:
        return True
    return environment in supported


def about_dict() -> dict[str, Any]:
    return {
        "package": PACKAGE_SUMMARY["name"],
        "schema_version": SCHEMA_VERSION,
        "tagline": PACKAGE_SUMMARY["tagline"],
        "one_sentence": PACKAGE_SUMMARY["one_sentence"],
        "what_it_is": PACKAGE_SUMMARY["what_it_is"],
        "what_it_is_not": PACKAGE_SUMMARY["what_it_is_not"],
        "who_it_is_for": PACKAGE_SUMMARY["who_it_is_for"],
        "core_outputs": list(PACKAGE_SUMMARY["core_outputs"]),
        "supported_input_families": list(PACKAGE_SUMMARY["supported_input_families"]),
        "main_question": PACKAGE_SUMMARY["main_question"],
        "ontology_axes": [
            {"name": axis, "description": AXIS_DESCRIPTIONS[axis]} for axis in AXIS_ORDER
        ],
    }


def api_reference_dict() -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in API_ENTRIES:
        grouped.setdefault(entry.category, []).append(asdict(entry))
    return {
        "package": PACKAGE_SUMMARY["name"],
        "schema_version": SCHEMA_VERSION,
        "categories": grouped,
    }


def scenario_guide_dict(
    *,
    domain: str | None = None,
    environment: str | None = None,
    scenario: str | None = None,
) -> dict[str, Any]:
    domain = _normalize_domain(domain)
    environment = _normalize_environment(environment)
    scenario = scenario.strip().lower() if scenario else None
    selected = []
    for spec in SCENARIOS:
        if scenario is not None and spec.key != scenario:
            continue
        if not _match_domain(spec.domains, domain):
            continue
        if not _match_environment(spec.environments, environment):
            continue
        selected.append(asdict(spec))
    return {
        "package": PACKAGE_SUMMARY["name"],
        "filters": {"domain": domain, "environment": environment, "scenario": scenario},
        "scenarios": selected,
    }


def environment_matrix_dict() -> dict[str, Any]:
    return {
        "package": PACKAGE_SUMMARY["name"],
        "environments": [asdict(env) for env in ENVIRONMENTS],
    }


def workflow_recommendation_dict(
    *,
    domain: str | None = None,
    environment: str | None = None,
    scenario: str | None = None,
) -> dict[str, Any]:
    domain = _normalize_domain(domain) or "generic"
    environment = _normalize_environment(environment) or "notebook"
    scenario_payload = scenario_guide_dict(domain=domain, environment=environment, scenario=scenario)
    selected = scenario_payload["scenarios"]
    if not selected:
        selected = scenario_guide_dict(domain=domain, environment=None, scenario=scenario)["scenarios"]
    if not selected:
        selected = scenario_guide_dict(domain=None, environment=environment, scenario=scenario)["scenarios"]
    if not selected:
        selected = scenario_guide_dict(domain=None, environment=None, scenario=scenario)["scenarios"][:3]

    priorities = list(DOMAIN_AXIS_PRIORITIES.get(domain, DOMAIN_AXIS_PRIORITIES["generic"]))

    input_advice = {
        "fmri": "Prefer FMRIInput or an xarray-like object with explicit TR, ROI names, and optional network labels.",
        "eeg": "Prefer EEGInput or an MNE-like object with sampling rate and channel names.",
        "clinical": "Prefer IrregularTimeSeriesInput or a long pandas table with subject/time/channel/value columns.",
        "wearable": "Prefer a long pandas/parquet table with subject, visit, time, channel, and value columns.",
        "generic": "Start with arrays or DataFrames; move to typed wrappers if semantic metadata matter.",
    }[domain]

    export_tip = {
        "notebook": "Use profile.to_markdown() or profile.to_card_markdown() while exploring interactively.",
        "python_script": "Persist profile.to_json() or profile.to_card_json() to reproducible artifacts.",
        "cli_batch": "Run the CLI with --format card-json or card-markdown inside a shell pipeline.",
        "pandas_pipeline": "Keep data in DataFrame/parquet form and generate card JSON beside your ETL outputs.",
        "neuro_stack": "Wrap domain objects or use native adaptors, then export cards for methods notes or benchmarks.",
        "ml_benchmark": "Store card JSON plus schema version next to benchmark metadata so datasets remain comparable.",
    }.get(environment, "Export both a human-readable report and a machine-readable card.")

    return {
        "package": PACKAGE_SUMMARY["name"],
        "domain": domain,
        "environment": environment,
        "recommended_input_setup": input_advice,
        "priority_axes": priorities,
        "recommended_steps": [
            "Organize the dataset in the most semantically faithful input form rather than stripping metadata too early.",
            "Run profile_dataset(...) with domain-specific metadata such as sampling_rate, TR, channel names, visit columns, or explicit timestamps whenever available.",
            "Inspect the priority axes together with reliability, notes, and domain/plugin metrics rather than reading any single score in isolation.",
            "Export a dataset card so the profile can travel into papers, benchmark registries, or internal data catalogs.",
            "Use task hints and reliability notes to guide model-family choice, validation design, and communication of caveats.",
        ],
        "recommended_scenarios": selected,
        "export_tip": export_tip,
    }


def docs_index_dict() -> dict[str, Any]:
    return {
        "package": PACKAGE_SUMMARY["name"],
        "available_guides": {
            "about": "Explain what EchoTime is for, what it outputs, and what it is not.",
            "api": "List the main public API, grouped by role, with purpose and rationale.",
            "scenarios": "Show domain/application playbooks and where echotime fits in each workflow.",
            "environments": "Show where the package works best: notebook, CLI, pandas pipeline, neuro stack, benchmark pipeline.",
            "workflow": "Return a domain/environment-specific onboarding workflow.",
            "user-guide": "Combine the major guide documents into one long-form handbook.",
            "cases": "Cross-disciplinary case gallery with popular time-series application areas.",
            "docs-index": "List the available guide documents.",
        },
        "filters": {
            "domain": ["generic", "fmri", "eeg", "clinical", "wearable"],
            "environment": [env.key for env in ENVIRONMENTS],
            "scenario": [spec.key for spec in SCENARIOS],
        },
    }


def _render_about_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# What is EchoTime?",
        "",
        f"**{payload['tagline']}**",
        "",
        payload["one_sentence"],
        "",
        "## What the package is",
        "",
        payload["what_it_is"],
        "",
        "## What the package is not",
        "",
        payload["what_it_is_not"],
        "",
        "## Who should use it",
        "",
        payload["who_it_is_for"],
        "",
        "## Core outputs",
        "",
    ]
    for item in payload["core_outputs"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Supported input families", ""])
    for item in payload["supported_input_families"]:
        lines.append(f"- {item}")
    lines.extend(["", "## The main question it answers", "", payload["main_question"], "", "## Ontology axes", "", "| axis | description |", "|---|---|"])
    for axis in payload["ontology_axes"]:
        lines.append(f"| {axis['name']} | {axis['description']} |")
    return "\n".join(lines)


def _render_api_markdown(payload: dict[str, Any]) -> str:
    lines = ["# EchoTime API reference", ""]
    for category, entries in payload["categories"].items():
        lines.extend([f"## {category}", ""])
        for entry in entries:
            lines.extend([
                f"### `{entry['name']}`",
                "",
                f"**Signature:** `{entry['signature']}`",
                "",
                f"**Purpose:** {entry['purpose']}",
                "",
                f"**Why this API exists:** {entry['why_exists']}",
                "",
                f"**When to use it:** {entry['when_to_use']}",
                "",
                f"**Returns:** {entry['returns']}",
                "",
                "**Accepted inputs / context:**",
                "",
            ])
            for item in entry["accepted_inputs"]:
                lines.append(f"- {item}")
            lines.extend(["", "**Inspect these outputs:**", ""])
            for item in entry["outputs_to_inspect"]:
                lines.append(f"- {item}")
            lines.extend(["", f"**Recommended environments:** {', '.join(entry['recommended_environments'])}", ""])
    return "\n".join(lines)


def _render_scenarios_markdown(payload: dict[str, Any]) -> str:
    lines = ["# EchoTime scenario guide", ""]
    filters = payload["filters"]
    active = {k: v for k, v in filters.items() if v is not None}
    if active:
        lines.append(f"**filters:** {active}")
        lines.append("")
    if not payload["scenarios"]:
        lines.append("No scenarios matched the requested filters.")
        return "\n".join(lines)
    for scenario in payload["scenarios"]:
        lines.extend([
            f"## {scenario['title']}",
            "",
            f"**scenario key:** `{scenario['key']}`  ",
            f"**domains:** {', '.join(scenario['domains'])}  ",
            f"**environments:** {', '.join(scenario['environments'])}",
            "",
            f"**Data shape:** {scenario['data_shape']}",
            "",
            "**Typical inputs:**",
            "",
        ])
        for item in scenario["typical_inputs"]:
            lines.append(f"- {item}")
        lines.extend(["", f"**Where EchoTime helps:** {scenario['echotime_role']}", "", "**Best entrypoints:**", ""])
        for item in scenario["best_entrypoints"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "**Outputs to inspect:**", ""])
        for item in scenario["outputs_to_inspect"]:
            lines.append(f"- {item}")
        lines.extend(["", "**What you can do with it:**", ""])
        for item in scenario["what_you_can_do"]:
            lines.append(f"- {item}")
        lines.extend(["", "**Caveats:**", ""])
        for item in scenario["caveats"]:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def _render_environments_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# EchoTime environment matrix",
        "",
        "| environment | title | best for | typical inputs | what echotime adds | usual outputs |",
        "|---|---|---|---|---|---|",
    ]
    for env in payload["environments"]:
        lines.append(
            f"| {env['key']} | {env['title']} | {env['best_for']} | {'; '.join(env['typical_inputs'])} | {env['echotime_value']} | {'; '.join(env['usual_outputs'])} |"
        )
    lines.extend(["", "## Notes by environment", ""])
    for env in payload["environments"]:
        lines.append(f"### {env['title']} (`{env['key']}`)")
        lines.append("")
        for note in env["notes"]:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)


def _render_workflow_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# EchoTime recommended workflow",
        "",
        f"**domain:** {payload['domain']}  ",
        f"**environment:** {payload['environment']}",
        "",
        f"**Recommended input setup:** {payload['recommended_input_setup']}",
        "",
        f"**Priority axes:** {', '.join(payload['priority_axes'])}",
        "",
        "## Suggested steps",
        "",
    ]
    for idx, step in enumerate(payload["recommended_steps"], start=1):
        lines.append(f"{idx}. {step}")
    lines.extend(["", f"**Export tip:** {payload['export_tip']}", "", "## Relevant scenarios", ""])
    for scenario in payload["recommended_scenarios"]:
        lines.append(f"### {scenario['title']}")
        lines.append("")
        lines.append(scenario["echotime_role"])
        lines.append("")
        lines.append("**Best entrypoints:**")
        lines.append("")
        for item in scenario["best_entrypoints"]:
            lines.append(f"- `{item}`")
        lines.append("")
    return "\n".join(lines)


def _render_docs_index_markdown(payload: dict[str, Any]) -> str:
    lines = ["# EchoTime documentation index", "", "## Available guides", ""]
    for key, value in payload["available_guides"].items():
        lines.append(f"- **{key}**: {value}")
    lines.extend(["", "## Available filters", ""])
    for key, values in payload["filters"].items():
        lines.append(f"- **{key}**: {', '.join(values)}")
    return "\n".join(lines)


def _render_text_from_markdown(text: str) -> str:
    return text


def _render(payload: dict[str, Any], *, topic: str, format: GuideFormat) -> str:
    if format == "json":
        return json.dumps(payload, indent=2)
    if topic == "about":
        markdown = _render_about_markdown(payload)
    elif topic == "api":
        markdown = _render_api_markdown(payload)
    elif topic == "scenarios":
        markdown = _render_scenarios_markdown(payload)
    elif topic == "environments":
        markdown = _render_environments_markdown(payload)
    elif topic == "workflow":
        markdown = _render_workflow_markdown(payload)
    elif topic == "docs-index":
        markdown = _render_docs_index_markdown(payload)
    else:
        raise ValueError(f"Unknown guide topic: {topic}")
    if format == "text":
        return _render_text_from_markdown(markdown)
    return markdown


def about(*, format: GuideFormat = "markdown") -> str:
    """Return a package-level introduction.

    This is the most direct answer to "what is echotime for?" and "when should I use it?".
    """

    return _render(about_dict(), topic="about", format=format)


def api_reference(*, format: GuideFormat = "markdown") -> str:
    """Return the public API handbook grouped by role."""

    return _render(api_reference_dict(), topic="api", format=format)


def scenario_guide(
    *,
    domain: str | None = None,
    environment: str | None = None,
    scenario: str | None = None,
    format: GuideFormat = "markdown",
) -> str:
    """Return scenario playbooks filtered by domain, environment, or scenario key."""

    payload = scenario_guide_dict(domain=domain, environment=environment, scenario=scenario)
    return _render(payload, topic="scenarios", format=format)


def environment_matrix(*, format: GuideFormat = "markdown") -> str:
    """Return a guide to the environments where echotime fits naturally."""

    return _render(environment_matrix_dict(), topic="environments", format=format)


def workflow_recommendation(
    *,
    domain: str | None = None,
    environment: str | None = None,
    scenario: str | None = None,
    format: GuideFormat = "markdown",
) -> str:
    """Return a domain- and environment-aware onboarding workflow."""

    payload = workflow_recommendation_dict(domain=domain, environment=environment, scenario=scenario)
    return _render(payload, topic="workflow", format=format)


def docs_index(*, format: GuideFormat = "markdown") -> str:
    """Return the list of built-in guide documents and available filters."""

    return _render(docs_index_dict(), topic="docs-index", format=format)


def user_guide(*, format: GuideFormat = "markdown") -> str:
    """Return a long-form combined handbook for new users."""

    payloads = [
        about(format="markdown"),
        api_reference(format="markdown"),
        environment_matrix(format="markdown"),
        scenario_guide(format="markdown"),
        workflow_recommendation(format="markdown"),
        __import__("echotime.gallery", fromlist=["case_gallery"]).case_gallery(format="markdown"),
    ]
    combined = "\n\n".join(payloads)
    if format == "markdown":
        return combined
    if format == "text":
        return combined
    return json.dumps(
        {
            "about": about_dict(),
            "api": api_reference_dict(),
            "environments": environment_matrix_dict(),
            "scenarios": scenario_guide_dict(),
            "workflow": workflow_recommendation_dict(),
            "cases": __import__("echotime.gallery", fromlist=["case_gallery_dict"]).case_gallery_dict(),
        },
        indent=2,
    )

# --- v0.8 additions: similarity guidance, hot cases, and homepage support ---

PACKAGE_SUMMARY["core_outputs"] = PACKAGE_SUMMARY["core_outputs"] + (
    "similarity report",
    "rolling similarity diagnostics",
    "hot case gallery",
    "project homepage HTML",
)

EXTRA_API_ENTRIES: tuple[ApiEntry, ...] = (
    ApiEntry(
        name="compare_series",
        category="similarity analysis",
        signature="compare_series(left, right, *, left_timestamps=None, right_timestamps=None, left_name='left', right_name='right', n_points=256) -> SimilarityReport",
        purpose="Compare two raw trajectories using shape, DTW, trend, derivative, and spectral similarity.",
        why_exists=(
            "Cross-disciplinary users often want to say 'does this curve look like that one?' before they want a full forecasting or classification model. This API gives that question a structured answer."
        ),
        when_to_use="Use for GitHub star growth, crypto or commodity price windows, launch-week traffic curves, and any pair of trajectories where shape matters.",
        returns="SimilarityReport",
        accepted_inputs=("univariate arrays", "multichannel arrays", "optional timestamps"),
        outputs_to_inspect=("reference_metrics", "component_mean", "component_scores", "to_summary_card_markdown()", "to_narrative_report()"),
        recommended_environments=("notebook", "python_script", "cli_batch", "pandas_pipeline"),
    ),
    ApiEntry(
        name="compare_profiles",
        category="similarity analysis",
        signature="compare_profiles(left, right, *, left_name='left profile', right_name='right profile') -> SimilarityReport",
        purpose="Compare two echotime profiles or raw datasets at the ontology-axis level.",
        why_exists=(
            "Sometimes raw units and scales differ too much for direct shape matching, but the datasets are still structurally analogous. Profile similarity answers that higher-level question."
        ),
        when_to_use="Use for cross-domain analogies, benchmark curation, or when you want to explain that two datasets are 'the same kind of temporal problem'.",
        returns="SimilarityReport",
        accepted_inputs=("DatasetProfile", "SeriesProfile", "or raw inputs accepted by profile_dataset"),
        outputs_to_inspect=("overall_axis_similarity", "dynamic_similarity", "multivariate_similarity", "metadata['axis_similarity']"),
        recommended_environments=("notebook", "python_script", "ml_benchmark", "pandas_pipeline"),
    ),
    ApiEntry(
        name="rolling_similarity",
        category="similarity analysis",
        signature="rolling_similarity(left, right, *, window, step=1, left_timestamps=None, right_timestamps=None, n_points=128) -> list[dict]",
        purpose="Track how similarity changes over aligned rolling windows.",
        why_exists=(
            "Many high-traffic stories are regime stories: BTC and gold are similar in some windows but not others, and launch-week growth patterns drift over time."
        ),
        when_to_use="Use for windowed market comparisons, launch tracking, and changing relationships over time.",
        returns="list of per-window similarity summaries",
        accepted_inputs=("pair of arrays or multichannel arrays", "window length", "optional timestamps"),
        outputs_to_inspect=("component_mean", "pearson_r", "shape_similarity", "trend_similarity", "spectral_similarity"),
        recommended_environments=("notebook", "python_script", "pandas_pipeline"),
    ),
    ApiEntry(
        name="ncc_sequence / max_ncc / best_shift / sbd / independent_max_ncc / independent_sbd / acf_distance / periodogram_distance / trend_distance / ordinal_pattern_js_distance / linear_trend_model_distance / lcss_similarity / lcss_distance / edr_distance / erp_distance / twed_distance",
        category="similarity analysis",
        signature=(
            "ncc_sequence(x, y, *, normalize=True) -> tuple[np.ndarray, np.ndarray]; "
            "max_ncc(...) -> float; best_shift(...) -> int; sbd(...) -> float; "
            "independent_max_ncc(...) -> float; independent_sbd(...) -> float; "
            "acf_distance(x, y, *, max_lag=10) -> float; "
            "periodogram_distance(x, y, *, n_coeffs=32) -> float; "
            "trend_distance(x, y) -> float; "
            "ordinal_pattern_js_distance(x, y, *, order=3, delay=1) -> float; "
            "linear_trend_model_distance(x, y) -> float; "
            "lcss_similarity(x, y, *, epsilon=1.0, window=None, mode='exact') -> float; "
            "lcss_distance(x, y, *, epsilon=1.0, window=None, mode='exact') -> float; "
            "edr_distance(x, y, *, epsilon=1.0, normalized=True, window=None, mode='exact') -> float; "
            "erp_distance(x, y, *, gap_value=0.0, window=None, mode='exact') -> float; "
            "twed_distance(x, y, *, lambda_=1.0, nu=0.001, t_x=None, t_y=None, window=None, mode='exact') -> float"
        ),
        purpose="Expose the extracted low-level similarity primitives directly when you need one explicit metric instead of a report bundle, including a fast screening path for the elastic distances.",
        why_exists=(
            "EchoTime's main surface is intentionally report-first, but advanced users still need direct access to shift-aware, rhythm-aware, and elastic distances for retrieval, thresholding, and custom pipelines."
        ),
        when_to_use="Use when you already know which similarity family you need and want a scalar score or lag estimate to plug into downstream logic; use `mode='fast'` for shortlist screening and `mode='exact'` for final reporting.",
        returns="NumPy arrays, scalar similarities, scalar distances, or a best-lag integer depending on the function",
        accepted_inputs=(
            "1D arrays",
            "2D multichannel arrays",
            "optional timestamps for TWED",
            "optional gap, tolerance, or band-width hyperparameters for elastic methods",
            "`mode='fast'` for shortlist screening, `mode='exact'` for final scoring",
        ),
        outputs_to_inspect=(
            "the returned scalar score or distance",
            "the lag array from ncc_sequence",
            "best_shift for lead-lag interpretation",
        ),
        recommended_environments=("notebook", "python_script", "ml_benchmark", "pandas_pipeline"),
    ),
    ApiEntry(
        name="hot_case_gallery / similarity_playbook / project_homepage_html / project_playground_html",
        category="built-in guidance",
        signature="hot_case_gallery(...); similarity_playbook(...); project_homepage_html(version='0.17.0'); project_playground_html(version='0.17.0')",
        purpose="Provide shareable, high-attention case ideas plus a static project-homepage starting point.",
        why_exists=(
            "Community adoption grows faster when the package already knows how to explain itself through timely examples and a reusable project page."
        ),
        when_to_use="Use when you want demos that can travel on social, in blog posts, on GitHub Pages, or in onboarding decks.",
        returns="Markdown/JSON guides and a self-contained HTML string",
        accepted_inputs=("optional audience/window filters",),
        outputs_to_inspect=("hot cases", "similarity guidance", "homepage HTML"),
        recommended_environments=("python_script", "cli_batch", "notebook"),
    ),
)

API_ENTRIES = API_ENTRIES + EXTRA_API_ENTRIES


def docs_index_dict() -> dict[str, Any]:  # type: ignore[override]
    return {
        "package": PACKAGE_SUMMARY["name"],
        "available_guides": {
            "about": "Explain what EchoTime is for, what it outputs, and what it is not.",
            "api": "List the main public API, grouped by role, with purpose and rationale.",
            "scenarios": "Show domain/application playbooks and where echotime fits in each workflow.",
            "environments": "Show where the package works best: notebook, CLI, pandas pipeline, neuro stack, benchmark pipeline.",
            "workflow": "Return a domain/environment-specific onboarding workflow.",
            "user-guide": "Combine the major guide documents into one long-form handbook.",
            "cases": "Cross-disciplinary case gallery with popular time-series application areas.",
            "hot-cases": "High-attention, shareable cases for the next 90 days.",
            "similarity": "How to use echotime for raw-series and structural similarity analysis.",
            "docs-index": "List the available guide documents.",
        },
        "filters": {
            "domain": ["generic", "fmri", "eeg", "clinical", "wearable", "traffic", "product", "energy"],
            "environment": [env.key for env in ENVIRONMENTS],
            "scenario": [spec.key for spec in SCENARIOS],
        },
    }


def hot_cases(*, format: GuideFormat = "markdown") -> str:
    """Return the high-attention case gallery for demos and public-facing examples."""

    return __import__("echotime.hotcases", fromlist=["hot_case_gallery"]).hot_case_gallery(format=format)


def similarity_guide(*, format: GuideFormat = "markdown") -> str:
    """Return the built-in guide explaining echotime similarity analysis."""

    return __import__("echotime.hotcases", fromlist=["similarity_playbook"]).similarity_playbook(format=format)


def user_guide(*, format: GuideFormat = "markdown") -> str:  # type: ignore[override]
    """Return a long-form combined handbook for new users, including similarity and hot cases."""

    payloads = [
        about(format="markdown"),
        api_reference(format="markdown"),
        environment_matrix(format="markdown"),
        scenario_guide(format="markdown"),
        workflow_recommendation(format="markdown"),
        __import__("echotime.hotcases", fromlist=["similarity_playbook"]).similarity_playbook(format="markdown"),
        __import__("echotime.gallery", fromlist=["case_gallery"]).case_gallery(format="markdown"),
        __import__("echotime.hotcases", fromlist=["hot_case_gallery"]).hot_case_gallery(format="markdown"),
    ]
    combined = "\n\n".join(payloads)
    if format == "markdown":
        return combined
    if format == "text":
        return combined
    return json.dumps(
        {
            "about": about_dict(),
            "api": api_reference_dict(),
            "environments": environment_matrix_dict(),
            "scenarios": scenario_guide_dict(),
            "workflow": workflow_recommendation_dict(),
            "similarity": __import__("echotime.hotcases", fromlist=["similarity_playbook_dict"]).similarity_playbook_dict(),
            "cases": __import__("echotime.gallery", fromlist=["case_gallery_dict"]).case_gallery_dict(),
            "hot_cases": __import__("echotime.hotcases", fromlist=["hot_case_gallery_dict"]).hot_case_gallery_dict(),
        },
        indent=2,
    )

# --- v0.9 additions: agent-driving and docs-homepage positioning ---

PACKAGE_SUMMARY["core_outputs"] = PACKAGE_SUMMARY["core_outputs"] + (
    "agent-driven execution plan",
    "compact agent context bundle",
)

EXTRA_API_ENTRIES_V09: tuple[ApiEntry, ...] = (
    ApiEntry(
        name="AgentDriver / agent_drive / agent_context",
        category="agent driving",
        signature=(
            "AgentDriver(goal='understand_dataset', budget='lean|balanced|deep', ...); "
            "agent_drive(data, reference=None, goal=..., budget=...); "
            "agent_context(profile_or_similarity_report, budget='lean')"
        ),
        purpose="Let an agent or application choose the cheapest useful EchoTime workflow and export a compact context bundle.",
        why_exists=(
            "LLM agents often waste tokens by running too many analyses and by carrying oversized intermediate reports. This API chooses a small workflow first, stops early when the signal is already clear, and compresses the result into a reusable context payload."
        ),
        when_to_use="Use when echotime sits inside an agent loop, a notebook assistant, a retrieval pipeline, or a batch report generator that needs compact summaries.",
        returns="AgentDriveResult or compact context dict/markdown/json",
        accepted_inputs=(
            "the same raw inputs accepted by profile_dataset or compare_series",
            "optional reference trajectory for comparison goals",
            "a goal string that explains what the agent is trying to solve",
        ),
        outputs_to_inspect=(
            "result.steps",
            "result.compact_context",
            "result.token_saving_rationale",
            "result.to_context_markdown()",
        ),
        recommended_environments=("notebook", "python_script", "cli_batch", "pandas_pipeline", "ml_benchmark"),
    ),
)

API_ENTRIES = API_ENTRIES + EXTRA_API_ENTRIES_V09


def docs_index_dict() -> dict[str, Any]:  # type: ignore[override]
    return {
        "package": PACKAGE_SUMMARY["name"],
        "available_guides": {
            "about": "Explain what EchoTime is for, what it outputs, and what it is not.",
            "api": "List the main public API, grouped by role, with purpose and rationale.",
            "scenarios": "Show domain/application playbooks and where echotime fits in each workflow.",
            "environments": "Show where the package works best: notebook, CLI, pandas pipeline, neuro stack, benchmark pipeline.",
            "workflow": "Return a domain/environment-specific onboarding workflow.",
            "user-guide": "Combine the major guide documents into one long-form handbook.",
            "cases": "Cross-disciplinary case gallery with popular time-series application areas.",
            "hot-cases": "High-attention, shareable cases for the next 90 days.",
            "similarity": "How to use echotime for raw-series and structural similarity analysis.",
            "agent-driving": "How to use echotime inside an agent loop while spending fewer tokens.",
            "homepage": "Render the static project homepage HTML.",
            "docs-index": "List the available guide documents.",
        },
        "filters": {
            "domain": ["generic", "fmri", "eeg", "clinical", "wearable", "traffic", "product", "energy"],
            "environment": [env.key for env in ENVIRONMENTS],
            "scenario": [spec.key for spec in SCENARIOS],
        },
    }


def agent_driving(*, format: GuideFormat = "markdown") -> str:
    """Return the guide explaining echotime's agent-driving layer."""

    return __import__("echotime.agent", fromlist=["agent_driving_guide"]).agent_driving_guide(format=format)


def user_guide(*, format: GuideFormat = "markdown") -> str:  # type: ignore[override]
    """Return a long-form combined handbook for new users, including similarity, agent driving, and hot cases."""

    payloads = [
        about(format="markdown"),
        api_reference(format="markdown"),
        environment_matrix(format="markdown"),
        scenario_guide(format="markdown"),
        workflow_recommendation(format="markdown"),
        __import__("echotime.hotcases", fromlist=["similarity_playbook"]).similarity_playbook(format="markdown"),
        __import__("echotime.agent", fromlist=["agent_driving_guide"]).agent_driving_guide(format="markdown"),
        __import__("echotime.gallery", fromlist=["case_gallery"]).case_gallery(format="markdown"),
        __import__("echotime.hotcases", fromlist=["hot_case_gallery"]).hot_case_gallery(format="markdown"),
    ]
    combined = "\n\n".join(payloads)
    if format == "markdown":
        return combined
    if format == "text":
        return combined
    return json.dumps(
        {
            "about": about_dict(),
            "api": api_reference_dict(),
            "environments": environment_matrix_dict(),
            "scenarios": scenario_guide_dict(),
            "workflow": workflow_recommendation_dict(),
            "similarity": __import__("echotime.hotcases", fromlist=["similarity_playbook_dict"]).similarity_playbook_dict(),
            "agent_driving": __import__("echotime.agent", fromlist=["agent_driving_guide_dict"]).agent_driving_guide_dict(),
            "cases": __import__("echotime.gallery", fromlist=["case_gallery_dict"]).case_gallery_dict(),
            "hot_cases": __import__("echotime.hotcases", fromlist=["hot_case_gallery_dict"]).hot_case_gallery_dict(),
        },
        indent=2,
    )
