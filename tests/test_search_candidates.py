"""Candidate budget contracts and regressions for full-series representations."""

from __future__ import annotations

import importlib

import numpy as np
import pytest

from echotime._search_candidates import CandidateEngine


STRATEGIES = ("multiview", "pyramid", "binary")


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("budget", [0, 1, 5, 9, 100])
def test_candidate_ids_budget_uniqueness_and_determinism(strategy, budget):
    rng = np.random.default_rng(42)
    series = [rng.normal(size=(40 + i, 3)) for i in range(12)]
    query = rng.normal(size=(45, 3))
    engine = CandidateEngine(series, seed=19)
    first, stats = engine.select(query, budget, strategy)
    second, repeated_stats = engine.select(query, budget, strategy)
    independent, _ = CandidateEngine(series, seed=19).select(query, budget, strategy)
    assert first.dtype == np.int64
    assert first.shape == (min(budget, len(series)),)
    assert len(np.unique(first)) == len(first)
    assert np.all((first >= 0) & (first < len(series)))
    np.testing.assert_array_equal(first, second)
    np.testing.assert_array_equal(first, independent)
    assert stats["strategy"] == strategy
    assert stats["candidate_count"] == len(first)
    assert stats["candidate_prep_seconds"] >= 0
    assert stats["candidate_ranking_seconds"] >= 0
    assert "recall" not in stats
    if 0 < budget < len(series):
        assert stats["approximation_layers"]
        assert repeated_stats["feature_cache_misses"] == 0


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_complete_suffix_participates_in_candidate_retrieval(strategy):
    n = 1024
    suffix = np.sin(np.linspace(0, 6 * np.pi, 256)) + 2.0
    series = [np.zeros(n), np.concatenate((np.zeros(768), suffix)), np.concatenate((np.zeros(768), -suffix))]
    query = series[1].copy()
    ids, _ = CandidateEngine(series, seed=7).select(query, 1, strategy)
    np.testing.assert_array_equal(ids, [1])


@pytest.mark.parametrize("strategy", ["multiview", "pyramid"])
def test_full_observation_event_protection_keeps_a_narrow_suffix_spike(strategy):
    # 128-point interpolation misses this isolated spike completely.  Event
    # and derivative-spectrum views must still inspect the original samples.
    n = 4097
    query = np.zeros(n)
    query[4090] = 1.0
    grid = np.linspace(0, n - 1, 128)
    assert not np.any(np.interp(grid, np.arange(n), query))
    series = [np.zeros(n) for _ in range(11)] + [query.copy()]
    ids, _ = CandidateEngine(series).select(query, 5, strategy)
    assert 11 in ids


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_snapshot_ownership_and_query_immutability(strategy):
    rng = np.random.default_rng(3)
    series = [rng.normal(size=64) for _ in range(8)]
    original = [a.copy() for a in series]
    query = original[5].copy()
    query_before = query.copy()
    engine = CandidateEngine(series, seed=31)
    for item in series:
        item[:] = np.nan
    ids, _ = engine.select(query, 3, strategy)
    expected, _ = CandidateEngine(original, seed=31).select(query, 3, strategy)
    np.testing.assert_array_equal(ids, expected)
    np.testing.assert_array_equal(query, query_before)


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_already_oriented_short_wide_series_are_not_transposed(strategy):
    rng = np.random.default_rng(5)
    series = [rng.normal(size=(2, 40)) for _ in range(5)]
    ids, stats = CandidateEngine(series, n_points=16).select(series[4], 1, strategy)
    assert stats["feature_channels"] == 40
    np.testing.assert_array_equal(ids, [4])


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_mixed_channels_and_query_dimension_fallback_are_explicit(strategy):
    rng = np.random.default_rng(12)
    query = rng.normal(size=(40, 4))
    series = [rng.normal(size=(30, 1 + i % 3)) for i in range(7)]
    ids, stats = CandidateEngine(series).select(query, 3, strategy)
    assert len(ids) == 3
    assert stats["feature_channels"] == 1
    assert "channel_mean_aggregation" in stats["approximation_layers"]
    same_channels = [rng.normal(size=(30, 3)) for _ in range(7)]
    ids, stats = CandidateEngine(same_channels).select(query, 3, strategy)
    assert stats["feature_channels"] == 1
    assert "channel_mean_aggregation" in stats["approximation_layers"]


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_empty_nonfinite_and_constant_series_have_deterministic_filling(strategy):
    series = [np.array([]), np.array([np.nan, np.inf]), np.ones(20), np.zeros(20), np.empty((4, 0))]
    ids, stats = CandidateEngine(series).select(np.zeros(20), 2, strategy)
    assert set(ids) == {2, 3}
    assert stats["invalid_series"] == 3
    invalid = [np.array([]), np.array([np.nan]), np.empty((4, 0))]
    ids, _ = CandidateEngine(invalid).select(np.array([]), 2, strategy)
    np.testing.assert_array_equal(ids, [0, 1])
    ids, _ = CandidateEngine([]).select(np.array([]), 5, strategy)
    assert ids.size == 0


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_extreme_finite_dynamic_range_does_not_break_candidate_protocol(strategy):
    series = [np.full((30, 2), v) for v in (1e-300, -1e-300, 1.7e308, -1.7e308)]
    query = np.full((25, 3), 1.7e308)
    with np.errstate(over="raise", invalid="raise"):
        ids, stats = CandidateEngine(series).select(query, 2, strategy)
    assert len(ids) == 2
    assert len(np.unique(ids)) == 2
    assert "corpus_feature_standardization_and_clipping" in stats["approximation_layers"]


def test_multiview_feature_cache_is_populated_lazily():
    rng = np.random.default_rng(13)
    series = [rng.normal(size=128) for _ in range(10)]
    engine = CandidateEngine(series)
    _, binary = engine.select(series[0], 4, "binary")
    assert binary["feature_cache_misses"] == 1
    assert binary["binary_bits"] == 128
    _, multi = engine.select(series[0], 5, "multiview")
    assert multi["feature_cache_hits"] == 1
    assert multi["feature_cache_misses"] == 4
    assert sum(multi["view_quotas"].values()) == 5
    assert set(multi["view_quotas"].values()) == {1}


def test_pyramid_pool_is_monotone_and_reserves_protection():
    rng = np.random.default_rng(99)
    series = [rng.normal(size=256) for _ in range(70)]
    ids, stats = CandidateEngine(series).select(series[3], 5, "pyramid")
    sizes = stats["pyramid_pool_sizes"]
    assert sizes[0] == len(series)
    assert sizes[-1] == 5
    assert all(left >= right for left, right in zip(sizes, sizes[1:]))
    assert stats["event_protection_quota"] == 1
    assert stats["spectrum_protection_quota"] == 1
    assert len(ids) == 5


def test_invalid_parameters_are_explicit():
    for points in (0, 7, 12.5, True):
        with pytest.raises(ValueError, match="n_points"):
            CandidateEngine([], n_points=points)
    with pytest.raises(ValueError, match="seed"):
        CandidateEngine([], seed=-1)
    with pytest.raises(ValueError, match="oriented"):
        CandidateEngine([np.zeros((2, 3, 4))])
    engine = CandidateEngine([np.zeros(8), np.ones(8)])
    for budget in (-1, 1.5, True):
        with pytest.raises(ValueError, match="budget"):
            engine.select(np.zeros(8), budget)
    with pytest.raises(ValueError, match="strategy"):
        engine.select(np.zeros(8), 1, "unknown")


@pytest.mark.parametrize("strategy", ["faiss", "faiss_hnsw"])
def test_missing_faiss_is_an_explicit_optional_dependency_error(monkeypatch, strategy):
    original = importlib.import_module

    def unavailable(name, *args, **kwargs):
        if name == "faiss":
            raise ImportError("FAISS unavailable in this test")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", unavailable)
    with pytest.raises(ImportError, match="optional FAISS"):
        CandidateEngine([np.zeros(8), np.ones(8)]).select(np.zeros(8), 1, strategy)


def test_optional_faiss_retrieves_float32_feature_neighbors_and_stable_ties():
    pytest.importorskip("faiss")
    series = [np.zeros(32) for _ in range(7)] + [np.ones(32)] + [np.array([])]
    engine = CandidateEngine(series)
    ids, stats = engine.select(np.zeros(32), 2, "faiss")
    np.testing.assert_array_equal(ids, [0, 1])
    assert stats["faiss_index"] == "IndexFlatL2"
    assert stats["faiss_omp_max_threads"] > 0
    assert stats["faiss_version"] != "unknown"
    again, _ = engine.select(np.zeros(32), 2, "faiss")
    np.testing.assert_array_equal(ids, again)
    match, _ = engine.select(np.ones(32), 1, "faiss")
    np.testing.assert_array_equal(match, [7])


def test_optional_hnsw_has_real_graph_search_and_distinct_approximation_layers():
    pytest.importorskip("faiss")
    rng = np.random.default_rng(73)
    series = [rng.normal(size=64) for _ in range(96)]
    engine = CandidateEngine(series, seed=29)
    ids, stats = engine.select(series[93], 5, "faiss_hnsw")
    assert len(ids) == len(np.unique(ids)) == 5
    assert 93 in ids
    assert stats["faiss_index"] == "IndexHNSWFlat"
    assert stats["hnsw_M"] == 32
    assert stats["hnsw_ef_construction"] == 80
    assert stats["hnsw_ef_search"] == 64
    assert stats["ann_returned_count"] == 5
    assert stats["ann_fill_count"] == 0
    assert "float32_faiss_feature_distance" in stats["approximation_layers"]
    assert "hnsw_graph_search_omissions" in stats["approximation_layers"]
    assert not stats["hnsw_rebuild_determinism_guaranteed"]
    again, _ = engine.select(series[93], 5, "faiss_hnsw")
    np.testing.assert_array_equal(again, ids)
    _, flat = engine.select(series[93], 5, "faiss")
    assert flat["faiss_index"] == "IndexFlatL2"
    assert "hnsw_graph_search_omissions" not in flat["approximation_layers"]


def test_optional_hnsw_per_query_parameters_do_not_conflict_across_threads():
    pytest.importorskip("faiss")
    from concurrent.futures import ThreadPoolExecutor

    rng = np.random.default_rng(61)
    series = [rng.normal(size=32) for _ in range(80)]
    engine = CandidateEngine(series)
    expected = [engine.select(series[37], n, "faiss_hnsw")[0] for n in (3, 68)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda n: engine.select(series[37], n, "faiss_hnsw"), (3, 68)))
    for (ids, stats), reference, budget in zip(results, expected, (3, 68)):
        np.testing.assert_array_equal(ids, reference)
        assert stats["hnsw_ef_search"] == max(64, budget)
