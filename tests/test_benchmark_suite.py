"""Safety and evidence-format checks for the opt-in performance harness."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("acceleration_benchmark_suite", ROOT / "benchmarks/run_suite.py")
suite = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = suite
SPEC.loader.exec_module(suite)


def test_default_profile_is_small_and_full_is_explicit():
    args = suite.parser().parse_args([])
    assert args.profile == "smoke"
    smoke = suite.build_cases(args.profile)
    assert max(case.n_series for case in smoke) <= 32
    assert max(case.n_points for case in smoke) <= 48
    full = suite.build_cases("full")
    assert any(case.n_series == 100000 for case in full)
    assert all(case.n_series < 1000000 for case in full)
    assert any(case.n_points == 5470 for case in full)


def test_glob_filters_do_not_expand_to_other_large_tasks():
    selected = suite.select_cases(suite.build_cases("full"), ["search/dtw/*/n100000/*"], [])
    assert len(selected) == 3
    assert {case.mode for case in selected} == {"brute", "certified", "approximate"}
    assert all(case.n_series == 100000 and case.metric == "dtw" for case in selected)


def test_search_modes_share_frozen_synthetic_input():
    selected = suite.select_cases(suite.build_cases("smoke"), ["search/dtw/*"], [])
    first_query, first_bank = suite._bank(selected[0], 42)
    for case in selected[1:]:
        query, bank = suite._bank(case, 42)
        assert np.array_equal(query, first_query)
        assert np.array_equal(bank, first_bank)
    other_query, _ = suite._bank(selected[0], 43)
    assert not np.array_equal(first_query, other_query)


def test_brute_order_preserves_ties_and_puts_nan_after_infinity():
    values = np.array([np.nan, 0.0, np.inf, -0.0, -np.inf, 2.0, np.nan])
    assert suite._order(values, 7).tolist() == [4, 1, 3, 5, 2, 0, 6]


def test_unexpected_runtime_failure_is_an_error(monkeypatch):
    def failed_prepare(*_):
        raise ValueError("deliberate implementation failure")

    monkeypatch.setattr(suite, "prepare_case", failed_prepare)
    result = suite.run_case(suite.build_cases("smoke")[0], suite.parser().parse_args([]))
    assert result["status"] == "error"
    assert result["error_type"] == "ValueError"
    assert result["error"] == "deliberate implementation failure"


def test_cli_creates_json_and_markdown_with_explicit_source(tmp_path):
    output = tmp_path / "smoke.json"
    completed = subprocess.run([
        sys.executable, str(ROOT / "benchmarks/run_suite.py"),
        "--source-tree", str(ROOT / "src"), "--backend", "python",
        "--case", "batch/dtw/n8/t24/w4", "--repeats", "2", "--warmups", "0",
        "--out", str(output),
    ], cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(output.read_text())
    assert result["summary"] == {"ok": 1, "unavailable": 0, "error": 0}
    assert Path(result["environment"]["package_path"]).parent == ROOT / "src/echotime"
    assert result["environment"]["gpu"]["execution_status"] == "not_implemented_in_this_suite"
    assert len(result["cases"][0]["warm_samples_seconds"]) == 2
    assert result["cases"][0]["timing"]["p50_seconds"] > 0
    assert "p95 (ms)" in output.with_suffix(".md").read_text()


def test_large_python_profile_requires_explicit_opt_in(tmp_path):
    completed = subprocess.run([
        sys.executable, str(ROOT / "benchmarks/run_suite.py"),
        "--source-tree", str(ROOT / "src"), "--profile", "server", "--backend", "python",
        "--case", "compare/t290", "--out", str(tmp_path / "should-not-exist.json"),
    ], cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert completed.returncode == 2
    assert "--allow-slow-python" in completed.stderr
    assert not (tmp_path / "should-not-exist.json").exists()


def test_list_does_not_need_a_valid_source_tree():
    completed = subprocess.run([
        sys.executable, str(ROOT / "benchmarks/run_suite.py"),
        "--source-tree", "/does/not/exist", "--profile", "full", "--list",
        "--case", "pairwise/*/n400/t5470/*",
    ], cwd=ROOT, text=True, capture_output=True, timeout=10)
    assert completed.returncode == 0
    assert len(completed.stdout.splitlines()) == 3


def test_cannot_overwrite_reference_baseline(tmp_path):
    baseline = tmp_path / "reference.json"
    baseline.write_text('{"sentinel": true}')
    completed = subprocess.run([
        sys.executable, str(ROOT / "benchmarks/run_suite.py"),
        "--case", "batch/dtw/n8/t24/w4", "--baseline", str(baseline), "--out", str(baseline),
    ], cwd=ROOT, text=True, capture_output=True, timeout=10)
    assert completed.returncode == 2
    assert "must differ" in completed.stderr
    assert json.loads(baseline.read_text()) == {"sentinel": True}
