"""Regression against the original, independently frozen Python implementation."""

import importlib.util
import json
import os
from pathlib import Path

import pytest

from echotime import _native


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("acceleration_golden", ROOT / "tools/acceleration_golden.py")
golden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(golden)
SNAPSHOT = golden.decode(json.loads((ROOT / "tests/golden/acceleration_reference.json").read_text(encoding="utf-8")))
CASES = SNAPSHOT["cases"]


def test_golden_snapshot_contract():
    from echotime.batch import METRICS

    assert SNAPSHOT["format_version"] == golden.FORMAT_VERSION
    assert SNAPSHOT["provenance"]["reference_commit"] == "08f7df742b364175105e957d39f9f81fe6211bb3"
    assert SNAPSHOT["provenance"]["backend"] == "python"
    assert {case["kwargs"]["metric"] for case in CASES if "metric" in case["kwargs"]} == set(METRICS)
    assert len({case["id"] for case in CASES}) == len(CASES)


@pytest.mark.parametrize("backend", ["python", "native"])
@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_acceleration_reference(case, backend):
    if backend == "native" and not _native.native_available():
        pytest.skip("Native extension is not installed; Python reference cases still run")
    if "expected_exception" in case:
        exception = case["expected_exception"]
        exception_type = {"ValueError": ValueError, "TypeError": TypeError}[exception["type"]]
        with pytest.raises(exception_type) as caught:
            golden.run_case(case, SNAPSHOT["inputs"], backend)
        assert str(caught.value) == exception["message"]
        return
    actual = golden.run_case(case, SNAPSHOT["inputs"], backend)
    portable = os.environ.get("ECHOTIME_GOLDEN_PORTABLE") == "1"
    golden.assert_matches(actual, case["expected"], exact=case["contract"] == "A" and not portable,
                          path=case["id"])
