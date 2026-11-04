"""Run from a source installation: python examples/search_index.py.

This small deterministic demonstration measures recall for its own query;
the number printed is not a general recall guarantee for another database.
"""
import json
import tempfile

import numpy as np

from echotime import PreparedSeries, SearchIndex, compare_series


def main():
    rng = np.random.default_rng(20261104)
    collection = rng.normal(size=(128, 128)).cumsum(axis=1)
    query = collection[37] + rng.normal(scale=.05, size=128)
    index = SearchIndex.build(collection, target="dtw", layout="rows", window=8, n_jobs=2)
    exact = index.search(query, k=5)
    approximate = index.search(query, k=5, mode="approximate", candidates=24,
                               strategy="multiview", audit=True)
    refined = index.refine(query, approximate)
    assert np.array_equal(refined.ids, exact.ids)
    assert np.array_equal(refined.values, exact.values)
    with tempfile.TemporaryDirectory() as directory:
        index.save(directory + "/index")
        restored = SearchIndex.load(directory + "/index").search(query, k=5)
        assert np.array_equal(restored.ids, exact.ids)
    score = compare_series(PreparedSeries(query), PreparedSeries(collection[37]), output="score")
    print(json.dumps({"exact": exact.to_dict(), "approximate": approximate.to_dict(),
                      "refined_certified": refined.certified,
                      "separate_composite_score": score.to_dict()}, indent=2))


if __name__ == "__main__":
    main()
