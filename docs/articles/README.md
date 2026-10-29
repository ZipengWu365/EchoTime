# Time-series similarity articles

These articles compare tasks, mathematical assumptions and software interfaces. They do not report a new cross-library benchmark.

| Article | Language | Reviewed |
|---|---|---|
| [Time-series similarity: choosing between DTW, matrix profiles and learned representations](time-series-similarity-guide.en.md) | English | 2026-10-29 |
| [时序相似性方法盘点：DTW、矩阵轮廓与学习表示该怎么选](time-series-similarity-guide.zh-CN.md) | 简体中文 | 2026-10-29 |

## Evidence ledger

The ledger was assembled before drafting. Citation roles describe what each source supports; recommendations in the articles are explicitly presented as a proposed evaluation procedure. Software documentation was checked on 2026-10-29. This is a targeted narrative comparison, with no claim of systematic-review completeness. No library speed or accuracy ranking was measured for these articles.

| Claim or object | Role | Primary source | Boundary |
|---|---|---|---|
| DTW aligns ordered observations under admissible paths; local cost and path constraints define the result | Definition / Tool | [tslearn DTW guide](https://tslearn.readthedocs.io/en/stable/user_guide/dtw.html) | A package's transformed similarity score need not equal a canonical raw DTW distance |
| SBD uses normalized cross-correlation to allow a global shift; k-Shape also defines a centroid procedure | Origin / Definition | [Paparrizos and Gravano, SIGMOD 2015](https://www.cs.columbia.edu/~gravano/Papers/2015/sigmod2015.pdf) | A global shift differs from local nonlinear time deformation; classification/clustering results do not establish universal retrieval performance |
| shapeDTW aligns sequences of local descriptors | Origin / Definition | [Zhao and Itti, Pattern Recognition 2018](https://doi.org/10.1016/j.patcog.2017.09.020); [author preprint](https://arxiv.org/abs/1606.01601) | Descriptor and neighbourhood settings are part of the method |
| ADTW adds a penalty for warping | Origin / Definition | [Herrmann and Webb, Pattern Recognition 2023](https://doi.org/10.1016/j.patcog.2023.109333) | Parameter scale and tuning protocol matter; no claim of task-independent dominance |
| Soft-DTW replaces hard path minimization with a smooth aggregation | Origin / Definition | [Cuturi and Blondel, ICML 2017](https://proceedings.mlr.press/v70/cuturi17a.html) | Differentiability requires a suitable ground cost and positive smoothing parameter |
| Raw soft-DTW can be negative; corrected divergences have assumptions | Limitation / Boundary | [Blondel, Mensch and Vert, AISTATS 2021](https://proceedings.mlr.press/v130/blondel21a.html) | The paper's divergence result is conditional on the ground cost; it does not establish the triangle inequality |
| A matrix profile records nearest-neighbour distances for fixed-length subsequences | Definition / Tool | [STUMPY matrix-profile tutorial](https://stumpy.readthedocs.io/en/stable/Tutorial_The_Matrix_Profile.html) | Standard formulation uses z-normalized Euclidean distances and a self-match exclusion policy |
| STUMPY supports joins between two series and optional normalization | Tool | [STUMPY AB joins](https://stumpy.readthedocs.io/en/latest/Tutorial_AB_Joins.html) | Window length, join direction and normalization remain part of the query |
| TS2Vec learns hierarchical contrastive representations of timestamps and subsequences | Origin / Boundary | [Yue et al., AAAI 2022](https://ojs.aaai.org/index.php/AAAI/article/view/20881) | Classification, forecasting and anomaly-detection evidence does not establish every retrieval objective |
| MOMENT supplies pretrained representations for multiple time-series tasks | Origin / Boundary | [Goswami et al., ICML 2024](https://proceedings.mlr.press/v235/goswami24a.html) | Pretraining does not by itself determine a domain's similarity labels |
| TS-RAG retrieves segments to support forecasting | Origin / Boundary | [Ning et al., NeurIPS 2025](https://proceedings.nips.cc/paper_files/paper/2025/hash/eed25c037bc08afcbefab6f7a6b700e0-Abstract-Conference.html) | Forecasting improvement is an endpoint distinct from retrieval relevance |
| Multivariate comparisons depend on normalization and channel assumptions | Contrast / Boundary | [d'Hondt et al., PACMMOD 2025](https://doi.org/10.1145/3725258); [author institution record](https://research.tue.nl/en/publications/a-structured-study-of-multivariate-time-series-distance-measures/) | Findings concern the evaluated measures, datasets and protocols |
| aeon offers distances, alignment paths, and whole-series/subsequence search | Tool | [aeon distances](https://www.aeon-toolkit.org/en/stable/api_reference/distances.html); [similarity search](https://www.aeon-toolkit.org/en/stable/examples/similarity_search/similarity_search.html) | Availability differs by estimator and installed version |
| tslearn offers time-series learning and DTW/soft-DTW-based workflows | Tool | [tslearn documentation](https://tslearn.readthedocs.io/en/stable/); [user guide](https://tslearn.readthedocs.io/en/stable/user_guide/userguide.html) | Do not infer relative runtime from API availability |
| DTAIDistance provides C implementations, pruning, paths and pairwise matrices | Tool | [DTW API](https://dtaidistance.readthedocs.io/en/latest/modules/dtw.html) | Its `distance_fast` name refers to the accelerated implementation; it does not imply downsampling |
| sktime supports multiple learning tasks and composable interfaces | Tool | [sktime get-started guide](https://www.sktime.net/docs/get-started/) | Treat as overlapping ecosystem functionality, not an exclusive category |
| EchoTime's `compare_series` is a resampled, normalized, composite report | Tool / Limitation | [Inspected source](https://github.com/ZipengWu365/EchoTime/blob/320b7e65c74be6decef665cea87f56c5dc88ccd2/src/echotime/similarity.py) | Fixed weights and qualitative labels are not calibrated probabilities; inspect later code for changes |
| EchoTime's `compare_profiles` compares profile-axis summaries | Tool / Boundary | [Inspected source](https://github.com/ZipengWu365/EchoTime/blob/320b7e65c74be6decef665cea87f56c5dc88ccd2/src/echotime/similarity.py) | Structural agreement does not establish shared mechanisms or successful model transfer |

## Editorial checks

- **Facts:** linked methods to original papers or official documentation; kept literature coverage separate from implemented APIs; reported no new performance numbers.
- **Expression:** explained comparison objects and information loss before method names; used explicit assumptions for normalization, time alignment and multivariate channels.
- **Distribution:** one clear question per social card; links lead to the full comparison and reproducible package entry point. Social copy is stored as drafts in [`social/2026-10-29-similarity-roundup.md`](../../social/2026-10-29-similarity-roundup.md).

Review links and implementation notes before reusing this material after package updates. The companion [literature map](../references/time-series-similarity-literature.md) records the broader paper inventory.
