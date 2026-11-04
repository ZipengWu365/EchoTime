# EchoTime acceleration benchmark

Profile: **quick**. Commit: `08f7df742b364175105e957d39f9f81fe6211bb3`. Backend: `native`. Threads: `1`.

Measured package: `/workspace/scratch/875f2180653d/echotime-baseline/src/echotime/__init__.py`.

Warm percentiles describe repeated calls on the same data in one process. Small repeat counts do not estimate production tail latency.

First call excludes Python import, input generation and index construction; these costs are reported separately in JSON. Brute-force recall checks are outside timed search calls.

Process peak RSS is a cumulative process high-water mark, not an isolated per-case peak. GPU inventory does not imply GPU execution.

| Case | Status | First (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Recall@k | Speedup vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|
| `compare/t290` | ok | 10.208 | 7.412 | 8.743 | 8.750 | — | — |
| `compare/t1024` | ok | 8.744 | 8.146 | 10.937 | 11.003 | — | — |
| `score/t290` | unavailable | — | — | — | — | — | — |
| `score/t1024` | unavailable | — | — | — | — | — | — |
| `compare_prepared/t290` | unavailable | — | — | — | — | — | — |
| `compare_prepared/t1024` | unavailable | — | — | — | — | — | — |
| `score_prepared/t290` | unavailable | — | — | — | — | — | — |
| `score_prepared/t1024` | unavailable | — | — | — | — | — | — |
| `rolling/t290/w60` | ok | 313.541 | 277.052 | 288.172 | 289.713 | — | — |
| `rolling_fast/t290/w60` | unavailable | — | — | — | — | — | — |
| `profile/t96/c8` | ok | 299.569 | 109.214 | 119.341 | 120.761 | — | — |
| `batch/acf/n64/t128/unrestricted` | ok | 5.741 | 3.036 | 6.873 | 7.382 | — | — |
| `batch/best_shift/n64/t128/unrestricted` | ok | 6.196 | 5.124 | 5.538 | 5.604 | — | — |
| `batch/dtw/n64/t128/unrestricted` | ok | 2.904 | 0.818 | 2.469 | 2.791 | — | — |
| `batch/edr/n64/t128/unrestricted` | ok | 0.929 | 0.848 | 2.498 | 2.821 | — | — |
| `batch/erp/n64/t128/unrestricted` | ok | 1.067 | 0.976 | 2.653 | 2.948 | — | — |
| `batch/independent_max_ncc/n64/t128/unrestricted` | ok | 5.548 | 4.972 | 5.660 | 5.781 | — | — |
| `batch/independent_sbd/n64/t128/unrestricted` | ok | 7.701 | 4.515 | 4.934 | 4.975 | — | — |
| `batch/lcss/n64/t128/unrestricted` | ok | 0.901 | 0.989 | 1.119 | 1.123 | — | — |
| `batch/lcss_similarity/n64/t128/unrestricted` | ok | 1.026 | 0.790 | 1.170 | 1.245 | — | — |
| `batch/linear_trend_model/n64/t128/unrestricted` | ok | 5.256 | 5.949 | 6.232 | 6.261 | — | — |
| `batch/max_ncc/n64/t128/unrestricted` | ok | 4.033 | 4.120 | 4.413 | 4.456 | — | — |
| `batch/ordinal_js/n64/t128/unrestricted` | ok | 3.531 | 3.188 | 3.344 | 3.352 | — | — |
| `batch/periodogram/n64/t128/unrestricted` | ok | 1.841 | 1.960 | 2.142 | 2.160 | — | — |
| `batch/sbd/n64/t128/unrestricted` | ok | 3.782 | 3.864 | 4.190 | 4.242 | — | — |
| `batch/trend/n64/t128/unrestricted` | ok | 5.857 | 4.374 | 4.647 | 4.662 | — | — |
| `batch/twed/n64/t128/unrestricted` | ok | 3.367 | 2.384 | 2.507 | 2.531 | — | — |
| `batch/dtw/n64/t128/w16` | ok | 1.139 | 0.683 | 0.739 | 0.744 | — | — |
| `batch/erp/n64/t128/w16` | ok | 1.196 | 0.945 | 1.000 | 1.005 | — | — |
| `batch/twed/n64/t128/w16` | ok | 1.969 | 1.687 | 1.933 | 1.979 | — | — |
| `pairwise/dtw/n32/t128/w16` | ok | 1.419 | 1.541 | 2.006 | 2.040 | — | — |
| `pairwise/sbd/n32/t128/wNone` | ok | 65.865 | 12.395 | 13.466 | 13.617 | — | — |
| `pairwise/erp/n32/t128/w16` | ok | 1.913 | 1.601 | 1.920 | 1.958 | — | — |
| `search/dtw/brute/n128/t128/w16` | ok | 1.214 | 1.267 | 2.068 | 2.124 | — | — |
| `search/dtw/certified/n128/t128/w16` | unavailable | — | — | — | — | — | — |
| `search/dtw/approximate/n128/t128/w16` | unavailable | — | — | — | — | — | — |
| `search/sbd/brute/n128/t128/wNone` | ok | 8.278 | 7.598 | 9.137 | 9.396 | — | — |
| `search/sbd/certified/n128/t128/wNone` | unavailable | — | — | — | — | — | — |
| `search/sbd/approximate/n128/t128/wNone` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/ties/n64/t128` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/near_duplicates/n64/t128` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/similar_bank/n64/t128` | unavailable | — | — | — | — | — | — |
| `real/real_python_javascript_pageviews_2024` | ok | 10.378 | 8.255 | 10.086 | 10.376 | — | — |
| `real/real_btc_oil_vix_2024` | ok | 8.719 | 8.968 | 9.449 | 9.540 | — | — |
| `real/real_heatwave_city_temps_2024` | ok | 8.044 | 6.251 | 8.946 | 8.995 | — | — |

## Unavailable or failed cases

- `score/t290`: compare_series(output='score') is unavailable in this revision
- `score/t1024`: compare_series(output='score') is unavailable in this revision
- `compare_prepared/t290`: echotime.prepared.PreparedSeries is unavailable in this revision
- `compare_prepared/t1024`: echotime.prepared.PreparedSeries is unavailable in this revision
- `score_prepared/t290`: compare_series(output='score') is unavailable in this revision
- `score_prepared/t1024`: compare_series(output='score') is unavailable in this revision
- `rolling_fast/t290/w60`: rolling_similarity(mode='fast') is unavailable in this revision
- `search/dtw/certified/n128/t128/w16`: echotime.search is unavailable in this revision
- `search/dtw/approximate/n128/t128/w16`: echotime.search is unavailable in this revision
- `search/sbd/certified/n128/t128/wNone`: echotime.search is unavailable in this revision
- `search/sbd/approximate/n128/t128/wNone`: echotime.search is unavailable in this revision
- `adversarial/dtw/ties/n64/t128`: echotime.search is unavailable in this revision
- `adversarial/dtw/near_duplicates/n64/t128`: echotime.search is unavailable in this revision
- `adversarial/dtw/similar_bank/n64/t128`: echotime.search is unavailable in this revision

## Interpretation limits

- A local smoke run validates instrumentation and small inputs; it does not establish a server throughput target.
- An absent optional API is recorded as unavailable. An implemented API throwing an unexpected exception is an error and produces a nonzero exit status.
- Exact search is checked against original batch metric values and deterministic row-ID tie order. Approximate search reports observed Recall@k on this fixed query, not a population guarantee.
- CandidateRecall@k remains null unless the search API explicitly supplies it; returned-result Recall@k is independently measured.
- Array checksums help identify a run; they are not a cross-platform floating-point equivalence test. Use the golden and native-equivalence tests for that purpose.
