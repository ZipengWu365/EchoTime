"""The environment sidecar cannot silently change the frozen regression contract."""

import importlib.util
import json
import platform
from pathlib import Path

import numpy as np
import pandas
import pytest
import scipy


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("snapshot_golden", ROOT / "tools/acceleration_golden.py")
golden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(golden)
FROZEN = ROOT / "tests/golden/acceleration_reference.json"


@pytest.fixture
def sidecar(tmp_path):
    data = json.loads(FROZEN.read_text(encoding="utf-8"))
    source = tmp_path / "original"
    data["provenance"].update({
        "kind": "environment_reference", "source_fixture_sha256": golden.FROZEN_SHA256,
        "backend": "python", "isolated_subprocess": True,
        "native_extension_disabled": True, "source_only_imports": True,
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "pandas": pandas.__version__,
        "platform": platform.platform(), "machine": platform.machine(),
        "numeric_dispatch": golden.numeric_dispatch(),
        "reference_source": str(source),
        "imported_package_path": str(source / "src/echotime/__init__.py"),
    })
    data["drift_summary"] = {}
    return data, tmp_path / "reference.json"


def write_sidecar(sidecar):
    data, path = sidecar
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_frozen_remains_default():
    snapshot = golden.load_snapshot(FROZEN)
    assert "kind" not in snapshot["provenance"]
    assert len(snapshot["cases"]) == 383


def test_validated_sidecar_contract(sidecar):
    snapshot = golden.load_snapshot(FROZEN, write_sidecar(sidecar))
    assert snapshot["provenance"]["kind"] == "environment_reference"
    assert len(snapshot["cases"]) == 383


@pytest.mark.parametrize("key,value", [
    ("kind", "accelerated_reference"), ("reference_commit", "main"),
    ("source_fixture_sha256", "wrong"), ("source_sha256", {}),
    ("backend", "native"), ("isolated_subprocess", False),
    ("native_extension_disabled", False), ("source_only_imports", False),
    ("numpy", "different-version"), ("scipy", "different-version"),
    ("numeric_dispatch", {}),
    ("imported_package_path", "/accelerated/src/echotime/__init__.py"),
])
def test_rejects_invalid_provenance(sidecar, key, value):
    sidecar[0]["provenance"][key] = value
    with pytest.raises(ValueError):
        golden.load_snapshot(FROZEN, write_sidecar(sidecar))


@pytest.mark.parametrize("mutation", ["inputs", "contracts", "count", "case", "outcome", "drift"])
def test_rejects_changed_frozen_contract(sidecar, mutation):
    data = sidecar[0]
    if mutation in {"inputs", "contracts"}:
        data[mutation] = {}
    elif mutation == "count":
        data["cases"].pop()
    elif mutation == "case":
        data["cases"][0]["contract"] = "not-checked"
    elif mutation == "outcome":
        data["cases"][0].pop("expected", None)
        data["cases"][0].pop("expected_exception", None)
    else:
        data.pop("drift_summary")
    with pytest.raises(ValueError):
        golden.load_snapshot(FROZEN, write_sidecar(sidecar))


def test_cannot_replace_immutable_fixture(tmp_path):
    changed = tmp_path / "golden.json"
    changed.write_bytes(FROZEN.read_bytes() + b" ")
    with pytest.raises(ValueError, match="immutable"):
        golden.load_snapshot(changed)
    with pytest.raises(ValueError, match="separate"):
        golden.load_snapshot(FROZEN, FROZEN)
