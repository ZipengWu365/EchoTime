
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from echotime import environment_doctor, project_launchpad_html, write_pages_bundle


def _env() -> dict[str, str]:
    env = os.environ.copy()
    root = Path(__file__).resolve().parents[1]
    src = root / 'src'
    env['PYTHONPATH'] = str(src)
    return env


def test_environment_doctor_returns_actions() -> None:
    payload = environment_doctor(format='dict')
    assert 'recommended_actions' in payload
    assert payload['recommended_actions']
    assert 'stdout_encoding' in payload


def test_launchpad_html_mentions_start_here_and_doctor() -> None:
    html = project_launchpad_html()
    assert 'Start here' in html
    assert 'Environment doctor' in html
    assert 'echotime-demo --open-browser' in html
    assert '--export-pages docs' in html


def test_cli_homepage_writes_html_file_on_ascii_stdout() -> None:
    env = _env()
    env['PYTHONIOENCODING'] = 'ascii'
    with tempfile.TemporaryDirectory() as tmpdir:
        proc = subprocess.run([sys.executable, '-m', 'echotime.cli', '--guide', 'homepage'], env=env, cwd=tmpdir, capture_output=True, text=True)
        assert proc.returncode == 0
        assert 'written to' in proc.stdout.lower()
        out = Path(tmpdir) / 'echotime-homepage.html'
        assert out.exists()
        assert '<!doctype html>' in out.read_text(encoding='utf-8').lower()


def test_demo_server_module_runs_without_runpy_warning() -> None:
    env = _env()
    proc = subprocess.run([sys.executable, '-W', 'error', '-m', 'echotime.demo_server', '--help'], env=env, capture_output=True, text=True)
    assert proc.returncode == 0
    assert 'Run the local EchoTime live demo server.' in proc.stdout


def test_export_pages_writes_start_here() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / 'docs'
        write_pages_bundle(out, version='0.17.0')
        assert (out / 'index.html').exists()
        assert (out / 'start-here.html').exists()
        assert (out / '404.html').exists()
