# CPU performance (0.18.0.dev0)

This page records what was accelerated, how, and how the results were checked.
Numbers come from `benchmarks/perf_2026-11.csv`,
`benchmarks/backend_comparison_2026-11.csv` and
`benchmarks/validation_real_2026-11.csv`. They were measured on BlueBEAR
Ice Lake nodes, 32 allocated cores, on real fMRI data:
- AOMIC ID1000: 290 frames × 400 Schaefer ROIs.
- NNDb: 5,470 frames × 400 ROIs.

## The rule: the numbers do not change

The pure-Python code remains the reference definition of every metric. An
accelerated path has to reproduce it in one of two ways.

**Bit for bit:**
- LCSS, EDR, ERP, TWED and DTW;
- `max_ncc`, `sbd` and `best_shift`, including their independent variants;
- sample-entropy template counts;
- ordinal-pattern counts and permutation entropy.

The C++ kernels perform the reference's floating-point operations in the
reference's order:
- same operands;
- no `-ffast-math`;
- `-ffp-contract=off`, so there is no FMA contraction;
- numpy's pairwise summation is reproduced for multichannel row norms.

**Within rounding (≤ 1e-12, observed ≤ 5e-16):**
- ACF, periodogram, trend, ordinal-JS and linear-trend-model distances in the batch APIs;
- the all-pairs correlation summary inside `compute_multivariate_metrics`.

These paths vectorise a norm or a mean that the reference computes element
by element.

`tests/test_native_equivalence.py` enforces both rules on randomised inputs:
- lengths from 2 to 6,000, equal and unequal;
- 1 to 9 channels;
- constant series and dropped NaN rows;
- every parameter variant, TWED timestamps and fast mode;
- 1 versus 8 threads.

`benchmarks/validate_real_data.py` repeats the checks on the two real runs.

## Which technique for which function

| Function | Before (0.17.x) | Technique | Why this technique |
|---|---|---|---|
| `lcss_*`, `edr_distance`, `erp_distance`, `twed_distance`, new `dtw_distance` | Python loop over every DP cell (about 1 µs per cell) | C++ kernel. Univariate pairs of equal length run 8 at a time in SIMD lanes, other pairs in a scalar kernel. Threads run over pairs and the GIL is released. | The DP recurrence is sequential within a pair, so speed comes from running many pairs side by side. Each lane performs the scalar operations, so results stay bit-identical. |
| `max_ncc`, `sbd`, `best_shift` (batch) | `np.correlate` per pair, O(n·m) | One rFFT per series and one inverse FFT per pair. The top lags are then recomputed with the same `ddot` calls that `np.correlate` makes. | FFT makes this O((n+m) log(n+m)), and the exact recomputation keeps values and argmax lags bit-identical. Single-pair calls keep `np.correlate`, which is already fast. |
| `acf`, `periodogram`, `trend`, `ordinal_js`, `linear_trend_model` (batch) | Both embeddings recomputed for every pair | Each series is embedded once, then pairwise norms are vectorised. | The cost is dominated by repeated embedding, so compiled code is not needed. |
| `ordinal_pattern_js_distance`, `permutation_entropy` | Python loop with one `argsort` per window | One stable row-wise `argsort` plus `bincount`, in first-seen order. | Same sort and same counts, about 50 times fewer Python calls. |
| `sample_entropy`, used by `profile_series` and `profile_dataset` | O(n²·m) Python loop (≈0.5 s per series) | C++ template counts. Python does the final division and log as before. | This was about 90 % of profiling time. |
| `compute_multivariate_metrics` | R(R−1)/2 calls to `np.corrcoef`, again for every window | One centred cross-product per window, then numpy's division and clipping steps. | O(R²) Python calls became O(1) BLAS calls. It falls back to the loop when values are non-finite. |
| `lz_complexity` | Median recomputed for every sample | Median computed once. | Pure algorithmic waste; same result. |
| `compare_series` / `rolling_similarity` | Python DTW | Native DTW kernel. | Bit-identical; the rest of the comparison is unchanged. |

## C++ versus Cython versus numba

The TWED and DTW kernels were written three ways with identical arithmetic
(`benchmarks/compare_backends.py`). The workload was all 2,016 pairs of 64
ID1000 ROIs at 290 frames. Every implementation was bit-identical to the
others. Single-thread times were stable across three runs; 32-thread ranges
span the runs.

| Implementation | Build cost | TWED 1 thread | TWED 32 threads | DTW 1 thread | DTW 32 threads |
|---|---|---|---|---|---|
| C++ scalar kernel (pybind11, std::thread) | compiled at install | 0.656 s | 0.031 s | 0.619 s | 0.030 s |
| Cython `prange` (OpenMP) | 8 s compile, needs Cython and OpenMP | 0.672 s | 0.021–0.042 s | 0.666 s | 0.021–0.031 s |
| numba 0.68 `prange` | 1.3–2.4 s JIT on every new process | 0.670 s | 0.021–0.050 s | 0.667 s | 0.021 s |
| **C++ lane kernel (8 pairs per SIMD group; shipped)** | compiled at install | **0.155 s** | **0.006 s** | **0.137 s** | **0.005–0.006 s** |

The three scalar kernels run at the same speed. The DP chain is
latency-bound, so the language does not matter; the 4× gain comes from the
lane layout. C++ was chosen for four reasons:

1. **Same toolchain as DeTime.** DeTime already uses pybind11 and C++17, so
   the user's packages share one toolchain.
2. **No runtime dependency.** Numba would pull in llvmlite (about 100 MB) and
   lags numpy releases; EchoTime's own `mixed-stack` profile already pins
   `numba<0.62`. Numba also adds JIT start-up in every worker process, which
   matters for Slurm arrays.
3. **No OpenMP runtime.** `std::thread` builds unchanged with clang on macOS
   and with MSVC; Cython's `prange` needs libomp on macOS.
4. **Explicit SIMD control.** GCC/Clang vector extensions give explicit SIMD
   with bitwise selects, so lane results provably equal the scalar kernel.
   Other compilers fall back to the same code on scalars.

## Speed-ups on real data

See `benchmarks/perf_2026-11.csv` (filled by `benchmarks/perf_2026_11.py`).
In that file:
- "before" is the 0.17.x Python path. It is extrapolated linearly from a
  timed sample of pairs where running it in full would take hours; the
  `before_measured` column says which.
- "after" is always the full workload.

| Function | Workload | Frames | Pairs | Before (Python) | After, 1 thread | After, 32 threads | Speed-up (1 / 32 threads) |
|---|---|---|---|---|---|---|---|
| `sbd` | single_pair | 290 | 1 | 0.3 ms | 0.6 ms | 0.6 ms | 1× / 1× |
| `sbd` | one_vs_400 | 290 | 400 | 40.3 ms | 29.4 ms | 30.6 ms | 1× / 1× |
| `sbd` | all_pairs_400x400 | 290 | 80200 | 8.2 s* | 2.0 s | 1.7 s | 4× / 5× |
| `best_shift` | single_pair | 290 | 1 | 0.3 ms | 0.4 ms | 0.4 ms | 1× / 1× |
| `best_shift` | one_vs_400 | 290 | 400 | 39.7 ms | 28.7 ms | 27.9 ms | 1× / 1× |
| `best_shift` | all_pairs_400x400 | 290 | 80200 | 8.0 s* | 3.7 s | 3.3 s | 2× / 2× |
| `lcss` | single_pair | 290 | 1 | 23.9 ms | 0.5 ms | 0.5 ms | 44× / 44× |
| `lcss` | one_vs_400 | 290 | 400 | 9.5 s* | 19.7 ms | 6.1 ms | 482× / 1,545× |
| `lcss` | all_pairs_400x400 | 290 | 80200 | 31.7 min* | 3.0 s | 138.7 ms | 630× / 13,724× |
| `edr` | single_pair | 290 | 1 | 49.8 ms | 0.5 ms | 0.5 ms | 96× / 96× |
| `edr` | one_vs_400 | 290 | 400 | 19.8 s* | 33.5 ms | 6.5 ms | 590× / 3,058× |
| `edr` | all_pairs_400x400 | 290 | 80200 | 1.1 h* | 5.8 s | 233.0 ms | 688× / 17,114× |
| `erp` | single_pair | 290 | 1 | 62.5 ms | 0.4 ms | 0.4 ms | 146× / 146× |
| `erp` | one_vs_400 | 290 | 400 | 25.3 s* | 23.6 ms | 7.2 ms | 1,075× / 3,515× |
| `erp` | all_pairs_400x400 | 290 | 80200 | 1.4 h* | 3.6 s | 168.0 ms | 1,373× / 29,782× |
| `twed` | single_pair | 290 | 1 | 84.1 ms | 0.6 ms | 0.6 ms | 135× / 135× |
| `twed` | one_vs_400 | 290 | 400 | 32.3 s* | 42.6 ms | 17.8 ms | 759× / 1,821× |
| `twed` | all_pairs_400x400 | 290 | 80200 | 1.8 h* | 6.2 s | 274.3 ms | 1,037× / 23,605× |
| `dtw` | single_pair | 290 | 1 | 4.0 ms | 0.2 ms | 0.2 ms | 22× / 22× |
| `dtw` | one_vs_400 | 290 | 400 | 1.5 s* | 6.1 ms | 5.2 ms | 250× / 296× |
| `dtw` | all_pairs_400x400 | 290 | 80200 | 5.1 min* | 389.5 ms | 46.8 ms | 788× / 6,547× |
| `acf` | single_pair | 290 | 1 | 0.3 ms | 0.3 ms | 0.3 ms | 1× / 1× |
| `acf` | one_vs_400 | 290 | 400 | 37.3 ms | 20.6 ms | 20.3 ms | 2× / 2× |
| `acf` | all_pairs_400x400 | 290 | 80200 | 7.4 s* | 181.4 ms | 181.9 ms | 41× / 41× |
| `periodogram` | single_pair | 290 | 1 | 0.3 ms | 0.2 ms | 0.2 ms | 1× / 1× |
| `periodogram` | one_vs_400 | 290 | 400 | 23.3 ms | 13.1 ms | 12.8 ms | 2× / 2× |
| `periodogram` | all_pairs_400x400 | 290 | 80200 | 4.7 s* | 161.9 ms | 162.3 ms | 29× / 29× |
| `ordinal_js` | single_pair | 290 | 1 | 0.4 ms | 0.3 ms | 0.3 ms | 1× / 1× |
| `ordinal_js` | one_vs_400 | 290 | 400 | 52.0 ms | 23.9 ms | 23.9 ms | 2× / 2× |
| `ordinal_js` | all_pairs_400x400 | 290 | 80200 | 10.4 s* | 187.6 ms | 188.6 ms | 55× / 55× |
| `trend` | single_pair | 290 | 1 | 0.5 ms | 0.4 ms | 0.4 ms | 2× / 2× |
| `trend` | one_vs_400 | 290 | 400 | 63.9 ms | 33.1 ms | 33.1 ms | 2× / 2× |
| `trend` | all_pairs_400x400 | 290 | 80200 | 12.9 s* | 192.9 ms | 194.4 ms | 67× / 66× |
| `sbd` | single_pair | 5470 | 1 | 6.3 ms | 0.9 ms | 0.9 ms | 7× / 7× |
| `sbd` | one_vs_400 | 5470 | 400 | 2.8 s* | 140.4 ms | 119.2 ms | 20× / 24× |
| `sbd` | all_pairs_400x400 | 5470 | 80200 | 9.5 min* | 13.9 s | 8.9 s | 41× / 64× |
| `best_shift` | single_pair | 5470 | 1 | 7.3 ms | 0.8 ms | 0.8 ms | 9× / 9× |
| `best_shift` | one_vs_400 | 5470 | 400 | 2.8 s* | 140.4 ms | 114.4 ms | 20× / 25× |
| `best_shift` | all_pairs_400x400 | 5470 | 80200 | 9.5 min* | 27.7 s | 17.7 s | 21× / 32× |
| `twed` | single_pair | 5470 | 1 | 258.6 ms | 1.3 ms | 1.3 ms | 196× / 196× |
| `twed` | one_vs_400 | 5470 | 400 | 1.7 min* | 156.3 ms | 86.9 ms | 660× / 1,186× |
| `twed` | all_pairs_400x400 | 5470 | 80200 | 5.7 h* | 19.3 s | 875.1 ms | 1,068× / 23,604× |
| `erp` | single_pair | 5470 | 1 | 193.6 ms | 0.8 ms | 0.8 ms | 244× / 244× |
| `erp` | one_vs_400 | 5470 | 400 | 1.3 min* | 84.7 ms | 33.6 ms | 913× / 2,302× |
| `erp` | all_pairs_400x400 | 5470 | 80200 | 4.3 h* | 11.0 s | 456.3 ms | 1,406× / 33,977× |
| `dtw` | single_pair | 5470 | 1 | 133.7 ms | 0.8 ms | 0.8 ms | 160× / 160× |
| `dtw` | one_vs_400 | 5470 | 400 | 53.2 s* | 92.9 ms | 27.8 ms | 572× / 1,914× |
| `dtw` | all_pairs_400x400 | 5470 | 80200 | 3.0 h* | 14.1 s | 579.8 ms | 767× / 18,611× |
| `edr` | single_pair | 5470 | 1 | 163.9 ms | 1.0 ms | 1.0 ms | 167× / 167× |
| `edr` | one_vs_400 | 5470 | 400 | 1.1 min* | 99.3 ms | 27.7 ms | 657× / 2,360× |
| `edr` | all_pairs_400x400 | 5470 | 80200 | 3.6 h* | 15.5 s | 645.9 ms | 840× / 20,219× |
| `lcss` | single_pair | 5470 | 1 | 90.7 ms | 1.5 ms | 1.5 ms | 62× / 62× |
| `lcss` | one_vs_400 | 5470 | 400 | 35.9 s* | 62.4 ms | 24.8 ms | 575× / 1,449× |
| `lcss` | all_pairs_400x400 | 5470 | 80200 | 2.0 h* | 8.2 s | 352.8 ms | 886× / 20,473× |
| `twed` | single_pair | 5470 | 1 | 28.2 s | 113.2 ms | 113.2 ms | 249× / 249× |
| `twed` | one_vs_30 | 5470 | 30 | 14.1 min* | 1.9 s | 455.1 ms | 439× / 1,859× |
| `twed` | all_pairs_30x30 | 5470 | 465 | 3.6 h* | 24.2 s | 1.8 s | 543× / 7,368× |
| `dtw` | single_pair | 5470 | 1 | 16.2 s | 112.6 ms | 112.6 ms | 144× / 144× |
| `dtw` | one_vs_30 | 5470 | 30 | 8.1 min* | 1.2 s | 191.0 ms | 391× / 2,543× |
| `dtw` | all_pairs_30x30 | 5470 | 465 | 2.0 h* | 11.0 s | 497.0 ms | 666× / 14,811× |
| `profile_series` | per_roi | 290 | 1 | 323.8 ms | 20.0 ms | 20.0 ms | 16× / 16× |
| `profile_series` | per_roi | 5470 | 1 | 1.3 s | 151.9 ms | 151.9 ms | 8× / 8× |
| `profile_dataset` | 400_rois | 290 | 400 | 2.2 min* | 8.9 s | 8.9 s | 15× / 15× |
| `compare_series` | single_pair | 290 | 1 | 19.3 ms | 8.0 ms | – | 2× |
| `rolling_similarity` | window60_step5 | 290 | 47 | 407.2 ms | 268.3 ms | – | 2× |

\* Extrapolated linearly from a timed sample of pairs (see `before_measured`).

## Using it

```python
import echotime as et

et.similarity_backend_info()                     # which kernels run, thread default
D = et.pairwise_distance_matrix(X, "twed")       # X is (time, n_roi); columns are series
v = et.one_vs_many(group_mean, X, "sbd")         # one series against every ROI
d = et.paired_distances(subject_rois, mean_rois, "erp", window=10)
```

| Setting | Effect |
|---|---|
| `ECHOTIME_BACKEND=python` or `et.set_similarity_backend("python")` | Forces the reference implementation |
| `ECHOTIME_NUM_THREADS` or `n_jobs=` | Sets the thread count. The default is the CPUs in the process affinity mask, which respects Slurm allocations. |

### Building

The extension is optional. If it cannot be compiled, installation still
succeeds and EchoTime runs the Python reference.

| Platform | Flags |
|---|---|
| Linux x86-64 | `-O3 -fno-fast-math -ffp-contract=off -march=x86-64-v3` (AVX2) |
| Override the target level | `ECHOTIME_NATIVE_MARCH=x86-64-v2`, or `none` to keep the toolchain default |
| macOS / Windows | Same C++ code, compiler-default target |

A `-march=native` inherited from the Python build is overridden, so one build
runs on every node of a cluster.

## Reading the table

- **Elastic distances.** All 400×400 pairs on one 290-frame run took 5 min to
  1.8 h in Python. They now take 0.05–0.3 s on 32 cores, and 0.4–0.9 s at
  5,470 frames with a 20-sample band. Unbanded 5,470-frame DP costs about
  0.11 s per pair on one core.
- **Shift-based correlation.**
  - One pair: the single-pair functions still use `np.correlate`, which is
    already fast at fMRI lengths. A batch call on one pair is slower than the
    single-pair function.
  - Many pairs: the batch path wins 4–5× for all pairs at 290 frames and
    20–64× at 5,470 frames.
  - The exact top-lag recomputation is a serial Python loop costing about
    20 µs per pair. That is why 32 threads add little here.
- **Embedding distances.** All pairs are 30–70× faster because each
  embedding is computed once.
- **Profiles.**
  - `profile_series`: 16× faster at 290 frames and 8× at 5,470 frames.
  - `profile_dataset` on 400 ROIs: 8.9 s instead of more than 2.2 min. The
    2.2 min "before" figure is a lower bound: it scales the 20-ROI time
    linearly and ignores the O(R²) correlation loop.

## Not changed

- `profile_series` now spends most of its remaining ~20 ms per ROI on
  `acf_periodic_peak` and `hurst_exponent_rs`. Both make many small numpy calls.
- `rolling_similarity` still builds a full `compare_series` report for every
  window.
- DeTime's neural `*_BLOCK` methods are out of scope (they belong to DeTime).
