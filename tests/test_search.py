import json
import numpy as np
import pytest

from echotime import batch
from echotime._native import native_available
from echotime.search import SearchIndex, PreparedCollection
from echotime.similarity import compare_series

BACKENDS = ["python"] + (["native"] if native_available() else [])
SIMILARITY = {"lcss_similarity", "max_ncc", "independent_max_ncc", "similarity_score", "component_mean"}


def truth_order(values, target):
    return np.asarray(sorted(range(len(values)), key=lambda i: (1, 0, i) if np.isnan(values[i]) else (0, -values[i] if target in SIMILARITY else values[i], i)))


def assert_exact(values, reference):
    assert [float(x).hex() for x in values] == [float(x).hex() for x in reference]


def database():
    rng = np.random.default_rng(51)
    rows = [rng.normal(size=20 + i) for i in range(8)]
    rows[1] = rows[0].copy()
    rows[4][3] = np.nan
    rows += [np.ones(24), np.zeros(25), np.array([np.nan, np.nan])]
    return rows


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("target", [name for name in batch.METRICS if name != "best_shift"])
def test_all_lowlevel_topk_exact(target, backend):
    rows = database()
    query = rows[0]
    params = {"window": 3} if target in batch._ELASTIC else {}
    index = SearchIndex.build(rows, target=target, backend=backend, **params)
    actual = batch.one_vs_many(query, rows, metric=target, backend=backend, n_jobs=1, **params)
    order = truth_order(actual, target)
    for k in (1, 3, len(rows) + 5):
        hits = index.search(query, k=k, block_size=3, bounds="all")
        np.testing.assert_array_equal(hits.ids, order[:k])
        assert_exact(hits.values, actual[order[:k]])
        assert hits.certified and hits.stats["coverage_complete"]
        assert hits.stats["covered_candidates"] == len(rows)
        assert hits.stats["pruned"] + hits.stats["exact_evaluations"] == len(rows)


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("target", ["dtw", "edr", "lcss", "lcss_similarity", "erp", "twed", "sbd", "acf", "periodogram", "trend"])
def test_mixed_channels_global_reference(target, backend):
    rng = np.random.default_rng(814)
    rows = [rng.normal(size=(23, 3)), rng.normal(size=26), rng.normal(size=(21, 3)), rng.normal(size=(18, 2))]
    rows[0][2, 0] = np.nan
    query = rng.normal(size=(20, 3))
    index = SearchIndex.build(rows, target=target, backend=backend)
    actual = batch.one_vs_many(query, rows, metric=target, backend=backend)
    order = truth_order(actual, target)
    hits = index.search(query, k=8, block_size=1, bounds="all")
    np.testing.assert_array_equal(hits.ids, order)
    assert_exact(hits.values, actual[order])


@pytest.mark.parametrize("target,params", [
    ("dtw", {"window": 0, "normalize": True}),
    ("erp", {"window": 2, "gap_value": 0.3, "mode": "fast"}),
    ("edr", {"window": 1, "epsilon": 0.1, "normalized": False, "mode": "fast"}),
    ("lcss", {"window": None, "epsilon": 0., "mode": "fast"}),
    ("twed", {"window": 4, "nu": 0., "lambda_": 0.}),
    ("acf", {"max_lag": 4}), ("periodogram", {"n_coeffs": 7}),
    ("ordinal_js", {"order": 4, "delay": 2}), ("sbd", {"normalize": False}),
])
def test_parameters_range_threshold_and_adjacent_float(target, params):
    rows = database()[:8]
    index = SearchIndex.build(rows, target=target, **params)
    values = batch.one_vs_many(rows[0], rows, metric=target, **params)
    for radius in (0., values[3], np.nextafter(values[3], -np.inf), float("inf"), -1.):
        selected = [i for i in truth_order(values, target) if values[i] <= radius]
        hits = index.range_search(rows[0], radius, bounds="all", block_size=2)
        np.testing.assert_array_equal(hits.ids, selected)
        assert_exact(hits.values, values[selected])


@pytest.mark.parametrize("target", ["similarity_score", "component_mean"])
@pytest.mark.parametrize("points", [4, 16, 32])
def test_highlevel_full_report_reference(target, points):
    rng = np.random.default_rng(21)
    rows = [rng.normal(size=23), rng.normal(size=(27, 3)), np.ones(20), np.arange(20.), rng.normal(size=25)]
    rows[4][3] = np.nan
    query = rows[0]
    index = SearchIndex.build(rows, target=target, n_points=points)
    values = np.asarray([getattr(compare_series(query, row, n_points=points), target) for row in rows])
    order = truth_order(values, target)
    for k in (1, 3, 8):
        hits = index.search(query, k=k)
        np.testing.assert_array_equal(hits.ids, order[:k])
        assert_exact(hits.values, values[order[:k]])


def test_cheap_component_pruning_and_dtw_cutoff_do_work():
    rng = np.random.default_rng(7)
    query = rng.normal(size=64)
    rows = [query.copy(), *[query + value for value in range(3, 15)]]
    index = SearchIndex.build(rows, target="dtw", window=4)
    hits = index.search(query, k=1, bounds="cheap")
    assert hits.ids.tolist() == [0]
    assert hits.stats["pruned"] == 12
    assert hits.stats["endpoint_bounds"] == 12
    no_bounds = index.search(query, k=1, bounds="none")
    assert no_bounds.stats["cutoff_abandoned"] == 12
    assert_exact(no_bounds.values, hits.values)


def test_timestamps_and_snapshot_mutation():
    rng = np.random.default_rng(29)
    rows = rng.normal(size=(5, 20))
    ts = np.arange(20.) ** 1.5
    saved = rows.copy()
    index = SearchIndex.build(rows, target="twed", layout="rows", timestamps=ts, nu=.1)
    rows[:] = 99
    query = saved[0]
    values = batch.one_vs_many(query, saved, metric="twed", layout="rows", query_timestamps=ts, candidate_timestamps=ts, nu=.1)
    hits = index.search(query, k=5, query_timestamps=ts)
    order = truth_order(values, "twed")
    assert_exact(hits.values, values[order])
    with pytest.raises(ValueError):
        index.collection[0].flags.writeable = True
    with pytest.raises(AttributeError):
        index.collection._series = ()
    with pytest.raises(AttributeError):
        index.target = "dtw"
    with pytest.raises(ValueError):
        hits.ids.flags.writeable = True


@pytest.mark.parametrize("mmap", [True, False])
def test_roundtrip_ragged_multichannel_timestamps(tmp_path, mmap):
    rows = [np.arange(20.), np.arange(75.).reshape(25, 3), np.empty(0)]
    ts = [np.arange(20.), np.arange(25.) ** 1.2, np.empty(0)]
    original = SearchIndex.build(rows, target="twed", timestamps=ts, nu=.03, window=4)
    before = original.search(rows[0], k=5, query_timestamps=ts[0])
    saved = original.save(tmp_path / "index")
    loaded = SearchIndex.load(saved, mmap=mmap)
    after = loaded.search(rows[0], k=5, query_timestamps=ts[0])
    np.testing.assert_array_equal(after.ids, before.ids)
    assert_exact(after.values, before.values)
    with pytest.raises(ValueError):
        loaded.collection[0].flags.writeable = True
    with pytest.raises(FileExistsError):
        original.save(saved)


def test_persistence_refuses_corrupt_offset_and_format(tmp_path):
    index = SearchIndex.build(database(), target="dtw")
    path = index.save(tmp_path / "index")
    offsets = np.load(path / "offsets.npy")
    offsets[-1] += 1
    np.save(path / "offsets.npy", offsets)
    with pytest.raises(ValueError):
        SearchIndex.load(path)
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["version"] = 999
    (path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="unsupported"):
        SearchIndex.load(path)


def test_empty_zero_k_validation_and_stable_ties(tmp_path):
    empty = SearchIndex.build([], target="dtw")
    assert empty.search([1], k=3).ids.size == 0
    assert SearchIndex.load(empty.save(tmp_path / "empty")).search([1]).ids.size == 0
    index = SearchIndex.build(np.ones((8, 20)), target="dtw", layout="rows")
    assert index.search(np.ones(20), k=3).ids.tolist() == [0, 1, 2]
    assert index.search(np.ones(20), k=0).ids.size == 0
    for k in (-1, True, 1.5):
        with pytest.raises(ValueError):
            index.search(np.ones(20), k=k)
    with pytest.raises(ValueError):
        SearchIndex.build(database(), target="best_shift")
    with pytest.raises(TypeError):
        SearchIndex.build(database(), target="dtw", mode="fast")
    SearchIndex.build(database(), target="dtw", mode="exact")
    with pytest.raises(ValueError):
        index.search(np.ones(20), initial_candidates=[0, 0])
    with pytest.raises(ValueError):
        SearchIndex.build(database(), target="max_ncc").range_search(np.ones(20), .5)


def test_warm_start_refine_batch_and_explain():
    rows = database()[:5]
    index = SearchIndex.build(rows, target="dtw", window=3)
    hits = index.search(rows[0], k=3)
    warm = index.search(rows[0], k=3, initial_candidates=np.array([4, 2]))
    np.testing.assert_array_equal(warm.ids, hits.ids)
    assert_exact(warm.values, hits.values)
    refined = index.refine(rows[0], hits)
    np.testing.assert_array_equal(refined.ids, hits.ids)
    batch_hits = index.search_batch(rows[:2], k=3)
    np.testing.assert_array_equal(batch_hits[0].ids, hits.ids)
    reports = index.explain(rows[0], hits.ids[:2], n_points=16)
    assert len(reports) == 2
    assert_exact([r.similarity_score for r in reports], [compare_series(rows[0], rows[i], n_points=16).similarity_score for i in hits.ids[:2]])


def test_highlevel_invalid_input_keeps_reference_exception():
    index = SearchIndex.build([np.arange(20.)], target="similarity_score")
    with pytest.raises(ValueError, match="infs or NaNs"):
        index.search(np.full(20, np.nan))


def test_array_like_gap_is_a_snapshot_not_a_mutable_cache_key(tmp_path):
    from array import array
    gap = array("d", [0.])
    index = SearchIndex.build([np.array([1., 3.])], target="erp", gap_value=gap)
    first = index.search([1.], k=1)
    gap[0] = 10.
    second = index.search([1.], k=1)
    assert_exact(first.values, second.values)
    assert_exact(SearchIndex.load(index.save(tmp_path / "index")).search([1.]).values, first.values)
    assert index.params["gap_value"][0] == 0.


def test_boolean_normalization_and_integer_array_parameters_keep_meaning():
    rows = database()[:4]
    # A nonempty list is truthy under the original bool(normalize) contract.
    index = SearchIndex.build(rows, target="dtw", normalize=[False], window=np.asarray(3))
    expected = SearchIndex.build(rows, target="dtw", normalize=True, window=3).search(rows[0])
    actual = index.search(rows[0])
    assert_exact(actual.values, expected.values)


def test_mixed_erp_empty_pair_retains_scalar_gap_validation():
    query = np.arange(12.).reshape(6, 2)
    rows = [query, np.empty(0)]
    for backend in BACKENDS:
        expected = batch.one_vs_many(query, rows, "erp", gap_value=np.zeros(2), backend=backend)
        index = SearchIndex.build(rows, target="erp", gap_value=np.zeros(2), backend=backend)
        hits = index.search(query, k=2)
        assert_exact(hits.values, expected)
        assert hits.ids.tolist() == [0, 1]


def test_numpy_thread_count_and_semantics_manifest(tmp_path):
    index = SearchIndex.build(database(), n_jobs=np.int64(2))
    path = index.save(tmp_path / "index")
    assert SearchIndex.load(path).search(database()[0], k=1).ids.tolist() == [0]
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["score_semantics"] = "future-incompatible-version"
    (path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="semantics"):
        SearchIndex.load(path)
