"""Small, deterministic elastic/kernel calculations for educational animations.

Reference definitions below are deliberately explicit. They are not new public
EchoTime APIs, and no animation represents a trained model or a benchmark result.
"""

from __future__ import annotations

from copy import deepcopy
import math

import numpy as np


_X = np.array([0.2, 0.4, 1.1, 2.4, 3.2, 2.5, 1.2, 0.3, -0.4, -0.1])
_Y = np.array([0.1, 0.3, 0.5, 1.2, 2.6, 3.1, 2.3, 1.1, 0.2, -0.3])
_SOURCE = {
    "dtw": ("tslearn: DTW definitions and path constraints", "https://tslearn.readthedocs.io/en/stable/user_guide/dtw.html"),
    "wdtw": ("aeon: logistic weighted DTW", "https://www.aeon-toolkit.org/en/stable/api_reference/auto_generated/aeon.distances.wdtw_distance.html"),
    "soft": ("Cuturi and Blondel (2017): Soft-DTW", "https://proceedings.mlr.press/v70/cuturi17a.html"),
    "divergence": ("Blondel, Mensch and Vert (2021): corrected divergences", "https://proceedings.mlr.press/v130/blondel21a.html"),
    "lcss": ("tslearn: Longest Common Subsequence", "https://tslearn.readthedocs.io/en/stable/user_guide/lcss.html"),
    "local": ("EchoTime low-level similarity implementations", "https://github.com/ZipengWu365/EchoTime/blob/main/src/echotime/similarity_methods.py"),
    "swale": ("Morse and Patel (2007), Definition 5.1", "https://dbgroup.eecs.umich.edu/files/sigmod07timeseries.pdf"),
    "msm": ("aeon: Move-Split-Merge recurrence", "https://www.aeon-toolkit.org/en/stable/api_reference/auto_generated/aeon.distances.msm_distance.html"),
    "twed": ("Marteau: TWED recurrence and stiffness", "https://arxiv.org/pdf/cs/0703033"),
    "frechet": ("Eiter and Mannila (1994): discrete Frechet distance", "https://www.kr.tuwien.ac.at/staff/eiter/et-archive/files/cdtr9464.pdf"),
    "sequence": ("Biopython: global and local sequence alignment", "https://biopython.org/docs/latest/Tutorial/chapter_pairwise.html"),
    "shape": ("Zhao and Itti: shapeDTW", "https://arxiv.org/abs/1606.01601"),
    "kernels": ("scikit-learn: pairwise kernels and their formulas", "https://scikit-learn.org/stable/modules/metrics.html"),
    "gak": ("Cuturi (2011): local-kernel conditions for global alignment", "https://marcocuturi.net/Papers/cuturi11fast.pdf"),
    "registry": ("EchoTime imported atlas: named formula conventions", "https://github.com/ZipengWu365/EchoTime/blob/main/src/echotime/data/ts_similarity_package_v2_registry.csv"),
}


def _sources(*keys):
    return [{"label": _SOURCE[k][0], "url": _SOURCE[k][1]} for k in keys]


def _matrix(a):
    return [[float(v) if np.isfinite(v) else None for v in row] for row in a]


def _frame(phase, caption, panel, value=None, value_label="prefix cost"):
    frame = {"phase": phase, "caption": caption, "panel": panel}
    if value is not None and np.isfinite(value):
        frame.update(value=float(value), value_label=value_label)
    return frame


def _panel(matrix, title, path=None, cursor=None):
    result = {"kind": "matrix", "title": title, "z": _matrix(matrix),
              "row_label": "x index", "col_label": "y index"}
    if path:
        result["path"] = [list(p) for p in path]
    if cursor is not None:
        result["cursor"] = list(cursor)
    return result


def _traceback(parent, end, *, zero_stop=None):
    i, j = end
    path, matched = [], []
    while i > 0 and j > 0:
        if zero_stop is not None and zero_stop[i, j] <= 0:
            break
        path.append((i - 1, j - 1))
        pi, pj = parent[i, j]
        if pi < 0 or pj < 0:
            break
        if pi == i - 1 and pj == j - 1:
            matched.append((i - 1, j - 1))
        i, j = int(pi), int(pj)
    return path[::-1], matched[::-1]


def _dtw(x, y, *, window=None, itakura=False, weighted=False, derivative=False,
         descriptor=False, g=0.6):
    a, b = np.asarray(x), np.asarray(y)
    if derivative:
        a, b = np.diff(a), np.diff(b)
    if descriptor:
        a = np.lib.stride_tricks.sliding_window_view(np.pad(a, 1, mode="edge"), 3)
        b = np.lib.stride_tricks.sliding_window_view(np.pad(b, 1, mode="edge"), 3)
    cost = (a[:, None] - b[None, :]) ** 2 if a.ndim == 1 else np.sum((a[:, None, :] - b[None, :, :]) ** 2, axis=2)
    n, m = cost.shape
    allowed = np.ones((n, m), dtype=bool)
    ii, jj = np.indices((n, m))
    if window is not None:
        allowed &= np.abs(ii - jj) <= window
    if itakura:
        # Equal-length example: slopes 1/2 and 2 anchored at both endpoints.
        assert n == m
        allowed &= (jj >= ii / 2) & (jj <= 2 * ii)
        allowed &= (m - 1 - jj >= (n - 1 - ii) / 2) & (m - 1 - jj <= 2 * (n - 1 - ii))
    if weighted:
        weights = 1.0 / (1.0 + np.exp(-g * (np.abs(ii - jj) - max(n, m) / 2)))
        cost = cost * weights
    cost = np.where(allowed, cost, np.inf)
    d = np.full((n + 1, m + 1), np.inf)
    d[0, 0] = 0
    parent = np.full((n + 1, m + 1, 2), -1, dtype=int)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if not allowed[i - 1, j - 1]:
                continue
            predecessors = [(i - 1, j - 1), (i - 1, j), (i, j - 1)]
            previous = min(predecessors, key=lambda p: d[p])
            d[i, j] = cost[i - 1, j - 1] + d[previous]
            parent[i, j] = previous
    path, _ = _traceback(parent, (n, m))
    return {"cost": cost, "dp": d[1:, 1:], "path": path, "pairs": path,
            "value": float(math.sqrt(d[-1, -1])), "a": a, "b": b}


def _soft_dtw(x, y, gamma=0.7):
    cost = (np.asarray(x)[:, None] - np.asarray(y)[None, :]) ** 2
    n, m = cost.shape
    d = np.full((n + 1, m + 1), np.inf)
    d[0, 0] = 0
    weights = np.zeros((n + 1, m + 1, 3))
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            previous = np.array([d[i - 1, j - 1], d[i - 1, j], d[i, j - 1]])
            minimum = np.min(previous)
            exponents = np.exp(-(previous - minimum) / gamma)
            weights[i, j] = exponents / np.sum(exponents)
            d[i, j] = cost[i - 1, j - 1] + minimum - gamma * np.log(np.sum(exponents))
    # Reverse-mode chain rule: expected occupancy of every alignment cell.
    adjoint = np.zeros_like(d)
    adjoint[n, m] = 1
    for i in range(n, 0, -1):
        for j in range(m, 0, -1):
            for w, p in zip(weights[i, j], [(i - 1, j - 1), (i - 1, j), (i, j - 1)]):
                adjoint[p] += adjoint[i, j] * w
    return {"cost": cost, "dp": d[1:, 1:], "occupancy": adjoint[1:, 1:], "value": float(d[-1, -1])}


def _edit(kind, x, y, *, epsilon=0.35, gap=0.5, penalty=0.5, reward=2.0,
          lambda_=0.4, nu=0.2, tx=None, ty=None):
    x, y = np.asarray(x), np.asarray(y)
    n, m = len(x), len(y)
    local = np.abs(x[:, None] - y[None, :])
    d = np.zeros((n + 1, m + 1))
    parent = np.full((n + 1, m + 1, 2), -1, dtype=int)
    if kind == "edr":
        d[:, 0], d[0, :] = np.arange(n + 1), np.arange(m + 1)
        local = (local > epsilon).astype(float)
    elif kind == "erp":
        d[1:, 0], d[0, 1:] = np.cumsum(np.abs(x - gap)), np.cumsum(np.abs(y - gap))
    elif kind in {"nw", "swale"}:
        d[:, 0], d[0, :] = -penalty * np.arange(n + 1), -penalty * np.arange(m + 1)
    elif kind == "twed":
        d.fill(np.inf)
        d[0, 0] = 0
        xp, yp = np.r_[0, x], np.r_[0, y]
        tx = np.r_[0, np.arange(1, n + 1) if tx is None else tx]
        ty = np.r_[0, np.arange(1, m + 1) if ty is None else ty]
        local = local + np.abs(xp[:-1, None] - yp[None, :-1]) + nu * (np.abs(tx[1:, None] - ty[None, 1:]) + np.abs(tx[:-1, None] - ty[None, :-1]))
    elif kind == "frechet":
        d.fill(np.inf)
        d[0, 0] = 0
    elif kind == "lcss":
        local = (local <= epsilon).astype(float)
    if kind in {"nw", "sw"}:
        local = np.where(local <= epsilon, reward, -1.0)
    if kind == "swale":
        local = (local <= epsilon).astype(float)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            predecessors = [(i - 1, j - 1), (i - 1, j), (i, j - 1)]
            if kind == "lcss":
                if local[i - 1, j - 1]:
                    choices = [(d[i - 1, j - 1] + 1, predecessors[0])]
                else:
                    choices = [(d[i - 1, j], predecessors[1]), (d[i, j - 1], predecessors[2])]
                value, previous = max(choices, key=lambda t: t[0])
            elif kind == "swale":
                if local[i - 1, j - 1]:
                    value, previous = d[i - 1, j - 1] + reward, predecessors[0]
                else:
                    value, previous = max([(d[i - 1, j] - penalty, predecessors[1]), (d[i, j - 1] - penalty, predecessors[2])], key=lambda t: t[0])
            elif kind in {"nw", "sw"}:
                choices = [(d[i - 1, j - 1] + local[i - 1, j - 1], predecessors[0]),
                           (d[i - 1, j] - penalty, predecessors[1]), (d[i, j - 1] - penalty, predecessors[2])]
                if kind == "sw":
                    choices.append((0.0, (-1, -1)))
                value, previous = max(choices, key=lambda t: t[0])
            elif kind == "edr":
                value, previous = min([(d[i - 1, j - 1] + local[i - 1, j - 1], predecessors[0]),
                                       (d[i - 1, j] + 1, predecessors[1]), (d[i, j - 1] + 1, predecessors[2])], key=lambda t: t[0])
            elif kind == "erp":
                value, previous = min([(d[i - 1, j - 1] + local[i - 1, j - 1], predecessors[0]),
                                       (d[i - 1, j] + abs(x[i - 1] - gap), predecessors[1]),
                                       (d[i, j - 1] + abs(y[j - 1] - gap), predecessors[2])], key=lambda t: t[0])
            elif kind == "twed":
                del_x = abs(xp[i] - xp[i - 1]) + nu * abs(tx[i] - tx[i - 1]) + lambda_
                del_y = abs(yp[j] - yp[j - 1]) + nu * abs(ty[j] - ty[j - 1]) + lambda_
                value, previous = min([(d[i - 1, j - 1] + local[i - 1, j - 1], predecessors[0]),
                                       (d[i - 1, j] + del_x, predecessors[1]), (d[i, j - 1] + del_y, predecessors[2])], key=lambda t: t[0])
            elif kind == "frechet":
                previous = min(predecessors, key=lambda p: d[p])
                value = max(local[i - 1, j - 1], d[previous])
            else:
                raise ValueError(kind)
            d[i, j], parent[i, j] = value, previous
    end = tuple(int(v) for v in np.unravel_index(np.argmax(d), d.shape)) if kind == "sw" else (n, m)
    path, pairs = _traceback(parent, end, zero_stop=d if kind == "sw" else None)
    if kind == "frechet":
        pairs = path
    value = d[end]
    if kind == "lcss":
        value /= min(n, m)
    if kind == "edr":
        value /= max(n, m)
    return {"cost": local, "dp": d[1:, 1:], "path": path, "pairs": pairs,
            "value": float(value), "a": x, "b": y, "end": end}


def _msm(x, y, c=0.6):
    def operation(v, a, b):
        return c if min(a, b) <= v <= max(a, b) else c + min(abs(v - a), abs(v - b))
    n, m = len(x), len(y)
    d = np.full((n + 1, m + 1), np.inf)
    parent = np.full((n + 1, m + 1, 2), -1, dtype=int)
    d[1, 1] = abs(x[0] - y[0])
    parent[1, 1] = (0, 0)
    for i in range(2, n + 1):
        d[i, 1] = d[i - 1, 1] + operation(x[i - 1], x[i - 2], y[0])
        parent[i, 1] = (i - 1, 1)
    for j in range(2, m + 1):
        d[1, j] = d[1, j - 1] + operation(y[j - 1], x[0], y[j - 2])
        parent[1, j] = (1, j - 1)
    for i in range(2, n + 1):
        for j in range(2, m + 1):
            choices = [(d[i - 1, j - 1] + abs(x[i - 1] - y[j - 1]), (i - 1, j - 1)),
                       (d[i - 1, j] + operation(x[i - 1], x[i - 2], y[j - 1]), (i - 1, j)),
                       (d[i, j - 1] + operation(y[j - 1], x[i - 1], y[j - 2]), (i, j - 1))]
            d[i, j], parent[i, j] = min(choices, key=lambda t: t[0])
    path, pairs = _traceback(parent, (n, m))
    return {"cost": np.abs(np.asarray(x)[:, None] - np.asarray(y)[None, :]),
            "dp": d[1:, 1:], "path": path, "pairs": pairs, "value": float(d[n, m]),
            "a": np.asarray(x), "b": np.asarray(y)}


def _dp_frames(trace, *, transform=None, local_title="Local comparison costs", dp_title="Accumulated prefix costs", result_label="distance", final_value=None):
    cost, d = trace["cost"], trace["dp"]
    value = trace["value"] if final_value is None else final_value
    frames = []
    if transform is not None:
        a, b, title = transform
        for marker in [0, len(a) // 3, 2 * len(a) // 3, len(a) - 1]:
            frames.append(_frame(0, title, {"kind": "lines", "title": title, "a": np.asarray(a).tolist(), "b": np.asarray(b).tolist(), "marker": marker, "a_label": "x transform", "b_label": "y transform"}))
    else:
        for progress in [0.25, 0.5, 0.75, 1.0]:
            shown = cost.copy()
            row = max(1, int(math.ceil(len(cost) * progress)))
            shown[row:] = np.nan
            frames.append(_frame(0, "Compare samples to construct the local table", _panel(shown, local_title, cursor=(row - 1, 0))))
    for row in range(len(d)):
        shown = d.copy()
        shown[row + 1:] = np.nan
        frames.append(_frame(1, "Extend solved prefixes using the stated recurrence", _panel(shown, dp_title, cursor=(row, len(d[0]) - 1)), d[row, -1]))
    if "occupancy" in trace:
        occupancy = trace["occupancy"]
        for fraction in [0.2, 0.4, 0.6, 0.8, 1.0]:
            shown = occupancy.copy()
            shown[:max(0, len(shown) - math.ceil(len(shown) * fraction))] = np.nan
            frames.append(_frame(2, "Reverse propagation distributes weight over many alignments", _panel(shown, "Expected cell occupancy (gradient)")))
        frames.append(_frame(3, "Read the soft objective; no single path is selected", _panel(occupancy, "Expected alignment occupancy"), value, result_label))
    else:
        path = trace["path"]
        for fraction in [0.2, 0.4, 0.6, 0.8, 1.0]:
            count = max(1, math.ceil(len(path) * fraction))
            frames.append(_frame(2, "Follow the chosen predecessor decisions", _panel(d, dp_title, path=path[-count:]), value, result_label))
        a, b = trace.get("a"), trace.get("b")
        if a is not None and a.ndim == 1:
            frames.append(_frame(3, "Inspect the selected correspondences and final score", {"kind": "alignment", "title": "Chosen pairs (gaps remain unlinked)", "a": a.tolist(), "b": b.tolist(), "pairs": [list(p) for p in trace["pairs"]]}, value, result_label))
        else:
            frames.append(_frame(3, "Read the final descriptor-space objective", _panel(d, dp_title, path=path), value, result_label))
    return frames


def _entry(identifier, title, intro, steps, formula, caveats, source_keys, trace,
           *, definition="reference", parameters=None, frames=None, label="distance", x=None, y=None):
    en, zh = intro
    steps_en, steps_zh = zip(*steps)
    caveats_en, caveats_zh = zip(*caveats)
    return {"id": identifier, "title": title, "family": "elastic", "definition": definition,
            "intro_en": en, "intro_zh": zh, "steps_en": list(steps_en), "steps_zh": list(steps_zh),
            "formula": formula, "caveats_en": list(caveats_en), "caveats_zh": list(caveats_zh),
            "sources": _sources(*source_keys), "x": np.asarray(_X if x is None else x).tolist(), "y": np.asarray(_Y if y is None else y).tolist(),
            "input_label": "Deterministic illustrative arrays; no benchmark data",
            "parameters": parameters or {},
            "result": {"label": label, "value": float(trace["value"]), "detail": "The explicit definition and parameters shown on this card."},
            "frames": frames if frames is not None else _dp_frames(trace, result_label=label)}


def _elastic_examples():
    examples = []
    dtw_specs = [
        ("dtw", "Dynamic time warping", {},
         ("DTW compares ordered series while allowing repeated matches along a monotone alignment path. The animation builds squared pointwise costs, fills the dynamic-programming table, and traces a minimum-cost path. This reference example returns the square root of the total cost; EchoTime's composite dtw_similarity uses a different local cost and scaling.",
          "DTW 在保持先后顺序的前提下，允许同一个观测与多个观测匹配。动图依次展示平方局部误差、动态规划累计表和最低代价路径。本例返回累计代价的平方根；EchoTime 的复合 dtw_similarity 使用不同的局部代价与缩放。"),
         "DTW(x,y) = sqrt(min_path sum_(i,j) (x_i-y_j)^2)",
         ("Unrestricted warping can align events that should remain distinct; the output is not generally a metric.", "无限制扭曲可能对齐本应区分的事件；该输出一般不满足全部度量公理。")),
        ("cdtw", "DTW with a path band", {"window": 1},
         ("Constrained DTW restricts the allowed correspondences before optimizing their cumulative cost. Here only cells at most one sample from the diagonal are admissible. Empty cells in the animation are forbidden states, not zero-cost matches; the same recurrence operates on the remaining band.",
          "约束 DTW 先限制允许匹配的位置，再优化累计误差。本例只允许偏离对角线不超过一个采样点的单元格。动图中的空格表示禁止状态，不能当作零代价；其余带状区域采用相同的递推。"),
         "cDTW = sqrt(min_path sum (x_i-y_j)^2), with |i-j| <= 1",
         ("A narrow band can exclude the desired alignment. Unequal-length inputs require an endpoint-aware constraint.", "窄窗口可能排除希望找到的匹配；长度不同时还须确保约束允许连接两端。")),
        ("itakura_dtw", "DTW with slope constraints", {"itakura": True},
         ("An Itakura-style parallelogram limits how strongly an alignment can stretch near either endpoint. This equal-length illustration uses slopes one half and two, anchored at the first and last samples. Dynamic programming then finds the least-cost path inside that explicitly shown region.",
          "Itakura 型平行四边形限制对齐路径在两端附近的伸缩程度。本例长度相等，允许斜率范围为二分之一至二，并同时锚定首尾观测。动态规划在图示允许区域内寻找最低代价路径。"),
         "Allowed: i/2 <= j <= 2i and (n-1-i)/2 <= n-1-j <= 2(n-1-i)",
         ("Mask discretization and unequal-length slope conventions differ across libraries; this card specifies an equal-length integer-grid example.", "不同库的离散掩码和异长斜率约定可能不同；本卡明确采用等长整数网格示例。")),
        ("wdtw", "Weighted dynamic time warping", {"weighted": True},
         ("Weighted DTW changes the price of a match according to its displacement from the diagonal. The local squared discrepancy is multiplied by a logistic weight that increases with displacement. The animation then optimizes those weighted costs and displays the resulting path, without imposing a hard band.",
          "加权 DTW 根据匹配位置偏离对角线的程度改变代价。局部平方误差乘以随位移增加的逻辑函数权重，再对这些加权代价求最优路径。本例不施加硬窗口。"),
         "w(k)=1/(1+exp(-0.6*(k-L/2))); d=sqrt(min_path sum w(|i-j|)*(x_i-y_j)^2)",
         ("These weights are at most one: the penalty is relative across displacements, not an added nonnegative surcharge to ordinary DTW.", "这里的权重不超过一；所谓惩罚表示不同位移之间的相对权重，不是给普通 DTW 额外增加非负费用。")),
        ("ddtw", "DTW on first differences", {"derivative": True},
         ("This atlas entry applies DTW to first differences, so the alignment responds to changes rather than absolute levels. The first frames expose the transformed series before the local table is accumulated. It is an explicit first-difference variant; other DDTW implementations use a smoothed derivative estimator.",
          "本条目对一阶差分使用 DTW，因此匹配依据是变化而非绝对水平。动图先展示变换后的序列，再构造累计表。本例明确使用一阶差分；其他 DDTW 实现可能采用平滑导数估计。"),
         "Delta x_i=x_(i+1)-x_i; d=DTW(Delta x,Delta y), squared costs then square root",
         ("Differencing removes constant offsets and amplifies high-frequency noise. The result depends on the derivative estimator.", "差分消除常数偏移，也会放大高频噪声；结果取决于导数估计方法。")),
        ("wddtw", "Weighted DTW on differences", {"derivative": True, "weighted": True},
         ("This variant first takes adjacent differences and then uses displacement-weighted DTW. It combines sensitivity to local changes with a preference for smaller index displacement. The displayed derivative table and weighted path belong to that stated composition, which need not equal every library's WDDTW convention.",
          "该变体先计算相邻差分，再进行位移加权 DTW，结合局部变化比较与较小索引位移偏好。图中导数表和加权路径对应这里明确给出的组合，不保证与所有库的 WDDTW 约定相同。"),
         "d=sqrt(min_path sum w(|i-j|)*(Delta x_i-Delta y_j)^2), g=0.6",
         ("Both derivative estimation and the logistic slope change the answer; offset tolerance does not imply robustness to arbitrary noise.", "导数估计和逻辑权重斜率都会改变结果；容忍水平偏移并不意味着对任意噪声稳健。")),
        ("shape_dtw", "DTW on local shape descriptors", {"descriptor": True},
         ("shapeDTW compares short neighborhoods around samples so that a match reflects local context. Here each descriptor contains three raw values with edge repetition, and DTW minimizes squared descriptor differences. The animation reports the descriptor-space objective, an explicit variant rather than a raw-signal score recomputed along its path.",
          "shapeDTW 用观测周围的短邻域描述局部形状。本例将三个原始数值组成描述符，边界使用重复填充，然后最小化描述符之间的平方差。动图报告描述符空间的目标值，不是沿该路径重新计算的原始信号距离。"),
         "phi(x_i)=[x_(i-1),x_i,x_(i+1)] with edge repetition; d=DTW(phi(x),phi(y))",
         ("Descriptor radius, scaling and the choice to rescore the final path in raw space all change the method. No trained descriptor is used here.", "邻域半径、缩放以及是否在原空间重新计分都会改变结果；本例没有训练描述符。")),
    ]
    for identifier, title, options, intro, formula, caveat in dtw_specs:
        trace = _dtw(_X, _Y, **options)
        transformed = options.get("derivative", False)
        transform = (np.diff(_X), np.diff(_Y), "First differences remove constant offsets") if transformed else None
        steps = [
            (("Take first differences with the stated convention." if transformed else "Choose raw observations and any neighborhood descriptor."),
             ("按明确约定计算一阶差分。" if transformed else "选择原始观测以及需要的邻域描述符。")),
            ("Compute local squared discrepancies; apply the indicated weights or admissibility mask.", "计算局部平方误差，并施加指定权重或允许匹配的掩码。"),
            ("At each admissible cell, add its local cost to the smallest predecessor cost.", "在每个允许单元格，把局部代价加到三个前驱的最小累计代价上。"),
            ("Trace one minimizing path and take the square root of its accumulated objective.", "回溯一条最小化目标的路径，并对其累计目标值取平方根。"),
        ]
        if options.get("descriptor"):
            steps[0] = ("Construct a three-sample raw neighborhood descriptor at each index, repeating edge values.", "逐点构造三个采样值的原始邻域描述符，在边界重复端点数值。")
        sources = ["shape" if options.get("descriptor") else "wdtw" if options.get("weighted") else "dtw", "registry"]
        parameters = {"local_cost": "squared Euclidean", "final_square_root": True, "normalization": "none", **options}
        if options.get("weighted"):
            parameters["g"] = 0.6
        if transformed:
            parameters["derivative"] = "adjacent first differences; n-1 outputs"
        if options.get("descriptor"):
            parameters.update(descriptor_radius=1, padding="edge repetition", reported_cost="descriptor-space")
        frames = _dp_frames(trace, transform=transform)
        if options.get("descriptor"):
            for frame, i in zip(frames[:4], (0, 3, 6, 9)):
                j = int(np.argmin(trace["cost"][i]))
                frame["caption"] = "Three-point neighborhoods describe context around each sample"
                frame["panel"] = {"kind": "bars", "title": f"Descriptors at x[{i + 1}] and y[{j + 1}]",
                                  "a": trace["a"][i].tolist(), "b": trace["b"][j].tolist(),
                                  "labels": ["previous", "center", "next"],
                                  "a_label": "x neighborhood", "b_label": "y neighborhood"}
        examples.append(_entry(identifier, title, intro, steps, formula,
                               [caveat, ("Signal scale, path constraints and final normalization must match before distances from different tools are compared.", "比较不同工具的数值之前，须统一信号尺度、路径约束和最终归一化。")], sources, trace,
                               parameters=parameters, frames=frames))

    soft = _soft_dtw(_X, _Y)
    self_x, self_y = _soft_dtw(_X, _X)["value"], _soft_dtw(_Y, _Y)["value"]
    for corrected in (False, True):
        trace = deepcopy(soft)
        if corrected:
            trace["value"] = soft["value"] - (self_x + self_y) / 2
        frames = _dp_frames(trace, result_label="divergence" if corrected else "soft objective")
        if corrected:
            for fraction in (0.25, 0.5, 0.75, 1.0):
                frames.append(_frame(3, "Subtract one half of each self-alignment score", {"kind": "bars", "title": "Cross score and self-corrections", "a": [soft["value"], -self_x / 2, -self_y / 2], "labels": ["cross", "-self x / 2", "-self y / 2"], "marker": min(2, int(fraction * 3))}, trace["value"], "divergence"))
        identifier = "soft_dtw_divergence" if corrected else "soft_dtw"
        intro = (
            ("The corrected soft-DTW divergence subtracts self-alignment terms from the cross-series soft score. This removes its nonzero self-cost by construction. The animation shows both the diffuse alignment occupancy and the three-term correction; theoretical nonnegativity and identification results depend on the ground-cost assumptions.",
             "修正 soft-DTW 散度从交叉序列分数中扣除两个自对齐项，因此相同输入的自代价按构造归零。动图展示分散的对齐占据权重和三项修正；非负性与可识别性的理论结论依赖局部代价条件。")
            if corrected else
            ("Soft-DTW replaces the hard minimum over alignment alternatives with a log-sum-exp soft minimum. Many paths contribute to the result, and the gradient with respect to local costs gives expected cell occupancy. The score is a smooth objective and may be negative or favor a point different from the input itself.",
             "Soft-DTW 用 log-sum-exp 软最小值替代路径选择中的硬最小值。多个路径共同贡献目标值，对局部代价求导得到每个单元格的期望占据权重。它是平滑目标，可以为负，也可能不在输入自身处取得最小值。"))
        steps = [
            ("Form the squared local discrepancy table and choose gamma=0.7.", "构造平方局部误差表，设平滑参数 gamma=0.7。"),
            ("Use -gamma*log(sum(exp(-previous/gamma))) in each DP update.", "每步动态规划使用 -gamma*log(sum(exp(-previous/gamma)))。"),
            ("Propagate derivatives backward to display expected alignment occupancy across multiple paths.", "反向传播导数，显示多个路径共同形成的期望对齐占据权重。"),
            (("Subtract half of softDTW(x,x) and half of softDTW(y,y)." if corrected else "Read the signed soft objective without choosing a unique path."),
             ("分别扣除 softDTW(x,x) 和 softDTW(y,y) 的一半。" if corrected else "读取有符号的软目标值，不选择唯一对齐路径。")),
        ]
        examples.append(_entry(identifier, "Soft-DTW divergence" if corrected else "Soft dynamic time warping", intro, steps,
            "D_gamma(x,y)=sDTW_gamma(x,y)-0.5*sDTW_gamma(x,x)-0.5*sDTW_gamma(y,y)" if corrected else "R_ij=(x_i-y_j)^2-gamma*log(sum_predecessors exp(-R/gamma))",
            [("Gamma controls the spread over alignments; this example uses squared local costs and no path band.", "Gamma 控制路径权重的分散程度；本例使用平方局部代价，不加路径窗口。"),
             ("A divergence is not automatically a metric; its properties depend on the ground cost and it need not satisfy the triangle inequality.", "散度并不自动成为度量；其性质依赖局部代价，也不必满足三角不等式。") if corrected else
             ("Raw soft-DTW can be negative and has an entropic self-bias; do not treat it as a conventional nonnegative distance.", "原始 soft-DTW 可以为负并具有熵正则化自偏差，不能直接作为普通非负距离理解。")],
            ["soft", "divergence"], trace, parameters={"gamma": 0.7, "local_cost": "squared Euclidean", "self_x": self_x, "self_y": self_y, "cross": soft["value"]}, frames=frames, label="divergence" if corrected else "soft objective"))

    edit_specs = [
        ("lcss_similarity", "LCSS matched fraction", "lcss", "similarity",
         ("LCSS counts an order-preserving set of sufficiently close sample pairs. Unmatched samples may be skipped, so the result describes matched coverage rather than the magnitude of every residual. The animation uses a tolerance of 0.35 and divides the match count by the shorter sequence length.",
          "LCSS 寻找保持先后顺序且足够接近的观测配对。未匹配点可以跳过，因此结果反映匹配覆盖率，不累加全部数值误差。本例容差为 0.35，并以较短序列长度归一化匹配数量。"),
         "L_ij=L_(i-1,j-1)+1 if |x_i-y_j|<=epsilon, else max(L_(i-1,j),L_(i,j-1)); s=L_nm/min(n,m)",
         ("Tolerance changes which pairs count as matches. Missing subsequences may be ignored by the shorter-length normalization.", "容差改变哪些配对算匹配；以较短长度归一化可能忽略较长序列中未匹配的部分。"), ["lcss", "local"]),
        ("lcss_distance", "One minus LCSS similarity", "lcss", "distance",
         ("This distance-like transform is one minus the normalized LCSS match count. It retains the order-preserving, tolerance-based matching rule. The final conversion reverses the direction of the score without restoring information discarded by skipped points or thresholding; different sequences can therefore receive zero distance.",
          "该距离形式等于一减归一化 LCSS 匹配数量，仍采用保持顺序的容差匹配。最后的变换只反转分数方向，无法恢复跳过观测或阈值判断丢失的信息，因此不同序列也可能得到零距离。"),
         "d_LCSS=1-LCSS_epsilon(x,y)/min(n,m)",
         ("One minus a similarity need not satisfy metric axioms. Zero here means full tolerance-based coverage of the shorter sequence.", "一减相似度不保证满足度量公理；这里的零值表示较短序列在容差内被完全覆盖。"), ["lcss", "local"]),
        ("edr", "Edit distance on real sequences", "edr", "distance",
         ("EDR replaces the size of a sample discrepancy with a thresholded substitution cost. A nearby pair costs zero, a mismatching substitution costs one, and insertions or deletions cost one. Dynamic programming finds the least expensive edit sequence; this example reports EchoTime's length-normalized default.",
          "EDR 把观测差异转成阈值替换代价：相近配对为零，不匹配替换为一，插入和删除也为一。动态规划寻找费用最低的编辑序列；本例采用 EchoTime 默认的长度归一化输出。"),
         "D_ij=min(D_(i-1,j)+1,D_(i,j-1)+1,D_(i-1,j-1)+1[|x_i-y_j|>epsilon]); d=D_nm/max(n,m)",
         ("The amplitude of a mismatch beyond epsilon is discarded. Normalization and epsilon must be specified when comparing implementations.", "超过 epsilon 后的误差幅度被丢弃；比较不同实现时须明确容差与归一化。"), ["local", "registry"]),
        ("swale_similarity", "SWALE rewards and gap costs", "swale", "alignment score",
         ("SWALE scores tolerance-based matches with a reward and unmatched observations with a gap penalty. Its recurrence combines the number of accepted matches with the price of omitted observations. This example uses reward 2, gap score -0.5 and epsilon 0.35; the raw score is not normalized to a probability.",
          "SWALE 对容差内的匹配给奖励，对未匹配的观测施加间隙惩罚。递推同时考虑接受的匹配数量与省略观测的费用。本例奖励为 2、间隙分数为 -0.5、容差为 0.35；原始分数没有归一化为概率。"),
         "S_ij=2+S_(i-1,j-1) for a tolerance match; otherwise max(S_(i-1,j)-0.5,S_(i,j-1)-0.5)",
         ("Rewards, gap penalties and sequence length influence the score scale. This implements the paper's scoring recurrence, not its FTSE acceleration.", "奖励、间隙惩罚和序列长度都会影响分数量级；本例演示论文的计分递推，没有实现 FTSE 加速。"), ["swale"]),
        ("erp", "Edit distance with a real gap", "erp", "distance",
         ("ERP charges the numerical cost of matching observations or matching one observation to a fixed gap value. The animation compares substitution with deletion and insertion at each prefix. Here the gap is 0.5 and the univariate local norm is absolute difference, matching EchoTime's explicit low-level calculation.",
          "ERP 对观测之间的替换以及观测与固定间隙值之间的匹配收取数值代价。动图逐个前缀比较替换、删除与插入。本例间隙值为 0.5，单变量局部范数为绝对差，与 EchoTime 底层计算一致。"),
         "D_ij=min(D_(i-1,j-1)+|x_i-y_j|,D_(i-1,j)+|x_i-g|,D_(i,j-1)+|y_j-g|)",
         ("Gap choice changes the cost. If the gap value is also a valid observation, distinct raw lists can have zero ERP distance.", "间隙值选择会改变代价；若间隙值也属于合法观测，不同原始列表可以得到零 ERP 距离。"), ["local", "registry"]),
        ("msm", "Move, split and merge", "msm", "distance",
         ("MSM transforms one ordered sequence through move, split and merge operations. Moving costs the absolute change in value. Split/merge costs depend on a base cost and neighboring values, so the recurrence uses local context instead of a fixed gap symbol. The animation displays its cumulative operation costs.",
          "MSM 通过移动、分裂和合并操作变换有序序列。移动费用是数值的绝对变化；分裂与合并费用取决于基础费用和邻近数值，因此递推使用局部上下文而非固定间隙符号。动图展示这些操作的累计费用。"),
         "C(v,a,b)=c if v lies between a,b; else c+min(|v-a|,|v-b|); D=min(move,split,merge)",
         ("This is a univariate definition with c=0.6. Multivariate dependent and independent generalizations require separate conventions.", "本例是 c=0.6 的单变量定义；多变量的联合式与独立式推广须另行指定。"), ["msm"]),
        ("twed", "Time warp edit distance", "twed", "distance",
         ("TWED combines edit penalties, consecutive-value changes and timestamp discrepancies. A match compares both the current pair and the preceding pair; deletions also include elapsed-time stiffness. The animation uses the zero-value, zero-time sentinel and infinite leading boundaries from EchoTime's corrected recurrence.",
          "TWED 联合考虑编辑惩罚、相邻数值变化和时间戳差异。匹配同时比较当前配对与前一个配对；删除还包括经过时间的刚度代价。动图使用 EchoTime 修正递推中的零值零时刻哨兵及无穷边界。"),
         "D=min(Dprev+|x_i-y_j|+|x_(i-1)-y_(j-1)|+nu*(|t_i-s_j|+|t_(i-1)-s_(j-1)|),delete_x,delete_y)",
         ("Positive stiffness, timestamps, the sentinel and boundary conventions matter to metric claims. A constrained or resampled approximation does not automatically inherit them.", "正刚度、时间戳、哨兵和边界约定都是度量结论的条件；加约束或重采样近似不自动继承这些性质。"), ["twed", "local"]),
        ("discrete_frechet", "Discrete Frechet bottleneck", "frechet", "distance",
         ("Discrete Frechet comparison minimizes the largest local separation along a monotone traversal. This differs from objectives that add every local mismatch: one difficult pair can determine the bottleneck. Here observations are points on the value axis, with order preserved and no extra time coordinate in the local norm.",
          "离散 Fréchet 比较最小化单调遍历过程中最大的局部距离。单个困难配对可能决定最终瓶颈。本例将观测视为数值轴上的点，保留其顺序，但局部范数不额外包含时间坐标。"),
         "F_ij=max(|x_i-y_j|,min(F_(i-1,j),F_(i,j-1),F_(i-1,j-1)))",
         ("Repeated vertices can make distinct raw vertex lists indistinguishable. Adding time as a coordinate changes the geometry and its scale.", "重复顶点可能使不同原始顶点列表无法区分；加入时间坐标会改变几何与尺度。"), ["frechet"]),
        ("needleman_wunsch_similarity", "Global sequence alignment", "nw", "alignment score",
         ("This numerical Needleman-Wunsch illustration aligns both full sequences using an explicit match/mismatch rule and linear gap costs. The entire prefix table contributes to a global solution ending at its bottom-right cell. The time-series scoring rule is specified here, rather than implied by the algorithm name.",
          "该数值 Needleman-Wunsch 示例使用明确的匹配／不匹配规则与线性间隙费用，对齐两条完整序列。全局解终止于前缀表右下角。本卡明确指定时间序列的计分规则，不将其视为算法名称隐含的唯一选择。"),
         "S_ij=max(S_(i-1,j-1)+s_ij,S_(i-1,j)-0.5,S_(i,j-1)-0.5); s_ij=2 if close else -1",
         ("The biological algorithm does not fix a numerical time-series substitution score. This educational adaptation uses epsilon=0.35 and linear, not affine, gaps.", "原始序列算法不规定数值时间序列的替换分数；本教学改写使用 epsilon=0.35 和线性间隙，不使用仿射间隙。"), ["sequence", "registry"]),
        ("smith_waterman_similarity", "Local sequence alignment", "sw", "alignment score",
         ("Smith-Waterman allows an alignment to restart at zero, so it can select matching internal subsequences while leaving unrelated ends unused. This explicit numerical example uses the same threshold substitution scores as the global card. The best cell may occur anywhere, and traceback stops when the score returns to zero.",
          "Smith-Waterman 允许分数从零重新开始，因此能选择内部匹配子序列，并不使用无关的两端。本数值示例采用与全局卡片相同的阈值替换计分。最优单元格可以位于任意位置，回溯在零分处停止。"),
         "S_ij=max(0,S_(i-1,j-1)+s_ij,S_(i-1,j)-0.5,S_(i,j-1)-0.5); result=max_ij S_ij",
         ("A high local alignment score does not establish whole-series similarity. Substitution and gap choices determine which segment wins.", "较高的局部对齐分数不能证明整段序列相似；替换与间隙设定决定获选片段。"), ["sequence", "registry"]),
    ]
    tx = np.cumsum([1, 0.8, 1.1, 0.9, 1.2, 1.0, 0.8, 1.2, 1.0, 0.9])
    ty = np.cumsum([0.9, 1.0, 0.9, 1.2, 0.8, 1.2, 1.0, 0.9, 1.1, 1.0])
    for identifier, title, kind, label, intro, formula, caveat, sources in edit_specs:
        trace = _msm(_X, _Y) if kind == "msm" else _edit(kind, _X, _Y, tx=tx, ty=ty)
        if identifier == "lcss_distance":
            trace["value"] = 1 - trace["value"]
        parameters = {"normalization": "none", "local_norm": "absolute difference"}
        if kind in {"lcss", "edr", "swale", "nw", "sw"}:
            parameters["epsilon"] = 0.35
        if kind in {"nw", "sw", "swale"}:
            parameters.update(match_reward=2.0, gap_score=-0.5)
        if kind in {"nw", "sw"}:
            parameters["mismatch_score"] = -1.0
        if kind == "erp":
            parameters["gap_value"] = 0.5
        if kind == "msm":
            parameters["c"] = 0.6
        if kind == "lcss":
            parameters["normalization"] = "match count / min(n,m)"
        if kind == "edr":
            parameters["normalization"] = "edit count / max(n,m)"
        if kind == "twed":
            parameters.update(lambda_=0.4, nu=0.2, t_x=tx.tolist(), t_y=ty.tolist(), sentinel=[0, 0], boundary="D00=0; other leading states infinite")
        operation = {
            "lcss": ("Count tolerance matches and carry forward the larger match count when skipping.", "累计容差内匹配，跳过观测时保留较大的匹配计数。"),
            "edr": ("Choose the cheapest substitution, insertion or deletion for each prefix.", "逐个前缀选择费用最低的替换、插入或删除。"),
            "swale": ("Reward a tolerance match; otherwise choose the less costly gap transition.", "对容差匹配给予奖励，否则选择费用较低的间隙转移。"),
            "erp": ("Compare matching x to y with matching either observation to gap g=0.5.", "比较 x 与 y 的匹配，以及任一观测与间隙 g=0.5 的匹配。"),
            "msm": ("Compare a move with context-dependent split and merge costs.", "比较移动费用与依赖上下文的分裂、合并费用。"),
            "twed": ("Combine value changes, time stiffness and deletion penalties in the minimum-cost recurrence.", "在最小代价递推中结合数值变化、时间刚度和删除惩罚。"),
            "frechet": ("Keep the larger of the present separation and the smallest predecessor bottleneck.", "在当前距离和最小前驱瓶颈之间取较大者。"),
            "nw": ("Maximize the global score with a match/mismatch or a linear gap transition.", "使用匹配／不匹配或线性间隙转移，最大化全局分数。"),
            "sw": ("Maximize the score with an additional zero restart option at every cell.", "在每个单元格增加从零开始选项，并最大化分数。"),
        }[kind]
        steps = [
            ("Set the stated local scoring rule, tolerance and boundary conditions.", "设置明确的局部计分规则、容差与边界条件。"),
            operation,
            (("Start at the maximum score and stop traceback at zero." if kind == "sw" else "Trace the selected predecessor operations from the complete-prefix state."),
             ("从最大分数处开始回溯，在零分处停止。" if kind == "sw" else "从完整前缀状态沿选定的前驱操作回溯。")),
            (("Convert the count to one minus its shorter-length-normalized value." if identifier == "lcss_distance" else "Read the final score with the normalization explicitly stated below."),
             ("将匹配数量除以较短长度，再用一减去该比例。" if identifier == "lcss_distance" else "按下方明确的归一化约定读取最终分数。")),
        ]
        local_title = "Tolerance match mask" if kind in {"lcss", "swale"} else "Substitution costs" if kind in {"edr", "erp"} else "Local match scores" if kind in {"nw", "sw"} else "Local comparison costs"
        dp_title = "Best prefix match counts" if kind == "lcss" else "Best prefix scores" if kind in {"nw", "sw", "swale"} else "Prefix bottlenecks" if kind == "frechet" else "Accumulated edit costs"
        frames = _dp_frames(trace, local_title=local_title, dp_title=dp_title, result_label=label)
        if kind == "twed":
            for f in frames[:4]:
                f["caption"] = "Match cost includes current, previous and timestamp discrepancies"
            for f, marker in zip(frames[:2], (3, 8)):
                f["caption"] = "Unequal sampling intervals enter the timestamp stiffness term"
                f["panel"] = {"kind": "lines", "title": "Explicit timestamps of the two inputs",
                              "a": tx.tolist(), "b": ty.tolist(), "marker": marker,
                              "a_label": "x timestamps", "b_label": "y timestamps"}
        if kind == "msm":
            def operation(v, a, b):
                return 0.6 if min(a, b) <= v <= max(a, b) else 0.6 + min(abs(v - a), abs(v - b))
            for f, i in zip(frames[:4], (2, 4, 6, 8)):
                j = i
                candidates = [trace["dp"][i - 1, j - 1] + abs(_X[i] - _Y[j]),
                              trace["dp"][i - 1, j] + operation(_X[i], _X[i - 1], _Y[j]),
                              trace["dp"][i, j - 1] + operation(_Y[j], _X[i], _Y[j - 1])]
                f["caption"] = "Compare move with context-dependent split and merge transitions"
                f["panel"] = {"kind": "bars", "title": f"Candidate totals at cell ({i + 1}, {j + 1})",
                              "a": candidates, "labels": ["move", "split/merge x", "split/merge y"],
                              "marker": int(np.argmin(candidates)), "a_label": "candidate total"}
        item = _entry(identifier, title, intro, steps, formula,
                      [caveat, ("The small arrays are an algorithm illustration, not evidence of retrieval or classification quality.", "这些小数组用于解释计算过程，不构成检索或分类性能证据。")], sources, trace,
                      definition="echotime" if kind in {"lcss", "edr", "erp", "twed"} else "reference", parameters=parameters, frames=frames, label=label)
        if kind in {"lcss", "edr", "erp", "twed"}:
            from echotime import similarity_methods as sm
            api_name = {"lcss_similarity": "lcss_similarity", "lcss_distance": "lcss_distance", "edr": "edr_distance", "erp": "erp_distance", "twed": "twed_distance"}[identifier]
            kwargs = {"epsilon": 0.35} if kind in {"lcss", "edr"} else {"gap_value": 0.5} if kind == "erp" else {"lambda_": 0.4, "nu": 0.2, "t_x": tx, "t_y": ty}
            observed = float(getattr(sm, api_name)(_X, _Y, **kwargs))
            if not np.isclose(observed, trace["value"], rtol=1e-12, atol=1e-12):
                raise AssertionError((identifier, observed, trace["value"]))
            item["checks"] = {"api": "echotime.similarity_methods." + api_name, "expected": trace["value"], "observed": observed, "tolerance": 1e-12}
        examples.append(item)

    # Separate channels intentionally have different best temporal correspondences.
    channels_x = np.vstack([_X, [0.2, 0.5, 1.2, 2.2, 2.9, 2.1, 1.1, 0.1, -0.2, 0.1]])
    channels_y = np.vstack([_Y, [0.4, 1.1, 2.3, 3.0, 2.0, 1.0, 0.2, -0.1, 0.0, 0.2]])
    base_options = {"dtw": {}, "cdtw": {"window": 1}, "wdtw": {"weighted": True}, "ddtw": {"derivative": True}}
    for base in ("dtw", "cdtw", "wdtw", "ddtw", "erp"):
        traces = [_edit("erp", a, b) if base == "erp" else _dtw(a, b, **base_options[base]) for a, b in zip(channels_x, channels_y)]
        values = [tr["value"] for tr in traces]
        result = float(np.mean(values))
        frames = []
        for channel, trace in enumerate(traces):
            # Each channel has its own complete DP problem and its own path.
            for fraction in (0.25, 0.5, 0.75, 1.0):
                shown = trace["dp"].copy()
                shown[math.ceil(len(shown) * fraction):] = np.nan
                frames.append(_frame(channel, f"Channel {channel + 1}: solve its own prefix table", _panel(shown, f"Channel {channel + 1} accumulated costs")))
            for fraction in (0.35, 0.7, 1.0):
                path = trace["path"][-max(1, math.ceil(len(trace["path"]) * fraction)):]
                frames.append(_frame(2, f"Channel {channel + 1}: retain its individual path", _panel(trace["dp"], f"Channel {channel + 1} path", path=path), values[channel], "channel distance"))
        for marker in (0, 1, 2, 2):
            frames.append(_frame(3, "Average the two distances after separate alignments", {"kind": "bars", "title": "Independent channel scores and mean", "a": values + [result], "labels": ["channel 1", "channel 2", "mean"], "marker": marker}, result, "mean distance"))
        item = _entry("independent_" + base, "Independent-channel " + base.upper(),
            (f"Independent {base.upper()} computes a separate alignment problem for every channel, then averages the resulting distances. The two channels in this example prefer different correspondences. Their paths are shown separately, making explicit that averaging final scores does not impose a shared multivariate warping path.",
             f"独立通道 {base.upper()} 为每个通道分别求解对齐问题，再平均最终距离。本例两个通道偏好的配对不同，动图分别显示各自路径，因此可直接看到平均分数不等于施加共享的多变量扭曲路径。"),
            [("Keep matching channel identities and define channelwise preprocessing.", "保持通道对应关系，并明确各通道预处理。"),
             (f"Solve the stated {base.upper()} problem independently for channel one and channel two.", f"分别求解通道一和通道二的 {base.upper()} 问题。"),
             ("Retain each channel's own alignment; different channels may select different time matches.", "保留各通道自身的对齐；不同通道可以选择不同时间匹配。"),
             ("Take the arithmetic mean of channel distances, with equal weights in this example.", "对通道距离取算术平均；本例使用相等权重。")],
            "d_independent(X,Y) = (d_base(X_channel1,Y_channel1)+d_base(X_channel2,Y_channel2))/2",
            [("Independent warping can break simultaneity across channels; use a shared-path definition when simultaneous events must remain coupled.", "各通道独立扭曲可能破坏通道间同时性；要求同步事件保持耦合时，应选择共享路径定义。"),
             ("Channel scale and aggregation convention matter. This atlas uses a mean; some libraries use a sum.", "通道尺度和聚合约定会影响结果；本图谱使用平均值，有些库使用求和。")],
            ["local" if base == "erp" else "wdtw" if base == "wdtw" else "dtw", "registry"],
            {"value": result}, parameters={"channels_x": channels_x.tolist(), "channels_y": channels_y.tolist(), "base": base, "aggregation": "arithmetic mean", "channel_values": values, **({"gap_value": 0.5} if base == "erp" else base_options[base])},
            frames=frames, x=channels_x[0], y=channels_y[0])
        item["input_label"] = "Channel 1 above; both channels and separate paths are recorded in parameters"
        if base == "ddtw":
            item["parameters"]["derivative_convention"] = "adjacent first differences"
        if base == "wdtw":
            item["parameters"]["g"] = 0.6
        if base == "erp":
            from echotime.similarity_methods import erp_distance
            observed = float(np.mean([erp_distance(a, b, gap_value=0.5) for a, b in zip(channels_x, channels_y)]))
            assert np.isclose(observed, result)
            item["checks"] = {"api": "mean of per-channel echotime.erp_distance (no standalone independent_erp API)", "expected": result, "observed": observed, "tolerance": 1e-12}
        examples.append(item)
    return examples


def _transform_panel(base, transform, title, *, marker_base=None, min_input=None):
    lo, hi = min(0.0, base * 1.25), max(1.0, base * 1.35)
    if min_input is not None:
        lo = min_input
    grid = np.sort(np.unique(np.r_[np.linspace(lo, hi, 49), base]))
    marker_base = base if marker_base is None else marker_base
    marker = int(np.argmin(abs(grid - marker_base)))
    return {"kind": "lines", "title": title, "x": grid.tolist(),
            "a": [float(transform(t)) for t in grid], "marker": marker,
            "a_label": "transformed score", "xlabel": "input to transform"}


def _scalar_frames(contributions, transform, *, term_title, transform_title):
    terms = np.asarray(contributions)
    cumulative = np.cumsum(terms)
    base = float(cumulative[-1])
    frames = []
    for count in (2, 4, 6, 8, len(terms)):
        count = min(count, len(terms))
        frames.append(_frame(0, "Compute the indicated contribution at each aligned index", {"kind": "bars", "title": term_title, "a": terms[:count].tolist(), "labels": [str(i + 1) for i in range(count)], "marker": count - 1, "a_label": "contribution"}, float(cumulative[count - 1]), "partial sum"))
    for count in (2, 4, 6, 8, len(terms)):
        count = min(count, len(terms))
        frames.append(_frame(1, "Accumulate the contributions into the base score", {"kind": "lines", "title": "Running total", "a": cumulative[:count].tolist(), "marker": count - 1, "a_label": "cumulative score"}, float(cumulative[count - 1]), "partial sum"))
    for q in np.linspace(min(0, base), max(0, base), 7):
        frames.append(_frame(2, "Evaluate the stated scalar transformation", _transform_panel(base, transform, transform_title, marker_base=q), transform(q), "transform output"))
    for _ in range(3):
        frames.append(_frame(3, "Read the kernel score for this complete pair", _transform_panel(base, transform, transform_title), transform(base), "kernel score"))
    return frames


def _kernel_entry(identifier, title, intro, steps, formula, caveats, sources, value, frames, parameters):
    item = _entry(identifier, title, intro, steps, formula, caveats, sources,
                  {"value": value}, parameters=parameters, frames=frames, label="kernel score")
    item["family"] = "kernel"
    return item


def _gak(x, y, sigma=1.0):
    squared = (np.asarray(x)[:, None] - np.asarray(y)[None, :]) ** 2
    gaussian = np.exp(-squared / (2 * sigma * sigma))
    local = gaussian / (2.0 - gaussian)
    n, m = local.shape
    d = np.zeros((n + 1, m + 1))
    d[0, 0] = 1.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i, j] = local[i - 1, j - 1] * (d[i - 1, j - 1] + d[i - 1, j] + d[i, j - 1])
    return {"local": local, "dp": d[1:, 1:], "value": float(d[-1, -1])}


def _kernel_examples():
    examples = []
    dot = float(np.dot(_X, _Y))
    squared = float(np.sum((_X - _Y) ** 2))
    common_steps = [
        ("Use the same aligned coordinate system for both vectors.", "对两个向量使用同一个已对齐坐标系。"),
        ("Compute and sum the coordinatewise contributions shown in the plot.", "计算图示逐坐标贡献并求和。"),
        ("Apply the specified scalar kernel transformation to that complete sum.", "对完整求和结果施加指定的标量核变换。"),
        ("Read the pair score; kernel magnitude is not a calibrated similarity probability.", "读取成对分数；核函数量级不是校准后的相似概率。"),
    ]
    elementary = [
        ("linear_kernel", "Linear inner-product kernel", dot, lambda q: q, _X * _Y,
         ("The linear kernel adds products of corresponding coordinates. Its animation shows which indices contribute positively or negatively before adding them into the inner product. It preserves amplitude and offset effects unless preprocessing removes them, and its scale grows with vector energy.",
          "线性核将对应坐标的乘积相加。动图先展示各位置的正负贡献，再累加成内积。若预处理没有消除幅度与偏移，它们会保留在结果中；分数量级随向量能量变化。"),
         "K(x,y)=sum_i x_i*y_i", "Coordinate products x_i*y_i", "Identity transform of the inner product", {},
         ("An inner product is not bounded by one and can be negative; normalization would produce a different kernel or cosine score.", "内积没有一的上界，也可以为负；归一化会产生不同的核或余弦分数。")),
        ("polynomial_kernel", "Polynomial kernel", (0.1 * dot + 1) ** 3, lambda q: (0.1 * q + 1) ** 3, _X * _Y,
         ("The polynomial kernel first computes an inner product, then applies a shifted integer power. Here degree three creates nonlinear interactions implicitly without constructing every product feature. The animation separates the coordinate sum from its nonlinear expansion, so the large final magnitude is not mistaken for a probability.",
          "多项式核先计算内积，再对平移后的结果取整数次幂。本例次数为三，隐式表示非线性交互而不逐一构造乘积特征。动图分开显示坐标求和与非线性展开，最终大数值不能解释为概率。"),
         "K(x,y)=(0.1*dot(x,y)+1)^3", "Coordinate products", "Cubic transformation", {"gamma": 0.1, "coef0": 1.0, "degree": 3},
         ("The usual positive-semidefinite guarantee uses a nonnegative scale/offset and integer degree. Large norms or degrees can dominate numerically.", "通常的半正定保证使用非负尺度、非负偏置和整数次数；较大范数或次数可能在数值上主导结果。")),
        ("sigmoid_kernel", "Sigmoid similarity transform", math.tanh(0.1 * dot - 0.5), lambda q: math.tanh(0.1 * q - 0.5), _X * _Y,
         ("This sigmoid score maps an affine inner product through tanh. The animation shows saturation: sufficiently large input scores compress into a narrow output range. The formula is commonly called a sigmoid kernel, but arbitrary scale and offset choices do not guarantee a positive-semidefinite Gram matrix.",
          "该 sigmoid 分数将内积的仿射变换送入 tanh。动图展示饱和现象：较大输入分数被压缩到很窄的输出范围。该公式常称为 sigmoid 核，但任意尺度与偏置选择不保证 Gram 矩阵半正定。"),
         "K(x,y)=tanh(0.1*dot(x,y)-0.5)", "Coordinate products", "Tanh of affine inner product", {"gamma": 0.1, "coef0": -0.5},
         ("A bounded output does not establish positive semidefiniteness or a probabilistic interpretation; saturation can hide changes in the input dot product.", "输出有界不能证明半正定性或概率解释；饱和可能掩盖输入内积变化。")),
        ("rbf_kernel", "Gaussian kernel on aligned values", math.exp(-0.4 * squared), lambda q: math.exp(-0.4 * q), (_X - _Y) ** 2,
         ("The Gaussian RBF kernel converts squared Euclidean discrepancy between aligned vectors into an exponentially decreasing score. The animation first accumulates squared residuals, then locates that total on the exponential curve. Its bandwidth controls how quickly disagreement reduces the score, while time alignment remains fixed.",
          "高斯 RBF 核将已对齐向量的平方欧氏差异转成指数递减分数。动图先累加平方残差，再把总量定位到指数曲线上。带宽控制分数随差异下降的速度，时间对齐保持固定。"),
         "K(x,y)=exp(-0.4*sum_i (x_i-y_i)^2)", "Squared aligned residuals", "Exponential similarity transformation", {"gamma": 0.4},
         ("Signal scaling changes effective bandwidth. Equal dimensionality and aligned coordinates are required by this illustrated vector kernel.", "信号缩放改变有效带宽；此向量核示例要求维度一致且坐标已对齐。")),
    ]
    for identifier, title, value, transform, terms, intro, formula, term_title, transform_title, parameters, caveat in elementary:
        examples.append(_kernel_entry(identifier, title, intro, common_steps, formula,
            [caveat, ("No local time warping is performed by this aligned-vector construction.", "此已对齐向量构造不执行局部时间扭曲。")], ["kernels"], value,
            _scalar_frames(terms, transform, term_title=term_title, transform_title=transform_title), {"preprocessing": "none", **parameters}))

    trace = _dtw(_X, _Y)
    base = trace["value"] ** 2
    transform = lambda q: math.exp(-0.7 * q)
    frames = _dp_frames(trace)
    for q in np.linspace(0, base, 5):
        frames.append(_frame(3, "Map the minimum accumulated DTW cost to a similarity score", _transform_panel(base, transform, "exp(-0.7 * DTW squared)", marker_base=q), transform(q), "kernel score"))
    examples.append(_kernel_entry("dtw_rbf_kernel", "Exponential transform of DTW",
        ("This construction first selects the minimum-cost DTW path and then exponentially transforms its squared distance. The animation shows the path calculation before the score conversion. Although the formula resembles a Gaussian kernel, replacing Euclidean distance by DTW does not automatically preserve positive semidefiniteness.",
         "该构造先选择最低代价 DTW 路径，再对距离平方做指数变换。动图先展示路径计算，再展示分数转换。将欧氏距离替换成 DTW 不自动保留高斯核的半正定性。"),
        [("Build squared local costs and a monotone DTW recurrence.", "构造平方局部代价与单调 DTW 递推。"),
         ("Select the path with the least accumulated discrepancy.", "选择累计差异最小的路径。"),
         ("Use that accumulated cost as DTW squared in exp(-gamma*cost).", "把该累计代价作为 DTW 平方代入 exp(-gamma*cost)。"),
         ("Interpret the decreasing score with gamma=0.7 and the stated local norm.", "结合 gamma=0.7 和明确的局部范数理解该递减分数。")],
        "K=exp(-0.7*DTW(x,y)^2), DTW uses squared costs then square root",
        [("A DTW-based exponential may produce an indefinite Gram matrix. Do not infer kernel-method guarantees from its name.", "DTW 指数形式可能得到不定 Gram 矩阵；不能从名称推断核方法保证。"),
         ("The value changes with the path band, local cost and distance normalization.", "路径窗口、局部代价和距离归一化都会改变结果。")], ["dtw", "gak"], transform(base), frames, {"gamma": 0.7, "base_distance": trace["value"], "squared_distance": base}))

    zx = (_X - np.mean(_X)) / np.std(_X)
    zy = (_Y - np.mean(_Y)) / np.std(_Y)
    correlations = np.correlate(zx, zy, mode="full") / (np.linalg.norm(zx) * np.linalg.norm(zy))
    lags = np.arange(-len(_Y) + 1, len(_X))
    winning = int(np.argmax(correlations))
    sbd = float(1 - correlations[winning])
    frames = []
    for marker in range(len(lags)):
        frames.append(_frame(min(2, marker // 7), "Sweep lag using full-series energy normalization", {"kind": "lines", "title": "Normalized cross-correlation at each lag", "x": lags.tolist(), "a": correlations.tolist(), "marker": marker, "a_label": "NCC", "xlabel": "lag"}, float(correlations[marker]), "lag NCC"))
    for q in np.linspace(0, sbd, 5):
        frames.append(_frame(3, "Convert the best lag to SBD, then apply exp(-2*SBD)", _transform_panel(sbd, lambda t: math.exp(-2 * t), "Exponential SBD transform", marker_base=q), math.exp(-2 * q), "kernel score"))
    examples.append(_kernel_entry("sbd_kernel", "Exponential transform of SBD",
        ("SBD selects the largest normalized cross-correlation over global shifts, then subtracts it from one. This atlas construction maps that SBD value through exp(-2*SBD). The lag sweep makes its shift tolerance visible, while its full-series normalization distinguishes it from overlap-normalized Pearson correlation.",
         "SBD 在全局平移中选择最大的归一化互相关，再用一减去该值。本图谱构造进一步计算 exp(-2*SBD)。动图逐个扫描滞后，展示平移容忍性；采用完整序列能量归一化，与重叠区域 Pearson 相关不同。"),
        [("Z-normalize both series using their own full-series mean and standard deviation.", "用各自完整序列的均值和标准差进行 z 标准化。"),
         ("Evaluate zero-padded cross-correlation at every global lag.", "在每个全局滞后处计算零填充互相关。"),
         ("Set SBD to one minus the largest full-energy-normalized correlation.", "令 SBD 等于一减完整能量归一化相关的最大值。"),
         ("Apply exp(-2*SBD) to obtain the stated kernel-like score.", "应用 exp(-2*SBD)，得到明确约定的核形式分数。")],
        "K=exp(-2*(1-max_lag NCC_lag(z(x),z(y))))",
        [("Maximizing over shifts and exponentiating a distance-like score do not establish positive semidefiniteness.", "对平移取最大值再指数化距离形式分数，不能证明半正定性。"),
         ("Only one global lag is chosen. Constant inputs have undefined statistical normalization and need an explicit software convention.", "只选择一个全局滞后；常数输入的统计归一化未定义，需要明确的软件约定。")], ["local", "registry"], math.exp(-2 * sbd), frames,
        {"gamma": 2.0, "normalize": True, "NCC_normalization": "full-series L2 energies", "best_lag": int(lags[winning]), "sbd": sbd}))

    soft = _soft_dtw(_X, _Y)
    divergence = soft["value"] - 0.5 * _soft_dtw(_X, _X)["value"] - 0.5 * _soft_dtw(_Y, _Y)["value"]
    frames = _dp_frames(soft, result_label="raw soft objective")
    for q in np.linspace(0, divergence, 5):
        frames.append(_frame(3, "Correct self-bias, then map divergence through exp(-D/gamma)", _transform_panel(divergence, lambda t: math.exp(-t / 0.7), "Exponential corrected soft-DTW", marker_base=q), math.exp(-q / 0.7), "kernel score"))
    examples.append(_kernel_entry("soft_dtw_kernel", "Exponential soft-DTW divergence",
        ("This imported atlas name denotes an exponential of the self-corrected soft-DTW divergence. It first includes contributions from multiple alignments, subtracts both self terms, then applies exp(-D/gamma). This explicit construction is separate from directly exponentiating raw soft-DTW or choosing a modified local kernel for GAK.",
         "本图谱名称对应自修正 soft-DTW 散度的指数形式。先综合多个对齐路径，减去两个自对齐项，再计算 exp(-D/gamma)。该明确构造区别于直接指数化原始 soft-DTW，也区别于为 GAK 选择修正局部核。"),
        [("Compute cross and self soft-DTW objectives with the same gamma and local cost.", "使用相同 gamma 和局部代价计算交叉及自对齐 soft-DTW。"),
         ("Inspect the diffuse occupancy of alternative alignments.", "检查备选对齐的分散占据权重。"),
         ("Subtract the self terms to obtain the corrected divergence D.", "扣除自对齐项得到修正散度 D。"),
         ("Evaluate exp(-D/gamma) using gamma=0.7.", "使用 gamma=0.7 计算 exp(-D/gamma)。")],
        "K=exp(-D_gamma/gamma); D_gamma=sDTW(x,y)-0.5*sDTW(x,x)-0.5*sDTW(y,y)",
        [("A corrected divergence does not by itself prove that its exponential is a positive-semidefinite kernel for an arbitrary ground cost.", "修正散度本身不能证明对任意局部代价，其指数形式都是半正定核。"),
         ("This gamma is used for both soft alignment and the final exponential; a separate outer bandwidth would define another variant.", "这里同一个 gamma 同时控制软对齐与最终指数变换；若另设外层带宽，则得到另一变体。")], ["divergence", "soft", "registry"], math.exp(-divergence / 0.7), frames,
        {"gamma": 0.7, "ground_cost": "squared Euclidean", "divergence": divergence}))

    gak = _gak(_X, _Y)
    for logarithmic in (False, True):
        frames = []
        for row in (2, 4, 6, 8):
            shown = gak["local"].copy()
            shown[row:] = np.nan
            frames.append(_frame(0, "Convert local squared discrepancy using phi/(2-phi)", _panel(shown, "Modified Gaussian local similarities")))
        for row in range(len(_X)):
            shown = gak["dp"].copy()
            shown[row + 1:] = np.nan
            frames.append(_frame(1, "Multiply local similarity by the sum of three prefix masses", _panel(shown, "Alignment path mass (sum-product DP)", cursor=(row, len(_Y) - 1)), gak["dp"][row, -1], "prefix path mass"))
        for row in (2, 4, 6, 8):
            frames.append(_frame(2, "All monotone paths contribute; no single optimal path is selected", _panel(gak["dp"], "Completed sum over alignment weights", cursor=(row, row)), gak["value"], "unnormalized GAK"))
        value = math.log(gak["value"] + 1e-12) if logarithmic else gak["value"]
        for _ in range(3):
            frames.append(_frame(3, "Take log of the complete path sum" if logarithmic else "Read the unnormalized all-path similarity", _transform_panel(gak["value"], lambda q: math.log(q + 1e-12) if logarithmic else q, "Log of positive path sum" if logarithmic else "Raw path-sum score", min_input=gak["value"] / 20 if logarithmic else None), value, "log GAK" if logarithmic else "GAK"))
        intro = (("Log GAK applies a logarithm to the positive sum of alignment weights. The underlying computation still uses sum-product dynamic programming, so all admissible paths contribute. This card uses Cuturi's modified Gaussian local kernel and reports log of the unnormalized path sum, with a stated tiny epsilon for numerical definition.",
                  "Log GAK 对正的对齐权重总和取对数。底层仍使用求和—乘积动态规划，因此全部允许路径共同贡献。本卡采用 Cuturi 的修正高斯局部核，报告未归一化路径和的对数，并明确微小 epsilon 的数值约定。") if logarithmic else
                 ("The Global Alignment Kernel adds products of local similarities over all monotone alignment paths. The dynamic program uses a sum rather than choosing a minimum-cost predecessor. Here the local kernel is phi/(2-phi), with phi a Gaussian, following a sufficient positive-definiteness construction; the displayed result is unnormalized.",
                  "全局对齐核将所有单调对齐路径上的局部相似度乘积相加。动态规划对前驱求和，不选择最低代价前驱。本例局部核为 phi/(2-phi)，其中 phi 是高斯核，对应一个充分的正定性构造；输出未做自相似归一化。"))
        formula = "log(K_GA+1e-12), K_GA=sum_paths product(phi/(2-phi)), phi=exp(-(x_i-y_j)^2/2)" if logarithmic else "K_ij=kappa_ij*(K_(i-1,j)+K_(i,j-1)+K_(i-1,j-1)); kappa=phi/(2-phi), K_00=1"
        examples.append(_kernel_entry("lgak" if logarithmic else "gak", "Log global alignment score" if logarithmic else "Global alignment kernel", intro,
            [("Build phi=exp(-squared_cost/(2*sigma^2)) with sigma=1, then kappa=phi/(2-phi).", "用 sigma=1 构造 phi=exp(-平方代价/(2*sigma^2))，再令 kappa=phi/(2-phi)。"),
             ("Multiply each local kappa by the sum of its three predecessor path weights.", "每个局部 kappa 乘以三个前驱路径权重之和。"),
             ("Accumulate every monotone alignment; do not replace the sum with a maximum or minimum.", "累加全部单调对齐，不能将求和换成最大或最小值。"),
             (("Apply log(K+epsilon) to compress the positive output scale." if logarithmic else "Read the unnormalized path sum; optional self-normalization is a separate step."),
              ("应用 log(K+epsilon) 压缩正输出的量级。" if logarithmic else "读取未归一化路径和；可选的自相似归一化是另一个步骤。"))], formula,
            [("The logarithm does not generally preserve positive semidefiniteness; log GAK is a score transformation, not an automatic Mercer kernel.", "取对数一般不保留半正定性；log GAK 是分数变换，不自动成为 Mercer 核。") if logarithmic else
             ("An arbitrary local similarity or hard path restriction does not inherit the stated positive-definiteness construction.", "任意局部相似度或硬路径限制都不自动继承上述正定性构造。"),
             ("Raw path sums depend strongly on sequence length and can overflow for long inputs; log-domain computation and self-normalization are distinct remedies.", "原始路径和强烈依赖长度，长输入可能溢出；对数域计算和自相似归一化是不同处理方式。")], ["gak", "registry"], value, frames,
            {"sigma": 1.0, "local_kernel": "phi/(2-phi)", "normalization": "none", "hard_path_band": None, "epsilon": 1e-12 if logarithmic else 0.0, "raw_gak": gak["value"]}))

    weights = np.exp(-(lags / 2.0) ** 2 / 2)
    weights /= weights.sum()
    terms = weights * correlations
    weighted = float(terms.sum())
    frames = []
    for marker in (0, 4, 9, 14, 18):
        frames.append(_frame(0, "Compute full-energy NCC for the indicated global lag", {"kind": "lines", "title": "Lag-wise NCC", "x": lags.tolist(), "a": correlations.tolist(), "marker": marker, "a_label": "NCC"}, correlations[marker], "lag NCC"))
    for marker in (0, 4, 9, 14, 18):
        frames.append(_frame(1, "Apply fixed symmetric lag weights, normalized to sum to one", {"kind": "bars", "title": "Gaussian lag weights (sigma=2)", "a": weights.tolist(), "labels": [str(v) for v in lags], "marker": marker}, weights[marker], "lag weight"))
    for marker in (0, 4, 9, 14, 18):
        frames.append(_frame(2, "Multiply each lag correlation by its weight", {"kind": "bars", "title": "Weighted lag contributions", "a": terms.tolist(), "labels": [str(v) for v in lags], "marker": marker}, terms[marker], "weighted contribution"))
    for count in (4, 8, 12, 16, 19):
        frames.append(_frame(3, "Sum weighted correlations across lags instead of taking their maximum", {"kind": "lines", "title": "Cumulative weighted NCC", "x": lags[:count].tolist(), "a": np.cumsum(terms)[:count].tolist(), "marker": count - 1, "a_label": "weighted total"}, float(terms[:count].sum()), "weighted score"))
    examples.append(_kernel_entry("weighted_ncc_kernel", "Weighted lag correlation score",
        ("This explicitly specified score averages normalized cross-correlations across lags using fixed symmetric weights. Nearby shifts receive more weight than large shifts; no winning lag is selected. The animation separates correlation, lag preference, multiplication and accumulation, making clear how the score differs from maximum NCC.",
         "该明确指定的分数使用固定对称权重对各滞后的归一化互相关求加权平均。较小位移得到较大权重，不选择获胜滞后。动图分别展示相关、滞后偏好、乘法和累计过程，说明其与最大 NCC 的计算区别。"),
        [("Z-normalize the input and compute full-energy NCC for all zero-padded shifts.", "对输入 z 标准化，并计算所有零填充位移的完整能量 NCC。"),
         ("Assign Gaussian lag weights with sigma=2 and normalize their sum to one.", "设置 sigma=2 的高斯滞后权重，并使权重总和为一。"),
         ("Multiply every lag correlation by its corresponding weight.", "将每个滞后相关乘以对应权重。"),
         ("Sum the contributions; this score averages lag evidence rather than selecting one lag.", "累计贡献；该分数平均滞后证据，不选取单个滞后。")],
        "K=sum_l w_l*NCC_l(z(x),z(y)); w_l proportional to exp(-l^2/(2*2^2))",
        [("Weighting rules are part of the definition. This generic atlas formula does not supply a positive-semidefinite guarantee for arbitrary lag weights.", "权重规则是定义的一部分；通用图谱公式不为任意滞后权重提供半正定保证。"),
         ("Full-series normalization, zero padding and centering differ from overlap-specific correlations. Constant inputs need a separate convention.", "完整序列归一化、零填充和中心化与重叠区域相关不同；常数输入需要另行约定。")], ["local", "registry"], weighted, frames,
        {"lag_sigma": 2.0, "weights": weights.tolist(), "lags": lags.tolist(), "normalization": "full-series energy; weights sum to one", "centered": True}))
    return examples


def build_examples():
    """Return the complete 24 elastic and 10 kernel educational entries."""
    examples = _elastic_examples() + _kernel_examples()
    assert len(examples) == 34
    assert len({e["id"] for e in examples}) == 34
    concise = {
        "dtw": ["Compute squared discrepancies for every sample pair.", "Accumulate each cost from its cheapest predecessor.", "Trace one minimum-cost monotone alignment path.", "Take the square root of the accumulated path cost."],
        "cdtw": ["Allow matches only within one sample of the diagonal.", "Accumulate squared costs inside the allowed band.", "Trace the cheapest path that respects the band.", "Take the square root of the constrained path cost."],
        "itakura_dtw": ["Build an endpoint-anchored parallelogram with slopes 1/2 and 2.", "Accumulate squared costs only in admissible cells.", "Trace the cheapest path inside the parallelogram.", "Take the square root of its accumulated cost."],
        "wdtw": ["Assign logistic weights according to index displacement.", "Multiply local squared discrepancies by those weights.", "Find a path minimizing the weighted cumulative cost.", "Take the square root of the weighted path cost."],
        "ddtw": ["Replace each series by its adjacent first differences.", "Build squared discrepancies between these differences.", "Find the minimum-cost path in difference space.", "Take the square root of that path's cumulative cost."],
        "wddtw": ["Take adjacent first differences of both inputs.", "Weight squared difference costs by index displacement.", "Find the cheapest path through the weighted table.", "Take the square root of the accumulated objective."],
        "shape_dtw": ["Describe each sample using its three-point neighborhood.", "Compare descriptors using squared Euclidean cost.", "Find the minimum-cost path between descriptor sequences.", "Report the square-root descriptor-space objective."],
        "soft_dtw": ["Compute squared local costs and set gamma to 0.7.", "Replace hard predecessor minima by a soft minimum.", "Propagate derivatives to obtain expected cell occupancy.", "Read the signed soft objective; no unique path is selected."],
        "soft_dtw_divergence": ["Compute cross and self soft-DTW with the same gamma.", "Use soft minima to combine alternative alignments.", "Inspect the cross-alignment occupancy matrix.", "Subtract half of each self score from the cross score."],
        "lcss_similarity": ["Mark pairs whose absolute difference is at most 0.35.", "Count ordered matches while allowing unmatched samples to be skipped.", "Trace the chosen matched pairs in their original order.", "Divide the match count by the shorter sequence length."],
        "lcss_distance": ["Mark sample pairs within the tolerance of 0.35.", "Find the largest order-preserving match count.", "Trace the accepted pairs while leaving gaps unmatched.", "Return one minus the shorter-length-normalized match count."],
        "edr": ["Assign substitution cost zero inside tolerance, one outside.", "Compare substitution with unit-cost insertion and deletion.", "Trace the cheapest edit sequence through the prefix table.", "Divide the edit cost by the longer sequence length."],
        "swale_similarity": ["Use match reward 2, gap score -0.5 and tolerance 0.35.", "Reward a match; otherwise select the better gap transition.", "Trace the selected ordered matches and gaps.", "Read the unnormalized alignment score."],
        "erp": ["Choose gap value 0.5 and absolute local differences.", "Compare substitution with matching either sample to the gap.", "Trace the minimum-cost sequence of edit operations.", "Sum the chosen edit costs without length normalization."],
        "msm": ["Compare move costs with context-dependent split and merge costs.", "Accumulate the cheapest operation for each prefix pair.", "Trace the selected move, split and merge decisions.", "Read the total operation cost with base penalty 0.6."],
        "twed": ["Keep explicit timestamps and the common zero-time sentinel.", "Combine current, previous, time and deletion costs.", "Trace minimum-cost operations from infinite leading boundaries.", "Read TWED with lambda 0.4 and stiffness 0.2."],
        "discrete_frechet": ["Measure the absolute separation of each ordered sample pair.", "Keep the larger of local separation and best predecessor bottleneck.", "Trace a monotone traversal with the smallest bottleneck.", "Report its largest local separation."],
        "needleman_wunsch_similarity": ["Define tolerance-based match scores and linear gap costs.", "Maximize the global alignment score for every prefix pair.", "Trace from the complete-prefix cell through the selected operations.", "Read the score for aligning both full sequences."],
        "smith_waterman_similarity": ["Define tolerance-based match scores and linear gap costs.", "Allow every prefix score to restart at zero.", "Trace from the best cell until the score returns to zero.", "Report the highest-scoring local alignment."],
        "linear_kernel": ["Keep both vectors on their aligned coordinate grid.", "Multiply each corresponding pair of values.", "Add the positive and negative coordinate contributions.", "Read the complete inner product without normalization."],
        "polynomial_kernel": ["Keep both vectors on their aligned coordinate grid.", "Sum coordinate products into an inner product.", "Scale by 0.1, add one and take the third power.", "Read the polynomial score; its scale is not a probability."],
        "sigmoid_kernel": ["Keep both vectors on their aligned coordinate grid.", "Sum coordinate products into an inner product.", "Apply tanh to 0.1 times the inner product minus 0.5.", "Read the saturating score with the stated parameters."],
        "rbf_kernel": ["Compare corresponding values on the fixed time grid.", "Accumulate their squared residuals.", "Map the total cost through exp(-0.4 times cost).", "Read the Gaussian similarity for the complete pair."],
        "dtw_rbf_kernel": ["Build a squared-cost DTW table.", "Find the minimum-cost monotone alignment path.", "Use the accumulated cost as the squared DTW distance.", "Map that cost through exp(-0.7 times cost)."],
        "sbd_kernel": ["Z-normalize each input using its full-series statistics.", "Sweep global lags using full-energy normalized correlation.", "Set SBD to one minus the largest lag correlation.", "Compute exp(-2 times SBD)."],
        "soft_dtw_kernel": ["Compute cross and self soft-DTW with gamma 0.7.", "Inspect the diffuse occupancy of alternative alignments.", "Subtract the self terms to obtain the corrected divergence.", "Compute exp(-divergence / 0.7)."],
        "gak": ["Convert Gaussian local similarities using phi / (2 - phi).", "Multiply each local score by the sum of three prefix masses.", "Accumulate all monotone alignments without selecting one path.", "Read the unnormalized all-path similarity."],
        "lgak": ["Convert Gaussian local similarities using phi / (2 - phi).", "Accumulate alignment weights by sum-product dynamic programming.", "Retain the positive contribution of every monotone path.", "Take log of the path sum plus epsilon 1e-12."],
        "weighted_ncc_kernel": ["Compute full-energy NCC over zero-padded global shifts.", "Assign symmetric Gaussian lag weights that sum to one.", "Multiply each lag correlation by its corresponding weight.", "Sum across lags instead of selecting a winning shift."],
    }
    for base in ("dtw", "cdtw", "wdtw", "ddtw", "erp"):
        concise["independent_" + base] = [
            "Keep matching channel identities and separate their inputs.",
            f"Solve the stated {base.upper()} recurrence separately for each channel.",
            "Retain each channel's own temporal alignment path.",
            "Average the final channel distances with equal weights.",
        ]
    for example in examples:
        example["animation_steps_en"] = concise[example["id"]]
        assert len(example["animation_steps_en"]) == 4
        assert max(map(len, example["animation_steps_en"])) <= 85
    return examples
