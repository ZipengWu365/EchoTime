"""NCC reuse preserves the selected batch backend's exact refinement path."""

from __future__ import annotations

import numpy as np
import pytest

from echotime import _native, batch
import echotime._search_ncc as ncc_module
from echotime._search_ncc import NCCCache


pytestmark = pytest.mark.skipif(not _native.native_available(), reason="requires the native batch reference")
_METRICS = ["max_ncc", "sbd", "best_shift", "independent_max_ncc", "independent_sbd"]


def _assert_bits(actual: np.ndarray, expected: np.ndarray) -> None:
    if expected.dtype.kind in "iu":
        np.testing.assert_array_equal(actual, expected)
    else:
        np.testing.assert_array_equal(actual.view(np.uint64), expected.view(np.uint64))


@pytest.mark.parametrize("metric", _METRICS)
@pytest.mark.parametrize("normalize", [False, True])
@pytest.mark.parametrize("layout", ["single", "multi", "mixed"])
@pytest.mark.parametrize("query_length", [15, 16, 37])
def test_ncc_cache_matches_native_for_fft_threshold_ragged_and_channel_fallbacks(
    metric: str, normalize: bool, layout: str, query_length: int,
) -> None:
    rng = np.random.default_rng(810)
    bank = []
    for i, length in enumerate((0, 1, 8, 15, 16, 17, 31, 40, 63, 64, 97)):
        channels = 1 if layout == "single" else (1 + i % 3 if layout == "mixed" else 3)
        # Keep explicit empty inputs univariate; a (0, d) matrix is transposed
        # by the legacy orientation heuristic into a zero-channel series.
        values = rng.normal(size=length) if channels == 1 or length == 0 else rng.normal(size=(length, channels))
        bank.append(values)
    bank[8][::9] = np.nan
    bank.append(np.ones(32) if layout == "single" else np.ones((32, 3)))
    bank.append(np.full(25, np.nan))
    query = rng.normal(size=query_length) if layout == "single" else rng.normal(size=(query_length, 3))
    expected = batch.one_vs_many(query, bank, metric, backend="native", normalize=normalize, n_jobs=1)
    cache = NCCCache(bank, metric, {"normalize": normalize}, n_jobs=1)
    prepared = cache.prepare_query(query)
    _assert_bits(cache.evaluate(prepared, np.arange(len(bank))), expected)
    ids = np.asarray([12, 6, 8, 0, 11, 5, 6, 2, 10, 1, 4, 9, 7, 3])
    pieces = [cache.evaluate(prepared, ids[start:start + 3]) for start in range(0, len(ids), 3)]
    _assert_bits(np.concatenate(pieces), expected[ids])


@pytest.mark.parametrize("metric", _METRICS)
@pytest.mark.parametrize("normalize", [False, True])
def test_ncc_cache_preserves_constant_periodic_ties_and_missing_query(metric: str, normalize: bool) -> None:
    bank = [np.ones(32), np.zeros(39), np.tile([1., -1.], 20), np.tile([1., -1.], 30), np.full(20, np.nan)]
    cache = NCCCache(bank, metric, {"normalize": normalize}, n_jobs=1)
    for query in (np.ones(35), np.tile([1., -1.], 16), np.full(21, np.nan)):
        expected = batch.one_vs_many(query, bank, metric, backend="native", normalize=normalize, n_jobs=1)
        _assert_bits(cache.evaluate(query, np.arange(len(bank))), expected)


@pytest.mark.parametrize("metric", ["max_ncc", "independent_sbd"])
def test_ncc_bank_fft_reused_across_queries_with_same_padding_length(
    metric: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    rng = np.random.default_rng(811)
    bank = [rng.normal(size=(32, 2)) for _ in range(5)]
    queries = [rng.normal(size=(n, 2)) for n in (32, 33)]
    expected = [batch.one_vs_many(query, bank, metric, backend="native", n_jobs=1) for query in queries]
    original_fft = batch.sp_fft.rfft
    calls: list[int] = []

    def counted(values: np.ndarray, length: int, **kwargs: object) -> np.ndarray:
        calls.append(length)
        return original_fft(values, length, **kwargs)

    monkeypatch.setattr(batch.sp_fft, "rfft", counted)
    cache = NCCCache(bank, metric, {}, n_jobs=1)
    first = cache.prepare_query(queries[0])
    assert calls == []
    first_values = np.concatenate([
        cache.evaluate(first, np.array([0, 1])), cache.evaluate(first, np.array([2, 3, 4])),
    ])
    _assert_bits(first_values, expected[0])
    assert len(calls) == 12  # Two channels, one query and five bank members.
    _assert_bits(cache.evaluate(first, np.arange(5)), expected[0])
    assert len(calls) == 12
    second = cache.prepare_query(queries[1])
    _assert_bits(cache.evaluate(second, np.arange(5)), expected[1])
    assert len(calls) == 14  # Only the second query needs new FFTs.
    assert len(set(calls)) == 1


def test_ncc_spectrum_cache_is_bounded_without_changing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    rng = np.random.default_rng(812)
    bank = [rng.normal(size=(32, 2)) for _ in range(5)]
    query = rng.normal(size=(32, 2))
    expected = batch.one_vs_many(query, bank, "sbd", backend="native", n_jobs=1)
    monkeypatch.setattr(ncc_module, "_SPECTRUM_CACHE_BYTES", 1100)
    cache = NCCCache(bank, "sbd", {}, n_jobs=1)
    prepared = cache.prepare_query(query)
    _assert_bits(cache.evaluate(prepared, np.arange(5)), expected)
    assert 0 < cache._spectrum_bytes <= 1100
    _assert_bits(cache.evaluate(prepared, np.arange(4, -1, -1)), expected[::-1])
    assert cache._spectrum_bytes <= 1100


def test_ncc_cache_snapshots_and_prepared_query_ownership() -> None:
    rng = np.random.default_rng(813)
    bank = [rng.normal(size=n) for n in (8, 16, 32)]
    raw_query = rng.normal(size=31)
    cache = NCCCache(bank, "max_ncc", {}, n_jobs=1)
    query = cache.prepare_query(raw_query)
    expected = cache.evaluate(query, np.arange(3))
    bank[0][:] = 100
    raw_query[:] = -100
    _assert_bits(cache.evaluate(query, np.arange(3)), expected)
    for values in (query.raw, query.clean, *query.units):
        with pytest.raises(ValueError):
            values.setflags(write=True)
    with pytest.raises(ValueError, match="different"):
        NCCCache(bank, "max_ncc", {}, n_jobs=1).evaluate(query, np.array([0]))
    with pytest.raises(IndexError):
        cache.evaluate(query, np.array([-1]))
    with pytest.raises(ValueError, match="integer"):
        cache.evaluate(query, np.array([1.5]))
    assert cache.evaluate(None, np.array([], dtype=np.int64)).size == 0
