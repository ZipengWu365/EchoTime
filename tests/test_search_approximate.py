import numpy as np
import pytest

from echotime import SearchIndex, one_vs_many, compare_series


@pytest.mark.parametrize("target", ["dtw", "sbd", "similarity_score"])
@pytest.mark.parametrize("strategy", ["multiview", "pyramid", "binary", "faiss", "faiss_hnsw"])
def test_approximate_exact_rerank_and_refinement(target, strategy):
    if strategy.startswith("faiss"):
        pytest.importorskip("faiss")
    rng = np.random.default_rng(29)
    rows = np.cumsum(rng.normal(size=(36, 64)), axis=1)
    query = rows[19] + rng.normal(scale=.1, size=64)
    params = {"window": 4} if target == "dtw" else {"n_points": 32} if target == "similarity_score" else {}
    index = SearchIndex.build(rows, target=target, layout="rows", n_jobs=2, **params)
    provisional = index.search(query, k=5, mode="approximate", candidates=12, strategy=strategy, audit=True)
    assert not provisional.certified and not provisional.stats["coverage_complete"]
    assert provisional.stats["candidates"] == 12
    assert provisional.stats["audit_queries"] == 1
    assert provisional.stats["audit_seconds"] >= 0
    assert 0 <= provisional.recall_estimate <= 1
    values = np.asarray([compare_series(query, row, n_points=32).similarity_score for row in rows]) if target == "similarity_score" else one_vs_many(query, rows, metric=target, layout="rows", **params)
    assert [float(x).hex() for x in provisional.values] == [float(x).hex() for x in values[provisional.ids]]
    refined = index.refine(query, provisional)
    truth = index.search(query, k=5)
    assert refined.certified and refined.stats["covered_candidates"] == len(rows)
    np.testing.assert_array_equal(refined.ids, truth.ids)
    np.testing.assert_array_equal(refined.values, truth.values)
    actual_recall = len(set(truth.ids).intersection(provisional.ids)) / len(truth.ids)
    assert provisional.recall_estimate == actual_recall


def test_recall_is_not_invented_and_audit_measures_known_misses():
    rows = np.tile(np.arange(20.), (12, 1)) + np.arange(12.)[:, None] * 10
    index = SearchIndex.build(rows, layout="rows", target="dtw")
    class FixedCandidates:
        def select(self, query, budget, strategy):
            return np.array([1, 3, 7, 10]), {"strategy": "test_selected_subset"}
    index._candidate_engine = FixedCandidates()
    hits = index.search(rows[0], k=3, mode="approximate", candidates=4)
    assert hits.recall_estimate is None
    assert hits.stats["audit_queries"] == 0
    audited = index.search(rows[0], k=3, mode="approximate", candidates=4, audit=True)
    assert audited.recall_estimate == 1 / 3  # Ground truth is 0,1,2; C={1,3,7,10}.
    assert not audited.certified


def test_full_budget_remains_explicit_approximate_and_small_budget_rejected():
    rows = np.random.default_rng(83).normal(size=(10, 32))
    index = SearchIndex.build(rows, layout="rows")
    hits = index.search(rows[0], k=3, mode="approximate", candidates=100, audit=True)
    assert not hits.certified and hits.recall_estimate == 1.0
    assert hits.stats["candidates"] == len(rows)
    with pytest.raises(ValueError, match="at least"):
        index.search(rows[0], k=5, mode="approximate", candidates=4)
    with pytest.raises(ValueError):
        index.search(rows[0], k=3, audit=True)


def test_approximate_roundtrip_rebuilds_features_without_pickle(tmp_path):
    rows = np.random.default_rng(11).normal(size=(20, 32))
    index = SearchIndex.build(rows, target="dtw", layout="rows", window=3)
    before = index.search(rows[0], k=3, mode="approximate", candidates=10, strategy="binary")
    after = SearchIndex.load(index.save(tmp_path / "search")).search(rows[0], k=3, mode="approximate", candidates=10, strategy="binary")
    np.testing.assert_array_equal(before.ids, after.ids)
    np.testing.assert_array_equal(before.values, after.values)
