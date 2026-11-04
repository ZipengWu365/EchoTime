# Reusable preparation and time-series search

EchoTime can reuse per-series work, compute scores without constructing full
reports, and retrieve neighbors under its existing metrics. The search API
defaults to certified retrieval; approximate candidate selection is explicit.

This is the first implementation of the acceleration plan: reference fixtures
(P0), much of the preparation/report work (P1), certified search (P2), and an
initial approximate search layer (P3). It does not claim that every task is
faster, that all roadmap items are complete, or that GPU execution is available.
Persistent worker pools, a new ISA dispatch layer, and GPU kernels remain future
work. Use the [server handoff](acceleration_server_handoff.md) for reproducible
large-workload acceptance tests and the RTX PRO 6000 testing prompt.

## 1. Select the output you need

The existing `compare_series` call still returns a full `SimilarityReport` by
default. Use `output="score"` when only the five components and aggregate scores
are needed:

```python
import numpy as np
from echotime.similarity import compare_series

rng = np.random.default_rng(42)
left = rng.normal(size=290).cumsum()
right = rng.normal(size=290).cumsum()

report = compare_series(left, right)                 # Existing report API
score = compare_series(left, right, output="score") # SimilarityScore

print(score.similarity_score)
print(score.component_mean)
print(score.component_scores)
```

`SimilarityScore.to_dict()` contains `similarity_score`, `component_mean`, and
`component_scores`. Score-only mode uses the same five-component scoring logic
as the report. It omits diagnostic reference statistics, interpretation, notes,
and suggestions. The score still includes DTW where the original definition
requires it; this option does not replace the scoring function with a cheaper
proxy.

## 2. Prepare reused inputs

`PreparedSeries` owns an immutable snapshot and lazily caches the existing
resampling, per-channel trajectories, differences, trends, ranks, and spectra.
Use it when the same series participates in multiple comparisons:

```python
from echotime.prepared import PreparedSeries

prepared_left = PreparedSeries(left, n_points=256)
prepared_right = PreparedSeries(right, n_points=256)

score = compare_series(prepared_left, prepared_right, output="score")
report = compare_series(prepared_left, prepared_right)
```

Changing the original NumPy array after construction does not change the
snapshot. The snapshot owns its timestamps and resolution. An explicit
`n_points` passed to `compare_series` must agree with prepared inputs; both
prepared inputs must agree with each other. Do not supply new timestamps for an
already prepared input. Create a new `PreparedSeries` when its data or
configuration changes.

For raw inputs, omitted `n_points` retains the original 256-point behavior. With
a prepared input, omission inherits that snapshot's resolution. Preparing a
series does not guarantee that every component is finite: existing short-series,
constant-series, and missing-data behavior is preserved.

Preparation is lazy. Constructor time includes the input snapshot, while the
first comparison may populate additional caches. A warm comparison can therefore
be faster than the first one. Report snapshot construction, first use, and warm
use separately when evaluating a one-off query versus a repeated-query service.

`PreparedSeries.cache_key` includes a semantic version, shape, dtype, resolution,
layout convention, and content digest. Cached features belong to the immutable
snapshot. This is an in-process cache, with no global eviction service or
automatic persistent feature store.

Channel handling follows the existing comparison API. When channel counts match,
the corresponding channels are compared. When counts differ, the prepared
trajectories are aggregated before computing the pair's features. Averaging
already-computed channel features would change that definition.

## 3. Retrieve original-metric neighbors

`SearchIndex` fixes the collection, target metric, and metric parameters. Query
policy is selected separately:

```python
from echotime.search import SearchIndex

bank = rng.normal(size=(128, 256)).cumsum(axis=1)
query = rng.normal(size=256).cumsum()

index = SearchIndex.build(
    bank,
    target="dtw",
    layout="rows",  # Here: (n_series, time)
    window=16,
    normalize=False,
    backend="auto",
    n_jobs=1,
)
hits = index.search(query, k=10)  # mode="certified" is the default

print(hits.ids)           # Original zero-based collection positions
print(hits.values)        # Original DTW values under this configuration
print(hits.certified)
print(hits.stats)
```

Collection layout follows the batch APIs. A two-dimensional array defaults to
`layout="columns"`, meaning `(time, n_series)`. Specify `layout="rows"` for the
shape above. Lists can contain unequal-length or multichannel series; a
three-dimensional array is `(n_series, time, channels)`. Cleaning, channel
alignment, and metric-specific restrictions follow the selected original metric.

Supported targets are the existing batch metrics except `best_shift`, plus
`similarity_score` and `component_mean`. `best_shift` returns a lag and is not a
retrieval distance. Existing metric aliases, such as `dtw_distance`, are accepted.

| Target family | Ranking direction | Reference values |
|---|---|---|
| `dtw`, `edr`, `erp`, `twed`, `lcss` | Smaller first | Existing elastic distance with the configured parameters |
| `sbd`, `independent_sbd` | Smaller first | Existing shape-based distance |
| `max_ncc`, `independent_max_ncc`, `lcss_similarity` | Larger first | Existing similarity value |
| `acf`, `periodogram`, `trend`, `ordinal_js`, `linear_trend_model` | Smaller first | Existing embedding distance under the selected backend |
| `similarity_score`, `component_mean` | Larger first | Existing five-component comparison score |

NaNs sort last. Equal values sort by original collection position, including
ties at the k boundary. The same orientation and metric parameters must be used
in an independent brute-force comparison.

For irregular TWED timestamps, pass the collection timestamps to `build` and
the query timestamps to `search(query_timestamps=...)`. The collection accepts a
shared one-dimensional timestamp array or per-series arrays as in the batch API.
For high-level score targets, timestamps belong to each prepared series. The
high-level API retains its original timestamp validation and interpolation rules.

### What certified retrieval guarantees

A certified result covers the entire collection: each position has been scored
or safely excluded by an implemented bound or cutoff. It does not imply
sublinear work. A difficult dataset can require a complete scan.

Distance pruning uses strict `lower_bound > threshold`; equality survives so
stable ties remain correct. Similarity pruning uses strict
`upper_bound < threshold`. Implemented paths include:

| Path | Current behavior and limits |
|---|---|
| DTW | Endpoint and ordered row-cost envelope bounds, plus row-level cutoff in native DP |
| EDR/LCSS | Conservative match-envelope bounds and applicable native cutoff paths |
| ERP/TWED | Exact threshold evaluation with native cutoff; no certified ERP sum bound |
| High-level scores | Compute inexpensive components; bound the unknown DTW component using the original aggregate arithmetic, including the invalid-component branch |
| NCC/SBD | Complete blocked evaluation with cached input normalization and forward FFTs; no spectral pruning certificate |
| Embedding metrics | Complete blocked/vector evaluation; cache compatible representations where available |

`bounds="auto"` selects a cached native complete scan for sufficiently cheap
elastic workloads, because Python bounds can cost more than the DP they save.
The current heuristic uses an estimated per-pair work limit of 65,536 DP cells
times channels; it is a performance heuristic, not an exactness condition. Other
elastic workloads use the cheap bounds and enable envelope bounds for explicit
windows no wider than 64. Inspect `evaluation_policy` and `fallback_reason` for
the selected path. `bounds="cheap"` limits explicit bounds to cheaper checks;
`bounds="all"` enables implemented envelope bounds more broadly.
`bounds="none"` disables explicit bound pruning but can still use DP cutoff.
Use a full `one_vs_many` call for an independent brute-force reference.

The amplitude-spectrum NCC bound and ERP sum bound are useful mathematical
ideas, but their current floating-point implementations do not carry a rounding
proof. They are marked uncertified and do not exclude candidates from certified
search. An empirical epsilon does not establish a guarantee. In particular,
NCC/SBD stats report the blocked exact-scan fallback instead of claiming a
spectral certificate.

The NCC cache reuses collection forward FFTs across queries and computes a
query's transform once per required padding length. Ragged inputs can require
multiple padding lengths. Inverse FFTs and the existing exact dot-product lag
refinement remain pair-specific, and short or incompatible-channel pairs retain
the original direct fallback. This removes repeated preparation without claiming
that candidates were excluded by a spectral bound. The cache can grow when
queries introduce new required padding lengths, subject to a 256 MiB LRU limit
on persistent collection spectra. A currently evaluated block can temporarily
hold additional spectra.

### Exactness is relative to the selected reference backend

Elastic and NCC paths retain the existing exact-value contract. Embedding
distances already permit small Python/native rounding differences in the batch
API. Search uses the selected backend's values as its reference. A tie that
exists under one backend can differ in the last bits under another; cross-backend
embedding rankings should not be called bit-identical without verification.

The embedding cache preserves the native batch implementation's elementwise
differences and row reductions. It does not substitute a squared-norm/dot-product
identity with a different rounding or cancellation path. For ACF, periodogram,
and trend, a mixed-channel collection retains the full collection's scalar
fallback policy even when an individual query block happens to have matching
channel counts. This avoids changing an existing value when block size changes.

`backend="auto"` resolves using the installed native extension and existing
backend configuration. Explicit `backend="native"` requires that extension.
Python remains a functional fallback; its cutoff wrapper may compute the full
DP before determining that a threshold was exceeded. Native availability alone
does not guarantee a speedup for a particular workload.

The native elastic search path caches cleaned collection data and applicable
ERP/TWED side terms, then evaluates candidates in blocks with the configured
worker count. The top-k threshold updates between blocks; workers in one block
share that block's threshold. The reported `n_jobs_effective` describes the
chosen path. Block-level native calls still create their worker threads; this
version does not implement a persistent worker pool. `search_batch` reuses the
index across sequential queries rather than parallelizing multiple queries.

## 4. Search the high-level score directly

The two high-level targets retain their distinct meanings: weighted
`similarity_score` and the mean of finite components, `component_mean`.

```python
score_index = SearchIndex.build(
    bank, target="similarity_score", layout="rows", n_points=256
)
score_hits = score_index.search(query, k=5)

# Generate full explanations only for the selected positions.
reports = score_index.explain(query, score_hits.ids)
```

`explain` constructs full `SimilarityReport` objects. For an index targeting a
different metric, the explanatory report still uses EchoTime's high-level
comparison definition; its aggregate similarity score is not the DTW, SBD, or
other target value returned by that index.

## 5. Approximate candidates with original-value reranking

```python
fast_hits = index.search(
    query,
    k=10,
    mode="approximate",
    candidates=32,
    strategy="multiview",
)
```

Approximate mode changes the candidate set. Selected candidates are scored with
the original target metric, and returned values keep that metric's meaning. A
missed candidate can still change the final top-k. `fast_hits.certified` is false.
The candidate budget must be at least `min(k, collection_size)`; the API rejects
a smaller budget rather than silently returning too few potential neighbors.

The initial strategies are `multiview`, `pyramid`, `binary`, and optional
`faiss` / `faiss_hnsw`. Their screening representations are proxies, not final metric values.
FAISS uses its own vector precision and distance conventions; exact vector-space
retrieval is not an exactness claim for the original time-series target.
Installing `faiss-cpu` does not activate GPU FAISS. Core operation does not
require FAISS; the NumPy strategies remain available.

| Strategy | Implemented candidate selection | Main limitations |
|---|---|---|
| `multiview` | Reserve candidate quotas for level, events, first differences, derivative spectrum, and coarse trend; fill duplicate quota slots using combined standardized distances | Scans the feature bank; a small budget can leave some views without a quota |
| `pyramid` | Narrow 16/32/64/128-point representations while retaining event/spectrum protection slots from the full collection | Early narrowing can discard a true neighbor; protection slots are a heuristic |
| `binary` | 128 seeded random-hyperplane sign bits, packed into 16 bytes per code, followed by Hamming ranking | Scans all codes; raw snapshots, features, and projections consume memory in addition to those 16 bytes |
| `faiss` | Optional CPU `IndexFlatL2` over standardized float32 level features, with deterministic corpus-ID handling of boundary ties | Exhaustive vector scan; original-metric candidates remain approximate |
| `faiss_hnsw` | Optional CPU HNSW graph over the same float32 features, with M=32, efConstruction=80, and per-query efSearch at least 64 and the candidate budget | Adds ANN candidate misses; multi-thread graph construction is not guaranteed to reproduce the same candidate subset across rebuilds |

Descriptors cover the full retained time range. Event and spectral features
also inspect the full retained observations. Index-time resampling, feature
standardization/clipping, phase loss, random projection, mixed-channel means,
and candidate truncation remain approximation layers. Candidate stats list the
layers actually used and separate cache preparation from ranking. This is not a
proof that a particular transient, channel interaction, or timestamp-dependent
neighbor will be retained.

HNSW is an approximate graph index; Flat is an exhaustive vector scan. Both
rerank selected candidates with the original EchoTime metric. Stable ID ties
apply within the selected subset, without promising that independently rebuilt
HNSW graphs select identical subsets. Candidate stats record `faiss_version` and
`faiss_omp_max_threads`; the latter is FAISS's configured OpenMP upper limit,
not a measured active-thread count. It is separate from EchoTime `n_jobs`.
This version does not provide IVF or GPU FAISS.

There is no general recall guarantee for a fixed budget. Candidate cost and
index/feature construction still depend on collection size and strategy.
Approximate mode should be evaluated on the intended data and queries, including
near duplicates and ties.

### Audit cost and interpretation

```python
audited_hits = index.search(
    query, k=10, mode="approximate", candidates=32,
    strategy="multiview", audit=True,
)
print(audited_hits.recall_estimate)
print(audited_hits.stats["candidate_recall_at_k"])
print(audited_hits.stats["result_recall_at_k"])
```

`audit=True` additionally runs a certified query covering the full collection.
It pays that cost to obtain the query's ground truth. `recall_estimate` is this
single query's measured candidate recall, with `audit_queries=1`; it is not a
population confidence bound. `audit_seconds` is reported separately, and
`elapsed_seconds` includes the audit. Without an audit, recall remains `None`.
Do not include audit work in a claimed low-latency serving path by accident, or
exclude it while claiming that every live query is audited for free.

### Refine a provisional result

```python
final_hits = index.refine(query, fast_hits, k=10)
assert final_hits.certified
```

`refine` uses provisional IDs to choose a useful evaluation order, then covers
the rest of the collection. Provisional scores and certificates are recomputed;
they are not trusted as evidence for the new query. This is a warm-started
certified search, not a saved DP frontier or an interruption/resume protocol.

## 6. Range and batch queries

```python
nearby = index.range_search(query, radius=100.0)
many = index.search_batch(bank[:4], layout="rows", k=5)
```

`range_search` returns every non-NaN distance less than or equal to the radius,
including equality. It currently supports distance targets only; similarity
thresholds are not overloaded into the radius API. `search_batch` returns one
`SearchResult` per query and reuses the same collection and feature caches.

## 7. Snapshot persistence and memory mapping

```python
from pathlib import Path

snapshot_path = Path("my_dtw_index")  # Choose a new directory.
index.save(snapshot_path)
loaded = SearchIndex.load(snapshot_path, mmap=True, backend="auto", n_jobs=1)
loaded_hits = loaded.search(query, k=10)
```

The snapshot contains numeric `.npy` arrays and a JSON manifest for target,
parameters, shapes, offsets, timestamps, and format version. It does not contain
pickled executable objects. Saving refuses an existing destination. Loading
checks the format, score-semantics version, array schema, offsets, and shapes.

`mmap=True` maps raw numeric storage read-only. Derived features and FAISS state
are rebuilt lazily in the loading process, so a freshly loaded index can have a
larger first-query cost than an already warmed one. Memory mapping does not
eliminate the memory needed for materialized feature caches.
Keep snapshot files unchanged while an index maps them. Index metric
configuration is fixed; build another snapshot to change the target or parameters.

`load(..., backend=None)` resolves a backend on the loading machine instead of
forcing the original machine's native extension. Pass `backend` and `n_jobs`
explicitly for a controlled benchmark. A saved snapshot preserves data and
configuration; it does not freeze NumPy/SciPy, compiler behavior, or the installed
EchoTime implementation. Record those versions when reproducibility matters.

## 8. Rolling exploration with a separate fast definition

```python
from echotime.similarity import rolling_similarity

full = rolling_similarity(left, right, window=60, step=5)
fast = rolling_similarity(left, right, window=60, step=5, mode="fast")
```

The default `mode="full"` preserves all 11 original output columns and the
per-window resampling semantics. Its implementation avoids diagnostics and
report text that the returned rows do not need.

`mode="fast"` returns only `start`, `stop`, `pearson_r`, and
`first_difference_r`. It uses raw positional windows, pairwise deletion for
nonfinite observations, float64 moving moments, periodic recentering, and direct
recomputation for numerically uncertain windows. Channel-wise correlations are
averaged; mismatched channel counts use aggregate raw trajectories. It does not
estimate the five-component similarity score. Timestamps are rejected because
this mode does not implement time alignment; `n_points` applies only to full mode.

Use fast rolling to screen locations for subsequent complete comparisons. Its
runtime advantage must be described together with its reduced output and changed
window definition.

## 9. Validate before interpreting speedups

```bash
python -m pytest tests/test_acceleration_golden.py tests/test_native_equivalence.py -q
python benchmarks/run_suite.py --list
python benchmarks/run_suite.py --profile smoke --backend native \
  --out benchmark-results/current-smoke.json
```

The committed [golden reference](../tests/golden/README.md) was captured from the
unmodified original Python implementation. It checks all 16 batch metrics and
complete high-level outputs. The benchmark defaults to small inputs, records
actual package/source identity, separates preparation and validation costs, and
reports optional APIs as unavailable rather than inventing results.
On a different numerical environment, use the documented original-source
sidecar protocol to distinguish environment drift from a code regression. It
retains strict A equality and the historical fixture separately; a portable
comparison by itself does not establish exact equivalence.

Read search `stats` with the timing: candidate count, explicit bounds, exclusions,
exact evaluations, cutoff abandonments, DP cells, preparation/bound/exact time,
effective threads, and coverage. A bound that saves DP cells can still be slower
if its own Python work dominates. A full-scan fallback remains correct even when
its indexing overhead exceeds a direct batch call.

Large comparisons, matched baselines, recall limitations, memory accounting, and
the next GPU decision are documented in the
[server handoff](acceleration_server_handoff.md). Local smoke success establishes
working instrumentation and small-case correctness; it does not establish the
server performance targets from the development plan.
