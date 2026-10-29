"""Numerical teaching traces for pointwise, shifted and native comparisons.

Reference demonstrations are deliberately separate from the public API. Native
cards assert their reported output against a real ``compare_series`` call.
All input arrays are synthetic illustrations, not benchmark observations.
"""

from __future__ import annotations

import copy
import math
from itertools import combinations
from typing import Callable

import numpy as np
from scipy.spatial import distance as sd
from scipy.stats import entropy, kendalltau, rankdata, spearmanr

ROOT_URL = "https://github.com/ZipengWu365/EchoTime/blob/main/"
REGISTRY = ROOT_URL + "src/echotime/data/ts_similarity_package_v2_registry.csv"
NATIVE = ROOT_URL + "src/echotime/similarity.py"
LOWLEVEL = ROOT_URL + "src/echotime/similarity_methods.py"
KSHAPE = "https://www.paparrizos.org/papers/PaparrizosSIGMOD15.pdf"
CID = "https://www.cs.ucr.edu/~eamonn/Complexity-Invariant%20Distance%20Measure.pdf"


def _source(label: str, url: str) -> dict:
    return {"label": label, "url": url}


def _scipy(name: str, *, stats: bool = False) -> dict:
    namespace = "stats" if stats else "spatial.distance"
    return _source("SciPy: " + name, f"https://docs.scipy.org/doc/scipy/reference/generated/scipy.{namespace}.{name}.html")


def _floats(values) -> list[float]:
    return [float(v) for v in values]


def _plain(value):
    """Keep the interchange format independent of NumPy scalar encodings."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _z(x) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return (x - x.mean()) / x.std()


def _frame(phase: int, caption: str, panel: dict, value: float | None = None,
           label: str = "partial result", highlight: list[int] | None = None) -> dict:
    if len(caption) > 100:
        raise ValueError(caption)
    out = {"phase": phase, "caption": caption, "panel": panel}
    if value is not None:
        out.update(value=float(value), value_label=label)
    if highlight is not None:
        out["input_highlight"] = highlight
    return out


def _lines(a, b=None, *, title: str, marker: int | None = None,
           a_label: str = "x", b_label: str = "y", x=None) -> dict:
    panel = {"kind": "lines", "title": title, "a": _floats(a), "a_label": a_label}
    if b is not None:
        panel.update(b=_floats(b), b_label=b_label)
    if marker is not None:
        panel["marker"] = int(marker)
    if x is not None:
        panel["x"] = _floats(x)
    return panel


def _bars(a, b=None, *, title: str, marker: int | None = None,
          a_label: str = "contribution", b_label: str = "y", labels=None) -> dict:
    panel = {"kind": "bars", "title": title, "a": _floats(a), "a_label": a_label}
    if b is not None:
        panel.update(b=_floats(b), b_label=b_label)
    if marker is not None:
        panel["marker"] = int(marker)
    if labels is not None:
        panel["labels"] = list(labels)
    return panel


def _card(id: str, title: str, family: str, x, y, *, intro_en: str,
          intro_zh: str, steps_en: list[str], steps_zh: list[str], formula: str,
          caveats_en: list[str], caveats_zh: list[str], sources: list[dict],
          parameters: dict, value: float, frames: list[dict],
          kind: str = "distance", definition: str = "reference", detail: str = "") -> dict:
    if not math.isfinite(float(value)):
        raise ValueError(f"Non-finite result for {id}")
    if len(steps_en) != 4 or len(steps_zh) != 4 or not 16 <= len(frames) <= 28:
        raise ValueError(f"Invalid teaching stages/frames for {id}: {len(frames)}")
    return _plain(dict(id=id, title=title, family=family, definition=definition,
                intro_en=intro_en, intro_zh=intro_zh, steps_en=steps_en,
                steps_zh=steps_zh, formula=formula, caveats_en=caveats_en,
                caveats_zh=caveats_zh, sources=sources, x=_floats(x), y=_floats(y),
                input_label="Deterministic synthetic illustration; sample index is the time axis.",
                parameters=parameters, result={"label": kind, "value": float(value), "detail": detail},
                frames=frames))


# Relative measures use strictly positive inputs: this makes their domain and
# all denominators explicit rather than introducing hidden epsilon corrections.
X = np.array([1.0, 1.5, 2.4, 3.7, 4.5, 3.8, 2.6, 2.1, 2.8, 3.8, 4.1, 3.3])
Y = np.array([1.3, 1.8, 2.0, 3.2, 5.2, 4.4, 2.9, 1.6, 2.6, 3.1, 4.4, 3.9])


def _sum_trace(a, b, terms, finish: Callable[[float], float], *, term_label: str,
               final_label: str, prep_label: str = "Aligned samples", reduction: str = "sum") -> list[dict]:
    """Expose actual fixed terms and their partial reduction, never invent scores."""
    a, b, terms = map(lambda v: np.asarray(v, dtype=float), (a, b, terms))
    frames = []
    n = len(terms)
    for k in np.linspace(2, len(a), 4, dtype=int):
        frames.append(_frame(0, prep_label,
                             _lines(a[:k], b[:k], title=prep_label, marker=k - 1)))
    for k in np.linspace(1, n, 4, dtype=int):
        visible = terms.copy()
        visible[k:] = 0.0
        frames.append(_frame(1, f"Compute coordinate {k}: {term_label}",
                             _bars(visible, title=term_label, marker=k - 1),
                             float(terms[k - 1]), "coordinate term", [min(k - 1, len(a) - 1)]))
    for k in np.linspace(1, n, 8, dtype=int):
        visible = terms.copy()
        visible[k:] = 0.0
        partial = float(np.max(terms[:k])) if reduction == "max" else float(np.sum(terms[:k]))
        frames.append(_frame(2, f"Accumulate {k} of {n} coordinate terms",
                             _bars(visible, title="Terms included so far", marker=k - 1),
                             partial, "running " + reduction))
    total = float(np.max(terms)) if reduction == "max" else float(np.sum(terms))
    final = finish(total)
    for k in np.linspace(0, n - 1, 4, dtype=int):
        frames.append(_frame(3, final_label,
                             _bars(terms, title=term_label, marker=k), final, "final result"))
    return frames


# Each row states its actual scalar operation and its distinctive use/boundary.
_POINTWISE_TEXT = {
    "euclidean": (
        "Euclidean distance", "sqrt(sum_i (x_i-y_i)^2)",
        "Euclidean distance treats an aligned time series as one vector. Every vertical gap contributes a squared cost, and the final square root returns the result to the original amplitude units. The animation shows exactly which sample differences produce the final distance; no temporal realignment is performed.",
        "欧氏距离把已经对齐的时间序列视为向量。每个时刻的垂直差先平方后累加，再开平方回到原始幅值单位。动图展示各时刻如何贡献最终距离，整个计算不重新对齐时间。",
        "Square each residual", "Take the square root of the total squared gap",
        "A single large residual can dominate the squared sum.", "单个大误差可能主导平方和。", "euclidean"),
    "squared_euclidean": (
        "Squared Euclidean", "sum_i (x_i-y_i)^2",
        "Squared Euclidean distance accumulates squared residuals without taking a square root. This makes coordinate contributions additive and keeps large errors prominent. It has the same nearest-neighbour ordering as Euclidean distance on the same vectors, but the output has squared amplitude units and is not a metric.",
        "平方欧氏距离直接累加平方残差，不再开平方。因此各坐标贡献可相加，大误差受到更强惩罚。在同一组向量上，它与欧氏距离给出相同的近邻排序，但结果单位为幅值平方，也不满足一般的三角不等式。",
        "Square each residual", "Keep the squared sum; do not take a square root",
        "Squaring a metric does not generally preserve the triangle inequality.", "对度量取平方通常不保留三角不等式。", "sqeuclidean"),
    "rmse_distance": (
        "Root mean square error", "sqrt(mean_i (x_i-y_i)^2)",
        "RMSE averages squared residuals before taking a square root. For vectors of one fixed length it is Euclidean distance divided by the square root of that length. The animation separates the squared-error accumulation, averaging, and final root so its difference from a raw Euclidean total is visible.",
        "RMSE 先对平方误差取平均，再开平方。向量长度固定时，它等于欧氏距离除以长度的平方根。动图将平方累加、求平均和开平方分开，说明它与未归一化欧氏距离的关系。",
        "Square each residual", "Divide by sample count, then take the square root",
        "The fixed-length equivalence does not justify comparing different missing-data or alignment protocols.", "固定长度下的等价关系不能代替缺失值和对齐协议的一致性。", "euclidean"),
    "manhattan": (
        "Manhattan distance", "sum_i abs(x_i-y_i)",
        "Manhattan distance adds the absolute gap at every aligned time point. Positive and negative errors cannot cancel, and the penalty grows linearly with each residual. Its animation accumulates visible vertical discrepancies one by one. Longer vectors can produce larger totals even when their typical per-sample discrepancy is unchanged.",
        "曼哈顿距离累加每个对齐时刻的绝对差。正负误差不会抵消，每个残差的惩罚线性增长。动图逐项累积垂直差；即使平均误差不变，序列更长也可能产生更大的总距离。",
        "Take each absolute residual", "Sum the absolute gaps",
        "The sum depends on the number of compared coordinates.", "总和依赖比较的坐标数量。", "cityblock"),
    "mae_distance": (
        "Mean absolute error", "mean_i abs(x_i-y_i)",
        "MAE reports the average absolute discrepancy on an aligned time axis. It divides the Manhattan total by the number of compared coordinates, retaining the original amplitude units. The animation shows both the individual absolute gaps and the average, making clear why the same total can imply different typical errors at different lengths.",
        "MAE 表示对齐时间轴上的平均绝对差。它将曼哈顿总距离除以比较坐标数，仍使用原始幅值单位。动图同时展示各点绝对误差和最终平均值，帮助区分总误差与典型逐点误差。",
        "Take each absolute residual", "Divide the absolute-error sum by sample count",
        "Averaging does not remove sensitivity to a systematic time shift.", "求平均不能消除系统性的时间偏移影响。", "cityblock"),
    "minkowski": (
        "Minkowski distance (p=3)", "(sum_i abs(x_i-y_i)^p)^(1/p); p=3",
        "Minkowski distance controls how strongly larger coordinate errors dominate through an exponent p. This illustration fixes p to three: absolute residuals are cubed, added, and then transformed by a cube root. Choosing another p changes the definition; p equals one and two recover Manhattan and Euclidean distances.",
        "Minkowski 距离用指数 p 控制大误差的影响。本例固定 p=3：绝对残差立方后相加，再开立方。p 的选择属于方法定义；p=1 与 p=2 分别对应曼哈顿和欧氏距离。",
        "Cube the absolute residual (p=3)", "Take the p-th root of the accumulated p-th powers",
        "The norm/metric property requires p >= 1; p < 1 defines a different quasi-distance.", "范数和度量性质要求 p≥1；p<1 时属于不同的拟距离。", "minkowski"),
    "chebyshev": (
        "Chebyshev distance", "max_i abs(x_i-y_i)",
        "Chebyshev distance keeps only the largest aligned absolute error. A running maximum identifies the worst discrepancy as the animation scans the sequence. It answers a maximum-deviation question, so a small improvement at the worst point matters while changes below the current maximum may leave the result unchanged.",
        "Chebyshev 距离只保留最大的逐点绝对误差。动图扫描序列并更新当前最大值，回答最坏偏差有多大的问题。因此最大误差位置的变化很重要，其他位置的小幅变化可能完全不改变结果。",
        "Measure the absolute residual", "Keep the largest coordinate discrepancy",
        "One isolated spike may determine the entire result.", "一个孤立尖峰就可能决定全部结果。", "chebyshev"),
    "canberra": (
        "Canberra distance", "sum_i abs(x_i-y_i)/(abs(x_i)+abs(y_i))",
        "Canberra distance normalizes each coordinate error by the magnitudes at that same coordinate before adding the ratios. This gives small-amplitude positions a potentially large influence compared with an unscaled absolute error. The example uses positive values so the animation can expose the local denominator without an undefined zero-over-zero term.",
        "Canberra 距离先用每个坐标两侧幅值之和归一化该点误差，再累加比值。相较未缩放的绝对误差，低幅值位置可能获得较大影响。本例使用正值，明确展示逐点分母并避免 0/0。",
        "Divide each gap by local absolute magnitudes", "Sum coordinate-wise relative errors",
        "Near-zero coordinates can be influential; a zero-over-zero convention must be stated.", "接近零的坐标可能影响很大；必须声明 0/0 的处理约定。", "canberra"),
    "bray_curtis": (
        "Bray-Curtis dissimilarity", "sum_i abs(x_i-y_i) / sum_i abs(x_i+y_i)",
        "Bray-Curtis divides a total absolute discrepancy by a total combined magnitude. The denominator is global, unlike Canberra's coordinate-specific denominators. On the positive illustration it measures discrepancy relative to the combined mass. The displayed calculation uses the exact absolute-sum denominator in the imported registry and SciPy definition.",
        "Bray-Curtis 用总绝对差除以整体合并幅值。其分母是全局的，与 Canberra 逐坐标归一化不同。本例输入为正值，结果表示相对合并总量的差异；所示公式采用导入登记表及 SciPy 的绝对和分母。",
        "Accumulate absolute gaps", "Divide by the fixed total abs(x+y)",
        "Signed data can cause a zero or small denominator; the usual bounded interpretation assumes nonnegative data.", "带符号数据可能使分母为零或很小；通常的有界解释依赖非负输入。", "braycurtis"),
    "sorensen": (
        "Sorensen-style dissimilarity", "sum_i abs(x_i-y_i) / sum_i (abs(x_i)+abs(y_i))",
        "This registry entry normalizes the absolute-error total by the sum of both vectors' absolute magnitudes. On nonnegative data it agrees with Bray-Curtis; signed data distinguish their denominators. The animation states the formula explicitly because the Sorensen name is also used for set-based coefficients with a different input object.",
        "此登记条目用两侧绝对幅值的总和归一化绝对误差总量。非负输入时它与 Bray-Curtis 相同，带符号输入时两者分母不同。Sorensen 也用于集合系数，因此本动图直接声明所演示的数值向量公式。",
        "Accumulate absolute gaps", "Divide by total absolute mass of both vectors",
        "This is the registry's numerical-vector convention, not the binary set Dice coefficient.", "这里使用登记表的数值向量约定，与二元集合 Dice 系数的输入对象不同。", None),
    "soergel": (
        "Soergel-style distance", "sum_i abs(x_i-y_i) / sum_i max(abs(x_i),abs(y_i))",
        "The Soergel-style entry divides total absolute discrepancy by the sum of the larger magnitudes at each coordinate. The animation contrasts its fixed maximum-envelope denominator with the residual sum. Nonnegative vectors provide the standard overlap interpretation; the absolute-magnitude extension shown in the registry needs its signed-data convention kept explicit.",
        "Soergel 型条目用各坐标较大幅值的总和归一化绝对误差。动图展示最大幅值包络分母与误差总和的关系。非负向量具有通常的重叠解释；登记表对带符号输入采用绝对幅值扩展，需要明确这一约定。",
        "Accumulate absolute gaps", "Divide by the total maximum-magnitude envelope",
        "The example uses nonnegative values; signed extensions need separate property checks.", "本例使用非负值；带符号扩展的性质需要另行检查。", None),
    "kulczynski": (
        "Kulczynski-style ratio", "sum_i abs(x_i-y_i) / sum_i min(abs(x_i),abs(y_i))",
        "This registry convention compares total discrepancy with the smaller magnitude available at each coordinate. A small shared-magnitude denominator can amplify the result sharply. The animation exposes this denominator rather than hiding it in a generic distance score. Several different association coefficients share the Kulczynski name, so this particular formula is recorded explicitly.",
        "此登记约定用各坐标较小幅值的总和作为分母。共享幅值较小时，比值会显著放大。动图显式展示分母。Kulczynski 名称也用于其他关联系数，因此这里记录的只是所列的特定公式。",
        "Accumulate absolute gaps", "Divide by the total minimum shared magnitude",
        "The ratio is undefined at zero shared mass and is not bounded by one.", "共享总量为零时比值未定义，结果也不以 1 为上界。", None),
    "clark": (
        "Clark distance", "sqrt(sum_i (abs(x_i-y_i)/(abs(x_i)+abs(y_i)))^2)",
        "Clark distance forms a relative error at each coordinate, then takes an Euclidean norm of those ratios. It therefore differs from Canberra's straight sum of relative errors. The animation first exposes the local ratios and then squares and aggregates them, showing how one relatively discordant coordinate can dominate the combined score.",
        "Clark 距离先形成逐坐标相对误差，再对这些比值求欧氏范数。它与直接累加相对误差的 Canberra 不同。动图先计算局部比值，再平方聚合，展示相对差异较大的位置如何影响总体结果。",
        "Square the coordinate-wise relative error", "Take the root of the sum of squared relative errors",
        "The local zero-over-zero convention matters, especially for sparse signals.", "稀疏信号尤其需要明确局部 0/0 的处理约定。", None),
    "wave_hedges": (
        "Wave-Hedges distance", "sum_i abs(x_i-y_i)/max(abs(x_i),abs(y_i))",
        "Wave-Hedges normalizes each coordinate's absolute discrepancy by its larger magnitude and then adds the ratios. In contrast to a single global normalization, every active coordinate can contribute substantially regardless of its absolute scale. The animation illustrates the local maximum denominator on strictly positive data, avoiding an unstated zero-over-zero rule.",
        "Wave-Hedges 用每个坐标较大的幅值归一化该点误差，再求和。与全局归一化相比，每个非零坐标都可能产生明显贡献，不取决于其绝对规模。本例使用严格正值，避免未声明的 0/0 规则。",
        "Scale each gap by its larger local magnitude", "Add the local maximum-normalized discrepancies",
        "Sparse near-zero coordinates require a declared convention; signed inputs change the usual range.", "稀疏近零坐标需要声明约定；带符号输入会改变通常的取值范围。", None),
    "lorentzian": (
        "Lorentzian-style log distance", "sum_i log(1+abs(x_i-y_i))",
        "This Lorentzian-style entry applies a logarithm to each absolute residual before summing. The transformation compresses large residuals relative to a linear or squared penalty. Its animation compares raw residuals with the log-transformed contributions. The added constant one fixes an implicit amplitude scale, which must be meaningful for the data units.",
        "此 Lorentzian 型条目先对每个绝对残差进行 log(1+误差) 变换，再累加。相较线性或平方惩罚，对数会压缩大误差。加数 1 隐含了幅值尺度，因此使用时必须考虑数据单位。",
        "Apply log(1+absolute residual)", "Sum the log-compressed discrepancies",
        "Changing measurement units changes the balance introduced by the constant one.", "改变测量单位会改变常数 1 所引入的尺度关系。", None),
}

_POINTWISE_ZH_OPERATIONS = {
    "euclidean": ("计算各坐标残差的平方。", "对平方差总和开平方。"),
    "squared_euclidean": ("计算各坐标残差的平方。", "直接保留平方差总和，不开平方。"),
    "rmse_distance": ("计算各坐标残差的平方。", "平方差总和除以样本数后，再开平方。"),
    "manhattan": ("计算各坐标的绝对残差。", "直接保留绝对差总和。"),
    "mae_distance": ("计算各坐标的绝对残差。", "绝对差总和除以样本数。"),
    "minkowski": ("对各坐标绝对残差取三次方，本例 p=3。", "对三次方总和开立方。"),
    "chebyshev": ("计算各坐标的绝对残差。", "以所有坐标中的最大绝对差作为结果。"),
    "canberra": ("逐坐标以两侧绝对幅值之和归一化绝对差。", "累加所有逐坐标相对误差。"),
    "bray_curtis": ("计算各坐标的绝对残差。", "用绝对差总和除以固定的 sum(abs(x+y))。"),
    "sorensen": ("计算各坐标的绝对残差。", "用绝对差总和除以两向量绝对幅值的总和。"),
    "soergel": ("计算各坐标的绝对残差。", "用绝对差总和除以各坐标较大绝对幅值的总和。"),
    "kulczynski": ("计算各坐标的绝对残差。", "用绝对差总和除以各坐标较小绝对幅值的总和。"),
    "clark": ("逐坐标计算相对绝对误差，再将比值平方。", "对相对误差平方和开平方。"),
    "wave_hedges": ("逐坐标以较大绝对幅值归一化绝对差。", "累加各坐标归一化后的误差。"),
    "lorentzian": ("逐坐标计算 log(1+绝对残差)。", "直接累加对数压缩后的局部贡献。"),
}


def _pointwise_examples() -> list[dict]:
    out = []
    delta = np.abs(X - Y)
    for name, desc in _POINTWISE_TEXT.items():
        title, formula, en, zh, term_label, final_label, caution, caution_zh, scipy_name = desc
        finish: Callable[[float], float] = lambda total: total
        terms = delta.copy()
        parameters = {"samples": len(X), "preprocessing": "none", "domain": "strictly positive illustration"}
        reduction = "sum"
        if name in {"euclidean", "squared_euclidean", "rmse_distance"}:
            terms = delta ** 2
            if name == "euclidean": finish = math.sqrt
            elif name == "rmse_distance": finish = lambda total: math.sqrt(total / len(X))
        elif name == "mae_distance": finish = lambda total: total / len(X)
        elif name == "minkowski":
            terms = delta ** 3; finish = lambda total: total ** (1 / 3); parameters["p"] = 3
        elif name == "chebyshev": reduction = "max"
        elif name == "canberra": terms = delta / (np.abs(X) + np.abs(Y))
        elif name in {"bray_curtis", "sorensen", "soergel", "kulczynski"}:
            den = {"bray_curtis": np.abs(X + Y), "sorensen": np.abs(X) + np.abs(Y),
                   "soergel": np.maximum(np.abs(X), np.abs(Y)),
                   "kulczynski": np.minimum(np.abs(X), np.abs(Y))}[name].sum()
            finish = lambda total, den=float(den): total / den
            parameters["global_denominator"] = float(den)
        elif name == "clark": terms = (delta / (np.abs(X) + np.abs(Y))) ** 2; finish = math.sqrt
        elif name == "wave_hedges": terms = delta / np.maximum(np.abs(X), np.abs(Y))
        elif name == "lorentzian": terms = np.log1p(delta)
        total = float(terms.max()) if reduction == "max" else float(terms.sum())
        value = finish(total)
        source = [_scipy(scipy_name)] if scipy_name else [_source("Imported registry: explicit formula convention", REGISTRY)]
        out.append(_card(name, title, "lock-step", X, Y, intro_en=en, intro_zh=zh,
             steps_en=["Keep the two series on the same sample grid; no shift or warping is estimated.",
                       term_label + "; the highlighted point supplies one coordinate contribution.",
                       ("Update the running maximum." if reduction == "max" else "Accumulate the coordinate contributions in sample order."),
                       final_label + "."],
             steps_zh=["在同一采样网格上比较两条序列，不估计平移或时间规整。", _POINTWISE_ZH_OPERATIONS[name][0],
                       "更新当前最大误差。" if reduction == "max" else "按采样顺序累积局部贡献。", _POINTWISE_ZH_OPERATIONS[name][1]],
             formula=formula, caveats_en=[caution, "Sample alignment and amplitude units are part of the comparison protocol."],
             caveats_zh=[caution_zh, "采样对齐和幅值单位属于比较协议的一部分。"], sources=source,
             parameters=parameters, value=value,
             frames=_sum_trace(X, Y, terms, finish, term_label=term_label, final_label=final_label, reduction=reduction),
             detail="Exact formula evaluation on the displayed aligned vectors."))
    return out


def _normalised_examples() -> list[dict]:
    out = []
    # Variance is fixed before looking at this pair, not estimated from x and y.
    variance = np.array([.4, .6, 1.0, 1.5, 2.0, 1.3, .9, .7, 1.1, 1.7, 1.8, 1.2])
    terms = (X - Y) ** 2 / variance
    value = math.sqrt(float(terms.sum()))
    assert np.isclose(value, sd.seuclidean(X, Y, variance))
    out.append(_card("seuclidean_distance", "Standardized Euclidean", "lock-step", X, Y,
        intro_en="Standardized Euclidean distance divides each squared coordinate residual by a supplied variance. Coordinates with greater reference variation receive less weight. This animation uses an explicit, fixed variance vector, so the comparison does not secretly estimate scale from the two sequences being scored. The final root gives a distance in variance-standardized coordinates.",
        intro_zh="标准化欧氏距离用给定方差缩放每个坐标的平方残差。参考变化更大的坐标权重较低。本动图使用显式固定的方差向量，不从待比较的两条序列暗中估计尺度，最后开平方得到标准化坐标空间中的距离。",
        steps_en=["Align samples and provide a positive reference variance for every coordinate.",
                  "Square each residual and divide it by that coordinate's variance.",
                  "Sum the standardized squared contributions.", "Take the square root; retain the same variance vector for future comparisons."],
        steps_zh=["对齐采样点，为每个坐标提供正的参考方差。", "平方残差后除以对应坐标的方差。", "累加标准化平方项。", "开平方；后续比较保持同一参考方差。"],
        formula="sqrt(sum_i (x_i-y_i)^2 / v_i), with fixed v_i > 0",
        caveats_en=["Zero variances need an explicit exclusion or regularization policy.", "Estimating variances using test data can leak information; use a declared reference fit."],
        caveats_zh=["零方差需要明确的剔除或正则化策略。", "用测试数据估计方差可能泄漏信息；应声明参考拟合来源。"],
        sources=[_scipy("seuclidean")], parameters={"variance": _floats(variance), "variance_source": "fixed illustrative vector"},
        value=value, frames=_sum_trace(X, Y, terms, math.sqrt, term_label="Squared residual / reference variance", final_label="Square root of the weighted squared-error sum")))
    for name, p in (("znorm_euclidean", 2), ("znorm_manhattan", 1)):
        x = X; y = 1.8 * Y + 3.0
        a, b = _z(x), _z(y)
        terms = np.abs(a - b) ** p
        finish = math.sqrt if p == 2 else float
        value = finish(float(terms.sum()))
        norm = "Euclidean" if p == 2 else "Manhattan"
        card = _card(name, f"Z-normalized {norm}", "lock-step", x, y,
            intro_en=f"Z-normalized {norm} first removes each sequence's own mean and divides by its standard deviation. The final {norm} comparison therefore emphasizes the shape remaining on a common time grid. The input illustration deliberately includes an offset and gain difference so the normalized traces visibly differ from the raw signals.",
            intro_zh=f"Z 标准化 {norm} 比较先分别减去每条序列的均值，再除以各自标准差，随后在共同时间网格上比较标准化形状。本例刻意加入偏移和增益差，使原始信号与标准化后的曲线形成清晰对照。",
            steps_en=["Estimate each series' own mean and population standard deviation.",
                      "Subtract that mean and divide by that standard deviation.",
                      "Accumulate squared normalized gaps." if p == 2 else "Accumulate absolute normalized gaps.",
                      "Take the square root of the total." if p == 2 else "Keep the absolute-gap total."],
            steps_zh=["分别估计每条序列的均值和总体标准差。", "分别去均值并除以标准差。", "累加标准化后的平方差。" if p == 2 else "累加标准化后的绝对差。", "对总和开平方。" if p == 2 else "保留绝对差总和。"],
            formula=f"||z(x)-z(y)||_{p}; z(x)=(x-mean(x))/std(x, ddof=0)",
            caveats_en=["Positive gain and offset information is deliberately removed; distinct raw series can have zero distance.", "Constant sequences need a separately declared convention; this illustration has positive variance."],
            caveats_zh=["正增益和偏移信息被主动去除；不同原序列可能距离为零。", "常量序列必须另行规定处理方式；本例方差严格为正。"],
            sources=[_source("Imported registry: normalization convention", REGISTRY), _scipy("euclidean" if p == 2 else "cityblock")],
            parameters={"ddof": 0, "norm": p, "means": [float(x.mean()), float(y.mean())], "standard_deviations": [float(x.std()), float(y.std())]},
            value=value, frames=_sum_trace(a, b, terms, finish, term_label="Squared normalized gaps" if p == 2 else "Absolute normalized gaps", final_label=f"{norm} distance in z-normalized coordinates", prep_label="Each series independently z-normalized"))
        out.append(card)
    ce_x = float(np.linalg.norm(np.diff(X))); ce_y = float(np.linalg.norm(np.diff(Y)))
    ed = float(np.linalg.norm(X - Y)); factor = max(ce_x, ce_y) / min(ce_x, ce_y)
    value = ed * factor
    frames = []
    for k in np.linspace(2, len(X), 4, dtype=int):
        frames.append(_frame(0, "Compute the aligned Euclidean baseline", _lines(X[:k], Y[:k], title="Aligned input prefixes")))
    for k in np.linspace(2, len(X) - 1, 4, dtype=int):
        frames.append(_frame(1, "Consecutive changes define the chosen complexity estimate", _bars(np.diff(X)[:k] ** 2, np.diff(Y)[:k] ** 2, title="Squared first differences", a_label="x", b_label="y")))
    for k in np.linspace(1, len(X) - 1, 8, dtype=int):
        cx = float(np.linalg.norm(np.diff(X)[:k])); cy = float(np.linalg.norm(np.diff(Y)[:k]))
        frames.append(_frame(2, "Accumulate first-difference energy in both sequences", _bars([cx, cy], title="Complexity accumulated so far", labels=["CE(x)", "CE(y)"]), max(cx, cy) / min(cx, cy), "partial complexity ratio"))
    for k in range(4):
        frames.append(_frame(3, "Multiply Euclidean distance by the final complexity ratio", _bars([ed, factor, value], title="ED baseline, CE ratio, corrected distance", labels=["ED", "ratio", "CID"], marker=k % 3), value, "CID"))
    out.append(_card("cid_distance", "Complexity-invariant distance", "lock-step", X, Y,
        intro_en="CID multiplies a base Euclidean distance by the ratio of the larger to the smaller series complexity. Here complexity is the Euclidean length of the first-difference vector. The animation separately computes the baseline mismatch, both complexity estimates and their correction factor; its name does not establish invariance to every possible change in complexity.",
        intro_zh="CID 用较大与较小复杂度之比修正欧氏距离。本例复杂度定义为一阶差分向量的欧氏长度。动图依次计算基准差异、两侧复杂度及修正因子；名称并不意味着对所有改变复杂度的操作都严格不变。",
        steps_en=["Compute the ordinary Euclidean distance on aligned samples.", "Form first differences and sum their squared values for each series.", "Take both roots and divide the larger complexity by the smaller.", "Multiply the baseline distance by this complexity ratio."],
        steps_zh=["计算对齐样本的欧氏距离。", "分别计算一阶差分及平方和。", "分别开平方，用较大复杂度除以较小复杂度。", "以复杂度比乘以基准距离。"],
        formula="CID=||x-y||_2 * max(CE(x),CE(y))/min(CE(x),CE(y)); CE(x)=||diff(x)||_2",
        caveats_en=["A constant series has zero complexity; the correction needs an explicit boundary rule.", "The estimator depends on sampling and noise; this animation makes no accuracy or universal invariance claim."],
        caveats_zh=["常量序列的复杂度为零，修正项需要明确的边界规则。", "估计值依赖采样和噪声；此动图不提供准确率或普遍不变性结论。"],
        sources=[_source("Batista, Wang and Keogh: original CID paper", CID)],
        parameters={"base_distance": "Euclidean", "complexity": "L2 norm of first differences", "CE_x": ce_x, "CE_y": ce_y},
        value=value, frames=frames))
    return out


def _corr_trace(a, b, *, title: str, transform: Callable[[float], float],
                final_label: str, rank: bool = False) -> tuple[list[dict], float]:
    a, b = np.asarray(a), np.asarray(b)
    aa, bb = (rankdata(a), rankdata(b)) if rank else (a.copy(), b.copy())
    centered = "cosine" not in title.lower() and "angular" not in title.lower()
    if centered: aa, bb = aa - aa.mean(), bb - bb.mean()
    terms = aa * bb / (np.linalg.norm(aa) * np.linalg.norm(bb))
    corr = float(np.clip(terms.sum(), -1, 1))
    frames = []
    for k in np.linspace(3, len(a), 4, dtype=int):
        frames.append(_frame(0, "Compare paired observations on the same time grid",
            {"kind": "scatter", "title": "Paired observations: x versus y", "a": _floats(a[:k]), "b": _floats(b[:k]), "marker": k - 1}))
    for k in np.linspace(3, len(aa), 4, dtype=int):
        frames.append(_frame(1, "Average ranks, then center" if rank else ("Center each vector" if centered else "Keep vector directions; do not center"),
            _lines(aa[:k], bb[:k], title="Centered ranks" if rank else ("Centered coordinates" if centered else "Uncentered vectors"))))
    for k in np.linspace(1, len(terms), 8, dtype=int):
        partial = terms.copy(); partial[k:] = 0.0
        frames.append(_frame(2, "Accumulate normalized products using fixed full-vector norms",
            _bars(partial, title="Contribution to normalized dot product", marker=k - 1), float(terms[:k].sum()), "partial normalized dot product"))
    value = transform(corr)
    for k in np.linspace(0, len(a) - 1, 4, dtype=int):
        frames.append(_frame(3, final_label, _bars(terms, title="All normalized coordinate products", marker=k), value, "final result"))
    return frames, value


def _kendall_trace(x, y, *, distance: bool = False) -> tuple[list[dict], float]:
    x, y = np.asarray(x), np.asarray(y)
    pairs = list(combinations(range(len(x)), 2))
    categories = []
    signs = []
    for i, j in pairs:
        dx, dy = np.sign(x[j] - x[i]), np.sign(y[j] - y[i])
        signs.append(float(dx * dy))
        categories.append(0 if dx * dy > 0 else 1 if dx * dy < 0 else 2 if dx == 0 and dy != 0 else 3 if dy == 0 and dx != 0 else 4)
    frames = []
    for k in np.linspace(3, len(x), 4, dtype=int):
        frames.append(_frame(0, "Kendall compares ordering across pairs of observations",
            {"kind": "scatter", "title": "Paired observations", "a": _floats(x[:k]), "b": _floats(y[:k]), "marker": k - 1}))
    for k in np.linspace(1, len(pairs), 4, dtype=int):
        z = [[None] * len(x) for _ in x]
        for (i, j), sign in zip(pairs[:k], signs[:k]): z[i][j] = sign
        frames.append(_frame(1, "Pair signs: +1 concordant, -1 discordant, 0 tied",
            {"kind": "matrix", "title": "Pairwise order agreement", "z": z, "row_label": "earlier index", "col_label": "later index", "cursor": list(pairs[k - 1])}))
    for k in np.linspace(1, len(pairs), 8, dtype=int):
        counts = np.bincount(categories[:k], minlength=5)
        frames.append(_frame(2, "Count agreements, disagreements and one-sided ties",
            _bars(counts[:4], title="Counts over examined pairs", labels=["C", "D", "tie x", "tie y"])))
    c, d, tx, ty, _ = np.bincount(categories, minlength=5)
    tau = float((c - d) / math.sqrt((c + d + tx) * (c + d + ty)))
    assert np.isclose(tau, kendalltau(x, y).statistic)
    value = 1.0 - tau if distance else tau
    for k in range(4):
        frames.append(_frame(3, "Return 1 - tie-adjusted tau-b" if distance else "Normalize net agreement with tau-b tie correction",
            _bars([c, d, tx, ty], title="Final counts used by tau-b", labels=["C", "D", "tie x", "tie y"], marker=k), value, "1 - tau-b" if distance else "tau-b"))
    return frames, value


def _correlation_examples() -> list[dict]:
    out = []
    x = np.array([1., 2., 2., 4., 3., 5., 5., 7., 8., 6., 9., 10.])
    y = np.array([1., 1.8, 2.2, 3.4, 2.7, 4.1, 4.1, 6.4, 6.1, 5.5, 8., 9.2])
    for family, variants in (("cosine", ["cosine_similarity", "cosine_distance", "angular_distance"]),
                             ("pearson", ["pearson_similarity", "pearson_distance"]),
                             ("spearman", ["spearman_similarity", "spearman_distance"]),
                             ("kendall", ["kendall_similarity", "kendall_distance"])):
        for name in variants:
            distance = name.endswith("distance")
            angular = name == "angular_distance"
            transform = (lambda s: math.acos(float(np.clip(s, -1, 1))) / math.pi) if angular else ((lambda s: 1 - s) if distance else float)
            final_label = "Apply arccos and divide by pi" if angular else ("Subtract similarity from one" if distance else "Read the signed agreement coefficient")
            if family == "kendall": frames, value = _kendall_trace(x, y, distance=distance)
            else: frames, value = _corr_trace(x, y, title=family, transform=transform, final_label=final_label, rank=family == "spearman")
            if family == "cosine":
                title = "Angular distance" if angular else ("Cosine distance" if distance else "Cosine similarity")
                intro_en = "Cosine comparison uses the angle between two complete sample vectors. It divides their dot product by both vector norms and leaves the mean level intact. The animation shows the signed coordinate products and their norm-scaled accumulation, then applies the selected angular or one-minus transform when this card reports a distance."
                intro_zh = "余弦比较使用完整采样向量之间的夹角，以两向量范数乘积归一化点积，并保留均值水平。动图展示带符号坐标乘积及归一化累加；距离型条目随后应用反余弦或 1 减相似度变换。"
                formula = "acos(cos(x,y))/pi" if angular else ("1 - dot(x,y)/(||x||_2 ||y||_2)" if distance else "dot(x,y)/(||x||_2 ||y||_2)")
                steps = ["Keep each full sample vector without mean subtraction.", "Compute vector norms and coordinate-wise products.", "Divide the product sum by the product of the two norms.", final_label + "."]
                steps_zh = ["保留完整采样向量，不去均值。", "计算向量范数和逐坐标乘积。", "以范数乘积归一化点积。", "应用所示最终变换得到分数。"]
                caveats = ["Zero-norm vectors have no defined angle; this example excludes them.", "Positive scaling is removed but an additive offset changes the direction.", "The normalized angular form is a metric on unit directions; 1-cosine generally fails the triangle inequality."]
                caveats_zh = ["零范数向量的夹角未定义，本例不包含此情形。", "正缩放被消除，但加性偏移会改变方向。", "归一化角距离在单位方向上是度量；1−余弦一般不满足三角不等式。"]
                sources = [_scipy("cosine")]
            elif family == "pearson":
                title = "Pearson distance" if distance else "Pearson correlation"
                intro_en = "Pearson correlation measures linear co-variation of aligned observations after centering both vectors. The animation reveals each centered-product contribution and normalizes by the full centered norms. Positive correlation, anticorrelation and weak linear association remain different outcomes; a distance card applies the explicit one-minus transform to the same coefficient."
                intro_zh = "Pearson 相关衡量对齐观测去均值后的线性协同变化。动图逐项展示中心化乘积，再用完整中心化向量的范数归一化。正相关、负相关和弱线性关系具有不同含义；距离条目显式使用 1 减相关系数。"
                formula = ("1 - " if distance else "") + "corr(x,y)"
                steps = ["Pair observations at the same sample index.", "Subtract the mean from each series independently.", "Sum centered products and divide by centered vector norms.", final_label + "."]
                steps_zh = ["按相同采样位置配对观测。", "分别减去各自均值。", "累加中心化乘积并按范数归一化。", "读取相关系数或其 1 减变换。"]
                caveats = ["Constant inputs have undefined statistical correlation; zero-return conventions are software-specific.", "Correlation describes linear dependence, not matching units or causal influence.", "1-r is a dissimilarity and generally fails the triangle inequality."]
                caveats_zh = ["常量输入的统计相关未定义；返回零属于软件约定。", "相关描述线性依赖，不代表单位相同或因果作用。", "1−r 属于差异量，一般不满足三角不等式。"]
                sources = [_scipy("correlation")]
            elif family == "spearman":
                title = "Spearman distance" if distance else "Spearman rank correlation"
                intro_en = "Spearman correlation replaces amplitudes by their ranks and then computes Pearson correlation of those ranks. Tied observations receive average ranks in this example. The animation makes this change of representation explicit: a monotone nonlinear amplitude transformation can retain rank agreement even when the raw scatter is not a straight line."
                intro_zh = "Spearman 相关先把幅值转换成排名，再计算排名的 Pearson 相关。本例对并列值使用平均排名。动图显式展示表示变换：单调非线性幅值变换即使改变原始散点的线性关系，仍可能保留排名一致性。"
                formula = ("1 - " if distance else "") + "corr(rank_average(x),rank_average(y))"
                steps = ["Pair observations and retain their original sample identities.", "Replace amplitudes with average ranks, including ties.", "Compute Pearson correlation of the two rank vectors.", final_label + "."]
                steps_zh = ["配对观测并保留原始采样身份。", "将幅值替换为含并列处理的平均排名。", "计算两组排名的 Pearson 相关。", "读取排名相关或其 1 减变换。"]
                caveats = ["Amplitude differences are intentionally discarded by ranking.", "A nonmonotone dependence may be strong while Spearman correlation is weak.", "The chosen tie rule and missing-value handling belong to the definition."]
                caveats_zh = ["排名主动舍弃幅值差异。", "强非单调依赖也可能具有很弱的 Spearman 相关。", "并列排名和缺失值处理属于定义的一部分。"]
                sources = [_scipy("spearmanr", stats=True)]
            else:
                title = "Kendall distance" if distance else "Kendall tau-b"
                intro_en = "Kendall tau-b compares the ordering of every pair of aligned observations. Concordant and discordant pairs contribute with opposite signs, while one-sided ties alter the normalization. The animation exposes the pairwise sign matrix and count table. This implementation uses tau-b, so its treatment of ties is not replaced by a no-ties shortcut."
                intro_zh = "Kendall tau-b 比较每对对齐观测的顺序关系。同序和逆序配对贡献相反符号，单侧并列值改变归一化。动图展示配对符号矩阵与计数表，使用含并列校正的 tau-b，不用无并列情形的简化公式替代。"
                formula = ("1 - " if distance else "") + "(C-D)/sqrt((C+D+T_x)*(C+D+T_y))"
                steps = ["Enumerate unordered observation pairs.", "Classify each pair as concordant, discordant or tied.", "Count one-sided ties separately; joint ties enter neither tie term.", "Apply tau-b normalization, then 1-tau if this is the distance variant."]
                steps_zh = ["枚举无序观测配对。", "判断同序、逆序或并列。", "分别统计单侧并列；双侧并列不进入单侧并列项。", "应用 tau-b 归一化；距离型再取 1−tau。"]
                caveats = ["Ordering does not preserve the magnitude of differences.", "A zero normalization denominator leaves tau undefined; the illustration avoids this case.", "The animated pair enumeration is educational; optimized software need not enumerate all pairs explicitly."]
                caveats_zh = ["顺序关系不保留差异幅度。", "归一化分母为零时 tau 未定义，本例避开此情形。", "动画显式枚举配对用于教学；优化软件无需逐对枚举。"]
                sources = [_scipy("kendalltau", stats=True)]
            out.append(_card(name, title, "lock-step", x, y, intro_en=intro_en, intro_zh=intro_zh,
                steps_en=steps, steps_zh=steps_zh, formula=formula, caveats_en=caveats, caveats_zh=caveats_zh,
                sources=sources, parameters={"centering": family != "cosine", "ranking": family in {"spearman", "kendall"}, "tie_rule": "average rank or tau-b correction" if family in {"spearman", "kendall"} else "not applicable"},
                value=value, frames=frames, kind="distance" if distance else "similarity"))
    return out


def _distribution_examples() -> list[dict]:
    counts_x = np.array([1., 3., 6., 9., 7., 4., 2., 1.])
    counts_y = np.array([1., 2., 3., 6., 9., 7., 4., 2.])
    p = counts_x / counts_x.sum(); q = counts_y / counts_y.sum(); m = (p + q) / 2
    specs = {
        "jensen_shannon": ("Jensen-Shannon distance", .5 * p * np.log(p / m) + .5 * q * np.log(q / m), math.sqrt,
            "sqrt(0.5*KL(p||m)+0.5*KL(q||m)); m=(p+q)/2; natural logarithm",
            "Jensen-Shannon distance compares two probability vectors through their midpoint distribution. Each side contributes a KL divergence to that midpoint, the two values are averaged, and the square root produces the distance shown here. The animated bins share a fixed support; their positions describe probability mass rather than a time-warping alignment.",
            "Jensen-Shannon 距离以两概率向量的中点分布作为共同参照，平均两侧到中点的 KL 散度，再开平方。本动画使用固定共同支持集；横轴位置表示概率质量所在的箱，而不是时间规整的匹配位置。",
            "Compute each bin's two-sided KL-to-midpoint contribution", "Take the square root of the averaged divergence",
            ["This card shows the square root, not raw JS divergence.", "Logarithm base changes the scale; natural logs are used here."],
            ["本条目展示平方根形式，并非原始 JS 散度。", "对数底改变数值尺度，本例使用自然对数。"], [_scipy("jensenshannon")]),
        "kl_divergence": ("Kullback-Leibler divergence", p * np.log(p / q), float,
            "KL(p||q)=sum_i p_i*log(p_i/q_i); natural logarithm",
            "KL divergence weights each log probability ratio by the mass of the first distribution. Individual bin contributions can be negative even though the complete divergence is nonnegative. The animation retains those signed contributions and a declared direction p to q. Changing the order of the distributions generally changes the answer.",
            "KL 散度用第一个分布的概率质量加权对数概率比。单箱贡献可以为负，而完整散度非负。动画保留这些带符号贡献，并明确方向为 p 到 q；交换两分布通常改变结果。",
            "Weight log(p/q) by p", "Add signed bin terms in the declared p-to-q direction",
            ["If p is positive where q is zero, KL is infinite; both vectors here are strictly positive.", "KL is asymmetric and does not obey the metric triangle inequality."],
            ["若 p 在 q 为零处为正，KL 为无穷；本例两侧均严格为正。", "KL 不对称，也不满足度量三角不等式。"], [_scipy("entropy", stats=True)]),
        "jeffreys_divergence": ("Jeffreys divergence", (p - q) * np.log(p / q), float,
            "KL(p||q)+KL(q||p)=sum_i (p_i-q_i)*log(p_i/q_i)",
            "Jeffreys divergence adds KL divergences in both directions. On strictly positive probabilities the two terms combine into a per-bin product of the probability difference and its log ratio. The animation shows this symmetric contribution directly. Symmetrizing KL removes its directional asymmetry while leaving a divergence whose metric properties need separate analysis.",
            "Jeffreys 散度相加两个方向的 KL 散度。概率严格为正时，可逐箱写成概率差与对数比的乘积。动图直接展示该对称贡献；对称化消除了方向不对称，但不能自动赋予其度量性质。",
            "Combine KL terms in both directions", "Sum the symmetric log-ratio contributions",
            ["Symmetry alone does not establish a metric.", "A support mismatch can make the result infinite; no smoothing is hidden in this illustration."],
            ["对称性本身不能证明度量性质。", "支持集不匹配可能使结果无穷；本例没有隐藏平滑。"], [_scipy("entropy", stats=True), _source("Imported registry: two-sided KL convention", REGISTRY)]),
        "bhattacharyya_distance": ("Bhattacharyya distance", np.sqrt(p * q), lambda s: -math.log(s),
            "-log(sum_i sqrt(p_i*q_i))",
            "Bhattacharyya distance first adds the geometric-mean overlap of corresponding probability masses. It then applies a negative logarithm, so greater overlap gives a smaller distance. The animation separates the overlap coefficient from the final transformed score. The supplied positive distributions overlap everywhere, making the logarithm finite without a numerical floor.",
            "Bhattacharyya 距离先累加对应概率质量的几何平均重叠，再取负对数，使更大重叠对应更小距离。动画区分重叠系数和最终变换结果。本例各箱概率为正，无需数值下限即可保证对数有限。",
            "Compute geometric-mean overlap in each bin", "Apply negative log to the full overlap coefficient",
            ["Disjoint support gives zero overlap and infinite distance.", "This log-overlap quantity generally lacks the triangle inequality."],
            ["支持集不相交时重叠为零、距离为无穷。", "该负对数重叠量一般不满足三角不等式。"], [_source("Imported registry: overlap definition", REGISTRY)]),
        "hellinger_distance": ("Hellinger distance", .5 * (np.sqrt(p) - np.sqrt(q)) ** 2, math.sqrt,
            "sqrt(0.5*sum_i (sqrt(p_i)-sqrt(q_i))^2)",
            "Hellinger distance compares square-root probability vectors using a scaled Euclidean distance. The animation shows how transforming probabilities changes the coordinate gaps before squaring and accumulation. The factor one half inside the root fixes the common zero-to-one normalization. Shared bin definitions are essential because each square-root mass is compared with its corresponding bin.",
            "Hellinger 距离对概率开平方后，计算缩放的欧氏距离。动画展示变换如何改变坐标差，再平方累加。根号内的二分之一确定常见的 0 到 1 归一化。每个概率质量必须对应相同的箱定义。",
            "Square the difference between square-root masses; divide by two", "Take the square root of the accumulated contributions",
            ["This convention includes the factor 1/sqrt(2); some sources omit it.", "A distance between histograms does not preserve the temporal order that generated them."],
            ["此约定包含 1/√2 因子，部分资料会省略。", "直方图间距离不保留生成它们的原始时间顺序。"], [_source("Imported registry: normalized Hellinger formula", REGISTRY)]),
        "chi_square_distance": ("Symmetric chi-square distance", .5 * (p - q) ** 2 / (p + q), float,
            "0.5*sum_i (p_i-q_i)^2/(p_i+q_i)",
            "This symmetric chi-square histogram distance divides squared probability differences by the combined mass of each bin, then sums half of those ratios. Small-mass bins can matter disproportionately relative to unweighted squared error. The animation follows the exact symmetric convention in the registry; it does not perform a statistical chi-square hypothesis test.",
            "此对称卡方直方图距离用每箱概率和归一化平方概率差，再累加其一半。低概率箱相较无权平方误差可能获得更高影响。动画遵循登记表的对称定义，不进行卡方假设检验。",
            "Divide squared bin differences by combined probability mass", "Sum half of the mass-scaled squared differences",
            ["The name also denotes other asymmetric distances and test statistics; use the displayed formula.", "A zero-over-zero bin needs an explicit zero contribution convention."],
            ["该名称还用于非对称距离和检验统计量，应以所示公式为准。", "两侧均为零的箱需要显式约定贡献为零。"], [_source("Imported registry: symmetric chi-square convention", REGISTRY)]),
    }
    out = []
    for name, spec in specs.items():
        title, terms, finish, formula, en, zh, local_step, final_step, caveats, caveats_zh, sources = spec
        value = finish(float(terms.sum()))
        if name == "jensen_shannon": assert np.isclose(value, sd.jensenshannon(p, q))
        if name == "kl_divergence": assert np.isclose(value, entropy(p, q))
        a, b = (np.sqrt(p), np.sqrt(q)) if name == "hellinger_distance" else (p, q)
        frames = _sum_trace(a, b, terms, finish, term_label=local_step, final_label=final_step,
                            prep_label="Square-root probability vectors" if name == "hellinger_distance" else "Probability mass on shared bins")
        card = _card(name, title, "lock-step", counts_x, counts_y, intro_en=en, intro_zh=zh,
            steps_en=["Declare one shared bin support and normalize nonnegative mass to sum to one.", local_step + ".", "Accumulate the displayed bin contributions, retaining any signed terms.", final_step + "."],
            steps_zh=["声明共同箱支持集，将非负质量归一化为概率。", "按该方法公式计算逐箱贡献。", "累加所示贡献，保留可能出现的符号。", "应用所示最后的根号、对数或直接求和。"],
            formula=formula, caveats_en=caveats, caveats_zh=caveats_zh, sources=sources,
            parameters={"probability_p": _floats(p), "probability_q": _floats(q), "log_base": "e", "smoothing": "none", "support": "eight shared illustrative bins"},
            value=value, frames=frames, kind="divergence" if "divergence" in name else "distance")
        card["input_label"] = "Synthetic counts on eight shared bins; these bins are not timestamps."
        out.append(card)
    return out


def _overlap_indices(n: int, m: int, lag: int) -> tuple[np.ndarray, np.ndarray]:
    indices = np.arange(n)
    keep = (indices - lag >= 0) & (indices - lag < m)
    return indices[keep], indices[keep] - lag


def _alignment_panel(x, y, lag: int, *, title: str) -> dict:
    a, b = _overlap_indices(len(x), len(y), lag)
    return {"kind": "alignment", "title": title, "a": _floats(x), "b": _floats(y),
            "pairs": [[int(i), int(j)] for i, j in zip(a, b)]}


def _sliding_examples() -> list[dict]:
    from echotime.similarity_methods import independent_max_ncc, independent_sbd, max_ncc, ncc_sequence, sbd

    x = np.array([0., .1, .8, 2.1, 1.4, .3, -.2, -.1, .1, 0.])
    y = np.r_[0., 0., x[:-2]] + .03 * np.sin(np.arange(len(x)))
    out = []
    zx, zy = _z(x), _z(y)
    lags = np.arange(-(len(y) - 1), len(x))
    manual_scores = []
    denom = float(np.linalg.norm(zx) * np.linalg.norm(zy))
    for lag in lags:
        i, j = _overlap_indices(len(x), len(y), int(lag))
        manual_scores.append(float(np.dot(zx[i], zy[j]) / denom))
    scores = np.asarray(manual_scores)
    api_scores, api_lags = ncc_sequence(x, y)
    assert np.array_equal(lags, api_lags) and np.allclose(scores, api_scores)
    for name in ("max_normalized_cross_correlation", "sbd"):
        is_distance = name == "sbd"
        value = 1.0 - float(scores.max()) if is_distance else float(scores.max())
        actual = sbd(x, y) if is_distance else max_ncc(x, y)
        assert np.isclose(value, actual)
        frames = []
        for k in np.linspace(3, len(x), 4, dtype=int):
            frames.append(_frame(0, "Z-normalize each full series once before the lag scan",
                _lines(zx[:k], zy[:k], title="Global z-normalization, fixed for every lag")))
        for k, lag in enumerate(lags):
            frames.append(_frame(1 if k < len(lags) // 2 else 2,
                f"Lag {int(lag):+d}: overlap product / fixed full-series norms",
                _alignment_panel(zx, zy, int(lag), title=f"Lag {int(lag):+d}; unmatched values contribute zero"),
                float(scores[k]), "NCC at this lag"))
        best = int(np.argmax(scores))
        for k in range(4):
            frames.append(_frame(3, "Return one minus the largest NCC" if is_distance else "Keep the largest normalized cross-correlation",
                _lines(scores, title="Complete lag profile; marker is the selected shift", x=lags, marker=best,
                       a_label="NCC"), value, "SBD" if is_distance else "maximum NCC"))
        card = _card(name, "Shape-based distance (SBD)" if is_distance else "Maximum normalized cross-correlation",
            "sliding", x, y,
            intro_en=("SBD transforms the best normalized cross-correlation into a dissimilarity by subtracting it from one. " if is_distance else "Maximum NCC finds the global integer shift with the largest normalized cross-correlation. ") +
                     "EchoTime first z-normalizes each full series, then uses full-series norms at every lag. The animation shows overlap pairs and the complete lag profile, including the reduced overlap near the boundaries.",
            intro_zh=("SBD 将最大的归一化互相关从 1 中减去，形成差异量。" if is_distance else "最大 NCC 寻找归一化互相关最大的全局整数平移。") +
                     "EchoTime 先对完整序列分别进行 Z 标准化，再在每个滞后位置使用固定的完整序列范数。动画显示重叠配对与完整滞后曲线，包括边界附近的较短重叠。",
            steps_en=["Z-normalize both complete series once.", "Slide through all integer lags and match only overlapping samples.",
                      "Divide each overlap dot product by the same full-series norm product.",
                      "Subtract the best NCC from one." if is_distance else "Select the largest NCC and record its lag."],
            steps_zh=["对两条完整序列分别进行 Z 标准化。", "遍历整数滞后，仅匹配重叠样本。", "以固定的完整序列范数乘积归一化各重叠点积。", "用 1 减去最大 NCC。" if is_distance else "选取最大 NCC 并记录滞后。"],
            formula=("1 - " if is_distance else "") + "max_lag sum_overlap z(x)[i]*z(y)[i-lag] / (||z(x)||_2*||z(y)||_2)",
            caveats_en=["This is a global shift, not local time warping.", "Full-norm zero-padding NCC differs from Pearson or cosine re-normalized on each overlap.", "Constant series have undefined statistical correlation; EchoTime retains a zero-NCC convention for zero energy."],
            caveats_zh=["这里估计全局平移，不进行局部时间规整。", "固定全范数的补零 NCC 与在各重叠片段重新归一化的 Pearson 或余弦不同。", "常量信号的统计相关未定义；EchoTime 对零能量保留零 NCC 的约定。"],
            sources=[_source("EchoTime: ncc_sequence, max_ncc and sbd", LOWLEVEL), _source("k-Shape original paper: shape-based cross-correlation", KSHAPE)],
            parameters={"normalize": True, "padding": "zero outside overlap", "normalization": "full-series norm product", "lags": [int(l) for l in lags], "selected_lag": int(lags[best])},
            value=value, frames=frames, kind="distance" if is_distance else "similarity", definition="echotime")
        card["checks"] = {"api": "sbd" if is_distance else "max_ncc", "expected": value, "observed": float(actual), "tolerance": 1e-12}
        out.append(card)

    bounded_lags = np.arange(-3, 4)
    specs = [
        ("shift_euclidean_distance", "Shifted Euclidean", "sqrt(sum of squared overlap errors)", lambda a, b: float(np.linalg.norm(a - b)), False,
         "The unnormalized total can favour lags with fewer overlapping points.", "未归一化总量可能偏向重叠点较少的滞后。"),
        ("shift_rmse_distance", "Shifted RMSE", "sqrt(mean of squared overlap errors)", lambda a, b: float(np.sqrt(np.mean((a - b) ** 2))), False,
         "Averaging adjusts for overlap length but a tiny overlap can still give an unstable optimum.", "平均化调整了重叠长度影响，但很短的重叠仍可能产生不稳定最优点。"),
        ("shift_manhattan_distance", "Shifted Manhattan", "sum of absolute overlap errors", lambda a, b: float(np.abs(a - b).sum()), False,
         "The unnormalized L1 total changes with overlap size; restrict admissible lags.", "未归一化 L1 总量随重叠数量变化，应限制允许的滞后。"),
        ("shift_mae_distance", "Shifted MAE", "mean absolute overlap error", lambda a, b: float(np.abs(a - b).mean()), False,
         "Per-overlap averaging does not guarantee a stable estimate on very short overlaps.", "对重叠片段求平均不能保证短片段上的估计稳定。"),
        ("shift_cosine_similarity", "Shifted cosine similarity", "cosine on the current overlap", lambda a, b: float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))), True,
         "Every overlap has its own norm; this is different from full-norm NCC.", "每个重叠片段使用自己的范数，与全范数 NCC 不同。"),
        ("shift_cosine_distance", "Shifted cosine distance", "cosine on the current overlap", lambda a, b: float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))), True,
         "The one-minus transform does not establish a metric on raw time series.", "1 减变换不能自动证明原时间序列上的度量性质。"),
        ("shift_pearson_similarity", "Shifted Pearson correlation", "Pearson r on the current overlap", lambda a, b: float(np.corrcoef(a, b)[0, 1]), True,
         "Each overlap is independently centered; selecting the best lag also selects among several correlations.", "每个重叠片段分别去均值；选取最佳滞后同时也是在多个相关结果中选择。"),
        ("shift_pearson_distance", "Shifted Pearson distance", "Pearson r on the current overlap", lambda a, b: float(np.corrcoef(a, b)[0, 1]), True,
         "One minus the selected correlation is an explicit dissimilarity, not a probability or significance test.", "1 减选定相关是明确的差异量，并非概率或显著性检验。"),
    ]
    # Positive offset avoids zero-norm overlaps for the cosine examples, while
    # a bounded lag range leaves at least seven samples in every overlap.
    sx, sy = x + 1.0, y + 1.0
    for name, title, operation, scorer, maximize, caution, caution_zh in specs:
        vals = []
        for lag in bounded_lags:
            i, j = _overlap_indices(len(sx), len(sy), int(lag))
            vals.append(scorer(sx[i], sy[j]))
        vals = np.asarray(vals)
        best = int(np.argmax(vals) if maximize else np.argmin(vals))
        complement = name in {"shift_cosine_distance", "shift_pearson_distance"}
        value = 1.0 - float(vals[best]) if complement else float(vals[best])
        frames = []
        for k in np.linspace(3, len(sx), 4, dtype=int):
            frames.append(_frame(0, "Use the declared bounded lag window: -3 to +3 samples",
                _lines(sx[:k], sy[:k], title="Original input; no hidden standardization")))
        for lag, v in zip(bounded_lags, vals):
            frames.append(_frame(1, f"Lag {int(lag):+d}: {operation}",
                _alignment_panel(sx, sy, int(lag), title=f"Overlap correspondence at lag {int(lag):+d}"), v, "current overlap score"))
        for k in range(len(vals)):
            selected = float(np.max(vals[:k + 1]) if maximize else np.min(vals[:k + 1]))
            frames.append(_frame(2, "Compare scores only over the admitted lag window",
                _lines(vals[:k + 1], title="Candidate score versus lag", x=bounded_lags[:k + 1], marker=k, a_label="overlap score"), selected, "best candidate so far"))
        for k in range(4):
            frames.append(_frame(3, "Select the largest score, then apply 1-score" if complement else ("Select the largest overlap similarity" if maximize else "Select the smallest overlap error"),
                _lines(vals, title="Complete bounded lag scan", x=bounded_lags, marker=best, a_label="candidate score"), value, "final result"))
        is_cos = "cosine" in name; is_pearson = "pearson" in name
        numerator = "cosine(x_overlap,y_overlap)" if is_cos else "corr(x_overlap,y_overlap)" if is_pearson else {
            "shift_euclidean_distance": "||x_overlap-y_overlap||_2", "shift_rmse_distance": "sqrt(mean((x_overlap-y_overlap)^2))",
            "shift_manhattan_distance": "||x_overlap-y_overlap||_1", "shift_mae_distance": "mean(abs(x_overlap-y_overlap))"}[name]
        formula = ("1 - " if complement else "") + ("max" if maximize else "min") + "_{lag=-3,...,3} " + numerator
        card = _card(name, title, "sliding", sx, sy,
            intro_en=f"{title} evaluates {operation} after each permitted integer shift, using only samples that overlap. This example admits lags from minus three to plus three samples, leaving at least seven paired observations. The animation shows the actual overlap pairs and candidate scores before selecting their {'maximum' if maximize else 'minimum'}." + (" The final one-minus transform produces the displayed dissimilarity." if complement else ""),
            intro_zh=f"{title} 在每个允许的整数平移后，仅对重叠样本计算对应分数。本例滞后范围为 −3 至 +3 个采样点，始终保留至少七对观测。动图展示实际配对和候选分数，再选择{'最大' if maximize else '最小'}值。" + ("最后取 1 减分数得到差异量。" if complement else ""),
            steps_en=["Fix the permitted lags and minimum acceptable overlap before scoring.", f"At each lag, compute {operation} on the actual paired samples.",
                      "Record every candidate score together with its lag.", "Choose the maximum and apply 1-score." if complement else ("Choose the maximum overlap score." if maximize else "Choose the minimum overlap score.")],
            steps_zh=["先固定允许滞后与最小可接受重叠长度。", "对每个滞后的实际配对样本计算对应分数。", "记录所有候选分数及其滞后。", "选择最大分数后取 1 减。" if complement else ("选取最大重叠分数。" if maximize else "选取最小重叠分数。")],
            formula=formula, caveats_en=[caution, "The bounded window is an explicit demonstration choice; allowing every possible lag changes the problem.", "Overlap cropping removes unmatched endpoints from this score."],
            caveats_zh=[caution_zh, "有界窗口是明确的演示选择；允许所有滞后会改变问题。", "重叠裁剪会从分数中排除未匹配的两端。"],
            sources=[_source("Imported registry: overlap-based shift definitions", REGISTRY), _scipy("correlation" if is_pearson else "cosine" if is_cos else "euclidean" if "euclidean" in name or "rmse" in name else "cityblock")],
            parameters={"lags": [int(l) for l in bounded_lags], "minimum_overlap": 7, "normalization": "per overlap" if maximize else "none beyond stated mean/root", "selected_lag": int(bounded_lags[best])},
            value=value, frames=frames, kind="similarity" if name.endswith("similarity") else "distance")
        out.append(card)

    x2 = np.array([.2, .9, 1.8, 1.2, .1, -.6, -.3, .4, .8, .2])
    y2 = np.r_[x2[2:], 0., 0.] + .02 * np.cos(np.arange(len(x2)))
    channels_x = np.column_stack([x, x2]); channels_y = np.column_stack([y, y2])
    ncc0, lags0 = ncc_sequence(x, y); ncc1, lags1 = ncc_sequence(x2, y2)
    peaks = np.array([max(ncc0), max(ncc1)], dtype=float)
    mean_peak = float(peaks.mean())
    for name in ("independent_max_ncc", "independent_sbd"):
        distance = name == "independent_sbd"
        value = 1 - mean_peak if distance else mean_peak
        observed = independent_sbd(channels_x, channels_y) if distance else independent_max_ncc(channels_x, channels_y)
        assert np.isclose(value, observed)
        frames = []
        for channel in range(2):
            for k in (5, 10):
                frames.append(_frame(0, f"Normalize channel {channel + 1} independently",
                    _lines(_z(channels_x[:, channel])[:k], _z(channels_y[:, channel])[:k], title=f"Channel {channel + 1}: separate z-normalized input")))
        for channel, prof in enumerate((ncc0, ncc1)):
            for k in np.linspace(0, len(lags0) - 1, 8, dtype=int):
                frames.append(_frame(channel + 1, f"Channel {channel + 1} chooses its own lag; current lag {int(lags0[k]):+d}",
                    _lines(prof, title=f"NCC lag profile of channel {channel + 1}", x=lags0, marker=k, a_label=f"channel {channel + 1}"), float(prof[k]), "channel NCC"))
        for k in range(4):
            frames.append(_frame(3, "Average the channel-wise SBD values" if distance else "Average each channel's maximum NCC",
                _bars(1 - peaks if distance else peaks, title="Each channel keeps its own best shift", labels=["channel 1", "channel 2"], marker=k % 2), value, "channel mean"))
        card = _card(name, "Independent channel SBD" if distance else "Independent channel maximum NCC", "sliding", x, y,
            intro_en="Independent channel comparison permits each paired channel to choose a different global lag. The illustration uses two channels with peaks shifted in opposite directions, then averages their individually optimized scores. " + ("For SBD it averages one minus each channel's maximum NCC." if distance else "For independent maximum NCC it averages the channel maxima.") + " The upper input plot shows channel one; both channels are displayed in the computational frames.",
            intro_zh="独立通道比较允许每对通道选择不同的全局滞后。本例使用两组峰值向相反方向偏移的通道，再平均各自优化后的分数。" + ("SBD 型平均每个通道的 1 减最大 NCC。" if distance else "最大 NCC 型直接平均各通道最大值。") + "上方输入图显示第一通道，计算帧依次展示两个通道。",
            steps_en=["Match channels explicitly and normalize each series within each channel.", "Compute the full-norm NCC lag profile for channel one.", "Repeat the lag scan independently for channel two.", "Average channel-wise dissimilarities." if distance else "Average the maxima; no common lag is required."],
            steps_zh=["明确通道配对，并在每个通道内分别标准化。", "计算第一通道的全范数 NCC 滞后曲线。", "独立计算第二通道的滞后曲线。", "平均通道差异量。" if distance else "平均各通道最大值，不要求共同滞后。"],
            formula="mean_c (1-max_lag NCC_c(lag))" if distance else "mean_c max_lag NCC_c(lag)",
            caveats_en=["Independent lags discard cross-channel timing consistency; choose a joint-lag method if synchrony matters.", "Channels are averaged equally here; this is not a learned weighting.", "The channel pairing must have a scientific meaning."],
            caveats_zh=["独立滞后舍弃跨通道时序一致性；同步关系重要时应使用共同滞后的方法。", "本例对通道等权平均，不学习权重。", "通道配对必须有科学意义。"],
            sources=[_source("EchoTime: independent_max_ncc and independent_sbd", LOWLEVEL)],
            parameters={"channels_x": channels_x.tolist(), "channels_y": channels_y.tolist(), "upper_plot_channel": 0, "channel_best_lags": [int(lags0[np.argmax(ncc0)]), int(lags1[np.argmax(ncc1)])], "aggregation": "equal channel mean"},
            value=value, frames=frames, kind="distance" if distance else "similarity", definition="echotime")
        card["input_label"] = "Upper traces: first of two explicitly recorded channels; both appear in the animation."
        card["checks"] = {"api": name, "expected": value, "observed": float(observed), "tolerance": 1e-12}
        out.append(card)
    return out


def _absolute_dtw_trace(a: np.ndarray, b: np.ndarray, window: int) -> tuple[np.ndarray, list[list[int]], float]:
    n, m = len(a), len(b)
    d = np.full((n + 1, m + 1), np.inf); d[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(max(1, i - window), min(m, i + window) + 1):
            d[i, j] = abs(a[i - 1] - b[j - 1]) + min(d[i - 1, j], d[i, j - 1], d[i - 1, j - 1])
    path = []
    i, j = n, m
    while i and j:
        path.append([i - 1, j - 1])
        choices = [(d[i - 1, j - 1], i - 1, j - 1), (d[i - 1, j], i - 1, j), (d[i, j - 1], i, j - 1)]
        _, i, j = min(choices, key=lambda row: row[0])
    return d[1:, 1:], list(reversed(path)), float(d[n, m] / (n + m))


def _matrix_rows(values: np.ndarray, rows: int) -> list[list[float | None]]:
    return [[float(v) if i < rows and np.isfinite(v) else None for v in row]
            for i, row in enumerate(values)]


def _native_examples() -> list[dict]:
    from scipy.signal import savgol_filter
    from echotime.similarity import compare_series, _resampled_multichannel
    from echotime.metrics import _normalized_spectrum

    raw_x = np.array([0., .3, .9, 1.8, 2.7, 2.1, 1.5, 1.1, 1.3, 2., 2.8, 3.4,
                      3., 2.4, 2.1, 2.5, 3.4, 4.2, 4.4, 4., 3.7, 3.9, 4.8, 5.2])
    raw_y = .8 * raw_x + 1.5 + .35 * np.sin(np.arange(len(raw_x)) * 1.1)
    n = len(raw_x)
    report = compare_series(raw_x, raw_y, n_points=n)
    x = _resampled_multichannel(raw_x, n_points=n)[:, 0]
    y = _resampled_multichannel(raw_y, n_points=n)[:, 0]
    dx, dy = _z(np.diff(x)), _z(np.diff(y))
    r_level = float(np.corrcoef(x, y)[0, 1]); r_diff = float(np.corrcoef(dx, dy)[0, 1])
    clip = lambda v: float(np.clip(v, 0, 1))
    geom = lambda a, b: math.sqrt(clip(a) * clip(b))
    parameters = {"n_points": n, "default_n_points": 256, "channels": 1,
                  "preprocessing": "compare_series linear resampling followed by per-channel population z-score",
                  "demonstration_note": "24 points expose the computation; production default is 256"}
    source = [_source("EchoTime comparison implementation", NATIVE)]
    out = []

    # Shape combines two positive-part correlations, rather than an arithmetic
    # average of unnormalized waveform differences.
    frames = []
    for k in np.linspace(4, n, 4, dtype=int):
        frames.append(_frame(0, "Resample to 24 points and z-normalize each input",
            _lines(x[:k], y[:k], title="Standardized level traces")))
    for k in np.linspace(3, n, 6, dtype=int):
        frames.append(_frame(1, "Measure level correlation on aligned samples",
            {"kind": "scatter", "title": "Standardized level pairs", "a": _floats(x[:k]), "b": _floats(y[:k]), "marker": k - 1},
            float(np.corrcoef(x[:k], y[:k])[0, 1]), "prefix Pearson r"))
    for k in np.linspace(3, n - 1, 6, dtype=int):
        frames.append(_frame(2, "Compare re-normalized first differences",
            _lines(dx[:k], dy[:k], title="Standardized first-difference pairs"),
            float(np.corrcoef(dx[:k], dy[:k])[0, 1]), "prefix difference correlation"))
    shape = geom(r_level, r_diff)
    for k in range(4):
        frames.append(_frame(3, "Clip both correlations to [0,1], then take their geometric mean",
            _bars([clip(r_level), clip(r_diff), shape], title="Level, change and combined similarity",
                  labels=["level", "change", "GM"], marker=k % 3), shape, "shape similarity"))
    out.append(_card("shape_similarity", "EchoTime shape similarity", "native", raw_x, raw_y,
        intro_en="EchoTime's shape component combines agreement in standardized levels with agreement in their first differences. Negative correlations are clipped to zero, and a geometric mean requires both views to contribute positively. The animation reproduces these intermediate views and their actual component scores on a 24-point example, making the package-specific blend explicit.",
        intro_zh="EchoTime 的形状分项结合标准化水平值和一阶差分的一致性。负相关先截为零，几何平均要求两个视角都具有正贡献。动图使用 24 点示例复现各中间表示与真实分项数值，明确展示这个软件特有的组合。",
        steps_en=["Resample and standardize each channel with the same declared point count.", "Compute Pearson correlation of aligned levels.", "Compute Pearson correlation of standardized first differences.", "Clip correlations to [0,1] and take their geometric mean."],
        steps_zh=["按声明的点数重采样并分别标准化通道。", "计算对齐水平值的 Pearson 相关。", "计算标准化一阶差分的 Pearson 相关。", "将相关截至 [0,1] 后取几何平均。"],
        formula="sqrt(max(r(x,y),0)*max(r(z(diff(x)),z(diff(y))),0))",
        caveats_en=["Clipping makes anticorrelation and zero correlation equally contribute zero.", "This is a package-specific similarity component, not a calibrated probability.", "The 24-point demonstration changes resolution from the default 256-point pipeline."],
        caveats_zh=["截断使负相关和零相关都贡献零。", "这是软件特定的相似性分项，不是校准概率。", "24 点演示采用的分辨率与默认 256 点流程不同。"],
        sources=source, parameters=copy.deepcopy(parameters), value=shape, frames=frames, kind="similarity", definition="echotime"))

    # Exact absolute-cost dynamic programs used by the native score.
    level_window = max(3, min(18, n // 20)); diff_window = max(3, min(16, len(dx) // 20))
    level_matrix, level_path, d_level = _absolute_dtw_trace(x, y, level_window)
    diff_matrix, diff_path, d_diff = _absolute_dtw_trace(dx, dy, diff_window)
    s_level, s_diff = math.exp(-d_level / .45), math.exp(-d_diff / .35)
    dtw = geom(s_level, s_diff)
    frames = []
    for k in np.linspace(4, n, 4, dtype=int):
        frames.append(_frame(0, "Use standardized levels and re-standardized first differences",
            _lines(x[:k], y[:k], title="Native DTW level inputs")))
    for rows in np.linspace(2, n, 8, dtype=int):
        frames.append(_frame(1, "Fill the constrained level DP using absolute local differences",
            {"kind": "matrix", "title": f"Level DP: cumulative absolute cost, band {level_window}",
             "z": _matrix_rows(level_matrix, int(rows)), "path": level_path if rows == n else [],
             "row_label": "x sample", "col_label": "y sample"}))
    for rows in np.linspace(2, len(dx), 8, dtype=int):
        frames.append(_frame(2, "Repeat constrained absolute-cost DP on standardized differences",
            {"kind": "matrix", "title": f"Difference DP: cumulative cost, band {diff_window}",
             "z": _matrix_rows(diff_matrix, int(rows)), "path": diff_path if rows == len(dx) else [],
             "row_label": "x change", "col_label": "y change"}))
    for k in range(4):
        frames.append(_frame(3, "Divide each path cost by n+m; exponentiate and take a geometric mean",
            _bars([s_level, s_diff, dtw], title="Two exponential scores and their geometric mean",
                  labels=["level", "change", "GM"], marker=k % 3), dtw, "native DTW similarity"))
    out.append(_card("dtw_similarity", "EchoTime DTW similarity", "native", raw_x, raw_y,
        intro_en="The native DTW component runs constrained alignments on both standardized levels and standardized first differences. Each local cost is an absolute gap; the accumulated path cost is divided by the sum of sequence lengths. Two different exponential scales convert those costs into scores, whose geometric mean is the reported component. The animation reconstructs both actual dynamic programs.",
        intro_zh="原生 DTW 分项对标准化水平值和标准化一阶差分分别执行有约束对齐。局部代价是绝对差，累计路径代价除以两序列长度之和，再通过不同尺度的指数函数转成分数，最终取几何平均。动图重建这两个实际动态规划。",
        steps_en=["Standardize levels and first differences separately.", "Accumulate absolute local costs within the level warping band.", "Run the same recurrence on differences with their declared band.", "Normalize costs by n+m, use scales 0.45 and 0.35, and combine geometrically."],
        steps_zh=["分别标准化水平值与一阶差分。", "在水平值规整窗口内累加绝对局部代价。", "对差分按其窗口执行同样递推。", "按 n+m 归一化，以 0.45 和 0.35 指数映射后取几何平均。"],
        formula="sqrt(exp(-aDTW_w(x,y)/0.45)*exp(-aDTW_v(z(diff(x)),z(diff(y)))/0.35)); aDTW=sum_path abs(gap)/(n+m)",
        caveats_en=["This native score differs from square-root-of-squared-cost DTW distances in other libraries.", "The band, resampling resolution, derivative normalization and scales affect the value.", "A high score does not imply causal correspondence or a probability of identity."],
        caveats_zh=["此原生分数与其他库常用的平方代价开根号 DTW 距离不同。", "窗口、重采样分辨率、差分标准化和指数尺度都会影响数值。", "高分不表示因果对应或同一性的概率。"],
        sources=source, parameters={**parameters, "level_band": level_window, "difference_band": diff_window, "level_scale": .45, "difference_scale": .35, "level_cost": d_level, "difference_cost": d_diff},
        value=dtw, frames=frames, kind="similarity", definition="echotime"))

    # Reconstruct the existing Savitzky-Golay settings, including its endpoints.
    w = int(max(7, min(n - (1 - n % 2), (n // 6) * 2 + 1)))
    if w % 2 == 0: w += 1
    w = min(w, n if n % 2 else n - 1)
    tx = savgol_filter(x, window_length=w, polyorder=min(3, w - 2), mode="interp")
    ty = savgol_filter(y, window_length=w, polyorder=min(3, w - 2), mode="interp")
    dtx, dty = _z(np.diff(tx)), _z(np.diff(ty))
    tr = float(np.corrcoef(tx, ty)[0, 1]); tdr = float(np.corrcoef(dtx, dty)[0, 1]); trend = geom(tr, tdr)
    frames = []
    for k in np.linspace(0, n - 1, 4, dtype=int):
        frames.append(_frame(0, f"Smooth with Savitzky-Golay window {w}, polynomial order 3",
            _lines(x, tx, title="Left input and its fitted trend", marker=k, a_label="input x", b_label="trend x")))
    for k in np.linspace(0, n - 1, 6, dtype=int):
        frames.append(_frame(1, "Compare the two smooth level trajectories",
            _lines(tx, ty, title="Savitzky-Golay trends", marker=k), tr, "trend level correlation"))
    for k in np.linspace(0, n - 2, 6, dtype=int):
        frames.append(_frame(2, "Compare standardized changes of the smooth trends",
            _lines(dtx, dty, title="Standardized trend differences", marker=k), tdr, "trend change correlation"))
    for k in range(4):
        frames.append(_frame(3, "Clip both trend correlations and combine geometrically",
            _bars([clip(tr), clip(tdr), trend], title="Trend levels, trend changes and combined score",
                  labels=["level", "change", "GM"], marker=k % 3), trend, "trend similarity"))
    out.append(_card("trend_similarity", "EchoTime trend similarity", "native", raw_x, raw_y,
        intro_en="The trend component smooths each standardized input with the package's Savitzky-Golay settings. It compares both the smoothed levels and their standardized first differences, then combines clipped correlations geometrically. The animation reveals the fitted trend before comparison. This separates the declared smoothing scale from a claim that the observed signal has one uniquely identifiable trend.",
        intro_zh="趋势分项按软件的 Savitzky-Golay 设置平滑各标准化输入，分别比较平滑后的水平值和标准化一阶差分，再对截断相关取几何平均。动画先展示拟合趋势，再比较两侧；所声明的平滑尺度不意味着信号存在唯一可识别的趋势。",
        steps_en=["Apply the declared Savitzky-Golay smoother to both standardized inputs.", "Measure correlation between the smooth level curves.", "Measure correlation between standardized first differences of those curves.", "Clip both correlations and take their geometric mean."],
        steps_zh=["按所声明参数对两侧标准化输入进行 Savitzky-Golay 平滑。", "比较平滑水平曲线的相关。", "比较平滑曲线标准化一阶差分的相关。", "截断两个相关并取几何平均。"],
        formula="sqrt(max(corr(T(x),T(y)),0)*max(corr(z(diff(T(x))),z(diff(T(y)))),0))",
        caveats_en=["The window is length-dependent, so changing n_points changes the smoothing scale.", "Smoothing can conceal short events that still matter for the application.", "Endpoint interpolation is part of the displayed Savitzky-Golay convention."],
        caveats_zh=["窗口随长度变化，改变 n_points 会改变平滑尺度。", "平滑可能掩盖应用中重要的短暂事件。", "端点插值属于此 Savitzky-Golay 实现约定。"],
        sources=source + [_source("SciPy: Savitzky-Golay filter", "https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.savgol_filter.html")],
        parameters={**parameters, "window_length": w, "polyorder": 3, "mode": "interp"}, value=trend, frames=frames, kind="similarity", definition="echotime"))

    frames, diff_raw = _corr_trace(dx, dy, title="pearson", transform=clip,
                                 final_label="Clip first-difference correlation to [0,1]")
    frames[:4] = [_frame(0, "Resample and standardize the original level traces",
                         _lines(x[:k], y[:k], title="Standardized level inputs"))
                  for k in np.linspace(4, n, 4, dtype=int)]
    frames[4:8] = [_frame(1, "Take first differences and standardize each change vector",
                         _lines(dx[:k], dy[:k], title="Standardized first differences"))
                  for k in np.linspace(3, n - 1, 4, dtype=int)]
    out.append(_card("derivative_similarity", "EchoTime derivative similarity", "native", raw_x, raw_y,
        intro_en="The derivative component compares local increments after standardizing the input and then standardizing its first differences. It reports the positive part of their Pearson correlation. The animation follows the difference vectors and their normalized product terms, exposing why two signals can share a slow level pattern while differing substantially in their local changes.",
        intro_zh="差分分项先标准化输入，再标准化其一阶差分，以两组差分 Pearson 相关的正部分作为相似度。动画追踪差分向量及归一化乘积，说明两条序列即使共享缓慢变化的水平形状，局部变化仍可能不同。",
        steps_en=["Resample and standardize each original series.", "Take first differences and standardize those differences separately.", "Compute Pearson correlation of the aligned change vectors.", "Clip the correlation to [0,1]."],
        steps_zh=["重采样并标准化原序列。", "取一阶差分并分别标准化。", "计算对齐变化向量的 Pearson 相关。", "将相关截至 [0,1]。"],
        formula="max(corr(z(diff(x)),z(diff(y))),0)",
        caveats_en=["Differencing can amplify measurement noise and reduces the sample count by one.", "Anticorrelated changes receive zero similarity after clipping.", "Sampling resolution determines which changes are treated as local."],
        caveats_zh=["差分可能放大测量噪声，并使样本数减少一个。", "反向相关的变化经截断后获得零相似度。", "采样分辨率决定哪些变化被视为局部。"],
        sources=source, parameters=copy.deepcopy(parameters), value=diff_raw, frames=frames, kind="similarity", definition="echotime"))

    # Native spectral convention: differences, linear detrend, drop DC, normalize
    # non-DC periodogram mass; JS is base-2 divergence, not its square root.
    frequency, px = _normalized_spectrum(dx); _, py = _normalized_spectrum(dy)
    mid = .5 * (px + py)
    pp, qq, mm = np.maximum(px, 1e-12), np.maximum(py, 1e-12), np.maximum(mid, 1e-12)
    js_terms = .5 * (pp * np.log2(pp / mm) + qq * np.log2(qq / mm))
    js = float(js_terms.sum()); overlap = clip(1 - js)
    uniform = np.full(len(px), 1 / len(px))
    structure = clip(float(np.corrcoef(px - uniform, py - uniform)[0, 1])); spectral = geom(overlap, structure)
    frames = []
    for k in np.linspace(3, len(dx), 4, dtype=int):
        frames.append(_frame(0, "The native spectrum is computed from standardized first differences",
            _lines(dx[:k], dy[:k], title="Differenced signals entering the spectrum")))
    for k in np.linspace(2, len(px), 6, dtype=int):
        frames.append(_frame(1, "Linearly detrend, discard DC, normalize remaining spectral power",
            _bars(px[:k], py[:k], title="Normalized non-DC power", a_label="spectrum x", b_label="spectrum y")))
    for k in np.linspace(1, len(px), 6, dtype=int):
        partial = js_terms.copy(); partial[k:] = 0
        frames.append(_frame(2, "Compute JS overlap; separately compare centered spectral structure",
            _bars(partial, title="Per-frequency JS divergence contributions", marker=k - 1), float(js_terms[:k].sum()), "partial JS divergence (bits)"))
    for k in range(4):
        frames.append(_frame(3, "Combine 1-JS divergence and positive spectral correlation geometrically",
            _bars([overlap, structure, spectral], title="Overlap, spectral structure and combined score", labels=["1-JS", "corr", "GM"], marker=k % 3), spectral, "spectral similarity"))
    out.append(_card("spectral_similarity", "EchoTime spectral similarity", "native", raw_x, raw_y,
        intro_en="EchoTime's spectral component works on standardized first differences. It linearly detrends the periodogram input, drops the zero-frequency bin, and normalizes the remaining power. One term measures one minus base-two JS divergence; another measures positive correlation of spectral structure. Their geometric mean produces the actual score shown by the animation.",
        intro_zh="EchoTime 的频谱分项作用于标准化一阶差分。周期图计算使用线性去趋势，去除零频箱并归一化其余功率。一个分项取 1 减二进制 JS 散度，另一个衡量频谱结构的正相关，动图展示两者几何平均得到的实际分数。",
        steps_en=["Use standardized first differences as spectral input.", "Compute linearly detrended periodograms, remove DC and normalize power.", "Calculate 1-JS divergence in bits and positive spectral correlation.", "Take the geometric mean of overlap and structure scores."],
        steps_zh=["以标准化一阶差分作为频谱输入。", "计算线性去趋势周期图，去除零频并归一化功率。", "计算二进制 1−JS 散度与频谱正相关。", "对重叠和结构分数取几何平均。"],
        formula="sqrt(clip(1-JS_base2(Px,Py),0,1)*max(corr(Px-U,Py-U),0)); spectra of z(diff(x))",
        caveats_en=["Power spectra discard phase; similar spectra do not ensure aligned waveforms.", "The JS term here is a divergence in bits, not the square-root JS distance in another atlas card.", "Resampling, differentiation and detrending all change the spectral object being compared."],
        caveats_zh=["功率谱舍弃相位，频谱相似不保证波形对齐。", "这里的 JS 项是以比特为单位的散度，与另一条目的平方根 JS 距离不同。", "重采样、差分和去趋势都会改变所比较的频谱对象。"],
        sources=source + [_source("EchoTime spectral preprocessing and JS definition", ROOT_URL + "src/echotime/metrics.py")],
        parameters={**parameters, "periodogram_detrend": "linear", "drop_DC": True, "JS_log_base": 2, "frequency_grid": _floats(frequency)},
        value=spectral, frames=frames, kind="similarity", definition="echotime"))

    # Reference metrics in a native report: same actual resampled arrays and
    # same tau-b / average-rank definitions as the standalone illustrations.
    for name, family, title in (("pearson_r", "pearson", "EchoTime reference: Pearson r"),
                                ("spearman_rho", "spearman", "EchoTime reference: Spearman rho"),
                                ("kendall_tau", "kendall", "EchoTime reference: Kendall tau-b")):
        if family == "kendall": frames, val = _kendall_trace(x, y)
        else: frames, val = _corr_trace(x, y, title=family, transform=float, final_label="Keep the signed reference coefficient", rank=family == "spearman")
        if family == "pearson":
            intro = "The native report includes signed Pearson correlation as a familiar reference alongside its clipped component scores. It is evaluated after the same resampling and per-channel standardization as the other report terms. This animation reveals centered products on that actual comparison grid and retains negative values instead of interpreting them as positive shape agreement."
            zh = "原生报告保留带符号 Pearson 相关作为参照，与截断后的分项并列。其输入经过相同的重采样和逐通道标准化。动画在实际比较网格上展示中心化乘积，并保留负值的含义。"
            form = "corr(x,y) after compare_series preprocessing"
            steps = ["Use the report's resampled, standardized input arrays.", "Center the paired observations.", "Normalize their product sum by both centered norms.", "Keep the signed coefficient in the reference-metric section."]
            steps_zh = ["使用报告经过重采样和标准化的输入。", "对配对观测去均值。", "按中心化范数归一化点积。", "在参照指标中保留带符号系数。"]
            sc = _scipy("correlation")
        elif family == "spearman":
            intro = "The native Spearman reference converts the report's resampled observations to average ranks and correlates those ranks. It complements amplitude-based comparisons by exposing monotone agreement on the same grid. The animation makes the ranking operation visible, including ties, and retains a signed coefficient; its value depends on the observations created by the chosen interpolation resolution."
            zh = "原生 Spearman 参照把报告重采样后的观测转换为平均排名，再计算相关。它在相同网格上展示单调一致性，补充幅值比较。动画显示含并列处理的排名操作并保留符号；结果依赖所选插值分辨率产生的观测。"
            form = "corr(rank_average(x),rank_average(y)) after compare_series preprocessing"
            steps = ["Use the same resampled observations as the native report.", "Assign average ranks independently, retaining paired sample identities.", "Center ranks and normalize their product sum.", "Report the signed rank coefficient."]
            steps_zh = ["使用原生报告相同的重采样观测。", "独立赋予平均排名，保留配对身份。", "对排名去均值并归一化乘积。", "报告带符号排名系数。"]
            sc = _scipy("spearmanr", stats=True)
        else:
            intro = "The native Kendall reference uses tau-b, including corrections for one-sided ties, on the resampled input grid. It counts ordering agreements and disagreements rather than amplitude gaps. The animation reconstructs its pair classifications and normalization. This explanatory enumeration matches the score while leaving the numerical library free to use a more efficient algorithm internally."
            zh = "原生 Kendall 参照在重采样网格上使用包含单侧并列校正的 tau-b，统计顺序同向与反向关系，不比较幅值差。动画重建配对分类和归一化；这种教学枚举与实际分数一致，数值库内部可以使用更高效算法。"
            form = "(C-D)/sqrt((C+D+T_x)*(C+D+T_y)) on resampled observations"
            steps = ["Use the native report's resampled observations.", "Compare relative orders for observation pairs.", "Count concordance, discordance and one-sided ties.", "Apply tau-b normalization and keep its sign."]
            steps_zh = ["使用原生报告重采样后的观测。", "比较观测对的相对顺序。", "统计同序、逆序和单侧并列。", "应用 tau-b 归一化并保留符号。"]
            sc = _scipy("kendalltau", stats=True)
        out.append(_card(name, title, "native", raw_x, raw_y, intro_en=intro, intro_zh=zh,
            steps_en=steps, steps_zh=steps_zh, formula=form,
            caveats_en=["EchoTime assigns zero for constant inputs; statistical correlation is undefined in that case.", "These are dependence summaries, not causal tests or identity probabilities.", "The illustrative report explicitly uses n_points=24; the default is 256."],
            caveats_zh=["EchoTime 对常量输入赋零；此时统计相关本身未定义。", "这些是依赖关系摘要，不是因果检验或同一性概率。", "演示报告显式使用 n_points=24，默认值为 256。"],
            sources=source + [sc], parameters=copy.deepcopy(parameters), value=val, frames=frames,
            kind="similarity", definition="echotime"))

    # A shifted example makes the native bounded-lag selection visible.
    lag_y_raw = np.r_[raw_x[:2], raw_x[:-2]] + .12 * np.sin(np.arange(n))
    lag_y = _resampled_multichannel(lag_y_raw, n_points=n)[:, 0]
    max_lag = max(1, min(24, n // 10)); lags = np.arange(-max_lag, max_lag + 1)
    corr = []
    for lag in lags:
        i, j = _overlap_indices(n, n, int(lag)); corr.append(float(np.corrcoef(x[i], lag_y[j])[0, 1]))
    corr = np.asarray(corr); best = int(np.argmax(corr)); value = float(corr[best])
    lag_report = compare_series(raw_x, lag_y_raw, n_points=n)
    frames = []
    for k in np.linspace(4, n, 4, dtype=int):
        frames.append(_frame(0, f"The native lag bound is {max_lag} at this 24-point resolution",
            _lines(x[:k], lag_y[:k], title="Resampled and standardized shifted inputs")))
    for lag, v in zip(lags, corr):
        frames.append(_frame(1, f"Lag {int(lag):+d}: center and correlate the overlapping observations",
            _alignment_panel(x, lag_y, int(lag), title=f"Native overlap at lag {int(lag):+d}"), v, "overlap Pearson r"))
    for k in range(len(lags)):
        frames.append(_frame(2, "Retain the largest correlation among the admitted lags",
            _lines(corr[:k + 1], title="Native bounded Pearson lag profile", x=lags[:k + 1], marker=k, a_label="Pearson r"), float(corr[:k + 1].max()), "best correlation so far"))
    for _ in range(4):
        frames.append(_frame(3, "Return the best signed correlation; interpret lag on the resampled axis",
            _lines(corr, title="Selected native lag", x=lags, marker=best, a_label="Pearson r"), value, "best-lag Pearson r"))
    card = _card("best_lag_pearson_r", "EchoTime reference: best-lag Pearson", "native", raw_x, lag_y_raw,
        intro_en="The native best-lag reference scans a bounded set of shifts on the report's resampled grid. Pearson correlation is recomputed on each actual overlap, including a separate overlap mean and norm. The animation uses a delayed illustrative series to show the improvement from lag zero to the selected lag while keeping the finite search window explicit.",
        intro_zh="原生最佳滞后参照在报告重采样网格上扫描有限平移。每个实际重叠片段重新计算 Pearson 相关，使用各自均值和范数。动画以延迟序列展示零滞后到最佳滞后的变化，并明确有限搜索窗口。",
        steps_en=["Resample both inputs; derive the native maximum lag from n_points.", "At every admitted lag, take the actual overlap.", "Recompute centered Pearson correlation on each overlap.", "Return the maximum signed coefficient and interpret its lag in resampled points."],
        steps_zh=["重采样两侧输入，按 n_points 得到原生最大滞后。", "对每个允许滞后取实际重叠。", "在各重叠片段重新计算中心化 Pearson 相关。", "返回最大带符号系数，滞后单位为重采样点。"],
        formula="max_{|lag|<=max(1,min(24,n//10))} corr(x_overlap,y_overlap)",
        caveats_en=["The selected lag is measured on the normalized/resampled axis, not automatically in physical time.", "Searching several lags changes the interpretation from a prespecified single correlation.", "Overlap-specific centering differs from full-norm normalized cross-correlation."],
        caveats_zh=["所选滞后以归一化重采样轴为单位，不能自动解释为实际时间。", "搜索多个滞后与事先指定单个相关的统计解释不同。", "逐重叠去均值与全范数归一化互相关不同。"],
        sources=source, parameters={**parameters, "max_lag": max_lag, "selected_lag": int(lags[best])}, value=value, frames=frames, kind="similarity", definition="echotime")
    card["checks"] = {"api": "compare_series(..., n_points=24).reference_metrics['best_lag_pearson_r']", "expected": value, "observed": float(lag_report.reference_metrics["best_lag_pearson_r"]), "tolerance": 1e-12}
    out.append(card)

    # Histogram mutual information, using the exact native bin-count rule.
    bins = int(np.clip(round(np.sqrt(n / 4.0)), 4, 20))
    hist, xedges, yedges = np.histogram2d(x, y, bins=bins)
    joint = hist / hist.sum(); marginal_x = joint.sum(axis=1); marginal_y = joint.sum(axis=0)
    independent = marginal_x[:, None] * marginal_y[None, :]
    terms = np.zeros_like(joint); nonzero = joint > 0
    terms[nonzero] = joint[nonzero] * np.log(joint[nonzero] / np.maximum(independent[nonzero], 1e-12))
    mi = float(terms.sum()); hx = float(entropy(marginal_x)); hy = float(entropy(marginal_y))
    nmi = clip(mi / math.sqrt(hx * hy))
    frames = []
    for k in np.linspace(4, n, 4, dtype=int):
        frames.append(_frame(0, "Pair standardized observations; fix four bins on each axis",
            {"kind": "scatter", "title": "Observations before joint histogramming", "a": _floats(x[:k]), "b": _floats(y[:k]), "marker": k - 1}))
    for k in np.linspace(3, n, 8, dtype=int):
        h, _, _ = np.histogram2d(x[:k], y[:k], bins=[xedges, yedges])
        frames.append(_frame(1, "Count paired observations using the same fixed bin edges",
            {"kind": "matrix", "title": "Joint histogram counts", "z": h.tolist(), "row_label": "x bin", "col_label": "y bin"}))
    for k in np.linspace(1, terms.size, 8, dtype=int):
        partial = terms.copy().reshape(-1); partial[k:] = 0.0
        frames.append(_frame(2, "Compare joint mass with the product of its marginals",
            {"kind": "matrix", "title": "Contributions p(x,y) log[p(x,y)/(p(x)p(y))]", "z": partial.reshape(terms.shape).tolist(), "row_label": "x bin", "col_label": "y bin"},
            float(terms.reshape(-1)[:k].sum()), "partial mutual information (nats)"))
    for k in range(4):
        frames.append(_frame(3, "Normalize MI by sqrt(H(x)*H(y)) and clip to [0,1]",
            _bars([mi, hx, hy, nmi], title="MI, marginal entropies and normalized score", labels=["MI", "H(x)", "H(y)", "NMI"], marker=k), nmi, "normalized mutual information"))
    out.append(_card("normalized_mutual_information", "EchoTime reference: normalized mutual information", "native", raw_x, raw_y,
        intro_en="EchoTime estimates mutual information from a joint histogram of aligned, resampled observations. It compares observed joint mass with the product of marginal masses, then divides by the geometric mean of marginal entropies. The animation shows the actual bin counts and information terms. The resulting finite-sample dependence estimate is sensitive to the declared binning rule.",
        intro_zh="EchoTime 通过对齐且重采样观测的联合直方图估计互信息，比较联合概率与边缘概率乘积，再除以两侧熵的几何平均。动画显示真实箱计数及信息贡献项。有限样本依赖估计对所声明的分箱规则敏感。",
        steps_en=["Use the aligned resampled observations and the native bin-count rule.", "Count their joint histogram and normalize it to probability mass.", "Compute MI from joint-versus-independent mass and both marginal entropies.", "Divide MI by sqrt(Hx*Hy) and clip to [0,1]."],
        steps_zh=["使用对齐的重采样观测和原生分箱数规则。", "计算联合直方图并归一化为概率。", "由联合质量与独立质量比较得到 MI，同时计算边缘熵。", "以 sqrt(Hx*Hy) 归一化 MI 并截至 [0,1]。"],
        formula="I(X;Y)/sqrt(H(X)*H(Y)); bins=clip(round(sqrt(n/4)),4,20); natural logarithms",
        caveats_en=["Binning and finite sample size introduce estimation bias; a nonzero score is not a significance test.", "The native function needs at least twelve finite paired observations and gives constant inputs a zero convention.", "Dependence does not establish causality, waveform equality or temporal forecasting ability."],
        caveats_zh=["分箱和有限样本引入估计偏差；非零分数不是显著性检验。", "原生函数要求至少十二对有限观测，并对常量输入约定为零。", "依赖关系不证明因果、波形相等或时间预测能力。"],
        sources=source, parameters={**parameters, "bins_per_axis": bins, "x_bin_edges": _floats(xedges), "y_bin_edges": _floats(yedges), "log_base": "e"},
        value=nmi, frames=frames, kind="similarity", definition="echotime"))

    for card in out:
        if card["id"] == "best_lag_pearson_r":
            assert np.isclose(card["checks"]["expected"], card["checks"]["observed"], atol=1e-12)
            continue
        expected = card["result"]["value"]
        section = report.component_scores if card["id"] in report.component_scores else report.reference_metrics
        observed = float(section[card["id"]])
        if not np.isclose(expected, observed, rtol=1e-11, atol=1e-12):
            raise AssertionError((card["id"], expected, observed))
        card["checks"] = {"api": "compare_series(..., n_points=24): " + card["id"], "expected": expected, "observed": observed, "tolerance": 1e-11}
    return out


def build_examples() -> list[dict]:
    """Return all 56 owned examples, with actual native API checks executed."""
    examples = (_pointwise_examples() + _normalised_examples() + _correlation_examples()
                + _distribution_examples() + _sliding_examples() + _native_examples())
    ids = [row["id"] for row in examples]
    if len(ids) != 56 or len(set(ids)) != 56:
        raise AssertionError(f"Expected 56 unique pointwise/sliding/native cards, got {len(ids)}")
    for row in examples:
        row["animation_steps_en"] = _animation_steps(row)
        assert len(row["animation_steps_en"]) == 4
        assert max(map(len, row["animation_steps_en"])) <= 85, row["id"]
    return examples


def _animation_steps(row: dict) -> list[str]:
    """Concise complete statements for the GIF; full explanations stay in docs."""
    name = row["id"]
    if name in _POINTWISE_TEXT:
        desc = _POINTWISE_TEXT[name]
        return ["Keep samples on the same time grid.", desc[4] + ".",
                "Keep the largest error seen so far." if name == "chebyshev" else "Accumulate the coordinate contributions.", desc[5] + "."]
    specific = {
        "seuclidean_distance": ["Fix a positive variance for each coordinate.", "Divide squared gaps by reference variances.", "Accumulate standardized squared errors.", "Take the square root of the total."],
        "znorm_euclidean": ["Estimate each series' mean and standard deviation.", "Z-normalize each series independently.", "Accumulate squared normalized gaps.", "Take the square root."],
        "znorm_manhattan": ["Estimate each series' mean and standard deviation.", "Z-normalize each series independently.", "Accumulate absolute normalized gaps.", "Keep the absolute-gap sum."],
        "cid_distance": ["Compute the aligned Euclidean distance.", "Measure first-difference energy in each series.", "Divide larger complexity by smaller complexity.", "Multiply Euclidean distance by the complexity ratio."],
        "shape_similarity": ["Resample and z-normalize the input series.", "Measure level correlation.", "Measure correlation of standardized first differences.", "Clip correlations and take their geometric mean."],
        "dtw_similarity": ["Standardize levels and first differences.", "Run band-constrained absolute-cost DTW on levels.", "Run the same DTW recurrence on differences.", "Normalize costs, exponentiate and combine geometrically."],
        "trend_similarity": ["Smooth inputs with the specified Savitzky-Golay filter.", "Compare the smooth level curves.", "Compare standardized changes of the smooth curves.", "Clip correlations and combine geometrically."],
        "derivative_similarity": ["Resample and standardize the original series.", "Take first differences and standardize them.", "Compute Pearson correlation of aligned changes.", "Clip the correlation to the interval [0,1]."],
        "spectral_similarity": ["Start from standardized first differences.", "Detrend, compute spectra, discard DC and normalize power.", "Measure JS overlap and positive spectral correlation.", "Combine the two scores with a geometric mean."],
        "pearson_r": ["Use the report's resampled inputs.", "Center paired observations.", "Normalize the product sum by centered norms.", "Keep the signed Pearson coefficient."],
        "spearman_rho": ["Use the report's resampled observations.", "Assign average ranks, including ties.", "Compute Pearson correlation of ranks.", "Keep the signed rank coefficient."],
        "kendall_tau": ["Use the report's resampled observations.", "Compare orders within each observation pair.", "Count concordance, discordance and one-sided ties.", "Apply tau-b normalization and keep its sign."],
        "best_lag_pearson_r": ["Fix the native lag bound from the resampled length.", "Select the actual overlap at each lag.", "Recompute Pearson correlation on each overlap.", "Choose the largest signed correlation."],
        "normalized_mutual_information": ["Pair observations and apply the native bin-count rule.", "Form the joint histogram and normalize its counts.", "Compute MI and both marginal entropies.", "Divide MI by sqrt(Hx*Hy) and clip to [0,1]."],
        "max_normalized_cross_correlation": ["Z-normalize both complete series once.", "Slide through all integer lags.", "Use fixed full-series norms at every lag.", "Keep the largest NCC and its lag."],
        "sbd": ["Z-normalize both complete series once.", "Slide through all integer lags.", "Use fixed full-series norms at every lag.", "Subtract the largest NCC from one."],
        "independent_max_ncc": ["Pair and normalize each channel separately.", "Find channel one's NCC profile.", "Find channel two's NCC profile independently.", "Average the two channel maxima."],
        "independent_sbd": ["Pair and normalize each channel separately.", "Find channel one's NCC profile.", "Find channel two's NCC profile independently.", "Average one minus each channel's maximum NCC."],
    }
    if name in specific:
        return specific[name]
    if name.startswith("shift_"):
        metric = "Pearson r" if "pearson" in name else "cosine" if "cosine" in name else "RMSE" if "rmse" in name else "MAE" if "mae" in name else "L1 error" if "manhattan" in name else "Euclidean error"
        maximize = "cosine" in name or "pearson" in name
        final = "Choose the maximum and return 1-score." if maximize and name.endswith("distance") else "Choose the maximum overlap score." if maximize else "Choose the minimum overlap error."
        return ["Fix lags from -3 to +3 and retain adequate overlap.", f"Compute {metric} on each actual overlap.", "Record every candidate score with its lag.", final]
    if name.startswith("cosine") or name == "angular_distance":
        final = "Return arccos(cosine) divided by pi." if name == "angular_distance" else "Return one minus cosine." if name.endswith("distance") else "Keep the cosine similarity."
        return ["Keep the uncentered sample vectors.", "Compute coordinate products and both vector norms.", "Divide the dot product by the norm product.", final]
    if name.startswith("pearson"):
        return ["Pair observations at the same sample index.", "Center each sample vector independently.", "Normalize the centered product sum.", "Return one minus Pearson r." if name.endswith("distance") else "Keep the signed Pearson r."]
    if name.startswith("spearman"):
        return ["Pair observations and retain sample identities.", "Assign average ranks, including ties.", "Compute Pearson correlation of rank vectors.", "Return one minus rank correlation." if name.endswith("distance") else "Keep the signed rank correlation."]
    if name.startswith("kendall"):
        return ["Enumerate unordered observation pairs.", "Classify concordance, discordance and ties.", "Count one-sided ties separately.", "Apply tau-b normalization and return 1-tau." if name.endswith("distance") else "Apply tie-corrected tau-b normalization."]
    # Remaining six methods are the probability-vector comparisons. Their two
    # method-specific calculation statements already fit the animation sidebar.
    return ["Normalize counts on one shared bin support.", row["steps_en"][1],
            "Accumulate the displayed bin contributions.", row["steps_en"][3]]
