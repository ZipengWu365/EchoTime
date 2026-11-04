"""Embedding caches preserve a complete native one-vs-many reference call."""

from __future__ import annotations

import numpy as np
import pytest

from echotime import _native, batch
from echotime import similarity_methods as sm
from echotime._search_vectors import VectorCache


pytestmark = pytest.mark.skipif(not _native.native_available(), reason="native batch reference requires the extension")

_METRICS = [
    ("acf", {"max_lag": 17}),
    ("periodogram", {"n_coeffs": 23}),
    ("trend", {}),
    ("ordinal_js", {"order": 4, "delay": 2}),
    ("linear_trend_model", {}),
]


def _assert_bits(actual: np.ndarray, expected: np.ndarray) -> None:
    np.testing.assert_array_equal(actual.view(np.uint64), expected.view(np.uint64))


@pytest.mark.parametrize("metric,params", _METRICS)
@pytest.mark.parametrize("query_kind", ["random", "constant", "missing"])
def test_cache_full_subset_reordered_duplicate_and_small_blocks_match_native_bits(
    metric: str, params: dict[str, int], query_kind: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    rng = np.random.default_rng(610)
    bank = [rng.normal(size=n) for n in (0, 1, 2, 7, 17, 40, 73)]
    bank.append(np.full(24, np.nan))
    bank.append(np.ones(35))
    bank[5][::5] = np.inf
    query = rng.normal(size=37)
    if query_kind == "constant":
        query[:] = 5.0
    elif query_kind == "missing":
        query[:] = np.nan
    expected = batch.one_vs_many(query, bank, metric, backend="native", **params)
    cache = VectorCache(bank, metric, params)
    prepared = cache.prepare_query(query)
    _assert_bits(cache.evaluate(prepared, np.arange(len(bank))), expected)
    ids = np.array([8, 2, 1, 4, 0, 8, 7, 6, 3, 5])
    _assert_bits(cache.evaluate(prepared, ids), expected[ids])
    monkeypatch.setattr(batch, "_EMBED_BLOCK_BYTES", 64)
    pieces = [cache.evaluate(prepared, ids[start:start + 3]) for start in range(0, len(ids), 3)]
    _assert_bits(np.concatenate(pieces), expected[ids])


@pytest.mark.parametrize("metric,params", _METRICS[:3])
def test_multichannel_cache_matches_native_row_reductions(metric: str, params: dict[str, int]) -> None:
    rng = np.random.default_rng(611)
    bank = [rng.normal(size=(n, 9)) for n in (24, 31, 47, 60)]
    bank[0][::5, 1] = np.nan
    bank[1][:] = np.nan
    query = rng.normal(size=(39, 9))
    expected = batch.one_vs_many(query, bank, metric, backend="native", **params)
    cache = VectorCache(bank, metric, params)
    _assert_bits(cache.evaluate(query, np.arange(len(bank))), expected)


@pytest.mark.parametrize("metric,params", _METRICS[:3])
@pytest.mark.parametrize("mixed_bank", [False, True])
def test_fallback_channel_policy_is_fixed_by_entire_bank(
    metric: str, params: dict[str, int], mixed_bank: bool,
) -> None:
    rng = np.random.default_rng(612)
    dimensions = [2, 3, 2, 3, 2] if mixed_bank else [3] * 5
    bank = [rng.normal(size=(30 + i, d)) for i, d in enumerate(dimensions)]
    query = rng.normal(size=(42, 2))
    expected = batch.one_vs_many(query, bank, metric, backend="native", **params)
    cache = VectorCache(bank, metric, params)
    prepared = cache.prepare_query(query)
    assert prepared.uses_reference
    # Each block can have a uniform channel count, including the query's own.
    # It still must use the whole bank's reference policy.
    actual = np.concatenate([cache.evaluate(prepared, np.array([i])) for i in range(len(bank))])
    _assert_bits(actual, expected)


@pytest.mark.parametrize("metric,params,function", [
    ("acf", {"max_lag": 10}, "_autocorrelation_vector"),
    ("periodogram", {"n_coeffs": 16}, "_periodogram_embedding"),
    ("trend", {}, "_trend_feature_vector"),
    ("ordinal_js", {"order": 3, "delay": 1}, "_ordinal_pattern_distribution"),
    ("linear_trend_model", {}, "_linear_trend_parameters"),
])
def test_bank_embeds_once_and_prepared_query_is_reused_across_blocks(
    metric: str, params: dict[str, int], function: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    rng = np.random.default_rng(613)
    bank = [rng.normal(size=41) for _ in range(5)]
    original = getattr(sm, function)
    calls: list[int] = []

    def counted(values: np.ndarray, *args: object, **kwargs: object) -> np.ndarray:
        calls.append(len(values))
        return original(values, *args, **kwargs)

    monkeypatch.setattr(sm, function, counted)
    cache = VectorCache(bank, metric, params)
    assert len(calls) == len(bank)
    query = cache.prepare_query(rng.normal(size=37))
    assert len(calls) == len(bank) + 1
    for ids in (np.array([0, 1]), np.array([2, 3, 4]), np.arange(5)):
        cache.evaluate(query, ids)
    assert len(calls) == len(bank) + 1


def test_bank_and_query_snapshots_are_isolated_and_indices_are_checked() -> None:
    rng = np.random.default_rng(614)
    bank = [rng.normal(size=31) for _ in range(3)]
    raw_query = rng.normal(size=35)
    cache = VectorCache(bank, "trend", {})
    query = cache.prepare_query(raw_query)
    expected = cache.evaluate(query, np.arange(3))
    bank[0][:] = 1234.0
    raw_query[:] = -1234.0
    _assert_bits(cache.evaluate(query, np.arange(3)), expected)
    with pytest.raises(ValueError):
        query.raw.setflags(write=True)
    with pytest.raises(ValueError):
        query.embedding.setflags(write=True)
    with pytest.raises(ValueError, match="integer"):
        cache.evaluate(query, np.array([0.5]))
    with pytest.raises(IndexError):
        cache.evaluate(query, np.array([-1]))
    with pytest.raises(IndexError):
        cache.evaluate(query, np.array([3]))
    other = VectorCache(bank, "trend", {})
    with pytest.raises(ValueError, match="different"):
        other.evaluate(query, np.array([0]))
    assert cache.evaluate(None, np.array([], dtype=np.int64)).size == 0


def test_native_embedding_parameter_validation_and_aliases_are_preserved() -> None:
    bank = [np.arange(20.0), np.arange(24.0)]
    with pytest.raises(ValueError, match="embedding"):
        VectorCache(bank, "dtw", {})
    with pytest.raises(TypeError, match="does not take"):
        VectorCache(bank, "acf", {"n_coeffs": 4})
    with pytest.raises(ValueError, match="positive"):
        VectorCache(bank, "acf", {"max_lag": 0})
    with pytest.raises(ValueError, match="univariate"):
        VectorCache([np.ones((30, 2))], "ordinal_js", {})
    with pytest.raises(ValueError, match="at least one"):
        VectorCache([np.array(3.0)], "acf", {})
    cache = VectorCache(bank, "acf_distance", {"max_lag": 8})
    expected = batch.one_vs_many(bank[0], bank, "acf", max_lag=8, backend="native")
    _assert_bits(cache.evaluate(bank[0], np.arange(2)), expected)
