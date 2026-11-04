# EchoTime acceleration benchmark

Profile: **quick**. Commit: `c7fd3986af2ea750d9146ca204bedb8a050b55d7`. Backend: `native`. Threads: `1`.

Measured package: `/workspace/scratch/875f2180653d/echotime-development/src/echotime/__init__.py`.

Warm percentiles describe repeated calls on the same data in one process. Small repeat counts do not estimate production tail latency.

First call excludes Python import, input generation and index construction; these costs are reported separately in JSON. Brute-force recall checks are outside timed search calls.

Process peak RSS is a cumulative process high-water mark, not an isolated per-case peak. GPU inventory does not imply GPU execution.

| Case | Status | First (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Recall@k | Speedup vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|
| `compare/t290` | ok | 8.479 | 7.555 | 8.650 | 8.833 | — | 0.981× |
| `compare/t1024` | ok | 7.092 | 6.314 | 6.435 | 6.448 | — | 1.290× |
| `score/t290` | ok | 2.527 | 2.688 | 3.122 | 3.130 | — | — |
| `score/t1024` | ok | 3.460 | 2.386 | 2.846 | 2.878 | — | — |
| `compare_prepared/t290` | ok | 6.897 | 3.945 | 4.443 | 4.524 | — | — |
| `compare_prepared/t1024` | ok | 6.098 | 4.007 | 4.133 | 4.142 | — | — |
| `score_prepared/t290` | ok | 3.043 | 0.474 | 0.540 | 0.544 | — | — |
| `score_prepared/t1024` | ok | 2.664 | 0.509 | 0.833 | 0.867 | — | — |
| `rolling/t290/w60` | ok | 178.238 | 134.494 | 161.823 | 167.137 | — | 2.060× |
| `rolling_fast/t290/w60` | ok | 8.767 | 9.769 | 11.007 | 11.246 | — | — |
| `profile/t96/c8` | ok | 190.862 | 54.968 | 56.819 | 57.033 | — | 1.987× |
| `batch/acf/n64/t128/unrestricted` | ok | 2.732 | 2.233 | 2.481 | 2.530 | — | 1.360× |
| `batch/best_shift/n64/t128/unrestricted` | ok | 3.619 | 2.979 | 3.134 | 3.160 | — | 1.720× |
| `batch/dtw/n64/t128/unrestricted` | ok | 0.978 | 0.895 | 1.095 | 1.126 | — | 0.914× |
| `batch/edr/n64/t128/unrestricted` | ok | 1.001 | 1.039 | 1.103 | 1.108 | — | 0.816× |
| `batch/erp/n64/t128/unrestricted` | ok | 1.079 | 0.935 | 1.037 | 1.039 | — | 1.043× |
| `batch/independent_max_ncc/n64/t128/unrestricted` | ok | 3.557 | 3.417 | 3.805 | 3.831 | — | 1.455× |
| `batch/independent_sbd/n64/t128/unrestricted` | ok | 3.689 | 3.575 | 3.844 | 3.867 | — | 1.263× |
| `batch/lcss/n64/t128/unrestricted` | ok | 0.939 | 0.682 | 0.794 | 0.815 | — | 1.450× |
| `batch/lcss_similarity/n64/t128/unrestricted` | ok | 0.751 | 0.679 | 0.817 | 0.833 | — | 1.164× |
| `batch/linear_trend_model/n64/t128/unrestricted` | ok | 3.672 | 3.610 | 4.124 | 4.159 | — | 1.648× |
| `batch/max_ncc/n64/t128/unrestricted` | ok | 3.351 | 2.994 | 3.326 | 3.356 | — | 1.376× |
| `batch/ordinal_js/n64/t128/unrestricted` | ok | 2.848 | 2.402 | 2.601 | 2.622 | — | 1.327× |
| `batch/periodogram/n64/t128/unrestricted` | ok | 1.744 | 1.326 | 1.509 | 1.546 | — | 1.479× |
| `batch/sbd/n64/t128/unrestricted` | ok | 3.411 | 3.090 | 5.162 | 5.551 | — | 1.250× |
| `batch/trend/n64/t128/unrestricted` | ok | 6.334 | 5.825 | 5.922 | 5.933 | — | 0.751× |
| `batch/twed/n64/t128/unrestricted` | ok | 3.271 | 2.920 | 2.949 | 2.954 | — | 0.817× |
| `batch/dtw/n64/t128/w16` | ok | 0.881 | 0.722 | 0.758 | 0.761 | — | 0.946× |
| `batch/erp/n64/t128/w16` | ok | 0.727 | 0.839 | 0.930 | 0.931 | — | 1.126× |
| `batch/twed/n64/t128/w16` | ok | 1.874 | 1.800 | 1.905 | 1.915 | — | 0.937× |
| `pairwise/dtw/n32/t128/w16` | ok | 1.316 | 1.798 | 2.538 | 2.678 | — | 0.857× |
| `pairwise/sbd/n32/t128/wNone` | ok | 13.837 | 12.556 | 15.199 | 15.628 | — | 0.987× |
| `pairwise/erp/n32/t128/w16` | ok | 2.056 | 1.841 | 2.706 | 2.815 | — | 0.870× |
| `search/dtw/brute/n128/t128/w16` | ok | 1.214 | 3.063 | 3.125 | 3.128 | — | 0.414× |
| `search/dtw/certified/n128/t128/w16` | ok | 8.127 | 0.528 | 2.181 | 2.510 | 1.0 | — |
| `search/dtw/approximate/n128/t128/w16` | ok | 67.572 | 1.049 | 1.180 | 1.196 | 0.7 | — |
| `search/sbd/brute/n128/t128/wNone` | ok | 7.767 | 9.240 | 12.294 | 12.793 | — | 0.822× |
| `search/sbd/certified/n128/t128/wNone` | ok | 13.672 | 4.142 | 4.172 | 4.175 | 1.0 | — |
| `search/sbd/approximate/n128/t128/wNone` | ok | 59.190 | 1.576 | 2.190 | 2.210 | 0.5 | — |
| `adversarial/dtw/ties/n64/t128` | ok | 1.138 | 0.684 | 0.800 | 0.820 | 1.0 | — |
| `adversarial/dtw/near_duplicates/n64/t128` | ok | 1.122 | 0.683 | 0.830 | 0.845 | 1.0 | — |
| `adversarial/dtw/similar_bank/n64/t128` | ok | 1.151 | 0.588 | 1.003 | 1.048 | 1.0 | — |
| `real/real_python_javascript_pageviews_2024` | ok | 10.510 | 9.136 | 11.116 | 11.404 | — | 0.904× |
| `real/real_btc_oil_vix_2024` | ok | 10.422 | 8.926 | 9.565 | 9.631 | — | 1.005× |
| `real/real_heatwave_city_temps_2024` | ok | 8.280 | 8.702 | 11.362 | 11.517 | — | 0.718× |

## Interpretation limits

- A local smoke run validates instrumentation and small inputs; it does not establish a server throughput target.
- An absent optional API is recorded as unavailable. An implemented API throwing an unexpected exception is an error and produces a nonzero exit status.
- Exact search is checked against original batch metric values and deterministic row-ID tie order. Approximate search reports observed Recall@k on this fixed query, not a population guarantee.
- CandidateRecall@k remains null unless the search API explicitly supplies it; returned-result Recall@k is independently measured.
- Array checksums help identify a run; they are not a cross-platform floating-point equivalence test. Use the golden and native-equivalence tests for that purpose.
