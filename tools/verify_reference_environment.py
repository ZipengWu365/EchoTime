#!/usr/bin/env python3
"""Evaluate immutable golden inputs with the pristine original in this environment.

This creates a NEW environment-reference sidecar. It never regenerates inputs,
updates the committed golden, or evaluates the accelerated implementation for
expected values. The worker runs in an isolated interpreter, imports only
hash-verified original EchoTime Python sources, and disables native extensions.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.abc
import importlib.machinery
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any
import warnings


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/golden/acceleration_reference.json"
REFERENCE_COMMIT = "08f7df742b364175105e957d39f9f81fe6211bb3"
SOURCE_FIXTURE_SHA256 = "6865f8f90be4708454e7d61b0b8c97100ee430111c889fcb966faa72d9cc923a"
_BATCH_APIS = {"one_vs_many", "paired_distances", "pairwise_distance_matrix", "cross_distance_matrix"}


class ReferenceValidationError(RuntimeError):
    """The independent reference's identity or isolation could not be verified."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root: Path, *args: str) -> bytes:
    try:
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ReferenceValidationError(f"Cannot inspect reference Git state: {exc}") from exc


def numerical_environment() -> dict[str, Any]:
    """Versions used to compute this sidecar; no accelerated package is imported."""
    import numpy as np
    import scipy

    try:
        pandas = importlib.metadata.version("pandas")
    except importlib.metadata.PackageNotFoundError:
        pandas = None
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "pandas": pandas, "machine": platform.machine(), "platform": platform.platform()}


def load_frozen_fixture() -> dict[str, Any]:
    """Return the committed, encoded fixture after verifying its immutable bytes."""
    raw = FIXTURE_PATH.read_bytes()
    if _sha256(raw) != SOURCE_FIXTURE_SHA256:
        raise ReferenceValidationError("The immutable golden fixture SHA256 has changed")
    relative = FIXTURE_PATH.relative_to(ROOT).as_posix()
    committed = _git(ROOT, "show", f"HEAD:{relative}")
    if raw != committed:
        raise ReferenceValidationError("The golden fixture differs from the committed HEAD version")
    fixture = json.loads(raw)
    if fixture.get("format_version") != 1:
        raise ReferenceValidationError("Unsupported golden format version")
    if fixture["provenance"].get("reference_commit") != REFERENCE_COMMIT:
        raise ReferenceValidationError("The golden fixture names a different reference commit")
    return fixture


def validate_reference_source(reference_source: Path, provenance: dict[str, Any]) -> dict[str, Any]:
    """Verify the original checkout, every recorded Python source, and inventory.

    ``reference_source`` may be the checkout root or its ``src`` directory.
    Tracked changes anywhere in that checkout and extra Python files anywhere
    inside its EchoTime package are refused. Existing .pyc files are never used
    by the source-only loader below.
    """
    requested = Path(reference_source).resolve()
    if (requested / "src/echotime/__init__.py").is_file():
        checkout, src = requested, requested / "src"
    elif (requested / "echotime/__init__.py").is_file():
        checkout, src = requested.parent, requested
    else:
        raise ReferenceValidationError("--reference-source must contain src/echotime or be its src directory")
    git_root = Path(_git(checkout, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if git_root != checkout:
        raise ReferenceValidationError("Reference source is not the root of its own Git checkout")
    head = _git(checkout, "rev-parse", "HEAD").decode().strip()
    if head != REFERENCE_COMMIT or provenance.get("reference_commit") != REFERENCE_COMMIT:
        raise ReferenceValidationError(f"Reference HEAD must be exactly {REFERENCE_COMMIT}; got {head}")
    if _git(checkout, "status", "--porcelain", "--untracked-files=no").strip():
        raise ReferenceValidationError("Reference checkout has modified tracked files")
    expected = provenance.get("source_sha256")
    if not isinstance(expected, dict) or not expected:
        raise ReferenceValidationError("Golden provenance is missing reference source hashes")
    actual_paths = {path.relative_to(checkout).as_posix() for path in (src / "echotime").rglob("*.py")}
    if actual_paths != set(expected):
        added, missing = sorted(actual_paths - set(expected)), sorted(set(expected) - actual_paths)
        raise ReferenceValidationError(f"Reference Python source inventory differs; extra={added}, missing={missing}")
    hashes = {}
    for relative, expected_hash in sorted(expected.items()):
        path = checkout / relative
        if not path.resolve().is_relative_to(src / "echotime") or path.is_symlink():
            raise ReferenceValidationError(f"Reference source escapes its package: {relative}")
        hashes[relative] = _sha256(path.read_bytes())
        if hashes[relative] != expected_hash:
            raise ReferenceValidationError(f"Reference source SHA256 mismatch: {relative}")
    return {"reference_commit": head, "reference_source": str(checkout), "reference_src": str(src),
            "source_sha256": hashes}


class _VerifiedSourceLoader(importlib.machinery.SourceFileLoader):
    """Compile verified source bytes directly, bypassing every existing .pyc."""

    def __init__(self, fullname: str, path: Path, expected_hash: str):
        super().__init__(fullname, str(path))
        self.expected_hash = expected_hash

    def get_code(self, fullname: str):
        data = self.get_data(self.path)
        if _sha256(data) != self.expected_hash:
            raise ReferenceValidationError(f"Reference source changed during import: {self.path}")
        return self.source_to_code(data, self.path)


class _ReferenceFinder(importlib.abc.MetaPathFinder):
    """Resolve EchoTime exclusively from the verified original source manifest."""

    def __init__(self, verified: dict[str, Any]):
        self.checkout = Path(verified["reference_source"])
        self.hashes = verified["source_sha256"]

    def find_spec(self, fullname: str, path=None, target=None):
        if fullname == "echotime._echotime_native":
            raise ImportError("Native extension is disabled for the independent Python reference")
        if fullname != "echotime" and not fullname.startswith("echotime."):
            return None
        stem = "src/" + fullname.replace(".", "/")
        for relative, is_package in ((stem + "/__init__.py", True), (stem + ".py", False)):
            if relative in self.hashes:
                source = self.checkout / relative
                loader = _VerifiedSourceLoader(fullname, source, self.hashes[relative])
                return importlib.util.spec_from_file_location(
                    fullname, source, loader=loader,
                    submodule_search_locations=[str(source.parent)] if is_package else None,
                )
        raise ModuleNotFoundError(f"{fullname} is not present in the verified original source manifest")


def _load_codec():
    # This module supplies only fixture encoding/decoding/comparison. Its case
    # generator and dispatcher are deliberately never used for sidecar values.
    path = ROOT / "tools/acceleration_golden.py"
    spec = importlib.util.spec_from_file_location("_environment_reference_codec", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_inputs(value: Any, inputs: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        if set(value) == {"$input"}:
            return inputs[value["$input"]]
        return {key: _resolve_inputs(item, inputs) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_inputs(item, inputs) for item in value]
    return value


def _check_imports(verified: dict[str, Any]) -> dict[str, str]:
    root = Path(verified["reference_source"])
    imported = {}
    for name, module in tuple(sys.modules.items()):
        if name != "echotime" and not name.startswith("echotime."):
            continue
        source = Path(getattr(module, "__file__", "")).resolve()
        if not source.is_relative_to(root):
            raise ReferenceValidationError(f"Loaded EchoTime module outside the reference: {name}: {source}")
        relative = source.relative_to(root).as_posix()
        if relative not in verified["source_sha256"] or not isinstance(module.__loader__, _VerifiedSourceLoader):
            raise ReferenceValidationError(f"Loaded EchoTime module without verified source: {name}: {source}")
        imported[name] = str(source)
    expected_package = root / "src/echotime/__init__.py"
    if imported.get("echotime") != str(expected_package):
        raise ReferenceValidationError("Imported package path differs from the pristine original checkout")
    return imported


def _wire_drift(original: Any, current: Any) -> dict[str, Any]:
    """Report every numeric/structural change without rounding it away."""
    result = {"changed_numeric_values": 0, "nonfinite_changes": 0, "structure_changes": 0,
              "max_absolute_difference": 0.0, "max_scaled_difference": 0.0,
              "finite_difference_overflows": 0, "examples": []}

    def example(path, before, after):
        if len(result["examples"]) < 12:
            result["examples"].append({"path": path, "original": before, "current": after})

    def walk(before, after, path):
        if isinstance(before, dict) and set(before) == {"$float"} and isinstance(after, dict) and set(after) == {"$float"}:
            a, b = float.fromhex(before["$float"]), float.fromhex(after["$float"])
            if (math.isnan(a) and math.isnan(b)) or a.hex() == b.hex():
                return
            result["changed_numeric_values"] += 1
            example(path, a.hex(), b.hex())
            if math.isfinite(a) and math.isfinite(b):
                difference = abs(a - b)
                if math.isfinite(difference):
                    result["max_absolute_difference"] = max(result["max_absolute_difference"], difference)
                    result["max_scaled_difference"] = max(result["max_scaled_difference"], difference / max(1.0, abs(a)))
                else:
                    result["finite_difference_overflows"] += 1
            else:
                result["nonfinite_changes"] += 1
            return
        if isinstance(before, dict) and isinstance(after, dict) and before.keys() == after.keys():
            for key in before:
                walk(before[key], after[key], f"{path}.{key}")
            return
        if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
            for index, (a, b) in enumerate(zip(before, after)):
                walk(a, b, f"{path}[{index}]")
            return
        if before != after:
            result["structure_changes"] += 1
            example(path, repr(before)[:200], repr(after)[:200])

    walk(original, current, "expected")
    return result


def drift_summary(original_cases: list[dict[str, Any]], current_cases: list[dict[str, Any]], codec=None) -> dict[str, Any]:
    """Separate exact wire drift from each case's unchanged A/B contract."""
    codec = codec or _load_codec()
    if [case["id"] for case in original_cases] != [case["id"] for case in current_cases]:
        raise ReferenceValidationError("Sidecar case inventory differs from the immutable fixture")
    groups = {name: {"cases": 0, "changed_cases": 0, "contract_failures": 0,
                     "changed_numeric_values": 0, "nonfinite_changes": 0, "structure_changes": 0,
                     "max_absolute_difference": 0.0, "max_scaled_difference": 0.0,
                     "finite_difference_overflows": 0} for name in ("A", "B")}
    changes = []
    for before, after in zip(original_cases, current_cases):
        group = groups[before["contract"]]
        group["cases"] += 1
        old_value = {key: before[key] for key in ("expected", "expected_exception") if key in before}
        new_value = {key: after[key] for key in ("expected", "expected_exception") if key in after}
        if old_value == new_value:
            continue
        change = _wire_drift(old_value, new_value)
        group["changed_cases"] += 1
        try:
            if "expected_exception" in before or "expected_exception" in after:
                assert before.get("expected_exception") == after.get("expected_exception")
            else:
                codec.assert_matches(codec.decode(after["expected"]), codec.decode(before["expected"]),
                                     exact=before["contract"] == "A")
            within_contract = True
        except AssertionError:
            within_contract = False
        group["contract_failures"] += int(not within_contract)
        for key in ("changed_numeric_values", "nonfinite_changes", "structure_changes", "finite_difference_overflows"):
            group[key] += change[key]
        for key in ("max_absolute_difference", "max_scaled_difference"):
            group[key] = max(group[key], change[key])
        changes.append({"id": before["id"], "contract": before["contract"], "within_contract": within_contract, **change})
    return {"total_cases": len(original_cases), "changed_cases": len(changes), "by_contract": groups,
            "note": "Differences from the immutable capture are evidence, not accepted tolerances for contract A. max_scaled_difference uses abs(current-original)/max(1,abs(original)); it is not relative error near zero.",
            "changes": changes}


def _write_new_json(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".reference-", suffix=".json", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(result, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
        # A hard link publishes a complete file atomically and refuses to
        # overwrite an existing artifact, including a concurrently created one.
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _worker(reference_source: Path, output: Path) -> int:
    if not sys.flags.isolated:
        raise ReferenceValidationError("The reference worker must run with Python -I isolation")
    if any(name == "echotime" or name.startswith("echotime.") for name in sys.modules):
        raise ReferenceValidationError("EchoTime was already imported before source isolation")
    fixture = load_frozen_fixture()
    verified = validate_reference_source(reference_source, fixture["provenance"])
    os.environ["ECHOTIME_BACKEND"] = "python"
    os.environ["ECHOTIME_NUM_THREADS"] = "1"
    sys.dont_write_bytecode = True
    sys.path.insert(0, verified["reference_src"])
    sys.meta_path.insert(0, _ReferenceFinder(verified))
    import echotime
    from echotime import _native
    from echotime import batch, profile, similarity

    _native.set_similarity_backend("python")
    if _native.native_available() or _native.resolve_backend() != "python":
        raise ReferenceValidationError("Independent reference did not disable the native backend")
    _check_imports(verified)
    functions = {name: getattr(batch, name) for name in _BATCH_APIS}
    functions.update({name: getattr(similarity, name) for name in ("compare_series", "rolling_similarity")})
    functions.update({name: getattr(profile, name) for name in ("profile_dataset", "profile_series")})
    codec = _load_codec()
    inputs = codec.decode(fixture["inputs"])
    records = []
    with warnings.catch_warnings(record=True) as observed_warnings:
        warnings.simplefilter("always")
        for number, original in enumerate(fixture["cases"], start=1):
            # Copy exactly the committed case spec; no RNG or case generator.
            specification = {key: value for key, value in original.items() if key not in {"expected", "expected_exception"}}
            case = codec.decode(specification)
            kwargs = _resolve_inputs(case.get("kwargs", {}), inputs)
            if case["api"] in _BATCH_APIS:
                kwargs.update(backend="python", n_jobs=1)
            try:
                value = functions[case["api"]](*[inputs[name] for name in case["inputs"]], **kwargs)
                value = value.to_dict() if hasattr(value, "to_dict") else value
                record = {**specification, "expected": codec.encode(value)}
            except (ValueError, TypeError) as exc:
                record = {**specification, "expected_exception": {"type": type(exc).__name__, "message": str(exc)}}
            records.append(record)
            if number % 100 == 0:
                print(f"Original reference evaluated {number}/{len(fixture['cases'])} frozen cases", flush=True)
    # Recheck bytes and imports after execution so a concurrent edit cannot
    # silently produce an artifact with an obsolete provenance statement.
    if validate_reference_source(reference_source, fixture["provenance"]) != verified:
        raise ReferenceValidationError("Reference source changed during evaluation")
    if load_frozen_fixture() != fixture:
        raise ReferenceValidationError("Immutable fixture changed during evaluation")
    imported = _check_imports(verified)
    drift = drift_summary(fixture["cases"], records, codec)
    result = {
        "format_version": fixture["format_version"],
        "provenance": {**verified, **numerical_environment(), "kind": "environment_reference", "backend": "python",
                       "source_fixture_sha256": SOURCE_FIXTURE_SHA256,
                       "imported_package_path": str(Path(echotime.__file__).resolve()),
                       "imported_modules": imported, "isolated_subprocess": True,
                       "native_extension_disabled": True, "source_only_imports": True,
                       "numeric_dispatch": codec.numeric_dispatch(),
                       "verification_tool_sha256": _sha256(Path(__file__).read_bytes()),
                       "codec_sha256": _sha256((ROOT / "tools/acceleration_golden.py").read_bytes()),
                       "source_fixture_provenance": fixture["provenance"],
                       "warning_count": len(observed_warnings)},
        "contracts": fixture["contracts"], "inputs": fixture["inputs"], "cases": records,
        "drift_summary": drift,
    }
    _write_new_json(output, result)
    print(json.dumps({"output": str(output), "reference_commit": REFERENCE_COMMIT,
                      "cases": len(records), "drift_by_contract": drift["by_contract"]}, sort_keys=True), flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-source", type=Path, required=True, help="Pristine original checkout or its src directory")
    parser.add_argument("--out", type=Path, required=True, help="New sidecar JSON; existing files are never overwritten")
    parser.add_argument("--_worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        fixture = load_frozen_fixture()
        verified = validate_reference_source(args.reference_source, fixture["provenance"])
        output = args.out.resolve()
        if output == FIXTURE_PATH.resolve() or output.is_relative_to(Path(verified["reference_source"])):
            raise ReferenceValidationError("Sidecar output must not overwrite the golden or write inside the pristine reference")
        if output.exists():
            raise ReferenceValidationError(f"Sidecar output already exists: {output}")
        if args._worker:
            return _worker(Path(verified["reference_source"]), output)
        environment = {key: value for key, value in os.environ.items() if key not in {
            "PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "ECHOTIME_BACKEND", "ECHOTIME_REFERENCE_SNAPSHOT", "ECHOTIME_GOLDEN_PORTABLE"}}
        environment.update(ECHOTIME_BACKEND="python", ECHOTIME_NUM_THREADS="1")
        completed = subprocess.run([
            sys.executable, "-I", str(Path(__file__).resolve()), "--_worker",
            "--reference-source", verified["reference_source"], "--out", str(output),
        ], cwd=verified["reference_source"], env=environment, check=False)
        return completed.returncode
    except (ReferenceValidationError, FileExistsError, OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
