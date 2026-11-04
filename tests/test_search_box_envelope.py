"""Compiled interval extrema retain the original clipped-window envelope."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from echotime._search_bounds import _box_deltas


def _reference(a: np.ndarray, b: np.ndarray, width: int | None) -> np.ndarray:
    if width is None:
        return np.maximum(np.maximum(np.min(b, axis=0) - a, a - np.max(b, axis=0)), 0.0)
    out = np.empty_like(a)
    for i, row in enumerate(a):
        start, stop = max(0, i - width), min(len(b), i + width + 1)
        if stop <= start:
            out[i] = 0.0
        else:
            low, high = np.min(b[start:stop], axis=0), np.max(b[start:stop], axis=0)
            out[i] = np.maximum(np.maximum(low - row, row - high), 0.0)
    return out


@pytest.mark.parametrize("dim", [1, 3, 9, 129])
def test_box_extrema_exact_for_ragged_boundary_windows_and_large_widths(dim: int) -> None:
    rng = np.random.default_rng(720 + dim)
    for n, m in itertools.product((1, 2, 8, 19, 31), repeat=2):
        left, right = rng.normal(size=(n, dim)), rng.normal(size=(m, dim))
        for width in (None, 0, 1, 3, abs(n - m), max(n, m) - 1, 10**20):
            actual = _box_deltas(left, right, width)
            expected = _reference(left, right, width)
            np.testing.assert_array_equal(actual.view(np.uint64), expected.view(np.uint64))


@pytest.mark.parametrize("scale", [1e-300, 1.0, 1e150])
def test_box_extrema_preserve_endpoint_values_repeated_extrema_and_signed_zero(scale: float) -> None:
    left = np.asarray([-5.0, -0.0, 0.0, 2.0, 7.0, 3.0, -4.0, 0.0, 2.0, -0.0])[:, None] * scale
    right = np.asarray([0.0, -0.0, 3.0, 3.0, -4.0, -4.0])[:, None] * scale
    right[2] = np.nextafter(right[2], np.inf)
    for width in (0, 1, 2, 4, 9):
        actual = _box_deltas(left, right, width)
        expected = _reference(left, right, width)
        np.testing.assert_array_equal(actual.view(np.uint64), expected.view(np.uint64))


def test_box_extrema_empty_finite_window_keeps_zero_fallback() -> None:
    for width in (0, 1, 100):
        actual = _box_deltas(np.ones((5, 3)), np.empty((0, 3)), width)
        np.testing.assert_array_equal(actual, np.zeros((5, 3)))
    assert _box_deltas(np.empty((0, 3)), np.ones((5, 3)), 1).shape == (0, 3)
