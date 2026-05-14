import json
import os
import tempfile
import subprocess
import sys
from pathlib import Path

import numpy as np

from echotime import (
    EEGInput,
    EventStreamInput,
    FMRIInput,
    IrregularSubjectInput,
    IrregularTimeSeriesInput,
    SCHEMA_VERSION,
    about,
    api_reference,
    case_gallery,
    compare_profiles,
    compare_series,
    hot_case_gallery,
    project_homepage_html,
    project_pages_bundle,
    project_playground_html,
    rolling_similarity,
    similarity_playbook,
    AgentDriver,
    agent_context,
    agent_drive,
    agent_driving_guide,
    clear_custom_extensions,
    docs_index,
    ecosystem_positioning,
    coverage_matrix,
    agent_manifest,
    tooling_router,
    github_readme,
    explain_dataset,
    explain_similarity,
    list_starter_datasets,
    starter_dataset,
    write_starter_dataset,
    ts_compare,
    ts_profile,
    ts_route,
    tool_schemas,
    zero_install_guide,
    pages_deploy_guide,
    integration_templates_guide,
    case_studies_guide,
    compare_from_text,
    demo_server_html,
    environment_matrix,
    live_demo_guide,
    parse_numeric_text,
    profile_from_text,
    project_api_reference_html,
    project_docs_home_html,
    project_docs_pages,
    project_demo_manifest,
    project_getting_started_html,
    project_tutorials_html,
    profile_dataset,
    register_plugin,
    scenario_guide,
    schema_dict,
    user_guide,
    routing_contract_guide,
    workflow_recommendation,
)
from echotime.registry import PluginResult


def teardown_function(function) -> None:  # noqa: ARG001
    clear_custom_extensions()


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else src_path
    return env



def test_sine_more_rhythmic_and_predictable_than_noise() -> None:
    rng = np.random.default_rng(42)
    t = np.linspace(0, 20 * np.pi, 512)
    sine = np.sin(t) + 0.05 * rng.normal(size=t.size)
    noise = rng.normal(size=t.size)

    sine_profile = profile_dataset(sine)
    noise_profile = profile_dataset(noise)

    assert sine_profile.axes["rhythmicity"] > noise_profile.axes["rhythmicity"]
    assert sine_profile.axes["predictability"] > noise_profile.axes["predictability"]


def test_multivariate_coupling_detects_correlated_channels() -> None:
    rng = np.random.default_rng(0)
    t = np.linspace(0, 10 * np.pi, 400)
    base = np.sin(t)
    X = np.column_stack([
        base,
        0.9 * base + 0.1 * rng.normal(size=t.size),
        0.7 * np.roll(base, 2) + 0.2 * rng.normal(size=t.size),
    ])
    profile = profile_dataset(X)
    assert profile.axes["coupling_networkedness"] > 0.45
    assert "network_metrics" in profile.plugin_metrics


def test_irregular_timestamps_raise_sampling_irregularity() -> None:
    rng = np.random.default_rng(1)
    x = np.sin(np.linspace(0, 8 * np.pi, 256))
    regular_t = np.arange(x.size)
    irregular_t = np.cumsum(rng.uniform(0.4, 1.6, size=x.size))

    regular_profile = profile_dataset(x, timestamps=regular_t)
    irregular_profile = profile_dataset(x, timestamps=irregular_t)

    assert irregular_profile.axes["sampling_irregularity"] > regular_profile.axes["sampling_irregularity"]


def test_cohort_heterogeneity_detects_subject_differences() -> None:
    rng = np.random.default_rng(7)
    t = np.linspace(0, 12 * np.pi, 300)
    s1 = np.sin(t)
    s2 = rng.normal(size=t.size)
    cohort = np.stack([s1[:, None], s2[:, None]], axis=0)
    profile = profile_dataset(cohort)
    assert profile.axes["heterogeneity"] > 0.15


def test_fmri_input_exposes_domain_metrics() -> None:
    rng = np.random.default_rng(11)
    t = np.linspace(0, 6 * np.pi, 240)
    subject_1 = np.column_stack([
        np.sin(t),
        0.9 * np.sin(t + 0.1),
        -0.5 * np.sin(t) + 0.1 * rng.normal(size=t.size),
    ])
    subject_2 = np.column_stack([
        np.sin(t) + 0.05 * rng.normal(size=t.size),
        0.85 * np.sin(t + 0.1),
        -0.45 * np.sin(t) + 0.1 * rng.normal(size=t.size),
    ])

    fmri = FMRIInput(
        values=np.stack([subject_1, subject_2], axis=0),
        tr=2.0,
        roi_names=["A", "B", "C"],
        network_labels=["DMN", "DMN", "SAL"],
    )
    profile = profile_dataset(fmri)

    assert profile.metadata["domain"] == "fmri"
    assert "fmri_metrics" in profile.plugin_metrics
    assert "fmri_low_frequency_ratio" in profile.plugin_metrics["fmri_metrics"]


def test_eeg_input_exposes_bandpower_metrics() -> None:
    fs = 128.0
    t = np.arange(0, 8, 1 / fs)
    alpha = np.sin(2 * np.pi * 10 * t)
    theta = 0.4 * np.sin(2 * np.pi * 6 * t)
    X = np.column_stack([alpha + theta, 0.8 * alpha])

    profile = profile_dataset(EEGInput(values=X, sampling_rate=fs, channel_names=["C3", "C4"]))

    assert profile.metadata["domain"] == "eeg"
    assert "eeg_bandpower" in profile.plugin_metrics
    assert profile.plugin_metrics["eeg_bandpower"]["eeg_alpha_ratio"] > profile.plugin_metrics["eeg_bandpower"]["eeg_delta_ratio"]


def test_dataset_card_json_contains_schema_and_reliability() -> None:
    x = np.sin(np.linspace(0, 8 * np.pi, 128))
    profile = profile_dataset(x)
    payload = json.loads(profile.to_card_json())
    assert payload["schema_version"] == SCHEMA_VERSION
    assert "axes" in payload
    assert "ontology_schema" in payload
    assert "reliability" in payload


def test_custom_plugin_registration() -> None:
    class DemoPlugin:
        name = "demo_plugin"

        def applies(self, normalized, context):  # noqa: ANN001, D401
            return True

        def compute(self, normalized, context):  # noqa: ANN001, D401
            return PluginResult(metrics={"demo_metric": 0.75})

    register_plugin(DemoPlugin())
    profile = profile_dataset(np.sin(np.linspace(0, 4 * np.pi, 128)))
    assert profile.plugin_metrics["demo_plugin"]["demo_metric"] == 0.75


def test_reliability_and_bootstrap_are_exposed() -> None:
    rng = np.random.default_rng(22)
    t = np.linspace(0, 10 * np.pi, 300)
    cohort = np.stack([
        np.column_stack([np.sin(t), np.sin(t + 0.1)]),
        np.column_stack([np.sin(t) + 0.05 * rng.normal(size=t.size), np.sin(t + 0.2)]),
        np.column_stack([0.8 * np.sin(t) + 0.05 * rng.normal(size=t.size), 0.9 * np.sin(t + 0.3)]),
    ])
    profile = profile_dataset(cohort, bootstrap=24, random_state=0)
    reliability = profile.reliability
    assert reliability["overall_score"] > 0.0
    assert reliability["axes"]["predictability"]["ci_low"] is not None
    assert reliability["axes"]["predictability"]["ci_high"] is not None


def test_schema_export_contains_subdimensions() -> None:
    payload = schema_dict()
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["axes"]
    assert payload["axes"][0]["subdimensions"]


def test_mne_like_object_is_adapted_natively() -> None:
    class FakeRaw:
        def __init__(self, data, sfreq, ch_names):
            self._data = data
            self.info = {"sfreq": sfreq, "ch_names": ch_names}
            self.ch_names = ch_names
            self.times = np.arange(data.shape[1]) / sfreq

        def get_data(self):
            return self._data

    fs = 128.0
    t = np.arange(0, 5, 1 / fs)
    data = np.vstack([
        np.sin(2 * np.pi * 10 * t),
        np.sin(2 * np.pi * 10 * t + 0.2),
    ])
    raw = FakeRaw(data, sfreq=fs, ch_names=["C3", "C4"])
    profile = profile_dataset(raw)
    assert profile.metadata["native_adaptor"] == "mne"
    assert profile.metadata["sampling_rate"] == fs
    assert profile.metadata["domain"] == "eeg"


def test_xarray_like_object_is_adapted_natively() -> None:
    class FakeCoord:
        def __init__(self, values):
            self.values = np.asarray(values)

    class FakeDataArray:
        def __init__(self, values):
            self.values = values
            self.dims = ("subject", "time", "channel")
            self.coords = {
                "time": FakeCoord(np.arange(values.shape[1])),
                "channel": FakeCoord(["A", "B"]),
                "subject": FakeCoord(["s1", "s2"]),
            }

    t = np.linspace(0, 4 * np.pi, 200)
    values = np.stack([
        np.column_stack([np.sin(t), np.cos(t)]),
        np.column_stack([np.sin(t + 0.1), np.cos(t + 0.1)]),
    ], axis=0)
    data = FakeDataArray(values)
    profile = profile_dataset(data)
    assert profile.metadata["native_adaptor"] == "xarray"
    assert profile.metadata["subject_ids"] == ["s1", "s2"]
    assert profile.metadata["channel_labels"] == ["A", "B"]


def test_irregular_input_adaptor_exposes_irregular_plugins() -> None:
    t1 = np.array([0.0, 0.8, 1.7, 3.3, 4.1, 7.9, 8.2, 10.0])
    v1 = np.sin(t1)
    t2 = np.array([0.2, 1.1, 2.1, 2.8, 5.5, 6.0, 9.1])
    v2 = np.cos(t2)
    subject = IrregularSubjectInput(values=[v1, v2], timestamps=[t1, t2], channel_names=["hr", "spo2"])
    profile = profile_dataset(IrregularTimeSeriesInput(subjects=[subject], channel_names=["hr", "spo2"], domain="generic"))

    assert profile.metadata["observation_mode"] == "irregular"
    assert profile.plugin_metrics["irregular_observation"]["channel_asynchrony"] > 0.2
    assert profile.axes["sampling_irregularity"] > 0.1


def test_event_stream_input_exposes_event_metrics_and_archetype() -> None:
    timestamps = np.array([0.0, 0.3, 0.31, 1.5, 4.2, 4.21, 4.22, 9.0, 9.5, 12.0])
    channels = np.array(["med", "alarm", "alarm", "lab", "alarm", "alarm", "med", "lab", "med", "alarm"], dtype=object)
    values = np.array([1, 1, 1, 2, 1, 1, 1, 2, 1, 1], dtype=float)
    profile = profile_dataset(EventStreamInput(timestamps=timestamps, channels=channels, values=values, domain="generic"))

    assert profile.metadata["observation_mode"] == "event_stream"
    assert "event_stream" in profile.plugin_metrics
    assert profile.plugin_metrics["event_stream"]["event_interval_burstiness"] > 0.3
    assert "event_stream" in profile.archetypes


def test_long_table_records_are_adapted_natively() -> None:
    records = [
        {"timestamp": 0.0, "value": 1.0, "channel": "A", "subject": "s1", "event_type": "x"},
        {"timestamp": 0.2, "value": 1.0, "channel": "B", "subject": "s1", "event_type": "y"},
        {"timestamp": 0.8, "value": 2.0, "channel": "A", "subject": "s2", "event_type": "x"},
        {"timestamp": 1.0, "value": 1.0, "channel": "B", "subject": "s2", "event_type": "z"},
    ]
    profile = profile_dataset(records)
    assert profile.metadata["native_adaptor"] == "record_table"
    assert profile.metadata["observation_mode"] == "event_stream"
    assert profile.metadata["n_subjects"] == 2


def test_reliability_mentions_irregular_inputs() -> None:
    t1 = np.array([0.0, 1.0, 3.0, 6.0, 10.0, 15.0])
    v1 = np.sin(t1)
    profile = profile_dataset(IrregularTimeSeriesInput(subjects=IrregularSubjectInput(values=v1, timestamps=t1)))
    notes = " ".join(profile.reliability["notes"]).lower()
    assert "irregular" in notes


def test_cli_handles_table_mode(tmp_path: Path) -> None:
    input_path = tmp_path / "events.csv"
    input_path.write_text(
        "timestamp,value,channel,subject,event_type\n0.0,1.0,A,s1,x\n0.4,1.0,B,s1,y\n1.0,2.0,A,s2,x\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "echotime.cli", str(input_path), "--input-mode", "table", "--format", "json"],
        check=True,
        capture_output=True,
        text=True,
        env=_subprocess_env(),
    )
    payload = json.loads(result.stdout)
    assert payload["metadata"]["observation_mode"] == "event_stream"


def test_irregular_lomb_scargle_support_improves_frequency_awareness() -> None:
    rng = np.random.default_rng(123)
    timestamps = np.cumsum(rng.uniform(0.5, 1.8, size=512))
    sine = np.sin(2 * np.pi * 0.07 * timestamps)
    noise = rng.normal(size=timestamps.size)

    sine_profile = profile_dataset(sine, timestamps=timestamps)
    noise_profile = profile_dataset(noise, timestamps=timestamps)

    assert sine_profile.metrics["irregular_spectral_support"] > 0.9
    assert sine_profile.axes["rhythmicity"] > noise_profile.axes["rhythmicity"]


def test_pandas_dataframe_adaptor_handles_wide_native_frames() -> None:
    try:
        import pandas as pd
    except Exception:  # pragma: no cover
        return

    t = np.linspace(0, 6 * np.pi, 256)
    df = pd.DataFrame(
        {
            "hr": np.sin(t),
            "resp": np.cos(t),
        },
        index=pd.date_range("2025-01-01", periods=t.size, freq="h"),
    )
    profile = profile_dataset(df)

    assert profile.metadata["native_adaptor"] == "pandas"
    assert profile.metadata["channel_labels"] == ["hr", "resp"]


def test_pandas_longitudinal_frame_exposes_longitudinal_metrics() -> None:
    try:
        import pandas as pd
    except Exception:  # pragma: no cover
        return

    rows = []
    for patient, phase_shift in [("p1", 0.0), ("p2", 0.5)]:
        for visit_id, anchor in [("v1", 0.0), ("v2", 30.0), ("v3", 90.0)]:
            local_t = np.linspace(0, 6, 24)
            rows.append(pd.DataFrame({
                "patient": patient,
                "visit": visit_id,
                "time": anchor + local_t,
                "hr": np.sin(local_t + phase_shift),
                "steps": np.cos(local_t + phase_shift) + 0.1 * (visit_id == "v3"),
                "device": "watchA" if patient == "p1" else "watchB",
            }))
    df = pd.concat(rows, ignore_index=True)
    profile = profile_dataset(df, domain="wearable")

    assert profile.metadata["native_adaptor"] == "pandas"
    assert profile.metadata["longitudinal_mode"] is True
    assert profile.plugin_metrics["longitudinal_metrics"]["mean_visits_per_subject"] >= 3.0
    assert "longitudinal_cohort" in profile.archetypes


def test_parquet_path_adaptor_uses_pandas_reader() -> None:
    try:
        import pandas as pd
    except Exception:  # pragma: no cover
        return

    frame = pd.DataFrame({
        "timestamp": [0.0, 1.0, 2.0, 3.0],
        "value": [1.0, 2.0, 1.5, 2.5],
        "subject": ["s1", "s1", "s2", "s2"],
        "channel": ["hr", "hr", "hr", "hr"],
    })

    original = pd.read_parquet
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "demo.parquet"
        path.write_bytes(b"PAR1")
        pd.read_parquet = lambda *args, **kwargs: frame  # type: ignore[assignment]
        try:
            profile = profile_dataset(path, domain="clinical")
        finally:
            pd.read_parquet = original  # type: ignore[assignment]

    assert profile.metadata["native_adaptor"] == "parquet_path"
    assert profile.metadata["domain"] == "clinical"


def test_about_guide_explains_package_positioning() -> None:
    text = about()
    assert "What is EchoTime?" in text
    assert "dataset-characterization layer" in text


def test_api_reference_mentions_profile_dataset_rationale() -> None:
    text = api_reference()
    assert "`profile_dataset`" in text
    assert "dataset, not just a single series" in text


def test_scenario_guide_filters_domain_and_environment() -> None:
    text = scenario_guide(domain="wearable", environment="pandas_pipeline")
    assert "Wearable or digital biomarker longitudinal cohort" in text
    assert "Resting-state or task fMRI cohort profiling" not in text


def test_environment_matrix_mentions_cli_and_notebook() -> None:
    text = environment_matrix()
    assert "Jupyter or interactive notebook" in text
    assert "CLI and shell batch jobs" in text


def test_workflow_recommendation_highlights_domain_axes() -> None:
    text = workflow_recommendation(domain="fmri", environment="neuro_stack")
    assert "coupling_networkedness" in text
    assert "Recommended input setup" in text


def test_user_guide_combines_multiple_sections() -> None:
    text = user_guide()
    assert "# What is EchoTime?" in text
    assert "# EchoTime API reference" in text
    assert "# EchoTime scenario guide" in text


def test_docs_index_lists_guide_topics() -> None:
    text = docs_index()
    assert "documentation index" in text.lower()
    assert "user-guide" in text


def test_cli_can_print_about_guide_without_input() -> None:
    cmd = [sys.executable, "-m", "echotime.cli", "--guide", "about"]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True, env=_subprocess_env())
    assert "What is EchoTime?" in completed.stdout



def test_summary_card_markdown_is_plain_language() -> None:
    x = np.sin(np.linspace(0, 10 * np.pi, 256))
    profile = profile_dataset(x, domain="traffic")
    text = profile.to_summary_card_markdown(audience="product")
    assert "Executive summary" in text
    assert "Recommended next actions" in text
    assert "plain-language label" in text



def test_narrative_report_has_everyday_language_sections() -> None:
    rng = np.random.default_rng(5)
    t = np.linspace(0, 8 * np.pi, 240)
    data = np.column_stack([np.sin(t), np.sin(t + 0.1) + 0.05 * rng.normal(size=t.size)])
    profile = profile_dataset(data, domain="energy")
    text = profile.to_narrative_report(audience="operations")
    assert "What this dataset is, in everyday language" in text
    assert "Why this matters for common analysis tasks" in text
    assert "Reliability and interpretation guardrails" in text



def test_case_gallery_mentions_web_traffic_and_fmri() -> None:
    text = case_gallery()
    assert "Web/app traffic and product analytics" in text
    assert "Resting-state or task fMRI cohort" in text



def test_cli_can_print_case_gallery_and_summary_card(tmp_path: Path) -> None:
    arr = np.sin(np.linspace(0, 4 * np.pi, 128))
    arr_path = tmp_path / "demo.npy"
    np.save(arr_path, arr)

    guide_cmd = [sys.executable, "-m", "echotime.cli", "--guide", "cases", "--domain", "traffic"]
    guide_out = subprocess.run(guide_cmd, capture_output=True, text=True, check=True, env=_subprocess_env())
    assert "Web/app traffic and product analytics" in guide_out.stdout

    card_cmd = [sys.executable, "-m", "echotime.cli", str(arr_path), "--format", "summary-card", "--domain", "traffic"]
    card_out = subprocess.run(card_cmd, capture_output=True, text=True, check=True, env=_subprocess_env())
    assert "EchoTime summary card" in card_out.stdout


def test_compare_series_scores_sine_higher_than_noise() -> None:
    rng = np.random.default_rng(77)
    t = np.linspace(0, 12 * np.pi, 300)
    left = np.sin(t)
    right_similar = np.sin(t + 0.15) + 0.05 * rng.normal(size=t.size)
    right_different = rng.normal(size=t.size)

    similar_report = compare_series(left, right_similar, left_name="a", right_name="b")
    different_report = compare_series(left, right_different, left_name="a", right_name="c")

    assert similar_report.similarity_score > different_report.similarity_score
    assert similar_report.component_scores["spectral_similarity"] > 0.6
    assert {"pearson_r", "spearman_rho", "kendall_tau"} <= set(similar_report.reference_metrics)
    assert similar_report.reference_metrics["pearson_r"] > different_report.reference_metrics["pearson_r"]



def test_compare_series_penalizes_monotonic_cumulative_mismatch() -> None:
    left_daily = np.r_[np.zeros(8), np.ones(5) * 8.0, np.ones(8) * 1.5, np.zeros(10), np.ones(9) * 0.3]
    right_daily = np.r_[np.ones(10) * 2.0, np.zeros(6), np.ones(10) * 0.5, np.ones(14) * 1.1]
    left = np.cumsum(left_daily)
    right = np.cumsum(right_daily)

    report = compare_series(left, right, left_name="left", right_name="right")

    assert report.reference_metrics["pearson_r"] > 0.75
    assert report.reference_metrics["first_difference_r"] < 0.0
    assert report.similarity_score < 0.35
    assert report.component_mean < 0.3
    assert report.component_scores["derivative_similarity"] == 0.0
    assert report.metadata["monotonic_like_inputs"] is True
    assert any("monotonic or cumulative" in note for note in report.notes)


def test_compare_profiles_detects_structural_similarity() -> None:
    t = np.linspace(0, 10 * np.pi, 240)
    left = np.column_stack([np.sin(t), np.sin(t + 0.2)])
    right = np.column_stack([0.9 * np.sin(t + 0.1), 1.1 * np.sin(t + 0.25)])
    far = np.column_stack([np.sign(np.sin(t)), np.random.default_rng(3).normal(size=t.size)])

    close_report = compare_profiles(left, right, left_name="left", right_name="right")
    far_report = compare_profiles(left, far, left_name="left", right_name="far")

    assert close_report.similarity_score > far_report.similarity_score
    assert close_report.component_scores["overall_axis_similarity"] > 0.5



def test_rolling_similarity_returns_windows() -> None:
    t = np.linspace(0, 8 * np.pi, 160)
    left = np.sin(t)
    right = np.sin(t + 0.1)
    windows = rolling_similarity(left, right, window=40, step=10)
    assert windows
    assert windows[0]["similarity_score"] > 0.5
    assert windows[0]["component_mean"] > 0.5
    assert {"pearson_r", "spearman_rho", "normalized_mutual_information"} <= set(windows[0])



def test_hot_case_gallery_and_similarity_playbook_are_exposed() -> None:
    hot = hot_case_gallery()
    playbook = similarity_playbook()
    assert "OpenClaw GitHub stars" in hot
    assert "compare_series" in playbook



def test_project_homepage_html_contains_core_sections() -> None:
    html = project_homepage_html()
    assert "EchoTime" in html
    assert "OpenClaw" in html
    assert "guide/index.html" in html
    assert "guide/tutorials.html" in html
    assert "guide/api.html" in html
    assert "left sidebar" in html



def test_cli_can_compare_two_arrays(tmp_path: Path) -> None:
    left = np.sin(np.linspace(0, 4 * np.pi, 128))
    right = np.sin(np.linspace(0, 4 * np.pi, 128) + 0.1)
    left_path = tmp_path / "left.npy"
    right_path = tmp_path / "right.npy"
    np.save(left_path, left)
    np.save(right_path, right)

    cmd = [sys.executable, "-m", "echotime.cli", str(left_path), "--reference", str(right_path), "--format", "similarity-summary"]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True, env=_subprocess_env())
    assert "EchoTime similarity summary" in completed.stdout



def test_cli_can_print_hot_cases_and_homepage(tmp_path: Path) -> None:  # noqa: ARG001
    hot_cmd = [sys.executable, "-m", "echotime.cli", "--guide", "hot-cases"]
    hot_out = subprocess.run(hot_cmd, capture_output=True, text=True, check=True, env=_subprocess_env())
    assert "OpenClaw GitHub stars" in hot_out.stdout

    home_cmd = [sys.executable, "-m", "echotime.cli", "--guide", "homepage"]
    home_out = subprocess.run(home_cmd, capture_output=True, text=True, check=True, env=_subprocess_env())
    assert "<html" in home_out.stdout.lower()



def test_agent_drive_compare_returns_compact_context() -> None:
    t = np.linspace(0, 10 * np.pi, 240)
    left = np.sin(t)
    right = np.sin(t + 0.1)
    result = agent_drive(left, right, goal="Decide whether these curves are similar with minimal token usage", budget="lean")
    assert result.mode == "compare"
    assert result.compact_context["type"] == "similarity"
    assert "series_similarity" in result.metadata


def test_agent_drive_profile_returns_profile_context() -> None:
    x = np.sin(np.linspace(0, 6 * np.pi, 256))
    result = agent_drive(x, goal="Explain this dataset to a non-technical collaborator", budget="balanced")
    assert result.mode == "profile"
    assert result.compact_context["type"] == "profile"
    assert result.get("profile") is not None


def test_agent_context_helpers_are_exposed_on_profile_and_similarity() -> None:
    t = np.linspace(0, 8 * np.pi, 200)
    profile = profile_dataset(np.sin(t))
    report = compare_series(np.sin(t), np.sin(t + 0.2))
    assert "top_axes" in profile.to_agent_context_dict()
    assert "overall_similarity" in report.to_agent_context_dict()
    assert "compact agent context" in report.to_agent_context_markdown().lower()


def test_agent_driver_plan_mentions_cheapest_move() -> None:
    driver = AgentDriver(goal="Compare these two trajectories and keep it compact", budget="lean")
    plan = driver.plan(has_reference=True)
    assert plan["mode"] == "compare"
    assert plan["planned_steps"][0]["name"] == "compare_series"


def test_agent_driving_guide_mentions_token_saving() -> None:
    text = agent_driving_guide()
    assert "Token-saving principles" in text
    assert "AgentDriver" in text


def test_cli_can_run_agent_context(tmp_path: Path) -> None:
    left = np.sin(np.linspace(0, 4 * np.pi, 128))
    right = np.sin(np.linspace(0, 4 * np.pi, 128) + 0.1)
    left_path = tmp_path / "left.npy"
    right_path = tmp_path / "right.npy"
    np.save(left_path, left)
    np.save(right_path, right)

    cmd = [
        sys.executable, "-m", "echotime.cli", str(left_path),
        "--reference", str(right_path),
        "--agent-goal", "Tell me if these are similar, cheaply",
        "--format", "agent-context",
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True, env=_subprocess_env())
    assert "EchoTime agent context" in completed.stdout


def test_docs_index_and_api_reference_include_agent_driving() -> None:
    assert "agent-driving" in docs_index()
    assert "AgentDriver / agent_drive / agent_context" in api_reference()


def test_ecosystem_positioning_mentions_adjacent_packages() -> None:
    text = ecosystem_positioning(format="markdown")
    assert "tsfresh" in text
    assert "aeon" in text
    assert "DTAIDistance" in text
    assert "dataset-first" in text


def test_coverage_matrix_marks_scope_honestly() -> None:
    text = coverage_matrix(format="markdown")
    assert "Dataset-first structural profiling" in text
    assert "Out of scope" in text
    assert "Forecasting models and backtesting" in text


def test_agent_manifest_json_has_routing_policy() -> None:
    manifest = agent_manifest(format="json")
    assert manifest["positioning"].startswith("dataset-first")
    assert "routing_policy" in manifest
    assert "budget_paths" in manifest


def test_tooling_router_forecasting_prefers_modelling_packages() -> None:
    route = tooling_router("forecast the next 14 days with prediction intervals", format="json")
    assert "Darts" in route["primary_packages"]
    assert "EchoTime" in route["echotime_role"]


def test_tooling_router_profile_task_prefers_echotime() -> None:
    route = tooling_router("characterize this dataset and write a summary card", format="json")
    assert route["primary_packages"] == ["echotime"] or route["primary_packages"] == ("echotime",)


def test_github_readme_contains_ecosystem_positioning() -> None:
    text = github_readme(format="markdown")
    assert "Where EchoTime fits in the ecosystem" in text
    assert "tsfresh" in text
    assert "Agent-ready by design" in text
    assert "playground.html" in text


def test_homepage_mentions_ecosystem_and_coverage() -> None:
    html = project_homepage_html(version="0.17.0")
    assert "Tutorials, API material, and ecosystem detail now live in dedicated docs pages" in html
    assert "guide/ecosystem.html" in html
    assert "guide/agents.html" in html


def test_docs_pages_render_sidebar_layout() -> None:
    docs_home = project_docs_home_html()
    api_html = project_api_reference_html()
    assert "docs-sidebar" in docs_home
    assert "Getting Started" in docs_home
    assert "doc-link active" in api_html
    assert "compare_series" in api_html


def test_tutorials_page_links_real_example_gallery() -> None:
    html = project_tutorials_html()
    assert "real example gallery built from frozen snapshots of public data" in html
    assert "example-github-breakout-analogs.html" in html
    assert "example-two-curves-similarity.html" in html
    assert "Open example" in html


def test_getting_started_page_shows_human_data_workflows() -> None:
    html = project_getting_started_html()
    assert "my_metrics.csv" in html
    assert "my_timeseries.csv" in html
    assert "patient_vitals.csv" in html
    assert "Print a summary card first; export HTML second." in html


def test_example_page_uses_clean_runnable_code_for_humans() -> None:
    pages = project_docs_pages()
    html = pages["guide/example-weekly-traffic-signals.html"]
    assert "Runnable example" in html
    assert "Use your own data" in html
    assert "import pandas as pd" in html
    assert "real_python_javascript_pageviews_2024.csv" in html
    assert "sys.path" not in html


def test_explain_dataset_returns_plain_summary_card() -> None:
    x = np.sin(np.linspace(0, 8 * np.pi, 128))
    text = explain_dataset(x)
    assert text.startswith("# EchoTime summary card")
    assert "overall reliability" in text.lower()


def test_profile_html_report_contains_html() -> None:
    x = np.sin(np.linspace(0, 8 * np.pi, 128))
    profile = profile_dataset(x)
    html = profile.to_html_report()
    assert html.lstrip().startswith("<!doctype html>")
    assert "Axis radar" in html


def test_similarity_html_report_contains_html() -> None:
    x = np.sin(np.linspace(0, 8 * np.pi, 128))
    y = np.sin(np.linspace(0, 8 * np.pi, 128) + 0.1)
    report = compare_series(x, y)
    html = report.to_html_report()
    assert html.lstrip().startswith("<!doctype html>")
    assert "Similarity components" in html
    assert "Similarity radar" in html
    assert "Familiar statistics" in html
    assert "Pearson r" in html
    assert "Mutual info" in html
    assert "Rolling component mean" not in html


def test_agent_tool_wrappers_expose_stable_fields() -> None:
    x = np.sin(np.linspace(0, 8 * np.pi, 128))
    profile_payload = ts_profile(x)
    compare_payload = ts_compare(x, x)
    route_payload = ts_route("Profile this dataset for modelling handoff.")
    assert profile_payload["tool"] == "ts_profile"
    assert {"headline", "recommended_next_step", "input_contract", "evidence", "error"} <= set(profile_payload)
    assert compare_payload["tool"] == "ts_compare"
    assert {"verdict", "stop_here", "input_contract", "evidence", "error"} <= set(compare_payload)
    assert route_payload["tool"] == "ts_route"
    assert {"recommended_tool", "input_contract", "evidence", "error"} <= set(route_payload)
    assert route_payload["recommended_tool"] in {"ts_profile", "ts_compare"}


def test_starter_dataset_listing_and_export(tmp_path: Path) -> None:
    items = list_starter_datasets()
    assert any(item["name"] == "weekly_website_traffic" for item in items)
    case = starter_dataset("weekly_website_traffic")
    assert case["domain"] == "traffic"
    out = tmp_path / "traffic.csv"
    write_starter_dataset("weekly_website_traffic", out)
    assert out.exists()
    assert "sessions" in out.read_text(encoding="utf-8").splitlines()[0]


def test_cli_quickstart_and_tool_json() -> None:
    env = _subprocess_env()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        arr_path = tmp_path / "x.npy"
        np.save(arr_path, np.sin(np.linspace(0, 8 * np.pi, 128)))
        quick = subprocess.run([sys.executable, "-m", "echotime.cli", "--guide", "quickstart"], capture_output=True, text=True, env=env, check=True)
        assert "60-second quickstart" in quick.stdout
        tool = subprocess.run([sys.executable, "-m", "echotime.cli", str(arr_path), "--format", "tool-json"], capture_output=True, text=True, env=env, check=True)
        payload = json.loads(tool.stdout)
        assert payload["tool"] == "ts_profile"


def test_tool_schemas_include_real_data_ref_fields() -> None:
    schemas = tool_schemas(format="dict")
    tools = {tool["name"]: tool for tool in schemas["tools"]}
    assert "data_ref" in tools["ts_profile"]["input_schema"]["properties"]
    assert {"left_ref", "right_ref"} <= set(tools["ts_compare"]["input_schema"]["properties"])
    assert "available_inputs" in tools["ts_route"]["input_schema"]["properties"]


def test_project_playground_html_contains_flagship_cases() -> None:
    html = project_playground_html()
    assert "OpenClaw-style GitHub breakout analogs" in html
    assert "BTC vs gold under shocks" in html
    assert "Heatwave vs grid load" in html
    assert "iframe" in html


def test_examples_notebooks_cover_flagship_and_beginner_cases() -> None:
    notebooks = sorted((Path(__file__).resolve().parents[1] / "examples" / "notebooks").glob("*.ipynb"))
    names = {path.name for path in notebooks}
    assert "06_energy_load_heatwave.ipynb" in names
    assert "07_wearable_recovery_cohort.ipynb" in names
    assert "08_single_column_csv_to_report.ipynb" in names
    assert "09_timestamps_and_values_irregularity.ipynb" in names
    assert "10_two_curves_similarity_verdict.ipynb" in names
    assert len(notebooks) >= 10


def test_tooling_router_can_return_object_without_fallback() -> None:
    route = tooling_router("compare these two curves and keep it compact", format="object")
    assert hasattr(route, "to_dict")
    payload = route.to_dict()
    assert payload["detected_task"] == "whole-series similarity triage"



def test_ts_route_reports_no_fallback_used() -> None:
    payload = ts_route("Compare these two curves and stop early if the signal is clear.", available_inputs=["left_ref", "right_ref"])
    assert payload["recommended_tool"] == "ts_compare"
    assert payload["evidence"]["fallback_used"] is False
    assert payload["stable_contract"] is True



def test_project_pages_bundle_contains_docs_surface() -> None:
    bundle = project_pages_bundle(version="0.17.0")
    assert "index.html" in bundle
    assert "playground.html" in bundle
    assert "guide/index.html" in bundle
    assert "guide/api.html" in bundle
    assert "guide/example-github-breakout-analogs.html" in bundle
    assert "reports/github_breakout_similarity.html" in bundle
    assert "social/github_breakout_card.svg" in bundle


def test_example_page_contains_code_and_visual_assets() -> None:
    bundle = project_pages_bundle(version="0.17.0")
    html = bundle["guide/example-github-breakout-analogs.html"]
    assert "plot_github_breakout_analogs.py" in html
    assert "Standalone report" in html
    assert "Social card" in html
    assert "<svg" in html


def test_blog_pages_include_real_visuals() -> None:
    bundle = project_pages_bundle(version="0.17.0")
    for path in (
        "blog/github_breakout_analogs.html",
        "blog/btc_vs_gold_under_shocks.html",
        "blog/heatwave_vs_grid_load.html",
    ):
        html = bundle[path]
        assert "<svg" in html
        assert "Similarity radar" in html or "Dataset radar" in html


def test_new_repo_guides_cover_zero_install_and_pages() -> None:
    assert "uvx" in zero_install_guide()
    assert "GitHub Pages" in pages_deploy_guide()
    assert "OpenAI tool-calling template" in integration_templates_guide()
    assert "decision stories" in case_studies_guide().lower()


def test_demo_server_helpers_parse_and_render() -> None:
    arr = parse_numeric_text("1, 2, 3\n4 5")
    assert arr.shape == (5,)
    profile_payload = profile_from_text("1, 2, 3, 4, 5")
    assert profile_payload.ok is True
    assert "summary card" in profile_payload.payload["summary_markdown"].lower()
    compare_payload = compare_from_text("1,2,3,4", "1.1,2.1,2.9,4.2")
    assert compare_payload.ok is True
    assert compare_payload.payload["tool_json"]["tool"] == "ts_compare"


def test_demo_server_html_mentions_local_live_demo() -> None:
    html = demo_server_html()
    assert "Local live demo" in html
    assert "/api/profile" in html
    assert "OpenClaw-style GitHub breakout analogs" in html or "GitHub breakout analogs" in html


def test_pages_bundle_manifest_and_blog_are_present() -> None:
    bundle = project_pages_bundle(version="0.17.0")
    assert "manifest/demo_manifest.json" in bundle
    assert "blog/github_breakout_analogs.html" in bundle
    manifest = json.loads(bundle["manifest/demo_manifest.json"])
    assert manifest["pages"]["homepage"] == "index.html"


def test_new_guides_cover_live_demo_and_routing_contracts() -> None:
    assert "echotime-demo" in live_demo_guide()
    assert "ts_profile({data_ref" in routing_contract_guide()


def test_project_demo_manifest_has_flagship_pages() -> None:
    manifest = project_demo_manifest()
    assert "github_breakout" in manifest["pages"]["reports"]
    assert manifest["notes"][1].startswith("Use echotime-demo")
