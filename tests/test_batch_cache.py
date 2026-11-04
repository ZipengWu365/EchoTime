import numpy as np
import pytest

from echotime import batch, similarity_methods as sm
from echotime._native import native_available

pytestmark = pytest.mark.skipif(not native_available(), reason="native batch path required")


def test_ncc_cleaning_once_per_unique_series(monkeypatch):
    rows = np.random.default_rng(1).normal(size=(12, 40))
    original = sm._clean_series
    calls = []
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(sm, "_clean_series", counted)
    batch.pairwise_distance_matrix(rows, "sbd", layout="rows", backend="native", n_jobs=1)
    assert len(calls) == len(rows)


def test_embedding_cache_once_and_chunking_exact(monkeypatch):
    rows = np.random.default_rng(7).normal(size=(11, 32))
    baseline = batch.pairwise_distance_matrix(rows, "trend", layout="rows", backend="native")
    original = sm._trend_feature_vector
    calls = []
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(sm, "_trend_feature_vector", counted)
    monkeypatch.setattr(batch, "_EMBED_BLOCK_BYTES", 1)
    result = batch.pairwise_distance_matrix(rows, "trend", layout="rows", backend="native")
    assert len(calls) == len(rows)
    np.testing.assert_array_equal(result.view(np.uint64), baseline.view(np.uint64))


@pytest.mark.parametrize("metric", ["acf", "periodogram", "ordinal_js", "linear_trend_model"])
def test_embedding_chunk_boundary_does_not_change_values(monkeypatch, metric):
    rows = [np.random.default_rng(i).normal(size=19 + i) for i in range(7)]
    original = batch.pairwise_distance_matrix(rows, metric, backend="native")
    monkeypatch.setattr(batch, "_EMBED_BLOCK_BYTES", 1)
    chunked = batch.pairwise_distance_matrix(rows, metric, backend="native")
    np.testing.assert_array_equal(original.view(np.uint64), chunked.view(np.uint64))


def test_twed_empty_bank_timestamp_sentinel():
    rows = [np.arange(20.), np.full(5, np.nan), np.empty(0)]
    result = batch.one_vs_many(rows[0], rows, metric="twed", backend="native")
    reference = batch.one_vs_many(rows[0], rows, metric="twed", backend="python")
    np.testing.assert_array_equal(result, reference)
