"""Numerical and input-domain regressions for the public low-level methods."""

from __future__ import annotations

import numpy as np
import pytest

from echotime import (
    best_shift,
    edr_distance,
    erp_distance,
    lcss_distance,
    lcss_similarity,
    max_ncc,
    ncc_sequence,
    sbd,
    twed_distance,
)


@pytest.mark.parametrize("normalize", [False, True])
def test_joint_ncc_self_match_is_one_for_multiple_channels(normalize: bool) -> None:
    t = np.linspace(-1, 1, 24)
    values = np.column_stack([t, t**2, np.sin(3 * t)])
    scores, lags = ncc_sequence(values, values, normalize=normalize)

    assert scores[lags == 0].item() == pytest.approx(1.0)
    assert max_ncc(values, values, normalize=normalize) == pytest.approx(1.0)
    assert sbd(values, values, normalize=normalize) == pytest.approx(0.0)


def test_joint_ncc_does_not_change_when_channels_are_duplicated() -> None:
    x = np.sin(np.linspace(0, 7, 40))
    y = np.cos(np.linspace(0, 7, 40))
    expected, lags = ncc_sequence(x, y)
    actual, actual_lags = ncc_sequence(np.tile(x[:, None], (1, 3)), np.tile(y[:, None], (1, 3)))

    np.testing.assert_allclose(actual, expected, atol=1e-14)
    np.testing.assert_array_equal(actual_lags, lags)


def test_joint_ncc_zero_lag_matches_flattened_cosine_without_normalization() -> None:
    x = np.arange(60, dtype=float).reshape(20, 3)
    y = np.flip(x, axis=0) + 2
    expected = np.dot(x.ravel(), y.ravel()) / (np.linalg.norm(x) * np.linalg.norm(y))
    scores, lags = ncc_sequence(x, y, normalize=False)

    assert scores[lags == 0].item() == pytest.approx(expected)


@pytest.mark.parametrize("empty", [[], [np.nan, np.inf]])
def test_no_finite_ncc_observations_have_no_lag_or_score(empty: list[float]) -> None:
    values, lags = ncc_sequence(empty, [1, 2, 3])

    assert values.size == lags.size == 0
    assert np.isnan(max_ncc(empty, [1, 2, 3]))
    assert np.isnan(sbd(empty, [1, 2, 3]))
    assert best_shift(empty, [1, 2, 3]) == 0


@pytest.mark.parametrize("method", [lcss_similarity, lcss_distance, edr_distance])
@pytest.mark.parametrize("epsilon", [-1.0, np.inf, np.nan])
def test_edit_match_threshold_rejects_invalid_values(method, epsilon: float) -> None:
    # Previously negative epsilon behaved differently in one and two channels.
    for x in (np.arange(20.), np.column_stack([np.arange(20.), np.arange(20.)])):
        with pytest.raises(ValueError, match="epsilon.*finite and nonnegative"):
            method(x, x, epsilon=epsilon)


@pytest.mark.parametrize("method", [lcss_similarity, edr_distance, erp_distance, twed_distance])
@pytest.mark.parametrize("window", [-1, 1.5, np.inf, True])
def test_elastic_window_rejects_invalid_values(method, window) -> None:
    with pytest.raises(ValueError, match="window.*nonnegative integer"):
        method([1, 2, 3], [1, 2, 3], window=window)


@pytest.mark.parametrize("parameter", ["lambda_", "nu"])
@pytest.mark.parametrize("value", [-1.0, np.inf, np.nan])
def test_twed_rejects_invalid_cost_parameters(parameter: str, value: float) -> None:
    with pytest.raises(ValueError, match=parameter + ".*finite and nonnegative"):
        twed_distance([0, 1, 2], [0, 1, 2], **{parameter: value})


@pytest.mark.parametrize("timestamps", [[1, np.nan, 3], [1, 1, 3], [1, 3, 2]])
@pytest.mark.parametrize("mode", ["exact", "fast"])
def test_twed_rejects_invalid_observation_times(timestamps, mode: str) -> None:
    with pytest.raises(ValueError, match="timestamps must be (finite|strictly increasing)"):
        twed_distance([0, 1, 2], [0, 1, 2], t_x=timestamps, mode=mode)


def test_twed_validates_timestamps_before_fast_resampling() -> None:
    timestamps = np.arange(1024, dtype=float)
    timestamps[700] = timestamps[699]
    with pytest.raises(ValueError, match="strictly increasing"):
        twed_distance(timestamps, timestamps, t_x=timestamps, mode="fast")


def test_twed_keeps_elapsed_time_across_dropped_nonfinite_values() -> None:
    actual = twed_distance([0, np.nan, 2], [0, 2], t_x=[1, 2, 3], t_y=[1, 3])

    assert actual == pytest.approx(0.0)


def test_twed_uses_the_original_infinite_boundary_for_prefix_deletions() -> None:
    # Marteau (2009), Fig. 2: D(0, j) and D(i, 0) are infinity.
    # For [100] versus [0, 100], the only finite path first matches 100 to
    # 0 (cost 100), then inserts 100 (cost 100 + lambda + nu).
    assert twed_distance([100], [0, 100]) == pytest.approx(201.001)
    assert twed_distance([0, 100], [100]) == pytest.approx(201.001)


@pytest.mark.parametrize("gap_value", [np.nan, np.inf, [np.nan]])
def test_erp_rejects_nonfinite_gap_values(gap_value) -> None:
    with pytest.raises(ValueError, match="gap_value must be finite"):
        erp_distance([1, 2], [1, 3], gap_value=gap_value)
