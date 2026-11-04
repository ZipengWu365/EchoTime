#!/usr/bin/env python3
"""Freeze the unmodified Python reference; never run automatically in tests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import scipy

from acceleration_golden import FORMAT_VERSION, encode, fixture_cases, run_case


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-commit", required=True, help="Full or abbreviated pristine reference commit")
    parser.add_argument("--out", type=Path, default=ROOT / "tests/golden/acceleration_reference.json")
    args = parser.parse_args()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    reference = subprocess.check_output(["git", "rev-parse", args.reference_commit], cwd=ROOT, text=True).strip()
    if head != reference:
        parser.error(f"HEAD {head} differs from the requested reference {reference}")
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "src/echotime"], cwd=ROOT)
    if dirty.returncode:
        parser.error("Reference source is dirty. Generate in a pristine checkout, not from an optimized implementation.")
    tracked = subprocess.check_output(["git", "ls-files", "src/echotime"], cwd=ROOT, text=True).splitlines()
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                     for name in sorted(tracked) if name.endswith(".py")}
    inputs, cases = fixture_cases()
    records = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        for number, case in enumerate(cases, start=1):
            try:
                records.append({**case, "expected": run_case(case, inputs, "python")})
            except (ValueError, TypeError) as exc:
                # Unsupported multivariate methods and invalid short inputs are
                # part of the frozen API contract, not silently omitted cases.
                records.append({**case, "expected_exception": {"type": type(exc).__name__, "message": str(exc)}})
            if number % 50 == 0:
                print(f"Frozen {number}/{len(cases)} cases", flush=True)
    result = {
        "format_version": FORMAT_VERSION,
        "provenance": {"reference_commit": head, "backend": "python", "seed": 20261104,
                       "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                       "platform": platform.platform(), "machine": platform.machine(), "source_sha256": source_hashes},
        "contracts": {"A": "Finite float hex equality; NaN matches NaN; infinity sign is exact.",
                      "B": "abs_tol=1e-12 and rel_tol=1e-12; structure and text remain exact.",
                      "ignored_values": ["package_version (key and nonempty string remain required)"]},
        "inputs": inputs, "cases": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(encode(result), indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Saved {len(cases)} frozen cases to {args.out}", flush=True)


if __name__ == "__main__":
    main()
