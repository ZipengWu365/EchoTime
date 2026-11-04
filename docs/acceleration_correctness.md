# Acceleration correctness contract

This document describes the guarantees actually implemented by the acceleration
branch. The design proposal in `planning/ACCELERATION_PLAN.md` contains further
work; an entry in that proposal is not evidence that the corresponding feature
has shipped. See [the implementation status](acceleration_status.md).

## 1. What an exact search reproduces

For a low-level target, the reference is a complete `one_vs_many` call with the
same metric parameters, input interpretation and selected backend. Sort ascending
for distances, descending for `max_ncc`, `independent_max_ncc` and
`lcss_similarity`. NaN sorts after all numeric values, and original corpus
position breaks every tie. Infinity is a numeric value, not a missing result.

For `similarity_score` or `component_mean`, the reference is the corresponding
field of `compare_series` at the index's fixed `n_points`. These are different
objectives. The five component weights, component order, geometric combinations,
channel aggregation and finite-component renormalization remain unchanged.

The native embedding implementation already uses row-wise vector reductions;
the Python implementation uses scalar norms. Those paths can differ by an ULP.
Search preserves the selected backend's original values. In a mixed-channel
embedding bank, the original batch function falls back for the **whole request**.
`VectorCache` fixes that policy for the whole database, so changing block size or
candidate budget cannot silently switch a pair between numerical definitions.

The frozen regression file is generated independently from the original Python
implementation at `08f7df742b364175105e957d39f9f81fe6211bb3`. Its A contracts use
float-hex equality; B contracts use declared tolerance. No regression expected
values are regenerated from the accelerated implementation. The portable golden
option is a diagnostic for another numerical platform, not an A-class pass.

## 2. Coverage and ties

A certified query covers every corpus position exactly once, either by accepting
its complete value or by a conservative exclusion. The top-k heap uses
`(is_nan, signed_value, corpus_id)` as its logical ordering. A candidate is
excluded by a lower bound only when `bound > kth_distance`; a similarity upper
bound must satisfy `bound < kth_score`. Equality always survives.

A block may use the threshold from the preceding block. That older threshold
can only admit unnecessary work: distance thresholds decrease and similarity
thresholds increase as more complete candidates enter the heap. Warm-start IDs
change evaluation order; they do not remove the remaining database from coverage.
`refine` recomputes warm-start values and then covers the rest of the database.

`k=0` has a vacuous exact answer. Otherwise an incomplete heap, or a heap whose
worst item is NaN, cannot prune using a finite top-k threshold. Range queries
include all non-NaN distances `<= radius`, including the threshold itself.

## 3. DTW lower bounds and floating point

EchoTime DTW has absolute local costs in one channel and row-L2 costs across
multiple channels. It is not squared Euclidean DTW. A normalized distance divides
the accumulated cost by `n+m`; the same division is applied to a lower bound.

The endpoint bound includes the first and last required local costs, with a
single cost for `n=m=1`. The Keogh bound uses each actual resolved band, including
`max(window, abs(n-m))`, and the distance from each row to the corresponding
axis-aligned envelope box. Forward and reverse bounds are combined with `max`,
never by adding them.

The implementation does not subtract a fitted epsilon and call that a proof.
For finite safe-range inputs, every box-coordinate distance is no larger than
the corresponding absolute local difference. The square, nonnegative row
reduction and square root use the reference arithmetic tree and are monotone.
The bound accumulates rows sequentially rather than with `np.sum`: any complete
path visits those rows in order, and inserting additional nonnegative costs
cannot reduce a round-to-nearest sum. This yields a lower bound on the actual
reference DP, including its summation order. The compiled local multi-channel
reduction reproduces the NumPy reference reduction and is separately tested.

SciPy min/max filters select exactly the same float64 envelope extrema as clipped
row intervals. They introduce no new approximate arithmetic. Unequal lengths use
positive/negative infinity padding for minima/maxima; wide bands use global
extrema. These cases have direct interval-versus-filter bitwise tests.

Empty, nonfinite prepared values and unsafe magnitudes use a trivial bound.
For NaN reference outputs, a numeric inequality is not defined; the trivial
fallback is safe for the ranking convention, and the complete scorer handles
the undefined result. It is not a claim that `0 <= NaN`.

## 4. EDR and LCSS bounds

The matching predicate retains the reference's arithmetic: an absolute threshold
in one channel, or a squared multi-channel sum compared with `epsilon**2`.
Testing the envelope box can overestimate how many observations have a possible
match, which is safe for an upper bound on match counts.

LCSS has at most `min(possible_left, possible_right)` matches. Its distance bound
uses the same `1 - matches/min(n,m)` operation as the reference. EDR costs at
least the maximum of the unmatched-left count, unmatched-right count and length
difference, with the original normalization if enabled. The integer counts
avoid an additional numerical approximation in the combinatorial bound.

The LCSS similarity search does not transform a rounded score threshold into a
distance cutoff. It evaluates the original similarity when the envelope does
not already exclude the candidate; this preserves boundary ties without a
`1 - (1 - score)` round trip.

## 5. Cutoff kernel protocol

`CutoffResult` exposes `value`, `exceeded_cutoff` and `cells_visited`.

- A complete value at or below the cutoff is returned unchanged.
- An exceeded result has `value=NaN` and `exceeded_cutoff=True`. This NaN is a
  protocol placeholder and must never be inserted into a distance matrix as a
  measured value.
- An undefined legacy result has `value=NaN` and `exceeded_cutoff=False`.
- Cutoff units are public metric units, including DTW or EDR normalization.
- Cutoffs use strict comparisons. An exact tie must complete and survive.

For DTW, EDR, ERP and TWED, a full path crosses every row and all transition
costs are nonnegative. A full-row minimum therefore bounds the complete cost.
ERP includes column zero in that minimum: ignoring its deletion prefix would
produce an incorrect certificate. LCSS uses the current best matching count
plus the maximum number of additional matches remaining.

Numeric eligibility checks prevent a certificate from hiding a later NaN.
TWED additionally limits timestamp arithmetic so that, for example, zero
stiffness multiplied by an overflowed time difference cannot create an unseen
`0*inf`. Unmodified full arithmetic is retained when the guard fails.

Very large legal window integers are clamped to a full-width band before C++
index arithmetic. The new entry points thereby avoid the legacy `i+window`
integer-overflow hazard. No relaxed floating-point compiler flags are introduced.

`cutoff_abandoned` includes cases where excess is proved only at the final row.
It is a count of excluded computations, not the fraction of work saved. Actual
DP reduction must be assessed using `cells_visited`. The Python fallback uses
the full reference DP before applying the same protocol, so it can report an
exceeded result without an early-exit speedup.

## 6. Composite upper bound

The four cheap components are computed with the same prepared arithmetic as the
full report. The unknown DTW component is evaluated in two possible validity
branches: a valid value at its maximum of 1, and an invalid value represented by
NaN. Each branch runs the actual fixed-order score helper, including valid-weight
renormalization. The larger finite result bounds the unknown final score.

The same procedure applies to `component_mean` with its original fixed-order
mean. It avoids treating `A+0.20` as universally valid when some components are
invalid. It also avoids claiming that default resampling makes every source
valid: all-NaN or insufficient finite source observations can still follow the
original exception path.

Shared level/difference-DTW budgets obtained by inverting an exponential are not
implemented as certified cuts. The algebraic identity is useful in real
arithmetic, but does not alone prove equivalence to the existing finite-precision
exponential/log/geometric-mean sequence at a ranking boundary.

## 7. Bounds deliberately excluded from certification

The NCC amplitude-spectrum inequality and ERP gap-sum inequality are implemented
as priority-only helpers. Their `SearchBound.certified` flag is False. They are
not used to discard corpus items by the public certified search.

For NCC, the real-arithmetic Fourier inequality does not supply a conservative
error envelope for this FFT implementation. The original complete NCC batch
calculation is therefore retained, with reusable spectra and unchanged exact
lag refinement. Odd-length half spectra have no singleton Nyquist term.

ERP/TWED pivot distances, LB_Webb, EAP state pruning, threshold-derived narrow
EDR bands and block-tree score bounds remain future work. A random property test
alone would not establish a floating-point or metric proof for these additions.

## 8. Approximate retrieval and measured recall

Multiview, pyramid, binary, FAISS Flat and FAISS HNSW descriptors represent the
entire time range. They are candidate generators for the original score, not
certified lower bounds. Representation compression, numerical clipping,
float32 storage and HNSW candidate omissions are disclosed as applicable.

Only selected candidates are reranked, using the original metric values.
`certified=False` remains explicit even if a particular budget happens to cover
the whole database. `audit=True` pays for a complete certified query and reports
that query's measured CandidateRecall@k and result Recall@k. Without an audit,
`recall_estimate=None` means unmeasured. One audited query supplies no population
confidence interval or general recall promise.

## 9. Scope of the performance claim

The `auto` policy uses cached complete native scans when the largest estimated
pair work is at most 65,536 cells times channels. This crossover was introduced
after the local benchmark showed Python lower-bound overhead overwhelming short
native DPs. It changes scheduling only and is a provisional CPU heuristic.
`bounds='none'`, `'cheap'` and `'all'` expose the alternatives for a target server.

The raw snapshots are immutable; mutable caller inputs cannot invalidate a bound
after preparation. Persisted indexes contain JSON and fixed numeric NPY files,
not pickle. Loaded raw storage can be memory mapped. Derived elastic, candidate,
vector and FFT caches still consume RAM; full out-of-core feature execution is
not implemented. `search_batch` performs queries sequentially and uses configured
native threads within each applicable query block.

The tests cover exhaustive short inputs, randomized ragged/multi-channel inputs,
missing and extreme values, exact/adjacent thresholds, repeated IDs, entire-bank
fallback rules, serialization, native/Python parity and all original goldens.
The server acceptance suite supplies the remaining scale/hardware evidence.
