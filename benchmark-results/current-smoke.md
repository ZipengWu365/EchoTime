# EchoTime acceleration benchmark

Profile: **smoke**. Commit: `c7fd3986af2ea750d9146ca204bedb8a050b55d7`. Backend: `native`. Threads: `1`.

Measured package: `/workspace/scratch/875f2180653d/echotime-development/src/echotime/__init__.py`.

Warm percentiles describe repeated calls on the same data in one process. Small repeat counts do not estimate production tail latency.

First call excludes Python import, input generation and index construction; these costs are reported separately in JSON. Brute-force recall checks are outside timed search calls.

Process peak RSS is a cumulative process high-water mark, not an isolated per-case peak. GPU inventory does not imply GPU execution.

| Case | Status | First (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Recall@k | Speedup vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|
| `compare/t48` | ok | 11.086 | 5.132 | 7.559 | 8.030 | — | 0.841× |
| `score/t48` | ok | 2.655 | 2.630 | 3.232 | 3.241 | — | — |
| `compare_prepared/t48` | ok | 4.549 | 2.642 | 2.683 | 2.691 | — | — |
| `score_prepared/t48` | ok | 2.356 | 0.677 | 0.749 | 0.755 | — | — |
| `rolling/t48/w12` | ok | 19.066 | 19.369 | 20.229 | 20.258 | — | 1.175× |
| `rolling_fast/t48/w12` | ok | 1.500 | 1.251 | 1.794 | 1.894 | — | — |
| `profile/t48/c3` | ok | 188.645 | 17.489 | 19.490 | 19.868 | — | 1.361× |
| `batch/acf/n8/t24/unrestricted` | ok | 0.590 | 0.445 | 0.631 | 0.646 | — | 0.893× |
| `batch/best_shift/n8/t24/unrestricted` | ok | 0.857 | 0.492 | 0.579 | 0.589 | — | 0.951× |
| `batch/dtw/n8/t24/unrestricted` | ok | 0.190 | 0.077 | 0.097 | 0.100 | — | 1.027× |
| `batch/edr/n8/t24/unrestricted` | ok | 0.183 | 0.134 | 0.151 | 0.153 | — | 0.602× |
| `batch/erp/n8/t24/unrestricted` | ok | 0.250 | 0.121 | 0.330 | 0.362 | — | 0.810× |
| `batch/independent_max_ncc/n8/t24/unrestricted` | ok | 0.784 | 0.591 | 1.884 | 2.132 | — | 0.868× |
| `batch/independent_sbd/n8/t24/unrestricted` | ok | 0.708 | 0.606 | 1.933 | 2.163 | — | 0.919× |
| `batch/lcss/n8/t24/unrestricted` | ok | 0.333 | 0.083 | 0.119 | 0.125 | — | 1.036× |
| `batch/lcss_similarity/n8/t24/unrestricted` | ok | 0.367 | 0.073 | 0.080 | 0.081 | — | 1.021× |
| `batch/linear_trend_model/n8/t24/unrestricted` | ok | 0.801 | 0.477 | 0.495 | 0.496 | — | 0.941× |
| `batch/max_ncc/n8/t24/unrestricted` | ok | 0.644 | 0.480 | 0.572 | 0.587 | — | 1.242× |
| `batch/ordinal_js/n8/t24/unrestricted` | ok | 0.845 | 0.334 | 0.390 | 0.391 | — | 1.038× |
| `batch/periodogram/n8/t24/unrestricted` | ok | 0.526 | 0.195 | 0.212 | 0.214 | — | 0.974× |
| `batch/sbd/n8/t24/unrestricted` | ok | 0.661 | 0.455 | 0.486 | 0.488 | — | 1.006× |
| `batch/trend/n8/t24/unrestricted` | ok | 0.860 | 0.449 | 0.480 | 0.480 | — | 1.934× |
| `batch/twed/n8/t24/unrestricted` | ok | 0.359 | 0.191 | 0.232 | 0.237 | — | 1.099× |
| `batch/dtw/n8/t24/w4` | ok | 0.169 | 0.079 | 0.099 | 0.101 | — | 0.978× |
| `batch/erp/n8/t24/w4` | ok | 0.199 | 0.102 | 0.131 | 0.134 | — | 0.997× |
| `batch/twed/n8/t24/w4` | ok | 0.305 | 0.185 | 0.214 | 0.217 | — | 1.195× |
| `pairwise/dtw/n6/t24/w4` | ok | 0.172 | 0.088 | 0.111 | 0.112 | — | 1.173× |
| `pairwise/sbd/n6/t24/wNone` | ok | 0.900 | 0.707 | 0.855 | 0.880 | — | 1.095× |
| `pairwise/erp/n6/t24/w4` | ok | 0.188 | 0.141 | 0.376 | 0.387 | — | 0.846× |
| `search/dtw/brute/n32/t24/w4` | ok | 0.337 | 0.214 | 0.230 | 0.231 | — | 2.212× |
| `search/dtw/certified/n32/t24/w4` | ok | 1.872 | 0.153 | 0.181 | 0.181 | 1.0 | — |
| `search/dtw/approximate/n32/t24/w4` | ok | 13.323 | 0.777 | 0.915 | 0.929 | 1.0 | — |
| `search/sbd/brute/n32/t24/wNone` | ok | 2.041 | 1.525 | 1.611 | 1.618 | — | 1.728× |
| `search/sbd/certified/n32/t24/wNone` | ok | 3.275 | 0.733 | 1.042 | 1.078 | 1.0 | — |
| `search/sbd/approximate/n32/t24/wNone` | ok | 14.873 | 1.348 | 1.657 | 1.661 | 0.7 | — |
| `adversarial/dtw/ties/n24/t24` | ok | 0.353 | 0.129 | 0.261 | 0.270 | 1.0 | — |
| `adversarial/dtw/near_duplicates/n24/t24` | ok | 0.300 | 0.159 | 0.300 | 0.307 | 1.0 | — |
| `adversarial/dtw/similar_bank/n24/t24` | ok | 0.354 | 0.161 | 0.215 | 0.220 | 1.0 | — |
| `real/real_python_javascript_pageviews_2024` | ok | 8.028 | 7.457 | 8.299 | 8.460 | — | 1.092× |

## Interpretation limits

- A local smoke run validates instrumentation and small inputs; it does not establish a server throughput target.
- An absent optional API is recorded as unavailable. An implemented API throwing an unexpected exception is an error and produces a nonzero exit status.
- Exact search is checked against original batch metric values and deterministic row-ID tie order. Approximate search reports observed Recall@k on this fixed query, not a population guarantee.
- CandidateRecall@k remains null unless the search API explicitly supplies it; returned-result Recall@k is independently measured.
- Array checksums help identify a run; they are not a cross-platform floating-point equivalence test. Use the golden and native-equivalence tests for that purpose.
