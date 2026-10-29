# Time-series similarity: a verified reading map

Checked on **2026-10-29**. This page connects 30 research sources to specific definitions, comparisons and limitations. It complements the [EchoTime method atlas](../../SIMILARITY_METHOD_ATLAS.md); an entry here is a literature reference, not an implementation or performance claim about EchoTime.

The same records are available as [JSON](time-series-similarity-literature.json) and [BibTeX](time-series-similarity-literature.bib). Citation keys are stable across all three files. The JSON records include verification level, successful source URLs, publication status and evidence boundaries.

## What to decide before choosing a score

Specify the comparison object (complete series, a local window, a multivariate event, or a learned representation), the differences that should count as errors, the differences that should be tolerated, and the downstream decision. These are design choices. A citation identifies the mathematical or empirical basis for a candidate; the target application still needs validation.

| Question | Relevant reading | What must remain explicit |
|---|---|---|
| Is timing fixed, globally shifted, or locally warped? | [DTW](#sakoe1978dtw), [SBD/k-Shape](#paparrizos2015kshape), [shapeDTW](#zhao2018shapedtw), [ADTW](#herrmann2023adtw) | Local cost, lag/window, endpoint and penalty policies |
| May unmatched samples be ignored or edited? | [LCSS](#vlachos2002lcss), [ERP](#chen2004erp), [EDR](#chen2005edr), [MSM](#stefan2013msm) | Thresholds, gap values and edit costs |
| Do timestamps and channel synchronization matter? | [TWED](#marteau2009twed), [multivariate DTW](#shokoohi2017multidtw), [2025 comparison](#dhondt2025multivariate) | Time units, shared origin, channel scales and coupled/independent alignments |
| Is the object a training loss or a mathematical metric? | [GAK](#cuturi2011gak), [soft-DTW](#cuturi2017softdtw), [corrected divergences](#blondel2021divergences), [DILATE](#leguen2019dilate) | Ground-cost conditions, differentiability, non-negativity and triangle inequality are separate properties |
| Is the task finding repeated local patterns? | [Matrix Profile](#yeh2016matrixprofile) | Window length, exclusion zone and normalization |
| Is the challenge indexing a large collection? | [SFA](#schaefer2012sfa), [SOFA](#schaefer2025sofa) | Exact target distance, lower-bound conditions, build cost and query workload |
| Can a learned embedding define useful neighbors? | [TS2Vec](#yue2022ts2vec), [SimMTM](#dong2023simmtm), [MOMENT](#goswami2024moment), [TS-RAG](#ning2025tsrag) | Checkpoint, pooling, scaling, data overlap and task-specific relevance evidence |

## Recent additions and their evidence type

The following 2023–2026 papers address different questions. Their outcomes should be compared within those questions.

| Work | What it contributes | Evidence that must not be inferred |
|---|---|---|
| [ADTW, 2023](#herrmann2023adtw) | An additive penalty on warping operations | A universally optimal distance |
| [SimMTM, 2023](#dong2023simmtm) | Similarity-assisted masked representation learning | Validated standalone semantic retrieval |
| [MOMENT, 2024](#goswami2024moment) | General-purpose pretrained time-series models | A universal metric for all notions of similarity |
| [Multivariate comparison, 2025](#dhondt2025multivariate) | Joint evaluation of distances, preprocessing and channel assumptions | A ranking that transfers to every new task |
| [SOFA, 2025](#schaefer2025sofa) | Exact Euclidean nearest-neighbor indexing | General DTW acceleration or semantic ranking quality |
| [TS-RAG, 2025](#ning2025tsrag) | Retrieval-augmented forecasting | A retrieval-quality improvement isolated from the forecasting model |
| [tsdistances, 2026](#azzari2026tsdistances) | CPU/GPU implementations of distance algorithms | A speedup measured in EchoTime or on the reader's hardware |

## Claim-to-citation map

Rows marked `Boundary` include editorial inferences that limit a paper's scope. They do not claim that the cited authors explicitly tested every excluded use.

| ID | Claim supported or bounded | Citation role | Sources |
|---|---|---|---|
| C01 | Alignment restrictions and local costs define the DTW comparison. | Definition | [sakoe1978dtw](#sakoe1978dtw), [herrmann2023adtw](#herrmann2023adtw) |
| C02 | Matching tolerances and gap penalties change the meaning of elastic edit scores. | Definition | [vlachos2002lcss](#vlachos2002lcss), [chen2004erp](#chen2004erp), [chen2005edr](#chen2005edr), [stefan2013msm](#stefan2013msm) |
| C03 | Timestamp differences and channel coupling are explicit modeling choices. | Boundary | [marteau2009twed](#marteau2009twed), [shokoohi2017multidtw](#shokoohi2017multidtw), [dhondt2025multivariate](#dhondt2025multivariate) |
| C04 | Global shifts and local warps capture different forms of temporal mismatch. | Contrast | [paparrizos2015kshape](#paparrizos2015kshape), [zhao2018shapedtw](#zhao2018shapedtw), [sakoe1978dtw](#sakoe1978dtw) |
| C05 | Raw soft-DTW, corrected divergence, kernel and metric are distinct objects. | Boundary | [cuturi2011gak](#cuturi2011gak), [cuturi2017softdtw](#cuturi2017softdtw), [blondel2021divergences](#blondel2021divergences) |
| C06 | A fixed-window subsequence join needs a window and a self-match policy. | Definition | [yeh2016matrixprofile](#yeh2016matrixprofile) |
| C07 | Exact retrieval indexing preserves a chosen target distance; it does not establish semantic relevance. | Boundary | [schaefer2012sfa](#schaefer2012sfa), [schaefer2025sofa](#schaefer2025sofa) |
| C08 | Learned and pretrained representations require a separate test of the intended similarity task. | Boundary | [yue2022ts2vec](#yue2022ts2vec), [dong2023simmtm](#dong2023simmtm), [goswami2024moment](#goswami2024moment) |
| C09 | Retrieval-assisted forecast performance does not isolate retrieval quality. | Boundary | [ning2025tsrag](#ning2025tsrag) |
| C10 | Runtime comparisons must specify implementation, workload and hardware. | Boundary | [wu2022fastdtw](#wu2022fastdtw), [azzari2026tsdistances](#azzari2026tsdistances) |
| C11 | Method rankings and normalization findings are conditional on evaluation design. | Boundary | [ding2008comparison](#ding2008comparison), [dhondt2025multivariate](#dhondt2025multivariate) |
| C12 | Histogram construction and square-root choice matter for Jensen-Shannon comparison. | Boundary | [bandt2002permutation](#bandt2002permutation), [lin1991js](#lin1991js), [endres2003jsmetric](#endres2003jsmetric) |

## Source records

Read the verification level beside each record. Definitions are concise paraphrases; quantitative rankings are intentionally left with the original experimental protocols.

### sakoe1978dtw

**[Dynamic programming algorithm optimization for spoken word recognition](https://ieeexplore.ieee.org/abstract/document/1163055/authors)** — Hiroaki Sakoe, Seibi Chiba. IEEE Transactions on Acoustics, Speech, and Signal Processing (1978).

- **Role and family:** Definition; elastic alignment.
- **Supported claim:** Dynamic programming aligns sequences under temporal consistency and path constraints; the alignment restrictions are part of the method specification.
- **Boundary:** A DTW score depends on local cost, step pattern, endpoint policy and path restrictions. The paper does not establish that every implementation or unconstrained alignment is appropriate for every domain.
- **Verification:** Publisher metadata and abstract; original paper text. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1109/TASSP.1978.1163055](https://doi.org/10.1109/TASSP.1978.1163055).
- **Additional checked sources:** [source 2](https://jeffe.cs.illinois.edu/teaching/compgeom/refs/Sakoe-Chiba-DTW.pdf).

### vlachos2002lcss

**[Discovering Similar Multidimensional Trajectories](https://people.cs.aau.dk/~simas/teaching/trajectories/00994784.pdf)** — Michail Vlachos, Dimitrios Gunopulos, George Kollios. Proceedings of the 18th International Conference on Data Engineering (2002).

- **Role and family:** Definition; thresholded elastic matching.
- **Supported claim:** LCSS-based trajectory matching rewards temporally ordered matching portions while allowing unmatched observations.
- **Boundary:** The spatial matching threshold, temporal tolerance and score normalization determine which observations count as matches. Robustness to noise is conditional on these choices and the evaluated data.
- **Verification:** Original paper text and bibliographic record. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1109/ICDE.2002.994784](https://doi.org/10.1109/ICDE.2002.994784).
- **Additional checked sources:** [source 2](https://dblp.org/rec/conf/icde/VlachosGK02.html).

### chen2004erp

**[On The Marriage of Lp-norms and Edit Distance](https://www.vldb.org/conf/2004/RS21P2.PDF)** — Lei Chen, Raymond T. Ng. Proceedings of the 30th International Conference on Very Large Data Bases (2004).

- **Role and family:** Definition; edit-based elastic matching.
- **Supported claim:** ERP combines edit operations with numerical penalties and develops lower bounds and pruning strategies for time-series retrieval.
- **Boundary:** The gap reference value and local norm must be specified. Metric statements must respect the paper's domain and gap convention; arbitrary normalization, squared costs or additional constraints need separate checks.
- **Verification:** Official VLDB paper; author institution metadata. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1016/B978-012088469-8.50070-X](https://doi.org/10.1016/B978-012088469-8.50070-X).
- **Additional checked sources:** [source 2](https://researchportal.hkust.edu.hk/en/publications/on-the-marriage-of-lp-norms-and-edit-distance/).

### chen2005edr

**[Robust and Fast Similarity Search for Moving Object Trajectories](https://cse.hkust.edu.hk/~leichen/pub/05/sigmod05.pdf)** — Lei Chen, M. Tamer Özsu, Vincent Oria. Proceedings of the ACM SIGMOD International Conference on Management of Data (2005).

- **Role and family:** Definition; thresholded edit distance.
- **Supported claim:** EDR applies edit operations to real-valued sequences using a tolerance-based match decision and develops pruning methods for trajectory retrieval.
- **Boundary:** Tolerance depends on units and preprocessing. The original trajectory experiments do not imply that EDR is universally best for arbitrary time-series retrieval or clustering.
- **Verification:** Author-hosted original paper; author institution metadata. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1145/1066157.1066213](https://doi.org/10.1145/1066157.1066213).
- **Additional checked sources:** [source 2](https://digitalcommons.njit.edu/fac_pubs/19908/).

### marteau2009twed

**[Time warp edit distance with stiffness adjustment for time series matching](https://arxiv.org/abs/cs/0703033)** — Pierre-François Marteau. IEEE Transactions on Pattern Analysis and Machine Intelligence (2009).

- **Role and family:** Definition; timestamp-aware elastic matching.
- **Supported claim:** TWED uses value differences, timestamp differences and edit penalties to control temporal elasticity. The paper defines strictly increasing sample timestamps and distinguishes positive temporal stiffness from its zero boundary.
- **Boundary:** The metric statement on value-time sequences requires positive stiffness and the stated cost assumptions. Timestamp units, a shared origin/sentinel and boundary initialization must be documented; a zero-stiffness variant does not retain the same guarantee.
- **Verification:** Author preprint full-text sections III.A, IV.C-D and Figure 2; journal metadata. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1109/TPAMI.2008.76](https://doi.org/10.1109/TPAMI.2008.76).
- **Additional checked sources:** [source 2](https://arxiv.org/pdf/cs/0703033); [source 3](https://pubmed.ncbi.nlm.nih.gov/19110495/).
- **Version/access note:** The arXiv record identifies the 2009 journal version. Figure 2 uses zero-valued, zero-time sentinels; the mathematical definition uses time distances.

### stefan2013msm

**[The Move-Split-Merge Metric for Time Series](https://ranger.uta.edu/~alex/publications/stefan_tkde2012_preprint.pdf)** — Alexandra Stefan, Vassilis Athitsos, Gautam Das. IEEE Transactions on Knowledge and Data Engineering (2013).

- **Role and family:** Definition; edit-based elastic matching.
- **Supported claim:** MSM minimizes the cost of move, split and merge operations and supplies a quadratic-time dynamic program for the original formulation.
- **Boundary:** The split/merge cost is a modeling parameter. Metric guarantees belong to the specified cost scheme and parameter domain; they do not transfer automatically to multivariate extensions or transformed similarities.
- **Verification:** Author-hosted original preprint; final journal metadata corroborated. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1109/TKDE.2012.88](https://doi.org/10.1109/TKDE.2012.88).
- **Additional checked sources:** [source 2](https://www.scienceopen.com/document?vid=849b99f5-8fd5-4d95-ad30-245090ec583f).
- **Version/access note:** The DOI and preprint carry 2012; the journal issue is June 2013. Publisher full text was not accessible in this check.

### paparrizos2015kshape

**[k-Shape: Efficient and Accurate Clustering of Time Series](https://www.cs.columbia.edu/~gravano/Papers/2015/sigmod2015.pdf)** — John Paparrizos, Luis Gravano. Proceedings of the ACM SIGMOD International Conference on Management of Data (2015).

- **Role and family:** Definition; shift-aware shape comparison.
- **Supported claim:** k-Shape combines a normalized cross-correlation-based shape dissimilarity with a centroid update designed for that comparison.
- **Boundary:** Global shifts and local time warps express different assumptions. Normalization, overlap and padding conventions matter; implementing SBD alone does not implement the complete k-Shape clustering procedure.
- **Verification:** Author-hosted original conference paper. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1145/2723372.2737793](https://doi.org/10.1145/2723372.2737793).

### zhao2018shapedtw

**[shapeDTW: Shape Dynamic Time Warping](https://www.sciencedirect.com/science/article/pii/S0031320317303710)** — Jiaping Zhao, Laurent Itti. Pattern Recognition (2018).

- **Role and family:** Definition; local-descriptor elastic matching.
- **Supported claim:** shapeDTW first describes local neighborhoods around timestamps, then aligns the resulting descriptor sequences with DTW.
- **Boundary:** Descriptor design and neighborhood width determine the compared structure. Reported audio-alignment and classification results do not validate a different implementation or establish universal downstream superiority.
- **Verification:** Publisher metadata, abstract and method description. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1016/j.patcog.2017.09.020](https://doi.org/10.1016/j.patcog.2017.09.020).
- **Version/access note:** Online publication was in 2017; the cited journal issue is February 2018.

### cuturi2011gak

**[Fast Global Alignment Kernels](https://icml.cc/2011/papers/489_icmlpaper.pdf)** — Marco Cuturi. Proceedings of the 28th International Conference on Machine Learning (2011).

- **Role and family:** Definition; alignment kernels.
- **Supported claim:** Global alignment kernels aggregate contributions across alignments and study sufficient conditions for positive definiteness, with faster triangular variants.
- **Boundary:** A kernel is not automatically a distance. Exponentiating an arbitrary DTW score does not inherit positive-definiteness guarantees from this paper.
- **Verification:** Official conference paper text. Checked 2026-10-29.
- **Publication status:** Published.
- **Additional checked sources:** [source 2](https://researchportal.ip-paris.fr/en/publications/fast-global-alignment-kernels/).

### cuturi2017softdtw

**[Soft-DTW: a Differentiable Loss Function for Time-Series](https://proceedings.mlr.press/v70/cuturi17a.html)** — Marco Cuturi, Mathieu Blondel. Proceedings of the 34th International Conference on Machine Learning (2017).

- **Role and family:** Definition; differentiable alignment loss.
- **Supported claim:** Soft-DTW replaces the hard minimum over alignment costs with a smooth minimum and permits gradient-based optimization of time-series outputs.
- **Boundary:** The smoothing parameter changes the objective. Raw soft-DTW values are not a zero-diagonal metric, and the method should not be described as merely a faster exact DTW implementation.
- **Verification:** Official PMLR publication and original paper. Checked 2026-10-29.
- **Publication status:** Published.
- **Additional checked sources:** [source 2](https://proceedings.mlr.press/v70/cuturi17a/cuturi17a.pdf).

### blondel2021divergences

**[Differentiable Divergences Between Time Series](https://proceedings.mlr.press/v130/blondel21a.html)** — Mathieu Blondel, Arthur Mensch, Jean-Philippe Vert. Proceedings of the 24th International Conference on Artificial Intelligence and Statistics (2021).

- **Role and family:** Boundary; corrected differentiable divergence.
- **Supported claim:** The paper identifies the entropic bias of raw soft-DTW and constructs corrected divergences, with non-negativity and equality properties under stated ground-cost conditions.
- **Boundary:** Non-negativity is conditional on the ground cost. A valid divergence need not obey the triangle inequality; the result does not turn every soft-DTW variant into a metric.
- **Verification:** Official PMLR publication; author research page. Checked 2026-10-29.
- **Publication status:** Published.
- **Additional checked sources:** [source 2](https://research.google/pubs/differentiable-divergences-between-time-series/).

### leguen2019dilate

**[Shape and Time Distortion Loss for Training Deep Time Series Forecasting Models](https://papers.nips.cc/paper_files/paper/2019/hash/466accbac9a66b805ba50e42ad715740-Abstract.html)** — Vincent Le Guen, Nicolas Thome. Advances in Neural Information Processing Systems (2019).

- **Role and family:** Definition; shape-and-timing forecasting loss.
- **Supported claim:** DILATE separates shape discrepancy and temporal distortion within a differentiable objective for multi-step forecasting.
- **Boundary:** This is a training-objective paper. Its forecasting experiments do not establish a general-purpose retrieval ranking, calibrated similarity probability or causal relation between signals.
- **Verification:** Official NeurIPS publication and abstract. Checked 2026-10-29.
- **Publication status:** Published.

### yeh2016matrixprofile

**[Matrix Profile I: All Pairs Similarity Joins for Time Series: A Unifying View That Includes Motifs, Discords and Shapelets](https://ieeexplore.ieee.org/document/7837992/)** — Chin-Chia Michael Yeh, Yan Zhu, Liudmila Ulanova, Nurjahan Begum, Yifei Ding, Hoang Anh Dau, Diego Furtado Silva, Abdullah Mueen, Eamonn Keogh. 2016 IEEE 16th International Conference on Data Mining (2016).

- **Role and family:** Definition; subsequence similarity joins.
- **Supported claim:** A matrix profile records a nearest-neighbor distance for each fixed-length subsequence; the original method builds on z-normalized Euclidean subsequence comparison.
- **Boundary:** A profile is an output of a similarity join, not a single whole-series distance. Window length, self-match exclusion, constants and missing values need explicit policies.
- **Verification:** Publisher abstract and original paper text. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1109/ICDM.2016.0179](https://doi.org/10.1109/ICDM.2016.0179).
- **Additional checked sources:** [source 2](https://www.cs.uoi.gr/~pvassil/supervision/diplomatikes/extraMaterial/Timeseries/2016_matrix_profile.pdf).

### schaefer2012sfa

**[SFA: A Symbolic Fourier Approximation and Index for Similarity Search in High Dimensional Datasets](https://doi.org/10.1145/2247596.2247656)** — Patrick Schäfer, Mikael Högqvist. Proceedings of the 15th International Conference on Extending Database Technology (2012).

- **Role and family:** Definition; lower-bound representation and indexing.
- **Supported claim:** SFA quantizes Fourier-based representations and combines them with a trie for exact similarity-search candidate filtering and refinement.
- **Boundary:** A lower-bound representation accelerates search for a specified target distance. Its symbolic comparison should not be assumed to preserve every semantic relation or arbitrary distance.
- **Verification:** Publisher abstract and author-hosted original paper. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1145/2247596.2247656](https://doi.org/10.1145/2247596.2247656).
- **Additional checked sources:** [source 2](https://www2.informatik.hu-berlin.de/~schaefpa/sfa_trie.pdf).

### batista2011cid

**[A Complexity-Invariant Distance Measure for Time Series](https://epubs.siam.org/doi/10.1137/1.9781611972818.60)** — Gustavo E. A. P. A. Batista, Xiaoyue Wang, Eamonn J. Keogh. Proceedings of the 2011 SIAM International Conference on Data Mining (2011).

- **Role and family:** Definition; complexity-adjusted distance.
- **Supported claim:** CID adjusts a base distance using a relative series-complexity factor, motivated by the effect of differing complexities on nearest-neighbor classification.
- **Boundary:** The complexity estimator and its zero-complexity convention matter. The name does not imply exact invariance to every operation that changes complexity.
- **Verification:** Official SIAM publication and abstract; software definition corroborates the formula. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1137/1.9781611972818.60](https://doi.org/10.1137/1.9781611972818.60).
- **Additional checked sources:** [source 2](https://search.r-project.org/CRAN/refmans/TSclust/html/diss.CID.html).

### shokoohi2017multidtw

**[Generalizing DTW to the multi-dimensional case requires an adaptive approach](https://pmc.ncbi.nlm.nih.gov/articles/PMC5668684/)** — Mohammad Shokoohi-Yekta, Bing Hu, Hongxia Jin, Jun Wang, Eamonn Keogh. Data Mining and Knowledge Discovery (2017).

- **Role and family:** Boundary; multivariate channel coupling.
- **Supported claim:** Dependent multivariate DTW shares an alignment across channels, whereas independent DTW allows different channel alignments; the paper demonstrates that the choices can yield different classifications.
- **Boundary:** The two constructions express different synchronization assumptions. Neither should be called a universally correct multivariate generalization.
- **Verification:** Author manuscript text and journal metadata. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1007/s10618-016-0455-0](https://doi.org/10.1007/s10618-016-0455-0).
- **Additional checked sources:** [source 2](https://pubmed.ncbi.nlm.nih.gov/29104448/).
- **Version/access note:** Online publication was in 2016; journal volume year is 2017. PMC text was searchable but a direct open later returned an access check.

### ding2008comparison

**[Querying and Mining of Time Series Data: Experimental Comparison of Representations and Distance Measures](https://users.eecs.northwestern.edu/~peters/references/vldb08.pdf)** — Hui Ding, Goce Trajcevski, Peter Scheuermann, Xiaoyue Wang, Eamonn Keogh. Proceedings of the VLDB Endowment (2008).

- **Role and family:** Contrast; comparative evaluation.
- **Supported claim:** This study compares representation and distance choices across multiple datasets rather than relying solely on the evaluations accompanying individual methods.
- **Boundary:** It is historical empirical evidence under the study's datasets and protocols. Its rankings cannot establish the best method for a current task or new data distribution.
- **Verification:** Author-hosted original paper and publication metadata. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.14778/1454159.1454226](https://doi.org/10.14778/1454159.1454226).
- **Additional checked sources:** [source 2](https://cir.nii.ac.jp/crid/1360292621315687168).

### wu2022fastdtw

**[FastDTW is Approximate and Generally Slower Than the Algorithm it Approximates](https://wu.renjie.im/research/fastdtw-is-slow/)** — Renjie Wu, Eamonn J. Keogh. IEEE Transactions on Knowledge and Data Engineering (2022).

- **Role and family:** Boundary; implementation and runtime comparison.
- **Supported claim:** The study shows that an approximate algorithm's name or asymptotic description is insufficient evidence of a runtime advantage over carefully implemented exact constrained DTW.
- **Boundary:** Its conclusions depend on implementations, lengths, windows and approximation radii. It does not justify claiming that every exact DTW implementation always beats every approximate implementation.
- **Verification:** Author project page with final journal citation and experiment descriptions. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1109/TKDE.2020.3033752](https://doi.org/10.1109/TKDE.2020.3033752).
- **Version/access note:** Accepted/online in 2020; final journal citation is 2022. The ICDE 2021 extended abstract is not counted as a second study.

### yue2022ts2vec

**[TS2Vec: Towards Universal Representation of Time Series](https://ojs.aaai.org/index.php/AAAI/article/view/20881)** — Zhihan Yue, Yujing Wang, Juanyong Duan, Tianmeng Yang, Congrui Huang, Yunhai Tong, Bixiong Xu. Proceedings of the AAAI Conference on Artificial Intelligence (2022).

- **Role and family:** Tool; learned representation.
- **Supported claim:** TS2Vec learns timestamp-level representations through hierarchical contrastive training and aggregates them to represent subsequences.
- **Boundary:** Classification, forecasting and anomaly-detection evidence supports representation utility. An embedding distance still requires a target-specific retrieval or clustering evaluation, including pooling and normalization choices.
- **Verification:** Official AAAI publication and abstract. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1609/aaai.v36i8.20881](https://doi.org/10.1609/aaai.v36i8.20881).

### herrmann2023adtw

**[Amercing: An intuitive and effective constraint for dynamic time warping](https://www.sciencedirect.com/science/article/pii/S0031320323000341)** — Matthieu Herrmann, Geoffrey I. Webb. Pattern Recognition (2023).

- **Role and family:** Definition; regularized elastic alignment.
- **Supported claim:** Amerced DTW adds a fixed cost to non-diagonal warping steps, providing a tunable alternative to a hard warping window or multiplicative weighting.
- **Boundary:** The additive penalty changes which alignments are preferred and needs an explicit tuning protocol. The paper's classification evidence does not prove universal retrieval superiority.
- **Verification:** Publisher metadata and abstract; author preprint cross-check. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1016/j.patcog.2023.109333](https://doi.org/10.1016/j.patcog.2023.109333).
- **Additional checked sources:** [source 2](https://arxiv.org/abs/2111.13314).
- **Version/access note:** Cite the 2023 formal article rather than counting the 2021 preprint as another method.

### dong2023simmtm

**[SimMTM: A Simple Pre-Training Framework for Masked Time-Series Modeling](https://papers.neurips.cc/paper_files/paper/2023/hash/5f9bfdfe3685e4ccdbc0e7fb29cccf2a-Abstract-Conference.html)** — Jiaxiang Dong, Haixu Wu, Haoran Zhang, Li Zhang, Jianmin Wang, Mingsheng Long. Advances in Neural Information Processing Systems (2023).

- **Role and family:** Tool; similarity-assisted representation learning.
- **Supported claim:** SimMTM uses learned series-level similarities to aggregate representations from masked examples for reconstruction during pretraining.
- **Boundary:** Similarity is part of the learning mechanism. Forecasting and classification evaluations do not by themselves validate a standalone semantic retrieval metric.
- **Verification:** Official NeurIPS publication; official code description. Checked 2026-10-29.
- **Publication status:** Published.
- **Additional checked sources:** [source 2](https://github.com/thuml/SimMTM).

### goswami2024moment

**[MOMENT: A Family of Open Time-series Foundation Models](https://proceedings.mlr.press/v235/goswami24a.html)** — Mononito Goswami, Konrad Szafer, Arjun Choudhry, Yifu Cai, Shuo Li, Artur Dubrawski. Proceedings of the 41st International Conference on Machine Learning (2024).

- **Role and family:** Tool; pretrained representation.
- **Supported claim:** MOMENT provides pretrained time-series models and evaluates them across several tasks and limited-supervision settings.
- **Boundary:** The existence of pretrained embeddings does not establish a universal notion of similarity. Retrieval use needs relevant-query labels or another explicit target, training-data overlap checks, pooling, scaling and checkpoint specification.
- **Verification:** Official PMLR publication; official project and implementation documentation. Checked 2026-10-29.
- **Publication status:** Published.
- **Additional checked sources:** [source 2](https://github.com/moment-timeseries-foundation-model/moment).

### paparrizos2024survey

**[A Survey on Time-Series Distance Measures](https://arxiv.org/abs/2412.20574)** — John Paparrizos, Haojun Li, Fan Yang, Kaize Wu, Jens E. d'Hondt, Odysseas Papapetrou. arXiv (2024).

- **Role and family:** Definition; taxonomy and literature discovery.
- **Supported claim:** The survey organizes distance measures into lock-step, sliding, elastic, kernel, feature, model and embedding families, covering both univariate and multivariate formulations.
- **Boundary:** This is a survey, not a new head-to-head experiment. Original method papers remain the sources for individual definitions and guarantees; the family taxonomy is not a claim that all methods are implemented in EchoTime.
- **Verification:** Author-uploaded arXiv record; author publication page. Checked 2026-10-29.
- **Publication status:** Preprint survey.
- **Additional checked sources:** [source 2](https://jensdhondt.com/publication/book_chapter_2024).
- **Version/access note:** The verified record is arXiv:2412.20574v1 (2024). A formally published successor was not established in this check.

### dhondt2025multivariate

**[A Structured Study of Multivariate Time-Series Distance Measures](https://doi.org/10.1145/3725258)** — Jens E. d'Hondt, Haojun Li, Fan Yang, Odysseas Papapetrou, John Paparrizos. Proceedings of the ACM on Management of Data (2025).

- **Role and family:** Contrast; multivariate comparative evaluation.
- **Supported claim:** The study jointly examines 30 distance measures, 13 normalizations, two channel-dependency models, 30 datasets and three downstream tasks, including supervised and unsupervised parameter selection.
- **Boundary:** Reported rankings and normalization effects are conditional on the study design. This supports testing preprocessing and channel assumptions, not claiming one distance or normalization is universally optimal.
- **Verification:** Publisher metadata and abstract; author institution record. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1145/3725258](https://doi.org/10.1145/3725258).
- **Additional checked sources:** [source 2](https://research.tue.nl/en/publications/a-structured-study-of-multivariate-time-series-distance-measures/); [source 3](https://jensdhondt.com/publication/sigmod_2025).

### schaefer2025sofa

**[Fast and Exact Similarity Search in Less than a Blink of an Eye](https://helios2.mi.parisdescartes.fr/~themisp/publications/icde25-sofa.pdf)** — Patrick Schäfer, Jakob Brand, Ulf Leser, Botao Peng, Themis Palpanas. Proceedings of the 41st IEEE International Conference on Data Engineering (2025).

- **Role and family:** Tool; exact Euclidean retrieval indexing.
- **Supported claim:** SOFA combines SFA-based summaries with a tree index and lower-bound filtering for exact Euclidean nearest-neighbor search.
- **Boundary:** The target is exact Euclidean retrieval; speed comparisons do not establish superior semantic similarity or transfer automatically to DTW. Index construction, memory, data and implementation must be included in a local comparison.
- **Verification:** Author-hosted original paper and official ICDE 2025 accepted-paper list; preprint cross-check. Checked 2026-10-29.
- **Publication status:** Published.
- **Additional checked sources:** [source 2](https://ieee-icde.org/2025/research-papers/); [source 3](https://arxiv.org/abs/2411.17483).
- **Version/access note:** The 2024 preprint and 2025 conference article are one work. DOI omitted because the publisher endpoint did not resolve in this check.

### ning2025tsrag

**[TS-RAG: Retrieval-Augmented Generation based Time Series Foundation Models are Stronger Zero-Shot Forecaster](https://proceedings.nips.cc/paper_files/paper/2025/hash/eed25c037bc08afcbefab6f7a6b700e0-Abstract-Conference.html)** — Kanghui Ning, Zijie Pan, Yu Liu, Yushan Jiang, James Zhang, Kashif Rasul, Anderson Schneider, Lintao Ma, Yuriy Nevmyvaka, Dongjin Song. Advances in Neural Information Processing Systems (2025).

- **Role and family:** Boundary; retrieval-augmented forecasting.
- **Supported claim:** TS-RAG retrieves segments through pretrained encoders and integrates retrieved patterns with a forecasting model using an adaptive mixer.
- **Boundary:** The reported downstream objective is forecasting. Forecast improvement alone does not establish general semantic nearest-neighbor accuracy, reliable causal analogues or superiority of the retrieval distance itself.
- **Verification:** Official NeurIPS publication and abstract. Checked 2026-10-29.
- **Publication status:** Published.

### azzari2026tsdistances

**[Algorithm 1061: tsdistances: A High-Performance Python Library for Time Series Distances with GPU Support](https://www.di.univr.it/?ent=pubbdip&id=1192651&lang=en)** — Alberto Azzari, Andrea Cracco, Francesco Masillo, Pietro Sala. ACM Transactions on Mathematical Software (2026).

- **Role and family:** Tool; CPU and GPU distance software.
- **Supported claim:** The software paper describes CPU and GPU implementations of time-series distances, with particular attention to elastic algorithms and parallel computation.
- **Boundary:** The publication establishes a relevant implementation source. This literature check did not run its benchmarks or verify interoperability; reported speedups must not be presented as EchoTime measurements.
- **Verification:** Author university publication record and abstract; independent bibliographic corroboration. Publisher full text unavailable. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1145/3802579](https://doi.org/10.1145/3802579).
- **Additional checked sources:** [source 2](https://dblp.org/pid/351/1189.html).
- **Version/access note:** ACM returned HTTP 403 during the check. The university record verifies year, authors, journal, volume, issue and DOI; this is not a full-text implementation audit.

### bandt2002permutation

**[Permutation Entropy: A Natural Complexity Measure for Time Series](https://doi.org/10.1103/PhysRevLett.88.174102)** — Christoph Bandt, Bernd Pompe. Physical Review Letters (2002).

- **Role and family:** Definition; ordinal-pattern representation.
- **Supported claim:** Permutation entropy uses the order patterns of neighboring observations to characterize temporal complexity.
- **Boundary:** An ordinal-pattern histogram is a representation, and a distance between such histograms is an additional design choice. Embedding dimension, delay and tie handling affect the representation; the original paper does not validate every histogram distance.
- **Verification:** Official publisher metadata and abstract. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1103/PhysRevLett.88.174102](https://doi.org/10.1103/PhysRevLett.88.174102).

### lin1991js

**[Divergence Measures Based on the Shannon Entropy](https://ieeexplore.ieee.org/abstract/document/61115/authors)** — Jianhua Lin. IEEE Transactions on Information Theory (1991).

- **Role and family:** Definition; probability-distribution divergence.
- **Supported claim:** Jensen-Shannon divergence compares probability distributions through entropy-based mixture differences and remains finite without the support restrictions of directed KL divergence.
- **Boundary:** The logarithm base sets the scale. Probability normalization is required; applying the divergence to a spectrum or ordinal histogram compares those summaries, which can discard time-domain information.
- **Verification:** Publisher metadata and abstract; original paper text. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1109/18.61115](https://doi.org/10.1109/18.61115).
- **Additional checked sources:** [source 2](https://www.cise.ufl.edu/~anand/sp06/jensen-shannon.pdf).

### endres2003jsmetric

**[A New Metric for Probability Distributions](https://research-repository.st-andrews.ac.uk/handle/10023/1591)** — Dominik M. Endres, Johannes E. Schindelin. IEEE Transactions on Information Theory (2003).

- **Role and family:** Boundary; probability-distribution metric.
- **Supported claim:** The paper establishes a metric proportional to the square root of equal-weight Jensen-Shannon divergence.
- **Boundary:** The square-root transformation is essential to this metric statement. A metric on probability summaries need not distinguish the underlying raw series when different series produce the same summary.
- **Verification:** Author institution repository metadata and original paper. Checked 2026-10-29.
- **Publication status:** Published.
- **DOI:** [10.1109/TIT.2003.813506](https://doi.org/10.1109/TIT.2003.813506).
- **Additional checked sources:** [source 2](https://research-repository.st-andrews.ac.uk/bitstream/10023/1591/1/Endres2003-IEEETransInfTheory49-NewMetric.pdf).

## Search scope and limitations

**Review type:** targeted narrative evidence collection, not an exhaustive systematic review.

The search started from method families already present in EchoTime, then checked recent work on elastic alignment, exact retrieval, learned representations, multivariate comparisons and distance software. Sources were prioritized in this order: original publisher/conference papers; author-hosted manuscripts; author-institution records. Bibliographic indexes were used only to corroborate metadata or locate original sources.

**Representative searches used on 2026-10-29:**

- `time series similarity distance survey dynamic time warping 2024 2025 benchmark`
- `time series foundation models similarity retrieval 2025 2026`
- `The Move-Split-Merge Metric for Time Series Stefan`
- `On The Marriage of Lp-norms and Edit Distance vldb.org`
- `Discovering similar multidimensional trajectories`
- `Robust and Fast Similarity Search for Moving Object Trajectories Chen Ozsu Oria 2005`
- `Soft-DTW: a Differentiable Loss Function for Time-Series`
- `Differentiable Divergences Between Time Series`
- `Matrix Profile I All Pairs Similarity Joins for Time Series`
- `A Structured Study of Multivariate Time-Series Distance Measures 2025 pdf`
- `Amercing: An Intuitive, Elegant and Effective Constraint for Dynamic Time Warping`
- `Fast and Exact Similarity Search in less than a Blink of an Eye`
- `SimMTM: A Simple Pre-Training Framework for Masked Time-Series Modeling`
- `MOMENT: A Family of Open Time-series Foundation Models`
- `tsdistances Azzari`
- `Time Warp Edit Distance t_0`
- `Divergence measures based on the Shannon entropy Lin 1991`

**Limitations:**

- This is a curated source set, not complete coverage of every method, paper or application.
- Per-record verification levels distinguish full-text checks, abstracts and metadata; not all proofs or experiments were re-audited.
- No cross-library benchmark, timing experiment or new model evaluation was performed for this literature collection.
- No exhaustive retraction/correction database audit was performed.
- Some publisher endpoints were blocked or unavailable; successful alternative sources and limits are recorded.
- Publication dates are taken from bibliographic records, not search-engine crawl or relative-time labels.

A method citation supports a definition or a documented experiment. It does not certify that a similarly named function is equivalent to the reference implementation. Implementation comparisons should record the local cost, preprocessing, boundary cases, dependency version and test evidence.

## Maintaining this collection

Add a reference only after checking a primary source. Record the precise supported claim, a boundary, the source URLs and the access date. Prefer a verified formal version over its preprint, and keep both URLs in one record when needed. Leave unavailable metadata out of BibTeX. Use the same stable key in the Markdown heading, JSON record and BibTeX entry. Do not insert unverified accuracy or speed claims into the method atlas.
