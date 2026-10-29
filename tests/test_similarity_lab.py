"""Independent mathematical checks for the shared-input teaching laboratory."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import pearsonr

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("similarity_lab_builder", ROOT / "tools/build_similarity_lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


@pytest.fixture(scope="module")
def data():
    return lab.build_data()


def test_identity_and_same_saved_inputs(data):
    for rows in data["states"].values():
        assert len(rows) == 21
        assert np.allclose(rows[0]["y"], data["x"], atol=1e-10)
        for name, item in rows[0]["methods"].items():
            assert item["value"] == pytest.approx(1 if name in {"pearson", "lcss"} else 0, abs=1e-8)
        for row in rows:
            for name in ("rmse", "dtw", "lcss"):
                assert row["methods"][name]["b"] == row["y"]


def test_offset_and_positive_gain_invariances(data):
    offset = data["states"]["offset"][-1]["methods"]
    assert offset["rmse"]["value"] == pytest.approx(1.5, abs=1e-10)
    for method in ("zrmse", "sbd", "derivative", "acf", "sax"):
        assert offset[method]["value"] == pytest.approx(0, abs=1e-9)
    gain = data["states"]["gain"][-1]["methods"]
    for method in ("zrmse", "sbd", "acf", "sax"):
        assert gain[method]["value"] == pytest.approx(0, abs=1e-9)
    assert gain["pearson"]["value"] == pytest.approx(1, abs=1e-9)
    assert gain["derivative"]["value"] > 0


def test_phase_construction_preserves_real_special_bins_and_magnitudes():
    x = lab.baseline()
    f = np.fft.rfft(x, norm="ortho")
    for level in range(21):
        y, _ = lab.transform(x, "phase", level)
        g = np.fft.rfft(y, norm="ortho")
        np.testing.assert_allclose(np.abs(f), np.abs(g), atol=2e-14)
        np.testing.assert_allclose(f[[0,-1]], g[[0,-1]], atol=2e-14)
        full = np.fft.fft(y)
        np.testing.assert_allclose(full[1:], np.conj(full[:0:-1]), atol=2e-14)
    assert np.linalg.norm(x-y) > 1


def test_circular_shift_and_reversal_feature_limits(data):
    for row in data["states"]["shift"]:
        assert row["methods"]["dft"]["value"] == pytest.approx(0, abs=1e-9)
    final = data["states"]["reversal"][-1]["methods"]
    assert final["dft"]["value"] == pytest.approx(0, abs=1e-9)
    assert final["acf"]["value"] == pytest.approx(0, abs=1e-9)
    assert final["rmse"]["value"] > 0.1
    # A circularly rolled, nonperiodically windowed signal need not obtain perfect
    # zero-padded linear NCC: the discarded tail retains energy in normalization.
    assert data["states"]["shift"][-1]["methods"]["sbd"]["value"] > 0.01
    assert data["states"]["phase"][-1]["methods"]["acf"]["value"] > 0.01


def test_warp_is_increasing_and_fixes_endpoints():
    x = lab.baseline()
    for level in range(21):
        _, params = lab.transform(x, "warp", level)
        t = params["sample_map"]
        assert t[0] == 0 and t[-1] == len(x)-1
        assert np.all(np.diff(t) > 0)


def test_dtw_path_and_lcss_matches_reproduce_results(data):
    x = np.asarray(data["x"])
    for rows in data["states"].values():
        for row in rows:
            y = np.asarray(row["y"])
            dt = row["methods"]["dtw"]
            pairs = np.asarray(dt["pairs"])
            assert pairs[0].tolist() == [0,0]
            assert pairs[-1].tolist() == [63,63]
            assert np.max(np.abs(pairs[:,0]-pairs[:,1])) <= 8
            assert set(map(tuple,np.diff(pairs,axis=0))).issubset({(1,1),(1,0),(0,1)})
            assert np.sum((x[pairs[:,0]]-y[pairs[:,1]])**2) == pytest.approx(dt["value"]**2, abs=2e-8)
            lc = row["methods"]["lcss"]
            pairs = np.asarray(lc["pairs"], dtype=int).reshape(-1,2)
            assert len(pairs)/64 == lc["value"]
            if len(pairs):
                assert np.all(np.diff(pairs,axis=0) > 0)
                assert np.max(np.abs(pairs[:,0]-pairs[:,1])) <= 8
                assert np.max(np.abs(x[pairs[:,0]]-y[pairs[:,1]])) <= 0.25+1e-9


def test_independent_small_alignment_examples():
    # One repeated sample is free under unconstrained DTW but only two distinct
    # ordered pairs can match in LCSS with zero amplitude tolerance.
    x = np.array([0.,1.,2.])
    y = np.array([0.,0.,2.])
    assert lab.dtw(x,y,radius=0)[0] == pytest.approx(1)
    assert lab.lcss(x,y,epsilon=0,radius=3)[0] == pytest.approx(2/3)
    x = np.array([0.,1.])
    y = np.array([0.,0.,1.])
    assert lab.dtw(x,y,radius=3)[0] == 0


def test_correlation_relation_sax_lower_bound_and_contributions(data):
    x = np.asarray(data["x"])
    for rows in data["states"].values():
        for row in rows:
            y = np.asarray(row["y"])
            results = row["methods"]
            assert results["pearson"]["value"] == pytest.approx(pearsonr(x,y).statistic, abs=2e-9)
            assert results["zrmse"]["value"]**2 == pytest.approx(2*(1-results["pearson"]["value"]), abs=2e-9)
            assert results["sax"]["value"] <= np.linalg.norm(lab.zscore(x)-lab.zscore(y))+1e-8
            for name in ("rmse", "zrmse", "dtw", "derivative", "dft", "acf", "paa", "sax"):
                item = results[name]
                assert sum(item["contribution"]) == pytest.approx(item["value"]**2, abs=2e-8)
            assert sum(results["pearson"]["contribution"]) == pytest.approx(results["pearson"]["value"], abs=1e-8)


def test_saved_bundle_matches_generator_and_resource_budget(data):
    saved = lab.unpack_data(json.loads((lab.BUNDLE/"states.json").read_text()))
    assert saved == data
    manifest = json.loads((lab.BUNDLE/"manifest.json").read_text())
    assert manifest["total_bytes"] < 3_000_000
    for filename, digest in manifest["sha256"].items():
        assert lab.digest(lab.BUNDLE/filename) == digest
