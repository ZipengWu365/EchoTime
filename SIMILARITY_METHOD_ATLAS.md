# EchoTime similarity method atlas

This guide audits EchoTime's current raw-series similarity stack, then imports the full method registry from `ts_similarity_package_v2_pkg` and marks which methods fit EchoTime's product direction.

## Literature anchors

The [verified reading map](docs/references/time-series-similarity-literature.md) links 30 research sources to definitions, comparisons, publication status, and evidence boundaries, including recent ADTW, multivariate-distance, retrieval-indexing, and representation-learning work. [BibTeX](docs/references/time-series-similarity-literature.bib) and [JSON](docs/references/time-series-similarity-literature.json) provide reusable records.

Use the [English selection guide](docs/articles/time-series-similarity-guide.en.md) or [中文选型指南](docs/articles/time-series-similarity-guide.zh-CN.md) to connect method families to whole-series, subsequence, dataset, and learning tasks.

The [animated method explanations](docs/method-animations/README.md) cover all 10 native entries and 127 registry entries with individual GIFs, static images, four calculation stages, example inputs, sources and limitations in English and Chinese. [Open the same explanations in the existing web atlas](https://zipengwu.me/EchoTime/guide/methods.html#method-animations). Teaching examples distinguish checked EchoTime implementations, explicit reference formulas and specified illustrative protocols.

The full registry is an inventory, not a claim that all methods have been implemented or independently reproduced here. The `implementation` column describes the imported reference registry; `EchoTime fit` and `EchoTime API` identify local coverage. `Conceptually covered` denotes a related component, which can use a different cost or transformation. Metric properties require the stated domain and parameter assumptions; feature-space metrics can be pseudometrics on the original series.

## Current EchoTime comparison layer

### shape_similarity

- family: EchoTime native component
- kind: similarity
- formula: `s_shape = GM(clip(r(x,y), 0, 1), clip(r(Delta x, Delta y), 0, 1))`
- note: Combines level correlation with first-difference correlation so the headline match does not ignore local dynamics.
- animation and explanation: [shape_similarity](docs/method-animations/native.md#shape_similarity)

### dtw_similarity

- family: EchoTime native component
- kind: similarity
- formula: `s_dtw = GM(exp(-aDTW_w(x,y)/0.45), exp(-aDTW_w(z(Delta x), z(Delta y))/0.35)); aDTW = min_path sum |x_i-y_j| / (n+m)`
- note: A package-specific blend on resampled, z-normalized series and re-normalized first differences. Uses absolute local costs and divides accumulated cost by n+m; it is not the common square-root-of-squared-cost DTW distance or a calibrated probability.
- animation and explanation: [dtw_similarity](docs/method-animations/native.md#dtw_similarity)

### trend_similarity

- family: EchoTime native component
- kind: similarity
- formula: `s_trend = GM(clip(r(T(x), T(y)), 0, 1), clip(r(Delta T(x), Delta T(y)), 0, 1))`
- note: Smooths both series first, then compares both the trend level and the trend slope.
- animation and explanation: [trend_similarity](docs/method-animations/native.md#trend_similarity)

### derivative_similarity

- family: EchoTime native component
- kind: similarity
- formula: `s_diff = clip(r(Delta x, Delta y), 0, 1)`
- note: Focuses on whether local changes move together even when the levels differ.
- animation and explanation: [derivative_similarity](docs/method-animations/native.md#derivative_similarity)

### spectral_similarity

- family: EchoTime native component
- kind: similarity
- formula: `s_spec = GM(1 - JSD(P_x, P_y), clip(r(P_x - U, P_y - U), 0, 1))`
- note: Compares normalized spectra of differenced series, mixing JS overlap with structural similarity relative to a uniform spectrum U.
- animation and explanation: [spectral_similarity](docs/method-animations/native.md#spectral_similarity)

### pearson_r

- family: EchoTime reference metric
- kind: similarity
- formula: `r(x,y) = sum_t (x_t - x_bar)(y_t - y_bar) / sqrt(sum_t (x_t - x_bar)^2 sum_t (y_t - y_bar)^2)`
- note: Familiar linear correlation exposed directly in every raw-series similarity report.
- animation and explanation: [pearson_r](docs/method-animations/native.md#pearson_r)

### spearman_rho

- family: EchoTime reference metric
- kind: similarity
- formula: `rho(x,y) = corr(rank(x), rank(y))`
- note: Rank-order correlation used as a robustness check against nonlinear monotone relationships.
- animation and explanation: [spearman_rho](docs/method-animations/native.md#spearman_rho)

### kendall_tau

- family: EchoTime reference metric
- kind: similarity
- formula: `tau_b(x,y) = (C - D) / sqrt((C + D + T_x)(C + D + T_y))`
- note: Kendall tau-b uses tie corrections: T_x and T_y count pairs tied only in x or only in y. EchoTime retains a zero-score convention for constant inputs, where statistical correlation is undefined.
- animation and explanation: [kendall_tau](docs/method-animations/native.md#kendall_tau)

### best_lag_pearson_r

- family: EchoTime reference metric
- kind: similarity
- formula: `max_lag_r(x,y) = max_ell r(x_t, y_{t-ell})`
- note: Searches over a bounded lag window to show whether a shift-aware linear relationship is stronger than the aligned one.
- animation and explanation: [best_lag_pearson_r](docs/method-animations/native.md#best_lag_pearson_r)

### normalized_mutual_information

- family: EchoTime reference metric
- kind: similarity
- formula: `NMI(X,Y) = I(X;Y) / sqrt(H(X) H(Y))`
- note: Histogram-based nonlinear dependence score used as a familiar cross-check against linear metrics.
- animation and explanation: [normalized_mutual_information](docs/method-animations/native.md#normalized_mutual_information)

## Implemented and high-fit additions from ts_similarity_package_v2_pkg

| method | family | EchoTime fit | EchoTime API | formula | why it matters |
|---|---|---|---|---|---|
| [independent_max_ncc](docs/method-animations/sliding.md#independent_max_ncc) | sliding | Implemented in EchoTime | `independent_max_ncc` | `$s(X,Y)=\frac{1}{d}\sum_c \max_k NCC_k(X^{(c)},Y^{(c)})$` | This method is now available as a public low-level EchoTime similarity function. |
| [independent_sbd](docs/method-animations/sliding.md#independent_sbd) | sliding | Implemented in EchoTime | `independent_sbd` | `$d(X,Y)=\frac{1}{d}\sum_c SBD(X^{(c)},Y^{(c)})$` | This method is now available as a public low-level EchoTime similarity function. |
| [max_normalized_cross_correlation](docs/method-animations/sliding.md#max_normalized_cross_correlation) | sliding | Implemented in EchoTime | `max_ncc` | `$s(x,y)=\max_k NCC_k(x,y)$` | This method is now available as a public low-level EchoTime similarity function. |
| [sbd](docs/method-animations/sliding.md#sbd) | sliding | Implemented in EchoTime | `sbd` | `$d(x,y)=1-\max_k NCC_k(x,y)$` | This method is now available as a public low-level EchoTime similarity function. |
| [edr](docs/method-animations/elastic.md#edr) | elastic | Implemented in EchoTime | `edr_distance` | `$EDR_{\epsilon}(x,y)$` | This method is now available as a public low-level EchoTime similarity function. |
| [erp](docs/method-animations/elastic.md#erp) | elastic | Implemented in EchoTime | `erp_distance` | `$ERP(x,y;g)$` | This method is now available as a public low-level EchoTime similarity function. |
| [lcss_distance](docs/method-animations/elastic.md#lcss_distance) | elastic | Implemented in EchoTime | `lcss_distance` | `$d(x,y)=1-s_{LCSS}(x,y)$` | This method is now available as a public low-level EchoTime similarity function. |
| [lcss_similarity](docs/method-animations/elastic.md#lcss_similarity) | elastic | Implemented in EchoTime | `lcss_similarity` | `$s(x,y)=LCSS_{\epsilon}(x,y)/\min(n,m)$` | This method is now available as a public low-level EchoTime similarity function. |
| [twed](docs/method-animations/elastic.md#twed) | elastic | Implemented in EchoTime | `twed_distance` | `$TWED_{\lambda,\nu}(x,y)$` | This method is now available as a public low-level EchoTime similarity function. |
| [acf_distance](docs/method-animations/feature-based.md#acf_distance) | feature-based | Implemented in EchoTime | `acf_distance` | `$d(x,y)=\\|ACF(x)-ACF(y)\\|_2$` | This method is now available as a public low-level EchoTime similarity function. |
| [ordinal_pattern_js_distance](docs/method-animations/feature-based.md#ordinal_pattern_js_distance) | feature-based | Implemented in EchoTime | `ordinal_pattern_js_distance` | `$d(x,y)=\sqrt{JSD(\Pi(x),\Pi(y))}$` | This method is now available as a public low-level EchoTime similarity function. |
| [periodogram_distance](docs/method-animations/feature-based.md#periodogram_distance) | feature-based | Implemented in EchoTime | `periodogram_distance` | `$d(x,y)=\\|P_x-P_y\\|_2$` | This method is now available as a public low-level EchoTime similarity function. |
| [trend_distance](docs/method-animations/feature-based.md#trend_distance) | feature-based | Implemented in EchoTime | `trend_distance` | `$d(x,y)=\\|\phi_{\mathrm{trend}}(x)-\phi_{\mathrm{trend}}(y)\\|_2$` | This method is now available as a public low-level EchoTime similarity function. |
| [linear_trend_model_distance](docs/method-animations/model-based.md#linear_trend_model_distance) | model-based | Implemented in EchoTime | `linear_trend_model_distance` | `$d(x,y)=\\|\theta_{\mathrm{trend}}(x)-\theta_{\mathrm{trend}}(y)\\|_2$` | This method is now available as a public low-level EchoTime similarity function. |

## Full extracted atlas

### lock-step

Pointwise comparison on an already aligned timeline.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| [euclidean](docs/method-animations/lock-step.md#euclidean) | distance | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sqrt{\sum_t \\|x_t-y_t\\|_2^2}$` | Equal-length pointwise Euclidean distance. |
| [squared_euclidean](docs/method-animations/lock-step.md#squared_euclidean) | distance | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sum_t \\|x_t-y_t\\|_2^2$` | Squared Euclidean loss. |
| [rmse_distance](docs/method-animations/lock-step.md#rmse_distance) | distance | yes on a common fixed-dimensional domain | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sqrt{\frac{1}{nd}\sum_t \\|x_t-y_t\\|_2^2}$` | Root-mean-square error over aligned points: a positive constant times Euclidean distance when n and d are fixed. |
| [manhattan](docs/method-animations/lock-step.md#manhattan) | distance | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sum_t \\|x_t-y_t\\|_1$` | L1 distance. |
| [mae_distance](docs/method-animations/lock-step.md#mae_distance) | distance | yes on a common fixed-dimensional domain | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{1}{nd}\sum_t \\|x_t-y_t\\|_1$` | Mean absolute error: a positive constant times L1 distance when n and d are fixed. |
| [minkowski](docs/method-animations/lock-step.md#minkowski) | distance | yes (p≥1) | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d_p(x,y)=\left(\sum_t \\|x_t-y_t\\|_p^p\right)^{1/p}$` | Generalized Lp distance. |
| [chebyshev](docs/method-animations/lock-step.md#chebyshev) | distance | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\max_t \\|x_t-y_t\\|_{\infty}$` | Maximum deviation distance. |
| [canberra](docs/method-animations/lock-step.md#canberra) | distance | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sum_i \frac{\|x_i-y_i\|}{\|x_i\|+\|y_i\|}$` | Relative L1 distance sensitive near zero. |
| [bray_curtis](docs/method-animations/lock-step.md#bray_curtis) | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{\sum_i \|x_i-y_i\|}{\sum_i \|x_i+y_i\|}$` | Bray-Curtis dissimilarity. |
| [sorensen](docs/method-animations/lock-step.md#sorensen) | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{\sum_i \|x_i-y_i\|}{\sum_i (\|x_i\|+\|y_i\|)}$` | Sorensen dissimilarity. |
| [soergel](docs/method-animations/lock-step.md#soergel) | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{\sum_i \|x_i-y_i\|}{\sum_i \max(\|x_i\|,\|y_i\|)}$` | Relative distance normalized by max magnitudes. |
| [kulczynski](docs/method-animations/lock-step.md#kulczynski) | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{\sum_i \|x_i-y_i\|}{\sum_i \min(\|x_i\|,\|y_i\|)}$` | Kulczynski-style relative dissimilarity. |
| [clark](docs/method-animations/lock-step.md#clark) | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sqrt{\sum_i\left(\frac{\|x_i-y_i\|}{\|x_i\|+\|y_i\|}\right)^2}$` | Clark distance. |
| [wave_hedges](docs/method-animations/lock-step.md#wave_hedges) | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sum_i \frac{\|x_i-y_i\|}{\max(\|x_i\|,\|y_i\|)}$` | Wave-Hedges distance. |
| [lorentzian](docs/method-animations/lock-step.md#lorentzian) | distance-like | not guaranteed | O(n·d) | no | yes | reference | Low-priority addition | `-` | `$d(x,y)=\sum_i \log(1+\|x_i-y_i\|)$` | Log-compressed deviation. |
| [cosine_similarity](docs/method-animations/lock-step.md#cosine_similarity) | similarity | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$s(x,y)=\frac{\langle x,y\rangle}{\\|x\\|\\|y\\|}$` | Directional similarity. |
| [cosine_distance](docs/method-animations/lock-step.md#cosine_distance) | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=1-s_{\cos}(x,y)$` | Monotone transform of cosine similarity. |
| [angular_distance](docs/method-animations/lock-step.md#angular_distance) | distance | yes on normalized vectors | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\arccos(s_{\cos}(x,y))/\pi$` | Angle-based distance. |
| [pearson_similarity](docs/method-animations/lock-step.md#pearson_similarity) | similarity | no | O(n·d) | no | yes | exact | Conceptually covered | `pearson_r` | `$r(x,y)=\frac{\sum_i(x_i-\bar x)(y_i-\bar y)}{\sqrt{\sum_i(x_i-\bar x)^2}\sqrt{\sum_i(y_i-\bar y)^2}}$` | Linear correlation. |
| [pearson_distance](docs/method-animations/lock-step.md#pearson_distance) | distance-like | no | O(n·d) | no | yes | exact | Conceptually covered | `pearson_r` | `$d(x,y)=1-r(x,y)$` | Correlation distance. |
| [spearman_similarity](docs/method-animations/lock-step.md#spearman_similarity) | similarity | no | O(n \log n) | no | yes | reference | Conceptually covered | `spearman_rho` | `$s(x,y)=r(\mathrm{rank}(x),\mathrm{rank}(y))$` | Rank correlation similarity. |
| [spearman_distance](docs/method-animations/lock-step.md#spearman_distance) | distance-like | no | O(n \log n) | no | yes | reference | Conceptually covered | `spearman_rho` | `$d(x,y)=1-\rho(x,y)$` | Distance-like rank dissimilarity. |
| [kendall_similarity](docs/method-animations/lock-step.md#kendall_similarity) | similarity | no | O(n^2) | no | yes | reference | Conceptually covered | `kendall_tau` | `$s(x,y)=\tau_b(x,y)$` | Kendall tau-b rank agreement. |
| [kendall_distance](docs/method-animations/lock-step.md#kendall_distance) | distance-like | no | O(n^2) | no | yes | reference | Conceptually covered | `kendall_tau` | `$d(x,y)=1-\tau_b(x,y)$` | Distance-like form of Kendall agreement. |
| [jensen_shannon](docs/method-animations/lock-step.md#jensen_shannon) | distance | yes on probability distributions | O(n) | no | yes | exact | Conceptually covered | `spectral_similarity` | `$d(x,y)=\sqrt{\frac{1}{2}KL(x\\|m)+\frac{1}{2}KL(y\\|m)}$` | Square root of Jensen-Shannon divergence, defined on probability distributions over a common support. |
| [kl_divergence](docs/method-animations/lock-step.md#kl_divergence) | divergence | no | O(n) | no | yes | exact | Low-priority addition | `-` | `$D_{KL}(x\\|y)=\sum_i p_i\log\frac{p_i}{q_i}$` | Asymmetric divergence. |
| [jeffreys_divergence](docs/method-animations/lock-step.md#jeffreys_divergence) | divergence | no | O(n) | no | yes | exact | Low-priority addition | `-` | `$J(x,y)=KL(x\\|y)+KL(y\\|x)$` | Symmetrized KL divergence. |
| [bhattacharyya_distance](docs/method-animations/lock-step.md#bhattacharyya_distance) | distance-like | no | O(n) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=-\log\sum_i \sqrt{p_i q_i}$` | Distribution overlap distance. |
| [hellinger_distance](docs/method-animations/lock-step.md#hellinger_distance) | distance | yes | O(n) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sqrt{\frac{1}{2}\sum_i(\sqrt{p_i}-\sqrt{q_i})^2}$` | Probability-distribution distance. |
| [chi_square_distance](docs/method-animations/lock-step.md#chi_square_distance) | distance-like | no | O(n) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{1}{2}\sum_i\frac{(x_i-y_i)^2}{x_i+y_i}$` | Chi-square distance for histograms. |
| [seuclidean_distance](docs/method-animations/lock-step.md#seuclidean_distance) | distance | yes | O(n) | no | yes | reference | Low-priority addition | `-` | `$d(x,y)=\sqrt{\sum_i \frac{(x_i-y_i)^2}{v_i}}$` | Variance-standardized Euclidean distance. |
| [znorm_euclidean](docs/method-animations/lock-step.md#znorm_euclidean) | distance | yes in normalized space; pseudometric on original series | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\\|\hat x-\hat y\\|_2$` | Euclidean after per-channel z-normalization. Positive rescaling and offset can map distinct series to the same representation; constant channels need a declared convention. |
| [znorm_manhattan](docs/method-animations/lock-step.md#znorm_manhattan) | distance | yes in normalized space; pseudometric on original series | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\\|\hat x-\hat y\\|_1$` | L1 after per-channel z-normalization. Positive rescaling and offset can map distinct series to the same representation; constant channels need a declared convention. |
| [cid_distance](docs/method-animations/lock-step.md#cid_distance) | distance-like | no | O(n·d) | no | yes | reference | Low-priority addition | `-` | `$CID(x,y)=ED(x,y)\cdot \frac{\max(CE(x),CE(y))}{\min(CE(x),CE(y))}$` | Complexity-invariant distance. |

### sliding

Shift-aware comparison under pure translation or lead-lag offsets.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| [max_normalized_cross_correlation](docs/method-animations/sliding.md#max_normalized_cross_correlation) | similarity | no | O(n \log n) or O(n^2) | yes | yes | exact | Implemented in EchoTime | `max_ncc` | `$s(x,y)=\max_k NCC_k(x,y)$` | Maximum normalized cross-correlation over shifts. |
| [sbd](docs/method-animations/sliding.md#sbd) | distance-like | no | O(n \log n) or O(n^2) | yes | yes | exact | Implemented in EchoTime | `sbd` | `$d(x,y)=1-\max_k NCC_k(x,y)$` | Shape-based distance. |
| [shift_euclidean_distance](docs/method-animations/sliding.md#shift_euclidean_distance) | distance-like | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=\min_k \\|x_{\Omega_k}-y_{\Omega_k}\\|_2$` | Best-overlap Euclidean distance over integer shifts. |
| [shift_rmse_distance](docs/method-animations/sliding.md#shift_rmse_distance) | distance-like | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=\min_k \sqrt{\frac{1}{\|\Omega_k\|}\sum_{t\in\Omega_k}(x_t-y_{t-k})^2}$` | Best-overlap RMSE. |
| [shift_manhattan_distance](docs/method-animations/sliding.md#shift_manhattan_distance) | distance-like | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=\min_k \\|x_{\Omega_k}-y_{\Omega_k}\\|_1$` | Best-overlap L1 distance. |
| [shift_mae_distance](docs/method-animations/sliding.md#shift_mae_distance) | distance-like | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=\min_k \frac{1}{\|\Omega_k\|}\\|x_{\Omega_k}-y_{\Omega_k}\\|_1$` | Best-overlap MAE. |
| [shift_cosine_similarity](docs/method-animations/sliding.md#shift_cosine_similarity) | similarity | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$s(x,y)=\max_k s_{\cos}(x_{\Omega_k},y_{\Omega_k})$` | Best-overlap cosine similarity. |
| [shift_cosine_distance](docs/method-animations/sliding.md#shift_cosine_distance) | distance-like | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=1-\max_k s_{\cos}(x_{\Omega_k},y_{\Omega_k})$` | Distance-like shift-invariant cosine measure. |
| [shift_pearson_similarity](docs/method-animations/sliding.md#shift_pearson_similarity) | similarity | no | O(n^2·d) | yes | yes | reference | Conceptually covered | `best_lag_pearson_r` | `$s(x,y)=\max_k r(x_{\Omega_k},y_{\Omega_k})$` | Best-overlap Pearson correlation. |
| [shift_pearson_distance](docs/method-animations/sliding.md#shift_pearson_distance) | distance-like | no | O(n^2·d) | yes | yes | reference | Conceptually covered | `best_lag_pearson_r` | `$d(x,y)=1-\max_k r(x_{\Omega_k},y_{\Omega_k})$` | Distance-like shift-invariant correlation measure. |
| [independent_sbd](docs/method-animations/sliding.md#independent_sbd) | distance-like | no | O(dn\log n) | yes | multivariate only | exact | Implemented in EchoTime | `independent_sbd` | `$d(X,Y)=\frac{1}{d}\sum_c SBD(X^{(c)},Y^{(c)})$` | Channel-independent SBD. |
| [independent_max_ncc](docs/method-animations/sliding.md#independent_max_ncc) | similarity | no | O(dn\log n) | yes | multivariate only | exact | Implemented in EchoTime | `independent_max_ncc` | `$s(X,Y)=\frac{1}{d}\sum_c \max_k NCC_k(X^{(c)},Y^{(c)})$` | Channel-independent maximum NCC. |

### elastic

Dynamic-programming alignments that allow local stretching or compression.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| [dtw](docs/method-animations/elastic.md#dtw) | distance | no | O(nm) | yes | yes | exact | Conceptually covered | `dtw_similarity` | `$DTW(x,y)=\min_{\pi}\sqrt{\sum_{(i,j)\in\pi} \\|x_i-y_j\\|_2^2}$` | Dynamic Time Warping. |
| [cdtw](docs/method-animations/elastic.md#cdtw) | distance | no | O(nw) | yes | yes | exact | Conceptually covered | `dtw_similarity` | `$DTW_w(x,y)$ with Sakoe-Chiba window` | Constrained DTW. |
| [itakura_dtw](docs/method-animations/elastic.md#itakura_dtw) | distance | no | O(nm) | yes | yes | reference | Possible addition | `-` | `$DTW_{\mathrm{Itakura}}(x,y)$` | DTW under Itakura parallelogram constraint. |
| [wdtw](docs/method-animations/elastic.md#wdtw) | distance | no | O(nm) | yes | yes | exact | Possible addition | `-` | `$WDTW(x,y)=\min_{\pi}\sqrt{\sum_{(i,j)\in\pi} w_{\|i-j\|}\\|x_i-y_j\\|_2^2}$` | Weighted DTW. |
| [ddtw](docs/method-animations/elastic.md#ddtw) | distance | no | O(nm) | yes | yes | exact | Conceptually covered | `dtw_similarity` | `$DTW(\Delta x,\Delta y)$` | Derivative DTW. |
| [wddtw](docs/method-animations/elastic.md#wddtw) | distance | no | O(nm) | yes | yes | exact | Possible addition | `-` | `$WDTW(\Delta x,\Delta y)$` | Weighted derivative DTW. |
| [soft_dtw](docs/method-animations/elastic.md#soft_dtw) | distance-like | no | O(nm) | yes | yes | exact | Possible addition | `-` | `$sDTW_{\gamma}(x,y)$` | Soft minimum relaxation of DTW. |
| [soft_dtw_divergence](docs/method-animations/elastic.md#soft_dtw_divergence) | distance-like | no | O(nm) | yes | yes | exact | Possible addition | `-` | `$D^{\gamma}(x,y)=sDTW(x,y)-\frac{1}{2}sDTW(x,x)-\frac{1}{2}sDTW(y,y)$` | Soft-DTW divergence. |
| [lcss_similarity](docs/method-animations/elastic.md#lcss_similarity) | similarity | no | O(nm) | yes | yes | exact | Implemented in EchoTime | `lcss_similarity` | `$s(x,y)=LCSS_{\epsilon}(x,y)/\min(n,m)$` | Longest Common Subsequence similarity. |
| [lcss_distance](docs/method-animations/elastic.md#lcss_distance) | distance-like | no | O(nm) | yes | yes | exact | Implemented in EchoTime | `lcss_distance` | `$d(x,y)=1-s_{LCSS}(x,y)$` | Distance-like LCSS form. |
| [edr](docs/method-animations/elastic.md#edr) | distance | no | O(nm) | yes | yes | exact | Implemented in EchoTime | `edr_distance` | `$EDR_{\epsilon}(x,y)$` | Edit distance on real sequence. |
| [swale_similarity](docs/method-animations/elastic.md#swale_similarity) | similarity | no | O(nm) | yes | yes | reference | Possible addition | `-` | `$SWALE_{\epsilon}(x,y)$` | Similarity with reward and penalty. |
| [erp](docs/method-animations/elastic.md#erp) | distance | requires a gap-domain convention | O(nm) | yes | yes | exact | Implemented in EchoTime | `erp_distance` | `$ERP(x,y;g)$` | Edit distance with real penalty. If gap values are valid observations, distinct raw sequences can have zero distance: with g=0, [1] and [0,1] do. State the sequence equivalence/domain before claiming a metric. |
| [msm](docs/method-animations/elastic.md#msm) | distance | yes | O(nm) | yes | univariate only | exact | Possible addition | `-` | `$MSM(x,y)$` | Move-Split-Merge distance. |
| [twed](docs/method-animations/elastic.md#twed) | distance | under the original assumptions with nu > 0 | O(nm) | yes | yes | exact | Implemented in EchoTime | `twed_distance` | `$TWED_{\lambda,\nu}(x,y)$` | Time Warp Edit distance. The metric result requires positive stiffness and the original timestamp/cost/boundary conventions; fast resampling and window constraints do not inherit that guarantee. |
| [discrete_frechet](docs/method-animations/elastic.md#discrete_frechet) | distance | pseudometric on raw vertex sequences | O(nm) | yes | yes | reference | Possible addition | `-` | `$\delta_F(x,y)$` | Discrete Frechet distance can identify different vertex lists obtained by repeating vertices. A metric claim needs an appropriate equivalence/domain convention. |
| [needleman_wunsch_similarity](docs/method-animations/elastic.md#needleman_wunsch_similarity) | similarity | no | O(nm) | yes | yes | reference | Possible addition | `-` | `$NW(x,y)$` | Global alignment score. |
| [smith_waterman_similarity](docs/method-animations/elastic.md#smith_waterman_similarity) | similarity | no | O(nm) | yes | yes | reference | Possible addition | `-` | `$SW(x,y)$` | Local alignment score. |
| [shape_dtw](docs/method-animations/elastic.md#shape_dtw) | distance | no | O(nmr) | yes | yes | reference | Possible addition | `-` | `$DTW(\phi_{\mathrm{shape}}(x),\phi_{\mathrm{shape}}(y))$` | DTW on local shape descriptors. |
| [independent_dtw](docs/method-animations/elastic.md#independent_dtw) | distance | no | O(dnm) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c DTW(X^{(c)},Y^{(c)})$` | Channel-independent DTW average. |
| [independent_cdtw](docs/method-animations/elastic.md#independent_cdtw) | distance | no | O(dnw) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c cDTW(X^{(c)},Y^{(c)})$` | Channel-independent constrained DTW. |
| [independent_wdtw](docs/method-animations/elastic.md#independent_wdtw) | distance | no | O(dnm) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c WDTW(X^{(c)},Y^{(c)})$` | Channel-independent weighted DTW. |
| [independent_ddtw](docs/method-animations/elastic.md#independent_ddtw) | distance | no | O(dnm) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c DDTW(X^{(c)},Y^{(c)})$` | Channel-independent derivative DTW. |
| [independent_erp](docs/method-animations/elastic.md#independent_erp) | distance | requires a gap-domain convention | O(dnm) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c ERP(X^{(c)},Y^{(c)})$` | Channel-independent ERP average; inherits the gap-domain qualifications of ERP. |

### kernel

Similarity through kernel scores rather than direct distances.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| [linear_kernel](docs/method-animations/kernel.md#linear_kernel) | similarity | PSD if input space valid | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$K(x,y)=\langle x,y \rangle$` | Linear kernel on flattened vectors. |
| [polynomial_kernel](docs/method-animations/kernel.md#polynomial_kernel) | similarity | depends on parameters | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$K(x,y)=(\gamma \langle x,y \rangle + c)^p$` | Polynomial kernel. |
| [sigmoid_kernel](docs/method-animations/kernel.md#sigmoid_kernel) | similarity | not always PSD | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$K(x,y)=\tanh(\gamma \langle x,y \rangle + c)$` | Sigmoid kernel. |
| [rbf_kernel](docs/method-animations/kernel.md#rbf_kernel) | similarity | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$K(x,y)=\exp(-\gamma \\|x-y\\|_2^2)$` | Gaussian kernel over aligned vectors. |
| [dtw_rbf_kernel](docs/method-animations/kernel.md#dtw_rbf_kernel) | similarity | not guaranteed | O(nm) | yes | yes | reference | Low-priority addition | `-` | `$K(x,y)=\exp(-\gamma DTW(x,y)^2)$` | RBF on DTW distance. |
| [sbd_kernel](docs/method-animations/kernel.md#sbd_kernel) | similarity | not guaranteed | O(n \log n) or O(n^2) | yes | yes | reference | Low-priority addition | `-` | `$K(x,y)=\exp(-\gamma SBD(x,y))$` | RBF-like kernel on SBD. |
| [soft_dtw_kernel](docs/method-animations/kernel.md#soft_dtw_kernel) | similarity | not guaranteed | O(nm) | yes | yes | reference | Low-priority addition | `-` | `$K(x,y)=\exp(-D^\gamma(x,y)/\gamma)$` | Kernelized soft-DTW divergence. |
| [gak](docs/method-animations/kernel.md#gak) | similarity | yes after normalization in practice | O(nm) | yes | yes | exact | Low-priority addition | `-` | `$K_G(x,y)=\sum_{\pi} \prod_{(i,j)\in\pi} k(x_i,y_j)$` | Global Alignment Kernel. |
| [lgak](docs/method-animations/kernel.md#lgak) | similarity | not a metric | O(nm) | yes | yes | exact | Low-priority addition | `-` | `$\log(K_G(x,y)+\epsilon)$` | Log-transformed GAK. |
| [weighted_ncc_kernel](docs/method-animations/kernel.md#weighted_ncc_kernel) | similarity | not guaranteed | O(n \log n) or O(n^2) | yes | yes | reference | Low-priority addition | `-` | `$K(x,y)=\sum_k w_k \cdot NCC_k(x,y)$` | Shift-aware weighted cross-correlation kernel. |

### feature-based

Compare derived features instead of raw waveforms.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| [stats_distance](docs/method-animations/feature-based.md#stats_distance) | distance | yes in feature space | O(n·d) | yes | yes | exact | Possible addition | `-` | `$d(x,y)=\\|\phi_{\mathrm{stats}}(x)-\phi_{\mathrm{stats}}(y)\\|_2$` | Distance on basic summary statistics. |
| [robust_stats_distance](docs/method-animations/feature-based.md#robust_stats_distance) | distance | yes in feature space | O(n·d) | yes | yes | exact | Possible addition | `-` | `$d(x,y)=\\|\phi_{\mathrm{robust}}(x)-\phi_{\mathrm{robust}}(y)\\|_2$` | Distance on robust statistics. |
| [acf_distance](docs/method-animations/feature-based.md#acf_distance) | distance | yes in feature space | O(nL) | yes | univariate only | exact | Implemented in EchoTime | `acf_distance` | `$d(x,y)=\\|ACF(x)-ACF(y)\\|_2$` | Autocorrelation-feature distance. |
| [spectral_cosine_similarity](docs/method-animations/feature-based.md#spectral_cosine_similarity) | similarity | no | O(n \log n) | yes | yes | exact | Conceptually covered | `spectral_similarity` | `$s(x,y)=s_{\cos}(\|FFT(x)\|,\|FFT(y)\|)$` | Cosine similarity in the magnitude spectrum. |
| [spectral_distance](docs/method-animations/feature-based.md#spectral_distance) | distance-like | no | O(n \log n) | yes | yes | exact | Possible addition | `-` | `$d(x,y)=1-s_{\cos}(\|FFT(x)\|,\|FFT(y)\|)$` | Distance-like spectral measure. |
| [periodogram_distance](docs/method-animations/feature-based.md#periodogram_distance) | distance | yes in feature space | O(n \log n) | yes | yes | exact | Implemented in EchoTime | `periodogram_distance` | `$d(x,y)=\\|P_x-P_y\\|_2$` | Distance between normalized periodograms. |
| [paa_distance](docs/method-animations/feature-based.md#paa_distance) | distance | yes in feature space | O(n·d) | yes | yes | exact | Possible addition | `-` | `$d(x,y)=\\|PAA(x)-PAA(y)\\|_2$` | Piecewise Aggregate Approximation distance. |
| [dwt_distance](docs/method-animations/feature-based.md#dwt_distance) | distance | yes in feature space | O(n·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=\\|W(x)-W(y)\\|_2$` | Distance on Haar wavelet coefficients. |
| [histogram_distance](docs/method-animations/feature-based.md#histogram_distance) | distance | yes in feature space | O(n·d) | yes | yes | exact | Possible addition | `-` | `$d(x,y)=\\|h(x)-h(y)\\|_2$` | Value-histogram distance. |
| [permutation_entropy_distance](docs/method-animations/feature-based.md#permutation_entropy_distance) | distance-like | no | O(n) | yes | univariate only | exact | Possible addition | `-` | `$d(x,y)=\|H_{\pi}(x)-H_{\pi}(y)\|$` | Absolute difference in permutation entropy. |
| [ordinal_pattern_js_distance](docs/method-animations/feature-based.md#ordinal_pattern_js_distance) | distance | yes on pattern distributions; pseudometric on series | O(n) | yes | univariate only | exact | Implemented in EchoTime | `ordinal_pattern_js_distance` | `$d(x,y)=\sqrt{JSD(\Pi(x),\Pi(y))}$` | Square root of Jensen-Shannon divergence between ordinal-pattern distributions; distinct series can have identical pattern distributions. |
| [trend_distance](docs/method-animations/feature-based.md#trend_distance) | distance | yes in feature space | O(n·d) | yes | yes | exact | Implemented in EchoTime | `trend_distance` | `$d(x,y)=\\|\phi_{\mathrm{trend}}(x)-\phi_{\mathrm{trend}}(y)\\|_2$` | Distance on trend/intercept/residual features. |
| [sax_hamming_distance](docs/method-animations/feature-based.md#sax_hamming_distance) | distance | yes on symbolic strings | O(n) | yes | univariate only | exact | Possible addition | `-` | `$d(x,y)=\frac{1}{w}\sum_{i=1}^w [SAX_i(x)\neq SAX_i(y)]$` | Hamming distance on SAX words. |
| [sax_mindist](docs/method-animations/feature-based.md#sax_mindist) | distance | no; lower bound under SAX assumptions | O(w) | yes | univariate only | exact | Possible addition | `-` | `$MINDIST(\hat x,\hat y)=\sqrt{\frac{n}{w}}\sqrt{\sum_i dist(\hat x_i,\hat y_i)^2}$` | Lower-bounding symbolic dissimilarity under SAX normalization and aggregation assumptions. Adjacent symbols can have zero distance; lower-bounding does not imply metric properties. |
| [bag_of_patterns_cosine_similarity](docs/method-animations/feature-based.md#bag_of_patterns_cosine_similarity) | similarity | no | O(nw) | yes | univariate only | reference | Possible addition | `-` | `$s(x,y)=s_{\cos}(BoP(x),BoP(y))$` | Cosine similarity on bag-of-patterns histograms. |
| [bag_of_patterns_distance](docs/method-animations/feature-based.md#bag_of_patterns_distance) | distance-like | no | O(nw) | yes | univariate only | reference | Possible addition | `-` | `$d(x,y)=1-s_{\cos}(BoP(x),BoP(y))$` | Distance-like bag-of-patterns measure. |
| [independent_stats_distance](docs/method-animations/feature-based.md#independent_stats_distance) | distance | yes in feature space | O(dn) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c \\|\phi(X^{(c)})-\phi(Y^{(c)})\\|_2$` | Channel-independent stats distance. |
| [independent_paa_distance](docs/method-animations/feature-based.md#independent_paa_distance) | distance | yes in feature space | O(dn) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c \\|PAA(X^{(c)})-PAA(Y^{(c)})\\|_2$` | Channel-independent PAA distance. |

### model-based

Compare fitted dynamics or transition structure.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| [ar_distance](docs/method-animations/model-based.md#ar_distance) | distance | yes in parameter space | O(np^2) | yes | univariate only | exact | Possible addition | `-` | `$d(x,y)=\\|\theta_{AR}(x)-\theta_{AR}(y)\\|_2$` | Distance between autoregressive coefficients. |
| [ar_spectrum_distance](docs/method-animations/model-based.md#ar_spectrum_distance) | distance | yes in spectral space | O(np^2 + Fp) | yes | univariate only | reference | Possible addition | `-` | `$d(x,y)=\\|\log S_{AR}(x)-\log S_{AR}(y)\\|_2$` | Distance between AR-implied log spectra. |
| [ar_prediction_error_distance](docs/method-animations/model-based.md#ar_prediction_error_distance) | distance-like | no | O(np^2) | yes | univariate only | reference | Possible addition | `-` | `$d(x,y)=\frac{1}{2}(MSE_{x\to y}+MSE_{y\to x})$` | Symmetric cross-prediction error. |
| [markov_distance](docs/method-animations/model-based.md#markov_distance) | distance | yes in transition space | O(n) | yes | univariate only | exact | Possible addition | `-` | `$d(x,y)=\\|P_x-P_y\\|_F$` | Distance between discretized transition matrices. |
| [linear_trend_model_distance](docs/method-animations/model-based.md#linear_trend_model_distance) | distance | yes in parameter space | O(n) | yes | univariate only | exact | Implemented in EchoTime | `linear_trend_model_distance` | `$d(x,y)=\\|\theta_{\mathrm{trend}}(x)-\theta_{\mathrm{trend}}(y)\\|_2$` | Distance between linear trend models. |

### embedding

Encode first, then compare in a latent or compressed space.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| [embedding_distance](docs/method-animations/embedding.md#embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=d_{\mathcal Z}(\phi(x),\phi(y))$` | Generic embedding-space distance. |
| [embedding_similarity](docs/method-animations/embedding.md#embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\mathcal Z}(\phi(x),\phi(y))$` | Generic embedding-space similarity. |
| [paa_embedding_distance](docs/method-animations/embedding.md#paa_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the PAA encoder. |
| [paa_embedding_similarity](docs/method-animations/embedding.md#paa_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the PAA encoder. |
| [dft_embedding_distance](docs/method-animations/embedding.md#dft_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the DFT-magnitude encoder. |
| [dft_embedding_similarity](docs/method-animations/embedding.md#dft_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the DFT-magnitude encoder. |
| [stats_embedding_distance](docs/method-animations/embedding.md#stats_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the basic-statistics encoder. |
| [stats_embedding_similarity](docs/method-animations/embedding.md#stats_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the basic-statistics encoder. |
| [robust_stats_embedding_distance](docs/method-animations/embedding.md#robust_stats_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the robust-statistics encoder. |
| [robust_stats_embedding_similarity](docs/method-animations/embedding.md#robust_stats_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the robust-statistics encoder. |
| [acf_embedding_distance](docs/method-animations/embedding.md#acf_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the ACF encoder. |
| [acf_embedding_similarity](docs/method-animations/embedding.md#acf_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the ACF encoder. |
| [wavelet_embedding_distance](docs/method-animations/embedding.md#wavelet_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the wavelet encoder. |
| [wavelet_embedding_similarity](docs/method-animations/embedding.md#wavelet_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the wavelet encoder. |
| [histogram_embedding_distance](docs/method-animations/embedding.md#histogram_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the histogram encoder. |
| [histogram_embedding_similarity](docs/method-animations/embedding.md#histogram_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the histogram encoder. |
| [periodogram_embedding_distance](docs/method-animations/embedding.md#periodogram_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the periodogram encoder. |
| [periodogram_embedding_similarity](docs/method-animations/embedding.md#periodogram_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the periodogram encoder. |
| [trend_embedding_distance](docs/method-animations/embedding.md#trend_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the trend-feature encoder. |
| [trend_embedding_similarity](docs/method-animations/embedding.md#trend_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the trend-feature encoder. |
| [random_projection_embedding_distance](docs/method-animations/embedding.md#random_projection_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the random projection encoder. |
| [random_projection_embedding_similarity](docs/method-animations/embedding.md#random_projection_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the random projection encoder. |
| [identity_embedding_distance](docs/method-animations/embedding.md#identity_embedding_distance) | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the identity-resample encoder. |
| [identity_embedding_similarity](docs/method-animations/embedding.md#identity_embedding_similarity) | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the identity-resample encoder. |
