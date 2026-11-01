# Changelog

## 0.18.0.dev0 — 2026-11-01 CPU performance

Numerics are unchanged: every accelerated path is tested against the
pure-Python reference (bit-identical for elastic distances, shift-based
correlation, sample/permutation entropy and ordinal counts; within rounding,
<= 1e-12, for embedding distances and the vectorised correlation summary).
See docs/performance.md and benchmarks/perf_2026-11.csv.

### Native kernels (optional C++ extension)

- Add `echotime._echotime_native` (C++17, pybind11, std::thread): LCSS, EDR,
  ERP, TWED and DTW dynamic programmes and sample-entropy template counts. The
  GIL is released and pairs run in parallel; univariate pairs of equal length
  run 8 at a time in SIMD lanes (GCC/Clang vector extensions), and banded rows
  cost O(band) instead of O(m). Built with -O3, no fast-math and
  -ffp-contract=off so results equal the Python reference bit for bit.
- The extension is optional (`setup.py` marks it optional): without a C++
  compiler the install succeeds and the pure-Python reference runs.
  `ECHOTIME_BACKEND=python|native|auto`, `set_similarity_backend()` and
  `similarity_backend_info()` select and report the backend;
  `ECHOTIME_NUM_THREADS` sets the default thread count.
- `lcss_similarity`, `lcss_distance`, `edr_distance`, `erp_distance`,
  `twed_distance`, `compare_series` (its DTW) and `sample_entropy` (and hence
  `profile_series`/`profile_dataset`) use the kernels automatically.

### Batch APIs (new, additive)

- `pairwise_distance_matrix`, `cross_distance_matrix`, `one_vs_many` and
  `paired_distances` evaluate any of 16 metrics over many pairs, preparing each
  series once. Shift-based correlation uses one FFT per series and one inverse
  FFT per pair, then recomputes the leading lags with the dot products
  `np.correlate` uses, so values and lags are identical to the single-pair
  functions.
- New `dtw_distance(x, y, window=None, normalize=False)`: classic DTW with an
  optional Sakoe-Chiba band; equals NeuroTime's `dtw_distance` for
  equal-length univariate input.

### Faster pure-Python paths (also used as fallback)

- Ordinal-pattern counts (`ordinal_pattern_js_distance`, `permutation_entropy`)
  are vectorised with the same stable sort per window.
- `lz_complexity` computes the median once instead of once per sample.
- `compute_multivariate_metrics` computes all pairwise correlations with one
  centred cross-product (native backend only; the loop remains the reference).

### Version

- Package version 0.18.0.dev0 in pyproject, `__version__`, `PACKAGE_VERSION`
  and the demo manifests. Generated pages and marketing text are not
  regenerated for this development version.

## Unreleased — 2026-10-29 maintenance

These changes describe the repository source. The package version remains 0.17.1
until a separate release is made; existing PyPI artifacts are unchanged.

### Shared-input similarity lab and mechanism tour

- Add a static interactive lab with one shared 64-sample input pair, seven
  controlled transformations, 21 levels each and eleven explicit reference
  definitions. Views expose the actual alignment, feature representation,
  contribution and score for the selected pair.
- Include a reproducible overview GIF and static poster, downloadable numerical
  states, keyboard controls, explicit preprocessing and per-method units.
- Add an English mechanism-level article linking original papers, comparing
  retained information and allowed deformations, and presenting three verified
  numerical examples plus research questions for GitHub Discussions.
- Link the lab and article from the existing Methods Atlas, reading pages and
  README; include all six lab resources and the article in wheel and Pages
  exports. Release refresh can explicitly reuse verified method animations.

### Animated method explanations

- Add individual deterministic GIFs and static posters for the 10 native report
  components and all 127 registry entries. Each method includes English/Chinese
  explanations, four calculation stages, parameters, numerical traces, source
  links and interpretation limits.
- Extend the existing Methods Atlas in place with search, bilingual text,
  keyboard-accessible click-to-play/stop controls and static defaults. Opening
  the page starts no animation; only one requested animation plays at a time.
- Keep current implementations, reference-formula demonstrations and explicitly
  specified encoder/model protocols distinct. The examples make no training or
  benchmark-performance claims and add no new public similarity algorithms.
- Package the assets with the wheel and static export; add complete-coverage,
  numerical-trace, link and asset-integrity checks to the documentation build.
- Link each existing atlas row to its explanation and add an animation entry
  point to the README and both method-selection articles.

### Numerical corrections

- Correct multichannel normalized cross-correlation: the numerator and Frobenius
  norms already aggregate the channels. The extra channel-count divisor has been
  removed. Identical nonconstant two-channel inputs now give `max_ncc = 1` and
  `sbd = 0`, instead of `0.5` for both.
- Correct TWED's dynamic-programming boundary to the original formulation:
  `D(0,0) = 0`, and nonempty prefixes against an empty prefix have infinite cost.
  This changes some valid-input results from earlier source versions. For
  `twed_distance([100.0], [0.0, 100.0])` with default parameters, the old boundary
  produced `1.003`; the corrected recurrence gives `201.001`.
- Reject invalid elastic-distance parameters and invalid TWED timestamps instead
  of returning misleading numeric scores. See the [code audit](docs/maintenance/2026-10-29-code-audit.md)
  for the precise checked domains and reproduction cases.

The TWED correction follows [Marteau's original formulation, Figure 2](https://arxiv.org/pdf/cs/0703033)
and is covered by hand-calculated cases and regression tests. The high-level
`compare_series` composite does not call `twed_distance`.
Recompute stored low-level TWED results or multichannel NCC/SBD results if these
functions were used in previous analyses. No full scientific benchmark has been
rerun as part of this maintenance update.

### Compatibility and maintenance

- Include the small tutorial-data, gallery-source, and visual resources needed
  during package import and Pages export in the wheel. Installed packages now
  resolve these resources without depending on the current working directory.
- Add an explicit runtime-resource manifest and a build freshness check.
- Declare Python 3.10+ to match the existing use of `dataclass(slots=True)`.
- Require a build backend that supports the project's SPDX license metadata.
- Add complete test-suite CI on Python 3.10, 3.11 and 3.13, plus source/wheel build,
  metadata validation, and a wheel import check outside the repository checkout.
- Correct selected mathematical property labels and cost definitions in the
  generated similarity atlas. Properties of a feature-space distance are kept
  separate from properties on the original sequence domain.

### Reading and documentation

- Add cited English and Chinese method-selection articles, a primary-source
  literature map, reusable JSON/BibTeX records, and social copy drafts.
- Link the articles from the README and documentation; include the generated
  reading pages in the wheel and Pages export.
- Add reproducible Markdown rendering, local-link checks, source hashes and a CI
  freshness check. Chinese page metadata now records its actual language.
- Preserve the repository's existing logo and maintainer image in the README
  generator so a refresh does not overwrite these choices.
- Correct the quickstart's expected output and the flagship demo descriptions
  to match the executed summary format and the actual public-data snapshots.
