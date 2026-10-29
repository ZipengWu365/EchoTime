#!/usr/bin/env python3
"""Rebuild the finite, deterministic data and media for the similarity lab.

This is an educational reference implementation, not a new public EchoTime
similarity API or a benchmark. The browser only renders these saved calculations.
HTML/JS are maintained beside the generated data. Run ``--check`` to validate the
committed bundle; run without arguments to regenerate JSON, GIF, PNG and hashes.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/echotime/data/similarity_lab"
N = 64
LEVELS = 21
BAND = 8
BLOCKS = 8
EPSILON = 0.25
COLORS = dict(bg="#101e2b", panel="#172a3b", grid="#2a4052", text="#f1f5f8",
              muted="#acbdcc", a="#5ad6d5", b="#ff9d86", gold="#ffd16d")
SOURCE = "https://github.com/ZipengWu365/EchoTime/blob/main/tools/build_similarity_lab.py"
SOURCES = {
    "rmse": ("NumPy: arithmetic mean", "https://numpy.org/doc/stable/reference/generated/numpy.mean.html"),
    "pearson": ("SciPy: Pearson correlation", "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"),
    "sbd": ("aeon: shape-based distance", "https://www.aeon-toolkit.org/en/stable/api_reference/auto_generated/aeon.distances.sbd_distance.html"),
    "dtw": ("tslearn: DTW and path constraints", "https://tslearn.readthedocs.io/en/stable/user_guide/dtw.html"),
    "derivative": ("NumPy: first differences", "https://numpy.org/doc/stable/reference/generated/numpy.diff.html"),
    "dft": ("NumPy: real DFT and Hermitian symmetry", "https://numpy.org/doc/stable/reference/generated/numpy.fft.rfft.html"),
    "acf": ("statsmodels: adjusted ACF", "https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.acf.html"),
    "paa": ("tslearn: PAA", "https://tslearn.readthedocs.io/en/stable/gen_modules/piecewise/tslearn.piecewise.PiecewiseAggregateApproximation.html"),
    "sax": ("Lin et al. (2007): SAX and MINDIST", "https://www.cs.ucr.edu/~stelo/papers/DMKD07b.pdf"),
    "lcss": ("tslearn: LCSS", "https://tslearn.readthedocs.io/en/stable/gen_modules/metrics/tslearn.metrics.lcss.html"),
}


def baseline() -> np.ndarray:
    """A deliberately asymmetric synthetic waveform, with two local events."""
    t = np.arange(N, dtype=float) / N
    return (0.15 + 0.75 * np.sin(2 * np.pi * t)
            + 0.32 * np.sin(6 * np.pi * t + 0.5)
            + 0.85 * np.exp(-0.5 * ((t - 0.32) / 0.04) ** 2)
            - 0.55 * np.exp(-0.5 * ((t - 0.72) / 0.025) ** 2)
            + 0.25 * t)


TRANSFORMS = [
    dict(id="offset", title="Vertical offset", strength="Added amplitude", unit="amplitude",
         description="B = A + 1.5s. Every timestamp keeps its original position.",
         observe="Compare raw RMSE with z-RMSE: removing each series' mean removes this offset."),
    dict(id="gain", title="Positive gain", strength="Amplitude multiplier", unit="times",
         description="B = (1 + 1.4s) A. The multiplier stays positive; there is no clipping.",
         observe="Pearson and z-RMSE discard positive amplitude scaling; raw amplitude methods retain it."),
    dict(id="shift", title="Circular global shift", strength="Rightward circular shift", unit="samples",
         description="B = roll(A, level), for integer levels 0 to 20. Samples wrap at the boundary.",
         observe="DFT magnitudes are unchanged by a circular shift. SBD searches zero-padded linear lags, so boundary loss can remain."),
    dict(id="warp", title="Local time warp", strength="Maximum sampling displacement", unit="samples",
         description="B[i] = interp(A, i + 6s sin²(pi i/63)). The sampling map is increasing and fixes both endpoints.",
         observe="DTW can change local correspondences within its eight-sample band. Interpolation can still leave residual error."),
    dict(id="spike", title="Local pulse / event", strength="Added pulse height", unit="amplitude",
         description="B[i] = A[i] + 3s exp(-0.5((i-44)/1.2)²). Only a short region changes appreciably.",
         observe="Pointwise costs locate the event. LCSS can leave it unmatched, depending on its amplitude tolerance."),
    dict(id="phase", title="Fourier phase change", strength="Phase-change fraction", unit="fraction",
         description="Rotate interior rFFT bins by s*pi*sin(0.83k). Keep the original real DC and Nyquist coefficients; invert with irFFT.",
         observe="All rFFT magnitudes stay fixed while the waveform changes. Finite-window ACF need not stay fixed."),
    dict(id="reversal", title="Blend toward time reversal", strength="Reversal mixture", unit="fraction",
         description="B = (1-s)A + s reverse(A). At s=1 the order is exactly reversed; intermediate mixtures need not preserve the spectrum.",
         observe="At full reversal, DFT magnitudes and finite-window ACF coincide. Pointwise and order-preserving alignments can still differ."),
]


def transform(x: np.ndarray, kind: str, level: int) -> tuple[np.ndarray, dict]:
    if not 0 <= level < LEVELS:
        raise ValueError("level must be an integer in [0, 20]")
    s = level / (LEVELS - 1)
    i = np.arange(len(x), dtype=float)
    if kind == "offset":
        return x + 1.5 * s, {"amount": 1.5 * s, "label": f"offset +{1.5*s:.3f}"}
    if kind == "gain":
        return x * (1 + 1.4 * s), {"amount": 1 + 1.4 * s, "label": f"gain ×{1+1.4*s:.3f}"}
    if kind == "shift":
        return np.roll(x, level), {"amount": level, "label": f"circular shift {level} samples", "boundary": "wrap"}
    if kind == "warp":
        sample_map = i + 6 * s * np.sin(np.pi * i / (len(x) - 1)) ** 2
        return np.interp(sample_map, i, x), {"amount": float(np.max(sample_map-i)), "label": f"local warp ≤{6*s:.2f} samples", "sample_map": sample_map.tolist()}
    if kind == "spike":
        return x + 3 * s * np.exp(-0.5 * ((i - 44) / 1.2) ** 2), {"amount": 3 * s, "label": f"pulse height {3*s:.2f}", "center": 44, "width": 1.2}
    if kind == "phase":
        spectrum = np.fft.rfft(x, norm="ortho")
        k = np.arange(1, len(spectrum) - 1)
        spectrum[1:-1] *= np.exp(1j * s * np.pi * np.sin(0.83 * k))
        return np.fft.irfft(spectrum, n=len(x), norm="ortho"), {"amount": s, "label": f"phase fraction {s:.2f}", "dc_and_nyquist": "unchanged real coefficients"}
    if kind == "reversal":
        return (1 - s) * x + s * x[::-1], {"amount": s, "label": f"reversal mixture {s:.2f}"}
    raise ValueError(f"Unknown transform: {kind}")


def zscore(x: np.ndarray) -> np.ndarray:
    std = np.std(x, ddof=0)
    if std < 1e-12:
        raise ValueError("The lab excludes constant sequences; z-score would be undefined.")
    return (x - np.mean(x)) / std


def acf(x: np.ndarray, lags: int = 12) -> np.ndarray:
    a = x - np.mean(x)
    return np.asarray([np.dot(a[:-k], a[k:]) / ((len(a) - k) * np.mean(a*a))
                       for k in range(1, lags + 1)])


def dtw(x: np.ndarray, y: np.ndarray, radius: int = BAND) -> tuple[float, list[list[int]], np.ndarray]:
    """Squared local cost, endpoint-constrained monotone path, no normalization."""
    n, m = len(x), len(y)
    acc = np.full((n + 1, m + 1), np.inf)
    parent = np.full((n + 1, m + 1, 2), -1, dtype=int)
    acc[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(max(1, i-radius), min(m, i+radius) + 1):
            choices = [(i-1, j-1), (i-1, j), (i, j-1)]
            p = min(choices, key=lambda q: acc[q])
            acc[i, j] = (x[i-1] - y[j-1]) ** 2 + acc[p]
            parent[i, j] = p
    if not np.isfinite(acc[-1, -1]):
        raise ValueError("The chosen band has no complete alignment path")
    i, j = n, m
    pairs = []
    while i and j:
        pairs.append([i - 1, j - 1])
        i, j = parent[i, j]
    pairs.reverse()
    per_a = np.zeros(n)
    for i, j in pairs:
        per_a[i] += (x[i] - y[j]) ** 2
    return float(np.sqrt(acc[-1, -1])), pairs, per_a


def lcss(x: np.ndarray, y: np.ndarray, epsilon: float = EPSILON,
         radius: int = BAND) -> tuple[float, list[list[int]], np.ndarray]:
    """Ordered one-to-one matches, with amplitude and temporal tolerances."""
    n, m = len(x), len(y)
    counts = np.zeros((n+1, m+1), dtype=int)
    action = np.zeros((n+1, m+1), dtype=np.int8)
    for i in range(1, n+1):
        for j in range(1, m+1):
            match = abs(i-j) <= radius and abs(x[i-1]-y[j-1]) <= epsilon
            diagonal = counts[i-1, j-1]+1 if match else -1
            options = [diagonal, counts[i-1, j], counts[i, j-1]]
            action[i, j] = int(np.argmax(options))
            counts[i, j] = options[action[i, j]]
    i, j = n, m
    pairs = []
    while i and j:
        if action[i, j] == 0:
            pairs.append([i-1, j-1])
            i, j = i-1, j-1
        elif action[i, j] == 1:
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    matched = np.zeros(n)
    for i, _ in pairs:
        matched[i] = 1
    return len(pairs) / min(n, m), pairs, matched


def method_definitions(x: np.ndarray) -> list[dict]:
    a = zscore(x)
    definitions = [
        dict(id="rmse", title="Raw RMSE", kind="lines", a=x, axis=np.arange(N),
             unit="amplitude", result="RMSE", direction="lower", preprocess="Raw amplitudes; no normalization.",
             keeps="This view keeps absolute level, amplitude and timestamp identity.",
             allows="It allows no time shift or local realignment.",
             caution="A vertical offset is a real difference under this rule, even when both shapes look alike.",
             formula="sqrt(sum_i (A[i]-B[i])² / n)", parameters="n=64; equally spaced samples", xlabel="Sample index", ylabel="Raw amplitude",
             contribution="Squared residual / n; bars sum to RMSE²", contribution_unit="amplitude²", source="rmse"),
        dict(id="zrmse", title="z-normalized RMSE", kind="lines", a=a, axis=np.arange(N),
             unit="z units", result="z-RMSE", direction="lower", preprocess="Separate mean removal and population-SD scaling for A and B.",
             keeps="This view keeps fluctuations at the same timestamps after standardization.",
             allows="It allows an additive offset and a positive gain to disappear.",
             caution="It still penalizes phase or timing changes. Constant sequences are excluded from this lab.",
             formula="sqrt(mean((z(A)-z(B))²))", parameters="z(v)=(v-mean(v))/std(v, ddof=0)", xlabel="Sample index", ylabel="Standardized amplitude",
             contribution="Squared standardized residual / n; sum = z-RMSE²", contribution_unit="z units²", source="pearson"),
        dict(id="pearson", title="Pearson correlation", kind="lines", a=a, axis=np.arange(N),
             unit="coefficient [-1, 1]", result="r", direction="higher", preprocess="Separate mean removal and population-SD scaling for A and B.",
             keeps="This view keeps same-time linear co-fluctuation and its sign.",
             allows="It allows offset and positive gain; a negative gain reverses the sign.",
             caution="Correlation is not amplitude agreement. Here z-RMSE² = 2(1-r), up to rounding.",
             formula="r = sum_i z(A)[i] z(B)[i] / n", parameters="No lag search; no significance test", xlabel="Sample index", ylabel="Standardized amplitude",
             contribution="Signed product / n; bars sum to r", contribution_unit="coefficient contribution", source="pearson"),
        dict(id="sbd", title="SBD / best linear lag NCC", kind="lines", a=a, axis=np.arange(N),
             unit="dimensionless", result="1 - max NCC", direction="lower", preprocess="Per-series z-score, then zero-padded linear cross-correlation.",
             keeps="This view keeps standardized waveform agreement under one global lag.",
             allows="It allows a single shift, offset and positive gain; it cannot locally stretch time.",
             caution="This is not circular correlation. Plot gaps are zero-padded terms; lost support can reduce the score. Full-series energies remain in the denominator.",
             formula="1 - max_l sum_i z(A)[i] z(B)[i-l] / (||z(A)|| ||z(B)||)", parameters="All integer lags -63…63; out-of-range samples=0", xlabel="A index after shifting B", ylabel="Standardized amplitude",
             contribution="NCC at every linear lag; gold line marks the chosen lag", contribution_unit="NCC coefficient", source="sbd"),
        dict(id="dtw", title="DTW with an eight-sample band", kind="alignment", a=x, axis=np.arange(N),
             unit="amplitude", result="sqrt(path cost)", direction="lower", preprocess="Raw amplitudes; no z-score.",
             keeps="This view keeps amplitude and chronological order, including both endpoints.",
             allows="It allows repeated matches and local timing changes inside a fixed band.",
             caution="It returns sqrt(total squared path cost), not RMSE or a path-length-normalized score. The band can prevent a desired match.",
             formula="sqrt(min_path sum_(i,j) (A[i]-B[j])²)", parameters="|i-j|≤8; steps (1,1),(1,0),(0,1); endpoint constrained", xlabel="Original sample indices", ylabel="Raw amplitude",
             contribution="Squared costs grouped by A index; sum = DTW²", contribution_unit="amplitude²", source="dtw"),
        dict(id="derivative", title="First-difference RMSE", kind="lines", a=np.diff(x), axis=np.arange(N-1),
             unit="amplitude / sample", result="difference RMSE", direction="lower", preprocess="First differences of raw amplitudes; sampling interval=1.",
             keeps="This view keeps local upward and downward increments at the same intervals.",
             allows="It allows a constant vertical offset to disappear; positive gain still matters.",
             caution="This is a chosen derivative comparison, not derivative-DTW. Noise and narrow events can produce large differences.",
             formula="sqrt(mean((diff(A)-diff(B))²))", parameters="diff(v)[i]=v[i+1]-v[i]; no smoothing or alignment", xlabel="Interval start index", ylabel="Amplitude change / sample",
             contribution="Squared increment residual / 63; sum = result²", contribution_unit="(amplitude/sample)²", source="derivative"),
        dict(id="dft", title="Fourier-magnitude distance", kind="features", a=np.abs(np.fft.rfft(x, norm="ortho")), axis=np.arange(N//2+1),
             unit="orthonormal amplitude", result="magnitude L2", direction="lower", preprocess="Raw input; orthonormal rFFT; keep magnitudes including DC.",
             keeps="This view keeps the strength of every non-negative frequency, including the mean.",
             allows="It allows phase changes, circular shifts and exact reversal to have identical features.",
             caution="The 33 unique bins are unweighted; interior bins are not multiplied by sqrt(2). This is not waveform Euclidean distance or physical PSD.",
             formula="|| abs(rFFT_ortho(A)) - abs(rFFT_ortho(B)) ||₂", parameters="64-point transform; norm=ortho; no detrending/windowing", xlabel="Frequency bin k (frequency=k/64 per sample)", ylabel="Orthonormal DFT magnitude",
             contribution="Squared magnitude gaps; sum = magnitude L2²", contribution_unit="orthonormal amplitude²", source="dft"),
        dict(id="acf", title="Autocorrelation-profile distance", kind="features", a=acf(x), axis=np.arange(1,13),
             unit="ACF coefficient", result="ACF L2", direction="lower", preprocess="Remove each mean; divide lag products by (n-lag) × population variance.",
             keeps="This view keeps within-series recurrence at lags 1 through 12.",
             allows="It allows offset, nonzero gain and exact reversal to share the same ACF.",
             caution="This is finite-window adjusted ACF, not circular ACF. Circular shifts or arbitrary phase changes need not leave it fixed; adjusted values may exceed ±1.",
             formula="acf_v(k)=sum_t (v[t]-mean(v))(v[t+k]-mean(v))/((n-k)var(v)); L2 gap", parameters="Lags 1…12; lag 0 omitted; adjusted denominator", xlabel="Lag (samples)", ylabel="Adjusted ACF coefficient",
             contribution="Squared ACF gaps; sum = ACF L2²", contribution_unit="coefficient²", source="acf"),
        dict(id="paa", title="PAA block-mean distance", kind="features", a=x.reshape(BLOCKS,-1).mean(axis=1), axis=np.arange(BLOCKS),
             unit="amplitude", result="block-mean L2", direction="lower", preprocess="Raw input; average eight disjoint blocks of eight samples.",
             keeps="This view keeps the coarse amplitude profile and the order of its blocks.",
             allows="It allows within-block fluctuations to disappear when their averages agree.",
             caution="The score is an unscaled feature L2. It does not include the sqrt(n/blocks) factor used for the usual Euclidean lower bound.",
             formula="||PAA_8(A)-PAA_8(B)||₂", parameters="8 equal non-overlapping blocks; fixed boundaries", xlabel="Block index (eight samples per block)", ylabel="Raw block mean",
             contribution="Squared block-mean gaps; sum = feature L2²", contribution_unit="amplitude²", source="paa"),
        dict(id="sax", title="SAX MINDIST lower bound", kind="symbols", a=a.reshape(BLOCKS,-1).mean(axis=1), axis=np.arange(BLOCKS),
             unit="z units (lower bound)", result="MINDIST", direction="lower", preprocess="Per-series z-score → eight PAA means → four Gaussian-quantile symbols.",
             keeps="This view keeps ordered coarse levels after standardization and quantization.",
             allows="It allows offset, positive gain and some nearby symbolic levels to share a zero lower bound.",
             caution="Zero MINDIST does not prove equal waveforms or even equal symbols: adjacent symbol intervals have zero minimum separation.",
             formula="sqrt((n/8) × sum_blocks gap(symbol_A,symbol_B)²)", parameters="Alphabet a,b,c,d; breakpoints -0.67448975,0,+0.67448975", xlabel="Block index (eight standardized samples)", ylabel="Standardized PAA mean + symbol",
             contribution="Eight × squared interval gaps; sum = MINDIST²", contribution_unit="z units²", source="sax"),
        dict(id="lcss", title="LCSS tolerance matches", kind="alignment", a=x, axis=np.arange(N),
             unit="matched fraction [0, 1]", result="matched / 64", direction="higher", preprocess="Raw amplitudes; no z-score.",
             keeps="This view keeps the longest ordered set of one-to-one tolerance matches.",
             allows="It allows skips and timing differences within eight samples; unmatched points carry no squared-error penalty.",
             caution="The score depends on epsilon in raw amplitude units. A high matched fraction can hide a local event that was skipped.",
             formula="max_ordered_matches count / min(len(A),len(B))", parameters="|A[i]-B[j]|≤0.25; |i-j|≤8; strictly increasing matched indices", xlabel="Original sample indices", ylabel="Raw amplitude",
             contribution="Matched A positions (1) and skipped positions (0)", contribution_unit="match indicator", source="lcss"),
    ]
    for method in definitions:
        method["a"] = method["a"].tolist()
        method["axis"] = method["axis"].tolist()
        title, url = SOURCES[method.pop("source")]
        method["sources"] = [{"title": title, "url": url}, {"title": "Exact lab definitions and generator", "url": SOURCE}]
    sax = next(d for d in definitions if d["id"] == "sax")
    sax["breakpoints"] = [NormalDist().inv_cdf(p) for p in (0.25,0.5,0.75)]
    sax["symbols_a"] = np.searchsorted(sax["breakpoints"], sax["a"], side="right").tolist()
    return definitions


def evaluate(x: np.ndarray, y: np.ndarray) -> dict:
    """Every card uses this same x/y. Per-card preprocessing is explicit."""
    ax, by = zscore(x), zscore(y)
    out = {}

    def distance(name, a, b, scale=1.0):
        c = np.asarray((a-b)**2 * scale)
        out[name] = dict(value=float(np.sqrt(np.sum(c))), b=np.asarray(b).tolist(), contribution=c.tolist())

    distance("rmse", x, y, 1/len(x))
    distance("zrmse", ax, by, 1/len(x))
    c = ax * by / len(x)
    out["pearson"] = dict(value=float(np.sum(c)), b=by.tolist(), contribution=c.tolist())
    cc = np.correlate(ax, by, mode="full") / (np.linalg.norm(ax) * np.linalg.norm(by))
    lags = np.arange(-len(y)+1, len(x))
    best = int(np.argmax(cc))
    lag = int(lags[best])
    pairs = [[i, i-lag] for i in range(len(x)) if 0 <= i-lag < len(y)]
    aligned = [float(by[i-lag]) if 0 <= i-lag < len(y) else None for i in range(len(x))]
    out["sbd"] = dict(value=float(1-cc[best]), b=aligned, contribution=cc.tolist(),
                      contribution_axis=lags.tolist(), best_lag=lag, pairs=pairs,
                      detail=f"Chosen lag {lag:+d}; {len(pairs)}/64 overlapping positions. Full energies normalize every lag.")
    value, pairs, c = dtw(x, y)
    out["dtw"] = dict(value=value, b=y.tolist(), pairs=pairs, contribution=c.tolist(),
                      detail=f"{len(pairs)} matched pairs; {len(pairs)-len(x)} extra pairs from repeated matching.")
    distance("derivative", np.diff(x), np.diff(y), 1/(len(x)-1))
    distance("dft", np.abs(np.fft.rfft(x,norm="ortho")), np.abs(np.fft.rfft(y,norm="ortho")))
    distance("acf", acf(x), acf(y))
    distance("paa", x.reshape(BLOCKS,-1).mean(axis=1), y.reshape(BLOCKS,-1).mean(axis=1))
    bp = np.asarray([NormalDist().inv_cdf(p) for p in (0.25,0.5,0.75)])
    pa, pb = ax.reshape(BLOCKS,-1).mean(axis=1), by.reshape(BLOCKS,-1).mean(axis=1)
    sa, sb = np.searchsorted(bp, pa, side="right"), np.searchsorted(bp, pb, side="right")
    gaps = [0.0 if abs(int(a)-int(b)) <= 1 else float(bp[max(a,b)-1] - bp[min(a,b)]) for a,b in zip(sa,sb)]
    c = (len(x)/BLOCKS) * np.asarray(gaps)**2
    out["sax"] = dict(value=float(np.sqrt(sum(c))), b=pb.tolist(), symbols_b=sb.tolist(),
                      contribution=c.tolist(), detail="A: " + "".join("abcd"[v] for v in sa) + "  |  B: " + "".join("abcd"[v] for v in sb))
    value, pairs, c = lcss(x, y)
    out["lcss"] = dict(value=value, b=y.tolist(), pairs=pairs, contribution=c.tolist(),
                       detail=f"{len(pairs)} matches; {len(x)-len(pairs)} A points and {len(y)-len(pairs)} B points skipped.")
    return out


def clean(obj):
    """Preserve 10 decimal places in traces (display shows up to six)."""
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError("Non-finite data in lab")
        return round(obj, 10)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    return obj


def build_data() -> dict:
    x = baseline()
    states = {}
    for item in TRANSFORMS:
        rows = []
        for level in range(LEVELS):
            y, parameters = transform(x, item["id"], level)
            rows.append(dict(level=level, strength=level/(LEVELS-1), parameters=parameters,
                             y=y.tolist(), methods=evaluate(x,y)))
        states[item["id"]] = rows
    values = [v for rows in states.values() for row in rows for v in row["y"]]
    lo, hi = min(min(x), min(values)), max(max(x), max(values))
    raw_limits = {}
    for kind, rows in states.items():
        vals = [v for row in rows for v in row["y"]] + x.tolist()
        lower, upper = min(vals), max(vals)
        raw_limits[kind] = [lower-.12*(upper-lower), upper+.12*(upper-lower)]
    return clean(dict(schema_version=1, n=N, levels=LEVELS, x=x.tolist(), methods=method_definitions(x),
                      perturbations=TRANSFORMS, states=states, raw_ylim=[lo-0.12*(hi-lo),hi+0.12*(hi-lo)], raw_ylim_by_transform=raw_limits,
                      provenance=dict(kind="Deterministic synthetic teaching example", seed="No random numbers",
                                      generator=SOURCE, calculation="float64 in Python/NumPy; saved traces rounded to 10 decimals",
                                      scope="Reference definitions for explanation; not a benchmark or replacement for EchoTime APIs")))


def canonical(data) -> bytes:
    return (json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))+"\n").encode("utf-8")


def pack_data(data: dict) -> dict:
    """Deduplicate repeated numeric arrays without losing precision or metadata.

    Raw B occurs in the source state and several method views; invariant features
    recur across levels. A simple explicit pool keeps the portable bundle small.
    Resolving an array reference is serialization work, not metric computation.
    """
    arrays, lookup = [], {}

    def visit(value):
        if isinstance(value, dict):
            return {k: visit(v) for k,v in value.items()}
        if isinstance(value, list):
            if len(value) >= 4 and (isinstance(value[0], (int,float)) or value[0] is None
                                    or isinstance(value[0], list)):
                key = canonical(value)
                if key not in lookup:
                    lookup[key] = len(arrays)
                    arrays.append(value)
                return {"$array": lookup[key]}
            return [visit(v) for v in value]
        return value

    packed = visit(data)
    return dict(encoding="array-pool-v1", description="Replace each {$array: i} with arrays[i]; all values are precomputed.",
                arrays=arrays, data=packed)


def unpack_data(payload: dict) -> dict:
    if payload.get("encoding") != "array-pool-v1":
        raise ValueError("Unsupported lab data encoding")
    arrays = payload["arrays"]
    def visit(value):
        if isinstance(value, dict):
            if set(value) == {"$array"}:
                return arrays[value["$array"]]
            return {k: visit(v) for k,v in value.items()}
        if isinstance(value, list):
            return [visit(v) for v in value]
        return value
    return visit(payload["data"])


@lru_cache(maxsize=16)
def font(size: int, bold: bool = False):
    from PIL import ImageFont
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path("/usr/share/fonts/truetype/dejavu") / name
    if not path.is_file():
        import matplotlib
        path = Path(matplotlib.get_data_path()) / "fonts/ttf" / name
    return ImageFont.truetype(str(path), size=size)


def wrapped(draw, xy, text, width, size=16, color=None, bold=False):
    f = font(size,bold)
    lines, current = [], ""
    for word in text.split():
        trial = (current+" "+word).strip()
        if draw.textlength(trial,font=f) > width and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    for k,line in enumerate(lines):
        draw.text((xy[0],xy[1]+k*(size+5)),line,font=f,fill=color or COLORS["text"])
    return len(lines)*(size+5)


def graph(draw, box, a, b=None, *, ylim=None, residual=False, xlabel="sample index", bars=False):
    left, top, right, bottom = box
    values = list(a)+(list(b) if b is not None else [])
    values = [v for v in values if v is not None]
    if ylim is None:
        lo, hi = min(0,min(values)), max(0,max(values))
        pad = max((hi-lo)*.12,.08)
        ylim = [lo-pad,hi+pad]
    lo,hi = ylim
    px = lambda i: left+i*(right-left)/max(len(a)-1,1)
    py = lambda v: bottom-(v-lo)*(bottom-top)/(hi-lo)
    for frac in (0,.5,1):
        v = lo+(hi-lo)*frac
        yy = py(v)
        draw.line((left,yy,right,yy),fill=COLORS["grid"],width=1)
        draw.text((left+3,yy-16),f"{v:.1f}",font=font(11),fill=COLORS["muted"])
    if residual and b is not None:
        for i,(av,bv) in enumerate(zip(a,b)):
            draw.line((px(i),py(av),px(i),py(bv)),fill=COLORS["gold"],width=1)
    for vals,color in ((a,COLORS["a"]),(b,COLORS["b"])):
        if vals is None:
            continue
        points=[(px(i),py(v)) for i,v in enumerate(vals)]
        if bars:
            for xx,yy in points:
                draw.line((xx,py(0),xx,yy),fill=color,width=3)
        else:
            draw.line(points,fill=color,width=3)
    draw.text((left,bottom+8),"0",font=font(12),fill=COLORS["muted"])
    draw.text((right-18,bottom+8),str(len(a)-1),font=font(12),fill=COLORS["muted"])
    wrapped(draw,(left+24,bottom+8),xlabel,right-left-48,size=12,color=COLORS["muted"])


def render_frame(data: dict, kind: str, level: int):
    from PIL import Image, ImageDraw
    image = Image.new("RGB",(1200,690),COLORS["bg"])
    draw = ImageDraw.Draw(image)
    state = data["states"][kind][level]
    meta = next(p for p in data["perturbations"] if p["id"] == kind)
    x,y = data["x"],state["y"]
    wrapped(draw,(30,22),"Same series. Different definitions of similarity.",1130,size=27,bold=True)
    wrapped(draw,(30,65),meta["title"]+" · "+state["parameters"]["label"],1130,size=20,color=COLORS["gold"])
    draw.text((30,99),"A  fixed reference",font=font(15),fill=COLORS["a"])
    draw.text((240,99),"B  same transformed input in every panel",font=font(15),fill=COLORS["b"])
    titles=["01  Same raw inputs","02  Raw RMSE","03  Constrained DTW","04  Fourier magnitudes"]
    positions=[30,324,618,912]
    for k,left in enumerate(positions):
        draw.rounded_rectangle((left,137,left+264,581),radius=14,fill=COLORS["panel"],outline=COLORS["grid"])
        wrapped(draw,(left+14,153),titles[k],236,size=17,bold=True)
    graph(draw,(44,218,280,416),x,y,ylim=data["raw_ylim_by_transform"][kind])
    wrapped(draw,(44,187),"raw amplitude",236,size=13,color=COLORS["muted"])
    wrapped(draw,(44,462),"One A/B pair is reused unchanged by all three comparisons.",236,size=16)
    graph(draw,(338,218,574,416),x,y,ylim=data["raw_ylim_by_transform"][kind],residual=True)
    wrapped(draw,(338,187),"raw amplitude; same-time gaps",236,size=13,color=COLORS["muted"])
    value=state["methods"]["rmse"]["value"]
    wrapped(draw,(338,462),f"RMSE = {value:.3f}",236,size=17,bold=True)
    wrapped(draw,(338,496),"Amplitude units. Gold segments compare identical timestamps. Offset and gain count.",236,size=15,color=COLORS["muted"])
    dt=state["methods"]["dtw"]
    left,right=632,868
    vals=x+y
    lo,hi=min(vals)-.2,max(vals)+.2
    px=lambda i:left+i*(right-left)/(N-1)
    ya=lambda v:278-(v-lo)*74/(hi-lo)
    yb=lambda v:414-(v-lo)*74/(hi-lo)
    for i,j in dt["pairs"]:
        draw.line((px(i),ya(x[i]),px(j),yb(y[j])),fill="#6d6043",width=1)
    draw.line([(px(i),ya(v)) for i,v in enumerate(x)],fill=COLORS["a"],width=3)
    draw.line([(px(i),yb(v)) for i,v in enumerate(y)],fill=COLORS["b"],width=3)
    draw.text((632,202),f"{hi:.1f}",font=font(10),fill=COLORS["muted"])
    draw.text((632,265),f"{lo:.1f}",font=font(10),fill=COLORS["muted"])
    draw.text((632,338),f"{hi:.1f}",font=font(10),fill=COLORS["muted"])
    draw.text((632,401),f"{lo:.1f}",font=font(10),fill=COLORS["muted"])
    wrapped(draw,(632,187),"raw amplitude; rows separated",236,size=13,color=COLORS["muted"])
    draw.text((632,287),"A index 0…63",font=font(12),fill=COLORS["a"])
    draw.text((632,423),"B index 0…63",font=font(12),fill=COLORS["b"])
    wrapped(draw,(632,462),f"DTW = {dt['value']:.3f}",236,size=17,bold=True)
    wrapped(draw,(632,496),"Amplitude units. Ordered matches may repeat. Band ±8; sqrt(total squared cost).",236,size=15,color=COLORS["muted"])
    dft=state["methods"]["dft"]
    fa=next(m for m in data["methods"] if m["id"]=="dft")["a"]
    graph(draw,(926,218,1162,416),fa,dft["b"],xlabel="frequency bin",bars=False)
    if abs(dft["value"])<1e-9:
        wrapped(draw,(990,255),"A and B overlap",160,size=13,color=COLORS["gold"])
    wrapped(draw,(926,187),"ortho rFFT magnitude",236,size=13,color=COLORS["muted"])
    wrapped(draw,(926,462),f"Magnitude L2 = {dft['value']:.3f}",236,size=17,bold=True)
    wrapped(draw,(926,496),"33 unique bins, DC retained. Phase and event timing are discarded.",236,size=15,color=COLORS["muted"])
    wrapped(draw,(30,604),meta["observe"],1140,size=18)
    wrapped(draw,(30,660),"EchoTime · Deterministic synthetic example · Scores keep their own definitions; no cross-method ranking",1140,size=13,color=COLORS["muted"])
    return image


def build_media(data: dict):
    from PIL import Image
    frames=[]
    durations=[]
    for kind in ("offset","gain","shift","warp","spike","phase"):
        for level in (0,7,14,20):
            frame=render_frame(data,kind,level)
            frames.append(frame.quantize(colors=96,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE))
            durations.append(1800 if level==20 else 750)
    frames[0].save(BUNDLE/"mechanism-comparison.gif",save_all=True,append_images=frames[1:],
                   duration=durations,loop=0,optimize=False,disposal=2)
    render_frame(data,"phase",20).save(BUNDLE/"mechanism-comparison.png",optimize=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_data(data: dict):
    assert len(data["methods"])==11
    assert sum(len(rows) for rows in data["states"].values())==147
    canonical(data)
    for rows in data["states"].values():
        for row in rows:
            assert len(row["y"])==N
            assert set(row["methods"])=={m["id"] for m in data["methods"]}
            r=row["methods"]
            assert abs(r["zrmse"]["value"]**2-2*(1-r["pearson"]["value"]))<2e-9
            assert r["sax"]["value"] <= math.sqrt(N)*r["zrmse"]["value"]+1e-8
            assert -1e-9<=r["lcss"]["value"]<=1+1e-9
            assert 0-1e-9<=r["sbd"]["value"]<=2+1e-9


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    data=build_data()
    validate_data(data)
    BUNDLE.mkdir(parents=True,exist_ok=True)
    if args.check:
        saved=unpack_data(json.loads((BUNDLE/"states.json").read_text()))
        if saved != data:
            raise SystemExit("Lab JSON is stale; run tools/build_similarity_lab.py")
        manifest=json.loads((BUNDLE/"manifest.json").read_text())
        for relative,expected in manifest["sha256"].items():
            if digest(BUNDLE/relative)!=expected:
                raise SystemExit(f"Lab asset differs from manifest: {relative}")
        if manifest["generator_sha256"]!=digest(Path(__file__)):
            raise SystemExit("Lab generator changed; rebuild manifest")
        print(f"Verified 147 states, 11 methods, {len(manifest['sha256'])} assets; {manifest['total_bytes']:,} bytes")
        return
    (BUNDLE/"states.json").write_bytes(canonical(pack_data(data)))
    # The web page fetches this same-origin JSON; it never recalculates a score.
    build_media(data)
    names=["similarity-lab.html","lab.js","states.json","mechanism-comparison.gif","mechanism-comparison.png"]
    manifest=dict(schema_version=1,states=147,methods=11,generator_sha256=digest(Path(__file__)),
                  sha256={name:digest(BUNDLE/name) for name in names},
                  bytes={name:(BUNDLE/name).stat().st_size for name in names})
    manifest["total_bytes"]=sum(manifest["bytes"].values())
    (BUNDLE/"manifest.json").write_bytes(canonical(manifest))
    print(json.dumps(manifest["bytes"],indent=2))
    print(f"Built 147 states × 11 methods; {manifest['total_bytes']:,} bytes")


if __name__=="__main__":
    main()
