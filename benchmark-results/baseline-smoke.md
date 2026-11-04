# EchoTime acceleration benchmark

Profile: **smoke**. Commit: `08f7df742b364175105e957d39f9f81fe6211bb3`. Backend: `native`. Threads: `1`.

Measured package: `/workspace/scratch/875f2180653d/echotime-baseline/src/echotime/__init__.py`.

Warm percentiles describe repeated calls on the same data in one process. Small repeat counts do not estimate production tail latency.

First call excludes Python import, input generation and index construction; these costs are reported separately in JSON. Brute-force recall checks are outside timed search calls.

Process peak RSS is a cumulative process high-water mark, not an isolated per-case peak. GPU inventory does not imply GPU execution.

| Case | Status | First (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Recall@k | Speedup vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|
| `compare/t48` | ok | 6.172 | 4.314 | 4.792 | 4.854 | — | — |
| `score/t48` | unavailable | — | — | — | — | — | — |
| `compare_prepared/t48` | unavailable | — | — | — | — | — | — |
| `score_prepared/t48` | unavailable | — | — | — | — | — | — |
| `rolling/t48/w12` | ok | 23.464 | 22.762 | 24.178 | 24.296 | — | — |
| `rolling_fast/t48/w12` | unavailable | — | — | — | — | — | — |
| `profile/t48/c3` | ok | 160.447 | 23.794 | 28.125 | 28.714 | — | — |
| `batch/acf/n8/t24/unrestricted` | ok | 0.802 | 0.398 | 0.464 | 0.466 | — | — |
| `batch/best_shift/n8/t24/unrestricted` | ok | 0.784 | 0.468 | 0.475 | 0.475 | — | — |
| `batch/dtw/n8/t24/unrestricted` | ok | 0.207 | 0.079 | 0.103 | 0.103 | — | — |
| `batch/edr/n8/t24/unrestricted` | ok | 0.180 | 0.081 | 0.112 | 0.115 | — | — |
| `batch/erp/n8/t24/unrestricted` | ok | 0.239 | 0.098 | 0.122 | 0.124 | — | — |
| `batch/independent_max_ncc/n8/t24/unrestricted` | ok | 0.796 | 0.513 | 0.678 | 0.709 | — | — |
| `batch/independent_sbd/n8/t24/unrestricted` | ok | 0.735 | 0.557 | 0.844 | 0.897 | — | — |
| `batch/lcss/n8/t24/unrestricted` | ok | 0.175 | 0.086 | 0.138 | 0.148 | — | — |
| `batch/lcss_similarity/n8/t24/unrestricted` | ok | 0.186 | 0.075 | 0.103 | 0.108 | — | — |
| `batch/linear_trend_model/n8/t24/unrestricted` | ok | 0.994 | 0.449 | 0.492 | 0.497 | — | — |
| `batch/max_ncc/n8/t24/unrestricted` | ok | 0.918 | 0.596 | 0.754 | 0.784 | — | — |
| `batch/ordinal_js/n8/t24/unrestricted` | ok | 0.626 | 0.347 | 0.381 | 0.382 | — | — |
| `batch/periodogram/n8/t24/unrestricted` | ok | 0.635 | 0.190 | 0.242 | 0.249 | — | — |
| `batch/sbd/n8/t24/unrestricted` | ok | 0.773 | 0.458 | 0.529 | 0.540 | — | — |
| `batch/trend/n8/t24/unrestricted` | ok | 0.721 | 0.868 | 0.929 | 0.939 | — | — |
| `batch/twed/n8/t24/unrestricted` | ok | 0.428 | 0.210 | 0.332 | 0.349 | — | — |
| `batch/dtw/n8/t24/w4` | ok | 0.256 | 0.078 | 0.082 | 0.082 | — | — |
| `batch/erp/n8/t24/w4` | ok | 0.250 | 0.101 | 0.122 | 0.125 | — | — |
| `batch/twed/n8/t24/w4` | ok | 0.316 | 0.221 | 0.339 | 0.347 | — | — |
| `pairwise/dtw/n6/t24/w4` | ok | 0.325 | 0.103 | 0.179 | 0.183 | — | — |
| `pairwise/sbd/n6/t24/wNone` | ok | 1.035 | 0.773 | 0.897 | 0.919 | — | — |
| `pairwise/erp/n6/t24/w4` | ok | 0.191 | 0.119 | 0.157 | 0.159 | — | — |
| `search/dtw/brute/n32/t24/w4` | ok | 0.404 | 0.473 | 1.552 | 1.768 | — | — |
| `search/dtw/certified/n32/t24/w4` | unavailable | — | — | — | — | — | — |
| `search/dtw/approximate/n32/t24/w4` | unavailable | — | — | — | — | — | — |
| `search/sbd/brute/n32/t24/wNone` | ok | 3.037 | 2.635 | 2.778 | 2.800 | — | — |
| `search/sbd/certified/n32/t24/wNone` | unavailable | — | — | — | — | — | — |
| `search/sbd/approximate/n32/t24/wNone` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/ties/n24/t24` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/near_duplicates/n24/t24` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/similar_bank/n24/t24` | unavailable | — | — | — | — | — | — |
| `real/real_python_javascript_pageviews_2024` | ok | 10.451 | 8.145 | 9.408 | 9.558 | — | — |

## Unavailable or failed cases

- `score/t48`: compare_series(output='score') is unavailable in this revision
- `compare_prepared/t48`: echotime.prepared.PreparedSeries is unavailable in this revision
- `score_prepared/t48`: compare_series(output='score') is unavailable in this revision
- `rolling_fast/t48/w12`: rolling_similarity(mode='fast') is unavailable in this revision
- `search/dtw/certified/n32/t24/w4`: echotime.search is unavailable in this revision
- `search/dtw/approximate/n32/t24/w4`: echotime.search is unavailable in this revision
- `search/sbd/certified/n32/t24/wNone`: echotime.search is unavailable in this revision
- `search/sbd/approximate/n32/t24/wNone`: echotime.search is unavailable in this revision
- `adversarial/dtw/ties/n24/t24`: echotime.search is unavailable in this revision
- `adversarial/dtw/near_duplicates/n24/t24`: echotime.search is unavailable in this revision
- `adversarial/dtw/similar_bank/n24/t24`: echotime.search is unavailable in this revision

## Interpretation limits

- A local smoke run validates instrumentation and small inputs; it does not establish a server throughput target.
- An absent optional API is recorded as unavailable. An implemented API throwing an unexpected exception is an error and produces a nonzero exit status.
- Exact search is checked against original batch metric values and deterministic row-ID tie order. Approximate search reports observed Recall@k on this fixed query, not a population guarantee.
- CandidateRecall@k remains null unless the search API explicitly supplies it; returned-result Recall@k is independently measured.
- Array checksums help identify a run; they are not a cross-platform floating-point equivalence test. Use the golden and native-equivalence tests for that purpose.
