"""Real-data equivalence of the native/batch paths against the Python reference.

Data: one AOMIC ID1000 run (290 frames x 400 Schaefer ROIs, TR 2.2 s) and one
NNDb run (5,470 frames x 400 ROIs, TR 1 s), detrended and z-scored per ROI.
Writes benchmarks/validation_real_2026-11.csv. Run on a compute node.
"""

from __future__ import annotations

import csv
import importlib.util
import os
import sys
import time
from pathlib import Path

import numpy as np
from scipy.signal import detrend

import echotime as et
from echotime import _native

DATA = Path(os.environ.get("FMRI_REPO", "/rds/projects/s/spillf-systems-mechanobiology-health-disease/Zipeng/fmri_repo")) / "data/roi_timeseries_raw"
ID1000 = DATA / "aomic_id1000/sub-0001_task-moviewatching_Schaefer400_raw.npy"
NNDB = DATA / "nndb/sub-10_task-500daysofsummer_Schaefer400_nbnc.npy"
OUT = Path(__file__).resolve().parent / "validation_real_2026-11.csv"
rows: list[dict] = []


def load(path: Path) -> np.ndarray:
    x = np.load(path).astype(np.float64)  # stored as (time, roi)
    x = detrend(x, axis=0)
    return (x - x.mean(0)) / x.std(0)


SINGLE = {
    "sbd": et.sbd, "max_ncc": et.max_ncc, "best_shift": et.best_shift,
    "lcss": et.lcss_distance, "edr": et.edr_distance, "erp": et.erp_distance, "twed": et.twed_distance, "dtw": et.dtw_distance,
    "acf": et.acf_distance, "periodogram": et.periodogram_distance, "trend": et.trend_distance,
    "ordinal_js": et.ordinal_pattern_js_distance, "linear_trend_model": et.linear_trend_model_distance,
}
EXACT = {"sbd", "max_ncc", "best_shift", "lcss", "edr", "erp", "twed", "dtw"}


def reference_pairs(cols, pairs, name, params):
    _native.set_similarity_backend("python")
    try:
        return np.asarray([SINGLE[name](cols[i], cols[j], **params) for i, j in pairs], dtype=float)
    finally:
        _native.set_similarity_backend(None)


def record(dataset, name, params, pairs, ref, got, seconds_ref):
    diff = np.abs(np.asarray(got, float) - np.asarray(ref, float))
    both_nan = np.isnan(ref) & np.isnan(got)
    identical = bool(np.all((np.asarray(got, float) == np.asarray(ref, float)) | both_nan))
    rows.append({
        "dataset": dataset, "metric": name, "params": repr(params), "n_pairs": len(pairs),
        "bit_identical": identical, "max_abs_diff": float(np.nanmax(diff)) if diff.size else 0.0,
        "required": "bit-identical" if name in EXACT else "<=1e-12",
        "pass": identical if name in EXACT else bool(np.nanmax(diff) <= 1e-12 * max(1.0, float(np.nanmax(np.abs(ref))))),
        "reference_seconds": round(seconds_ref, 2),
    })
    print(rows[-1], flush=True)


def check_matrix(dataset, X, n_roi, name, params):
    cols = [X[:, k] for k in range(n_roi)]
    I, J = np.triu_indices(n_roi)
    pairs = list(zip(I.tolist(), J.tolist()))
    t0 = time.perf_counter()
    ref = reference_pairs(cols, pairs, name, params)
    seconds = time.perf_counter() - t0
    M = et.pairwise_distance_matrix(X[:, :n_roi], name, **params)
    record(dataset, name, params, pairs, ref, M[I, J], seconds)


def main() -> None:
    print(et.similarity_backend_info(), flush=True)
    A = load(ID1000)
    B = load(NNDB)
    print("ID1000", A.shape, "NNDb", B.shape, flush=True)
    # ID1000: 40 ROIs, every metric, all 820 pairs incl. the diagonal.
    for name in SINGLE:
        params = {"window": 10} if name == "dtw" else {}
        check_matrix("aomic_id1000", A, 40, name, params)
    # NNDb: shift-based and embeddings on 30 ROIs; elastic distances windowed on 10 ROIs.
    for name in ("sbd", "max_ncc", "best_shift", "acf", "periodogram", "trend", "ordinal_js", "linear_trend_model"):
        check_matrix("nndb", B, 30, name, {})
    for name in ("lcss", "edr", "erp", "twed", "dtw"):
        check_matrix("nndb", B, 10, name, {"window": 20} if name != "lcss" else {"window": 20, "epsilon": 0.5})
    # NNDb full-length unbanded DP on two pairs per elastic metric.
    cols = [B[:, k] for k in range(4)]
    for name in ("erp", "twed", "dtw"):
        pairs = [(0, 1), (2, 3)]
        t0 = time.perf_counter()
        ref = reference_pairs(cols, pairs, name, {})
        seconds = time.perf_counter() - t0
        got = et.paired_distances([cols[0], cols[2]], [cols[1], cols[3]], name)
        record("nndb_full_dp", name, {}, pairs, ref, got, seconds)
    # profile_series on 10 ID1000 ROIs: native vs Python backend (rounding only).
    for k in range(10):
        _native.set_similarity_backend("python")
        ref = et.profile_series(A[:, k]).axes
        _native.set_similarity_backend(None)
        got = et.profile_series(A[:, k]).axes
        keys = sorted(ref)
        record("aomic_id1000_profile", "profile_series_axes", {"roi": k}, keys, np.array([ref[q] for q in keys]), np.array([got[q] for q in keys]), 0.0)
    # NeuroTime compatibility: EchoTime dtw_distance == NeuroTime dtw_distance for equal lengths.
    nt_path = Path(os.environ.get("FMRI_REPO", "/rds/projects/s/spillf-systems-mechanobiology-health-disease/Zipeng/fmri_repo")) / "neurotime/src/neurotime/_kernels.py"
    if nt_path.exists():
        spec = importlib.util.spec_from_file_location("nt_kernels_readonly", nt_path)
        K = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(K)
        pairs = [(i, i + 1) for i in range(0, 20, 2)]
        for window in (None, 5):
            ref = np.asarray([K.dtw_distance(A[:, i], A[:, j], window=window) for i, j in pairs])
            got = np.asarray([et.dtw_distance(A[:, i], A[:, j], window=window) for i, j in pairs])
            record("aomic_id1000_vs_neurotime", "dtw_vs_neurotime_dtw_distance", {"window": window}, pairs, ref, got, 0.0)
    with open(OUT, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    failed = [r for r in rows if not r["pass"]]
    print(f"wrote {OUT}: {len(rows)} checks, {len(failed)} failed", flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
