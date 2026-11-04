"""Exact cutoff certificates, tie handling, and unchanged legacy kernels."""

from __future__ import annotations

from contextlib import contextmanager

import numpy as np
import pytest

from echotime import _native
from echotime import similarity_methods as sm
from echotime._cutoff import CutoffResult, cutoff_distance


def _has_native_cutoff():
    return _native.native_available() and hasattr(_native.ext(), "dtw_pairs_cutoff")


native = pytest.mark.skipif(not _has_native_cutoff(), reason="native cutoff extension not built")
BACKENDS = ["python", pytest.param("native", marks=native)]
CASES = [
    ("dtw", {}),
    ("dtw", {"normalize": True}),
    ("erp", {"gap_value": 0.3}),
    ("twed", {"nu": 0.02, "lambda_": 0.4}),
    ("edr", {"epsilon": 0.25}),
    ("edr", {"epsilon": 0.25, "normalized": False}),
    ("lcss", {"epsilon": 0.25}),
]


@contextmanager
def _python_backend():
    previous = _native._override
    _native._override = "python"
    try:
        yield
    finally:
        _native._override = previous


def _reference(metric, x, y, **params):
    with _python_backend():
        return getattr(sm, f"{metric}_distance")(x, y, **params)


def _assert_identical(value, expected):
    if np.isnan(expected):
        assert np.isnan(value)
    else:
        assert np.float64(value).tobytes() == np.float64(expected).tobytes()


def _assert_result(result, expected, cutoff):
    assert isinstance(result, CutoffResult)
    assert result.exceeded_cutoff == bool(expected > cutoff)
    if result.exceeded_cutoff:
        assert np.isnan(result.value), "a cutoff certificate must not masquerade as a distance"
    else:
        _assert_identical(result.value, expected)


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("metric,params", CASES)
@pytest.mark.parametrize("seed,d", [(1, 1), (2, 3), (3, 9), (4, 129)])
def test_cutoff_matches_python_at_adjacent_float_thresholds(backend, metric, params, seed, d):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal((23, d))
    y = rng.standard_normal((28, d))
    for window in (None, 0, 3):
        kw = {**params, "window": window}
        expected = _reference(metric, x, y, **kw)
        for threshold in (np.inf, expected, np.nextafter(expected, -np.inf), expected / 2, -np.inf):
            result = cutoff_distance(x, y, metric, cutoff=threshold, backend=backend, **kw)
            _assert_result(result, expected, threshold)
            assert 0 < result.cells_visited <= len(x) * len(y)


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("metric,params", CASES)
def test_cutoff_matches_reference_preparation_and_fast_mode(backend, metric, params):
    rng = np.random.default_rng(18)
    x = rng.standard_normal((25, 3))
    y = rng.standard_normal(19)
    x[3] = np.nan
    y[5] = np.inf
    kw = dict(params)
    if metric != "dtw":
        kw["mode"] = "fast"
    if metric == "twed":
        kw["t_x"] = np.cumsum(rng.uniform(0.1, 1.5, len(x))) - 20
        kw["t_y"] = np.cumsum(rng.uniform(0.1, 1.5, len(y))) - 7
    expected = _reference(metric, x, y, **kw)
    for threshold in (np.inf, expected, np.nextafter(expected, -np.inf)):
        result = cutoff_distance(x, y, metric, cutoff=threshold, backend=backend, **kw)
        _assert_result(result, expected, threshold)


@pytest.mark.parametrize("backend", BACKENDS)
def test_fast_twed_resampling_and_timestamps(backend):
    rng = np.random.default_rng(29)
    x = rng.normal(size=521)
    y = rng.normal(size=517)
    kw = dict(mode="fast", window=2, t_x=np.cumsum(rng.uniform(0.1, 2, len(x))), t_y=np.cumsum(rng.uniform(0.1, 2, len(y))))
    expected = _reference("twed", x, y, **kw)
    result = cutoff_distance(x, y, "twed", cutoff=expected, backend=backend, **kw)
    _assert_result(result, expected, expected)
    assert result.cells_visited == 512 * 5 - 6


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("metric,params", CASES)
def test_empty_and_nonfinite_inputs_are_not_cutoff_certificates(backend, metric, params):
    for x, y in (([], [1]), ([1], []), ([np.nan, np.inf], [0, 1])):
        result = cutoff_distance(x, y, metric, cutoff=-np.inf, backend=backend, **params)
        assert np.isnan(result.value)
        assert not result.exceeded_cutoff
        assert result.cells_visited == 0


@pytest.mark.parametrize("backend", BACKENDS)
def test_erp_row_zero_boundary_is_part_of_the_frontier(backend):
    # The first row's only interior cell is 100, but its boundary is zero.
    # A path can delete the first x value at no cost, then match 100 exactly.
    result = cutoff_distance([0.0, 100.0], [100.0], "erp", gap_value=0.0, cutoff=0.0, backend=backend)
    assert result.value == 0.0
    assert not result.exceeded_cutoff
    assert result.cells_visited == 2


@pytest.mark.parametrize("backend", BACKENDS)
def test_cutoff_ties_keep_zero_and_lcss_one(backend):
    x = np.arange(20, dtype=float)
    for metric, params in CASES:
        expected = _reference(metric, x, x, **params)
        result = cutoff_distance(x, x, metric, cutoff=expected, backend=backend, **params)
        _assert_result(result, expected, expected)
        assert result.cells_visited == 400
    result = cutoff_distance(np.zeros(20), np.ones(20), "lcss", epsilon=0.0, cutoff=1.0, backend=backend)
    assert result.value == 1.0
    assert not result.exceeded_cutoff


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("metric,params", CASES)
def test_arbitrarily_large_window_means_the_full_matrix(backend, metric, params):
    x, y = [1.0, 4.0, 2.0], [1.0, 3.0, 2.0, 5.0]
    expected = _reference(metric, x, y, **params)
    for window in (int(np.iinfo(np.int64).max), 10**100):
        for threshold in (0.0, expected, np.inf):
            result = cutoff_distance(x, y, metric, window=window, cutoff=threshold, backend=backend, **params)
            _assert_result(result, expected, threshold)


@native
@pytest.mark.parametrize("metric,params", CASES)
def test_native_early_abandonment_reduces_visited_cells(metric, params):
    x = np.full(64, 5.0)
    y = np.full(64, 100.0)
    expected = _reference(metric, x, y, **params)
    result = cutoff_distance(x, y, metric, cutoff=0.0, backend="native", **params)
    _assert_result(result, expected, 0.0)
    assert result.cells_visited == 64


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("normalize", [False, True])
def test_overflow_dtw_and_zero_stiffness_twed_preserve_reference(backend, normalize):
    with np.errstate(over="ignore", invalid="ignore"):
        x, y = np.array([1.7e308, 1.6e308]), np.array([-1.7e308, -1.6e308])
        expected = _reference("dtw", x, y, normalize=normalize)
        for threshold in (0.0, np.inf):
            result = cutoff_distance(x, y, "dtw", normalize=normalize, cutoff=threshold, backend=backend)
            _assert_result(result, expected, threshold)
        kw = dict(nu=0.0, t_x=[-1.7e308, 1.7e308], t_y=[1.0, 2.0])
        expected = _reference("twed", [1.0, 2.0], [3.0, 4.0], **kw)
        result = cutoff_distance([1.0, 2.0], [3.0, 4.0], "twed", cutoff=0.0, backend=backend, **kw)
        _assert_result(result, expected, 0.0)


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("metric,params", CASES)
def test_finite_inputs_whose_channel_aggregation_overflows(backend, metric, params):
    # The legacy mixed-channel mean can overflow despite finite observations.
    # Later Inf-Inf costs can become NaN, which must survive without a false
    # early certificate based only on the original input's finite values.
    x = np.full((19, 2), 1.7e308)
    y = np.full((21, 3), 1.7e308)
    with np.errstate(over="ignore", invalid="ignore"):
        expected = _reference(metric, x, y, **params)
        for threshold in (0.0, np.inf):
            result = cutoff_distance(x, y, metric, cutoff=threshold, backend=backend, **params)
            _assert_result(result, expected, threshold)


def test_invalid_options_and_backend_setting_is_unchanged():
    previous = _native._override
    cutoff_distance([0, 1], [0, 2], "dtw_distance", backend="python")
    assert _native._override == previous
    for invalid in (np.nan, "not-a-number", object()):
        with pytest.raises(ValueError, match="cutoff"):
            cutoff_distance([0], [1], cutoff=invalid, backend="python")
    with pytest.raises(TypeError, match="mode"):
        cutoff_distance([0], [1], "dtw", mode="fast", backend="python")
    with pytest.raises(ValueError, match="metric"):
        cutoff_distance([0], [1], "lcss_similarity", backend="python")
    with pytest.raises(ValueError, match="epsilon"):
        cutoff_distance([0], [1], "edr", epsilon=-1, backend="python")
    with pytest.raises(ValueError, match="strictly increasing"):
        cutoff_distance([0, 1], [0, 1], "twed", t_x=[1, 1], backend="python")


def _native_batch(metric, arrays_a, arrays_b, pairs_i, pairs_j, cutoffs, threads, window=2):
    d = arrays_a[0].shape[1]
    va, oa = sm._bank(arrays_a, d)
    vb, ob = sm._bank(arrays_b, d)
    common = (va, oa, vb, ob, pairs_i, pairs_j, cutoffs)
    ext = _native.ext()
    if metric == "dtw":
        return ext.dtw_pairs_cutoff(*common, window, True, threads)
    if metric == "edr":
        return ext.edr_pairs_cutoff(*common, 0.3, True, window, False, threads)
    if metric == "lcss":
        return ext.lcss_pairs_cutoff(*common, 0.3, window, False, threads)
    if metric == "erp":
        gap = sm._erp_gap(0.2, d)
        ga = sm._rows([sm._pointwise_l2_to_reference(a, gap) for a in arrays_a])
        gb = sm._rows([sm._pointwise_l2_to_reference(b, gap) for b in arrays_b])
        return ext.erp_pairs_cutoff(va, oa, ga, vb, ob, gb, pairs_i, pairs_j, cutoffs, window, False, threads)
    def side(a):
        # The public TWED path returns before building auxiliaries for empties.
        return sm._twed_side(a, None, lambda_=0.4, nu=0.03) if len(a) else (a, a.copy(), np.empty(0), np.empty(0), np.empty(0))

    left = [side(a) for a in arrays_a]
    right = [side(b) for b in arrays_b]
    return ext.twed_pairs_cutoff(
        va, sm._bank([s[1] for s in left], d)[0], oa,
        sm._rows([s[2] for s in left]), sm._rows([s[3] for s in left]), sm._rows([s[4] for s in left]),
        vb, sm._bank([s[1] for s in right], d)[0], ob,
        sm._rows([s[2] for s in right]), sm._rows([s[3] for s in right]), sm._rows([s[4] for s in right]),
        pairs_i, pairs_j, cutoffs, 0.03, window, False, threads,
    )


@native
@pytest.mark.parametrize("metric", ["dtw", "edr", "lcss", "erp", "twed"])
@pytest.mark.parametrize("d", [1, 3])
def test_native_banks_heterogeneous_lengths_and_threads(metric, d):
    rng = np.random.default_rng(30)
    aa = [rng.standard_normal((n, d)) for n in (0, 22, 24, 31)]
    bb = [rng.standard_normal((n, d)) for n in (27, 23, 0, 25)]
    ii, jj = np.indices((4, 4), dtype=np.int64).reshape(2, -1)
    kw = {
        "dtw": {"normalize": True}, "edr": {"epsilon": 0.3},
        "lcss": {"epsilon": 0.3}, "erp": {"gap_value": 0.2},
        "twed": {"lambda_": 0.4, "nu": 0.03},
    }[metric]
    expected = np.array([
        _reference(metric, aa[i], bb[j], window=2, **kw) if len(aa[i]) and len(bb[j]) else np.nan
        for i, j in zip(ii, jj)
    ])
    cutoffs = np.where(np.isnan(expected), -np.inf, expected)
    cutoffs[::3] = 0.0
    results = [_native_batch(metric, aa, bb, ii, jj, cutoffs, t) for t in (1, 4)]
    for values, exceeded, cells in results:
        assert values.dtype == np.float64
        assert exceeded.dtype == np.bool_
        assert cells.dtype == np.int64
        for k in range(len(ii)):
            _assert_result(CutoffResult(float(values[k]), bool(exceeded[k]), int(cells[k])), expected[k], cutoffs[k])
            assert cells[k] <= len(aa[ii[k]]) * len(bb[jj[k]])
    for single, threaded in zip(results[0], results[1]):
        np.testing.assert_array_equal(single, threaded)
    empty = _native_batch(metric, aa, bb, ii[:0], jj[:0], cutoffs[:0], 4)
    assert all(a.shape == (0,) for a in empty)


@native
def test_native_cutoff_validation():
    values = np.arange(4, dtype=float).reshape(-1, 1)
    offsets = np.array([0, 4], dtype=np.int64)
    indices = np.array([0], dtype=np.int64)
    for cutoffs in (np.array([np.nan]), np.array([]), np.array([[1.0]])):
        with pytest.raises(ValueError, match="cutoffs"):
            _native.ext().dtw_pairs_cutoff(values, offsets, values, offsets, indices, indices, cutoffs, -1, False, 1)


@native
@pytest.mark.parametrize("metric", ["dtw", "edr", "lcss", "erp", "twed"])
def test_native_bank_large_window_cannot_overflow_bounds(metric):
    aa = [np.arange(5, dtype=float).reshape(-1, 1)]
    bb = [np.arange(7, dtype=float).reshape(-1, 1)]
    indices = np.array([0, 0], dtype=np.int64)
    cutoffs = np.array([np.inf, 0.0])
    full = _native_batch(metric, aa, bb, indices, indices, cutoffs, 1, window=-1)
    wide = _native_batch(metric, aa, bb, indices, indices, cutoffs, 1, window=int(np.iinfo(np.int64).max))
    for expected, result in zip(full, wide):
        np.testing.assert_array_equal(expected, result)

