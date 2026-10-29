"""Numerical truth checks for the educational elastic/kernel traces."""

import numpy as np

from tools.method_animation_data.elastic_kernel import (
    _X,
    _Y,
    _dtw,
    _edit,
    _gak,
    _msm,
    _soft_dtw,
)


def test_two_by_two_path_enumeration_checks_distinct_alignment_objectives():
    """Three explicitly listed paths provide an oracle separate from the DP."""
    x, y = np.array([0.2, 1.1]), np.array([0.5, 1.8])
    paths = [[(0, 0), (1, 1)], [(0, 0), (0, 1), (1, 1)],
             [(0, 0), (1, 0), (1, 1)]]
    squared = (x[:, None] - y[None, :]) ** 2
    costs = np.array([sum(squared[p] for p in path) for path in paths])
    assert np.isclose(_dtw(x, y)["value"] ** 2, costs.min())
    gamma = 0.7
    assert np.isclose(_soft_dtw(x, y, gamma)["value"],
                      -gamma * np.log(np.exp(-costs / gamma).sum()))

    local = _gak(x, y)["local"]
    all_path_mass = sum(np.prod([local[p] for p in path]) for path in paths)
    assert np.isclose(_gak(x, y)["value"], all_path_mass)

    absolute = np.abs(x[:, None] - y[None, :])
    bottlenecks = [max(absolute[p] for p in path) for path in paths]
    assert np.isclose(_edit("frechet", x, y)["value"], min(bottlenecks))


def test_soft_occupancy_is_the_derivative_of_the_displayed_objective():
    x, y = np.array([0.2, 1.1]), np.array([0.5, 1.8])
    trace = _soft_dtw(x, y)
    for index in range(len(x)):
        plus, minus = x.copy(), x.copy()
        step = 1e-6
        plus[index] += step
        minus[index] -= step
        numerical = (_soft_dtw(plus, y)["value"] - _soft_dtw(minus, y)["value"]) / (2 * step)
        analytic = np.sum(trace["occupancy"][index] * 2 * (x[index] - y))
        assert np.isclose(numerical, analytic, rtol=1e-6, atol=1e-6)
    assert np.allclose(trace["occupancy"][[0, -1], [0, -1]], 1)


def test_displayed_paths_and_edit_operations_agree_with_their_scores():
    for options in ({}, {"window": 1}, {"itakura": True}, {"weighted": True},
                    {"derivative": True}, {"descriptor": True}):
        trace = _dtw(_X, _Y, **options)
        path_cost = sum(trace["cost"][p] for p in trace["path"])
        assert np.isclose(path_cost, trace["value"] ** 2)
        if options.get("window"):
            assert all(abs(i - j) <= options["window"] for i, j in trace["path"])
    assert _msm([1.0], [3.0])["value"] == 2.0  # A single move.
    assert _msm([1.0, 1.0], [1.0], c=0.6)["value"] == 0.6  # One merge.
    assert _msm([1.0], [1.0, 1.0], c=0.6)["value"] == 0.6  # One split.
