# EchoTime acceleration benchmark

Profile: **smoke**. Commit: `442ec2fdb8cabf432b68fa84906111c410ee5ad2`. Backend: `native`. Threads: `1`.

Measured package: `/workspace/scratch/875f2180653d/echotime-development/src/echotime/__init__.py`.

Warm percentiles describe repeated calls on the same data in one process. Small repeat counts do not estimate production tail latency.

First call excludes Python import, input generation and index construction; these costs are reported separately in JSON. Brute-force recall checks are outside timed search calls.

Process peak RSS is a cumulative process high-water mark, not an isolated per-case peak. GPU inventory does not imply GPU execution.

| Case | Status | First (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Recall@k | Speedup vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|
| `compare/t48` | ok | 8.719 | 5.067 | 5.905 | 5.956 | — | 0.776× |
| `score/t48` | ok | 3.368 | 2.802 | 3.686 | 3.826 | — | — |
| `compare_prepared/t48` | ok | 4.905 | 2.339 | 2.668 | 2.734 | — | — |
| `score_prepared/t48` | ok | 4.459 | 0.578 | 0.827 | 0.861 | — | — |
| `rolling/t48/w12` | ok | 28.704 | 20.293 | 25.720 | 26.802 | — | 1.242× |
| `rolling_fast/t48/w12` | ok | 1.620 | 1.404 | 1.495 | 1.501 | — | — |
| `profile/t48/c3` | ok | 217.389 | 22.507 | 24.893 | 24.906 | — | 0.994× |
| `batch/acf/n8/t24/unrestricted` | ok | 1.054 | 0.488 | 0.941 | 0.947 | — | 0.692× |
| `batch/best_shift/n8/t24/unrestricted` | ok | 1.037 | 0.519 | 0.761 | 0.762 | — | 0.908× |
| `batch/dtw/n8/t24/unrestricted` | ok | 0.283 | 0.147 | 0.251 | 0.267 | — | 0.505× |
| `batch/edr/n8/t24/unrestricted` | ok | 0.189 | 0.091 | 0.360 | 0.398 | — | 0.880× |
| `batch/erp/n8/t24/unrestricted` | ok | 0.350 | 0.125 | 0.377 | 0.427 | — | 0.827× |
| `batch/independent_max_ncc/n8/t24/unrestricted` | ok | 0.873 | 0.799 | 0.861 | 0.862 | — | 0.643× |
| `batch/independent_sbd/n8/t24/unrestricted` | ok | 0.923 | 0.662 | 0.946 | 0.999 | — | 0.755× |
| `batch/lcss/n8/t24/unrestricted` | ok | 0.473 | 0.097 | 0.259 | 0.275 | — | 0.959× |
| `batch/lcss_similarity/n8/t24/unrestricted` | ok | 0.298 | 0.075 | 0.081 | 0.082 | — | 0.983× |
| `batch/linear_trend_model/n8/t24/unrestricted` | ok | 1.112 | 0.685 | 1.214 | 1.298 | — | 0.716× |
| `batch/max_ncc/n8/t24/unrestricted` | ok | 1.109 | 0.835 | 0.972 | 0.986 | — | 0.564× |
| `batch/ordinal_js/n8/t24/unrestricted` | ok | 0.847 | 0.356 | 0.436 | 0.441 | — | 0.953× |
| `batch/periodogram/n8/t24/unrestricted` | ok | 0.464 | 0.211 | 0.224 | 0.225 | — | 0.986× |
| `batch/sbd/n8/t24/unrestricted` | ok | 1.835 | 0.747 | 0.931 | 0.952 | — | 0.659× |
| `batch/trend/n8/t24/unrestricted` | ok | 1.574 | 1.089 | 1.548 | 1.548 | — | 0.435× |
| `batch/twed/n8/t24/unrestricted` | ok | 0.624 | 0.192 | 0.248 | 0.255 | — | 1.046× |
| `batch/dtw/n8/t24/w4` | ok | 0.150 | 0.128 | 0.341 | 0.355 | — | 0.577× |
| `batch/erp/n8/t24/w4` | ok | 0.346 | 0.110 | 0.141 | 0.142 | — | 0.904× |
| `batch/twed/n8/t24/w4` | ok | 2.097 | 0.196 | 0.216 | 0.217 | — | 0.982× |
| `pairwise/dtw/n6/t24/w4` | ok | 0.375 | 0.129 | 0.142 | 0.143 | — | 0.626× |
| `pairwise/sbd/n6/t24/wNone` | ok | 1.672 | 1.063 | 1.258 | 1.279 | — | 0.605× |
| `pairwise/erp/n6/t24/w4` | ok | 0.240 | 0.125 | 0.169 | 0.170 | — | 0.930× |
| `search/dtw/brute/n32/t24/w4` | ok | 0.638 | 0.329 | 0.375 | 0.378 | — | 0.639× |
| `search/dtw/certified/n32/t24/w4` | ok | 3.899 | 1.848 | 2.260 | 2.328 | 1.0 | — |
| `search/dtw/approximate/n32/t24/w4` | ok | 18.718 | 0.876 | 1.147 | 1.175 | 1.0 | — |
| `search/sbd/brute/n32/t24/wNone` | ok | 2.567 | 3.115 | 6.160 | 6.653 | — | 0.524× |
| `search/sbd/certified/n32/t24/wNone` | ok | 1.942 | 1.857 | 2.133 | 2.187 | 1.0 | — |
| `search/sbd/approximate/n32/t24/wNone` | ok | 13.939 | 1.775 | 2.594 | 2.647 | 0.7 | — |
| `adversarial/dtw/ties/n24/t24` | ok | 0.580 | 0.397 | 0.408 | 0.410 | 1.0 | — |
| `adversarial/dtw/near_duplicates/n24/t24` | ok | 0.563 | 0.377 | 0.527 | 0.542 | 1.0 | — |
| `adversarial/dtw/similar_bank/n24/t24` | ok | 0.592 | 0.456 | 0.599 | 0.619 | 1.0 | — |
| `real/real_python_javascript_pageviews_2024` | ok | 8.632 | 6.914 | 8.707 | 8.964 | — | 1.487× |

## Interpretation limits

- A local smoke run validates instrumentation and small inputs; it does not establish a server throughput target.
- An absent optional API is recorded as unavailable. An implemented API throwing an unexpected exception is an error and produces a nonzero exit status.
- Exact search is checked against original batch metric values and deterministic row-ID tie order. Approximate search reports observed Recall@k on this fixed query, not a population guarantee.
- CandidateRecall@k remains null unless the search API explicitly supplies it; returned-result Recall@k is independently measured.
- Array checksums help identify a run; they are not a cross-platform floating-point equivalence test. Use the golden and native-equivalence tests for that purpose.
