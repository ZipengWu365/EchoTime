"""Independent-oracle provenance, isolation, and drift-accounting tests."""

import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import py_compile
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_reference_environment", ROOT / "tools/verify_reference_environment.py")
reference = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reference)


def _fake_checkout(tmp_path, monkeypatch, *, commit=None, dirty=False):
    root = tmp_path / "original"
    package = root / "src/echotime"
    package.mkdir(parents=True)
    path = package / "__init__.py"
    path.write_text("MARKER = 'original'\n")
    provenance = {"reference_commit": reference.REFERENCE_COMMIT,
                  "source_sha256": {"src/echotime/__init__.py": hashlib.sha256(path.read_bytes()).hexdigest()}}

    def git(checkout, *args):
        assert checkout == root
        if args == ("rev-parse", "--show-toplevel"):
            return str(root).encode()
        if args == ("rev-parse", "HEAD"):
            return (commit or reference.REFERENCE_COMMIT).encode()
        if args == ("status", "--porcelain", "--untracked-files=no"):
            return b" M README.md\n" if dirty else b""
        raise AssertionError(args)

    monkeypatch.setattr(reference, "_git", git)
    return root, path, provenance


def test_committed_fixture_identity_and_inventory():
    frozen = reference.load_frozen_fixture()
    assert frozen["provenance"]["reference_commit"] == reference.REFERENCE_COMMIT
    assert hashlib.sha256(reference.FIXTURE_PATH.read_bytes()).hexdigest() == reference.SOURCE_FIXTURE_SHA256
    assert len(frozen["cases"]) == 383


def test_reference_accepts_checkout_root_or_src(tmp_path, monkeypatch):
    root, _, provenance = _fake_checkout(tmp_path, monkeypatch)
    validated = reference.validate_reference_source(root, provenance)
    assert reference.validate_reference_source(root / "src", provenance) == validated
    assert validated["reference_source"] == str(root)
    assert validated["source_sha256"] == provenance["source_sha256"]


def test_reference_rejects_wrong_commit(tmp_path, monkeypatch):
    root, _, provenance = _fake_checkout(tmp_path, monkeypatch, commit="f" * 40)
    with pytest.raises(reference.ReferenceValidationError, match="HEAD must be exactly"):
        reference.validate_reference_source(root, provenance)


def test_reference_rejects_tracked_changes(tmp_path, monkeypatch):
    root, _, provenance = _fake_checkout(tmp_path, monkeypatch, dirty=True)
    with pytest.raises(reference.ReferenceValidationError, match="modified tracked"):
        reference.validate_reference_source(root, provenance)


def test_reference_detects_source_change_even_if_git_reports_clean(tmp_path, monkeypatch):
    root, path, provenance = _fake_checkout(tmp_path, monkeypatch)
    path.write_text("MARKER = 'changed'\n")
    with pytest.raises(reference.ReferenceValidationError, match="SHA256 mismatch"):
        reference.validate_reference_source(root, provenance)


def test_reference_rejects_untracked_python_injection(tmp_path, monkeypatch):
    root, path, provenance = _fake_checkout(tmp_path, monkeypatch)
    path.with_name("injected.py").write_text("raise RuntimeError('must never load')\n")
    with pytest.raises(reference.ReferenceValidationError, match="inventory differs.*injected"):
        reference.validate_reference_source(root, provenance)


def test_verified_loader_bypasses_existing_bytecode(tmp_path):
    source = tmp_path / "module.py"
    source.write_text("VALUE = 'poisoned'\n")
    py_compile.compile(str(source), doraise=True)
    previous = source.stat()
    # Same file size and mtime makes timestamp-based .pyc reuse otherwise valid.
    source.write_text("VALUE = 'original'\n")
    os.utime(source, ns=(previous.st_atime_ns, previous.st_mtime_ns))
    assert source.stat().st_size == previous.st_size
    loader = reference._VerifiedSourceLoader("module", source, hashlib.sha256(source.read_bytes()).hexdigest())
    namespace = {}
    exec(loader.get_code("module"), namespace)
    assert namespace["VALUE"] == "original"


def test_verified_loader_rechecks_bytes_at_import_time(tmp_path):
    source = tmp_path / "module.py"
    source.write_text("VALUE = 1\n")
    loader = reference._VerifiedSourceLoader("module", source, hashlib.sha256(source.read_bytes()).hexdigest())
    source.write_text("VALUE = 2\n")
    with pytest.raises(reference.ReferenceValidationError, match="changed during import"):
        loader.get_code("module")


def test_finder_blocks_native_and_modules_outside_manifest(tmp_path, monkeypatch):
    root, _, provenance = _fake_checkout(tmp_path, monkeypatch)
    finder = reference._ReferenceFinder(reference.validate_reference_source(root, provenance))
    with pytest.raises(ImportError, match="Native extension is disabled"):
        finder.find_spec("echotime._echotime_native")
    with pytest.raises(ModuleNotFoundError, match="verified original source manifest"):
        finder.find_spec("echotime.accelerated_injection")
    assert finder.find_spec("numpy") is None


def test_drift_preserves_a_exactness_and_b_tolerance():
    codec = reference._load_codec()
    old = [
        {"id": "a", "contract": "A", "expected": codec.encode(1.0)},
        {"id": "b", "contract": "B", "expected": codec.encode(1.0)},
        {"id": "nonfinite", "contract": "A", "expected": codec.encode(float("nan"))},
    ]
    adjacent = codec.encode(math.nextafter(1.0, 2.0))
    new = [{**old[0], "expected": adjacent}, {**old[1], "expected": adjacent}, old[2]]
    summary = reference.drift_summary(old, new, codec)
    assert summary["changed_cases"] == 2
    assert summary["by_contract"]["A"]["contract_failures"] == 1
    assert summary["by_contract"]["B"]["changed_cases"] == 1
    assert summary["by_contract"]["B"]["contract_failures"] == 0
    assert summary["by_contract"]["A"]["max_absolute_difference"] == math.ulp(1.0)


def test_drift_reports_signed_zero_and_nonfinite_changes():
    codec = reference._load_codec()
    drift = reference._wire_drift(codec.encode([0.0, float("nan")]), codec.encode([-0.0, float("inf")]))
    assert drift["changed_numeric_values"] == 2
    assert drift["nonfinite_changes"] == 1
    assert drift["max_absolute_difference"] == 0.0


def test_sidecar_publication_never_overwrites_existing_file(tmp_path):
    output = tmp_path / "reference.json"
    output.write_text('{"unchanged": true}')
    with pytest.raises(FileExistsError):
        reference._write_new_json(output, {"replacement": True})
    assert json.loads(output.read_text()) == {"unchanged": True}
    assert not list(tmp_path.glob(".reference-*"))
    fresh = tmp_path / "fresh.json"
    reference._write_new_json(fresh, {"independent": True})
    assert json.loads(fresh.read_text()) == {"independent": True}


def _available_reference_checkout():
    configured = os.environ.get("ECHOTIME_TEST_REFERENCE_SOURCE")
    if configured:
        return Path(configured)
    sidecar = os.environ.get("ECHOTIME_REFERENCE_SNAPSHOT")
    if sidecar and Path(sidecar).is_file():
        return Path(json.loads(Path(sidecar).read_text())["provenance"]["reference_source"])
    local = ROOT.parent / "echotime-baseline"
    if local.is_dir():
        return local
    pytest.skip("Full isolated-reference integration needs the original checkout; set ECHOTIME_TEST_REFERENCE_SOURCE")


def test_isolated_worker_uses_original_frozen_inputs_with_poisoned_pythonpath(tmp_path):
    checkout = _available_reference_checkout()
    poisoned = tmp_path / "poison"
    package = poisoned / "echotime"
    package.mkdir(parents=True)
    marker = tmp_path / "wrong-package-imported"
    package.joinpath("__init__.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('poison')\nraise RuntimeError('wrong package')\n"
    )
    output = tmp_path / "environment-reference.json"
    environment = dict(os.environ)
    environment.update(PYTHONPATH=str(poisoned), ECHOTIME_BACKEND="native",
                       ECHOTIME_GOLDEN_PORTABLE="1", ECHOTIME_REFERENCE_SNAPSHOT="/not/a/reference.json")
    completed = subprocess.run([
        sys.executable, str(ROOT / "tools/verify_reference_environment.py"),
        "--reference-source", str(checkout), "--out", str(output),
    ], cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=90)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert not marker.exists()
    sidecar = json.loads(output.read_text())
    frozen = reference.load_frozen_fixture()
    provenance = sidecar["provenance"]
    assert provenance["kind"] == "environment_reference"
    assert provenance["backend"] == "python"
    assert provenance["isolated_subprocess"] is True
    assert provenance["native_extension_disabled"] is True
    assert provenance["source_only_imports"] is True
    assert provenance["source_fixture_sha256"] == reference.SOURCE_FIXTURE_SHA256
    assert provenance["source_sha256"] == frozen["provenance"]["source_sha256"]
    assert provenance["imported_package_path"] == str(checkout.resolve() / "src/echotime/__init__.py")
    assert sidecar["inputs"] == frozen["inputs"]
    assert sidecar["contracts"] == frozen["contracts"]
    specs = lambda cases: [{k: v for k, v in case.items() if k not in {"expected", "expected_exception"}} for case in cases]
    assert specs(sidecar["cases"]) == specs(frozen["cases"])
    assert sidecar["drift_summary"]["total_cases"] == len(frozen["cases"])
    assert "max_scaled_difference" in sidecar["drift_summary"]["by_contract"]["A"]
