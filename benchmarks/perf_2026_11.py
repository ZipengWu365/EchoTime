"""CPU benchmarks for EchoTime 0.18.0.dev0 (native kernels + batch APIs).

"before" is the pure-Python reference (``backend="python"``), i.e. the 0.17.x
code path, timed on a sample of pairs and extrapolated linearly to the full
workload when running it whole would take too long (column ``measured``).
"after" is the native/batch path, always timed on the full workload, single
thread and with all allocated threads.

Writes benchmarks/perf_2026-11.csv. Run on a compute node via Slurm.
"""

from __future__ import annotations

import csv
import os
import time
from pathlib import Path

import numpy as np
from scipy.signal import detrend

import echotime as et
from echotime import _native

DATA = Path(os.environ.get("FMRI_REPO", "/rds/projects/s/spillf-systems-mechanobiology-health-disease/Zipeng/fmri_repo")) / "data/roi_timeseries_raw"
OUT = Path(__file__).resolve().parent / "perf_2026-11.csv"
THREADS = _native.default_threads(None)
rows: list[dict] = []


def load(path):
    x = np.load(path).astype(np.float64)  # stored as (time, roi)
    x = detrend(x, axis=0)
    return (x - x.mean(0)) / x.std(0)


SINGLE = {
    "sbd": et.sbd, "best_shift": et.best_shift, "lcss": et.lcss_distance, "edr": et.edr_distance,
    "erp": et.erp_distance, "twed": et.twed_distance, "dtw": et.dtw_distance, "acf": et.acf_distance,
    "periodogram": et.periodogram_distance, "ordinal_js": et.ordinal_pattern_js_distance, "trend": et.trend_distance,
}


def timed(fn):
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0


def add(function, scenario, frames, n_pairs, before_s, before_measured, single_s, multi_s):
    rows.append({
        "function": function, "scenario": scenario, "frames": frames, "n_pairs": n_pairs,
        "before_python_s": round(before_s, 4), "before_measured": before_measured,
        "after_1thread_s": round(single_s, 4), "after_threads": THREADS, "after_nthreads_s": round(multi_s, 4),
        "speedup_1thread": round(before_s / single_s, 1) if single_s > 0 else float("nan"),
        "speedup_nthreads": round(before_s / multi_s, 1) if multi_s > 0 else float("nan"),
    })
    print(rows[-1], flush=True)


def before_estimate(cols, pairs, name, params, budget_pairs):
    sample = pairs[:budget_pairs]
    _native.set_similarity_backend("python")
    try:
        t = timed(lambda: [SINGLE[name](cols[i], cols[j], **params) for i, j in sample])
    finally:
        _native.set_similarity_backend(None)
    measured = len(sample) == len(pairs)
    return t * len(pairs) / len(sample), ("measured" if measured else f"extrapolated_from_{len(sample)}")


def bench_metric(X, name, params, frames, budget):
    R = X.shape[1]
    cols = [X[:, k] for k in range(R)]
    # single pair
    b, how = before_estimate(cols, [(0, 1)], name, params, 1)
    s1 = timed(lambda: et.paired_distances([cols[0]], [cols[1]], name, n_jobs=1, **params))
    add(name, "single_pair", frames, 1, b, how, s1, s1)
    # one vs all ROIs
    pairs = [(0, j) for j in range(R)]
    b, how = before_estimate(cols, pairs, name, params, budget)
    s1 = timed(lambda: et.one_vs_many(cols[0], X, name, n_jobs=1, **params))
    sN = timed(lambda: et.one_vs_many(cols[0], X, name, n_jobs=THREADS, **params))
    add(name, f"one_vs_{R}", frames, R, b, how, s1, sN)
    # all pairs (upper triangle incl. diagonal, as pairwise_distance_matrix computes)
    I, J = np.triu_indices(R)
    pairs = list(zip(I.tolist(), J.tolist()))
    b, how = before_estimate(cols, pairs, name, params, budget)
    s1 = timed(lambda: et.pairwise_distance_matrix(X, name, n_jobs=1, **params))
    sN = timed(lambda: et.pairwise_distance_matrix(X, name, n_jobs=THREADS, **params))
    add(name, f"all_pairs_{R}x{R}", frames, len(pairs), b, how, s1, sN)


def main() -> None:
    print(et.similarity_backend_info(), flush=True)
    A = load(DATA / "aomic_id1000/sub-0001_task-moviewatching_Schaefer400_raw.npy")
    B = load(DATA / "nndb/sub-10_task-500daysofsummer_Schaefer400_nbnc.npy")
    for name in SINGLE:
        params = {"window": 10} if name == "dtw" else {}
        bench_metric(A, name, params, 290, budget=40 if name in {"lcss", "edr", "erp", "twed", "dtw"} else 2000)
    # 5,470 frames: shift-based on all 400 ROIs; elastic banded (window 20 s) on 400 ROIs, unbanded on 30 ROIs.
    bench_metric(B, "sbd", {}, 5470, budget=300)
    bench_metric(B, "best_shift", {}, 5470, budget=300)
    for name in ("twed", "erp", "dtw", "edr", "lcss"):
        bench_metric(B, name, {"window": 20}, 5470, budget=20)
    for name in ("twed", "dtw"):
        bench_metric(B[:, :30], name, {}, 5470, budget=1)
    # profile_series per ROI and profile_dataset on 400 ROIs.
    for frames, X in ((290, A), (5470, B)):
        _native.set_similarity_backend("python")
        b = timed(lambda: [et.profile_series(X[:, k]) for k in range(3)]) / 3
        _native.set_similarity_backend(None)
        a = timed(lambda: [et.profile_series(X[:, k]) for k in range(20)]) / 20
        add("profile_series", "per_roi", frames, 1, b, "measured_3_rois", a, a)
    data = et.FMRIInput(A, tr=2.2, timestamps=np.arange(A.shape[0]) * 2.2, roi_names=[f"r{i}" for i in range(400)], subject_ids=["s"], time_axis=0, channel_axis=-1)
    small = et.FMRIInput(A[:, :20], tr=2.2, timestamps=np.arange(A.shape[0]) * 2.2, roi_names=[f"r{i}" for i in range(20)], subject_ids=["s"], time_axis=0, channel_axis=-1)
    _native.set_similarity_backend("python")
    b20 = timed(lambda: et.profile_dataset(small, bootstrap=0, random_state=0))
    _native.set_similarity_backend(None)
    a400 = timed(lambda: et.profile_dataset(data, bootstrap=0, random_state=0))
    # before for 400 ROIs: per-ROI part scales with R, pairwise-correlation part with R^2
    add("profile_dataset", "400_rois", 290, 400, b20 * 20, "extrapolated_from_20_rois_x20_(lower_bound:_ignores_R^2_term)", a400, a400)
    x, y = A[:, 0], A[:, 1]
    _native.set_similarity_backend("python")
    b = timed(lambda: et.compare_series(x, y))
    br = timed(lambda: et.rolling_similarity(x, y, window=60, step=5))
    _native.set_similarity_backend(None)
    add("compare_series", "single_pair", 290, 1, b, "measured", timed(lambda: et.compare_series(x, y)), float("nan"))
    add("rolling_similarity", "window60_step5", 290, 47, br, "measured", timed(lambda: et.rolling_similarity(x, y, window=60, step=5)), float("nan"))
    with open(OUT, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
