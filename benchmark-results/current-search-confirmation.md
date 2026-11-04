# EchoTime acceleration benchmark

Profile: **quick**. Commit: `c7fd3986af2ea750d9146ca204bedb8a050b55d7`. Backend: `native`. Threads: `1`.

Measured package: `/workspace/scratch/875f2180653d/echotime-development/src/echotime/__init__.py`.

Warm percentiles describe repeated calls on the same data in one process. Small repeat counts do not estimate production tail latency.

First call excludes Python import, input generation and index construction; these costs are reported separately in JSON. Brute-force recall checks are outside timed search calls.

Process peak RSS is a cumulative process high-water mark, not an isolated per-case peak. GPU inventory does not imply GPU execution.

| Case | Status | First (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Recall@k | Speedup vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|
| `search/dtw/brute/n128/t128/w16` | ok | 1.327 | 0.948 | 1.113 | 1.117 | — | — |
| `search/dtw/certified/n128/t128/w16` | ok | 3.299 | 0.540 | 0.632 | 0.634 | 1.0 | — |
| `search/dtw/approximate/n128/t128/w16` | ok | 46.024 | 0.897 | 1.076 | 1.084 | 0.7 | — |
| `search/sbd/brute/n128/t128/wNone` | ok | 7.704 | 6.529 | 6.970 | 7.000 | — | — |
| `search/sbd/certified/n128/t128/wNone` | ok | 10.805 | 2.476 | 2.911 | 2.929 | 1.0 | — |
| `search/sbd/approximate/n128/t128/wNone` | ok | 49.618 | 1.331 | 1.402 | 1.402 | 0.5 | — |

## Interpretation limits

- A local smoke run validates instrumentation and small inputs; it does not establish a server throughput target.
- An absent optional API is recorded as unavailable. An implemented API throwing an unexpected exception is an error and produces a nonzero exit status.
- Exact search is checked against original batch metric values and deterministic row-ID tie order. Approximate search reports observed Recall@k on this fixed query, not a population guarantee.
- CandidateRecall@k remains null unless the search API explicitly supplies it; returned-result Recall@k is independently measured.
- Array checksums help identify a run; they are not a cross-platform floating-point equivalence test. Use the golden and native-equivalence tests for that purpose.
