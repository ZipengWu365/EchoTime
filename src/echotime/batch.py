"""Batch evaluation of EchoTime's pairwise distances.

Four entry points share one engine:

* ``pairwise_distance_matrix(series, metric)``: all pairs within one set.
* ``cross_distance_matrix(left, right, metric)``: every left against every right.
* ``one_vs_many(query, candidates, metric)``: one series against a set.
* ``paired_distances(left, right, metric)``: ``left[k]`` against ``right[k]``
  (for example each subject's region against the group mean of the others).

Each entry equals calling the single-pair public function on that pair; the
batch path only removes repeated work:

* per-series preparation (cleaning, z-normalisation, embeddings, ordinal
  patterns, TWED/ERP terms) is done once per series, not once per pair;
* elastic distances (LCSS, EDR, ERP, TWED, DTW) run in the compiled kernel,
  parallel over pairs, bit-identical to the Python reference;
* shift-based correlation (``max_ncc``, ``sbd``, ``best_shift`` and their
  independent variants) finds the best lag with one FFT per series and one
  inverse FFT per pair, then recomputes the leading lags with the same dot
  products ``np.correlate`` uses, so the returned values and lags are
  bit-identical to the single-pair functions;
* embedding distances (ACF, periodogram, trend, ordinal-pattern JS, linear
  trend model) compute each embedding once and vectorise the pairwise norms;
  they agree with the single-pair functions to rounding (about 1e-15).

A 2-D array passed as a collection is read as ``(time, n_series)`` (one series
per column, the layout of an fMRI ROI matrix) unless ``layout="rows"``. A 3-D
array is ``(n_series, time, channels)``. Lists may hold series of different
lengths.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

import numpy as np
from scipy import fft as sp_fft

from . import _native
from . import similarity_methods as sm
from .metrics import EPS

_ELASTIC = {"lcss_similarity", "lcss", "edr", "erp", "twed", "dtw"}
_NCC = {"max_ncc", "sbd", "best_shift", "independent_max_ncc", "independent_sbd"}
_EMBED = {"acf", "periodogram", "trend", "ordinal_js", "linear_trend_model"}

_ALIASES = {
    "lcss_distance": "lcss",
    "edr_distance": "edr",
    "erp_distance": "erp",
    "twed_distance": "twed",
    "dtw_distance": "dtw",
    "acf_distance": "acf",
    "periodogram_distance": "periodogram",
    "trend_distance": "trend",
    "ordinal_pattern_js_distance": "ordinal_js",
    "ordinal_pattern_js": "ordinal_js",
    "linear_trend_model_distance": "linear_trend_model",
}

METRICS = tuple(sorted(_ELASTIC | _NCC | _EMBED))

# Pairs shorter than this use np.correlate directly: numpy switches to an
# unrolled small-kernel path (kernels of up to 11 samples) whose summation
# order the segment dot products below would not reproduce.
_MIN_FFT_LENGTH = 16
# Inverse-FFT block budget (bytes of float64 work per block).
_FFT_BLOCK_BYTES = 256 * 1024 * 1024
# Lags whose FFT estimate is within this of the block maximum are recomputed
# exactly. FFT error is ~1e-16 relative to |x||y|, so 1e-9 is a wide margin.
_NCC_REFINE_TOL = 1e-9


def _metric_name(metric: str) -> str:
    name = _ALIASES.get(str(metric), str(metric))
    if name not in METRICS:
        raise ValueError(f"unknown metric {metric!r}; choose from {METRICS} (or their *_distance aliases).")
    return name


def _as_collection(series: Any, layout: str) -> list[Any]:
    if layout not in {"columns", "rows"}:
        raise ValueError("layout must be 'columns' (time, n_series) or 'rows' (n_series, time).")
    if isinstance(series, np.ndarray):
        if series.ndim == 1:
            raise ValueError("a collection needs several series; wrap a single series in a list.")
        if series.ndim == 2:
            return [series[:, k] for k in range(series.shape[1])] if layout == "columns" else [series[k] for k in range(series.shape[0])]
        if series.ndim == 3:
            return [series[k] for k in range(series.shape[0])]
        raise ValueError("array collections must be 2-D or 3-D.")
    return list(series)


def _timestamps_for(timestamps: Any, count: int) -> list[Any]:
    if timestamps is None:
        return [None] * count
    if isinstance(timestamps, np.ndarray) and timestamps.ndim == 1:
        return [timestamps] * count
    items = list(timestamps)
    if len(items) != count:
        raise ValueError("timestamps must be one 1-D array shared by all series or one entry per series.")
    return items


# --------------------------------------------------------------- engine ----


def _evaluate(
    left: list[Any],
    right: list[Any] | None,
    I: np.ndarray,
    J: np.ndarray,
    metric: str,
    params: dict[str, Any],
    *,
    left_timestamps: list[Any],
    right_timestamps: list[Any] | None,
    n_jobs: int | None,
    backend: str | None,
) -> np.ndarray:
    name = _metric_name(metric)
    same = right is None
    right = left if same else right
    right_timestamps = left_timestamps if same else right_timestamps
    I = np.ascontiguousarray(I, dtype=np.int64)
    J = np.ascontiguousarray(J, dtype=np.int64)
    if I.size == 0:
        return np.zeros(0, dtype=np.int64 if name == "best_shift" else float)
    resolved = _native.resolve_backend(backend)
    threads = _native.default_threads(n_jobs)
    if name in _ELASTIC:
        return _elastic(left, right, same, I, J, name, params, left_timestamps, right_timestamps, resolved, threads)
    if name in _NCC:
        return _ncc(left, right, same, I, J, name, params, resolved, threads)
    return _embedding(left, right, same, I, J, name, params, resolved)


def _reference_loop(left: list[Any], right: list[Any], I: np.ndarray, J: np.ndarray, fn: Callable[[Any, Any], float], dtype=float) -> np.ndarray:
    previous = _native._override
    _native.set_similarity_backend("python")
    try:
        return np.asarray([fn(left[i], right[j]) for i, j in zip(I.tolist(), J.tolist())], dtype=dtype)
    finally:
        _native._override = previous


# ------------------------------------------------------- elastic family ----


def _prepare_elastic(raw: Any, timestamps: Any, mode: str) -> tuple[np.ndarray, np.ndarray | None]:
    arr, ts = sm._clean_series(sm._to_time_series(raw), None if timestamps is None else np.asarray(timestamps, dtype=float))
    if mode == "fast":
        arr, ts = sm._resample_series(arr, max_points=sm._FAST_MODE_MAX_POINTS, timestamps=ts)
    return arr, ts


def _elastic(left, right, same, I, J, name, params, left_ts, right_ts, resolved, threads) -> np.ndarray:
    allowed = {
        "lcss_similarity": {"epsilon", "window", "mode"},
        "lcss": {"epsilon", "window", "mode"},
        "edr": {"epsilon", "normalized", "window", "mode"},
        "erp": {"gap_value", "window", "mode"},
        "twed": {"lambda_", "nu", "window", "mode"},
        "dtw": {"window", "normalize"},
    }[name]
    unknown = set(params) - allowed
    if unknown:
        raise TypeError(f"{name} does not take {sorted(unknown)}.")
    mode = sm._validate_mode(params.get("mode", "exact"))
    window = params.get("window")
    sm._resolved_window(1, 1, window, mode)  # validates the argument like the single-pair call
    epsilon = sm._nonnegative_parameter("epsilon", params.get("epsilon", 1.0)) if name in {"lcss", "lcss_similarity", "edr"} else None
    lambda_ = sm._nonnegative_parameter("lambda_", params.get("lambda_", 1.0)) if name == "twed" else None
    nu = sm._nonnegative_parameter("nu", params.get("nu", 0.001)) if name == "twed" else None

    used_left = np.unique(I)
    used_right = np.unique(J)
    prep_left = {int(k): _prepare_elastic(left[k], left_ts[k], mode) for k in used_left}
    prep_right = prep_left if same else {int(k): _prepare_elastic(right[k], right_ts[k], mode) for k in used_right}
    if same:
        for k in used_right:
            if int(k) not in prep_left:
                prep_left[int(k)] = _prepare_elastic(left[k], left_ts[k], mode)
    dims = {a.shape[1] for a, _ in prep_left.values()} | {a.shape[1] for a, _ in prep_right.values()}

    def single(i: int, j: int) -> float:
        kwargs = {key: value for key, value in params.items()}
        if name == "twed":
            kwargs["t_x"] = left_ts[i]
            kwargs["t_y"] = right_ts[j]
        fn = {
            "lcss_similarity": sm.lcss_similarity,
            "lcss": sm.lcss_distance,
            "edr": sm.edr_distance,
            "erp": sm.erp_distance,
            "twed": sm.twed_distance,
            "dtw": sm.dtw_distance,
        }[name]
        return fn(left[i], right[j], **kwargs)

    if resolved == "python":
        return _python_elastic(I, J, single)
    if len(dims) != 1:
        # Mixed channel counts are averaged per pair by the reference, so they
        # cannot share one bank: evaluate those inputs pair by pair.
        return np.asarray([single(i, j) for i, j in zip(I.tolist(), J.tolist())], dtype=float)

    d = dims.pop()
    # Compact banks holding only the series that appear in the pairs.
    left_keys = sorted(prep_left)
    left_pos = {k: p for p, k in enumerate(left_keys)}
    if same:
        right_keys, right_pos = left_keys, left_pos
    else:
        right_keys = sorted(prep_right)
        right_pos = {k: p for p, k in enumerate(right_keys)}
    li = np.asarray([left_pos[int(k)] for k in I], dtype=np.int64)
    rj = np.asarray([right_pos[int(k)] for k in J], dtype=np.int64)
    va, oa = sm._bank([prep_left[k][0] for k in left_keys], d)
    if same:
        vb, ob = va, oa
    else:
        vb, ob = sm._bank([prep_right[k][0] for k in right_keys], d)
    ext = _native.ext()
    win = sm._native_window(window)
    fast = mode == "fast"
    if name in {"lcss", "lcss_similarity"}:
        out = ext.lcss_pairs(va, oa, vb, ob, li, rj, float(epsilon), win, fast, threads)
        if name == "lcss":
            out = np.where(np.isfinite(out), 1.0 - out, np.nan)
        return out
    if name == "edr":
        return ext.edr_pairs(va, oa, vb, ob, li, rj, float(epsilon), bool(params.get("normalized", True)), win, fast, threads)
    if name == "erp":
        gap = sm._erp_gap(params.get("gap_value", 0.0), d)
        ga = sm._rows([sm._pointwise_l2_to_reference(prep_left[k][0], gap) for k in left_keys])
        gb = ga if same else sm._rows([sm._pointwise_l2_to_reference(prep_right[k][0], gap) for k in right_keys])
        return ext.erp_pairs(va, oa, ga, vb, ob, gb, li, rj, win, fast, threads)
    if name == "twed":
        sides_a = [sm._twed_side(prep_left[k][0], prep_left[k][1], lambda_=lambda_, nu=nu) for k in left_keys]
        sides_b = sides_a if same else [sm._twed_side(prep_right[k][0], prep_right[k][1], lambda_=lambda_, nu=nu) for k in right_keys]

        def pack(sides):
            values, offsets = sm._bank([s[0] for s in sides], d)
            prev_values, _ = sm._bank([s[1] for s in sides], d)
            return values, prev_values, offsets, sm._rows([s[2] for s in sides]), sm._rows([s[3] for s in sides]), sm._rows([s[4] for s in sides])

        A = pack(sides_a)
        B = A if same else pack(sides_b)
        return ext.twed_pairs(*A, *B, li, rj, float(nu), win, fast, threads)
    # dtw
    out = ext.dtw_pairs(va, oa, vb, ob, li, rj, win, threads)
    if params.get("normalize", False):
        lens_a = np.diff(oa)[li]
        lens_b = np.diff(ob)[rj]
        out = out / (lens_a + lens_b)
    return out


def _python_elastic(I: np.ndarray, J: np.ndarray, single: Callable[[int, int], float]) -> np.ndarray:
    previous = _native._override
    _native.set_similarity_backend("python")
    try:
        return np.asarray([single(i, j) for i, j in zip(I.tolist(), J.tolist())], dtype=float)
    finally:
        _native._override = previous


# ---------------------------------------------------- shift-based family ----


def _ncc(left, right, same, I, J, name, params, resolved, threads) -> np.ndarray:
    unknown = set(params) - {"normalize"}
    if unknown:
        raise TypeError(f"{name} does not take {sorted(unknown)}.")
    normalize = bool(params.get("normalize", True))
    fn = {
        "max_ncc": sm.max_ncc,
        "sbd": sm.sbd,
        "best_shift": sm.best_shift,
        "independent_max_ncc": sm.independent_max_ncc,
        "independent_sbd": sm.independent_sbd,
    }[name]
    out_dtype = np.int64 if name == "best_shift" else float
    if resolved == "python":
        return _reference_loop(left, right, I, J, lambda a, b: fn(a, b, normalize=normalize), out_dtype)

    clean_left = {int(k): sm._clean_series(sm._to_time_series(left[k]))[0] for k in np.unique(I)}
    clean_right = clean_left if same else {int(k): sm._clean_series(sm._to_time_series(right[k]))[0] for k in np.unique(J)}
    if same:
        for k in np.unique(J):
            clean_left.setdefault(int(k), sm._clean_series(sm._to_time_series(left[k]))[0])
    independent = name.startswith("independent")

    # Channels become univariate "units"; joint metrics sum their correlations.
    def units(clean: dict[int, np.ndarray]) -> dict[int, list[np.ndarray]]:
        out = {}
        for k, arr in clean.items():
            xs = sm._z_normalize(arr) if normalize else arr
            out[k] = [np.ascontiguousarray(xs[:, dim]) for dim in range(xs.shape[1])]
        return out

    if independent:
        # independent_max_ncc z-normalises each channel inside max_ncc.
        def units_ind(clean):
            out = {}
            for k, arr in clean.items():
                cols = []
                for dim in range(arr.shape[1]):
                    col = arr[:, dim].reshape(-1, 1)
                    xs = sm._z_normalize(col) if normalize else col
                    cols.append(np.ascontiguousarray(xs[:, 0]))
                out[k] = cols
            return out

        U_left = units_ind(clean_left)
        U_right = U_left if same else units_ind(clean_right)
    else:
        U_left = units(clean_left)
        U_right = U_left if same else units(clean_right)

    results = np.empty(I.size, dtype=out_dtype)
    fallback: list[int] = []
    pairs_by_shape: dict[tuple[int, int, int], list[int]] = {}
    for p, (i, j) in enumerate(zip(I.tolist(), J.tolist())):
        a, b = clean_left[i], clean_right[j]
        if a.shape[1] != b.shape[1] or min(len(a), len(b)) < _MIN_FFT_LENGTH:
            fallback.append(p)
            continue
        pairs_by_shape.setdefault((len(a), len(b), a.shape[1]), []).append(p)

    if fallback:
        sub = _reference_loop(left, right, I[fallback], J[fallback], lambda a, b: fn(a, b, normalize=normalize), out_dtype)
        results[fallback] = sub

    for (n, m, d), members in pairs_by_shape.items():
        _ncc_group(np.asarray(members), n, m, d, I, J, U_left, U_right, independent, name, results, threads)
    return results


def _ncc_group(members, n, m, d, I, J, U_left, U_right, independent, name, results, threads) -> None:
    L = sp_fft.next_fast_len(n + m - 1, real=True)
    lags = np.arange(-(m - 1), n, dtype=int)
    keys_left = sorted({int(I[p]) for p in members})
    keys_right = sorted({int(J[p]) for p in members})
    spectra_left = {k: [sp_fft.rfft(col, L, workers=threads) for col in U_left[k]] for k in keys_left}
    spectra_right = {k: [np.conj(sp_fft.rfft(col, L, workers=threads)) for col in U_right[k]] for k in keys_right}
    norms_left = {k: float(np.linalg.norm(np.column_stack(U_left[k]))) for k in keys_left} if not independent else None
    norms_right = {k: float(np.linalg.norm(np.column_stack(U_right[k]))) for k in keys_right} if not independent else None
    # independent: one univariate problem per channel, combined by np.mean over finite values.
    channels = range(d)
    block = max(1, int(_FFT_BLOCK_BYTES // (8 * L * (d if not independent else 1) * 2)))
    for start in range(0, len(members), block):
        chunk = members[start : start + block]
        if independent:
            per_channel = []
            for dim in channels:
                prod = np.stack([spectra_left[int(I[p])][dim] * spectra_right[int(J[p])][dim] for p in chunk])
                corr = sp_fft.irfft(prod, L, axis=1, workers=threads)
                approx = _lag_window(corr, n, m, L)
                vals = []
                for row, p in enumerate(chunk):
                    x = U_left[int(I[p])][dim]
                    y = U_right[int(J[p])][dim]
                    denom = float(np.linalg.norm(x.reshape(-1, 1)) * np.linalg.norm(y.reshape(-1, 1)))
                    vals.append(_refine_max(approx[row], [x], [y], denom, n, m, lags)[0])
                per_channel.append(vals)
            for row, p in enumerate(chunk):
                values = [per_channel[dim][row] for dim in channels]
                finite = [v for v in values if np.isfinite(v)]
                ncc_mean = float(np.mean(finite)) if finite else float("nan")
                results[p] = ncc_mean if name == "independent_max_ncc" else (float(1.0 - ncc_mean) if np.isfinite(ncc_mean) else float("nan"))
            continue
        prod = None
        for dim in channels:
            term = np.stack([spectra_left[int(I[p])][dim] * spectra_right[int(J[p])][dim] for p in chunk])
            prod = term if prod is None else prod + term
        corr = sp_fft.irfft(prod, L, axis=1, workers=threads)
        approx = _lag_window(corr, n, m, L)
        for row, p in enumerate(chunk):
            i, j = int(I[p]), int(J[p])
            denom = float(norms_left[i] * norms_right[j])
            best, shift = _refine_max(approx[row], U_left[i], U_right[j], denom, n, m, lags)
            if name == "best_shift":
                results[p] = shift
            elif name == "max_ncc":
                results[p] = best
            else:  # sbd
                results[p] = float(1.0 - best) if np.isfinite(best) else float("nan")


def _lag_window(corr: np.ndarray, n: int, m: int, L: int) -> np.ndarray:
    """Circular correlation -> values ordered by lag -(m-1) .. n-1."""

    if m > 1:
        return np.concatenate([corr[:, L - (m - 1) :], corr[:, :n]], axis=1)
    return corr[:, :n]


def _exact_lag(xcols: list[np.ndarray], ycols: list[np.ndarray], lag: int, n: int, m: int) -> float:
    """Sum over channels of np.correlate(x, y, 'full') at ``lag``, reproduced exactly."""

    total = None
    for x, y in zip(xcols, ycols):
        if lag >= 0:
            length = min(n - lag, m)
            value = np.dot(x[lag : lag + length], y[:length])
        else:
            length = min(n, m + lag)
            value = np.dot(x[:length], y[-lag : -lag + length])
        total = value if total is None else total + value
    return float(total)


def _refine_max(approx: np.ndarray, xcols, ycols, denom: float, n: int, m: int, lags: np.ndarray) -> tuple[float, int]:
    if denom <= EPS:
        # ncc_sequence returns zeros: max 0.0 at the first lag.
        return 0.0, int(lags[0])
    scaled = approx / denom
    top = float(np.max(scaled))
    candidates = np.flatnonzero(scaled >= top - _NCC_REFINE_TOL)
    best_value = -np.inf
    best_index = -1
    for idx in candidates.tolist():
        exact = float(np.clip(_exact_lag(xcols, ycols, int(lags[idx]), n, m) / denom, -1.0, 1.0))
        if exact > best_value:
            best_value, best_index = exact, idx
    return best_value, int(lags[best_index])


# ----------------------------------------------------- embedding family ----


def _embedding(left, right, same, I, J, name, params, resolved) -> np.ndarray:
    allowed = {"acf": {"max_lag"}, "periodogram": {"n_coeffs"}, "trend": set(), "ordinal_js": {"order", "delay"}, "linear_trend_model": set()}[name]
    unknown = set(params) - allowed
    if unknown:
        raise TypeError(f"{name} does not take {sorted(unknown)}.")
    fn = {
        "acf": lambda a, b: sm.acf_distance(a, b, **params),
        "periodogram": lambda a, b: sm.periodogram_distance(a, b, **params),
        "trend": sm.trend_distance,
        "ordinal_js": lambda a, b: sm.ordinal_pattern_js_distance(a, b, **params),
        "linear_trend_model": sm.linear_trend_model_distance,
    }[name]
    if resolved == "python":
        return _reference_loop(left, right, I, J, fn)
    if name == "acf" and int(params.get("max_lag", 10)) <= 0:
        raise ValueError("max_lag must be positive.")

    def embed(raw: Any) -> np.ndarray | None:
        if name in {"ordinal_js", "linear_trend_model"}:
            values = sm._to_univariate_series(raw)
            if name == "linear_trend_model":
                return sm._linear_trend_parameters(values)
            return sm._ordinal_pattern_distribution(values, order=int(params.get("order", 3)), delay=int(params.get("delay", 1)))
        arr, _ = sm._clean_series(sm._to_time_series(raw))
        if name == "acf":
            max_lag = int(params.get("max_lag", 10))
            return np.stack([sm._autocorrelation_vector(arr[:, dim], max_lag=max_lag) for dim in range(arr.shape[1])]) if arr.shape[1] else None
        if len(arr) == 0:
            return None
        if name == "periodogram":
            return sm._periodogram_embedding(arr, n_coeffs=int(params.get("n_coeffs", 32)), normalize=True)
        return sm._trend_feature_vector(arr)

    def channels(raw: Any) -> int:
        return sm._to_time_series(raw).shape[1]

    keys_left = np.unique(I)
    keys_right = np.unique(J)
    if name in {"acf", "periodogram", "trend"}:
        dims = {channels(left[k]) for k in keys_left} | {channels(right[k]) for k in keys_right}
        if len(dims) != 1:
            return _reference_loop(left, right, I, J, fn)
    E_left = {int(k): embed(left[k]) for k in keys_left}
    E_right = E_left if same else {int(k): embed(right[k]) for k in keys_right}
    if same:
        for k in keys_right:
            E_left.setdefault(int(k), embed(left[k]))
    out = np.empty(I.size, dtype=float)
    missing = [p for p, (i, j) in enumerate(zip(I.tolist(), J.tolist())) if E_left[i] is None or E_right[j] is None]
    if missing:
        out[missing] = np.nan
    valid = np.setdiff1d(np.arange(I.size), np.asarray(missing, dtype=int))
    if valid.size == 0:
        return out
    A = np.stack([E_left[int(I[p])] for p in valid])
    B = np.stack([E_right[int(J[p])] for p in valid])
    if name == "acf":
        # mean over channels of the Euclidean norm of the ACF difference
        out[valid] = np.mean(np.sqrt(np.sum((A - B) ** 2, axis=-1)), axis=-1)
    elif name == "ordinal_js":
        out[valid] = _js_rows(A, B)
    else:
        out[valid] = np.sqrt(np.sum((A - B) ** 2, axis=-1))
    return out


def _js_rows(P: np.ndarray, Q: np.ndarray) -> np.ndarray:
    """Row-wise sm._jensen_shannon_distance (same masking and normalisation)."""

    sp = P.sum(axis=1, keepdims=True)
    sq = Q.sum(axis=1, keepdims=True)
    px = P / np.where(sp > EPS, sp, 1.0)
    py = Q / np.where(sq > EPS, sq, 1.0)
    mid = 0.5 * (px + py)
    with np.errstate(divide="ignore", invalid="ignore"):
        kl_x = np.where(px > EPS, px * np.log(px / mid), 0.0).sum(axis=1)
        kl_y = np.where(py > EPS, py * np.log(py / mid), 0.0).sum(axis=1)
    js = 0.5 * kl_x + 0.5 * kl_y
    return np.sqrt(np.maximum(js, 0.0))


# ---------------------------------------------------------- public API ----


def pairwise_distance_matrix(
    series: Any,
    metric: str = "sbd",
    *,
    layout: str = "columns",
    timestamps: Any | None = None,
    n_jobs: int | None = None,
    backend: str | None = None,
    **params: Any,
) -> np.ndarray:
    """All-pairs matrix ``M[i, j] = metric(series[i], series[j])``.

    Every metric here is symmetric except ``best_shift`` (antisymmetric), so
    the upper triangle and diagonal are computed and mirrored; ``best_shift``
    computes every ordered pair. ``timestamps`` (TWED only) is one array shared
    by all series or one per series. ``params`` are the single-pair keyword
    arguments (for example ``window=5`` or ``epsilon=0.5``).
    """

    items = _as_collection(series, layout)
    count = len(items)
    name = _metric_name(metric)
    ts = _timestamps_for(timestamps, count)
    if name == "best_shift":
        I, J = np.meshgrid(np.arange(count), np.arange(count), indexing="ij")
        values = _evaluate(items, None, I.ravel(), J.ravel(), name, params, left_timestamps=ts, right_timestamps=None, n_jobs=n_jobs, backend=backend)
        return values.reshape(count, count)
    I, J = np.triu_indices(count)
    values = _evaluate(items, None, I, J, name, params, left_timestamps=ts, right_timestamps=None, n_jobs=n_jobs, backend=backend)
    out = np.empty((count, count), dtype=values.dtype)
    out[I, J] = values
    out[J, I] = values
    return out


def cross_distance_matrix(
    left: Any,
    right: Any,
    metric: str = "sbd",
    *,
    layout: str = "columns",
    left_timestamps: Any | None = None,
    right_timestamps: Any | None = None,
    n_jobs: int | None = None,
    backend: str | None = None,
    **params: Any,
) -> np.ndarray:
    """``M[a, b] = metric(left[a], right[b])`` for every pair."""

    A = _as_collection(left, layout)
    B = _as_collection(right, layout)
    I, J = np.meshgrid(np.arange(len(A)), np.arange(len(B)), indexing="ij")
    values = _evaluate(
        A, B, I.ravel(), J.ravel(), metric, params,
        left_timestamps=_timestamps_for(left_timestamps, len(A)),
        right_timestamps=_timestamps_for(right_timestamps, len(B)),
        n_jobs=n_jobs, backend=backend,
    )
    return values.reshape(len(A), len(B))


def one_vs_many(
    query: Any,
    candidates: Any,
    metric: str = "sbd",
    *,
    layout: str = "columns",
    query_timestamps: Any | None = None,
    candidate_timestamps: Any | None = None,
    n_jobs: int | None = None,
    backend: str | None = None,
    **params: Any,
) -> np.ndarray:
    """``out[k] = metric(query, candidates[k])``."""

    B = _as_collection(candidates, layout)
    I = np.zeros(len(B), dtype=np.int64)
    J = np.arange(len(B), dtype=np.int64)
    return _evaluate(
        [query], B, I, J, metric, params,
        left_timestamps=[query_timestamps],
        right_timestamps=_timestamps_for(candidate_timestamps, len(B)),
        n_jobs=n_jobs, backend=backend,
    )


def paired_distances(
    left: Any,
    right: Any,
    metric: str = "sbd",
    *,
    layout: str = "columns",
    left_timestamps: Any | None = None,
    right_timestamps: Any | None = None,
    n_jobs: int | None = None,
    backend: str | None = None,
    **params: Any,
) -> np.ndarray:
    """``out[k] = metric(left[k], right[k])``."""

    A = _as_collection(left, layout)
    B = _as_collection(right, layout)
    if len(A) != len(B):
        raise ValueError("paired_distances needs collections of equal size.")
    idx = np.arange(len(A), dtype=np.int64)
    return _evaluate(
        A, B, idx, idx, metric, params,
        left_timestamps=_timestamps_for(left_timestamps, len(A)),
        right_timestamps=_timestamps_for(right_timestamps, len(B)),
        n_jobs=n_jobs, backend=backend,
    )


__all__ = [
    "METRICS",
    "cross_distance_matrix",
    "one_vs_many",
    "paired_distances",
    "pairwise_distance_matrix",
]
