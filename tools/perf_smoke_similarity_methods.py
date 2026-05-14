from __future__ import annotations

import argparse
import importlib.util
import inspect
import types
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def _load_similarity_methods() -> Any:
    package = sys.modules.get("echotime")
    if package is None:
        package = types.ModuleType("echotime")
        package.__path__ = [str(SRC / "echotime")]  # type: ignore[attr-defined]
        sys.modules["echotime"] = package

    metrics_module = sys.modules.get("echotime.metrics")
    if metrics_module is None:
        metrics_module = types.ModuleType("echotime.metrics")
        metrics_module.EPS = 1e-12
        sys.modules["echotime.metrics"] = metrics_module

    spec = importlib.util.spec_from_file_location("echotime.similarity_methods", SRC / "echotime" / "similarity_methods.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load echotime.similarity_methods.")
    module = importlib.util.module_from_spec(spec)
    sys.modules["echotime.similarity_methods"] = module
    spec.loader.exec_module(module)
    return module


SIMILARITY_METHODS = _load_similarity_methods()
edr_distance = SIMILARITY_METHODS.edr_distance
erp_distance = SIMILARITY_METHODS.erp_distance
lcss_similarity = SIMILARITY_METHODS.lcss_similarity
twed_distance = SIMILARITY_METHODS.twed_distance


@dataclass(slots=True)
class BenchmarkCase:
    name: str
    func: Callable[..., Any]
    x: np.ndarray
    y: np.ndarray
    kwargs: dict[str, Any]


def _call_with_mode(func: Callable[..., Any], *args: Any, mode: str, **kwargs: Any) -> Any:
    signature = inspect.signature(func)
    if "mode" in signature.parameters:
        kwargs["mode"] = mode
    if "window" in signature.parameters and "window" not in kwargs and mode == "fast":
        n = min(len(np.asarray(args[0]).reshape(-1)), len(np.asarray(args[1]).reshape(-1)))
        kwargs["window"] = max(abs(len(np.asarray(args[0]).reshape(-1)) - len(np.asarray(args[1]).reshape(-1))), max(1, int(np.ceil(0.10 * n))))
    return func(*args, **kwargs)


def _bench(func: Callable[..., Any], *args: Any, repeat: int = 5, **kwargs: Any) -> float:
    timings: list[float] = []
    for _ in range(repeat):
        start = time.perf_counter()
        func(*args, **kwargs)
        timings.append(time.perf_counter() - start)
    return float(np.median(np.asarray(timings, dtype=float)))


def _make_series(length: int, *, phase: float = 0.0, shift: int = 0, scale: float = 1.0, noise: float = 0.02) -> np.ndarray:
    t = np.linspace(0.0, 8.0 * np.pi, length, dtype=float)
    base = scale * (np.sin(t + phase) + 0.35 * np.sin(3.0 * t + 0.2))
    rolled = np.roll(base, shift)
    return rolled + noise * np.cos(11.0 * t + 0.1)


def _make_multivariate(length: int, channels: int = 3) -> np.ndarray:
    cols = []
    for idx in range(channels):
        cols.append(_make_series(length, phase=0.2 * idx, shift=idx * 2, scale=1.0 - 0.1 * idx))
    return np.column_stack(cols)


def _make_cases() -> list[BenchmarkCase]:
    return [
        BenchmarkCase("lcss", lcss_similarity, _make_series(256, shift=7), _make_series(256, phase=0.05), {"epsilon": 0.25}),
        BenchmarkCase("edr", edr_distance, _make_series(256, shift=4), _make_series(256, phase=0.03), {"epsilon": 0.20}),
        BenchmarkCase("erp", erp_distance, _make_series(256, shift=6), _make_series(256, phase=0.04), {"gap_value": 0.0}),
        BenchmarkCase(
            "twed",
            twed_distance,
            _make_series(256, shift=5),
            _make_series(256, phase=0.02),
            {},
        ),
    ]


def _format_seconds(seconds: float) -> str:
    if seconds < 0.001:
        return f"{seconds * 1_000_000.0:8.1f} us"
    if seconds < 1.0:
        return f"{seconds * 1_000.0:8.2f} ms"
    return f"{seconds:8.3f} s"


def run(*, lengths: list[int], repeat: int) -> int:
    cases = _make_cases()
    for length in lengths:
        print(f"\n=== length={length} ===")
        for case in cases:
            x = case.x if len(case.x) == length else _make_series(length, shift=7 if case.name != "twed" else 5)
            y = case.y if len(case.y) == length else _make_series(length, phase=0.05 if case.name != "twed" else 0.02)
            kwargs = dict(case.kwargs)
            if case.name == "twed":
                kwargs["t_x"] = np.linspace(0.0, 2.0, length)
                kwargs["t_y"] = np.linspace(0.0, 2.0, length)
            exact = _bench(_call_with_mode, case.func, x, y, mode="exact", repeat=repeat, **kwargs)
            fast = _bench(_call_with_mode, case.func, x, y, mode="fast", repeat=repeat, **kwargs)
            ratio = exact / fast if fast > 0 else float("inf")
            print(f"{case.name:>8} exact={_format_seconds(exact)}  fast={_format_seconds(fast)}  speedup={ratio:5.2f}x")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke benchmark low-level elastic similarity methods.")
    parser.add_argument("--lengths", nargs="+", type=int, default=[128, 256, 512], help="Series lengths to benchmark.")
    parser.add_argument("--repeat", type=int, default=5, help="Number of runs per measurement.")
    args = parser.parse_args()
    return run(lengths=args.lengths, repeat=max(1, args.repeat))


if __name__ == "__main__":
    raise SystemExit(main())
