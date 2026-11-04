# EchoTime acceleration implementation status

Base: `08f7df742b364175105e957d39f9f81fe6211bb3` (`0.18.0.dev0`).
Development branch: `feature/acceleration`.

The branch preserves the existing planning commit and implements a reviewable
CPU/search increment. It does not claim that every optimization in the merged
plan has been completed. The package version remains a development version.

## Implemented in this increment

| Area | Implementation | Evidence / entry point |
|---|---|---|
| P0 | Independently frozen original Python outputs and exception contracts; 383 fixtures spanning all 16 batch targets, reports, rolling and profiles | `tests/golden/`, `tools/generate_acceleration_golden.py` |
| P0 | Same-harness original/current benchmarks, source and native-binary fingerprints, first-call/warm timing and explicit unavailable states | `benchmarks/run_suite.py`, `benchmark-results/README.md` |
| P1 | Fixed eager `setdefault` computation; bounded pair embedding temporaries without changing reduction order | `batch.py`, `test_batch_cache.py` |
| P1 | Immutable `PreparedSeries`, lazy feature caches, shared rank/bin features, exact score-only output | `prepared.py`, `similarity.py` |
| P1 | Complete rolling output computes only required dependencies; separately named fast mode returns raw-window correlations with stability fallback | `rolling_similarity`, prepared/rolling tests |
| P1 | Shared full-series normalized spectrum and Hurst calculations in profile metrics | `metrics.py`, shared-call-count tests |
| P1/P2 | `PreparedCollection`; cached elastic banks, ERP/TWED side terms, vector features, NCC units and reusable FFTs | `_search_elastic.py`, `_search_vectors.py`, `_search_ncc.py` |
| P2 | Native row cutoff for DTW, ERP, TWED, EDR and LCSS, explicit exceeded-result protocol and DP-cell counts | `_cutoff.py`, `native/echotime_native.cpp` |
| P2 | Exact Top-K, distance range search, batch queries, stable ties, NaN-last ordering, deferred explanations | `SearchIndex` |
| P2 | DTW endpoints/ordered Keogh, integer envelope bounds for EDR/LCSS, two-validity-branch composite score bounds | `_search_bounds.py`, correctness document |
| P2 | Blocked native cutoff with stale but safe thresholds; cached legacy SIMD full-scan dispatch for low-cost pairs | `SearchIndex`, `ElasticCache.evaluate_full` |
| P3 | Full-length multiview, protected resolution pyramid, 128-bit random-hyperplane candidates, optional CPU FAISS Flat/HNSW | `_search_candidates.py`, `echotime[search]` |
| P3 | Exact reranking, explicit unmeasured recall or full-query audit, warm-start refinement to full coverage | `search(..., audit=True)`, `refine` |
| P4 foundation | Safe numeric persistence and optional read-only raw memmaps; explicit CPU/native/cutoff capability metadata | `save/load`, `similarity_backend_info` |
| Validation | Public runnable example, optional-FAISS CI job, server handoff, CUDA hardware-readiness probe | `examples/search_index.py`, `.github/workflows/tests.yml`, `benchmarks/gpu_probe.py` |

## Deliberately retained as complete scans

NCC does not use its real-arithmetic spectral bound to certify a floating-point
exclusion. It reuses input/FFT preparation and evaluates the complete original
score. Vector embedding targets reuse their existing native per-row reductions;
there is no change to a float32 FAISS distance or a GEMM norm identity in the
certified value path.

Short/narrow native DPs default to a cached complete scan because measured
Python-bound overhead was larger than the work it saved. The original slower
bound-heavy benchmark and the subsequent dispatch measurement are retained.
The branch makes no universal speedup or high-recall claim.

## Remaining work from the merged plan

| Proposed item | Status and reason | Next validation |
|---|---|---|
| Truly lazy strings/properties on the existing full-report dataclass | Deferred to preserve serialization, dataclass fields and eager report compatibility; score/rolling avoid unused explanations now | API compatibility decision plus report/pickle regressions |
| Best-lag prefix moments; fused native correlation statistics; GEMM correlation/selection | Deferred after removing these diagnostics from score/rolling hot paths | Measure remaining report/large-vector cost; B-level error and boundary reranking tests |
| Persistent native worker pool | Not implemented; scratch is per worker within a native batch, and thread creation is per batch | High-query-rate target-server measurements and shutdown/reentrancy tests |
| LB_Webb and EAP state-level pruning | Not implemented; current cutoff operates after complete rows | Independent reference cases, visit counts and net runtime |
| ERP/TWED pivots, certified spectral NCC pruning | Not certified/enabled | Implementation-specific metric and floating-point analysis, then adversarial tests |
| Tight composite DTW inverse budgets and block-tree score bounds | Not implemented | Bound validity across NaN branches and rounding/tie boundaries |
| ISA runtime dispatch, additional multivariate SIMD, wavefront DTW | Not implemented | Actual target CPU capabilities and throughput; existing FP64 contract |
| GPU DP, GPU-resident search, mixed-precision intervals | Not implemented or measured as EchoTime backends | RTX PRO 6000 probe, server workloads, then a separate implementation and parity gate |
| Million-series/full out-of-core feature execution | Not locally validated; mmap applies to raw persisted arrays, caches still use RAM | Host-memory measurements at scale and a bounded working-set design |
| Stable-distribution recall calibration | Not claimed from one-query audits | Independent held-out queries, failure groups and query-level uncertainty |
| Website navigation/release integration and binary wheel release matrix | A runnable example and guide exist; release packaging/website integration remains the release phase | Server acceptance, platform wheels, then explicit merge/release approval |

## Two boundary fixes found during implementation

1. Empty TWED sides formerly stored an extra previous-timestamp sentinel in a
   native batch, causing a shape error instead of Python's NaN result. The empty
   timestamp side now has length zero. Defined finite results are unchanged.
2. Extremely large legal windows could overflow C++ `i+window`. The new cutoff
   and cached-search paths clamp an already-full-width window before native
   indexing. Existing unrelated APIs have not been globally rewritten.

## Acceptance artifacts

The final local repository suite passed **1,592 tests with no skips**. A fresh
native-wheel installation and an actually absent-extension fallback both passed
the public retrieval, persistence, prepared-score and packaged-asset verifier.
See the [validation summary](../benchmark-results/validation-summary.md) for
commands, logs, dependency versions and untested platforms.

- [User guide](acceleration.md): public API examples and mode choices.
- [Correctness contract](acceleration_correctness.md): which bounds are certified
  and why, including the limitations of the floating-point claim.
- [Local measurements](../benchmark-results/README.md): complete retained evidence,
  regressions, first-call cost and the conditions of each result.
- [Server handoff](acceleration_server_handoff.md): exact commands and a ready-to-use
  Chinese prompt for the RTX PRO 6000 host.

The server stage should return test logs, baseline/current JSON and Markdown,
hardware/software inventories, recall evidence and failure cases. A visible GPU
or a measured GEMM throughput does not establish an EchoTime GPU speedup.
