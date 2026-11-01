"""Same TWED and DTW kernels in C++ (pybind11), Cython (prange) and numba.

Purpose: justify the toolchain choice in docs/performance.md with measured
speed, threading, build cost and exactness. Workload: all 2,016 pairs of 64
ID1000 ROIs (290 frames, univariate, no band).

    python compare_backends.py cpp_cython   # in the EchoTime dev venv
    python compare_backends.py numba        # in a venv with numba

Each run appends to benchmarks/backend_comparison_2026-11.csv; the C++ run
saves its outputs so the other runs can check bit-identity.
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

import numpy as np
from scipy.signal import detrend

HERE = Path(__file__).resolve().parent
OUT = HERE / "backend_comparison_2026-11.csv"
REF = HERE / "logs" / "backend_comparison_cpp_outputs.npz"
DATA = Path(os.environ.get("FMRI_REPO", "/rds/projects/s/spillf-systems-mechanobiology-health-disease/Zipeng/fmri_repo")) / "data/roi_timeseries_raw/aomic_id1000/sub-0001_task-moviewatching_Schaefer400_raw.npy"
THREADS = len(os.sched_getaffinity(0))
NU, LAMBDA = 0.001, 1.0


def workload():
    x = np.load(DATA).astype(np.float64)  # stored as (time, roi)
    x = detrend(x, axis=0)
    x = (x - x.mean(0)) / x.std(0)
    X = np.ascontiguousarray(x[:, :64].T)  # (series, time)
    I, J = np.triu_indices(64, k=1)
    return X, I.astype(np.int64), J.astype(np.int64)


def twed_terms(X):
    """Per-series TWED terms exactly as similarity_methods._twed_side (univariate)."""
    n = X.shape[1]
    t = np.arange(1, n + 1, dtype=float)
    prev = np.concatenate([np.zeros((X.shape[0], 1)), X[:, :-1]], axis=1)
    prev_t = np.concatenate([[0.0], t[:-1]])
    delete = np.abs(X - prev) + NU * np.abs(t - prev_t) + LAMBDA
    return prev, t, prev_t, delete


def write(row):
    new = not OUT.exists()
    with open(OUT, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(row))
        if new:
            writer.writeheader()
        writer.writerow(row)
    print(row, flush=True)


def timeit(fn, repeat=3):
    best = np.inf
    out = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        out = fn()
        best = min(best, time.perf_counter() - t0)
    return best, out


# ----------------------------------------------------------------- C++ ----
def run_cpp(X, I, J):
    import echotime
    from echotime import _native, similarity_methods as sm

    ext = _native.ext()
    series = [X[k].reshape(-1, 1) for k in range(X.shape[0])]
    values, offsets = sm._bank(series, 1)
    sides = [sm._twed_side(s, None, lambda_=LAMBDA, nu=NU) for s in series]
    pv, _ = sm._bank([s[1] for s in sides], 1)
    t = sm._rows([s[2] for s in sides]); tp = sm._rows([s[3] for s in sides]); de = sm._rows([s[4] for s in sides])
    outputs = {}
    for name, call in (
        ("twed", lambda th: ext.twed_pairs(values, pv, offsets, t, tp, de, values, pv, offsets, t, tp, de, I, J, NU, -1, False, th)),
        ("dtw", lambda th: ext.dtw_pairs(values, offsets, values, offsets, I, J, -1, th)),
    ):
        t1, out1 = timeit(lambda: call(1))
        tn, outn = timeit(lambda: call(THREADS))
        outputs[name] = out1
        write({"impl": "cpp_pybind11_lanes_simd", "kernel": name, "pairs": len(I), "frames": X.shape[1], "build_or_jit_s": "ahead-of-time",
               "t_1thread_s": round(t1, 4), "threads": THREADS, "t_nthreads_s": round(tn, 4),
               "bit_identical_to_cpp": True, "threads_identical": bool(np.array_equal(out1, outn)), "echotime": echotime.__version__})
    REF.parent.mkdir(exist_ok=True)
    np.savez(REF, **outputs)
    return outputs


# -------------------------------------------------------------- Cython ----
CYTHON_SRC = textwrap.dedent(r'''
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=False, initializedcheck=False
from cython.parallel import prange
from libc.math cimport fabs, INFINITY
from libc.stdlib cimport malloc, free
import numpy as np

cdef inline double min3(double a, double b, double c) noexcept nogil:
    cdef double r = a
    if b < r: r = b
    if c < r: r = c
    return r

cdef double twed_one(const double[:, ::1] X, const double[:, ::1] P, const double[::1] t, const double[::1] tp,
                     const double[:, ::1] D, long a, long b, double nu, double* prev, double* curr) noexcept nogil:
    cdef long n = X.shape[1], m = X.shape[1], i, j
    cdef double* tmp
    for j in range(m + 1):
        prev[j] = INFINITY
    prev[0] = 0.0
    for i in range(1, n + 1):
        for j in range(m + 1):
            curr[j] = INFINITY
        for j in range(1, m + 1):
            curr[j] = min3(prev[j] + D[a, i - 1], curr[j - 1] + D[b, j - 1],
                           prev[j - 1] + fabs(X[b, j - 1] - X[a, i - 1]) + fabs(P[b, j - 1] - P[a, i - 1])
                           + nu * (fabs(t[i - 1] - t[j - 1]) + fabs(tp[i - 1] - tp[j - 1])))
        tmp = prev; prev = curr; curr = tmp
    return prev[m]

cdef double dtw_one(const double[:, ::1] X, long a, long b, double* prev, double* curr) noexcept nogil:
    cdef long n = X.shape[1], m = X.shape[1], i, j
    cdef double* tmp
    for j in range(m + 1):
        prev[j] = INFINITY
    prev[0] = 0.0
    for i in range(1, n + 1):
        for j in range(m + 1):
            curr[j] = INFINITY
        for j in range(1, m + 1):
            curr[j] = fabs(X[b, j - 1] - X[a, i - 1]) + min3(prev[j], curr[j - 1], prev[j - 1])
        tmp = prev; prev = curr; curr = tmp
    return prev[m]

def twed_pairs(const double[:, ::1] X, const double[:, ::1] P, const double[::1] t, const double[::1] tp,
               const double[:, ::1] D, const long[::1] I, const long[::1] J, double nu, int threads):
    cdef long K = I.shape[0], k, m = X.shape[1]
    out = np.empty(K)
    cdef double[::1] o = out
    cdef double* prev
    cdef double* curr
    for k in prange(K, nogil=True, num_threads=threads, schedule="dynamic"):
        prev = <double*> malloc((m + 1) * sizeof(double))
        curr = <double*> malloc((m + 1) * sizeof(double))
        o[k] = twed_one(X, P, t, tp, D, I[k], J[k], nu, prev, curr)
        free(prev); free(curr)
    return out

def dtw_pairs(const double[:, ::1] X, const long[::1] I, const long[::1] J, int threads):
    cdef long K = I.shape[0], k, m = X.shape[1]
    out = np.empty(K)
    cdef double[::1] o = out
    cdef double* prev
    cdef double* curr
    for k in prange(K, nogil=True, num_threads=threads, schedule="dynamic"):
        prev = <double*> malloc((m + 1) * sizeof(double))
        curr = <double*> malloc((m + 1) * sizeof(double))
        o[k] = dtw_one(X, I[k], J[k], prev, curr)
        free(prev); free(curr)
    return out
''')


def run_cython(X, I, J):
    build = Path(tempfile.mkdtemp(prefix="et_cython_", dir=os.environ.get("TMPDIR")))
    (build / "et_cy.pyx").write_text(CYTHON_SRC)
    (build / "setup.py").write_text(textwrap.dedent('''
        from setuptools import setup, Extension
        from Cython.Build import cythonize
        import numpy
        ext = Extension("et_cy", ["et_cy.pyx"], extra_compile_args=["-O3", "-fopenmp", "-ffp-contract=off", "-march=x86-64-v3"],
                        extra_link_args=["-fopenmp"], include_dirs=[numpy.get_include()])
        setup(ext_modules=cythonize([ext], quiet=True))
    '''))
    t0 = time.perf_counter()
    subprocess.run([sys.executable, "setup.py", "build_ext", "--inplace", "-q"], cwd=build, check=True, capture_output=True)
    build_s = time.perf_counter() - t0
    sys.path.insert(0, str(build))
    import et_cy  # noqa: E402

    ref = np.load(REF)
    P, t, tp, D = twed_terms(X)
    for name, call in (
        ("twed", lambda th: et_cy.twed_pairs(X, np.ascontiguousarray(P), t, tp, np.ascontiguousarray(D), I, J, NU, th)),
        ("dtw", lambda th: et_cy.dtw_pairs(X, I, J, th)),
    ):
        t1, out1 = timeit(lambda: call(1))
        tn, outn = timeit(lambda: call(THREADS))
        write({"impl": "cython_prange_openmp", "kernel": name, "pairs": len(I), "frames": X.shape[1], "build_or_jit_s": round(build_s, 1),
               "t_1thread_s": round(t1, 4), "threads": THREADS, "t_nthreads_s": round(tn, 4),
               "bit_identical_to_cpp": bool(np.array_equal(out1, ref[name])), "threads_identical": bool(np.array_equal(out1, outn)), "echotime": "n/a"})


# --------------------------------------------------------------- numba ----
def run_numba(X, I, J):
    import numba
    from numba import njit, prange

    @njit(cache=False, fastmath=False)
    def min3(a, b, c):
        r = a
        if b < r:
            r = b
        if c < r:
            r = c
        return r

    @njit(parallel=True, fastmath=False)
    def twed_pairs(X, P, t, tp, D, I, J, nu):
        K = I.shape[0]
        m = X.shape[1]
        out = np.empty(K)
        for k in prange(K):
            a, b = I[k], J[k]
            prev = np.full(m + 1, np.inf)
            curr = np.full(m + 1, np.inf)
            prev[0] = 0.0
            for i in range(1, m + 1):
                curr[:] = np.inf
                for j in range(1, m + 1):
                    curr[j] = min3(prev[j] + D[a, i - 1], curr[j - 1] + D[b, j - 1],
                                   prev[j - 1] + abs(X[b, j - 1] - X[a, i - 1]) + abs(P[b, j - 1] - P[a, i - 1])
                                   + nu * (abs(t[i - 1] - t[j - 1]) + abs(tp[i - 1] - tp[j - 1])))
                prev, curr = curr, prev
            out[k] = prev[m]
        return out

    @njit(parallel=True, fastmath=False)
    def dtw_pairs(X, I, J):
        K = I.shape[0]
        m = X.shape[1]
        out = np.empty(K)
        for k in prange(K):
            a, b = I[k], J[k]
            prev = np.full(m + 1, np.inf)
            curr = np.full(m + 1, np.inf)
            prev[0] = 0.0
            for i in range(1, m + 1):
                curr[:] = np.inf
                for j in range(1, m + 1):
                    curr[j] = abs(X[b, j - 1] - X[a, i - 1]) + min3(prev[j], curr[j - 1], prev[j - 1])
                prev, curr = curr, prev
            out[k] = prev[m]
        return out

    ref = np.load(REF)
    P, t, tp, D = twed_terms(X)
    for name, call in (("twed", lambda: twed_pairs(X, P, t, tp, D, I, J, NU)), ("dtw", lambda: dtw_pairs(X, I, J))):
        numba.set_num_threads(1)
        t0 = time.perf_counter()
        call()  # JIT compile
        jit_s = time.perf_counter() - t0
        t1, out1 = timeit(call)
        numba.set_num_threads(THREADS)
        tn, outn = timeit(call)
        write({"impl": f"numba_{numba.__version__}_prange", "kernel": name, "pairs": len(I), "frames": X.shape[1], "build_or_jit_s": round(jit_s, 1),
               "t_1thread_s": round(t1, 4), "threads": THREADS, "t_nthreads_s": round(tn, 4),
               "bit_identical_to_cpp": bool(np.array_equal(out1, ref[name])), "threads_identical": bool(np.array_equal(out1, outn)), "echotime": "n/a"})


if __name__ == "__main__":
    X, I, J = workload()
    mode = sys.argv[1]
    if mode == "cpp_cython":
        run_cpp(X, I, J)
        run_cython(X, I, J)
    elif mode == "numba":
        run_numba(X, I, J)
    else:
        raise SystemExit("usage: compare_backends.py cpp_cython|numba")
