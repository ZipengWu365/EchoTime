from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from echotime import asset_consistency_report, compatibility_constraints, ts_compare, ts_profile, write_compatibility_constraints


def _env() -> dict[str, str]:
    env = os.environ.copy()
    root = Path(__file__).resolve().parents[1]
    src = root / 'src'
    env['PYTHONPATH'] = str(src)
    return env


def test_asset_consistency_report_is_green() -> None:
    payload = asset_consistency_report(format='dict')
    assert payload['ok'] is True
    assert payload['expected_version'] == '0.17.1'


def test_constraints_profiles_can_be_exported() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / 'mixed.txt'
        write_compatibility_constraints(out, profile='mixed-scientific-stack')
        text = out.read_text(encoding='utf-8')
        assert 'profile: mixed-scientific-stack' in text
        assert 'numba' in text
        assert compatibility_constraints('clean-venv').startswith('# EchoTime compatibility constraints')


def test_cli_can_write_constraints() -> None:
    env = _env()
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / 'constraints.txt'
        proc = subprocess.run([
            sys.executable, '-m', 'echotime.cli', '--write-constraints', str(out), '--constraint-profile', 'clean-venv'
        ], env=env, capture_output=True, text=True)
        assert proc.returncode == 0
        assert out.exists()
        assert 'clean-venv' in out.read_text(encoding='utf-8')


def test_tool_outputs_include_cache_and_artifact_fields() -> None:
    profile = ts_profile([0.0, 1.0, 0.0, 1.0], budget='lean')
    assert profile['ok'] is True
    for key in ['artifact_uri', 'cost_hint', 'input_digest', 'cache_key']:
        assert key in profile and profile[key]
    comp = ts_compare([0.0, 1.0, 0.0, 1.0], [0.1, 0.9, 0.2, 1.05], budget='lean')
    assert comp['ok'] is True
    for key in ['artifact_uri', 'cost_hint', 'input_digest', 'cache_key']:
        assert key in comp and comp[key]


def test_cli_asset_audit_json() -> None:
    env = _env()
    proc = subprocess.run([sys.executable, '-m', 'echotime.cli', '--guide', 'asset-audit', '--guide-format', 'json'], env=env, capture_output=True, text=True)
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload['ok'] is True


def test_cli_homepage_gbk_writes_fallback_file() -> None:
    env = _env()
    env['PYTHONIOENCODING'] = 'gbk'
    with tempfile.TemporaryDirectory() as tmpdir:
        proc = subprocess.run([sys.executable, '-m', 'echotime.cli', '--guide', 'homepage'], env=env, cwd=tmpdir, capture_output=True, text=True)
        assert proc.returncode == 0
        assert 'html output was written' in proc.stdout.lower()
        assert (Path(tmpdir) / 'echotime-homepage.html').exists()
