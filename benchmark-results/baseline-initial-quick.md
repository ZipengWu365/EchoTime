# EchoTime acceleration benchmark

Profile: **quick**. Commit: `08f7df742b364175105e957d39f9f81fe6211bb3`. Backend: `native`. Threads: `1`.

Measured package: `/workspace/scratch/875f2180653d/echotime-baseline/src/echotime/__init__.py`.

Warm percentiles describe repeated calls on the same data in one process. Small repeat counts do not estimate production tail latency.

First call excludes Python import, input generation and index construction; these costs are reported separately in JSON. Brute-force recall checks are outside timed search calls.

Process peak RSS is a cumulative process high-water mark, not an isolated per-case peak. GPU inventory does not imply GPU execution.

| Case | Status | First (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Recall@k | Speedup vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|
| `compare/t290` | ok | 9.704 | 9.920 | 12.640 | 12.906 | — | — |
| `compare/t1024` | ok | 9.867 | 8.379 | 9.565 | 9.681 | — | — |
| `score/t290` | unavailable | — | — | — | — | — | — |
| `score/t1024` | unavailable | — | — | — | — | — | — |
| `compare_prepared/t290` | unavailable | — | — | — | — | — | — |
| `compare_prepared/t1024` | unavailable | — | — | — | — | — | — |
| `score_prepared/t290` | unavailable | — | — | — | — | — | — |
| `score_prepared/t1024` | unavailable | — | — | — | — | — | — |
| `rolling/t290/w60` | ok | 310.279 | 307.834 | 314.371 | 315.584 | — | — |
| `rolling_fast/t290/w60` | unavailable | — | — | — | — | — | — |
| `profile/t96/c8` | ok | 204.826 | 76.837 | 82.208 | 82.339 | — | — |
| `batch/acf/n64/t128/unrestricted` | ok | 2.833 | 2.444 | 2.578 | 2.596 | — | — |
| `batch/best_shift/n64/t128/unrestricted` | ok | 3.492 | 3.698 | 3.840 | 3.867 | — | — |
| `batch/dtw/n64/t128/unrestricted` | ok | 1.034 | 0.880 | 1.008 | 1.021 | — | — |
| `batch/edr/n64/t128/unrestricted` | ok | 0.998 | 1.246 | 1.693 | 1.710 | — | — |
| `batch/erp/n64/t128/unrestricted` | ok | 1.198 | 1.297 | 1.537 | 1.544 | — | — |
| `batch/independent_max_ncc/n64/t128/unrestricted` | ok | 4.385 | 3.887 | 4.210 | 4.235 | — | — |
| `batch/independent_sbd/n64/t128/unrestricted` | ok | 4.339 | 5.549 | 6.497 | 6.539 | — | — |
| `batch/lcss/n64/t128/unrestricted` | ok | 0.839 | 0.949 | 1.282 | 1.291 | — | — |
| `batch/lcss_similarity/n64/t128/unrestricted` | ok | 0.986 | 0.716 | 0.882 | 0.898 | — | — |
| `batch/linear_trend_model/n64/t128/unrestricted` | ok | 4.499 | 4.270 | 5.078 | 5.129 | — | — |
| `batch/max_ncc/n64/t128/unrestricted` | ok | 4.767 | 3.178 | 3.402 | 3.420 | — | — |
| `batch/ordinal_js/n64/t128/unrestricted` | ok | 3.478 | 2.442 | 2.577 | 2.593 | — | — |
| `batch/periodogram/n64/t128/unrestricted` | ok | 1.764 | 1.707 | 7.395 | 8.479 | — | — |
| `batch/sbd/n64/t128/unrestricted` | ok | 4.845 | 4.485 | 5.245 | 5.313 | — | — |
| `batch/trend/n64/t128/unrestricted` | ok | 8.576 | 6.391 | 7.484 | 7.665 | — | — |
| `batch/twed/n64/t128/unrestricted` | ok | 2.550 | 2.458 | 2.931 | 2.960 | — | — |
| `batch/dtw/n64/t128/w16` | ok | 1.681 | 0.661 | 1.050 | 1.069 | — | — |
| `batch/erp/n64/t128/w16` | ok | 1.110 | 0.828 | 1.321 | 1.343 | — | — |
| `batch/twed/n64/t128/w16` | ok | 2.092 | 2.035 | 2.267 | 2.269 | — | — |
| `pairwise/dtw/n32/t128/w16` | ok | 2.124 | 1.505 | 1.780 | 1.807 | — | — |
| `pairwise/sbd/n32/t128/wNone` | ok | 14.494 | 11.826 | 13.080 | 13.284 | — | — |
| `pairwise/erp/n32/t128/w16` | ok | 1.665 | 1.794 | 1.958 | 1.985 | — | — |
| `search/dtw/brute/n128/t128/w16` | ok | 2.058 | 1.405 | 1.665 | 1.671 | — | — |
| `search/dtw/certified/n128/t128/w16` | unavailable | — | — | — | — | — | — |
| `search/dtw/approximate/n128/t128/w16` | unavailable | — | — | — | — | — | — |
| `search/sbd/brute/n128/t128/wNone` | ok | 8.611 | 7.819 | 12.513 | 13.380 | — | — |
| `search/sbd/certified/n128/t128/wNone` | unavailable | — | — | — | — | — | — |
| `search/sbd/approximate/n128/t128/wNone` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/ties/n64/t128` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/near_duplicates/n64/t128` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/similar_bank/n64/t128` | unavailable | — | — | — | — | — | — |
| `real/real_python_javascript_pageviews_2024` | ok | 8.343 | 8.136 | 9.040 | 9.052 | — | — |
| `real/real_btc_oil_vix_2024` | ok | 9.759 | 13.622 | 15.364 | 15.601 | — | — |
| `real/real_heatwave_city_temps_2024` | ok | 10.861 | 9.218 | 10.066 | 10.117 | — | — |

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
