# EchoTime numerical maintenance audit — 29 October 2026

## Scope and execution plan

This is a platform/software maintenance pass against repository baseline
`320b7e65c74be6decef665cea87f56c5dc88ccd2`. It checks public low-level similarity
functions and selected mathematical claims in the method atlas. It does not
introduce a new algorithm or a comparative research benchmark.

The evidence objects are reproducible numerical counterexamples, regression
tests, and corrected method descriptions. They run on a local CPU; no GPU,
cluster allocation, external dataset, or model training is needed. Failed
assertions or incomplete test execution must be reported as failures or
incomplete verification. Research dataset/baseline passports and a production
compute matrix are omitted because this change does not run research
experiments.

## Verified defects and changes

| Area | Observed at the baseline | Change and compatibility impact |
| --- | --- | --- |
| Joint multivariate normalized cross-correlation | An identical, nonconstant two-channel input returned approximately `max_ncc=0.5` and `sbd=0.5`. The numerator was divided by channel count even though the joint norm denominator already included all channels. | Removed the extra division. Nonzero-energy self-comparisons return NCC 1 and SBD 0, independent of channel count. Univariate scores retain the same normalization. Scores for existing multichannel joint comparisons change. |
| TWED dynamic-programming boundary | `twed_distance([100], [0, 100])` returned `1.003` with default parameters because leading deletions were initialized to finite accumulated costs. | Uses the original TWED infinite first row and column, with only `D[0,0]=0`. The example now returns `201.001`. This corrects numerical behavior on valid inputs; previously stored TWED results can change and should be recomputed if this distinction matters. |
| Negative match tolerance | Negative `epsilon` gave different behavior for univariate and multivariate LCSS/EDR: the multivariate squared comparison could make a negative tolerance act positive. | Rejects negative or nonfinite `epsilon` with `ValueError`. Zero remains valid. |
| Invalid elastic costs | Negative `lambda_` and `nu` could make TWED negative; an example with both negative returned `-62.0`. Nonfinite ERP gap values also propagated invalid scores. | TWED costs must be finite and nonnegative; ERP gap values must be finite. |
| Path window | Negative, fractional, and Boolean windows were silently converted or widened. | Requires a nonnegative integer or `None`; NumPy integer scalars remain accepted. The existing widening to at least the sequence-length difference remains. |
| Observation times | Nonfinite, repeated, or reversed TWED timestamps were accepted. Fast downsampling could conceal a local ordering error. | Retained observation timestamps must be finite and strictly increasing; validation happens before fast resampling. |
| Empty NCC input | Empty or entirely nonfinite inputs reached `np.correlate`, which raised an incidental array error. | Returns empty correlation/lag arrays; `max_ncc` and `sbd` return `NaN`, and the existing no-lag sentinel in `best_shift` remains 0. |

The TWED boundary follows Marteau, *Time Warp Edit Distance with Stiffness
Adjustment for Time Series Matching*, IEEE TPAMI 31(2), 2009,
[DOI: 10.1109/TPAMI.2008.76](https://doi.org/10.1109/TPAMI.2008.76).
The [author manuscript](https://arxiv.org/pdf/cs/0703033), Fig. 2, sets the zero
sentinel and infinite boundary. Its metric result depends on positive stiffness
and the stated input/cost assumptions. `nu=0` remains accepted by EchoTime as a
boundary case without that metric guarantee. Window constraints and fast
resampling do not automatically inherit the original theorem.

The TWED regression has a hand-computed expected result. With `x=[100]` and
`y=[0,100]`, the only finite path first matches 100 to 0, costing 100, then
inserts 100, costing `100 + lambda_ + nu = 101.001`. This gives `201.001` and
distinguishes the original boundary from the previous implementation. The
reverse comparison has the same expected result.

## Method-atlas corrections

The underlying registry contains 127 method/variant entries. An entry's presence
does not mean EchoTime implements it, or that every property has been proved or
independently reproduced. This pass checks a limited set of claims and retains
the existing explicit EchoTime implementation-status column.

- RMSE and MAE are metrics on a common fixed-dimensional domain: they are
  positive constant multiples of Euclidean and L1 distance respectively.
- Z-normalized Euclidean/L1 distances are metrics in normalized feature space.
  On original sequences they can identify distinct series related by positive
  rescaling and offset. Constant channels need a declared normalization rule.
- The square root of Jensen–Shannon divergence is the distance on probability
  distributions; ordinal-pattern representations can map distinct series to
  the same distribution, so the original-sequence comparison is a pseudometric.
- ERP requires a clear gap-domain convention before a metric claim. The public
  function gives `erp_distance([1], [0,1], gap_value=0) == 0`; distinct raw
  sequences can therefore coincide when gap values are allowed as observations.
  Channel-independent ERP inherits this qualification.
- Discrete Fréchet distance can identify vertex lists that differ only through
  repeated vertices. A metric claim needs an appropriate equivalence/domain
  convention.
- SAX MINDIST's lower-bound property does not make it a metric. Adjacent symbols
  can have zero separation.
- The native DTW component now states its actual absolute local costs,
  accumulated-cost normalization by `n+m`, re-normalized first differences,
  and exponential/geometric blend. It must not be read as a raw conventional
  square-root-of-squared-cost DTW value or a calibrated probability.
- The native Kendall description now specifies tau-b and its tie corrections,
  matching the SciPy call used by the package.

These changes qualify the mathematical domain and implementation semantics;
they do not establish performance superiority over another package.

## Installed-wheel resource repair

The previous resource resolver looked only beside a source checkout and in the
working directory. Package initialization imports tutorial modules that locate
`examples/data` and `examples/gallery` immediately. Those directories were
included in the source distribution through `MANIFEST.in`, but were absent from
the wheel's package data. The exported site additionally requires selected
image assets. A source-checkout test therefore could not validate the installed
wheel's resource contract.

The resolver now checks the source repository first, the package's frozen
`data/runtime` resources second, and the legacy working-directory location
last. `tools/sync_runtime_assets.py` copies the explicit minimal resource set
and records source SHA-256 hashes. It requires no third-party imports or
network access. The payload contains 18 resources and one manifest, totalling
793,130 bytes at this revision: six data CSVs, one source-provenance JSON, six
gallery source files, and five SVG/PNG assets. Large preview images and
generated reports are excluded.

`python tools/sync_runtime_assets.py --check` detects missing, stale or extra
copies. The release-refresh process synchronizes them after generating preview
assets. Package-data declarations include these resources in the wheel.
Three focused regressions verify the installed-layout fallback, source-copy
precedence and legacy working-directory behavior; they pass in 1.56 seconds.
The release validation additionally installs the actual wheel outside the
checkout and exercises imports and site export; its result belongs with the
integrated package validation, not the simulated-layout unit tests.

## Validation

The focused command is:

```bash
python -m pytest tests/test_similarity_correctness.py tests/test_similarity_methods.py -q
```

It completed with **62 passed in 2.47 seconds** on a CPU environment with
Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, pandas 2.2.3, and pytest 9.2.0.
This includes 49 new parameterized regression cases and 13 existing low-level
method tests. The new cases check self-similarity, duplication invariance,
zero-lag agreement with flattened cosine similarity, the hand-computed TWED
boundary case, invalid parameter domains, timestamp validation before
resampling, and preservation of supplied elapsed times across dropped values.

The full repository command is `python -m pytest -q`. Its integrated outcome
is recorded separately with the release/change summary, because this pass
runs alongside documentation and publishing-system changes. This focused test
result is correctness evidence for the inspected behaviors; its runtime is
not a speed benchmark.

## Remaining scope limits

`mode="fast"` resamples each elastic input to at most 512 samples and uses a
path band. It has no established general error bound or retrieval-recall
guarantee. It can omit a true neighbor from a shortlist, and reranking retained
candidates cannot recover omitted candidates.

Low-level functions remove rows containing nonfinite observations. Supply
explicit TWED timestamps to preserve elapsed time across removed rows. This
maintenance pass does not redesign missing-value semantics or channel-layout
inference. In particular, existing channel-count mismatches can trigger channel
aggregation; callers should supply matched channel layouts when channel
identity matters.

For zero-energy inputs after optional normalization, NCC retains the existing
zero-score convention. Correlation of a constant signal is statistically
undefined; the numerical fallback is not evidence of a measured lack of
association. High-level report components also use normalization and
resampling and should be interpreted according to their documented processing.

The other registry entries, learned representations, model-training behavior,
GPU execution, and cross-platform performance have not received an exhaustive
audit in this maintenance pass.
