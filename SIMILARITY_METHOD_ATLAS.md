# EchoTime similarity method atlas

This guide audits EchoTime's current raw-series similarity stack, then imports the full method registry from `ts_similarity_package_v2_pkg` and marks which methods fit EchoTime's product direction.

## Current EchoTime comparison layer

### shape_similarity

- family: EchoTime native component
- kind: similarity
- formula: `s_shape = GM(clip(r(x,y), 0, 1), clip(r(Delta x, Delta y), 0, 1))`
- note: Combines level correlation with first-difference correlation so the headline match does not ignore local dynamics.

### dtw_similarity

- family: EchoTime native component
- kind: similarity
- formula: `s_dtw = GM(exp(-DTW_w(x,y)/0.45), exp(-DTW_w(Delta x, Delta y)/0.35))`
- note: Turns constrained DTW distances into a similarity score and blends level-space and derivative-space warping.

### trend_similarity

- family: EchoTime native component
- kind: similarity
- formula: `s_trend = GM(clip(r(T(x), T(y)), 0, 1), clip(r(Delta T(x), Delta T(y)), 0, 1))`
- note: Smooths both series first, then compares both the trend level and the trend slope.

### derivative_similarity

- family: EchoTime native component
- kind: similarity
- formula: `s_diff = clip(r(Delta x, Delta y), 0, 1)`
- note: Focuses on whether local changes move together even when the levels differ.

### spectral_similarity

- family: EchoTime native component
- kind: similarity
- formula: `s_spec = GM(1 - JSD(P_x, P_y), clip(r(P_x - U, P_y - U), 0, 1))`
- note: Compares normalized spectra of differenced series, mixing JS overlap with structural similarity relative to a uniform spectrum U.

### pearson_r

- family: EchoTime reference metric
- kind: similarity
- formula: `r(x,y) = sum_t (x_t - x_bar)(y_t - y_bar) / sqrt(sum_t (x_t - x_bar)^2 sum_t (y_t - y_bar)^2)`
- note: Familiar linear correlation exposed directly in every raw-series similarity report.

### spearman_rho

- family: EchoTime reference metric
- kind: similarity
- formula: `rho(x,y) = corr(rank(x), rank(y))`
- note: Rank-order correlation used as a robustness check against nonlinear monotone relationships.

### kendall_tau

- family: EchoTime reference metric
- kind: similarity
- formula: `tau(x,y) = (C - D) / choose(n, 2)`
- note: Pairwise concordance measure that stays interpretable when rank ordering matters more than amplitude.

### best_lag_pearson_r

- family: EchoTime reference metric
- kind: similarity
- formula: `max_lag_r(x,y) = max_ell r(x_t, y_{t-ell})`
- note: Searches over a bounded lag window to show whether a shift-aware linear relationship is stronger than the aligned one.

### normalized_mutual_information

- family: EchoTime reference metric
- kind: similarity
- formula: `NMI(X,Y) = I(X;Y) / sqrt(H(X) H(Y))`
- note: Histogram-based nonlinear dependence score used as a familiar cross-check against linear metrics.

## Implemented and high-fit additions from ts_similarity_package_v2_pkg

| method | family | EchoTime fit | EchoTime API | formula | why it matters |
|---|---|---|---|---|---|
| independent_max_ncc | sliding | Implemented in EchoTime | `independent_max_ncc` | `$s(X,Y)=\frac{1}{d}\sum_c \max_k NCC_k(X^{(c)},Y^{(c)})$` | This method is now available as a public low-level EchoTime similarity function. |
| independent_sbd | sliding | Implemented in EchoTime | `independent_sbd` | `$d(X,Y)=\frac{1}{d}\sum_c SBD(X^{(c)},Y^{(c)})$` | This method is now available as a public low-level EchoTime similarity function. |
| max_normalized_cross_correlation | sliding | Implemented in EchoTime | `max_ncc` | `$s(x,y)=\max_k NCC_k(x,y)$` | This method is now available as a public low-level EchoTime similarity function. |
| sbd | sliding | Implemented in EchoTime | `sbd` | `$d(x,y)=1-\max_k NCC_k(x,y)$` | This method is now available as a public low-level EchoTime similarity function. |
| edr | elastic | Implemented in EchoTime | `edr_distance` | `$EDR_{\epsilon}(x,y)$` | This method is now available as a public low-level EchoTime similarity function. |
| erp | elastic | Implemented in EchoTime | `erp_distance` | `$ERP(x,y;g)$` | This method is now available as a public low-level EchoTime similarity function. |
| lcss_distance | elastic | Implemented in EchoTime | `lcss_distance` | `$d(x,y)=1-s_{LCSS}(x,y)$` | This method is now available as a public low-level EchoTime similarity function. |
| lcss_similarity | elastic | Implemented in EchoTime | `lcss_similarity` | `$s(x,y)=LCSS_{\epsilon}(x,y)/\min(n,m)$` | This method is now available as a public low-level EchoTime similarity function. |
| twed | elastic | Implemented in EchoTime | `twed_distance` | `$TWED_{\lambda,\nu}(x,y)$` | This method is now available as a public low-level EchoTime similarity function. |
| acf_distance | feature-based | Implemented in EchoTime | `acf_distance` | `$d(x,y)=\\|ACF(x)-ACF(y)\\|_2$` | This method is now available as a public low-level EchoTime similarity function. |
| ordinal_pattern_js_distance | feature-based | Implemented in EchoTime | `ordinal_pattern_js_distance` | `$d(x,y)=JS(\Pi(x),\Pi(y))$` | This method is now available as a public low-level EchoTime similarity function. |
| periodogram_distance | feature-based | Implemented in EchoTime | `periodogram_distance` | `$d(x,y)=\\|P_x-P_y\\|_2$` | This method is now available as a public low-level EchoTime similarity function. |
| trend_distance | feature-based | Implemented in EchoTime | `trend_distance` | `$d(x,y)=\\|\phi_{\mathrm{trend}}(x)-\phi_{\mathrm{trend}}(y)\\|_2$` | This method is now available as a public low-level EchoTime similarity function. |
| linear_trend_model_distance | model-based | Implemented in EchoTime | `linear_trend_model_distance` | `$d(x,y)=\\|\theta_{\mathrm{trend}}(x)-\theta_{\mathrm{trend}}(y)\\|_2$` | This method is now available as a public low-level EchoTime similarity function. |

## Full extracted atlas

### lock-step

Pointwise comparison on an already aligned timeline.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| euclidean | distance | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sqrt{\sum_t \\|x_t-y_t\\|_2^2}$` | Equal-length pointwise Euclidean distance. |
| squared_euclidean | distance | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sum_t \\|x_t-y_t\\|_2^2$` | Squared Euclidean loss. |
| rmse_distance | distance | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sqrt{\frac{1}{nd}\sum_t \\|x_t-y_t\\|_2^2}$` | Root-mean-square error over aligned points. |
| manhattan | distance | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sum_t \\|x_t-y_t\\|_1$` | L1 distance. |
| mae_distance | distance | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{1}{nd}\sum_t \\|x_t-y_t\\|_1$` | Mean absolute error. |
| minkowski | distance | yes (p≥1) | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d_p(x,y)=\left(\sum_t \\|x_t-y_t\\|_p^p\right)^{1/p}$` | Generalized Lp distance. |
| chebyshev | distance | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\max_t \\|x_t-y_t\\|_{\infty}$` | Maximum deviation distance. |
| canberra | distance | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sum_i \frac{\|x_i-y_i\|}{\|x_i\|+\|y_i\|}$` | Relative L1 distance sensitive near zero. |
| bray_curtis | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{\sum_i \|x_i-y_i\|}{\sum_i \|x_i+y_i\|}$` | Bray-Curtis dissimilarity. |
| sorensen | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{\sum_i \|x_i-y_i\|}{\sum_i (\|x_i\|+\|y_i\|)}$` | Sorensen dissimilarity. |
| soergel | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{\sum_i \|x_i-y_i\|}{\sum_i \max(\|x_i\|,\|y_i\|)}$` | Relative distance normalized by max magnitudes. |
| kulczynski | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{\sum_i \|x_i-y_i\|}{\sum_i \min(\|x_i\|,\|y_i\|)}$` | Kulczynski-style relative dissimilarity. |
| clark | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sqrt{\sum_i\left(\frac{\|x_i-y_i\|}{\|x_i\|+\|y_i\|}\right)^2}$` | Clark distance. |
| wave_hedges | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sum_i \frac{\|x_i-y_i\|}{\max(\|x_i\|,\|y_i\|)}$` | Wave-Hedges distance. |
| lorentzian | distance-like | not guaranteed | O(n·d) | no | yes | reference | Low-priority addition | `-` | `$d(x,y)=\sum_i \log(1+\|x_i-y_i\|)$` | Log-compressed deviation. |
| cosine_similarity | similarity | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$s(x,y)=\frac{\langle x,y\rangle}{\\|x\\|\\|y\\|}$` | Directional similarity. |
| cosine_distance | distance-like | no | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=1-s_{\cos}(x,y)$` | Monotone transform of cosine similarity. |
| angular_distance | distance | yes on normalized vectors | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\arccos(s_{\cos}(x,y))/\pi$` | Angle-based distance. |
| pearson_similarity | similarity | no | O(n·d) | no | yes | exact | Conceptually covered | `pearson_r` | `$r(x,y)=\frac{\sum_i(x_i-\bar x)(y_i-\bar y)}{\sqrt{\sum_i(x_i-\bar x)^2}\sqrt{\sum_i(y_i-\bar y)^2}}$` | Linear correlation. |
| pearson_distance | distance-like | no | O(n·d) | no | yes | exact | Conceptually covered | `pearson_r` | `$d(x,y)=1-r(x,y)$` | Correlation distance. |
| spearman_similarity | similarity | no | O(n \log n) | no | yes | reference | Conceptually covered | `spearman_rho` | `$s(x,y)=r(\mathrm{rank}(x),\mathrm{rank}(y))$` | Rank correlation similarity. |
| spearman_distance | distance-like | no | O(n \log n) | no | yes | reference | Conceptually covered | `spearman_rho` | `$d(x,y)=1-\rho(x,y)$` | Distance-like rank dissimilarity. |
| kendall_similarity | similarity | no | O(n^2) | no | yes | reference | Conceptually covered | `kendall_tau` | `$s(x,y)=\tau_b(x,y)$` | Kendall tau-b rank agreement. |
| kendall_distance | distance-like | no | O(n^2) | no | yes | reference | Conceptually covered | `kendall_tau` | `$d(x,y)=1-\tau_b(x,y)$` | Distance-like form of Kendall agreement. |
| jensen_shannon | distance | yes | O(n) | no | yes | exact | Conceptually covered | `spectral_similarity` | `$d(x,y)=\sqrt{\frac{1}{2}KL(x\\|m)+\frac{1}{2}KL(y\\|m)}$` | Symmetric divergence for nonnegative normalized sequences. |
| kl_divergence | divergence | no | O(n) | no | yes | exact | Low-priority addition | `-` | `$D_{KL}(x\\|y)=\sum_i p_i\log\frac{p_i}{q_i}$` | Asymmetric divergence. |
| jeffreys_divergence | divergence | no | O(n) | no | yes | exact | Low-priority addition | `-` | `$J(x,y)=KL(x\\|y)+KL(y\\|x)$` | Symmetrized KL divergence. |
| bhattacharyya_distance | distance-like | no | O(n) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=-\log\sum_i \sqrt{p_i q_i}$` | Distribution overlap distance. |
| hellinger_distance | distance | yes | O(n) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\sqrt{\frac{1}{2}\sum_i(\sqrt{p_i}-\sqrt{q_i})^2}$` | Probability-distribution distance. |
| chi_square_distance | distance-like | no | O(n) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\frac{1}{2}\sum_i\frac{(x_i-y_i)^2}{x_i+y_i}$` | Chi-square distance for histograms. |
| seuclidean_distance | distance | yes | O(n) | no | yes | reference | Low-priority addition | `-` | `$d(x,y)=\sqrt{\sum_i \frac{(x_i-y_i)^2}{v_i}}$` | Variance-standardized Euclidean distance. |
| znorm_euclidean | distance | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\\|\hat x-\hat y\\|_2$` | Euclidean after per-channel z-normalization. |
| znorm_manhattan | distance | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$d(x,y)=\\|\hat x-\hat y\\|_1$` | Manhattan after z-normalization. |
| cid_distance | distance-like | no | O(n·d) | no | yes | reference | Low-priority addition | `-` | `$CID(x,y)=ED(x,y)\cdot \frac{\max(CE(x),CE(y))}{\min(CE(x),CE(y))}$` | Complexity-invariant distance. |

### sliding

Shift-aware comparison under pure translation or lead-lag offsets.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| max_normalized_cross_correlation | similarity | no | O(n \log n) or O(n^2) | yes | yes | exact | Implemented in EchoTime | `max_ncc` | `$s(x,y)=\max_k NCC_k(x,y)$` | Maximum normalized cross-correlation over shifts. |
| sbd | distance-like | no | O(n \log n) or O(n^2) | yes | yes | exact | Implemented in EchoTime | `sbd` | `$d(x,y)=1-\max_k NCC_k(x,y)$` | Shape-based distance. |
| shift_euclidean_distance | distance-like | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=\min_k \\|x_{\Omega_k}-y_{\Omega_k}\\|_2$` | Best-overlap Euclidean distance over integer shifts. |
| shift_rmse_distance | distance-like | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=\min_k \sqrt{\frac{1}{\|\Omega_k\|}\sum_{t\in\Omega_k}(x_t-y_{t-k})^2}$` | Best-overlap RMSE. |
| shift_manhattan_distance | distance-like | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=\min_k \\|x_{\Omega_k}-y_{\Omega_k}\\|_1$` | Best-overlap L1 distance. |
| shift_mae_distance | distance-like | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=\min_k \frac{1}{\|\Omega_k\|}\\|x_{\Omega_k}-y_{\Omega_k}\\|_1$` | Best-overlap MAE. |
| shift_cosine_similarity | similarity | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$s(x,y)=\max_k s_{\cos}(x_{\Omega_k},y_{\Omega_k})$` | Best-overlap cosine similarity. |
| shift_cosine_distance | distance-like | no | O(n^2·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=1-\max_k s_{\cos}(x_{\Omega_k},y_{\Omega_k})$` | Distance-like shift-invariant cosine measure. |
| shift_pearson_similarity | similarity | no | O(n^2·d) | yes | yes | reference | Conceptually covered | `best_lag_pearson_r` | `$s(x,y)=\max_k r(x_{\Omega_k},y_{\Omega_k})$` | Best-overlap Pearson correlation. |
| shift_pearson_distance | distance-like | no | O(n^2·d) | yes | yes | reference | Conceptually covered | `best_lag_pearson_r` | `$d(x,y)=1-\max_k r(x_{\Omega_k},y_{\Omega_k})$` | Distance-like shift-invariant correlation measure. |
| independent_sbd | distance-like | no | O(dn\log n) | yes | multivariate only | exact | Implemented in EchoTime | `independent_sbd` | `$d(X,Y)=\frac{1}{d}\sum_c SBD(X^{(c)},Y^{(c)})$` | Channel-independent SBD. |
| independent_max_ncc | similarity | no | O(dn\log n) | yes | multivariate only | exact | Implemented in EchoTime | `independent_max_ncc` | `$s(X,Y)=\frac{1}{d}\sum_c \max_k NCC_k(X^{(c)},Y^{(c)})$` | Channel-independent maximum NCC. |

### elastic

Dynamic-programming alignments that allow local stretching or compression.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| dtw | distance | no | O(nm) | yes | yes | exact | Conceptually covered | `dtw_similarity` | `$DTW(x,y)=\min_{\pi}\sqrt{\sum_{(i,j)\in\pi} \\|x_i-y_j\\|_2^2}$` | Dynamic Time Warping. |
| cdtw | distance | no | O(nw) | yes | yes | exact | Conceptually covered | `dtw_similarity` | `$DTW_w(x,y)$ with Sakoe-Chiba window` | Constrained DTW. |
| itakura_dtw | distance | no | O(nm) | yes | yes | reference | Possible addition | `-` | `$DTW_{\mathrm{Itakura}}(x,y)$` | DTW under Itakura parallelogram constraint. |
| wdtw | distance | no | O(nm) | yes | yes | exact | Possible addition | `-` | `$WDTW(x,y)=\min_{\pi}\sqrt{\sum_{(i,j)\in\pi} w_{\|i-j\|}\\|x_i-y_j\\|_2^2}$` | Weighted DTW. |
| ddtw | distance | no | O(nm) | yes | yes | exact | Conceptually covered | `dtw_similarity` | `$DTW(\Delta x,\Delta y)$` | Derivative DTW. |
| wddtw | distance | no | O(nm) | yes | yes | exact | Possible addition | `-` | `$WDTW(\Delta x,\Delta y)$` | Weighted derivative DTW. |
| soft_dtw | distance-like | no | O(nm) | yes | yes | exact | Possible addition | `-` | `$sDTW_{\gamma}(x,y)$` | Soft minimum relaxation of DTW. |
| soft_dtw_divergence | distance-like | no | O(nm) | yes | yes | exact | Possible addition | `-` | `$D^{\gamma}(x,y)=sDTW(x,y)-\frac{1}{2}sDTW(x,x)-\frac{1}{2}sDTW(y,y)$` | Soft-DTW divergence. |
| lcss_similarity | similarity | no | O(nm) | yes | yes | exact | Implemented in EchoTime | `lcss_similarity` | `$s(x,y)=LCSS_{\epsilon}(x,y)/\min(n,m)$` | Longest Common Subsequence similarity. |
| lcss_distance | distance-like | no | O(nm) | yes | yes | exact | Implemented in EchoTime | `lcss_distance` | `$d(x,y)=1-s_{LCSS}(x,y)$` | Distance-like LCSS form. |
| edr | distance | no | O(nm) | yes | yes | exact | Implemented in EchoTime | `edr_distance` | `$EDR_{\epsilon}(x,y)$` | Edit distance on real sequence. |
| swale_similarity | similarity | no | O(nm) | yes | yes | reference | Possible addition | `-` | `$SWALE_{\epsilon}(x,y)$` | Similarity with reward and penalty. |
| erp | distance | yes | O(nm) | yes | yes | exact | Implemented in EchoTime | `erp_distance` | `$ERP(x,y;g)$` | Edit distance with real penalty. |
| msm | distance | yes | O(nm) | yes | univariate only | exact | Possible addition | `-` | `$MSM(x,y)$` | Move-Split-Merge distance. |
| twed | distance | yes | O(nm) | yes | yes | exact | Implemented in EchoTime | `twed_distance` | `$TWED_{\lambda,\nu}(x,y)$` | Time Warp Edit distance. |
| discrete_frechet | distance | yes | O(nm) | yes | yes | reference | Possible addition | `-` | `$\delta_F(x,y)$` | Discrete Fréchet distance. |
| needleman_wunsch_similarity | similarity | no | O(nm) | yes | yes | reference | Possible addition | `-` | `$NW(x,y)$` | Global alignment score. |
| smith_waterman_similarity | similarity | no | O(nm) | yes | yes | reference | Possible addition | `-` | `$SW(x,y)$` | Local alignment score. |
| shape_dtw | distance | no | O(nmr) | yes | yes | reference | Possible addition | `-` | `$DTW(\phi_{\mathrm{shape}}(x),\phi_{\mathrm{shape}}(y))$` | DTW on local shape descriptors. |
| independent_dtw | distance | no | O(dnm) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c DTW(X^{(c)},Y^{(c)})$` | Channel-independent DTW average. |
| independent_cdtw | distance | no | O(dnw) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c cDTW(X^{(c)},Y^{(c)})$` | Channel-independent constrained DTW. |
| independent_wdtw | distance | no | O(dnm) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c WDTW(X^{(c)},Y^{(c)})$` | Channel-independent weighted DTW. |
| independent_ddtw | distance | no | O(dnm) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c DDTW(X^{(c)},Y^{(c)})$` | Channel-independent derivative DTW. |
| independent_erp | distance | yes | O(dnm) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c ERP(X^{(c)},Y^{(c)})$` | Channel-independent ERP. |

### kernel

Similarity through kernel scores rather than direct distances.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| linear_kernel | similarity | PSD if input space valid | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$K(x,y)=\langle x,y \rangle$` | Linear kernel on flattened vectors. |
| polynomial_kernel | similarity | depends on parameters | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$K(x,y)=(\gamma \langle x,y \rangle + c)^p$` | Polynomial kernel. |
| sigmoid_kernel | similarity | not always PSD | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$K(x,y)=\tanh(\gamma \langle x,y \rangle + c)$` | Sigmoid kernel. |
| rbf_kernel | similarity | yes | O(n·d) | no | yes | exact | Low-priority addition | `-` | `$K(x,y)=\exp(-\gamma \\|x-y\\|_2^2)$` | Gaussian kernel over aligned vectors. |
| dtw_rbf_kernel | similarity | not guaranteed | O(nm) | yes | yes | reference | Low-priority addition | `-` | `$K(x,y)=\exp(-\gamma DTW(x,y)^2)$` | RBF on DTW distance. |
| sbd_kernel | similarity | not guaranteed | O(n \log n) or O(n^2) | yes | yes | reference | Low-priority addition | `-` | `$K(x,y)=\exp(-\gamma SBD(x,y))$` | RBF-like kernel on SBD. |
| soft_dtw_kernel | similarity | not guaranteed | O(nm) | yes | yes | reference | Low-priority addition | `-` | `$K(x,y)=\exp(-D^\gamma(x,y)/\gamma)$` | Kernelized soft-DTW divergence. |
| gak | similarity | yes after normalization in practice | O(nm) | yes | yes | exact | Low-priority addition | `-` | `$K_G(x,y)=\sum_{\pi} \prod_{(i,j)\in\pi} k(x_i,y_j)$` | Global Alignment Kernel. |
| lgak | similarity | not a metric | O(nm) | yes | yes | exact | Low-priority addition | `-` | `$\log(K_G(x,y)+\epsilon)$` | Log-transformed GAK. |
| weighted_ncc_kernel | similarity | not guaranteed | O(n \log n) or O(n^2) | yes | yes | reference | Low-priority addition | `-` | `$K(x,y)=\sum_k w_k \cdot NCC_k(x,y)$` | Shift-aware weighted cross-correlation kernel. |

### feature-based

Compare derived features instead of raw waveforms.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| stats_distance | distance | yes in feature space | O(n·d) | yes | yes | exact | Possible addition | `-` | `$d(x,y)=\\|\phi_{\mathrm{stats}}(x)-\phi_{\mathrm{stats}}(y)\\|_2$` | Distance on basic summary statistics. |
| robust_stats_distance | distance | yes in feature space | O(n·d) | yes | yes | exact | Possible addition | `-` | `$d(x,y)=\\|\phi_{\mathrm{robust}}(x)-\phi_{\mathrm{robust}}(y)\\|_2$` | Distance on robust statistics. |
| acf_distance | distance | yes in feature space | O(nL) | yes | univariate only | exact | Implemented in EchoTime | `acf_distance` | `$d(x,y)=\\|ACF(x)-ACF(y)\\|_2$` | Autocorrelation-feature distance. |
| spectral_cosine_similarity | similarity | no | O(n \log n) | yes | yes | exact | Conceptually covered | `spectral_similarity` | `$s(x,y)=s_{\cos}(\|FFT(x)\|,\|FFT(y)\|)$` | Cosine similarity in the magnitude spectrum. |
| spectral_distance | distance-like | no | O(n \log n) | yes | yes | exact | Possible addition | `-` | `$d(x,y)=1-s_{\cos}(\|FFT(x)\|,\|FFT(y)\|)$` | Distance-like spectral measure. |
| periodogram_distance | distance | yes in feature space | O(n \log n) | yes | yes | exact | Implemented in EchoTime | `periodogram_distance` | `$d(x,y)=\\|P_x-P_y\\|_2$` | Distance between normalized periodograms. |
| paa_distance | distance | yes in feature space | O(n·d) | yes | yes | exact | Possible addition | `-` | `$d(x,y)=\\|PAA(x)-PAA(y)\\|_2$` | Piecewise Aggregate Approximation distance. |
| dwt_distance | distance | yes in feature space | O(n·d) | yes | yes | reference | Possible addition | `-` | `$d(x,y)=\\|W(x)-W(y)\\|_2$` | Distance on Haar wavelet coefficients. |
| histogram_distance | distance | yes in feature space | O(n·d) | yes | yes | exact | Possible addition | `-` | `$d(x,y)=\\|h(x)-h(y)\\|_2$` | Value-histogram distance. |
| permutation_entropy_distance | distance-like | no | O(n) | yes | univariate only | exact | Possible addition | `-` | `$d(x,y)=\|H_{\pi}(x)-H_{\pi}(y)\|$` | Absolute difference in permutation entropy. |
| ordinal_pattern_js_distance | distance | yes | O(n) | yes | univariate only | exact | Implemented in EchoTime | `ordinal_pattern_js_distance` | `$d(x,y)=JS(\Pi(x),\Pi(y))$` | Jensen-Shannon distance between ordinal-pattern distributions. |
| trend_distance | distance | yes in feature space | O(n·d) | yes | yes | exact | Implemented in EchoTime | `trend_distance` | `$d(x,y)=\\|\phi_{\mathrm{trend}}(x)-\phi_{\mathrm{trend}}(y)\\|_2$` | Distance on trend/intercept/residual features. |
| sax_hamming_distance | distance | yes on symbolic strings | O(n) | yes | univariate only | exact | Possible addition | `-` | `$d(x,y)=\frac{1}{w}\sum_{i=1}^w [SAX_i(x)\neq SAX_i(y)]$` | Hamming distance on SAX words. |
| sax_mindist | distance | lower-bounding | O(w) | yes | univariate only | exact | Possible addition | `-` | `$MINDIST(\hat x,\hat y)=\sqrt{\frac{n}{w}}\sqrt{\sum_i dist(\hat x_i,\hat y_i)^2}$` | Lower-bounding symbolic distance in SAX space. |
| bag_of_patterns_cosine_similarity | similarity | no | O(nw) | yes | univariate only | reference | Possible addition | `-` | `$s(x,y)=s_{\cos}(BoP(x),BoP(y))$` | Cosine similarity on bag-of-patterns histograms. |
| bag_of_patterns_distance | distance-like | no | O(nw) | yes | univariate only | reference | Possible addition | `-` | `$d(x,y)=1-s_{\cos}(BoP(x),BoP(y))$` | Distance-like bag-of-patterns measure. |
| independent_stats_distance | distance | yes in feature space | O(dn) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c \\|\phi(X^{(c)})-\phi(Y^{(c)})\\|_2$` | Channel-independent stats distance. |
| independent_paa_distance | distance | yes in feature space | O(dn) | yes | multivariate only | exact | Possible addition | `-` | `$d(X,Y)=\frac{1}{d}\sum_c \\|PAA(X^{(c)})-PAA(Y^{(c)})\\|_2$` | Channel-independent PAA distance. |

### model-based

Compare fitted dynamics or transition structure.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| ar_distance | distance | yes in parameter space | O(np^2) | yes | univariate only | exact | Possible addition | `-` | `$d(x,y)=\\|\theta_{AR}(x)-\theta_{AR}(y)\\|_2$` | Distance between autoregressive coefficients. |
| ar_spectrum_distance | distance | yes in spectral space | O(np^2 + Fp) | yes | univariate only | reference | Possible addition | `-` | `$d(x,y)=\\|\log S_{AR}(x)-\log S_{AR}(y)\\|_2$` | Distance between AR-implied log spectra. |
| ar_prediction_error_distance | distance-like | no | O(np^2) | yes | univariate only | reference | Possible addition | `-` | `$d(x,y)=\frac{1}{2}(MSE_{x\to y}+MSE_{y\to x})$` | Symmetric cross-prediction error. |
| markov_distance | distance | yes in transition space | O(n) | yes | univariate only | exact | Possible addition | `-` | `$d(x,y)=\\|P_x-P_y\\|_F$` | Distance between discretized transition matrices. |
| linear_trend_model_distance | distance | yes in parameter space | O(n) | yes | univariate only | exact | Implemented in EchoTime | `linear_trend_model_distance` | `$d(x,y)=\\|\theta_{\mathrm{trend}}(x)-\theta_{\mathrm{trend}}(y)\\|_2$` | Distance between linear trend models. |

### embedding

Encode first, then compare in a latent or compressed space.

| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |
|---|---|---|---|---|---|---|---|---|---|---|
| embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=d_{\mathcal Z}(\phi(x),\phi(y))$` | Generic embedding-space distance. |
| embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\mathcal Z}(\phi(x),\phi(y))$` | Generic embedding-space similarity. |
| paa_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the PAA encoder. |
| paa_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the PAA encoder. |
| dft_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the DFT-magnitude encoder. |
| dft_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the DFT-magnitude encoder. |
| stats_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the basic-statistics encoder. |
| stats_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the basic-statistics encoder. |
| robust_stats_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the robust-statistics encoder. |
| robust_stats_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the robust-statistics encoder. |
| acf_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the ACF encoder. |
| acf_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the ACF encoder. |
| wavelet_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the wavelet encoder. |
| wavelet_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the wavelet encoder. |
| histogram_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the histogram encoder. |
| histogram_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the histogram encoder. |
| periodogram_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the periodogram encoder. |
| periodogram_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the periodogram encoder. |
| trend_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the trend-feature encoder. |
| trend_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the trend-feature encoder. |
| random_projection_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the random projection encoder. |
| random_projection_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the random projection encoder. |
| identity_embedding_distance | distance | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$d(x,y)=\\|\phi(x)-\phi(y)\\|_2$` | Euclidean distance using the identity-resample encoder. |
| identity_embedding_similarity | similarity | depends on latent metric | depends on encoder | yes | yes | adapter | Low-priority addition | `-` | `$s(x,y)=s_{\cos}(\phi(x),\phi(y))$` | Cosine similarity using the identity-resample encoder. |
