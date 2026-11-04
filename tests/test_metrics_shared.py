"""Shared per-series work must preserve the standalone metric definitions."""

from __future__ import annotations

import numpy as np
import pytest

from echotime import metrics


@pytest.mark.parametrize("kind", ["regular", "irregular", "constant", "missing", "short_spectrum"])
def test_shared_metric_results_equal_standalone_definitions(kind: str) -> None:
    rng = np.random.default_rng(510)
    values = rng.normal(size=65)
    timestamps = None
    if kind == "irregular":
        timestamps = np.cumsum(rng.uniform(0.1, 2.0, size=65))
    elif kind == "constant":
        values[:] = 3.0
    elif kind == "missing":
        values[::9] = np.nan
        timestamps = np.cumsum(rng.uniform(0.1, 2.0, size=65))
    elif kind == "short_spectrum":
        values = values[:8]
    clean, clean_ts = metrics._clean_series_and_timestamps(values, timestamps)
    expected = {
        name: getattr(metrics, name)(clean, timestamps=clean_ts)
        for name in (
            "spectral_entropy", "forecastability", "low_freq_power_ratio",
            "spectral_peak_ratio", "spectral_flatness", "high_freq_power_ratio",
        )
    }
    expected["spectral_drift_js"] = metrics.spectral_drift(clean, timestamps=clean_ts)
    expected["hurst_exponent"] = metrics.hurst_exponent_rs(clean)
    expected["hurst_complexity_proxy"] = metrics.hurst_complexity_proxy(clean)
    actual = metrics.compute_series_metrics(values, timestamps=timestamps)
    for name, value in expected.items():
        if np.isnan(value):
            assert np.isnan(actual.metrics[name])
        else:
            assert actual.metrics[name].hex() == float(value).hex()
    np.testing.assert_array_equal(actual.clean_values, clean)
    if clean_ts is not None:
        np.testing.assert_array_equal(actual.clean_timestamps, clean_ts)


@pytest.mark.parametrize("irregular", [False, True])
def test_full_spectrum_and_hurst_are_computed_once_while_drift_keeps_two_halves(
    monkeypatch: pytest.MonkeyPatch, irregular: bool,
) -> None:
    rng = np.random.default_rng(511)
    values = rng.normal(size=65)
    timestamps = np.cumsum(rng.uniform(0.1, 2.0, size=65)) if irregular else None
    spectrum_calls: list[tuple[int, np.ndarray | None]] = []
    hurst_calls: list[int] = []
    original_spectrum = metrics._normalized_spectrum
    original_hurst = metrics.hurst_exponent_rs

    def spectrum(x: np.ndarray, **kwargs: object) -> tuple[np.ndarray, np.ndarray]:
        spectrum_calls.append((len(x), kwargs.get("timestamps")))
        return original_spectrum(x, **kwargs)

    def hurst(x: np.ndarray) -> float:
        hurst_calls.append(len(x))
        return original_hurst(x)

    monkeypatch.setattr(metrics, "_normalized_spectrum", spectrum)
    monkeypatch.setattr(metrics, "hurst_exponent_rs", hurst)
    metrics.compute_series_metrics(values, timestamps=timestamps)
    assert [length for length, _ in spectrum_calls] == [65, 32, 33]
    assert hurst_calls == [65]
    if timestamps is not None:
        np.testing.assert_array_equal(spectrum_calls[1][1], timestamps[:32])
        np.testing.assert_array_equal(spectrum_calls[2][1], timestamps[32:])


def test_too_short_profile_keeps_existing_minimal_metric_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("short-profile early return evaluated full-series features")

    monkeypatch.setattr(metrics, "_normalized_spectrum", forbidden)
    monkeypatch.setattr(metrics, "hurst_exponent_rs", forbidden)
    summary = metrics.compute_series_metrics(np.array([1.0, np.nan, 2.0]))
    assert set(summary.metrics) == {
        "n_points", "missing_fraction", "delta_t_cv", "gap_fraction", "irregular_spectral_support",
    }
    assert summary.metrics["n_points"] == 2.0
