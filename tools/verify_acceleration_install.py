#!/usr/bin/env python3
"""Exercise an installed package away from its checkout, including fallback.

Run with the target environment's Python. No build or editable install happens
in this verifier. Optional FAISS is exercised only when it is installed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import tempfile


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expect-installed", action="store_true")
    parser.add_argument("--expect-backend", choices=("native", "python"))
    args = parser.parse_args(argv)
    import numpy as np
    import echotime as et
    from echotime import batch
    package = Path(et.__file__).resolve()
    if args.expect_installed:
        assert package.parent != Path(__file__).resolve().parents[1] / "src/echotime", package
    info = et.similarity_backend_info()
    if args.expect_backend:
        assert info["effective"] == args.expect_backend, info
    if args.expect_backend == "native":
        assert info["cutoff_available"] and info["cutoff_abi_version"] == 1
    if args.expect_backend == "python":
        assert not info["native_available"], "This check must test an actually absent extension"
    rng = np.random.default_rng(816)
    rows = rng.normal(size=(12, 24)).cumsum(axis=1)
    query = rows[3] + rng.normal(scale=.03, size=24)
    larger = {"max_ncc", "independent_max_ncc", "lcss_similarity"}
    metrics = []
    for metric in batch.METRICS:
        if metric == "best_shift":
            continue
        params = {"window": 3} if metric in batch._ELASTIC else {}
        reference = et.one_vs_many(query, rows, metric=metric, layout="rows", n_jobs=2, **params)
        order = np.lexsort((np.arange(len(rows)), -reference if metric in larger else reference))[:4]
        index = et.SearchIndex.build(rows, target=metric, layout="rows", n_jobs=2, **params)
        result = index.search(query, k=4)
        assert result.certified
        np.testing.assert_array_equal(result.ids, order)
        assert [float(x).hex() for x in result.values] == [float(x).hex() for x in reference[order]], metric
        metrics.append(metric)
    index = et.SearchIndex.build(rows, target="dtw", layout="rows", window=3, n_jobs=2)
    strategies = ["multiview", "pyramid", "binary"]
    if importlib.util.find_spec("faiss") is not None:
        strategies += ["faiss", "faiss_hnsw"]
    for strategy in strategies:
        result = index.search(query, k=3, mode="approximate", candidates=8, strategy=strategy, audit=True)
        assert not result.certified and result.recall_estimate is not None
        assert index.refine(query, result).certified
    with tempfile.TemporaryDirectory() as folder:
        restored = et.SearchIndex.load(index.save(Path(folder) / "index"))
        np.testing.assert_array_equal(restored.search(query, k=4).ids, index.search(query, k=4).ids)
        del restored  # Release read-only memmaps before removing the directory.
    score = et.compare_series(et.PreparedSeries(query, n_points=32), et.PreparedSeries(rows[3], n_points=32), output="score")
    full = et.compare_series(query, rows[3], n_points=32)
    assert float(score.similarity_score).hex() == float(full.similarity_score).hex()
    from echotime.sitebundle import project_pages_bundle
    from echotime.method_animations import animation_catalog
    pages = project_pages_bundle()
    assert len(animation_catalog()["methods"]) == 137
    assert "articles/catalog.json" in pages
    assert pages["assets/method-animations/media/dtw.gif"].startswith(b"GIF89a")
    assert "guide/similarity-lab.html" in pages
    output = {"status": "passed", "package": str(package), "version": et.__version__,
              "backend": info, "exact_metrics": metrics, "approximate_strategies": strategies,
              "prepared_score_matches_report": True, "persistence": "passed",
              "animation_count": 137, "site_bundle_pages": len(pages)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
