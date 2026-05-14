from __future__ import annotations

import importlib

import numpy as np

from echotime import (
    acf_distance,
    best_shift,
    edr_distance,
    erp_distance,
    independent_max_ncc,
    independent_sbd,
    lcss_distance,
    lcss_similarity,
    linear_trend_model_distance,
    max_ncc,
    ncc_sequence,
    ordinal_pattern_js_distance,
    periodogram_distance,
    sbd,
    trend_distance,
    twed_distance,
)


def _base_series() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x = np.sin(np.linspace(0.0, 4.0 * np.pi, 64))
    shifted = np.roll(x, 5)
    noisy = x + 0.05 * np.sin(np.linspace(0.0, 16.0 * np.pi, 64))
    different = np.cos(np.linspace(0.0, 4.0 * np.pi, 64))
    return x, shifted, noisy, different


def _long_series(length: int = 2304) -> tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0.0, 10.0 * np.pi, length)
    left = np.sin(t) + 0.05 * np.sin(7.0 * t)
    right = np.roll(left, 37) + 0.02 * np.cos(3.0 * t)
    return left, right


def _candidate_pool() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(123)
    base = np.sin(np.linspace(0.0, 6.0 * np.pi, 96))
    drift = 0.9 * base + np.linspace(0.0, 0.25, base.size)
    phase = np.roll(base, 3) + 0.01 * rng.normal(size=base.size)
    noisy = base + 0.01 * rng.normal(size=base.size)
    faster = np.sin(np.linspace(0.0, 8.0 * np.pi, 96))
    compressed = np.sin(np.linspace(0.0, 5.5 * np.pi, 96))
    different = np.cos(np.linspace(0.0, 6.0 * np.pi, 96))
    return {
        "base": base,
        "drift": drift,
        "phase": phase,
        "noisy": noisy,
        "faster": faster,
        "compressed": compressed,
        "different": different,
    }


def _topk_names(scores: dict[str, float], *, k: int, reverse: bool) -> tuple[str, ...]:
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=reverse)
    return tuple(name for name, _ in ordered[:k])


def test_shift_aware_similarity_methods_behave_monotonically() -> None:
    x, shifted, _, different = _base_series()

    values, lags = ncc_sequence(x, shifted)

    assert values.shape == lags.shape
    assert values.size == 127
    assert max_ncc(x, shifted) > 0.95
    assert best_shift(x, shifted) == -5
    assert sbd(x, shifted) < sbd(x, different)


def test_exact_mode_matches_legacy_defaults_for_deterministic_inputs() -> None:
    x, shifted, noisy, different = _base_series()
    multi_x = np.column_stack([x, np.roll(x, 2)])
    multi_shifted = np.column_stack([shifted, np.roll(shifted, 2)])
    multi_noisy = np.column_stack([noisy, np.roll(noisy, 2)])

    cases = [
        (lcss_similarity, (x, noisy), {"epsilon": 0.15}),
        (lcss_distance, (x, different), {"epsilon": 0.15}),
        (edr_distance, (x, noisy), {"epsilon": 0.15}),
        (erp_distance, (x, different), {}),
        (twed_distance, (x, noisy), {}),
        (lcss_similarity, (multi_x, multi_noisy), {"epsilon": 0.15}),
        (edr_distance, (multi_x, multi_shifted), {"epsilon": 0.15}),
        (erp_distance, (multi_x, multi_shifted), {}),
        (twed_distance, (multi_x, multi_shifted), {}),
    ]

    for fn, args, kwargs in cases:
        legacy = fn(*args, **kwargs)
        exact = fn(*args, mode="exact", **kwargs)
        assert np.isfinite(exact)
        assert np.isclose(exact, legacy)


def test_fast_mode_executes_on_univariate_and_multivariate_inputs() -> None:
    x, shifted, noisy, different = _base_series()
    multi_x = np.column_stack([x, np.roll(x, 2)])
    multi_shifted = np.column_stack([shifted, np.roll(shifted, 2)])
    multi_different = np.column_stack([different, np.roll(different, 2)])

    cases = [
        (lcss_similarity, (x, noisy), {"epsilon": 0.15, "window": 10}),
        (lcss_distance, (x, different), {"epsilon": 0.15, "window": 10}),
        (edr_distance, (multi_x, multi_shifted), {"epsilon": 0.15, "window": 10}),
        (erp_distance, (multi_x, multi_different), {"window": 10}),
        (twed_distance, (x, different), {"window": 10}),
        (twed_distance, (multi_x, multi_shifted), {"window": 10}),
    ]

    for fn, args, kwargs in cases:
        value = fn(*args, mode="fast", **kwargs)
        assert np.isfinite(value)


def test_elastic_methods_handle_different_lengths_and_window_arguments() -> None:
    x = np.sin(np.linspace(0.0, 5.0 * np.pi, 72))
    y = np.sin(np.linspace(0.2, 5.2 * np.pi, 103)) + 0.05 * np.cos(np.linspace(0.0, 14.0 * np.pi, 103))

    for fn, kwargs in [
        (lcss_similarity, {"epsilon": 0.20, "window": 12}),
        (lcss_distance, {"epsilon": 0.20, "window": 12}),
        (edr_distance, {"epsilon": 0.20, "window": 12}),
        (erp_distance, {"window": 12}),
        (twed_distance, {"window": 12}),
    ]:
        exact = fn(x, y, mode="exact", **kwargs)
        fast = fn(x, y, mode="fast", **kwargs)
        assert np.isfinite(exact)
        assert np.isfinite(fast)


def test_twed_fast_mode_accepts_timestamps() -> None:
    x = np.sin(np.linspace(0.0, 4.0 * np.pi, 96))
    y = np.roll(x, 7) + 0.03 * np.cos(np.linspace(0.0, 10.0 * np.pi, 96))
    t_x = np.cumsum(np.linspace(0.8, 1.2, x.size))
    t_y = np.cumsum(np.linspace(0.7, 1.3, y.size))

    exact = twed_distance(x, y, mode="exact", window=14, t_x=t_x, t_y=t_y)
    fast = twed_distance(x, y, mode="fast", window=14, t_x=t_x, t_y=t_y)

    assert np.isfinite(exact)
    assert np.isfinite(fast)


def test_fast_mode_preserves_candidate_ranking_reasonably() -> None:
    candidates = _candidate_pool()
    methods = [
        ("lcss_similarity", lcss_similarity, True, {"epsilon": 0.18, "window": 12}),
        ("lcss_distance", lcss_distance, False, {"epsilon": 0.18, "window": 12}),
        ("edr_distance", edr_distance, False, {"epsilon": 0.18, "window": 12}),
        ("erp_distance", erp_distance, False, {"window": 12}),
        ("twed_distance", twed_distance, False, {"window": 12}),
    ]

    for _, fn, higher_is_better, kwargs in methods:
        exact_scores = {name: float(fn(candidates["base"], series, mode="exact", **kwargs)) for name, series in candidates.items() if name != "base"}
        fast_scores = {name: float(fn(candidates["base"], series, mode="fast", **kwargs)) for name, series in candidates.items() if name != "base"}
        exact_top = _topk_names(exact_scores, k=5, reverse=higher_is_better)
        fast_top = _topk_names(fast_scores, k=5, reverse=higher_is_better)
        overlap = len(set(exact_top) & set(fast_top)) / 5.0
        assert overlap >= 0.80


def test_fast_mode_handles_long_sequences_without_choking() -> None:
    x, y = _long_series()
    t_x = np.cumsum(np.linspace(0.7, 1.3, x.size))
    t_y = np.cumsum(np.linspace(0.8, 1.2, y.size))
    multi_x = np.column_stack([x, np.roll(x, 11)])
    multi_y = np.column_stack([y, np.roll(y, 11)])

    values = [
        lcss_similarity(x, y, mode="fast", epsilon=0.18),
        lcss_distance(x, y, mode="fast", epsilon=0.18),
        edr_distance(multi_x, multi_y, mode="fast", epsilon=0.18, window=20),
        erp_distance(multi_x, multi_y, mode="fast", window=20),
        twed_distance(x, y, mode="fast", window=20, t_x=t_x, t_y=t_y),
    ]

    assert all(np.isfinite(value) for value in values)


def test_acf_distance_prefers_matching_rhythm() -> None:
    x, _, noisy, _ = _base_series()
    faster = np.sin(np.linspace(0.0, 8.0 * np.pi, 64))

    assert acf_distance(x, noisy, max_lag=12) < acf_distance(x, faster, max_lag=12)


def test_independent_shift_aware_methods_handle_multichannel_inputs() -> None:
    x, shifted, _, different = _base_series()
    multi_x = np.column_stack([x, np.roll(x, 2)])
    multi_shifted = np.column_stack([shifted, np.roll(shifted, 2)])
    multi_different = np.column_stack([different, np.roll(different, 2)])

    assert independent_max_ncc(multi_x, multi_shifted) > independent_max_ncc(multi_x, multi_different)
    assert independent_sbd(multi_x, multi_shifted) < independent_sbd(multi_x, multi_different)


def test_elastic_and_partial_match_methods_rank_similar_series_lower() -> None:
    x, _, noisy, different = _base_series()

    assert lcss_similarity(x, noisy, epsilon=0.15) > lcss_similarity(x, different, epsilon=0.15)
    assert lcss_distance(x, noisy, epsilon=0.15) < lcss_distance(x, different, epsilon=0.15)
    assert edr_distance(x, noisy, epsilon=0.15) < edr_distance(x, different, epsilon=0.15)
    assert erp_distance(x, noisy) < erp_distance(x, different)
    assert twed_distance(x, noisy) < twed_distance(x, different)


def test_periodogram_and_trend_distances_prefer_structurally_closer_series() -> None:
    x, _, noisy, different = _base_series()
    faster = np.sin(np.linspace(0.0, 8.0 * np.pi, 64))
    drifted = 0.8 * x + np.linspace(0.0, 0.8, x.size)

    assert periodogram_distance(x, noisy) < periodogram_distance(x, faster)
    assert trend_distance(x, noisy) < trend_distance(x, drifted)


def test_symbolic_and_trend_model_distances_run_as_public_apis() -> None:
    x, _, _, different = _base_series()
    x_step = np.concatenate([np.zeros(32), np.ones(32)])
    y_step = np.concatenate([np.zeros(28), np.ones(36)])
    x_trend = np.linspace(0.0, 1.0, 64)
    y_trend = np.linspace(0.1, 1.1, 64)
    z_trend = np.sin(np.linspace(0.0, 4.0 * np.pi, 64))

    assert ordinal_pattern_js_distance(x_step, y_step) < ordinal_pattern_js_distance(x_step, different)
    assert linear_trend_model_distance(x_trend, y_trend) < linear_trend_model_distance(x_trend, z_trend)


def test_tsontology_compat_shim_exposes_new_similarity_modules() -> None:
    atlas_module = importlib.import_module("tsontology.similarity_method_atlas")
    methods_module = importlib.import_module("tsontology.similarity_methods")

    assert hasattr(atlas_module, "similarity_method_atlas_dict")
    assert hasattr(methods_module, "twed_distance")
