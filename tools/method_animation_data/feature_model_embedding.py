"""Deterministic teaching examples for feature, model and embedding comparisons.

The computations below define the depicted examples. They are not additional
EchoTime public methods, fitted pretrained models, or benchmark results.
"""

from __future__ import annotations

from copy import deepcopy
from itertools import permutations
from math import factorial

import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import norm


SOURCE_ROOT = "https://github.com/ZipengWu365/EchoTime/blob/main/"
LOCAL = {"label": "EchoTime low-level implementation", "url": SOURCE_ROOT + "src/echotime/similarity_methods.py"}
REGISTRY = {"label": "Imported registry: named feature and comparison conventions", "url": SOURCE_ROOT + "src/echotime/data/ts_similarity_package_v2_registry.csv"}
GENERATOR = {"label": "Exact illustrative inputs and encoder definitions", "url": SOURCE_ROOT + "tools/method_animation_data/feature_model_embedding.py"}
PAA_SOURCE = {"label": "tslearn: piecewise aggregate approximation", "url": "https://tslearn.readthedocs.io/en/stable/gen_modules/piecewise/tslearn.piecewise.PiecewiseAggregateApproximation.html"}
SAX_SOURCE = {"label": "Lin et al. (2007), Experiencing SAX, author copy", "url": "https://www.cs.ucr.edu/~stelo/papers/DMKD07b.pdf"}
BOP_SOURCE = {"label": "Lin, Khade and Li (2012), bag-of-patterns representation", "url": "https://link.springer.com/article/10.1007/s10844-012-0196-5"}
FFT_SOURCE = {"label": "NumPy: real-input discrete Fourier transform", "url": "https://numpy.org/doc/stable/reference/generated/numpy.fft.rfft.html"}
WAVELET_SOURCE = {"label": "PyWavelets: Haar approximation and detail coefficients", "url": "https://pywavelets.readthedocs.io/en/latest/ref/dwt-discrete-wavelet-transform.html"}
ACF_SOURCE = {"label": "statsmodels: ACF denominator and adjusted convention", "url": "https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.acf.html"}
HIST_SOURCE = {"label": "NumPy: histogram bins and normalization", "url": "https://numpy.org/doc/stable/reference/generated/numpy.histogram.html"}
PE_SOURCE = {"label": "Bandt and Pompe (2002), permutation entropy", "url": "https://doi.org/10.1103/PhysRevLett.88.174102"}
JS_SOURCE = {"label": "SciPy: square-root Jensen-Shannon divergence", "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.jensenshannon.html"}
AR_SOURCE = {"label": "statsmodels: conditional least-squares autoregression", "url": "https://www.statsmodels.org/stable/generated/statsmodels.tsa.ar_model.AutoReg.html"}
AR_SPECTRUM_SOURCE = {"label": "statsmodels: ARMA lag-polynomial spectra", "url": "https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima_process.arma_periodogram.html"}
PROJECTION_SOURCE = {"label": "scikit-learn: Gaussian random projection", "url": "https://scikit-learn.org/stable/modules/random_projection.html"}
STAT_SOURCE = {"label": "NumPy: summary-statistic definitions", "url": "https://numpy.org/doc/stable/reference/routines.statistics.html"}


def _inputs():
    t = np.arange(16, dtype=float)
    x = .9 * np.sin(2 * np.pi * t / 8) + .22 * np.sin(2 * np.pi * t / 3) + .05 * t
    y = .75 * np.sin(2 * np.pi * (t - 1) / 8) + .18 * np.cos(2 * np.pi * t / 4) + .035 * t + .15
    return x, y


def _list(x):
    return np.asarray(x, dtype=float).tolist()


def _z(x):
    x = np.asarray(x, dtype=float)
    return (x - x.mean()) / x.std()


def _cos(a, b):
    a, b = np.asarray(a), np.asarray(b)
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator <= 0:
        raise ValueError("Cosine teaching examples require nonzero feature vectors.")
    return float(np.clip(np.dot(a, b) / denominator, -1., 1.))


def _paa(x, w=4):
    x = np.asarray(x)
    if len(x) % w:
        raise ValueError("These equal-block teaching examples use divisible lengths.")
    return x.reshape(w, len(x) // w).mean(axis=1)


def _stats(x):
    return np.array([np.mean(x), np.std(x), np.min(x), np.max(x)])


def _robust(x):
    q = np.quantile(x, [.25, .5, .75], method="linear")
    return np.r_[q, np.median(np.abs(x - q[1]))]


def _acf(x, k=6):
    z = np.asarray(x) - np.mean(x)
    return np.array([np.dot(z[:-lag], z[lag:]) / ((len(z) - lag) * np.var(z)) for lag in range(1, k + 1)])


def _power(x):
    p = np.abs(np.fft.rfft(x)) ** 2
    return p / p.sum()


def _haar(x):
    a = np.asarray(x, dtype=float)
    details = []
    while len(a) > 1:
        details.append((a[::2] - a[1::2]) / np.sqrt(2))
        a = (a[::2] + a[1::2]) / np.sqrt(2)
    return np.concatenate([a] + details[::-1])


def _trend(x):
    t = np.arange(len(x), dtype=float)
    slope, intercept = np.polyfit(t, x, 1)
    return np.array([intercept, slope, np.std(x - (intercept + slope * t))])


HIST_EDGES = np.linspace(-1.5, 2., 8)
RP = np.random.default_rng(20261029).normal(size=(6, 16)) / np.sqrt(6)


def _hist(x):
    count = np.histogram(x, bins=HIST_EDGES)[0].astype(float)
    if count.sum() != len(x):
        raise ValueError("The fixed illustrative bins must include all observations.")
    return count / count.sum()


def _generic(x):
    return np.array([np.mean(x), np.std(x), _acf(x, 1)[0], _trend(x)[1]])


ENCODERS = {
    "stats": {
        "name": "Basic statistics", "zh": "基础统计量", "fn": _stats,
        "labels": ["mean", "SD", "min", "max"],
        "explanation_en": "Represent each series by its mean, population standard deviation, minimum and maximum. These four coordinates summarize level, spread and range; their order in the vector is fixed, while the original temporal order is discarded.",
        "explanation_zh": "把每条序列表示为均值、总体标准差、最小值和最大值四个坐标。它们概括水平、波动和范围，坐标顺序固定，但原始时间顺序被舍弃。",
        "extract_en": "Compute mean, population SD, minimum and maximum in that order.",
        "extract_zh": "按均值、总体标准差、最小值、最大值的顺序提取特征。",
        "caveats_en": ["Permuting observations leaves this vector unchanged, even when temporal behavior changes completely.", "Features have different scales; this example uses no coordinate weighting. A production scaler must be fitted without test-data leakage."],
        "caveats_zh": ["任意重排序列不会改变该向量，即使时间行为发生显著变化。", "各坐标尺度不同；本例不加权。实际使用的缩放器应避免测试数据泄漏。"],
        "parameters": {"features": ["mean", "std_ddof0", "min", "max"], "coordinate_scaling": "none"},
        "sources": [STAT_SOURCE, REGISTRY],
    },
    "robust_stats": {
        "name": "Robust statistics", "zh": "稳健统计量", "fn": _robust,
        "labels": ["Q25", "median", "Q75", "MAD"],
        "explanation_en": "Replace extrema and moments with the lower quartile, median, upper quartile and median absolute deviation. This explicit descriptor emphasizes the central distribution and reduces the influence of isolated extreme values. It does not preserve the timing of those values.",
        "explanation_zh": "使用下四分位数、中位数、上四分位数和中位绝对偏差构成明确的描述向量。它强调分布的中心部分，降低孤立极端值的影响，同时舍弃这些数值出现的时刻。",
        "extract_en": "Calculate Q25, median, Q75 and unscaled median absolute deviation.",
        "extract_zh": "计算 Q25、中位数、Q75 和未经常数缩放的中位绝对偏差。",
        "caveats_en": ["Robustness concerns these particular statistics, not immunity to arbitrary contamination or distribution shift.", "Quantiles use linear interpolation and MAD is unscaled; alternative conventions produce different vectors."],
        "caveats_zh": ["稳健性针对所选统计量，并不表示可抵抗任意污染或分布变化。", "本例分位数采用线性插值，MAD 不乘缩放常数；其他约定会产生不同向量。"],
        "parameters": {"features": ["q25", "median", "q75", "unscaled_MAD"], "quantile_method": "linear"},
        "sources": [STAT_SOURCE, REGISTRY],
    },
    "paa": {
        "name": "PAA block means", "zh": "PAA 分段均值", "fn": _paa,
        "labels": ["block 1", "block 2", "block 3", "block 4"],
        "explanation_en": "Split the 16 observations into four equal, consecutive blocks and replace each block by its mean. Comparing these ordered block averages emphasizes coarse temporal structure. The animation highlights the exact observations contributing to each coordinate.",
        "explanation_zh": "把 16 个观测分成四个连续等长区间，每个区间用均值表示。比较这些有序均值可突出较粗的时间结构；动图逐块高亮每个坐标所使用的观测。",
        "extract_en": "Average each consecutive block of four observations to obtain four coordinates.",
        "extract_zh": "每四个连续观测求一次均值，得到四个坐标。",
        "caveats_en": ["The displayed Euclidean feature distance is unscaled; the usual length-scaled PAA lower bound additionally multiplies it by sqrt(n/w).", "Short events within a block can cancel, and moving a block boundary can alter the representation."],
        "caveats_zh": ["图中欧氏特征距离未经长度缩放；常用 PAA 下界还需乘以 sqrt(n/w)。", "区间内的短暂事件可能互相抵消，改变分段边界也会改变表示。"],
        "parameters": {"n_segments": 4, "block_size": 4, "z_normalization": False, "distance_length_scaling": False},
        "sources": [PAA_SOURCE, REGISTRY],
    },
    "acf": {
        "name": "Autocorrelation features", "zh": "自相关特征", "fn": _acf,
        "labels": ["lag " + str(k) for k in range(1, 7)],
        "explanation_en": "Center each series and compare it with delayed versions of itself. Six lag coordinates summarize repeated linear dependence. This example follows EchoTime's adjusted denominator, (n-lag) times the population variance, and omits the always-one lag-zero coordinate.",
        "explanation_zh": "先对序列去均值，再与自身的延迟版本比较。六个滞后坐标描述重复出现的线性依赖。本例采用 EchoTime 的调整分母，即 (n-lag) 乘总体方差，并省略恒为一的零滞后坐标。",
        "extract_en": "At each lag, sum centered lagged products and divide by (n-lag) times variance.",
        "extract_zh": "逐个滞后累加去均值后的乘积，除以 (n-lag) 乘方差。",
        "caveats_en": ["Adjusted high-lag sample estimates need not remain inside [-1,1]; estimates are less reliable with fewer overlapping pairs.", "ACF drops the mean and amplitude scale and cannot fully identify nonlinear dependence or the original waveform."],
        "caveats_zh": ["经过样本数调整的高滞后估计不一定落在 [-1,1]，重叠点越少估计越不稳定。", "ACF 舍弃均值和振幅尺度，无法完整识别非线性依赖或恢复原波形。"],
        "parameters": {"max_lag": 6, "denominator": "(n-lag)*population_variance", "lag_zero": "omitted"},
        "sources": [LOCAL, ACF_SOURCE],
    },
    "dft": {
        "name": "DFT magnitudes", "zh": "DFT 幅值", "fn": lambda x: np.abs(np.fft.rfft(x)),
        "labels": ["k" + str(k) for k in range(9)],
        "explanation_en": "Project the series onto sine and cosine bases, combine the real and imaginary parts into magnitudes, and compare the resulting frequency bins. The example retains all nine nonnegative-frequency bins of a length-16 real transform, including the DC bin.",
        "explanation_zh": "把序列投影到正弦、余弦基上，将实部和虚部合成为幅值，再比较频率坐标。本例保留长度 16 实数变换的全部九个非负频率坐标，包括直流分量。",
        "extract_en": "Compute the unnormalized real FFT and retain the magnitude of each bin.",
        "extract_zh": "计算未归一化的实数 FFT，保留各频率坐标的模。",
        "caveats_en": ["Magnitude discards phase; a circular shift changes Fourier phase while preserving these magnitudes.", "The DC coordinate reflects the mean, and raw magnitudes depend on record length and amplitude. Matching sampling rates and frequency grids is required.", "This example compares unweighted nonnegative-frequency rFFT magnitudes. Comparing a full FFT, or weighting interior rFFT magnitudes by sqrt(2), gives a different distance/cosine convention."],
        "caveats_zh": ["幅值表示舍弃相位；循环平移改变傅里叶相位，却保留这些幅值。", "直流坐标反映均值，原始幅值依赖记录长度与振幅；比较时需要一致的采样率和频率网格。", "本例比较未加权的非负频率 rFFT 幅值。比较完整 FFT 或将内部 rFFT 幅值乘 sqrt(2)，对应不同的距离与余弦约定。"],
        "parameters": {"fft": "rfft", "normalization": "backward", "n_bins": 9, "include_DC": True},
        "sources": [FFT_SOURCE, REGISTRY],
    },
    "periodogram": {
        "name": "Normalized FFT-bin powers", "zh": "归一化 FFT 频点功率", "fn": _power,
        "labels": ["k" + str(k) for k in range(9)],
        "explanation_en": "Square the real-FFT magnitudes and normalize their sum to one. EchoTime compares these power-share vectors with Euclidean distance. The example retains all nine bins and the mean-related DC component, so every coordinate represents a share of this particular discrete power convention.",
        "explanation_zh": "将实数 FFT 幅值平方，再除以总和得到功率占比向量。EchoTime 使用欧氏距离比较该向量。本例保留全部九个频点和与均值相关的直流项，因此每个坐标都是这一离散功率约定下的占比。",
        "extract_en": "Square each rFFT magnitude, then divide by the sum over all retained nonnegative-frequency bins.",
        "extract_zh": "对 rFFT 幅值逐点平方，再除以全部非负频点功率的总和。",
        "caveats_en": ["This is EchoTime's normalized rFFT-bin convention: no detrending, window, or one-sided interior-bin doubling. It is not a physical-density PSD estimate.", "Normalization discards total power and phase; positive amplitude rescaling alone leaves this representation unchanged."],
        "caveats_zh": ["这是 EchoTime 的归一化 rFFT 频点约定：不去趋势、不加窗，也不把单边谱内部频点乘二；它不等于具有物理单位的功率谱密度估计。", "归一化舍弃总功率和相位；单纯的正振幅缩放不会改变此表示。"],
        "parameters": {"n_coeffs": 9, "normalization": "divide rFFT squared magnitudes by their sum", "detrend": False, "one_sided_doubling": False},
        "sources": [LOCAL, FFT_SOURCE],
    },
    "wavelet": {
        "name": "Coarse Haar coefficients", "zh": "较粗尺度 Haar 系数", "fn": lambda x: _haar(x)[:8],
        "labels": ["A4", "D4", "D3a", "D3b", "D2a", "D2b", "D2c", "D2d"],
        "explanation_en": "Recursively average and difference adjacent pairs with orthonormal Haar scaling. Keep the coarsest average and the next three detail levels: eight of the 16 coefficients. Comparing this vector emphasizes retained scales while deliberately discarding the finest eight detail coefficients.",
        "explanation_zh": "对相邻点反复计算带正交归一化的和与差。本例保留最粗近似及随后三级细节，共 16 个系数中的八个；比较这些坐标强调所保留尺度，并主动舍弃最细的八个细节系数。",
        "extract_en": "Apply Haar pair averages/differences recursively and retain [A4,D4,D3,D2].",
        "extract_zh": "递归计算 Haar 相邻点和差，保留 [A4,D4,D3,D2]。",
        "caveats_en": ["This is a truncated transform; different high-frequency details can produce exactly the same retained vector.", "Haar coefficients depend on alignment and boundary handling. Here the length is a power of two and no padding is needed."],
        "caveats_zh": ["这里使用截断变换；不同的高频细节可能产生完全相同的保留向量。", "Haar 系数依赖对齐与边界处理。本例长度为二的幂，因此无需填充。"],
        "parameters": {"wavelet": "orthonormal Haar", "length": 16, "coefficient_order": "A4,D4,D3,D2,D1", "retained": 8, "boundary": "no padding"},
        "sources": [WAVELET_SOURCE, REGISTRY],
    },
    "histogram": {
        "name": "Value histograms", "zh": "数值直方图", "fn": _hist,
        "labels": ["bin " + str(k + 1) for k in range(7)],
        "explanation_en": "Count observations in seven shared, fixed value intervals and divide by the sample count. The two probability vectors describe how often values occur. Shared edges make the coordinates comparable; all temporal ordering is intentionally removed.",
        "explanation_zh": "在七个共享、固定的数值区间中计数，再除以样本数。两个概率向量描述数值出现的频率。共享边界保证坐标可比较，同时有意舍弃全部时间顺序。",
        "extract_en": "Use identical bin edges for both inputs and normalize counts into bin probabilities.",
        "extract_zh": "对两条序列使用相同分箱边界，将计数归一化为概率。",
        "caveats_en": ["Separate automatic binning can make coordinate-wise comparison invalid; the edges must be shared.", "Values within one bin are indistinguishable, and permuted sequences have identical histograms."],
        "caveats_zh": ["分别自动分箱可能导致坐标不可比，因此必须共享边界。", "同一区间内的数值无法区分，重排序列也具有相同直方图。"],
        "parameters": {"edges": HIST_EDGES.tolist(), "normalization": "probability mass, not density"},
        "sources": [HIST_SOURCE, REGISTRY],
    },
    "trend": {
        "name": "Linear trend features", "zh": "线性趋势特征", "fn": _trend,
        "labels": ["intercept", "slope", "resid SD"],
        "explanation_en": "Fit an ordinary least-squares line to each series on the sample-index axis. Compare the intercept, slope and population standard deviation of residuals. This is EchoTime's three-coordinate trend description; it retains overall direction and unexplained variation while compressing local structure.",
        "explanation_zh": "以样本索引为时间轴，对每条序列拟合普通最小二乘直线，再比较截距、斜率和残差的总体标准差。这是 EchoTime 的三坐标趋势描述，保留总体方向与未解释波动，同时压缩局部结构。",
        "extract_en": "Fit x_t = intercept + slope*t and append the residual population SD.",
        "extract_zh": "拟合 x_t = 截距 + 斜率*t，并加入残差总体标准差。",
        "caveats_en": ["The slope uses sample index, so changing the sampling interval changes its interpretation; physical-time comparisons require consistent units.", "Intercept, slope and residual SD have different scales. Curved trends and different residual patterns can share the same vector."],
        "caveats_zh": ["斜率使用样本索引，改变采样间隔会改变其含义；按物理时间比较需要统一单位。", "截距、斜率与残差标准差尺度不同；弯曲趋势或不同残差结构可能共享同一向量。"],
        "parameters": {"time_axis": "sample index 0..15", "fit": "ordinary least squares", "residual_std_ddof": 0, "features": ["intercept", "slope", "residual_std"]},
        "sources": [LOCAL, GENERATOR],
    },
    "random_projection": {
        "name": "Fixed Gaussian projection", "zh": "固定高斯随机投影", "fn": lambda x: RP @ x,
        "labels": ["proj " + str(k + 1) for k in range(6)],
        "explanation_en": "Multiply both 16-coordinate inputs by the same six-by-16 Gaussian matrix. Each output coordinate is a weighted sum of all observations. The matrix is fixed by an explicit random seed, allowing the comparison to be reproduced without fitting a neural encoder.",
        "explanation_zh": "将两个 16 维输入乘以同一个六乘十六高斯矩阵。每个输出坐标都是全部观测的加权和。矩阵由明确的随机种子固定，因此无需拟合神经编码器也可复现比较。",
        "extract_en": "Use the same fixed matrix with entries N(0,1/6) to project both inputs to six dimensions.",
        "extract_zh": "使用同一个元素分布为 N(0,1/6) 的固定矩阵，把两条输入投影到六维。",
        "caveats_en": ["The six-dimensional example has no asserted distortion guarantee. Johnson-Lindenstrauss guarantees require dimensions and probability assumptions tied to a finite point set.", "Changing the random seed changes the representation; a shared matrix and identical input length/order are essential."],
        "caveats_zh": ["本例六维投影不声称满足给定失真保证。Johnson-Lindenstrauss 保证需要维数、概率与有限样本集等条件。", "改变随机种子会改变表示；必须共享矩阵并保持输入长度及顺序一致。"],
        "parameters": {"seed": 20261029, "matrix_shape": [6, 16], "entry_variance": 1 / 6, "matrix": RP.tolist()},
        "sources": [PROJECTION_SOURCE, GENERATOR],
    },
    "identity": {
        "name": "Identity-resample features", "zh": "恒等重采样特征", "fn": lambda x: np.interp(np.linspace(0, 1, 8), np.linspace(0, 1, len(x)), x),
        "labels": ["grid " + str(k + 1) for k in range(8)],
        "explanation_en": "Linearly interpolate each series onto the same eight-point normalized-time grid and use the samples themselves as coordinates. This explicit identity-resample adapter aligns the representation length without learning a latent model or aligning local events.",
        "explanation_zh": "将每条序列线性插值到同一个八点归一化时间网格，直接把重采样值作为坐标。这个明确的恒等重采样适配器统一表示长度，无需学习潜在模型，也不进行局部事件对齐。",
        "extract_en": "Map each span to [0,1] and linearly interpolate at eight shared grid positions.",
        "extract_zh": "把各自时间跨度映射到 [0,1]，在八个共享位置进行线性插值。",
        "caveats_en": ["Normalizing time spans discards absolute duration unless it is retained separately.", "Interpolation can miss or smooth brief events; it provides no invariance to arbitrary local timing changes."],
        "caveats_zh": ["分别归一化时间跨度会舍弃绝对持续时间，除非另行保留。", "插值可能遗漏或平滑短暂事件，也不提供任意局部时间变化下的不变性。"],
        "parameters": {"n_points": 8, "interpolation": "linear", "grid": "independent normalized spans [0,1]"},
        "sources": [REGISTRY, {"label": "NumPy: one-dimensional linear interpolation", "url": "https://numpy.org/doc/stable/reference/generated/numpy.interp.html"}],
    },
    "generic": {
        "name": "Specified encoder protocol", "zh": "指定编码器协议", "fn": _generic,
        "labels": ["mean", "SD", "ACF1", "slope"],
        "explanation_en": "An embedding comparison first specifies an encoder, then a distance or similarity on its output. This diagram instantiates that protocol with the fixed vector [mean, population SD, adjusted lag-one ACF, linear slope]. It demonstrates the interface with actual numbers; no learned or pretrained representation is used.",
        "explanation_zh": "嵌入比较先指定编码器，再指定输出空间的距离或相似度。本图使用固定的 [均值、总体标准差、调整后一阶自相关、线性斜率] 向量，以真实计算演示接口；未使用学习得到的表示或预训练模型。",
        "extract_en": "Apply the explicitly specified four-statistic encoder identically to both inputs.",
        "extract_zh": "对两条输入使用完全相同、明确指定的四统计量编码器。",
        "caveats_en": ["This name is an interface pattern, not one uniquely defined algorithm; another encoder can produce entirely different neighbors.", "The illustrative coordinates have different units and receive no scaling. No semantic, causal or task-transfer guarantee follows from a small score."],
        "caveats_zh": ["该名称描述接口模式，不对应唯一算法；换用其他编码器会改变近邻关系。", "示例坐标单位不同且未缩放；较小分数不蕴含语义、因果或任务迁移保证。"],
        "parameters": {"encoder": ["mean", "std_ddof0", "adjusted_ACF_lag1", "OLS_slope"], "learned_weights": False, "coordinate_scaling": "none"},
        "sources": [GENERATOR, REGISTRY],
    },
}

SHORT_EXTRACTION = {
    "stats": "Compute mean, population SD, minimum and maximum.",
    "robust_stats": "Compute quartiles, median and unscaled median absolute deviation.",
    "paa": "Replace each four-sample block by its mean.",
    "acf": "Compute centered lag products at lags 1 to 6, with adjusted denominators.",
    "dft": "Take all nine real-FFT magnitudes, including the DC component.",
    "periodogram": "Square rFFT magnitudes and divide by their total across all nine bins.",
    "wavelet": "Compute Haar coefficients and retain the eight coarsest coordinates.",
    "histogram": "Count values in shared bins and divide by the sample count.",
    "trend": "Fit a line; retain intercept, slope and residual population SD.",
    "random_projection": "Multiply both inputs by the same fixed Gaussian matrix.",
    "identity": "Interpolate both inputs onto the same eight-point normalized-time grid.",
    "generic": "Apply the fixed mean, SD, lag-one ACF and slope encoder.",
}


def _panel(a, b=None, *, title, labels=None, kind="bars", marker=None, a_label="x features", b_label="y features"):
    p = {"kind": kind, "title": title, "a": _list(a), "a_label": a_label}
    if b is not None:
        p.update(b=_list(b), b_label=b_label)
    if labels is not None:
        p["labels"] = list(labels)
    if marker is not None:
        p["marker"] = int(marker)
    return p


def _frame(phase, caption, panel, value=None, value_label=None, highlight=None):
    f = {"phase": phase, "caption": caption, "panel": panel}
    if value is not None:
        f["value"] = float(value)
        f["value_label"] = value_label or "readout"
    if highlight is not None:
        f["input_highlight"] = [int(i) for i in highlight]
    return f


def _extraction_frames(key, x, y, spec):
    frames = []
    n = len(x)
    if key in ("stats", "robust_stats", "histogram"):
        for k in [4, 6, 8, 10, 12, 16]:
            frames.append(_frame(0, f"Summarize the first {k} observations using the stated descriptor.",
                _panel(spec["fn"](x[:k]), spec["fn"](y[:k]), title=f"Descriptor from first {k} samples", labels=spec["labels"]), highlight=range(k)))
    elif key == "paa":
        for k in [1, 2, 3, 4, 3, 4]:
            frames.append(_frame(0, f"Average the four samples inside block {k}.",
                _panel(_paa(x)[:k], _paa(y)[:k], title="PAA: one mean per consecutive block", labels=spec["labels"][:k], marker=k-1), highlight=range((k-1)*4, k*4)))
    elif key == "acf":
        for lag in range(1, 7):
            zx, zy = x - x.mean(), y - y.mean()
            frames.append(_frame(0, f"Lag {lag}: sum centered products, then divide by (n-lag) times variance.",
                _panel(zx[:-lag] * zx[lag:], zy[:-lag] * zy[lag:], title=f"Lag-{lag} centered products", kind="lines", a_label="x products", b_label="y products"),
                _acf(x)[lag-1], f"x ACF({lag})", highlight=[0, lag]))
    elif key in ("dft", "periodogram"):
        for k, part in [(0,"cos"),(1,"cos"),(1,"sin"),(2,"cos"),(2,"sin"),(3,"cos")]:
            angle = 2 * np.pi * k * np.arange(n) / n
            weights = np.cos(angle) if part == "cos" else -np.sin(angle)
            frames.append(_frame(0, f"Bin {k}: sum {part}-weighted samples to obtain a Fourier component.",
                _panel(x*weights, y*weights, title=f"Frequency k={k}: {part}-weighted samples", kind="lines", a_label="x weighted", b_label="y weighted"),
                np.sum(x*weights), f"x {part} component"))
    elif key in ("wavelet", "haar_full"):
        ax, ay = x.copy(), y.copy()
        for level in range(1, 5):
            dx, dy = (ax[::2]-ax[1::2])/np.sqrt(2), (ay[::2]-ay[1::2])/np.sqrt(2)
            ax, ay = (ax[::2]+ax[1::2])/np.sqrt(2), (ay[::2]+ay[1::2])/np.sqrt(2)
            frames.append(_frame(0, f"Haar level {level}: pair sums form the next approximation.",
                _panel(ax, ay, title=f"Level {level} approximation coefficients", a_label="x approximation", b_label="y approximation")))
            if level in (1, 2):
                frames.append(_frame(0, f"Haar level {level}: pair differences record detail at this scale.",
                    _panel(dx, dy, title=f"Level {level} detail coefficients", a_label="x detail", b_label="y detail")))
    elif key == "trend":
        t = np.arange(n)
        for k in [4,6,8,10,12,16]:
            tx, ty = _trend(x[:k]), _trend(y[:k])
            frames.append(_frame(0, f"Fit a straight line to the first {k} samples; retain residual variation.",
                _panel(tx[0]+tx[1]*t[:k], ty[0]+ty[1]*t[:k], title=f"Least-squares trends on first {k} samples", kind="lines", a_label="x fitted", b_label="y fitted"), highlight=range(k)))
    elif key == "identity":
        ax, ay = spec["fn"](x), spec["fn"](y)
        for k in [2,3,4,5,6,8]:
            p = _panel(ax[:k], ay[:k], title="Samples interpolated on the shared time grid", kind="lines", a_label="x resampled", b_label="y resampled")
            p["x"] = np.linspace(0, 1, 8)[:k].tolist()
            frames.append(_frame(0, f"Evaluate the first {k} positions of the eight-point normalized-time grid.", p))
    elif key == "random_projection":
        for k in range(6):
            frames.append(_frame(0, f"Projection coordinate {k+1}: sum samples times one shared matrix row.",
                _panel(RP[k]*x, RP[k]*y, title=f"Weighted samples for projection {k+1}", kind="lines", a_label="x weighted", b_label="y weighted"),
                RP[k] @ x, f"x projection {k+1}"))
    else:
        for k in range(4):
            frames.append(_frame(0, "The same explicit encoder and comparison rule are applied to both inputs.",
                {"kind":"pipeline","title":"Specified encoder protocol; no learned weights","labels":["Samples","Fixed features","Vector","Compare"],"active":k,
                 "a": _list(spec["fn"](x)), "b": _list(spec["fn"](y))}))
        for k in (2,4):
            frames.append(_frame(0, "The illustrative encoder exposes its computed coordinates.",
                _panel(spec["fn"](x)[:k], spec["fn"](y)[:k], title="Actual output of the specified encoder", labels=spec["labels"][:k])))
    return frames


def _comparison_frames(a, b, labels, mode, *, prefix="Feature"):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if mode == "euclidean":
        c = (a-b)**2
        finish = lambda s: np.sqrt(max(float(s), 0))
        title, step_caption, label = "Squared coordinate differences", "Accumulate squared differences, then take the square root.", "partial distance"
    elif mode in ("cosine", "one_minus_cosine"):
        c = a*b/(np.linalg.norm(a)*np.linalg.norm(b))
        finish = (lambda s: float(s)) if mode == "cosine" else (lambda s: 1-float(s))
        title, step_caption, label = "Dot-product terms / fixed full-vector norms", "Sum normalized dot-product contributions from the displayed coordinates.", "partial dot sum"
    else:
        raise ValueError(mode)
    result = float(finish(c.sum()))
    frames = []
    for k in np.linspace(1, len(a), 6).astype(int):
        frames.append(_frame(1, f"Expose {k} of {len(a)} coordinates; each has the same meaning in x and y.",
            _panel(a[:k], b[:k], title=f"{prefix} vectors", labels=labels[:k], marker=k-1)))
    for k in np.linspace(1, len(a), 6).astype(int):
        partial = np.sqrt(c[:k].sum()) if mode == "euclidean" else c[:k].sum()
        frames.append(_frame(2, step_caption,
            _panel(c[:k], title=title, labels=labels[:k], marker=k-1, a_label="contributions"), partial, label))
    for k in [0, max(0,len(a)//3), max(0,len(a)*2//3), len(a)-1]:
        frames.append(_frame(3,
            "Use one minus the completed cosine score." if mode == "one_minus_cosine" else "Read the completed comparison using every retained coordinate.",
            _panel(c, title=title, labels=labels, marker=k, a_label="contributions"), result, "final similarity" if mode == "cosine" else "final distance"))
    return frames, result


def _feature_example(method_id, key, mode="euclidean", *, family="feature-based", title=None, definition="reference"):
    x, y = _inputs()
    spec = deepcopy(ENCODERS[key])
    a, b = spec["fn"](x), spec["fn"](y)
    label = "similarity" if mode == "cosine" else "distance"
    comparison_en = "Take the Euclidean norm of the coordinate differences." if mode == "euclidean" else ("Normalize by both vector lengths and sum coordinate products to obtain cosine similarity." if mode == "cosine" else "Compute cosine similarity, then subtract it from one.")
    comparison_zh = "对坐标差计算欧氏范数。" if mode == "euclidean" else ("用两个向量的长度归一化坐标乘积之和，得到余弦相似度。" if mode == "cosine" else "计算余弦相似度，再用一减去该分数。")
    formula = "d(x,y) = sqrt(sum_j (phi_j(x)-phi_j(y))^2)" if mode == "euclidean" else ("s(x,y) = dot(phi(x),phi(y)) / (norm(phi(x))*norm(phi(y)))" if mode == "cosine" else "d(x,y) = 1 - dot(phi(x),phi(y)) / (norm(phi(x))*norm(phi(y)))")
    tail_en = " Cosine compares vector direction and is defined here for nonzero feature vectors." if mode != "euclidean" else " Euclidean distance retains differences in both vector scale and coordinates."
    tail_zh = " 余弦比较向量方向，本例特征向量均非零。" if mode != "euclidean" else " 欧氏距离同时保留向量尺度与坐标差异。"
    frames, result = _comparison_frames(a,b,spec["labels"],mode)
    frames = _extraction_frames(key,x,y,spec) + frames
    c_en, c_zh = list(spec["caveats_en"]), list(spec["caveats_zh"])
    if mode != "euclidean":
        c_en.append("Cosine ignores positive rescaling of the entire feature vector; 1-cosine is generally not a metric, and zero vectors require an explicit policy.")
        c_zh.append("余弦忽略整个特征向量的正比例缩放；1-cosine 通常不满足度量公理，零向量还需明确处理规则。")
    else:
        c_en.append("A metric on these feature vectors can be only a pseudometric on the original series when the representation loses information.")
        c_zh.append("当表示损失信息时，特征空间中的度量在原序列空间上可能只是伪度量。")
    e = {
        "id":method_id, "title":title or (spec["name"] + " " + label), "family":family,
        "definition":definition, "intro_en":spec["explanation_en"] + tail_en, "intro_zh":spec["explanation_zh"] + tail_zh,
        "steps_en":[spec["extract_en"], "Collect the computed coordinates in the same fixed order for both inputs.", comparison_en, "Interpret the score in this representation, accounting for the information it discards."],
        "steps_zh":[spec["extract_zh"],"把计算得到的坐标按同一个固定顺序组成两个向量。",comparison_zh,"结合表示所舍弃的信息，在该表示空间中解释分数。"],
        "animation_steps_en":[SHORT_EXTRACTION[key], "Collect matching coordinates in the same vector order.",
            "Take the Euclidean norm of coordinate differences." if mode=="euclidean" else "Normalize vector products to obtain cosine similarity.",
            "Subtract the completed cosine score from one." if mode=="one_minus_cosine" else "Read the score in this feature space, with its stated information loss."],
        "formula":formula,"caveats_en":c_en,"caveats_zh":c_zh,"sources":spec["sources"]+[GENERATOR],
        "x":_list(x),"y":_list(y),"input_label":"Deterministic synthetic teaching signals, 16 samples each",
        "parameters":dict(spec["parameters"],comparison=mode),
        "result":{"label":label,"value":result,"detail":"Computed from the explicitly defined illustrative encoder; no learned weights."},
        "frames":frames,
    }
    return e


def _full_haar_example():
    spec = deepcopy(ENCODERS["wavelet"])
    spec.update(fn=_haar, labels=["A4","D4","D3a","D3b"]+["D2"+str(k) for k in range(4)]+["D1"+str(k) for k in range(8)])
    x,y=_inputs(); a,b=_haar(x),_haar(y)
    frames,result=_comparison_frames(a,b,spec["labels"],"euclidean",prefix="Full orthonormal Haar")
    raw=float(np.linalg.norm(x-y))
    if not np.isclose(result,raw,atol=1e-12):
        raise AssertionError("Full orthonormal Haar must preserve the Euclidean norm.")
    e=_feature_example("dwt_distance","wavelet",title="Full Haar coefficient distance")
    e.update(intro_en="Apply the complete orthonormal Haar transform and compare all coefficients. The animation separates pair averages and details across four levels. With every coefficient retained and no boundary padding, the resulting Euclidean distance equals the raw-sample Euclidean distance by norm preservation.",
        intro_zh="进行完整正交 Haar 变换并比较全部系数。动图展示四级相邻点和差分解。保留所有系数且不填充边界时，由范数保持性质，系数的欧氏距离等于原始样本的欧氏距离。",
        steps_en=["Use equal-length inputs of length 16, so Haar pairs need no padding.","Recursively form orthonormal pair sums and differences at four levels.","Collect all 16 coefficients in [A4,D4,D3,D2,D1] order.","Take their Euclidean distance and verify equality with raw Euclidean distance."],
        steps_zh=["使用长度均为 16 的输入，因此相邻点分组无需填充。","递归进行四级正交归一化的相邻点和差分解。","按 [A4,D4,D3,D2,D1] 顺序保留全部 16 个系数。","计算系数欧氏距离，并核对其等于原始欧氏距离。"],
        formula="d = ||W_Haar x - W_Haar y||_2 = ||x-y||_2 (complete orthonormal transform)",
        caveats_en=["Using all orthonormal coefficients does not by itself create a new Euclidean notion of similarity.","Truncating coefficients, weighting scales or changing boundary conventions changes this equivalence."],
        caveats_zh=["保留全部正交系数本身不会产生新的欧氏相似性定义。","截断系数、对尺度加权或改变边界约定都会改变上述等价关系。"],
        parameters={"wavelet":"orthonormal Haar","length":16,"retained":16,"coefficient_order":"A4,D4,D3,D2,D1","padding":False},
        result={"label":"distance","value":result,"detail":f"Full-coefficient L2; raw Euclidean distance = {raw:.12g}."},
        frames=_extraction_frames("haar_full",x,y,spec)+frames,
        checks={"api":"orthonormal Haar identity","expected":raw,"observed":result,"tolerance":1e-12})
    return e


def _ordinal_distributions(x, order=3):
    perms=list(permutations(range(order)))
    ids={p:i for i,p in enumerate(perms)}
    patterns=[ids[tuple(np.argsort(x[i:i+order],kind="stable"))] for i in range(len(x)-order+1)]
    counts=np.bincount(patterns,minlength=len(perms)).astype(float)
    return counts/counts.sum(),patterns,["".join(map(str,p)) for p in perms]


def _ordinal_example(method_id):
    x,y=_inputs(); p,ix,labels=_ordinal_distributions(x); q,iy,_=_ordinal_distributions(y)
    entropy=lambda a: float(-np.sum(a[a>0]*np.log(a[a>0]))/np.log(factorial(3)))
    is_js=method_id=="ordinal_pattern_js_distance"
    hp,hq=entropy(p),entropy(q)
    if is_js:
        m=(p+q)/2
        c=np.zeros_like(p)
        for a in (p,q):
            mask=a>0;c[mask]+=.5*a[mask]*np.log(a[mask]/m[mask])
        value=float(np.sqrt(c.sum()))
    else:
        c=np.zeros_like(p);d=np.zeros_like(q)
        c[p>0]=-p[p>0]*np.log(p[p>0])/np.log(6)
        d[q>0]=-q[q>0]*np.log(q[q>0])/np.log(6)
        value=abs(hp-hq)
    frames=[]
    for k in [1,3,5,8,11,14]:
        px=np.bincount(ix[:k],minlength=6)/k; py=np.bincount(iy[:k],minlength=6)/k
        frames.append(_frame(0,f"Rank each length-three window; {k} windows counted so far.",
            _panel(px,py,title="Observed ordinal-pattern proportions",labels=labels,marker=ix[k-1],a_label="x pattern mass",b_label="y pattern mass"),highlight=range(k-1,k+2)))
    for k in range(1,7):
        frames.append(_frame(1,"Keep the full six-pattern distribution, including patterns with zero count.",
            _panel(p[:k],q[:k],title="Final ordinal-pattern distributions",labels=labels[:k],marker=k-1)))
    for k in range(1,7):
        if is_js:
            panel=_panel(c[:k],title="Per-pattern Jensen-Shannon contributions",labels=labels[:k],marker=k-1,a_label="JS contributions")
            readout=np.sqrt(max(c[:k].sum(),0));readlabel="partial JS distance"
        else:
            panel=_panel(c[:k],d[:k],title="Per-pattern normalized entropy contributions",labels=labels[:k],marker=k-1,a_label="x entropy terms",b_label="y entropy terms")
            readout=c[:k].sum();readlabel="partial H(x)"
        frames.append(_frame(2,"Accumulate the stated distribution functional; zero-mass terms contribute zero.",panel,readout,readlabel))
    for k in range(4):
        panel=_panel(c,title="JS terms; take square root of their sum",labels=labels,marker=k,a_label="JS contributions") if is_js else _panel([hp,hq],title="Normalized entropies; compare their absolute difference",labels=["H(x)","H(y)"],marker=k%2,a_label="entropy")
        frames.append(_frame(3,"Compare full pattern distributions." if is_js else "Compare only two scalar entropies; pattern identities have been compressed.",panel,value,"final distance"))
    return {"id":method_id,"title":"Ordinal-pattern JS distance" if is_js else "Permutation-entropy distance","family":"feature-based","definition":"echotime" if is_js else "reference",
        "intro_en":("Turn every three-observation window into its ordering pattern, then compare the six-pattern probability vectors with square-root Jensen-Shannon divergence. This retains which patterns are frequent and follows EchoTime's natural-log definition." if is_js else "Turn length-three windows into ordering patterns and compute each distribution's normalized Shannon entropy. Compare the two scalar entropies with an absolute difference. The score measures equality of this particular summary, so distinct pattern distributions can still have zero distance."),
        "intro_zh":("把每个三点窗口转换成排序模式，再以 Jensen-Shannon 散度的平方根比较六种模式的概率向量。它保留具体哪些模式更常出现，并遵循 EchoTime 使用自然对数的定义。" if is_js else "把三点窗口转换成排序模式，分别计算模式分布的归一化 Shannon 熵，再取两标量之差的绝对值。该分数比较这一特定摘要，因而不同模式分布仍可能得到零距离。"),
        "steps_en":["Form overlapping windows with order 3 and delay 1.","Stably rank each window and count all six possible permutations.","Compute square-root Jensen-Shannon divergence with natural logarithms." if is_js else "Compute H=-sum(p log p)/log(6) for each distribution.","Read a distribution distance and check the chosen order/delay." if is_js else "Take |H(x)-H(y)| and remember that entropy discards pattern identities."],
        "steps_zh":["使用阶数 3、延迟 1 构造重叠窗口。","稳定排序各窗口，并统计全部六种排列。","使用自然对数计算 Jensen-Shannon 散度的平方根。" if is_js else "对各分布计算 H=-sum(p log p)/log(6)。","读取分布距离，并检查所选阶数与延迟。" if is_js else "计算 |H(x)-H(y)|，同时注意熵舍弃具体模式身份。"],
        "formula":"d = sqrt((KL(p||m)+KL(q||m))/2), m=(p+q)/2" if is_js else "d = |H(p)-H(q)|; H(p)=-sum(p log p)/log(3!)",
        "caveats_en":["Order 3, delay 1 and stable tie-breaking by earlier position are explicit choices; frequent ties can change the interpretation.","Short sequences provide sparse pattern counts; overlapping windows are not independent samples.","Pattern frequencies discard when patterns occur." if is_js else "Equal entropy does not imply equal ordinal distributions or similar dynamics."],
        "caveats_zh":["阶数 3、延迟 1，以及按较早位置优先的稳定并列处理都是明确选择；大量并列值会改变解释。","短序列的模式统计稀疏，重叠窗口也不是独立样本。","模式频率舍弃模式出现的具体时刻。" if is_js else "相同的熵不意味着相同的模式分布或动力学。"],
        "sources":[PE_SOURCE,JS_SOURCE if is_js else GENERATOR,LOCAL],"x":_list(x),"y":_list(y),
        "parameters":{"order":3,"delay":1,"tie_policy":"stable by index","log_base":"e","entropy_normalized":not is_js},
        "result":{"label":"distance","value":value,"detail":"Natural-log JS distance" if is_js else f"Normalized entropies H(x)={hp:.8g}, H(y)={hq:.8g}"},"frames":frames}


def _sax_example(method_id):
    x,y=_inputs();zx,zy=_z(x),_z(y);px,py=_paa(zx),_paa(zy)
    bp=norm.ppf([.25,.5,.75]);sx=np.digitize(px,bp);sy=np.digitize(py,bp)
    labels=[f"{i+1}: {chr(97+a)}/{chr(97+b)}" for i,(a,b) in enumerate(zip(sx,sy))]
    hamming=method_id=="sax_hamming_distance"
    if hamming:
        c=(sx!=sy).astype(float)/4;value=float(c.sum())
    else:
        gap=lambda a,b: 0. if abs(int(a)-int(b))<=1 else float(bp[max(a,b)-1]-bp[min(a,b)])
        gaps=np.array([gap(a,b) for a,b in zip(sx,sy)]);c=4*gaps**2;value=float(np.sqrt(c.sum()))
    frames=[]
    for k in [4,8,12,16]:
        frames.append(_frame(0,"Standardize each full sequence to mean zero and population variance one.",
            _panel(zx[:k],zy[:k],title="Z-normalized sequences",kind="lines",a_label="z(x)",b_label="z(y)"),highlight=range(k)))
    for k in range(1,5):
        frames.append(_frame(1,f"Average block {k}, then locate its mean among Gaussian breakpoints.",
            _panel(px[:k],py[:k],title="PAA values before symbolization",labels=[f"block {j+1}" for j in range(k)],marker=k-1),highlight=range((k-1)*4,k*4)))
    for k in range(1,5):
        frames.append(_frame(1,"Encode bins by a=0, b=1, c=2, d=3; their numeric codes are not distances.",
            _panel(sx[:k],sy[:k],title="SAX symbol codes (not numeric distances)",labels=labels[:k],marker=k-1,a_label="x symbols",b_label="y symbols")))
    for k in range(1,5):
        frames.append(_frame(2,"Count unequal symbols with equal weight." if hamming else "Use the gap between symbol intervals; equal or adjacent bins contribute zero.",
            _panel(c[:k],title="Mismatch contributions / word length" if hamming else "Squared interval-gap terms times n/w",labels=labels[:k],marker=k-1,a_label="contributions"),
            c[:k].sum() if hamming else np.sqrt(c[:k].sum()),"partial dissimilarity"))
    for k in range(4):
        frames.append(_frame(3,"Hamming counts every symbol mismatch equally." if hamming else "Here all symbols are adjacent: MINDIST is zero although the waveforms differ.",
            _panel(c,title="Final SAX comparison contributions",labels=labels,marker=k,a_label="contributions"),value,"final dissimilarity"))
    return {"id":method_id,"title":"SAX Hamming distance" if hamming else "SAX MINDIST lower bound","family":"feature-based","definition":"reference",
        "intro_en":("Convert each standardized series to a four-symbol SAX word, then count the fraction of positions with different symbols. This treats every mismatch equally, including adjacent bins; it is a distance between words, with information lost during aggregation and quantization." if hamming else "Compare SAX words using the minimum gap between their symbol intervals, sum squared gaps and multiply by the PAA length factor. Equal or adjacent symbols contribute zero. In this example all paired symbols are adjacent, demonstrating why a valid lower bound can be zero for distinct series."),
        "intro_zh":("把每条标准化序列转换为四符号 SAX 单词，再统计对应位置符号不同的比例。所有不匹配均等计数，包括相邻区间；它比较符号单词，聚合和量化已经损失信息。" if hamming else "以 SAX 符号区间之间的最小间隔比较两个单词，累加间隔平方后加入 PAA 长度系数。相同或相邻符号贡献为零。本例各对应符号都相邻，展示了有效下界为何可对不同序列返回零。"),
        "steps_en":["Z-normalize each complete series and use four equal PAA blocks.","Quantize each mean with shared standard-normal quartile breakpoints.","Count mismatching symbols." if hamming else "Look up the minimum gap between the two symbol intervals.","Divide the mismatch count by four." if hamming else "Take sqrt(n/w)*sqrt(sum(gap^2)); this is a lower-bound calculation."],
        "steps_zh":["对各完整序列做 z 标准化，并计算四个等长 PAA 区间。","使用共享标准正态四分位断点量化各区间均值。","统计符号不匹配数。" if hamming else "查找两个符号区间之间的最小间隔。","将不匹配数除以四。" if hamming else "计算 sqrt(n/w)*sqrt(sum(gap^2))，得到下界。"],
        "formula":"d = sum_i [SAX_i(x) != SAX_i(y)] / 4" if hamming else "MINDIST = sqrt(16/4)*sqrt(sum_i interval_gap(SAX_i(x),SAX_i(y))^2)",
        "caveats_en":["Gaussian breakpoints are a coding convention; they do not make arbitrary observed signals normally distributed.","Hamming on words does not have the SAX Euclidean lower-bound interpretation." if hamming else "The Euclidean lower-bound interpretation requires the same normalized length, partitions and ordered breakpoints; lower-bounding does not imply metric axioms.","Both PAA aggregation and quantization can map distinct signals to the same code."],
        "caveats_zh":["高斯断点是一种编码约定，不会使任意观测信号变成正态分布。","单词上的 Hamming 距离不具有 SAX 欧氏下界的含义。" if hamming else "欧氏下界解释要求相同的标准化长度、分段和有序断点；具有下界性质不等于满足度量公理。","PAA 聚合和量化都可能把不同信号映射为相同代码。"],
        "sources":[SAX_SOURCE,GENERATOR],"x":_list(x),"y":_list(y),
        "parameters":{"length":16,"word_length":4,"alphabet_size":4,"breakpoints":bp.tolist(),"z_normalization_ddof":0,"x_word":"".join(chr(97+a) for a in sx),"y_word":"".join(chr(97+a) for a in sy)},
        "result":{"label":"word distance" if hamming else "lower bound","value":value,"detail":"Normalized symbol mismatch rate" if hamming else f"Compare with actual z-normalized Euclidean distance {np.linalg.norm(zx-zy):.8g}."},"frames":frames}


def _bop(x):
    bp=norm.ppf([.25,.5,.75]);words=[];events=[]
    previous=None
    for start in range(len(x)-8+1):
        word="".join(chr(97+i) for i in np.digitize(_paa(_z(x[start:start+8]),4),bp))
        accepted=word!=previous
        if accepted:words.append(word)
        events.append((start,word,accepted))
        previous=word
    return words,events


def _bop_example(method_id):
    x,y=_inputs();wx,ex=_bop(x);wy,ey=_bop(y);vocab=sorted(set(wx+wy))
    a=np.array([wx.count(w) for w in vocab],dtype=float);b=np.array([wy.count(w) for w in vocab],dtype=float)
    mode="cosine" if method_id.endswith("similarity") else "one_minus_cosine"
    frames=[]
    for k in [0,1,3,5,7,8]:
        xword,yword=ex[k][1],ey[k][1]
        frames.append(_frame(0,f"Window {k+1}: SAX words {xword} / {yword}; skip consecutive duplicates.",
            _panel(_z(x[k:k+8]),_z(y[k:k+8]),title="Locally normalized length-eight windows",kind="lines",a_label="x window",b_label="y window"),highlight=range(k,k+8)))
    comp,value=_comparison_frames(a,b,vocab,mode,prefix="SAX-word count")
    frames+=comp
    similarity=mode=="cosine"
    return {"id":method_id,"title":"Bag-of-patterns cosine similarity" if similarity else "Bag-of-patterns cosine distance","family":"feature-based","definition":"reference",
        "intro_en":"Slide an eight-sample window, normalize each window, encode it as a four-letter SAX word and count the words. Consecutive duplicate words are suppressed in this example. The resulting bag is compared by cosine, so local motifs contribute through their frequencies while their global order is discarded.",
        "intro_zh":"滑动八点窗口，对每个窗口单独标准化，编码为四字母 SAX 单词并计数。本例抑制连续重复单词，再用余弦比较词袋。局部模式通过出现频率参与比较，其全局顺序被舍弃。",
        "steps_en":["Slide a length-eight window, normalize it, then encode four PAA means with the shared SAX alphabet.","Suppress consecutive duplicate words and count both series in one shared vocabulary.","Accumulate matching word-count products divided by both vector norms.","Read cosine similarity between count vectors." if similarity else "Subtract the completed cosine similarity from one."],
        "steps_zh":["滑动八点窗口并标准化，再用共享 SAX 字母表编码四个 PAA 均值。","抑制连续重复词，在一个共享词表中对两条序列计数。","累加对应词频的乘积，并除以两个向量的范数乘积。","读取词频向量的余弦相似度。" if similarity else "用一减去完整的余弦相似度。"],
        "formula":"s = cosine(counts(SAX_windows(x)), counts(SAX_windows(y)))" if similarity else "d = 1 - cosine(counts(SAX_windows(x)), counts(SAX_windows(y)))",
        "caveats_en":["Window length, word length, alphabet and numerosity reduction define the comparison; the original BoP representation does not mandate this exact cosine adapter.","Global motif order and absolute window level/scale are discarded; a similar bag need not imply aligned events.","A zero count vector needs an explicit policy. This example has nonempty bags."],
        "caveats_zh":["窗口长度、词长、字母表与重复抑制规则共同定义比较；原 BoP 表示并未要求必须使用本例余弦适配器。","全局模式顺序和窗口的绝对水平、尺度被舍弃；词袋相似并不意味着事件对齐。","零计数向量需要明确处理规则，本例两个词袋均非空。"],
        "sources":[BOP_SOURCE,SAX_SOURCE,GENERATOR],"x":_list(x),"y":_list(y),
        "parameters":{"window":8,"stride":1,"word_length":4,"alphabet_size":4,"local_z_normalization":True,"numerosity_reduction":"consecutive exact duplicate words","vocabulary":vocab,"comparison":mode},
        "result":{"label":"similarity" if similarity else "distance","value":value,"detail":"Explicit BoP + cosine composition; shared vocabulary."},"frames":frames}


def _ar_fit(x):
    z=np.asarray(x)-np.mean(x)
    design=np.column_stack([z[1:-1],z[:-2]])
    target=z[2:]
    beta=np.linalg.lstsq(design,target,rcond=None)[0]
    residual=target-design@beta
    return beta, float(np.mean(residual**2)), design, target


def _ar_design_frames(x,y):
    _,_,ax,_=_ar_fit(x);_,_,ay,_=_ar_fit(y)
    frames=[]
    for k in [2,4,6,8,11,14]:
        z=np.column_stack([ax[:k],ay[:k]])
        frames.append(_frame(0,f"Build {k} lagged rows: x lags in the left columns, y lags in the right.",
            {"kind":"matrix","title":"AR(2) design: [x lag1, x lag2 | y lag1, y lag2]","z":z.tolist(),"row_label":"prediction row","col_label":"lagged predictors","cursor":[k-1,0]}))
    return frames


def _ar_example(method_id):
    x,y=_inputs();bx,vx,ax,tx=_ar_fit(x);by,vy,ay,ty=_ar_fit(y)
    roots_x=np.roots(np.r_[1,-bx]);roots_y=np.roots(np.r_[1,-by])
    stable=bool(np.all(np.abs(roots_x)<1) and np.all(np.abs(roots_y)<1))
    if not stable:raise AssertionError("The illustrated AR spectral fits must be stable.")
    omega=np.linspace(0,np.pi,17)
    response=lambda beta: 1-beta[0]*np.exp(-1j*omega)-beta[1]*np.exp(-2j*omega)
    sx=vx/np.abs(response(bx))**2;sy=vy/np.abs(response(by))**2
    parameters={"order":2,"demean":"separately using full series mean","intercept":False,"estimator":"conditional OLS, no regularization","residual_variance":"mean squared fitted residual","beta_x":bx.tolist(),"beta_y":by.tolist(),"ar_companion_root_radii_x":np.abs(roots_x).tolist(),"ar_companion_root_radii_y":np.abs(roots_y).tolist()}
    base={"id":method_id,"family":"model-based","definition":"protocol","x":_list(x),"y":_list(y),"parameters":parameters,"sources":[AR_SOURCE,GENERATOR],
        "caveats_en":["The example fixes order two and demeans each series separately. Changing order, centering or estimator changes the fitted object.","Sixteen samples suffice only for an illustration, not a reliable claim about the generating process."],
        "caveats_zh":["本例固定二阶，并分别去均值；改变阶数、中心化或估计器都会改变拟合对象。","十六个样本仅用于解释过程，不能据此可靠推断生成机制。"]}
    if method_id=="ar_distance":
        frames,value=_comparison_frames(bx,by,["AR lag1","AR lag2"],"euclidean",prefix="OLS autoregressive coefficient")
        base.update(title="Autoregressive-coefficient distance",
            intro_en="Fit a separately centered AR(2) model by conditional least squares to each short input, then compare the two lag coefficients. The distance describes this specified fitted linear recurrence. Mean level and innovation variance are excluded from the coefficient vector in this example.",
            intro_zh="分别对两条短序列去均值，用条件最小二乘拟合 AR(2)，再比较两个滞后系数。距离描述这一明确指定的线性递推拟合；本例系数向量不包含均值水平和创新方差。",
            steps_en=["Remove each series' sample mean and construct two lagged predictors.","Fit the same AR(2) equation by ordinary least squares for each input.","Compare the corresponding lag-one and lag-two coefficients.","Take the Euclidean norm of the coefficient difference."],
            steps_zh=["去除各序列样本均值，构造两个滞后预测量。","分别用普通最小二乘拟合相同形式的 AR(2) 方程。","比较对应的一阶和二阶滞后系数。","计算系数差的欧氏范数。"],
            formula="z_t = phi_1*z_(t-1)+phi_2*z_(t-2)+e_t; d=||phi_x-phi_y||_2",
            result={"label":"distance","value":value,"detail":"Distance between separately demeaned conditional-OLS AR(2) coefficients."},
            frames=_ar_design_frames(x,y)+frames)
        base["caveats_en"].append("Coefficient similarity does not establish equal innovation noise, nonlinear dependence or causal dynamics.")
        base["caveats_zh"].append("系数相似不能证明创新噪声、非线性依赖或因果动力学相同。")
    elif method_id=="ar_spectrum_distance":
        a,b=np.log(sx),np.log(sy);labels=[str(k) for k in range(17)]
        frames,value=_comparison_frames(a,b,labels,"euclidean",prefix="AR-implied natural-log spectrum")
        base.update(title="AR log-spectrum distance",
            intro_en="Fit the same centered AR(2) model to each input and evaluate its implied spectrum on 17 shared frequencies. The animation compares natural-log spectra with Euclidean distance. The two final fits are stable; their fitted residual variances are included, so both spectral shape and power level affect the score.",
            intro_zh="对两条输入拟合相同的中心化 AR(2) 模型，并在 17 个共享频点上计算模型隐含谱。动图以欧氏距离比较自然对数谱。两个最终拟合均稳定，且纳入拟合残差方差，因此谱形状和功率水平都会影响分数。",
            steps_en=["Demean each input, build two lags and fit conditional-OLS AR(2) models.","Check stability and evaluate sigma^2 / |1-phi_1 exp(-iw)-phi_2 exp(-2iw)|^2.","Take natural logs on the same 17-point frequency grid.","Take the Euclidean norm of the log-spectrum difference."],
            steps_zh=["分别去均值，构造两个滞后量并拟合条件最小二乘 AR(2)。","检查稳定性，计算 sigma^2 / |1-phi_1 exp(-iw)-phi_2 exp(-2iw)|^2。","在相同的 17 点频率网格上取自然对数。","计算对数谱差的欧氏范数。"],
            formula="S(w)=sigma^2/|1-sum_(j=1)^2 phi_j exp(-ijw)|^2; d=||log S_x-log S_y||_2",
            result={"label":"distance","value":value,"detail":"Unweighted L2 over 17 natural-log spectral coordinates; no integration weighting."},
            frames=_ar_design_frames(x,y)+frames)
        base["parameters"].update(omega=omega.tolist(),spectrum_convention="sigma2/abs(AR polynomial)^2; common 1/(2pi) omitted",log_base="e")
        base["sources"].append(AR_SPECTRUM_SOURCE)
        base["caveats_en"].append("The spectrum is an AR model implication; stability and stationarity assumptions require scrutiny. Grid density and log conventions change the numeric distance.")
        base["caveats_zh"].append("该谱是 AR 模型的推论，需要检查稳定性和平稳性假设。网格密度及对数约定会改变数值距离。")
    else:
        pred_y=ay@bx;pred_x=ax@by
        ex=(ty-pred_y)**2;ey=(tx-pred_x)**2
        mx,my=float(ex.mean()),float(ey.mean());value=.5*(mx+my)
        frames=_ar_design_frames(x,y)
        for k in [5,9,14]:
            frames.append(_frame(1,"Use the model fitted on x to predict centered y one step ahead.",
                _panel(ty[:k],pred_y[:k],title="x model applied to y: observed versus prediction",kind="lines",a_label="centered y",b_label="prediction from x model")))
        for k in [5,9,14]:
            frames.append(_frame(1,"Reverse the roles: the y model predicts centered x one step ahead.",
                _panel(tx[:k],pred_x[:k],title="y model applied to x: observed versus prediction",kind="lines",a_label="centered x",b_label="prediction from y model")))
        for k in [2,4,6,9,12,14]:
            frames.append(_frame(2,"Accumulate squared cross-prediction errors using the full target count.",
                _panel(ex[:k],ey[:k],title="Directional squared prediction errors",a_label="x model -> y",b_label="y model -> x"),
                .5*(ex[:k].sum()+ey[:k].sum())/len(ex),"partial symmetric error"))
        for k in range(4):
            frames.append(_frame(3,"Average the two completed directional mean-squared errors.",
                _panel([mx,my],title="Two directional MSEs",labels=["x -> y","y -> x"],marker=k%2,a_label="cross MSE"),value,"symmetric error"))
        base.update(title="Symmetric AR cross-prediction error",
            intro_en="Fit centered AR(2) models, apply the x model to y and the y model to x, then average their one-step mean-squared errors. This measures compatibility under a specified predictive model and centering convention. Even a self-comparison can remain positive because fitted innovations are not zero.",
            intro_zh="拟合中心化 AR(2) 模型，用 x 的模型预测 y，再用 y 的模型预测 x，最后平均两个一步预测均方误差。它度量指定预测模型和中心化约定下的兼容性；即使自比较，也可能因拟合创新不为零而得到正值。",
            steps_en=["Fit one centered conditional-OLS AR(2) model to each full input.","Transfer the x coefficients to centered y, and transfer the y coefficients to centered x.","Compute each direction's one-step squared residuals on the available 14 lagged targets.","Average the two directional MSEs; interpret this as error rather than a mathematical metric."],
            steps_zh=["分别对完整输入拟合中心化条件最小二乘 AR(2)。","将 x 的系数用于中心化 y，再将 y 的系数用于中心化 x。","对各方向的 14 个可用滞后目标计算一步预测残差平方。","平均两个方向的 MSE，把结果解释为误差分数。"],
            formula="d = (mean((y_centered-A_y phi_x)^2)+mean((x_centered-A_x phi_y)^2))/2",
            result={"label":"symmetric cross error","value":value,"detail":f"MSE(x model -> y)={mx:.8g}; MSE(y model -> x)={my:.8g}."},frames=frames)
        base["caveats_en"].append("This is not a held-out forecast evaluation: both models are fitted to the displayed records and only the comparison mechanism is illustrated. Self-error need not be zero.")
        base["caveats_zh"].append("这里并非留出预测评估：模型拟合于展示的记录，仅用于解释比较机制；自比较误差不必为零。")
    return base


def _markov_example():
    x,y=_inputs();edges=np.array([0.,.7]);sx=np.digitize(x,edges);sy=np.digitize(y,edges)
    def count(s,k):
        c=np.zeros((3,3))
        for a,b in zip(s[:k],s[1:k+1]):c[a,b]+=1
        return c
    cx,cy=count(sx,15),count(sy,15)
    px=cx/cx.sum(1,keepdims=True);py=cy/cy.sum(1,keepdims=True)
    c=(px-py)**2;value=float(np.sqrt(c.sum()));frames=[]
    for k in [1,3,6,9,12,15]:
        frames.append(_frame(0,f"Count the first {k} transitions using shared low/middle/high states.",
            {"kind":"matrix","title":"Transition counts: x (left) | y (right)","z":np.hstack([count(sx,k),count(sy,k)]).tolist(),"row_label":"current state","col_label":"x next state | y next state","cursor":[int(sx[k-1]),int(sx[k])]},highlight=[k-1,k]))
    for row in [0,1,2,0,1,2]:
        frames.append(_frame(1,"Normalize each series' transition counts by its own outgoing row total.",
            {"kind":"matrix","title":"Transition probabilities: x (left) | y (right)","z":np.hstack([px,py]).tolist(),"row_label":"current state","col_label":"x next state | y next state","cursor":[row,row]},px[row,row],"x stay probability"))
    labels=[f"{i}->{j}" for i in range(3) for j in range(3)]
    for k in [1,3,4,6,8,9]:
        frames.append(_frame(2,"Compare corresponding conditional transition probabilities.",
            _panel(c.ravel()[:k],title="Squared transition-probability differences",labels=labels[:k],marker=k-1,a_label="contributions"),np.sqrt(c.ravel()[:k].sum()),"partial Frobenius norm"))
    for k in range(4):
        frames.append(_frame(3,"Take the Frobenius norm of the complete transition-matrix difference.",
            {"kind":"matrix","title":"Signed probability difference P_x - P_y","z":(px-py).tolist(),"row_label":"current state","col_label":"next state","cursor":[k%3,k%3]},value,"final distance"))
    return {"id":"markov_distance","title":"Discretized Markov-transition distance","family":"model-based","definition":"protocol",
        "intro_en":"Map observations to three shared value states and count consecutive state transitions. Row-normalized count matrices describe the next-state distribution conditional on the current state. Compare these matrices by Frobenius distance. This illustrates a specified first-order discretization, without establishing that either signal is generated by a Markov chain.",
        "intro_zh":"把观测映射到三个共享数值状态，统计连续状态转移。按行归一化的计数矩阵描述给定当前状态时的下一状态分布，再以 Frobenius 距离比较两个矩阵。这只是指定的一阶离散化示例，并未证明信号由 Markov 链生成。",
        "steps_en":["Use shared thresholds 0 and 0.7, then count consecutive transitions between the three states.","Divide each row by its outgoing-transition count; every row is observed in this example.","Square differences between corresponding conditional transition probabilities.","Sum these squared differences and take their square root, giving the Frobenius norm."],
        "steps_zh":["用共享阈值 0 和 0.7 定义三个状态，再统计连续转移。","用各行转出总数进行归一化；本例每行均有观测。","对相对应的条件转移概率计算差的平方。","累加这些平方差并开平方，得到 Frobenius 范数。"],
        "formula":"P_ij = count(s_t=i,s_(t+1)=j) / count(s_t=i); d=||P_x-P_y||_F",
        "caveats_en":["State boundaries and sampling interval define the estimated transitions; independently chosen bins would not have matching meanings.","Unobserved rows need a documented smoothing or missing-row policy. No smoothing is used here because every row has observations.","First-order transition matrices discard longer history and do not prove causal equivalence or equal state occupancy."],
        "caveats_zh":["状态边界和采样间隔决定转移估计；分别选取的分箱可能不具有对应含义。","未观测行需要明确平滑或缺失规则。本例每行均有观测，因此不平滑。","一阶转移矩阵舍弃更长历史，也不能证明因果等价或状态占比相同。"],
        "sources":[REGISTRY,GENERATOR],"x":_list(x),"y":_list(y),"parameters":{"state_thresholds":edges.tolist(),"order":1,"smoothing":0,"unobserved_rows":"not present in this example","P_x":px.tolist(),"P_y":py.tolist()},
        "result":{"label":"distance","value":value,"detail":"Frobenius norm on conditional transition probabilities; rows unweighted."},"frames":frames}


def _independent_example(method_id,key):
    x,y=_inputs()
    # True two-channel data. The second channel is not just a repeated copy.
    t=np.arange(16);x2=.4*np.cos(2*np.pi*t/5)+.03*t;y2=.6*np.cos(2*np.pi*t/5+.4)+.02*t-.1
    xx=np.column_stack([x,x2]);yy=np.column_stack([y,y2]);spec=ENCODERS[key]
    feats_x=[spec["fn"](xx[:,i]) for i in range(2)];feats_y=[spec["fn"](yy[:,i]) for i in range(2)]
    distances=[float(np.linalg.norm(a-b)) for a,b in zip(feats_x,feats_y)];value=float(np.mean(distances));frames=[]
    for channel in range(2):
        a,b=feats_x[channel],feats_y[channel]
        for k in [1,2,3,4]:
            frames.append(_frame(0 if channel==0 else 1,f"Channel {channel+1}: extract the same {key} descriptor independently.",
                _panel(a[:k],b[:k],title=f"Channel {channel+1}: {spec['name']}",labels=spec["labels"][:k],marker=k-1),highlight=range(channel*16,(channel+1)*16)))
        for k in [1,2,3,4]:
            c=(a-b)**2
            frames.append(_frame(1 if channel==0 else 2,f"Channel {channel+1}: compute its own Euclidean feature distance.",
                _panel(c[:k],title=f"Channel {channel+1} squared feature differences",labels=spec["labels"][:k],marker=k-1,a_label="contributions"),np.sqrt(c[:k].sum()),f"channel {channel+1} distance"))
    for k in range(4):
        frames.append(_frame(3,"Average the two completed channel distances; no cross-channel terms are added.",
            _panel(distances,title="Independent channel distances",labels=["channel 1","channel 2"],marker=k%2,a_label="channel distance"),value,"mean channel distance"))
    e=_feature_example(method_id,key,title="Independent-channel "+spec["name"].lower()+" distance")
    e.update(x=_list(xx.T.ravel()),y=_list(yy.T.ravel()),input_breaks=[16],input_label="Two synthetic channels shown consecutively (samples 0–15 and 16–31)",
        intro_en=f"Extract {spec['name'].lower()} separately in each of two channels, compute one Euclidean distance per channel, then take their arithmetic mean. The displayed input concatenates channels only for visualization; the computation preserves channel boundaries and has no cross-channel dependence term.",
        intro_zh=f"分别从两个通道提取{spec['zh']}，各自计算一个欧氏距离，再取算术平均。图中的输入仅为展示而按通道拼接；计算始终保留通道边界，不包含跨通道依赖项。",
        steps_en=["Keep corresponding channel identities and units aligned.",f"Extract {spec['name'].lower()} independently from each channel.","Compute the Euclidean feature distance inside each channel.","Average the two channel distances with equal weights."],
        steps_zh=["保持对应通道身份与单位一致。",f"逐通道独立提取{spec['zh']}。","分别计算每个通道内部的欧氏特征距离。","对两个通道距离等权平均。"],
        formula="d(X,Y) = mean_c ||phi(X[:,c])-phi(Y[:,c])||_2",
        parameters=dict(spec["parameters"],channels=2,channel_weights=[.5,.5],raw_X=xx.tolist(),raw_Y=yy.tolist(),display_layout="channel-major flattening only"),
        result={"label":"distance","value":value,"detail":f"Channel distances {distances[0]:.8g} and {distances[1]:.8g}; arithmetic mean."},frames=frames)
    e["caveats_en"].append("Averaging independent channel distances cannot detect cross-channel timing or dependence changes that preserve each marginal descriptor.")
    e["caveats_zh"].append("独立通道距离的平均无法识别保持各通道边缘描述不变的跨通道时序或依赖变化。")
    return e


def _verify_local(examples):
    """Attach checks only after actually comparing with the installed source API."""
    from echotime import similarity_methods as sm
    checks = {
        "acf_distance": (sm.acf_distance,{"max_lag":6}),
        "periodogram_distance": (sm.periodogram_distance,{"n_coeffs":9}),
        "trend_distance": (sm.trend_distance,{}),
        "ordinal_pattern_js_distance": (sm.ordinal_pattern_js_distance,{"order":3,"delay":1}),
        "linear_trend_model_distance": (sm.linear_trend_model_distance,{}),
    }
    for e in examples:
        if e["id"] not in checks:continue
        fn,kw=checks[e["id"]]
        observed=float(fn(e["x"],e["y"],**kw)); expected=e["result"]["value"]
        if not np.isclose(observed,expected,rtol=1e-10,atol=1e-12):
            raise AssertionError(f"{e['id']} example {expected} differs from EchoTime {observed}")
        e["checks"]={"api":"echotime."+e["id"],"expected":expected,"observed":observed,"tolerance":1e-10}
        e["definition"]="echotime"


def build_examples():
    """Return all 47 registry examples owned by these three method families."""
    examples = [
        _feature_example("stats_distance","stats"),
        _feature_example("robust_stats_distance","robust_stats"),
        _feature_example("acf_distance","acf",definition="echotime"),
        _feature_example("spectral_cosine_similarity","dft","cosine",title="Fourier-magnitude cosine similarity"),
        _feature_example("spectral_distance","dft","one_minus_cosine",title="Fourier-magnitude cosine distance"),
        _feature_example("periodogram_distance","periodogram",definition="echotime"),
        _feature_example("paa_distance","paa"),
        _full_haar_example(),
        _feature_example("histogram_distance","histogram"),
        _ordinal_example("permutation_entropy_distance"),
        _ordinal_example("ordinal_pattern_js_distance"),
        _feature_example("trend_distance","trend",definition="echotime"),
        _sax_example("sax_hamming_distance"),
        _sax_example("sax_mindist"),
        _bop_example("bag_of_patterns_cosine_similarity"),
        _bop_example("bag_of_patterns_distance"),
        _independent_example("independent_stats_distance","stats"),
        _independent_example("independent_paa_distance","paa"),
        _ar_example("ar_distance"),
        _ar_example("ar_spectrum_distance"),
        _ar_example("ar_prediction_error_distance"),
        _markov_example(),
        _feature_example("linear_trend_model_distance","trend",family="model-based",title="Linear-trend model distance",definition="echotime"),
    ]
    for key in ["generic","paa","dft","stats","robust_stats","acf","wavelet","histogram","periodogram","trend","random_projection","identity"]:
        for suffix,mode in [("distance","euclidean"),("similarity","cosine")]:
            method_id=("embedding_" if key=="generic" else key+"_embedding_")+suffix
            examples.append(_feature_example(method_id,key,mode,family="embedding",title=ENCODERS[key]["name"]+" embedding "+suffix,definition="protocol" if key=="generic" else "reference"))
    for e in examples:
        e["sources"] = list({source["url"]: source for source in e["sources"]}.values())
    short_steps = {
        "dwt_distance": ["Compute orthonormal Haar pair sums and differences at four levels.", "Collect all 16 approximation and detail coefficients.", "Accumulate squared differences between matching coefficients.", "Verify that coefficient L2 equals raw-sample Euclidean distance."],
        "permutation_entropy_distance": ["Form overlapping three-point windows with delay one.", "Rank each window; count all six patterns with a fixed tie policy.", "Compute normalized Shannon entropy for each pattern distribution.", "Take the absolute entropy difference; pattern identities are discarded."],
        "ordinal_pattern_js_distance": ["Form overlapping three-point windows with delay one.", "Rank each window; count all six patterns with a fixed tie policy.", "Compare the full distributions with natural-log Jensen-Shannon divergence.", "Take the square root to obtain the displayed JS distance."],
        "sax_hamming_distance": ["Z-normalize each input and average four equal blocks.", "Quantize block means with shared Gaussian quartile breakpoints.", "Count positions with different symbols, including adjacent bins.", "Divide the mismatch count by the word length of four."],
        "sax_mindist": ["Z-normalize each input and average four equal blocks.", "Quantize block means with shared Gaussian quartile breakpoints.", "Look up interval gaps; equal or adjacent symbols contribute zero.", "Apply sqrt(n/w) to the gap norm to obtain a Euclidean lower bound."],
        "bag_of_patterns_cosine_similarity": ["Slide, normalize and SAX-encode each length-eight window.", "Suppress consecutive repeats and count a shared word vocabulary.", "Accumulate matching word-count products, divided by vector norms.", "Read cosine similarity between the two word-count vectors."],
        "bag_of_patterns_distance": ["Slide, normalize and SAX-encode each length-eight window.", "Suppress consecutive repeats and count a shared word vocabulary.", "Accumulate matching word-count products, divided by vector norms.", "Subtract the completed cosine similarity from one."],
        "independent_stats_distance": ["Keep the two channel identities aligned; display them consecutively.", "Extract mean, SD, minimum and maximum separately in each channel.", "Compute one Euclidean feature distance per channel.", "Average the two distances; cross-channel dependence is not measured."],
        "independent_paa_distance": ["Keep the two channel identities aligned; display them consecutively.", "Extract four consecutive block means separately in each channel.", "Compute one Euclidean PAA-vector distance per channel.", "Average the two distances; cross-channel dependence is not measured."],
        "ar_distance": ["Demean each input and construct two lagged predictors.", "Fit the same AR(2) recurrence by conditional least squares.", "Compare corresponding lag-one and lag-two coefficients.", "Take the Euclidean norm of the coefficient difference."],
        "ar_spectrum_distance": ["Demean each input and fit a conditional least-squares AR(2) model.", "Check stability; evaluate log spectra on 17 shared frequencies.", "Square differences between matching natural-log spectral coordinates.", "Take the Euclidean norm of the two log-spectrum vectors."],
        "ar_prediction_error_distance": ["Fit one centered conditional least-squares AR(2) model to each input.", "Use the x model to predict y, then use the y model to predict x.", "Compute each direction's one-step mean-squared prediction error.", "Average the two errors; even self-error can be positive."],
        "markov_distance": ["Bin both inputs with thresholds 0 and 0.7, then count state transitions.", "Normalize each row by its outgoing-transition count.", "Square differences between corresponding transition probabilities.", "Sum squared differences and take the square root."],
    }
    for e in examples:
        if e["id"] in short_steps:
            e["animation_steps_en"] = short_steps[e["id"]]
        assert len(e["animation_steps_en"]) == 4
        assert all(len(step) <= 85 for step in e["animation_steps_en"]), e["id"]
    _verify_local(examples)
    if len(examples)!=47 or len({x["id"] for x in examples})!=47:
        raise AssertionError("Feature/model/embedding coverage must be exactly 47 unique IDs.")
    return examples


if __name__ == "__main__":
    import json
    import csv
    from pathlib import Path
    examples=build_examples()
    expected={r["name"] for r in csv.DictReader((Path(__file__).resolve().parents[2]/"src/echotime/data/ts_similarity_package_v2_registry.csv").open()) if r["family"] in {"feature-based","model-based","embedding"}}
    assert {x["id"] for x in examples}==expected
    json.dumps(examples,allow_nan=False)
    for e in examples:
        assert 16<=len(e["frames"])<=28,(e["id"],len(e["frames"]))
        assert len(e["steps_en"])==len(e["steps_zh"])==4
        assert all(len(f["caption"])<=100 for f in e["frames"]),(e["id"],max(len(f["caption"]) for f in e["frames"]))
    print(json.dumps({"methods":len(examples),"frames":sum(len(e["frames"]) for e in examples),"local_api_checks":{e["id"]:e["checks"] for e in examples if "checks" in e},"results":{e["id"]:e["result"]["value"] for e in examples}},indent=2))
