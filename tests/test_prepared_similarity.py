"""Prepared/cache contracts and independently checked rolling semantics."""

from __future__ import annotations

import pickle

import numpy as np
import pytest

import echotime.prepared as prepared_module
import echotime.similarity as similarity
from echotime import _native
from echotime.prepared import PreparedChannel, PreparedSeries
from echotime.similarity import (
    SimilarityReport,
    SimilarityScore,
    aggregate_component_scores,
    compare_prepared_components,
    compare_series,
    prepared_dtw_similarity,
    rolling_similarity,
    score_from_components,
)


def _assert_exact(actual: float, expected: float) -> None:
    if np.isnan(expected):
        assert np.isnan(actual)
    else:
        assert float(actual).hex() == float(expected).hex()


@pytest.mark.parametrize("n_points", [4, 8, 32, 65])
@pytest.mark.parametrize("layout", ["single", "paired", "aggregate", "missing", "constant"])
def test_score_prepared_and_deferred_dtw_equal_full_report(n_points: int, layout: str) -> None:
    rng = np.random.default_rng(410)
    left = rng.normal(size=(57, 2))
    right = rng.normal(size=(49, 2))
    if layout == "single":
        left, right = left[:, 0], right[:, 0]
    elif layout == "aggregate":
        right = right[:, 0]
    elif layout == "missing":
        left[::7, 0] = np.nan
        right[::5, 1] = np.inf
    elif layout == "constant":
        left, right = np.ones(57), np.full(49, 3.0)

    report = compare_series(left, right, n_points=n_points)
    assert type(report) is SimilarityReport
    prepared_left = PreparedSeries(left, n_points=n_points)
    prepared_right = PreparedSeries(right, n_points=n_points)
    score = compare_series(prepared_left, prepared_right, output="score")
    assert isinstance(score, SimilarityScore)
    components = compare_prepared_components(prepared_left, prepared_right)
    assert "dtw_similarity" not in components
    components["dtw_similarity"] = prepared_dtw_similarity(prepared_left, prepared_right)
    for key, expected in report.component_scores.items():
        _assert_exact(score.component_scores[key], expected)
        _assert_exact(components[key], expected)
    _assert_exact(score.similarity_score, report.similarity_score)
    _assert_exact(score.component_mean, report.component_mean)
    aggregate = score_from_components(components)
    _assert_exact(aggregate_component_scores(components), report.similarity_score)
    _assert_exact(aggregate.similarity_score, report.similarity_score)
    _assert_exact(aggregate.component_mean, report.component_mean)
    assert list(score.component_scores) == list(report.component_scores)
    assert set(score.to_dict()) == {"similarity_score", "component_scores", "component_mean"}


def test_prepared_snapshot_arrays_configuration_and_pickle_are_immutable() -> None:
    raw = np.arange(80.0).reshape(40, 2)
    timestamps = np.arange(40.0) ** 1.2
    expected = similarity._resampled_multichannel(raw, timestamps=timestamps, n_points=32)
    prepared = PreparedSeries(raw, timestamps=timestamps, n_points=32)
    key = prepared.cache_key
    raw[:] = -123
    timestamps[:] = -123
    np.testing.assert_array_equal(prepared.resampled, expected)
    assert prepared.cache_key == key
    assert prepared.channel() is prepared.channel()
    channel = prepared.channel()
    arrays = [
        prepared.raw_values, prepared.timestamps, prepared.resampled,
        channel.values, channel.difference, channel.trend, channel.trend_difference,
        *channel.spectrum, channel.ranks, channel.bin_codes(4),
    ]
    for array in arrays:
        assert array is not None
        assert not array.flags.writeable
        with pytest.raises(ValueError):
            array.setflags(write=True)
    for name, value in [("n_points", 64), ("_n_points", 64), ("raw_values", raw)]:
        with pytest.raises(AttributeError):
            setattr(prepared, name, value)
    restored = pickle.loads(pickle.dumps(prepared))
    np.testing.assert_array_equal(restored.resampled, expected)
    assert restored.cache_key == key
    with pytest.raises(ValueError):
        restored.raw_values.setflags(write=True)


def test_prepared_resolution_timestamp_and_output_validation() -> None:
    raw = np.sin(np.arange(50.0))
    prepared = PreparedSeries(raw, n_points=32)
    inferred = compare_series(prepared, raw)
    assert inferred.metadata["resample_points"] == 32
    explicit = compare_series(raw, raw, n_points=32)
    assert inferred.to_dict() == explicit.to_dict()
    assert compare_series(raw, raw).metadata["resample_points"] == 256
    with pytest.raises(ValueError, match="same n_points"):
        compare_series(prepared, raw, n_points=64)
    with pytest.raises(ValueError, match="same n_points"):
        compare_series(prepared, PreparedSeries(raw, n_points=64))
    with pytest.raises(ValueError, match="Timestamps"):
        compare_series(prepared, raw, left_timestamps=np.arange(50.0))
    with pytest.raises(ValueError, match="output"):
        compare_series(raw, raw, output="fast")


def test_aggregate_features_are_computed_after_aggregation() -> None:
    rng = np.random.default_rng(411)
    prepared = PreparedSeries(rng.normal(size=(41, 3)), n_points=32)
    channel = prepared.channel(aggregate=True)
    expected_values = np.nanmean(prepared.resampled, axis=1)
    np.testing.assert_array_equal(channel.values, expected_values)
    np.testing.assert_array_equal(channel.difference, similarity._difference_view(expected_values))
    np.testing.assert_array_equal(channel.trend, similarity._smooth_trend(expected_values))
    expected_spectrum = similarity._normalized_spectrum(similarity._difference_view(expected_values))
    for actual, expected in zip(channel.spectrum, expected_spectrum):
        np.testing.assert_array_equal(actual, expected)


def test_prepared_reuses_resampling_trend_difference_spectrum_and_ranks(monkeypatch: pytest.MonkeyPatch) -> None:
    counts: dict[str, int] = {}

    def counted(module: object, name: str) -> None:
        original = getattr(module, name)

        def wrapped(*args: object, **kwargs: object) -> object:
            counts[name] = counts.get(name, 0) + 1
            return original(*args, **kwargs)

        monkeypatch.setattr(module, name, wrapped)

    for name in ("_resampled_multichannel", "_difference_view", "_smooth_trend", "_normalized_spectrum"):
        counted(similarity, name)
    counted(prepared_module, "rankdata")
    rng = np.random.default_rng(412)
    left = PreparedSeries(rng.normal(size=70), n_points=32)
    right = PreparedSeries(rng.normal(size=70), n_points=32)
    first = compare_series(left, right).to_dict()
    second = compare_series(left, right).to_dict()
    assert first == second
    assert counts == {
        "_resampled_multichannel": 2,
        "_difference_view": 4,
        "_smooth_trend": 2,
        "_normalized_spectrum": 2,
        "rankdata": 2,
    }


@pytest.mark.parametrize("case", ["random", "ties", "boundaries", "masked", "constant", "short"])
def test_cached_rank_and_histogram_diagnostics_match_original_pairwise_rules(case: str) -> None:
    rng = np.random.default_rng(413)
    left, right = rng.normal(size=(2, 256))
    if case == "ties":
        left, right = np.round(left), np.round(right)
    elif case == "boundaries":
        left = np.tile(np.linspace(-1.0, 1.0, 9), 28)
        right = np.roll(left, 7)
        left[1] = np.nextafter(left[1], -np.inf)
        right[2] = np.nextafter(right[2], np.inf)
    elif case == "masked":
        left[::11] = np.nan
        right[::13] = np.inf
    elif case == "constant":
        left[:] = 3.0
    elif case == "short":
        left, right = left[:2], right[:2]
    prepared_left, prepared_right = PreparedChannel(left), PreparedChannel(right)
    _assert_exact(similarity._prepared_spearman(prepared_left, prepared_right), similarity._safe_spearman_corr(left, right))
    _assert_exact(similarity._prepared_nmi(prepared_left, prepared_right), similarity._normalized_mutual_information(left, right))


def test_score_only_never_computes_unused_diagnostics_or_text(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("unused report dependency was evaluated")

    for name in ("_prepared_spearman", "_safe_kendall_tau", "_best_lag_corr", "_prepared_nmi", "_series_interpretation", "_monotonic_fraction"):
        monkeypatch.setattr(similarity, name, forbidden)
    rng = np.random.default_rng(414)
    result = compare_series(rng.normal(size=50), rng.normal(size=60), n_points=32, output="score")
    assert len(result.component_scores) == 5


def test_rolling_full_preserves_columns_and_skips_unused_report_work(monkeypatch: pytest.MonkeyPatch) -> None:
    rng = np.random.default_rng(415)
    left, right = rng.normal(size=(2, 73))
    expected = [
        compare_series(left[start:start + 30], right[start:start + 30], n_points=32)
        for start in range(0, 44, 9)
    ]

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("rolling evaluated an unused report dependency")

    for name in ("_safe_kendall_tau", "_best_lag_corr", "_series_interpretation", "_monotonic_fraction"):
        monkeypatch.setattr(similarity, name, forbidden)
    actual = rolling_similarity(left, right, window=30, step=9, n_points=32)
    assert len(actual) == len(expected)
    for window, report in zip(actual, expected):
        assert len(window) == 11
        _assert_exact(window["similarity_score"], report.similarity_score)
        _assert_exact(window["component_mean"], report.component_mean)
        for key in ("pearson_r", "spearman_rho", "normalized_mutual_information", "first_difference_r"):
            _assert_exact(window[key], report.reference_metrics[key])
        for key in ("shape_similarity", "trend_similarity", "spectral_similarity"):
            _assert_exact(window[key], report.component_scores[key])


@pytest.mark.parametrize("case", ["finite", "missing", "large_offset", "constant", "near_constant", "aggregate"])
@pytest.mark.parametrize("step", [1, 7, 53])
def test_fast_rolling_matches_direct_raw_window_correlations(case: str, step: int) -> None:
    rng = np.random.default_rng(416)
    left, right = rng.normal(size=(2, 420, 2))
    if case == "missing":
        left[::11, 0] = np.nan
        right[::13, 1] = np.inf
    elif case == "large_offset":
        left += 1e12
        right -= 1e12
    elif case == "constant":
        left[70:260] = 1.0
        right[70:260] = 2.0
    elif case == "near_constant":
        left = 1.0 + 1e-13 * left
        right = 2.0 + 1e-13 * right
    elif case == "aggregate":
        right = right[:, :1]
    paired_left, paired_right, _ = similarity._pair_multichannel(left, right)
    actual = rolling_similarity(left, right, window=41, step=step, mode="fast")
    for row in actual:
        assert set(row) == {"start", "stop", "pearson_r", "first_difference_r"}
        start, stop = int(row["start"]), int(row["stop"])
        x, y = paired_left[start:stop], paired_right[start:stop]
        expected_level = np.nanmean([similarity._safe_corr(x[:, i], y[:, i]) for i in range(x.shape[1])])
        expected_difference = np.nanmean([similarity._safe_corr(np.diff(x[:, i]), np.diff(y[:, i])) for i in range(x.shape[1])])
        np.testing.assert_allclose(row["pearson_r"], expected_level, rtol=1e-12, atol=1e-12, equal_nan=True)
        np.testing.assert_allclose(row["first_difference_r"], expected_difference, rtol=1e-12, atol=1e-12, equal_nan=True)


def test_fast_rolling_rejects_time_alignment_and_has_no_full_score_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = np.sin(np.arange(30.0))
    with pytest.raises(ValueError, match="timestamps"):
        rolling_similarity(raw, raw, window=10, mode="fast", left_timestamps=np.arange(30.0))
    with pytest.raises(ValueError, match="step"):
        rolling_similarity(raw, raw, window=10, step=0, mode="fast")

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("fast rolling evaluated full-score work")

    for name in ("_resampled_multichannel", "_smooth_trend", "_dtw_distance", "_normalized_spectrum", "_series_interpretation"):
        monkeypatch.setattr(similarity, name, forbidden)
    assert len(rolling_similarity(raw, raw, window=10, step=3, mode="fast")) == 7


def test_prepared_does_not_claim_invalid_inputs_become_valid_after_resampling() -> None:
    prepared = PreparedSeries([1.0, np.nan, 2.0])
    assert np.all(np.isnan(prepared.resampled))
    for output in ("report", "score"):
        with pytest.raises(ValueError, match="infs or NaNs"):
            compare_series(prepared, np.arange(20.0), output=output)


def test_prepared_dtw_explicit_python_backend_never_calls_native(monkeypatch: pytest.MonkeyPatch) -> None:
    rng = np.random.default_rng(417)
    left, right = [PreparedSeries(values, n_points=32) for values in rng.normal(size=(2, 40))]

    def forbidden() -> None:
        raise AssertionError("explicit Python DTW attempted to use the native extension")

    monkeypatch.setattr(_native, "_override", "native")
    monkeypatch.setattr(_native, "ext", forbidden)
    assert np.isfinite(prepared_dtw_similarity(left, right, backend="python"))


@pytest.mark.skipif(not _native.native_available(), reason="requires compiled native backend")
def test_prepared_dtw_explicit_native_backend_overrides_global_python(monkeypatch: pytest.MonkeyPatch) -> None:
    rng = np.random.default_rng(418)
    left, right = [PreparedSeries(values, n_points=32) for values in rng.normal(size=(2, 40))]
    expected = prepared_dtw_similarity(left, right, backend="python")
    original = _native.ext
    calls: list[int] = []

    def counted() -> object:
        calls.append(1)
        return original()

    monkeypatch.setattr(_native, "_override", "python")
    monkeypatch.setattr(_native, "ext", counted)
    _assert_exact(prepared_dtw_similarity(left, right, backend="native"), expected)
    assert len(calls) == 2
