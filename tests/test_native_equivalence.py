"""The compiled kernels and batch APIs must reproduce the Python reference.

Elastic distances, shift-based correlation, sample/permutation entropy and
ordinal-pattern counts are required to be bit-identical; embedding distances
and the vectorised correlation summaries may differ by rounding only
(<= 1e-12).
"""

from __future__ import annotations

import math
from contextlib import contextmanager

import numpy as np
import pytest

import echotime as et
from echotime import _native
from echotime import metrics as M
from echotime import similarity as S
from echotime import similarity_methods as sm

native = pytest.mark.skipif(not _native.native_available(), reason="native extension not built")


@contextmanager
def backend(name: str):
    previous = _native._override
    _native.set_similarity_backend(name)
    try:
        yield
    finally:
        _native._override = previous


def both(fn, *args, **kwargs):
    with backend("python"):
        ref = fn(*args, **kwargs)
    with backend("native"):
        fast = fn(*args, **kwargs)
    return ref, fast


def same(a, b) -> bool:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return a.shape == b.shape and bool(np.all((a == b) | (np.isnan(a) & np.isnan(b))))


def close(a, b, tol=1e-12) -> bool:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    nan = np.isnan(a) & np.isnan(b)
    return a.shape == b.shape and bool(np.all(nan | (np.abs(a - b) <= tol * np.maximum(1.0, np.abs(a)))))


def _random_pair(rng, n_max=80, dims=(1, 1, 1, 2, 3, 9)):
    n, m = (int(v) for v in rng.integers(2, n_max, size=2))
    d = int(rng.choice(dims))
    x = rng.standard_normal((n, d)).cumsum(axis=0) * rng.uniform(0.1, 3)
    y = rng.standard_normal((m, d)).cumsum(axis=0) * rng.uniform(0.1, 3)
    if rng.random() < 0.15:
        x[rng.integers(0, n)] = np.nan
    if rng.random() < 0.1:
        y[:] = 1.5
    if d == 1:
        x, y = x[:, 0], y[:, 0]
    return x, y


@native
@pytest.mark.parametrize("seed", range(6))
def test_elastic_single_pair_bit_identical(seed):
    rng = np.random.default_rng(seed)
    for _ in range(60):
        x, y = _random_pair(rng)
        window = None if rng.random() < 0.5 else int(rng.integers(0, 12))
        mode = "fast" if rng.random() < 0.2 else "exact"
        cases = [
            (et.lcss_similarity, dict(epsilon=float(rng.uniform(0, 2)), window=window, mode=mode)),
            (et.lcss_distance, dict(epsilon=float(rng.uniform(0, 2)), window=window, mode=mode)),
            (et.edr_distance, dict(epsilon=float(rng.uniform(0, 2)), window=window, mode=mode, normalized=bool(rng.random() < 0.5))),
            (et.erp_distance, dict(gap_value=float(rng.normal()), window=window, mode=mode)),
            (et.twed_distance, dict(lambda_=float(rng.uniform(0, 2)), nu=float(rng.uniform(0, 0.1)), window=window, mode=mode)),
            (et.dtw_distance, dict(window=window, normalize=bool(rng.random() < 0.5))),
        ]
        for fn, kw in cases:
            ref, fast = both(fn, x, y, **kw)
            assert same(ref, fast), (fn.__name__, kw, ref, fast)


@native
def test_twed_timestamps_and_long_windowed_series_bit_identical():
    rng = np.random.default_rng(11)
    for n, m, w in ((6000, 5990, 15), (3000, 3000, 4), (2, 3, None), (5, 2, 0)):
        x = rng.standard_normal(n).cumsum()
        y = rng.standard_normal(m).cumsum()
        tx = np.cumsum(rng.uniform(0.5, 2.0, n))
        ty = np.cumsum(rng.uniform(0.5, 2.0, m))
        for fn, kw in (
            (et.twed_distance, dict(t_x=tx, t_y=ty, nu=0.05, window=w)),
            (et.erp_distance, dict(window=w)),
            (et.edr_distance, dict(epsilon=0.3, window=w)),
            (et.lcss_similarity, dict(epsilon=0.3, window=w)),
            (et.dtw_distance, dict(window=w)),
        ):
            ref, fast = both(fn, x, y, **kw)
            assert same(ref, fast), (fn.__name__, n, m, w, ref, fast)


@native
def test_compare_series_dtw_bit_identical():
    rng = np.random.default_rng(3)
    for _ in range(100):
        n, m = (int(v) for v in rng.integers(1, 90, size=2))
        x, y = rng.standard_normal(n), rng.standard_normal(m)
        window = None if rng.random() < 0.5 else int(rng.integers(0, 15))
        ref, fast = both(S._dtw_distance, x, y, window)
        assert same(ref, fast)
    x, y = rng.standard_normal(200), rng.standard_normal(200)
    ref, fast = both(et.compare_series, x, y)
    assert ref.similarity_score == fast.similarity_score


@native
def test_sample_entropy_bit_identical():
    rng = np.random.default_rng(7)
    for n in (5, 6, 30, 200, 601, 1500):
        for x in (rng.standard_normal(n), np.round(rng.standard_normal(n), 1), np.sin(np.arange(n) / 3.0)):
            for m, r in ((2, 0.2), (3, 0.15), (1, 0.5)):
                ref, fast = both(M.sample_entropy, x, m=m, r_ratio=r)
                assert same(ref, fast), (n, m, r, ref, fast)


def _ordinal_reference(values, order, delay):
    from itertools import permutations

    patterns = list(permutations(range(order)))
    index = {p: k for k, p in enumerate(patterns)}
    counts = np.zeros(len(patterns))
    for idx in range(len(values) - (order - 1) * delay):
        window = values[idx : idx + order * delay : delay]
        counts[index[tuple(np.argsort(window, kind="mergesort"))]] += 1.0
    if counts.sum() > M.EPS:
        counts = counts / float(np.sum(counts))
    return counts


def _permutation_entropy_reference(x, order=3, delay=1):
    x = M._entropy_subsample(np.asarray(x, dtype=float))
    n = len(x)
    if n < order * delay + 2:
        return float("nan")
    patterns = {}
    for idx in range(n - delay * (order - 1)):
        window = x[idx : idx + delay * order : delay]
        pattern = tuple(np.argsort(window, kind="mergesort"))
        patterns[pattern] = patterns.get(pattern, 0) + 1
    counts = np.asarray(list(patterns.values()), dtype=float)
    probs = counts / counts.sum()
    entropy = -np.sum(probs * np.log(probs + M.EPS)) / math.log(math.factorial(order))
    return float(np.clip(entropy, 0.0, 1.0))


def test_ordinal_patterns_and_permutation_entropy_bit_identical():
    rng = np.random.default_rng(13)
    for _ in range(80):
        n = int(rng.integers(3, 900))
        x = rng.standard_normal(n)
        if rng.random() < 0.4:
            x = np.round(x, 1)
        order = int(rng.integers(2, 6))
        delay = int(rng.integers(1, 4))
        assert same(sm._ordinal_pattern_distribution(x, order=order, delay=delay), _ordinal_reference(x, order, delay))
        assert same(M.permutation_entropy(x, order, delay), _permutation_entropy_reference(x, order, delay))


@native
def test_multivariate_correlation_summary_close():
    rng = np.random.default_rng(17)
    for k in (2, 7, 40):
        A = rng.standard_normal((150, k)).cumsum(axis=0)
        A[:, 0] = 2.0
        ref, fast = both(M.compute_multivariate_metrics, A)
        assert close(ref.mean_abs_correlation, fast.mean_abs_correlation)
        assert close(ref.dynamic_correlation_instability, fast.dynamic_correlation_instability)


@native
def test_profile_series_and_dataset_match_python_backend():
    rng = np.random.default_rng(19)
    X = rng.standard_normal((240, 12)).cumsum(axis=0)
    ref, fast = both(et.profile_series, X[:, 0])
    assert ref.axes.keys() == fast.axes.keys()
    assert all(close(ref.axes[k], fast.axes[k]) for k in ref.axes)
    data = et.FMRIInput(X, tr=2.0, timestamps=np.arange(240) * 2.0, roi_names=[f"r{i}" for i in range(12)], subject_ids=["s"], time_axis=0, channel_axis=-1)
    ref, fast = both(et.profile_dataset, data, bootstrap=0, random_state=0)
    assert all(close(ref.axes[k], fast.axes[k]) for k in ref.axes)
    assert all(close(ref.metrics[k], fast.metrics[k]) for k in ref.metrics)


# ------------------------------------------------------------- batch APIs ----

SINGLE = {
    "max_ncc": et.max_ncc,
    "sbd": et.sbd,
    "best_shift": et.best_shift,
    "independent_max_ncc": et.independent_max_ncc,
    "independent_sbd": et.independent_sbd,
    "lcss_similarity": et.lcss_similarity,
    "lcss": et.lcss_distance,
    "edr": et.edr_distance,
    "erp": et.erp_distance,
    "twed": et.twed_distance,
    "dtw": et.dtw_distance,
    "acf": et.acf_distance,
    "periodogram": et.periodogram_distance,
    "trend": et.trend_distance,
    "ordinal_js": et.ordinal_pattern_js_distance,
    "linear_trend_model": et.linear_trend_model_distance,
}
PARAMS = {
    "lcss_similarity": {"epsilon": 0.6, "window": 6},
    "lcss": {"epsilon": 0.4, "mode": "fast"},
    "edr": {"epsilon": 0.5, "normalized": False},
    "erp": {"gap_value": 0.2, "window": 9},
    "twed": {"nu": 0.02, "lambda_": 0.7},
    "dtw": {"window": 4, "normalize": True},
    "acf": {"max_lag": 7},
    "periodogram": {"n_coeffs": 16},
    "ordinal_js": {"order": 4, "delay": 2},
    "max_ncc": {"normalize": False},
}
EXACT = {"max_ncc", "sbd", "best_shift", "independent_max_ncc", "independent_sbd", "lcss_similarity", "lcss", "edr", "erp", "twed", "dtw"}


def _single_matrix(left, right, name, params):
    fn = SINGLE[name]
    with backend("python"):
        return np.asarray([[fn(a, b, **params) for b in right] for a in left], dtype=float)


@pytest.mark.parametrize("name", sorted(SINGLE))
def test_batch_matrix_matches_single_pair_calls(name):
    rng = np.random.default_rng(23)
    X = rng.standard_normal((90, 9)).cumsum(axis=0)
    X[:, 3] = 0.25  # constant series: zero-energy correlation path
    X[5, 4] = np.nan  # dropped row
    params = PARAMS.get(name, {})
    cols = [X[:, k] for k in range(X.shape[1])]
    ref = _single_matrix(cols, cols, name, params)
    got = et.pairwise_distance_matrix(X, name, **params)
    check = same if (name in EXACT and _native.native_available()) else close
    assert check(got, ref), (name, np.nanmax(np.abs(got - ref)))
    assert same(et.pairwise_distance_matrix(X, name, backend="python", **params), ref)


@pytest.mark.parametrize("name", sorted(SINGLE))
def test_batch_cross_one_vs_many_and_paired(name):
    rng = np.random.default_rng(29)
    left = [rng.standard_normal(int(n)).cumsum() for n in rng.integers(20, 70, size=5)] + [rng.standard_normal(8)]
    right = [rng.standard_normal(int(n)).cumsum() for n in rng.integers(20, 70, size=6)]
    params = PARAMS.get(name, {})
    ref = _single_matrix(left, right, name, params)
    check = same if (name in EXACT and _native.native_available()) else close
    assert check(et.cross_distance_matrix(left, right, name, **params), ref)
    assert check(et.one_vs_many(left[0], right, name, **params), ref[0])
    assert check(et.paired_distances(left, right[:6], name, **params), np.diag(ref[:, :6])[: len(left)])


@native
def test_batch_multichannel_rows_layout_and_twed_timestamps():
    rng = np.random.default_rng(31)
    stack = rng.standard_normal((7, 60, 3)).cumsum(axis=1)
    items = [stack[k] for k in range(7)]
    for name in ("sbd", "best_shift", "independent_sbd", "twed", "erp", "dtw", "edr"):
        params = PARAMS.get(name, {})
        assert same(et.pairwise_distance_matrix(stack, name, **params), _single_matrix(items, items, name, params))
    rows = rng.standard_normal((5, 120)).cumsum(axis=1)
    assert same(et.pairwise_distance_matrix(rows, "sbd", layout="rows"), _single_matrix(list(rows), list(rows), "sbd", {}))
    ts = [np.cumsum(rng.uniform(0.5, 1.5, 120)) for _ in range(5)]
    got = et.pairwise_distance_matrix(rows, "twed", layout="rows", timestamps=ts, nu=0.1)
    with backend("python"):
        ref = np.asarray([[et.twed_distance(rows[i], rows[j], t_x=ts[i], t_y=ts[j], nu=0.1) for j in range(5)] for i in range(5)])
    assert same(got, ref)


@native
def test_batch_threads_do_not_change_results():
    rng = np.random.default_rng(37)
    X = rng.standard_normal((150, 20)).cumsum(axis=0)
    one = et.pairwise_distance_matrix(X, "twed", n_jobs=1)
    many = et.pairwise_distance_matrix(X, "twed", n_jobs=8)
    assert same(one, many)


def test_backend_controls():
    info = et.similarity_backend_info()
    assert info["effective"] in {"native", "python"}
    with backend("python"):
        assert et.similarity_backend_info()["effective"] == "python"
    with pytest.raises(ValueError):
        et.set_similarity_backend("gpu")
    with pytest.raises(ValueError):
        et.pairwise_distance_matrix(np.zeros((10, 3)), "nonexistent")
