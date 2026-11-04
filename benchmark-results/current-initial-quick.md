# EchoTime acceleration benchmark

Profile: **quick**. Commit: `442ec2fdb8cabf432b68fa84906111c410ee5ad2`. Backend: `native`. Threads: `1`.

Measured package: `/workspace/scratch/875f2180653d/echotime-development/src/echotime/__init__.py`.

Warm percentiles describe repeated calls on the same data in one process. Small repeat counts do not estimate production tail latency.

First call excludes Python import, input generation and index construction; these costs are reported separately in JSON. Brute-force recall checks are outside timed search calls.

Process peak RSS is a cumulative process high-water mark, not an isolated per-case peak. GPU inventory does not imply GPU execution.

| Case | Status | First (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Recall@k | Speedup vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|
| `compare/t290` | ok | 12.341 | 7.897 | 9.611 | 9.756 | — | 1.256× |
| `compare/t1024` | ok | 8.210 | 8.952 | 11.484 | 11.761 | — | 0.936× |
| `score/t290` | ok | 3.487 | 3.267 | 3.761 | 3.795 | — | — |
| `score/t1024` | ok | 3.090 | 3.153 | 3.616 | 3.649 | — | — |
| `compare_prepared/t290` | ok | 9.404 | 4.175 | 4.750 | 4.791 | — | — |
| `compare_prepared/t1024` | ok | 7.889 | 4.906 | 5.267 | 5.301 | — | — |
| `score_prepared/t290` | ok | 3.780 | 0.702 | 0.933 | 0.967 | — | — |
| `score_prepared/t1024` | ok | 4.369 | 0.648 | 0.814 | 0.825 | — | — |
| `rolling/t290/w60` | ok | 172.403 | 167.710 | 191.590 | 195.906 | — | 1.836× |
| `rolling_fast/t290/w60` | ok | 11.356 | 9.628 | 11.684 | 12.091 | — | — |
| `profile/t96/c8` | ok | 222.036 | 77.891 | 83.805 | 83.929 | — | 0.986× |
| `batch/acf/n64/t128/unrestricted` | ok | 3.775 | 5.459 | 9.436 | 9.819 | — | 0.448× |
| `batch/best_shift/n64/t128/unrestricted` | ok | 6.258 | 4.299 | 4.886 | 4.919 | — | 0.860× |
| `batch/dtw/n64/t128/unrestricted` | ok | 1.323 | 0.876 | 5.827 | 6.680 | — | 1.005× |
| `batch/edr/n64/t128/unrestricted` | ok | 2.012 | 1.084 | 1.118 | 1.124 | — | 1.149× |
| `batch/erp/n64/t128/unrestricted` | ok | 2.508 | 1.076 | 1.401 | 1.410 | — | 1.205× |
| `batch/independent_max_ncc/n64/t128/unrestricted` | ok | 4.997 | 5.767 | 8.135 | 8.526 | — | 0.674× |
| `batch/independent_sbd/n64/t128/unrestricted` | ok | 5.978 | 5.106 | 5.958 | 5.995 | — | 1.087× |
| `batch/lcss/n64/t128/unrestricted` | ok | 1.189 | 1.127 | 1.254 | 1.273 | — | 0.842× |
| `batch/lcss_similarity/n64/t128/unrestricted` | ok | 0.878 | 0.725 | 1.095 | 1.158 | — | 0.987× |
| `batch/linear_trend_model/n64/t128/unrestricted` | ok | 4.415 | 4.167 | 6.682 | 6.707 | — | 1.025× |
| `batch/max_ncc/n64/t128/unrestricted` | ok | 5.570 | 3.731 | 6.005 | 6.427 | — | 0.852× |
| `batch/ordinal_js/n64/t128/unrestricted` | ok | 9.491 | 3.966 | 4.203 | 4.229 | — | 0.616× |
| `batch/periodogram/n64/t128/unrestricted` | ok | 2.381 | 2.073 | 2.174 | 2.185 | — | 0.823× |
| `batch/sbd/n64/t128/unrestricted` | ok | 6.468 | 5.269 | 5.491 | 5.518 | — | 0.851× |
| `batch/trend/n64/t128/unrestricted` | ok | 4.164 | 4.117 | 4.249 | 4.265 | — | 1.552× |
| `batch/twed/n64/t128/unrestricted` | ok | 2.406 | 1.951 | 2.095 | 2.098 | — | 1.260× |
| `batch/dtw/n64/t128/w16` | ok | 0.779 | 0.585 | 0.900 | 0.934 | — | 1.129× |
| `batch/erp/n64/t128/w16` | ok | 0.773 | 0.647 | 0.764 | 0.781 | — | 1.280× |
| `batch/twed/n64/t128/w16` | ok | 1.750 | 1.321 | 1.466 | 1.489 | — | 1.541× |
| `pairwise/dtw/n32/t128/w16` | ok | 2.032 | 1.403 | 1.452 | 1.453 | — | 1.073× |
| `pairwise/sbd/n32/t128/wNone` | ok | 12.707 | 12.450 | 15.892 | 16.538 | — | 0.950× |
| `pairwise/erp/n32/t128/w16` | ok | 2.370 | 1.471 | 1.663 | 1.671 | — | 1.220× |
| `search/dtw/brute/n128/t128/w16` | ok | 1.234 | 1.119 | 1.618 | 1.668 | — | 1.255× |
| `search/dtw/certified/n128/t128/w16` | ok | 17.240 | 16.757 | 18.087 | 18.330 | 1.0 | — |
| `search/dtw/approximate/n128/t128/w16` | ok | 56.519 | 2.311 | 2.766 | 2.842 | 0.7 | — |
| `search/sbd/brute/n128/t128/wNone` | ok | 8.770 | 7.741 | 8.750 | 8.905 | — | 1.010× |
| `search/sbd/certified/n128/t128/wNone` | ok | 8.602 | 8.817 | 10.339 | 10.626 | 1.0 | — |
| `search/sbd/approximate/n128/t128/wNone` | ok | 56.877 | 3.105 | 3.778 | 3.814 | 0.5 | — |
| `adversarial/dtw/ties/n64/t128` | ok | 3.821 | 3.665 | 3.986 | 4.011 | 1.0 | — |
| `adversarial/dtw/near_duplicates/n64/t128` | ok | 5.812 | 5.008 | 6.674 | 6.798 | 1.0 | — |
| `adversarial/dtw/similar_bank/n64/t128` | ok | 4.739 | 4.544 | 6.394 | 6.758 | 1.0 | — |
| `real/real_python_javascript_pageviews_2024` | ok | 9.751 | 8.186 | 10.151 | 10.329 | — | 0.994× |
| `real/real_btc_oil_vix_2024` | ok | 9.093 | 7.940 | 9.174 | 9.241 | — | 1.716× |
| `real/real_heatwave_city_temps_2024` | ok | 8.330 | 7.474 | 8.307 | 8.452 | — | 1.233× |

## Interpretation limits

- A local smoke run validates instrumentation and small inputs; it does not establish a server throughput target.
- An absent optional API is recorded as unavailable. An implemented API throwing an unexpected exception is an error and produces a nonzero exit status.
- Exact search is checked against original batch metric values and deterministic row-ID tie order. Approximate search reports observed Recall@k on this fixed query, not a population guarantee.
- CandidateRecall@k remains null unless the search API explicitly supplies it; returned-result Recall@k is independently measured.
- Array checksums help identify a run; they are not a cross-platform floating-point equivalence test. Use the golden and native-equivalence tests for that purpose.
