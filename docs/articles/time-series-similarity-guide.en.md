# Time-series similarity: choosing between DTW, matrix profiles and learned representations

**A practical comparison of tasks, assumptions and Python tools.** Reviewed 29 October 2026. [中文版](time-series-similarity-guide.zh-CN.md)

For the calculation behind a method, open the [animated Methods Atlas](https://zipengwu.me/EchoTime/guide/methods.html#method-animations): each of its 137 entries has a GIF, a static summary, four explanatory stages, explicit example inputs and interpretation limits. Use the method name to find the corresponding explanation.

Two curves can share a shape and differ in energy consumption. Two recordings can contain the same short event while looking different overall. Two datasets can have similar spectra and different underlying mechanisms. A useful similarity method starts with a decision about which of these relationships matters.

The selection rule used in this guide is simple: **define the object being compared, decide which differences should remain visible, then choose the representation, comparison rule and implementation.** This is a proposed decision framework. The method descriptions below are supported by original papers and official documentation; the guide contains no new runtime or accuracy leaderboard.

## 1. First decide what constitutes a match

| Question | Object being compared | Output to evaluate |
|---|---|---|
| Which complete recording resembles this recording? | Whole series or explicitly segmented episodes | Ranked recordings and their relevance |
| Where does this short pattern recur? | A query against candidate subsequences | Match locations, durations and distances |
| Which datasets have comparable temporal characteristics? | Distributions of series or structural summaries | Specific properties that agree or differ |
| What discrepancy should a model minimize? | Predicted and observed sequences, or learned representations | Optimization behaviour and downstream performance |

A whole-recording average can obscure one short event. A subsequence search can find a close local match in a recording whose remaining content is unrelated. A dataset profile can support exploratory grouping without establishing that individual trajectories correspond. Keeping these outputs separate makes a comparison easier to interpret. The distinction between whole-series and subsequence search also appears explicitly in [aeon's search interfaces](https://www.aeon-toolkit.org/en/stable/examples/similarity_search/similarity_search.html).

Before selecting a method, write one concrete acceptance statement. For example: “Retrieve recordings containing the same machine operating cycle; allow modest timing variation, but retain the difference between normal and excessive vibration.” That sentence gives both a desired invariance and a difference that should survive preprocessing.

## 2. Every invariance removes information

For a nonconstant series (x), positive rescaling and translation give the same standardized shape: (z(3x+7)=z(x)). This follows directly from subtracting the mean and dividing by the standard deviation. It is useful when sensor gain and offset are irrelevant. It loses the amplitude and level information needed to compare absolute loads.

| Processing or comparison choice | Information it can discount | Check before using it |
|---|---|---|
| Per-series z-normalization | Mean level and positive amplitude scale | Should absolute level or excursion size distinguish a match? |
| Global-shift matching | A common displacement of the waveform | Is event timing itself part of the target? |
| Local time warping | Some differences in local duration and pace | Which duration changes are physically acceptable? |
| Magnitude-spectrum comparison | Fourier phase | Do event order and precise timing matter? |
| Summary-feature comparison | Details not retained by the features | Can important counterexamples share those summaries? |
| Learned representation | Distinctions suppressed by training and pooling | Does training preserve the distinctions in this retrieval task? |

The trade-off has a mathematical consequence. If a feature map φ sends two distinct inputs to the same vector, Euclidean distance between their features is zero. It remains a metric in feature space, but cannot separate every original series. This does not make the representation unusable; it tells you exactly which claim its distance can support.

## 3. What the main method families compare

**Pointwise distances and correlation.** On a shared observation grid, Euclidean or absolute error preserves disagreement at each aligned position. Correlation describes association after centring and scaling; it does not measure absolute agreement. For equal-length nonconstant vectors standardized with population variance, the identity $\|z(x)-z(y)\|^2 = 2n(1-r)$ explains why normalized Euclidean distance and Pearson correlation rank pairs equivalently under these conditions. Missing-data policies and different normalization conventions can break that equivalence.

**DTW and constrained DTW.** DTW searches admissible monotone alignment paths. The local cost, endpoint rules and allowed paths define the calculation. A warping band limits the allowed deformation. Standard DTW does not satisfy all metric axioms, so downstream procedures requiring a metric need separate justification. See the [tslearn formulation and constraints](https://tslearn.readthedocs.io/en/stable/user_guide/dtw.html).

Inspect the alignment as well as the score. A low cost can result from a path that repeatedly stretches a scientifically important episode. Whether that is acceptable follows from the task. Also record whether an implementation reports a sum of absolute costs, a sum of squared costs, its square root, or a normalized transformation; these quantities are not interchangeable.

**Global shape alignment and local shape descriptors.** The SBD comparison used in k-Shape searches normalized cross-correlation over shifts. The k-Shape algorithm additionally defines a centroid update. [Paparrizos and Gravano (2015)](https://www.cs.columbia.edu/~gravano/Papers/2015/sigmod2015.pdf) provide the original formulation. [shapeDTW](https://doi.org/10.1016/j.patcog.2017.09.020) instead builds local descriptors before alignment. A global shift and a locally varying alignment permit different changes; a descriptor's neighbourhood size introduces another modelling choice.

**Edit-based and penalized alignment.** LCSS, EDR, ERP, MSM and TWE specify different matching, insertion/deletion, split/merge or temporal penalties. Their names do not establish identical robustness or mathematical properties. Choose the cost and threshold with the measurement units in view. The [literature map](../references/time-series-similarity-literature.md) links their original definitions. A more recent example, [ADTW (2023)](https://doi.org/10.1016/j.patcog.2023.109333), penalizes warping with an additive cost. A penalty controls a modelling preference and must be scaled and selected consistently.

**Feature, spectral and symbolic comparisons.** A feature map can isolate a property such as autocorrelation, frequency content, trend or a symbolic pattern. For exploratory comparisons, inspect the property directly and name it in the result: “similar normalized spectra” is a narrower, testable statement than “the same temporal process.” Frequency comparisons require compatible physical sampling scales; an array index alone does not define hertz.

For multivariate data, specify which channels correspond and whether they share one alignment path. A joint path constrains the channels to move together; channel-wise paths permit separate adjustments. [d'Hondt et al. (2025)](https://doi.org/10.1145/3725258) evaluate distance families together with normalization and channel-dependency choices. Their study supports including these choices in the comparison protocol. It does not establish one setting for every application.

## 4. A matrix profile changes the search object

In its standard form, a matrix profile stores each fixed-length subsequence's distance to its nearest eligible neighbour, commonly using z-normalized Euclidean distance. A self-join excludes trivial nearby matches; a join between recordings searches another series. [STUMPY's introduction](https://stumpy.readthedocs.io/en/stable/Tutorial_The_Matrix_Profile.html) and [AB-join tutorial](https://stumpy.readthedocs.io/en/latest/Tutorial_AB_Joins.html) explain these operations.

This representation is useful for asking where repeated or unusually isolated patterns occur. A large profile value identifies isolation under the chosen window, distance and eligible comparison set. Assigning that segment a clinical or engineering meaning requires additional evidence.

Window length is part of the question. An event occupying five samples and a cycle occupying five hundred samples should not silently be evaluated as the same search problem. For a reproducible result, report the window, normalization, exclusion policy, constant-window convention and join direction. If several lengths are searched, state how matches across lengths are selected and compared.

## 5. Learning a representation and learning with a loss

[Soft-DTW](https://proceedings.mlr.press/v70/cuturi17a.html) uses a smooth aggregation over alignment costs, enabling differentiation with a suitable ground cost and positive smoothing parameter. This makes it useful as an optimization component. Its raw value can be negative and need not be minimized at equality. [Blondel, Mensch and Vert (2021)](https://proceedings.mlr.press/v130/blondel21a.html) introduce corrected divergences and establish properties under stated assumptions. A smooth loss, a nonnegative divergence and a mathematical metric have different requirements.

Learned embeddings provide another comparison space. [TS2Vec](https://ojs.aaai.org/index.php/AAAI/article/view/20881) uses hierarchical contrastive learning to build timestamp and subsequence representations. [MOMENT](https://proceedings.mlr.press/v235/goswami24a.html) supplies pretrained representations for multiple time-series tasks. Both motivate evaluating learned representations; neither citation settles the relevance definition for a new retrieval application.

Recent retrieval-augmented systems make the distinction especially useful. [TS-RAG (NeurIPS 2025)](https://proceedings.nips.cc/paper_files/paper/2025/hash/eed25c037bc08afcbefab6f7a6b700e0-Abstract-Conference.html) retrieves segments to support forecasting. Forecast accuracy measures the combined system's endpoint. A claim about retrieval quality additionally needs a relevance target and retrieval evaluation.

For an embedding-based comparison, record the checkpoint, training exposure, input length, preprocessing, pooling and latent distance. Validate that known task-relevant differences remain distinguishable. For example, a representation that places small and large excursions together may suit shape retrieval while failing an amplitude-sensitive search.

## 6. Which Python library fits the output?

The tools below overlap. The table identifies useful entry points, based on official documentation checked on the review date; it is not a speed ranking.

| Tool | Relevant documented capabilities | A useful starting task |
|---|---|---|
| [aeon](https://www.aeon-toolkit.org/en/stable/api_reference/distances.html) | Multiple distances, paths, pairwise calculations and [similarity-search estimators](https://www.aeon-toolkit.org/en/stable/examples/similarity_search/similarity_search.html) | Compare distance choices or build whole-series/subsequence search |
| [tslearn](https://tslearn.readthedocs.io/en/stable/user_guide/userguide.html) | DTW, soft-DTW, barycentres and time-series learning | Connect an alignment geometry to clustering or learning |
| [DTAIDistance](https://dtaidistance.readthedocs.io/en/latest/modules/dtw.html) | DTW implementations, paths, pruning and pairwise matrices | Compute and inspect DTW alignments and distances |
| [STUMPY](https://stumpy.readthedocs.io/en/stable/Tutorial_The_Matrix_Profile.html) | Matrix profiles and subsequence joins | Locate repeated or isolated fixed-length patterns |
| [sktime](https://www.sktime.net/docs/get-started/) | Interfaces and compositions across time-series learning tasks | Integrate transformations, estimators and evaluation |
| [EchoTime](https://github.com/ZipengWu365/EchoTime) | Composite series reports, profile comparison, HTML and JSON output | Inspect and communicate several structural views together |

Read the exact function's documentation before comparing numeric outputs. For example, DTAIDistance's `distance_fast` selects its C implementation and pruning defaults. EchoTime's low-level elastic `mode="fast"` uses bounded-resolution screening. The shared word “fast” does not imply the same approximation policy. [DTAIDistance API](https://dtaidistance.readthedocs.io/en/latest/modules/dtw.html) · [EchoTime implementation](https://github.com/ZipengWu365/EchoTime/blob/main/src/echotime/similarity_methods.py).

## 7. A comparison protocol you can defend

The following is a recommended procedure, rather than an empirical finding about a particular method.

1. **Freeze the match definition.** Specify the query, eligible candidates, physical units, duration, tolerated transformations and relevance labels. Class labels can be one relevance definition; they need not encode every scientifically meaningful match.
2. **Protect the evaluation boundary.** Split by the independent unit appropriate to the application before creating overlapping windows. Keep near-duplicate windows and future observations out of a retrieval pool when they would make the intended evaluation trivial or unavailable in practice.
3. **Expose preprocessing.** Report normalization, timestamp handling, gap treatment, channel order and resampling. Keep processing identical when isolating the effect of a distance, or explicitly compare the combined pipelines.
4. **Select parameters without using test outcomes.** Alignment windows, edit thresholds, pooling and learned checkpoints all belong to the protocol. If labels are used for selection, report that supervision.
5. **Measure the requested output.** Retrieval needs relevance-based ranking measures; alignment needs correspondence evidence; clustering needs a clustering evaluation; a forecasting system needs its forecast endpoint. Add runtime and memory for the actual workload.
6. **Inspect informative failures.** Include pairs with equal shape but different amplitude, a shifted event, changed duration and missing observations when those cases are relevant. Keep these controlled examples separate from evidence on real data.

For an approximate search, measure neighbour recall against an exact reference on a declared evaluation set. Recomputing precise distances for the returned shortlist improves those scores, but cannot recover a candidate the first stage omitted.

## 8. Use EchoTime to inspect several structural views

EchoTime provides a compact way to generate a component-level comparison and share it. The current `compare_series` implementation resamples each input to a common number of points, standardizes channels, and combines shape, DTW-related, trend, derivative and spectral components. Its default is 256 resampled points. When timestamps are supplied, each input's time span is normalized separately; absolute duration and clock alignment therefore need an explicit check outside this report. See the [inspected implementation](https://github.com/ZipengWu365/EchoTime/blob/320b7e65c74be6decef665cea87f56c5dc88ccd2/src/echotime/similarity.py).

```bash
python -m pip install echotime
```

```python
from pathlib import Path
import numpy as np
from echotime import compare_series

# Synthetic illustration of the report interface; no benchmark claim.
t = np.linspace(0, 4 * np.pi, 128)
x = np.sin(t)
y = np.sin(t + 0.2)

report = compare_series(x, y, left_name="reference", right_name="shifted")
print(report.to_summary_card_markdown())
Path("similarity_report.html").write_text(
    report.to_html_report(), encoding="utf-8"
)
```

Read the components and processing choices alongside the overall score. The weighted score is an exploratory summary, with no demonstrated probability calibration. A profile-level comparison similarly describes agreement between selected structural axes; it supplies no independent evidence of a shared causal mechanism or successful model transfer.

The practical next step is to take a pair whose similarity your team can explain, inspect the report, and compare its component behaviour against that explanation. Use a dedicated alignment or subsequence-search implementation when its outputs are required. The [method atlas](../../SIMILARITY_METHOD_ATLAS.md) distinguishes EchoTime coverage from broader methods, and the [literature map](../references/time-series-similarity-literature.md) provides the sources for extending the comparison.

---

**Scope and provenance.** This is a targeted narrative guide, reviewed against original papers, official software documentation and repository source. It does not claim exhaustive coverage, independent reproduction of cited studies, or measured superiority of EchoTime. [Evidence ledger and editorial checks](README.md).
