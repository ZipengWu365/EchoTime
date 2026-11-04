"""Small, versioned reference-fixture format for the acceleration project.

The reference data is committed separately. Tests never generate expectations.
Floating-point inputs and outputs use hexadecimal strings so the snapshot does
not lose bits in a decimal JSON round trip.
"""

from __future__ import annotations

import math
import contextlib
import hashlib
import importlib.metadata
import io
import json
import os
import platform
from pathlib import Path
import sys
from typing import Any

import numpy as np


FORMAT_VERSION = 1
EMBEDDING_METRICS = {"acf", "periodogram", "trend", "ordinal_js", "linear_trend_model"}
FROZEN_SHA256 = "6865f8f90be4708454e7d61b0b8c97100ee430111c889fcb966faa72d9cc923a"


def numeric_dispatch() -> dict[str, Any]:
    """Describe the local numerical build and dispatch, not just version labels."""
    config = io.StringIO()
    with contextlib.redirect_stdout(config):
        np.show_config()
    core = sys.modules.get("numpy._core._multiarray_umath", sys.modules.get("numpy.core._multiarray_umath"))
    features = getattr(core, "__cpu_features__", {})
    cpu_model = platform.processor()
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("model name"):
                cpu_model = line.partition(":")[2].strip()
                break
    variables = (
        "OPENBLAS_CORETYPE", "OPENBLAS_NUM_THREADS", "NPY_DISABLE_CPU_FEATURES",
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "MKL_CBWR", "MKL_ENABLE_INSTRUCTIONS",
        "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS",
    )
    return {
        "environment": {name: os.environ.get(name) for name in variables},
        "numpy_build": config.getvalue(), "cpu_model": cpu_model,
        "numpy_cpu_features": {name: bool(value) for name, value in sorted(features.items())},
    }


def load_snapshot(frozen_path: Path, reference_path: Path | None = None) -> dict[str, Any]:
    """Load the immutable fixture or an explicitly verified same-environment sidecar.

    This function never calculates expected values. A sidecar must be produced
    separately by verify_reference_environment.py from the pristine original
    implementation, using the exact committed input arrays and case definitions.
    """
    frozen_bytes = frozen_path.read_bytes()
    if hashlib.sha256(frozen_bytes).hexdigest() != FROZEN_SHA256:
        raise ValueError("The immutable original golden fixture has changed")
    frozen = json.loads(frozen_bytes)
    if reference_path is None:
        return decode(frozen)
    if reference_path.resolve() == frozen_path.resolve():
        raise ValueError("Reference sidecar must be separate from the frozen fixture")
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    provenance = reference.get("provenance", {})
    original = frozen["provenance"]
    required = {
        "kind": "environment_reference",
        "reference_commit": original["reference_commit"],
        "source_fixture_sha256": FROZEN_SHA256,
        "source_sha256": original["source_sha256"],
        "backend": "python",
        "isolated_subprocess": True,
        "native_extension_disabled": True,
        "source_only_imports": True,
    }
    for key, value in required.items():
        if provenance.get(key) != value:
            raise ValueError(f"Invalid environment reference provenance: {key}")
    import scipy

    try:
        pandas_version = importlib.metadata.version("pandas")
    except importlib.metadata.PackageNotFoundError:
        pandas_version = None
    environment = {
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "pandas": pandas_version,
        "machine": platform.machine(), "platform": platform.platform(),
    }
    for key, value in environment.items():
        if provenance.get(key) != value:
            raise ValueError(f"Reference sidecar belongs to a different environment: {key}")
    if provenance.get("numeric_dispatch") != numeric_dispatch():
        raise ValueError("Reference sidecar belongs to a different numerical build or CPU/BLAS dispatch")
    source = Path(provenance.get("reference_source", ""))
    package = Path(provenance.get("imported_package_path", ""))
    if not source.is_absolute() or package != source / "src/echotime/__init__.py":
        raise ValueError("Reference sidecar has an invalid original import path")
    for key in ("format_version", "contracts", "inputs"):
        if reference.get(key) != frozen[key]:
            raise ValueError(f"Reference sidecar changed frozen {key}")
    cases = reference.get("cases", [])
    if len(cases) != len(frozen["cases"]):
        raise ValueError("Reference sidecar changed the case count")
    for case, original_case in zip(cases, frozen["cases"]):
        spec = {k: v for k, v in case.items() if k not in {"expected", "expected_exception"}}
        original_spec = {k: v for k, v in original_case.items() if k not in {"expected", "expected_exception"}}
        if spec != original_spec:
            raise ValueError("Reference sidecar changed a frozen case definition")
        if ("expected" in case) == ("expected_exception" in case):
            raise ValueError("Reference sidecar must contain exactly one expected outcome per case")
    if not isinstance(reference.get("drift_summary"), dict):
        raise ValueError("Reference sidecar is missing the frozen-baseline drift report")
    return decode(reference)


def encode(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return {"$array": {"dtype": str(value.dtype), "shape": list(value.shape),
                            "values": [encode(v) for v in value.ravel().tolist()]}}
    if isinstance(value, (float, np.floating)):
        return {"$float": float(value).hex()}
    if isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_)):
        return int(value)
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(v) for v in value]
    if value is None or isinstance(value, str):
        return value
    raise TypeError(f"Cannot freeze {type(value).__name__}")


def decode(value: Any) -> Any:
    if isinstance(value, dict):
        if set(value) == {"$float"}:
            return float.fromhex(value["$float"])
        if set(value) == {"$array"}:
            arr = value["$array"]
            return np.asarray([decode(v) for v in arr["values"]], dtype=arr["dtype"]).reshape(arr["shape"])
        return {k: decode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [decode(v) for v in value]
    return value


def _resolve(value: Any, inputs: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        if set(value) == {"$input"}:
            return inputs[value["$input"]]
        return {k: _resolve(v, inputs) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v, inputs) for v in value]
    return value


def run_case(case: dict[str, Any], inputs: dict[str, Any], backend: str) -> Any:
    from echotime import _native
    from echotime.batch import one_vs_many, paired_distances, pairwise_distance_matrix, cross_distance_matrix
    from echotime.profile import profile_dataset, profile_series
    from echotime.similarity import compare_series, rolling_similarity

    functions = {fn.__name__: fn for fn in (
        one_vs_many, paired_distances, pairwise_distance_matrix, cross_distance_matrix,
        compare_series, rolling_similarity, profile_dataset, profile_series,
    )}
    kwargs = _resolve(case.get("kwargs", {}), inputs)
    if case["api"] in {"one_vs_many", "paired_distances", "pairwise_distance_matrix", "cross_distance_matrix"}:
        kwargs.update(backend=backend, n_jobs=1)
    previous = _native._override
    _native.set_similarity_backend(backend)
    try:
        result = functions[case["api"]](*[inputs[name] for name in case["inputs"]], **kwargs)
        return result.to_dict() if hasattr(result, "to_dict") else result
    finally:
        _native.set_similarity_backend(previous)


def fixture_cases() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Called only when deliberately regenerating a pristine reference."""
    from echotime.batch import METRICS

    rng = np.random.default_rng(20261104)
    base = np.cumsum(rng.normal(size=24))
    with_nan = base.copy()
    with_nan[[3, 10]] = np.nan
    banks = {
        "equal": [base, np.cumsum(rng.normal(size=24)), np.full(24, 2.0), with_nan],
        "ragged": [np.cumsum(rng.normal(size=n)) for n in (6, 9, 17, 24)],
        "multichannel": [np.cumsum(rng.normal(size=(19, 3)), axis=0) for _ in range(3)],
        "ties": [base[:12], base[:12].copy(), np.zeros(12), -base[:12]],
    }
    banks["multichannel"][1][[2, 8], 1] = np.nan
    variants = {
        "lcss_similarity": {"epsilon": 0.35, "window": 3, "mode": "fast"},
        "lcss": {"epsilon": 0.35, "window": 3, "mode": "fast"},
        "edr": {"epsilon": 0.35, "window": 3, "normalized": False, "mode": "fast"},
        "erp": {"gap_value": 0.75, "window": 3, "mode": "fast"},
        "twed": {"lambda_": 0.3, "nu": 0.07, "window": 3, "mode": "fast"},
        "dtw": {"window": 3, "normalize": False},
        "max_ncc": {"normalize": False}, "sbd": {"normalize": False},
        "best_shift": {"normalize": False}, "independent_max_ncc": {"normalize": False},
        "independent_sbd": {"normalize": False}, "acf": {"max_lag": 5},
        "periodogram": {"n_coeffs": 7}, "ordinal_js": {"order": 4, "delay": 2},
    }
    inputs: dict[str, Any] = {}
    cases: list[dict[str, Any]] = []

    def add(identifier: str, api: str, names: list[str], contract: str = "B", **kwargs: Any) -> None:
        cases.append({"id": identifier, "api": api, "inputs": names, "contract": contract, "kwargs": kwargs})

    for bank, collection in banks.items():
        inputs[bank] = collection
        inputs[bank + "_query"] = collection[0]
        inputs[bank + "_reversed"] = collection[::-1]
        for metric in METRICS:
            configurations = {"default": {}}
            if metric in variants:
                configurations["parameters"] = variants[metric]
            for variant, params in configurations.items():
                contract = "B" if metric in EMBEDDING_METRICS else "A"
                for api, names in (
                    ("pairwise_distance_matrix", [bank]),
                    ("one_vs_many", [bank + "_query", bank]),
                    ("paired_distances", [bank, bank + "_reversed"]),
                ):
                    add(f"batch/{metric}/{bank}/{variant}/{api}", api, names,
                        contract, metric=metric, **params)

    inputs["ragged_times"] = [np.cumsum(rng.uniform(0.5, 2.0, size=len(x))) for x in inputs["ragged"]]
    inputs["ragged_query_times"] = inputs["ragged_times"][0]
    for api, names, timestamps in (
        ("pairwise_distance_matrix", ["ragged"], {"timestamps": {"$input": "ragged_times"}}),
        ("one_vs_many", ["ragged_query", "ragged"], {
            "query_timestamps": {"$input": "ragged_query_times"}, "candidate_timestamps": {"$input": "ragged_times"}}),
    ):
        add("batch/twed/irregular/" + api, api, names, "A", metric="twed", lambda_=0.3, nu=0.07, **timestamps)
    inputs["equal_rows"] = np.asarray(banks["equal"])
    inputs["equal_columns"] = inputs["equal_rows"].T
    for layout in ("rows", "columns"):
        add(f"batch/dtw/layout_{layout}", "pairwise_distance_matrix", ["equal_" + layout], "A", metric="dtw", layout=layout)
    add("batch/sbd/cross", "cross_distance_matrix", ["ragged", "equal"], "A", metric="sbd")
    inputs["empty_bank"] = []
    add("batch/dtw/empty", "one_vs_many", ["equal_query", "empty_bank"], "A", metric="dtw")

    inputs["long"] = [np.cumsum(rng.normal(size=n)) for n in (520, 530)]
    inputs["long_query"] = inputs["long"][0]
    for metric in ("lcss", "edr", "erp", "twed"):
        add(f"batch/{metric}/fast_resample", "one_vs_many", ["long_query", "long"], "A", metric=metric, mode="fast", window=6)

    inputs.update({
        "report_left": np.cumsum(rng.normal(size=48)),
        "report_right": np.cumsum(rng.normal(size=43)),
        "report_constant": np.ones(48), "report_short": np.array([1.0, 2.0, 1.0]),
        "report_missing": np.full(12, np.nan),
        "report_multi_left": rng.normal(size=(48, 3)),
        "report_multi_right": rng.normal(size=(43, 2)),
    })
    for name, left, right, kwargs in (
        ("default", "report_left", "report_right", {}),
        ("small_grid", "report_left", "report_right", {"n_points": 32}),
        ("constant", "report_constant", "report_constant", {"n_points": 32}),
        ("nan", "equal_query", "equal_reversed", {}),
        ("short", "report_short", "report_short", {"n_points": 32}),
        ("missing", "report_missing", "report_left", {"n_points": 32}),
        ("multichannel", "report_multi_left", "report_multi_right", {"n_points": 32}),
    ):
        if name == "nan":
            inputs["report_nan"] = banks["equal"][-1]
            right = "report_nan"
        add("compare/" + name, "compare_series", [left, right], **kwargs)
    add("rolling/default_grid", "rolling_similarity", ["report_left", "report_right"], window=12, step=7)
    add("rolling/small_grid", "rolling_similarity", ["report_left", "report_right"], window=12, step=7, n_points=32)
    add("rolling/too_short", "rolling_similarity", ["report_short", "report_short"], window=12)
    inputs["profile_data"] = rng.normal(size=(48, 3)).cumsum(axis=0)
    inputs["profile_times"] = np.cumsum(rng.uniform(0.5, 2.0, size=48))
    add("profile/dataset", "profile_dataset", ["profile_data"], bootstrap=0, random_state=0,
        channel_names=["left", "middle", "right"], metadata={"fixture": "acceleration_reference"})
    add("profile/dataset_irregular", "profile_dataset", ["profile_data"], bootstrap=0, random_state=0,
        timestamps={"$input": "profile_times"})
    add("profile/series", "profile_series", ["report_left"])
    return inputs, cases


def assert_matches(actual: Any, expected: Any, *, exact: bool, path: str = "result") -> None:
    """Compare complete structure; exempt only the package release identifier."""
    if isinstance(actual, np.ndarray) or isinstance(expected, np.ndarray):
        assert isinstance(actual, np.ndarray) and isinstance(expected, np.ndarray), path + ": array type changed"
        assert actual.shape == expected.shape, path + ": shape changed"
        assert actual.dtype == expected.dtype, path + ": dtype changed"
        actual, expected = actual.tolist(), expected.tolist()
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and actual.keys() == expected.keys(), path + ": keys changed"
        for key in expected:
            if key == "package_version":
                assert isinstance(actual[key], str) and actual[key], path + ": invalid package version"
                continue
            assert_matches(actual[key], expected[key], exact=exact, path=f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, (list, tuple)) and len(actual) == len(expected), path + ": length changed"
        for i, (a, e) in enumerate(zip(actual, expected)):
            assert_matches(a, e, exact=exact, path=f"{path}[{i}]")
    elif isinstance(expected, float):
        assert isinstance(actual, (float, int, np.floating, np.integer)), path + ": numeric type changed"
        a = float(actual)
        if math.isnan(expected):
            assert math.isnan(a), f"{path}: expected NaN, got {a!r}"
        elif math.isinf(expected):
            assert a == expected, f"{path}: expected {expected!r}, got {a!r}"
        elif exact:
            assert a.hex() == expected.hex(), f"{path}: {a.hex()} != {expected.hex()}"
        else:
            assert math.isclose(a, expected, rel_tol=1e-12, abs_tol=1e-12), f"{path}: {a!r} != {expected!r}"
    else:
        assert actual == expected, f"{path}: {actual!r} != {expected!r}"
