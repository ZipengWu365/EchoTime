# Local acceleration evidence

These files record a CPU development-session check of the acceleration work.
They establish small-case correctness and measured local timings. Server-scale
throughput, population recall, production tail latency, and an EchoTime GPU
backend remain unverified by these runs.

For the final complete tests, package builds and installation checks, see
[the validation summary](validation-summary.md).

## Evidence inventory

| Evidence | Purpose and outcome |
|---|---|
| [baseline-smoke.json](baseline-smoke.json), [report](baseline-smoke.md) | Original `08f7df7` checkout: 28 available cases passed; 11 newly introduced APIs were unavailable |
| [current-smoke.json](current-smoke.json), [report](current-smoke.md) | Final local implementation: 39 cases passed, zero unavailable/errors |
| [baseline-quick.json](baseline-quick.json), [report](baseline-quick.md) | Original checkout: 31 available cases passed; 14 new API cases were unavailable |
| [current-quick.json](current-quick.json), [report](current-quick.md) | Final local implementation: 45 cases passed, zero unavailable/errors |
| [current-search-confirmation.json](current-search-confirmation.json), [report](current-search-confirmation.md) | Independent focused timing check after variable DTW brute-force timings appeared in the full quick run: all 6 cases passed |
| [baseline-initial-quick.json](baseline-initial-quick.json), [initial implementation](current-initial-quick.json) | Preserved first matched experiment, including the slow initial automatic bounds policy |
| [baseline-initial-smoke.json](baseline-initial-smoke.json), [initial implementation](current-initial-smoke.json) | Preserved first smoke experiment |
| [current-quick-bounds-none.json](current-quick-bounds-none.json), [cheap bounds](current-quick-bounds-cheap.json) | Separate diagnostic configurations exposing the cost of Python bounds; each passed all 6 search cases |
| [current-dtw-auto-simd.json](current-dtw-auto-simd.json), [report](current-dtw-auto-simd.md) | DTW-only check of the revised cached native scan policy; all 3 cases passed |
| [gpu-probe-local.json](gpu-probe-local.json) | Hardware-readiness probe reported `unavailable`; no GPU computation was performed |

The JSON files contain all measured samples, metadata, result summaries, quality
checks, and unavailable/error reasons. Each benchmark JSON has a same-name
Markdown report. No slow or low-recall initial result was replaced with a more
favorable number.

## Measurement conditions

The final baseline/current smoke and quick runs use the same harness SHA256:

```text
813703e98ebceec801f4c7e8d7ad2a1b9e8fd5a90fa1f5587df6ea94496c2d82
```

The pristine baseline is
`08f7df742b364175105e957d39f9f81fe6211bb3`, measured through an explicit
`--source-tree` pointing at its separate checkout and original native extension.
The development results were collected before committing the complete feature
branch, so `source_dirty=true` is intentional. Their Git HEAD alone does not
identify the measured implementation: use the recorded per-file Python, build
source, and compiled-extension SHA256 values as well. The original fixture
capture was made before modifying tracked reference source files.

The measured environment reports an AMD EPYC 9V74 80-Core Processor, with nine
CPUs available in process affinity; Python 3.12.14, NumPy 2.3.5, and SciPy 1.17.0.
EchoTime used the native backend with `n_jobs=1` and
`ECHOTIME_NUM_THREADS=1`. The BLAS/OpenMP thread environment variables were
unset and are recorded as such. This shared environment was not an isolated
performance lab. Team CPU-heavy tests were paused for the final measurements;
unrelated host load, scheduling, and thermal state were not controlled.

The main runs measured five warm calls after one additional warmup, using seed
`20261104`. The focused confirmation used nine warm calls and two warmups. Each
search case repeated the same query and candidate bank; these are latency
samples for one query, not independent recall trials.

The initial evidence used an earlier harness revision. The later harness adds
the optional `faiss_hnsw` CLI choice and optional-dependency inventory; the
original and development packages were remeasured together under the final
harness. The earlier matched files remain available for the regression diagnosis.

## Existing API observations

The following are p50 milliseconds from the final matched quick runs. A speedup
below 1 means the current observation was slower. All cases retain their original
API output contract.

| Case | Original p50 (ms) | Current p50 (ms) | Original / current |
|---|---:|---:|---:|
| Full `compare_series`, T=290 | 7.412 | 7.555 | 0.98× |
| Full `compare_series`, T=1024 | 8.146 | 6.314 | 1.29× |
| Full rolling, T=290/window=60/step=5, 47 windows | 277.052 | 134.494 | 2.06× |
| `profile_dataset`, T=96/channels=8 | 109.214 | 54.968 | 1.99× |

These observations do not establish a universal 3× improvement. The original
profile samples ranged from 81.795 to 121.116 ms, whereas the current samples
ranged from 53.630 to 57.087 ms. The small sample count and shared host limit how
precisely the observed ratio should be interpreted.

Several other final quick cases showed apparent regressions and are retained:

| Case | Original / current p50 |
|---|---:|
| EDR, N=64/T=128, unrestricted | 0.82× |
| TWED, N=64/T=128, unrestricted | 0.82× |
| Trend distance, N=64/T=128 | 0.75× |
| Pairwise DTW, N=32/T=128/window=16 | 0.86× |
| Pairwise ERP, N=32/T=128/window=16 | 0.87× |
| Real heatwave CSV comparison | 0.72× |

These are measurements to investigate on the server. The local data do not
separate code cost from scheduling noise sufficiently to attribute every
regression. The complete reports include the remaining cases, rather than only
the improved ones.

## New output and cache modes

The final quick run additionally observed:

| Mode | Warm p50 (ms) | First API call (ms) | Scope |
|---|---:|---:|---|
| Raw score-only, T=290 | 2.688 | 2.527 | Five components and aggregate scores |
| Prepared full report, T=290 | 3.945 | 6.897 | Full report with reusable prepared inputs |
| Prepared score-only, T=290 | 0.474 | 3.043 | Scores with reusable prepared inputs |
| Prepared score-only, T=1024 | 0.509 | 2.664 | Scores with reusable prepared inputs |
| Fast rolling, T=290/window=60/step=5 | 9.769 | 8.767 | Raw-window Pearson and first-difference correlations |

Prepared construction is separate in each case's `preparation` record; further
features populate lazily during first use. Score-only mode omits report
diagnostics/text. Fast rolling has a separate raw-window definition and reduced
output; it does not estimate the full similarity score. These numbers need those
conditions whenever they are quoted.

## Search observations and recall

The full final quick run had substantial timing variation in its brute-force DTW
case: `[1.081, 3.106, 3.129, 1.133, 3.063]` ms. Its certified samples were
`[0.507, 2.592, 0.528, 0.536, 0.498]` ms. Dividing those medians would give a
misleadingly large impression of a stable gain. The original samples and their
percentiles remain in `current-quick.json`.

A separately recorded focused confirmation, using the same N=128/T=128 data,
k=10, seed, backend, and thread count, gave:

| Target | Brute p50 (ms) | Certified p50 (ms) | Within-run ratio | Approximate p50 (ms) | Approximate Recall@10 |
|---|---:|---:|---:|---:|---:|
| DTW, window=16 | 0.948 | 0.540 | 1.76× | 0.897 | 0.70 |
| SBD | 6.529 | 2.476 | 2.64× | 1.331 | 0.50 |

Certified IDs and values matched the complete original batch reference in both
cases. The DTW automatic path chose a cached native complete scan, evaluating all
128 candidates. The SBD path reused bank preparation and forward FFTs but also
covered all 128 candidates. Those gains come from reused work, not evidence of
pruning in these two final cases.

Approximate mode used `strategy="multiview"` and 22 candidates. Its original
reranked values passed the reference checks, while the final neighbor set missed
3/10 DTW and 5/10 SBD reference neighbors for this query. This budget has not
demonstrated a 0.99-recall target. In this small DTW case, the approximate path
was slower than the certified cached scan. Candidate construction and scoring
costs both matter.

First-call costs also matter. In the focused run, certified DTW took 3.299 ms on
its first API call plus 0.396 ms for index construction; certified SBD took
10.805 ms plus 0.244 ms. The approximate first calls took 46.024 and 49.618 ms,
respectively, including lazy candidate-feature preparation. Input generation,
Python import, and benchmark-only ground-truth validation are separately
recorded. Warm throughput does not describe a one-off cold query.

FAISS Flat and HNSW have functional coverage in the test suite. The recorded
default performance runs use multiview; these files do not establish an HNSW
recall curve, graph-build amortization, or large-scale ANN throughput.

## The bounds regression and resulting policy change

The initial implementation's automatic Python bounds reduced DP work while
making a small native DTW search substantially slower. Independent diagnostic
runs measured the same N=128/T=128/window=16 configuration:

| Recorded run | Brute p50 (ms) | Certified p50 (ms) | Observation |
|---|---:|---:|---|
| Initial automatic bounds | 1.119 | 16.757 | The final measured call spent about 16.35 ms in bounds |
| Explicit `bounds=none` | 1.093 | 1.223 | Cached cutoff path without explicit bounds approached the batch scan |
| Explicit `bounds=cheap` | 1.117 | 4.787 | Same DP cells and exclusions as `none`; endpoint computation added overhead |
| Revised automatic scan diagnostic | 1.349 | 0.656 | Cached native complete scan avoided the Python bounds overhead |

These rows are separate runs, with their configuration and source hashes
preserved. They demonstrate why pruning counts alone are insufficient evidence
of acceleration. The revised automatic policy uses a cached native complete
scan for sufficiently inexpensive elastic work, with an explicit
`evaluation_policy` and fallback reason. It preserves the score/ranking contract.
The heuristic still requires validation on longer, wider, multichannel, and
large-bank workloads.

## What remains to measure

- Server profiles: 10k/100k candidates, T=5470 pairwise tasks, and the
  T=290/channels=400 profile workload were not run locally.
- Repeated same-host measurements with controlled CPU/BLAS/FAISS thread
  settings are needed before attributing small regressions or reporting a
  stable speedup range.
- Recall needs a fixed realistic bank and independent held-out queries, with
  query-level uncertainty and candidate-budget curves. Repeated timings of one
  query do not add recall evidence.
- Index construction, lazy feature/graph preparation, cold loading, and memory
  growth must be included in the intended deployment's cost model.
- `process_peak_rss_bytes` is a process high-water mark, not an isolated
  per-case peak. `result.stats` describes the final measured call, whereas p50
  describes the timing samples.
- GPU readiness was unavailable locally. The separate GEMM probe can be run on
  RTX PRO 6000 with a suitable CUDA PyTorch environment; its GFLOPS are not
  EchoTime or DTW performance.

Reproduction commands and the server-assistant prompt are in
[the server handoff](../docs/acceleration_server_handoff.md). API semantics and
cache/fallback behavior are in [the user guide](../docs/acceleration.md).
