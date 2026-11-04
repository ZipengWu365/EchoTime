"""Persistent bank parity, full/native dispatch, and cutoff result contracts."""

from __future__ import annotations

import numpy as np
import pytest

from echotime import _native
from echotime.batch import one_vs_many
from echotime._search_elastic import ElasticCache


native = pytest.mark.skipif(
    not _native.native_available() or not hasattr(_native.ext(), "dtw_pairs_cutoff"),
    reason="native cutoff extension not built",
)
BACKENDS = ["python", pytest.param("native", marks=native)]
METRICS = [
    ("dtw", {}), ("dtw", {"normalize": True}),
    ("erp", {"gap_value": 0.3}),
    ("twed", {"nu": 0.02, "lambda_": 0.1}),
    ("edr", {"epsilon": 0.2}), ("edr", {"epsilon": 0.2, "normalized": False}),
    ("lcss", {"epsilon": 0.2}), ("lcss_similarity", {"epsilon": 0.2}),
]


def _assert_bit_equal(actual, expected):
    actual, expected = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    np.testing.assert_array_equal(np.isnan(actual), np.isnan(expected))
    finite_or_inf = ~np.isnan(expected)
    np.testing.assert_array_equal(actual[finite_or_inf].view(np.uint64), expected[finite_or_inf].view(np.uint64))


@native
@pytest.mark.parametrize("metric,options", METRICS)
@pytest.mark.parametrize("long", [False, True], ids=["short-exact", "long-fast"])
def test_cached_full_cutoff_and_public_batch_are_bit_identical(metric, options, long):
    rng = np.random.default_rng(20261104)
    n = 530 if long else 23
    query = rng.normal(size=(n, 3))
    # The mismatch group aggregates to one channel and contains a full SIMD
    # group of equal-length pairs; the matching group retains all channels.
    series = [rng.normal(size=(n + 3, 3 if i < 4 else 2)) for i in range(16)] + [np.array([])]
    params = {"window": 3, **options}
    if metric != "dtw":
        params["mode"] = "fast" if long else "exact"
    query_ts = np.arange(n, dtype=float) * 0.7 - 2 if metric == "twed" else None
    timestamps = [np.arange(len(x), dtype=float) * 0.9 - 3 for x in series] if metric == "twed" else [None] * len(series)
    cache = ElasticCache(series, timestamps, metric, params)
    prepared = cache.prepare_query(query, query_ts, backend="native")
    ids = np.arange(len(series), dtype=np.int64)
    full, full_flags, full_cells = cache.evaluate_full(prepared, ids, n_jobs=4, backend="native")
    unbounded, cutoff_flags, cutoff_cells = cache.evaluate(prepared, ids, n_jobs=4, backend="native")
    reference = one_vs_many(query, series, metric, query_timestamps=query_ts,
                            candidate_timestamps=timestamps, n_jobs=4, backend="native", **params)
    _assert_bit_equal(full, reference)
    _assert_bit_equal(unbounded, reference)
    assert not np.any(full_flags)
    assert not np.any(cutoff_flags)
    np.testing.assert_array_equal(full_cells, cutoff_cells)
    assert full_cells[-1] == 0
    assert np.all(full_cells[:-1] > 0)

    if metric != "lcss_similarity":
        threshold = float(np.median(full[np.isfinite(full)]))
        bounded, exceeded, visited = cache.evaluate(prepared, ids, cutoff=threshold, n_jobs=4, backend="native")
        np.testing.assert_array_equal(exceeded, full > threshold)
        assert np.all(np.isnan(bounded[exceeded]))
        _assert_bit_equal(bounded[~exceeded], full[~exceeded])
        assert np.all(visited <= full_cells)

    # Cached bank positions must also survive a sparse, reordered request.
    subset = np.array([15, 1, 16, 6], dtype=np.int64)
    again, flags, cells = cache.evaluate_full(prepared, subset, n_jobs=4, backend="native")
    _assert_bit_equal(again, full[subset])
    np.testing.assert_array_equal(cells, full_cells[subset])
    assert not np.any(flags)


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("metric,options", METRICS)
@pytest.mark.parametrize("query", [[], [np.nan, np.inf]])
def test_empty_query_stays_nan_with_no_distance_certificate(backend, metric, options, query):
    cache = ElasticCache([np.array([1., 2.])], [None], metric, options)
    prepared = cache.prepare_query(query, backend=backend)
    full, full_flags, full_cells = cache.evaluate_full(prepared, [0], backend=backend)
    bounded, exceeded, visited = cache.evaluate(prepared, [0], cutoff=-np.inf, backend=backend)
    assert np.isnan(full[0]) and np.isnan(bounded[0])
    assert not full_flags[0] and not exceeded[0]
    assert full_cells[0] == visited[0] == 0


@pytest.mark.parametrize("query", [[], [np.nan, np.inf]])
def test_python_empty_erp_returns_before_gap_vector_validation(query):
    params = {"gap_value": [0., 0.]}
    cache = ElasticCache([np.array([1., 2.])], [None], "erp", params)
    prepared = cache.prepare_query(query, backend="python")
    values, flags, cells = cache.evaluate_full(prepared, [0], backend="python")
    reference = one_vs_many(query, [np.array([1., 2.])], "erp", backend="python", **params)
    _assert_bit_equal(values, reference)
    assert np.isnan(values[0]) and not flags[0] and cells[0] == 0


@native
@pytest.mark.parametrize("query", [[], [np.nan, np.inf]])
def test_native_empty_erp_keeps_existing_batch_gap_validation(query):
    # The existing native batch API validates a bank's gap vector eagerly;
    # its validation order differs from the Python scalar fallback above.
    params = {"gap_value": [0., 0.]}
    with pytest.raises(ValueError, match="gap_value"):
        one_vs_many(query, [np.array([1., 2.])], "erp", backend="native", **params)
    cache = ElasticCache([np.array([1., 2.])], [None], "erp", params)
    with pytest.raises(ValueError, match="gap_value"):
        cache.prepare_query(query, backend="native")


@pytest.mark.parametrize("metric,options", METRICS)
def test_elastic_bank_timestamp_validation_uses_retained_rows(metric, options):
    for timestamps, message in (([2., 1.], "strictly increasing"), ([1., np.nan], "finite"), ([0., 1., 2.], "match")):
        with pytest.raises(ValueError, match=message):
            ElasticCache([np.array([1., 2.])], [timestamps], metric, options)
    series = [np.array([1., np.nan, 2.])]
    cache = ElasticCache(series, [[-2., np.nan, -1.]], metric, options)
    for timestamps, message in (([2., 1.], "strictly increasing"), ([1., np.nan], "finite"), ([0., 1., 2.], "match")):
        with pytest.raises(ValueError, match=message):
            cache.prepare_query([1., 2.], timestamps, backend="python")
    prepared = cache.prepare_query([1., np.nan, 2.], [-2., np.nan, -1.], backend="python")
    values, flags, _ = cache.evaluate_full(prepared, [0], backend="python")
    assert np.isfinite(values[0]) and not flags[0]


@pytest.mark.parametrize("backend", BACKENDS)
def test_constructor_consumes_each_input_generator_once(backend):
    series = (np.array([1., 2., 3.]) for _ in range(2))
    timestamps = (None for _ in range(2))
    cache = ElasticCache(series, timestamps, "dtw", {})
    prepared = cache.prepare_query([1., 2., 3.], backend=backend)
    values, flags, cells = cache.evaluate_full(prepared, [0, 1], backend=backend)
    np.testing.assert_array_equal(values, [0., 0.])
    np.testing.assert_array_equal(cells, [9, 9])
    assert not np.any(flags)


@native
@pytest.mark.parametrize("metric,options", METRICS)
def test_cache_clamps_huge_windows_before_calling_legacy_native(metric, options):
    query = np.array([1., 4., 2.])
    series = [np.array([1., 3., 2., 5.]), np.array([0., 1.])]
    # Never pass the huge window to the legacy native API: it historically
    # overflows window_bounds.  A safe unbounded reference is sufficient.
    reference = one_vs_many(query, series, metric, backend="python", **options)
    for window in (int(np.iinfo(np.int64).max), 10**100):
        cache = ElasticCache(series, [None, None], metric, {**options, "window": window})
        prepared = cache.prepare_query(query, backend="native")
        full, _, full_cells = cache.evaluate_full(prepared, [0, 1], n_jobs=4, backend="native")
        unbounded, flags, cells = cache.evaluate(prepared, [0, 1], n_jobs=4, backend="native")
        _assert_bit_equal(full, reference)
        _assert_bit_equal(unbounded, reference)
        np.testing.assert_array_equal(full_cells, [12, 6])
        np.testing.assert_array_equal(cells, full_cells)
        assert not np.any(flags)
