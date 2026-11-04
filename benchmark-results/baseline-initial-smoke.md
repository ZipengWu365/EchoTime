# EchoTime acceleration benchmark

Profile: **smoke**. Commit: `08f7df742b364175105e957d39f9f81fe6211bb3`. Backend: `native`. Threads: `1`.

Measured package: `/workspace/scratch/875f2180653d/echotime-baseline/src/echotime/__init__.py`.

Warm percentiles describe repeated calls on the same data in one process. Small repeat counts do not estimate production tail latency.

First call excludes Python import, input generation and index construction; these costs are reported separately in JSON. Brute-force recall checks are outside timed search calls.

Process peak RSS is a cumulative process high-water mark, not an isolated per-case peak. GPU inventory does not imply GPU execution.

| Case | Status | First (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Recall@k | Speedup vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|
| `compare/t48` | ok | 5.734 | 3.933 | 4.119 | 4.133 | — | — |
| `score/t48` | unavailable | — | — | — | — | — | — |
| `compare_prepared/t48` | unavailable | — | — | — | — | — | — |
| `score_prepared/t48` | unavailable | — | — | — | — | — | — |
| `rolling/t48/w12` | ok | 21.870 | 25.194 | 25.284 | 25.293 | — | — |
| `rolling_fast/t48/w12` | unavailable | — | — | — | — | — | — |
| `profile/t48/c3` | ok | 146.796 | 22.362 | 24.470 | 24.883 | — | — |
| `batch/acf/n8/t24/unrestricted` | ok | 0.581 | 0.338 | 0.405 | 0.414 | — | — |
| `batch/best_shift/n8/t24/unrestricted` | ok | 0.835 | 0.471 | 0.543 | 0.556 | — | — |
| `batch/dtw/n8/t24/unrestricted` | ok | 0.243 | 0.074 | 0.082 | 0.083 | — | — |
| `batch/edr/n8/t24/unrestricted` | ok | 0.198 | 0.080 | 0.136 | 0.144 | — | — |
| `batch/erp/n8/t24/unrestricted` | ok | 0.245 | 0.104 | 0.259 | 0.286 | — | — |
| `batch/independent_max_ncc/n8/t24/unrestricted` | ok | 0.717 | 0.514 | 0.582 | 0.583 | — | — |
| `batch/independent_sbd/n8/t24/unrestricted` | ok | 0.686 | 0.500 | 0.521 | 0.524 | — | — |
| `batch/lcss/n8/t24/unrestricted` | ok | 0.163 | 0.093 | 0.148 | 0.154 | — | — |
| `batch/lcss_similarity/n8/t24/unrestricted` | ok | 0.131 | 0.073 | 0.078 | 0.079 | — | — |
| `batch/linear_trend_model/n8/t24/unrestricted` | ok | 0.862 | 0.491 | 0.542 | 0.547 | — | — |
| `batch/max_ncc/n8/t24/unrestricted` | ok | 0.620 | 0.472 | 0.476 | 0.477 | — | — |
| `batch/ordinal_js/n8/t24/unrestricted` | ok | 0.508 | 0.339 | 0.424 | 0.432 | — | — |
| `batch/periodogram/n8/t24/unrestricted` | ok | 0.348 | 0.208 | 0.278 | 0.284 | — | — |
| `batch/sbd/n8/t24/unrestricted` | ok | 0.625 | 0.492 | 0.785 | 0.816 | — | — |
| `batch/trend/n8/t24/unrestricted` | ok | 0.788 | 0.473 | 0.595 | 0.613 | — | — |
| `batch/twed/n8/t24/unrestricted` | ok | 0.326 | 0.200 | 0.203 | 0.203 | — | — |
| `batch/dtw/n8/t24/w4` | ok | 0.231 | 0.074 | 0.082 | 0.083 | — | — |
| `batch/erp/n8/t24/w4` | ok | 0.168 | 0.099 | 0.141 | 0.147 | — | — |
| `batch/twed/n8/t24/w4` | ok | 0.328 | 0.193 | 0.206 | 0.208 | — | — |
| `pairwise/dtw/n6/t24/w4` | ok | 0.263 | 0.081 | 0.092 | 0.094 | — | — |
| `pairwise/sbd/n6/t24/wNone` | ok | 0.932 | 0.643 | 0.654 | 0.655 | — | — |
| `pairwise/erp/n6/t24/w4` | ok | 0.192 | 0.116 | 0.148 | 0.154 | — | — |
| `search/dtw/brute/n32/t24/w4` | ok | 0.329 | 0.210 | 0.252 | 0.255 | — | — |
| `search/dtw/certified/n32/t24/w4` | unavailable | — | — | — | — | — | — |
| `search/dtw/approximate/n32/t24/w4` | unavailable | — | — | — | — | — | — |
| `search/sbd/brute/n32/t24/wNone` | ok | 1.764 | 1.633 | 1.948 | 1.998 | — | — |
| `search/sbd/certified/n32/t24/wNone` | unavailable | — | — | — | — | — | — |
| `search/sbd/approximate/n32/t24/wNone` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/ties/n24/t24` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/near_duplicates/n24/t24` | unavailable | — | — | — | — | — | — |
| `adversarial/dtw/similar_bank/n24/t24` | unavailable | — | — | — | — | — | — |
| `real/real_python_javascript_pageviews_2024` | ok | 10.748 | 10.281 | 10.494 | 10.536 | — | — |

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
