"""Bounds are tested against the implemented distances, with no epsilon."""
import itertools
import numpy as np
import pytest

from echotime._cutoff import cutoff_distance
from echotime._search_bounds import (dtw_endpoint_bound, dtw_keogh_bound,
    match_envelope_bound, component_upper_bound, ncc_spectral_bound, erp_sum_bound)
from echotime.similarity import score_from_components
from echotime import similarity_methods as sm


@pytest.mark.parametrize("normalize", [False, True])
def test_dtw_bounds_exhaustive_short_binary(normalize):
    rows = [np.asarray(x, dtype=float) for n in (1, 2, 3) for x in itertools.product((-1, 1), repeat=n)]
    for a in rows:
        for b in rows:
            for window in (None, 0, 1):
                actual = cutoff_distance(a, b, metric="dtw", backend="python", window=window, normalize=normalize).value
                for fn in (dtw_endpoint_bound, dtw_keogh_bound):
                    bound = fn(a, b, window=window, normalize=normalize)
                    assert bound.certified
                    assert bound.value <= actual, (a, b, window, bound, actual)


@pytest.mark.parametrize("dim", [1, 3, 9, 129])
def test_dtw_bounds_random_ragged_missing_and_extreme(dim):
    rng = np.random.default_rng(829 + dim)
    for _ in range(20):
        a = rng.normal(size=(18, dim))
        b = rng.normal(size=(21, dim))
        a[5, 0] = np.nan
        scale = rng.choice([1e-100, 1.0, 1e100])
        a *= scale
        b *= scale
        for normalize in (False, True):
            for window in (None, 0, 5):
                actual = cutoff_distance(a, b, metric="dtw", backend="python", window=window, normalize=normalize).value
                assert dtw_endpoint_bound(a, b, window=window, normalize=normalize).value <= actual
                assert dtw_keogh_bound(a, b, window=window, normalize=normalize).value <= actual


@pytest.mark.parametrize("metric", ["edr", "lcss", "lcss_similarity"])
@pytest.mark.parametrize("dim", [1, 3])
def test_match_envelopes(metric, dim):
    rng = np.random.default_rng(42)
    for _ in range(45):
        a, b = rng.integers(-2, 3, size=(19, dim)), rng.integers(-2, 3, size=(23, dim))
        for window in (None, 0, 5):
            for epsilon in (0, 1, np.sqrt(2), np.nextafter(np.sqrt(2), 0)):
                bound = match_envelope_bound(a, b, metric=metric, epsilon=epsilon, window=window)
                actual = sm.lcss_similarity(a, b, epsilon=epsilon, window=window) if metric == "lcss_similarity" else cutoff_distance(a, b, metric=metric, epsilon=epsilon, window=window).value
                assert bound.value >= actual if metric == "lcss_similarity" else bound.value <= actual


def test_composite_bound_both_validity_branches_and_targets():
    names = ["shape_similarity", "trend_similarity", "derivative_similarity", "spectral_similarity"]
    rng = np.random.default_rng(93)
    for _ in range(100):
        cheap = dict(zip(names, rng.uniform(size=4)))
        cheap[names[rng.integers(4)]] = np.nan
        for target in ("similarity_score", "component_mean"):
            upper = component_upper_bound(cheap, target=target)
            for dtw in (0., 1., np.nan, rng.random()):
                actual = getattr(score_from_components({**cheap, "dtw_similarity": dtw}), target)
                assert upper >= actual
    with pytest.raises(ValueError):
        component_upper_bound(cheap, target="unknown")


def test_unproved_float_bounds_are_priority_only():
    a, b = np.arange(18.), np.arange(21.) ** 0.5
    assert not erp_sum_bound(a, b).certified
    for metric in ("sbd", "max_ncc", "independent_sbd"):
        assert not ncc_spectral_bound(a, b, metric=metric).certified
        assert not ncc_spectral_bound(a, b, metric=metric, n_coeffs=3).certified


def test_empty_and_overflow_fallbacks():
    assert dtw_keogh_bound([], [1]).value == 0
    assert dtw_endpoint_bound([1e308], [-1e308]).value == 0
    assert match_envelope_bound([], [1], metric="lcss_similarity").value == 1
