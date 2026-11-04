#!/usr/bin/env python3
"""Reproducible acceleration benchmarks with a deliberately small default.

Run ``python benchmarks/run_suite.py --list`` before selecting expensive tasks.
The server/full profiles are opt-in and have never been implied by a smoke run.
Only standard-library modules are imported before --source-tree is applied, so
this exact harness can measure a pristine older checkout without accidentally
importing the development package installed in editable mode.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import fnmatch
import hashlib
import importlib
import importlib.util
import importlib.metadata
import inspect
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
METRICS = ("acf", "best_shift", "dtw", "edr", "erp", "independent_max_ncc",
           "independent_sbd", "lcss", "lcss_similarity", "linear_trend_model",
           "max_ncc", "ordinal_js", "periodogram", "sbd", "trend", "twed")
PROFILES = ("smoke", "quick", "server", "full")
REAL_DATASETS = ("real_python_javascript_pageviews_2024.csv", "real_btc_oil_vix_2024.csv",
                 "real_heatwave_city_temps_2024.csv")


@dataclass(frozen=True)
class Case:
    id: str
    group: str
    api: str
    n_series: int = 1
    n_points: int = 24
    channels: int = 1
    metric: str | None = None
    window: int | None = None
    step: int | None = None
    n_resample: int | None = None
    mode: str | None = None
    candidates: int | None = None
    scenario: str = "random_walk"
    dataset: str | None = None
    k: int = 10


class Unavailable(RuntimeError):
    """A genuinely absent optional API, not a failed implementation."""


def build_cases(profile: str) -> list[Case]:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile {profile!r}")
    smoke = profile == "smoke"
    large = profile in {"server", "full"}
    n, length = (8, 24) if smoke else ((10000, 256) if large else (64, 128))
    cases = [Case(f"compare/t{t}", "report", "compare", n_points=t,
                  n_resample=64 if smoke else 256) for t in ((48,) if smoke else (290, 1024))]
    cases += [Case(f"score/t{t}", "report", "score", n_points=t,
                   n_resample=64 if smoke else 256) for t in ((48,) if smoke else (290, 1024))]
    for api in ("compare_prepared", "score_prepared"):
        cases += [Case(f"{api}/t{t}", "report", api, n_points=t,
                       n_resample=64 if smoke else 256) for t in ((48,) if smoke else (290, 1024))]
    rolling_length, rolling_window = (48, 12) if smoke else (290, 60)
    for api in ("rolling", "rolling_fast"):
        cases.append(Case(f"{api}/t{rolling_length}/w{rolling_window}", "rolling", api,
                          n_points=rolling_length, window=rolling_window, step=7 if smoke else 5,
                          n_resample=32 if smoke else 128))
    profile_length, channels = (48, 3) if smoke else ((290, 400) if large else (96, 8))
    cases.append(Case(f"profile/t{profile_length}/c{channels}", "profile", "profile",
                      n_points=profile_length, channels=channels))
    for metric in METRICS:
        cases.append(Case(f"batch/{metric}/n{n}/t{length}/unrestricted", "batch", "one_vs_many",
                          n_series=n, n_points=length, metric=metric))
    for metric in ("dtw", "erp", "twed"):
        window = 4 if smoke else 16
        cases.append(Case(f"batch/{metric}/n{n}/t{length}/w{window}", "batch", "one_vs_many",
                          n_series=n, n_points=length, metric=metric, window=window))
    pn, plength = (6, 24) if smoke else ((400, 290) if large else (32, 128))
    for metric in ("dtw", "sbd", "erp"):
        window = None if metric == "sbd" else (4 if smoke else 16)
        cases.append(Case(f"pairwise/{metric}/n{pn}/t{plength}/w{window}", "pairwise", "pairwise",
                          n_series=pn, n_points=plength, metric=metric, window=window))
        if profile == "full":
            cases.append(Case(f"pairwise/{metric}/n400/t5470/w{window}", "pairwise", "pairwise",
                              n_series=400, n_points=5470, metric=metric, window=window))
    search_sizes = [32] if smoke else ([128] if not large else ([10000] if profile == "server" else [10000, 100000]))
    for search_n in search_sizes:
        for metric in ("dtw", "sbd"):
            window = (4 if smoke else 16) if metric == "dtw" else None
            for mode in ("brute", "certified", "approximate"):
                candidates = min(search_n, max(16, int(math.sqrt(search_n)) * 2)) if mode == "approximate" else None
                cases.append(Case(f"search/{metric}/{mode}/n{search_n}/t{length}/w{window}",
                                  "search", "search", n_series=search_n, n_points=length, metric=metric,
                                  window=window, mode=mode, candidates=candidates, k=min(10, search_n)))
    adverse_n = 24 if smoke else (512 if large else 64)
    for scenario in ("ties", "near_duplicates", "similar_bank"):
        cases.append(Case(f"adversarial/dtw/{scenario}/n{adverse_n}/t{length}", "adversarial", "search",
                          n_series=adverse_n, n_points=length, metric="dtw", mode="certified",
                          window=None, scenario=scenario, k=min(10, adverse_n)))
    for dataset in REAL_DATASETS[:1] if smoke else REAL_DATASETS:
        cases.append(Case("real/" + dataset.removesuffix(".csv"), "real", "real", dataset=dataset))
    return cases


def select_cases(cases: list[Case], patterns: list[str], groups: list[str]) -> list[Case]:
    return [case for case in cases
            if (not patterns or any(fnmatch.fnmatchcase(case.id, p) for p in patterns))
            and (not groups or case.group in groups)]


def _git(path: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(path), *args], text=True,
                                       stderr=subprocess.DEVNULL, timeout=5).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _rss() -> int | None:
    try:
        return int(Path("/proc/self/statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError, AttributeError):
        return None


def _peak_rss() -> int | None:
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(peak if sys.platform == "darwin" else peak * 1024)
    except (ImportError, AttributeError):
        return None


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "tolist"):
        return _jsonable(value.tolist())
    if isinstance(value, float) and not math.isfinite(value):
        return "nan" if math.isnan(value) else ("inf" if value > 0 else "-inf")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def environment(package: Any, backend_info: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import scipy

    package_path = Path(package.__file__).resolve()
    source_root = package_path.parent.parent.parent
    cpu_model = platform.processor()
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    gpu = {"execution_status": "not_implemented_in_this_suite", "devices": None,
           "note": "Device inventory is not a GPU kernel benchmark or a GPU speedup claim."}
    if shutil.which("nvidia-smi"):
        try:
            gpu["devices"] = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                text=True, stderr=subprocess.STDOUT, timeout=5).strip().splitlines()
        except (OSError, subprocess.SubprocessError) as exc:
            gpu["inventory_error"] = str(exc)
    source_hashes = {}
    for path in sorted(package_path.parent.rglob("*.py")):
        source_hashes[str(path.relative_to(package_path.parent))] = hashlib.sha256(path.read_bytes()).hexdigest()
    extension_hashes = {}
    for pattern in ("*.so", "*.pyd", "*.dylib"):
        for path in sorted(package_path.parent.glob(pattern)):
            extension_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    build_hashes = {}
    for relative in ("native/echotime_native.cpp", "setup.py", "pyproject.toml"):
        path = source_root / relative
        if path.is_file():
            build_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    optional_versions = {}
    for name in ("faiss-cpu", "torch", "cupy"):
        try:
            optional_versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            optional_versions[name] = None
    return {
        "python": platform.python_version(), "python_executable": sys.executable,
        "numpy": np.__version__, "scipy": scipy.__version__,
        "package_version": getattr(package, "__version__", None), "package_path": str(package_path),
        "source_commit": _git(source_root, "rev-parse", "HEAD"),
        "source_dirty": bool(_git(source_root, "status", "--porcelain", "--", "src/echotime", "native", "setup.py", "pyproject.toml")),
        "source_sha256": source_hashes, "extension_sha256": extension_hashes, "build_source_sha256": build_hashes,
        "optional_dependencies": optional_versions,
        "python_compiler": platform.python_compiler(),
        "observed_build_environment": {key: os.environ.get(key) for key in (
            "CC", "CXX", "CFLAGS", "CXXFLAGS", "ECHOTIME_NATIVE_MARCH")},
        "platform": platform.platform(), "machine": platform.machine(), "processor": cpu_model,
        "cpu_count": os.cpu_count(),
        "cpu_affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
        "backend": backend_info,
        "thread_environment": {key: os.environ.get(key) for key in (
            "ECHOTIME_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")},
        "gpu": gpu,
    }


def _bank(case: Case, seed: int) -> tuple[Any, Any]:
    import numpy as np

    # Same dataset for brute/certified/approximate, across profiles and revisions.
    salt = f"{case.n_series}/{case.n_points}/{case.channels}/{case.scenario}"
    salt_int = int.from_bytes(hashlib.sha256(salt.encode()).digest()[:8], "little")
    rng = np.random.default_rng(np.random.SeedSequence([seed, salt_int]))
    bank = rng.normal(size=(case.n_series, case.n_points)).cumsum(axis=1)
    query = rng.normal(size=case.n_points).cumsum()
    if case.scenario == "ties":
        bank[:] = query
        bank[case.n_series // 2:] += 1.0
    elif case.scenario in {"near_duplicates", "similar_bank"}:
        scale = 1e-8 if case.scenario == "near_duplicates" else 0.01
        bank = query[None, :] + rng.normal(scale=scale, size=bank.shape)
        bank[0] = query
    return np.ascontiguousarray(query), np.ascontiguousarray(bank)


def _order(values: Any, k: int) -> Any:
    import numpy as np

    # Finite/infinite values, then NaNs; ties use the original integer row ID.
    ids = np.arange(len(values), dtype=np.int64)
    return np.lexsort((ids, np.where(np.isnan(values), 0.0, values), np.isnan(values)))[:k]


def _search_parts(result: Any) -> tuple[Any, Any, dict[str, Any]]:
    if isinstance(result, dict):
        return result["ids"], result["values"], result.get("stats", {})
    return result.ids, result.values, getattr(result, "stats", {})


def prepare_case(case: Case, args: argparse.Namespace) -> tuple[Callable[[], Any], dict[str, Any], Callable[[Any], dict[str, Any]] | None]:
    import numpy as np
    from echotime.batch import one_vs_many, pairwise_distance_matrix
    from echotime.profile import profile_dataset
    from echotime.similarity import compare_series, rolling_similarity

    stages: dict[str, Any] = {}
    start = time.perf_counter()
    query, bank = _bank(case, args.seed)
    if case.api == "profile":
        rng = np.random.default_rng(args.seed)
        profile_data = rng.normal(size=(case.n_points, case.channels)).cumsum(axis=0)
    stages["data_generation_seconds"] = time.perf_counter() - start
    params = {"window": case.window} if case.window is not None else {}
    batch_kwargs = dict(metric=case.metric, layout="rows", backend=args.backend, n_jobs=args.n_jobs, **params)
    if case.api == "one_vs_many":
        return lambda: one_vs_many(query, bank, **batch_kwargs), stages, None
    if case.api == "pairwise":
        return lambda: pairwise_distance_matrix(bank, **batch_kwargs), stages, None
    if case.api in {"compare", "score", "compare_prepared", "score_prepared"}:
        compare_kwargs = {"n_points": case.n_resample}
        if case.api.startswith("score"):
            if "output" not in inspect.signature(compare_series).parameters:
                raise Unavailable("compare_series(output='score') is unavailable in this revision")
            compare_kwargs["output"] = "score"
        left, right = query, bank[0]
        if case.api.endswith("_prepared"):
            if importlib.util.find_spec("echotime.prepared") is None:
                raise Unavailable("echotime.prepared.PreparedSeries is unavailable in this revision")
            prepared_module = importlib.import_module("echotime.prepared")
            if not hasattr(prepared_module, "PreparedSeries"):
                raise Unavailable("echotime.prepared.PreparedSeries is unavailable in this revision")
            start = time.perf_counter()
            left = prepared_module.PreparedSeries(left, n_points=case.n_resample)
            right = prepared_module.PreparedSeries(right, n_points=case.n_resample)
            stages["series_prepare_seconds"] = time.perf_counter() - start
        return lambda: compare_series(left, right, **compare_kwargs), stages, None
    if case.api in {"rolling", "rolling_fast"}:
        fn = rolling_similarity
        rolling_kwargs = {"window": case.window, "n_points": case.n_resample}
        if case.api == "rolling_fast":
            if "mode" not in inspect.signature(rolling_similarity).parameters:
                raise Unavailable("rolling_similarity(mode='fast') is unavailable in this revision")
            rolling_kwargs["mode"] = "fast"
        return lambda: fn(query, bank[0], step=case.step, **rolling_kwargs), stages, None
    if case.api == "profile":
        return lambda: profile_dataset(profile_data, bootstrap=0, random_state=args.seed), stages, None
    if case.api == "real":
        import csv

        path = args.data_dir / case.dataset
        if not path.is_file():
            raise Unavailable(f"Bundled CSV was not found: {path}")
        start = time.perf_counter()
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fields = list(reader.fieldnames or [])
        columns = []
        for field in fields:
            if field.lower() in {"date", "timestamp", "time", "day", "week"}:
                continue
            values = []
            for row in rows:
                try:
                    values.append(float(row[field]) if row[field] else float("nan"))
                except (ValueError, TypeError):
                    values.append(float("nan"))
            arr = np.asarray(values, dtype=float)
            if np.isfinite(arr).sum() >= 4:
                columns.append((field, arr))
        if len(columns) < 2:
            raise ValueError(f"{path.name} does not contain two usable numeric columns")
        stages.update(data_loading_seconds=time.perf_counter() - start,
                      dataset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      selected_columns=[columns[0][0], columns[1][0]], dataset_rows=len(rows))
        return lambda: compare_series(columns[0][1], columns[1][1]), stages, None
    if case.api != "search":
        raise ValueError(f"Unsupported benchmark API {case.api}")

    def brute() -> dict[str, Any]:
        values = one_vs_many(query, bank, **batch_kwargs)
        ids = _order(values, case.k)
        return {"ids": ids, "values": values[ids], "stats": {"exact_evaluations": len(bank), "coverage_complete": True}}

    if case.mode == "brute":
        return brute, stages, None
    if importlib.util.find_spec("echotime.search") is None:
        raise Unavailable("echotime.search is unavailable in this revision")
    search_module = importlib.import_module("echotime.search")
    if not hasattr(search_module, "SearchIndex"):
        raise Unavailable("echotime.search.SearchIndex is unavailable in this revision")
    if case.mode == "approximate" and args.strategy in {"faiss", "faiss_hnsw"} and importlib.util.find_spec("faiss") is None:
        raise Unavailable("The explicitly selected faiss strategy requires the optional faiss-cpu package")
    start = time.perf_counter()
    index = search_module.SearchIndex.build(bank, target=case.metric, layout="rows",
                                          backend=args.backend, n_jobs=args.n_jobs, **params)
    stages["index_build_seconds"] = time.perf_counter() - start
    start = time.perf_counter()
    reference_values = one_vs_many(query, bank, **batch_kwargs)
    reference_ids = _order(reference_values, case.k)
    stages["validation_reference_seconds"] = time.perf_counter() - start
    # Validation deliberately stays outside the timed search; it is still
    # accounted for in end-to-end benchmark wall time and in the JSON above.
    search_kwargs = dict(k=case.k, mode=case.mode, bounds=args.bounds)
    if case.mode == "approximate":
        search_kwargs.update(candidates=case.candidates, strategy=args.strategy)

    def validate(result: Any) -> dict[str, Any]:
        ids, values, stats = _search_parts(result)
        ids, values = np.asarray(ids, dtype=int), np.asarray(values)
        if len(ids) != len(set(ids.tolist())) or len(ids) != min(case.k, len(bank)):
            raise AssertionError("Search returned duplicate IDs or the wrong result count")
        if (ids < 0).any() or (ids >= len(bank)).any():
            raise AssertionError("Search returned an out-of-range candidate ID")
        exact_values = np.array_equal(values, reference_values[ids], equal_nan=True)
        if not exact_values:
            raise AssertionError("Search result values differ from original batch metric values")
        exact_ids = bool(np.array_equal(ids, reference_ids))
        if case.mode == "certified" and not exact_ids:
            raise AssertionError("Certified search disagrees with stable brute-force top-k")
        recall = len(set(ids.tolist()) & set(reference_ids.tolist())) / len(reference_ids)
        return {"reference": "one_vs_many + (isnan, value, row_id) ordering", "exact_values": exact_values,
                "exact_ids": exact_ids, "recall_at_k": recall, "k": case.k,
                "candidate_recall_at_k": stats.get("candidate_recall_at_k"),
                "reference_ids": reference_ids.tolist(), "returned_ids": ids.tolist()}

    return lambda: index.search(query, **search_kwargs), stages, validate


def result_summary(result: Any) -> dict[str, Any]:
    import numpy as np

    if hasattr(result, "ids") or (isinstance(result, dict) and "ids" in result):
        ids, values, stats = _search_parts(result)
        return {"ids": _jsonable(ids), "values": _jsonable(values), "stats": _jsonable(stats)}
    if hasattr(result, "to_dict"):
        result = result.to_dict()
    if isinstance(result, np.ndarray):
        finite = result[np.isfinite(result)]
        return {"shape": list(result.shape), "dtype": str(result.dtype),
                "finite_count": int(len(finite)), "nan_count": int(np.isnan(result).sum()),
                "minimum": float(finite.min()) if len(finite) else None,
                "maximum": float(finite.max()) if len(finite) else None,
                "sha256": hashlib.sha256(np.ascontiguousarray(result).tobytes()).hexdigest()}
    serialized = json.dumps(_jsonable(result), sort_keys=True, separators=(",", ":"), allow_nan=False)
    summary = {"type": type(result).__name__, "sha256": hashlib.sha256(serialized.encode()).hexdigest()}
    if isinstance(result, list):
        summary["rows"] = len(result)
    if isinstance(result, dict) and "similarity_score" in result:
        summary["similarity_score"] = _jsonable(result["similarity_score"])
    if isinstance(result, (float, int)):
        summary["value"] = _jsonable(result)
    return summary


def run_case(case: Case, args: argparse.Namespace) -> dict[str, Any]:
    import numpy as np

    record: dict[str, Any] = {"id": case.id, "configuration": asdict(case), "status": "running"}
    record["rss_before_bytes"] = _rss()
    begin = time.perf_counter()
    try:
        fn, stages, validate = prepare_case(case, args)
        record["preparation"] = stages
        start = time.perf_counter()
        result = fn()
        first_seconds = time.perf_counter() - start
        if validate:
            validate(result)
        for _ in range(args.warmups):
            fn()
        samples = []
        for _ in range(args.repeats):
            start = time.perf_counter()
            result = fn()
            samples.append(time.perf_counter() - start)
        if validate:
            record["quality"] = validate(result)
        median = float(np.median(samples))
        units = case.n_series if case.api in {"one_vs_many", "search"} else (
            case.n_series * (case.n_series + 1) // 2 if case.api == "pairwise" else (
                len(result) if case.api in {"rolling", "rolling_fast"} else 1))
        unit_name = {"one_vs_many": "evaluated_candidate_series", "search": "database_candidate_series",
                     "pairwise": "upper_triangle_pairs_including_diagonal", "rolling": "windows",
                     "rolling_fast": "windows"}.get(case.api, "api_calls")
        record.update(status="ok", first_call_seconds=first_seconds, warmup_calls=args.warmups,
                      warm_samples_seconds=samples,
                      timing={"p50_seconds": median, "p95_seconds": float(np.percentile(samples, 95)),
                              "p99_seconds": float(np.percentile(samples, 99)), "minimum_seconds": min(samples),
                              "work_units_per_second": units / median if median else None,
                              "work_units": unit_name},
                      result=result_summary(result))
    except Unavailable as exc:
        record.update(status="unavailable", reason=str(exc))
    except Exception as exc:
        record.update(status="error", error_type=type(exc).__name__, error=str(exc))
    record.update(total_benchmark_seconds=time.perf_counter() - begin,
                  rss_after_bytes=_rss(), process_peak_rss_bytes=_peak_rss())
    return record


def compare_baseline(result: dict[str, Any], baseline: dict[str, Any]) -> None:
    by_id = {case["id"]: case for case in baseline.get("cases", [])}
    same_settings = all(result["run"].get(key) == baseline.get("run", {}).get(key)
                        for key in ("seed", "backend", "n_jobs", "strategy", "bounds"))
    same_environment = all(result["environment"].get(key) == baseline.get("environment", {}).get(key)
                           for key in ("machine", "processor", "cpu_affinity", "python", "numpy", "scipy", "thread_environment"))
    same_backend = (result["environment"]["backend"].get("effective") ==
                    baseline.get("environment", {}).get("backend", {}).get("effective"))
    for case in result["cases"]:
        old = by_id.get(case["id"])
        if not old or old.get("status") != "ok" or case["status"] != "ok":
            continue
        same_dataset = (case.get("preparation", {}).get("dataset_sha256") ==
                        old.get("preparation", {}).get("dataset_sha256"))
        if case["configuration"] != old.get("configuration") or not same_settings or not same_environment or not same_backend or not same_dataset:
            case["baseline_comparison"] = {"compatible": False, "reason": "Configuration, seed, backend, threads, strategy, numerical libraries, or CPU environment differ"}
            continue
        old_seconds, new_seconds = old["timing"]["p50_seconds"], case["timing"]["p50_seconds"]
        case["baseline_comparison"] = {"compatible": True, "baseline_p50_seconds": old_seconds,
                                       "p50_speedup": old_seconds / new_seconds if new_seconds else None}
    result["baseline"] = {"source_commit": baseline.get("environment", {}).get("source_commit"),
                          "created_utc": baseline.get("created_utc"),
                          "note": "Speedups require matched settings; CPU model/load, compiler and thermal state still need human review."}


def markdown(result: dict[str, Any]) -> str:
    run = result["run"]
    env = result["environment"]
    lines = ["# EchoTime acceleration benchmark", "",
             f"Profile: **{run['profile']}**. Commit: `{env['source_commit']}`. Backend: `{run['backend']}`. Threads: `{run['n_jobs']}`.", "",
             f"Measured package: `{env['package_path']}`.", "",
             "Warm percentiles describe repeated calls on the same data in one process. Small repeat counts do not estimate production tail latency.", "",
             "First call excludes Python import, input generation and index construction; these costs are reported separately in JSON. Brute-force recall checks are outside timed search calls.", "",
             "Process peak RSS is a cumulative process high-water mark, not an isolated per-case peak. GPU inventory does not imply GPU execution.", "",
             "| Case | Status | First (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Recall@k | Speedup vs baseline |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for case in result["cases"]:
        if case["status"] == "ok":
            timing = case["timing"]
            speedup = case.get("baseline_comparison", {}).get("p50_speedup")
            recall = case.get("quality", {}).get("recall_at_k")
            lines.append(f"| `{case['id']}` | ok | {case['first_call_seconds'] * 1000:.3f} | "
                         f"{timing['p50_seconds'] * 1000:.3f} | {timing['p95_seconds'] * 1000:.3f} | "
                         f"{timing['p99_seconds'] * 1000:.3f} | {recall if recall is not None else '—'} | "
                         f"{f'{speedup:.3f}×' if speedup is not None else '—'} |")
        else:
            lines.append(f"| `{case['id']}` | {case['status']} | — | — | — | — | — | — |")
    issues = [case for case in result["cases"] if case["status"] != "ok"]
    if issues:
        lines.extend(["", "## Unavailable or failed cases", ""])
        for case in issues:
            reason = case.get("reason", case.get("error", "unknown"))
            lines.append(f"- `{case['id']}`: {reason}")
    lines.extend(["", "## Interpretation limits", "",
                  "- A local smoke run validates instrumentation and small inputs; it does not establish a server throughput target.",
                  "- An absent optional API is recorded as unavailable. An implemented API throwing an unexpected exception is an error and produces a nonzero exit status.",
                  "- Exact search is checked against original batch metric values and deterministic row-ID tie order. Approximate search reports observed Recall@k on this fixed query, not a population guarantee.",
                  "- CandidateRecall@k remains null unless the search API explicitly supplies it; returned-result Recall@k is independently measured.",
                  "- Array checksums help identify a run; they are not a cross-platform floating-point equivalence test. Use the golden and native-equivalence tests for that purpose.", ""])
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--profile", choices=PROFILES, default="smoke")
    result.add_argument("--case", action="append", default=[], help="Case-ID glob; may be repeated")
    result.add_argument("--group", action="append", default=[], choices=("report", "rolling", "profile", "batch", "pairwise", "search", "adversarial", "real"))
    result.add_argument("--list", action="store_true", help="List cases without loading EchoTime or allocating input arrays")
    result.add_argument("--backend", choices=("auto", "python", "native"), default="auto")
    result.add_argument("--n-jobs", type=int, default=1, help="Explicit native worker count (default: 1)")
    result.add_argument("--repeats", type=int, default=3, help="Warm measured calls per case; not a tail-latency sample by default")
    result.add_argument("--warmups", type=int, default=1)
    result.add_argument("--seed", type=int, default=20261104)
    result.add_argument("--strategy", choices=("multiview", "pyramid", "binary", "faiss", "faiss_hnsw"), default="multiview")
    result.add_argument("--candidates", type=int, help="Override approximate candidate budgets (capped at collection size)")
    result.add_argument("--bounds", choices=("none", "cheap", "auto", "all"), default="auto")
    result.add_argument("--source-tree", type=Path, help="Explicit package source directory, normally CHECKOUT/src")
    result.add_argument("--data-dir", type=Path, default=ROOT / "examples/data")
    result.add_argument("--out", type=Path, help="JSON destination; defaults to benchmark-results/acceleration-PROFILE.json")
    result.add_argument("--baseline", type=Path, help="Existing JSON result to compare matching cases")
    result.add_argument("--allow-slow-python", action="store_true", help="Explicitly permit server/full profiles without a native backend")
    return result


def _write_json(path: Path, output: dict[str, Any]) -> None:
    """Replace complete checkpoints atomically, leaving the previous one intact on interruption."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(_jsonable(output), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    cli = parser()
    args = cli.parse_args(argv)
    if args.out is None:
        args.out = ROOT / f"benchmark-results/acceleration-{args.profile}.json"
    if args.repeats < 1 or args.warmups < 0 or args.n_jobs < 1:
        cli.error("repeats and n-jobs must be >= 1; warmups must be >= 0")
    cases = select_cases(build_cases(args.profile), args.case, args.group)
    if not cases:
        cli.error("No cases match the requested profile and filters")
    if args.candidates is not None:
        if args.candidates < 1:
            cli.error("--candidates must be positive")
        if any(case.mode == "approximate" and args.candidates < min(case.k, case.n_series) for case in cases):
            cli.error("--candidates must be at least k for each selected approximate search")
        cases = [replace(case, candidates=min(args.candidates, case.n_series)) if case.mode == "approximate" else case
                 for case in cases]
    if args.list:
        for case in cases:
            print(case.id)
        return 0
    baseline = None
    if args.baseline:
        if args.baseline.resolve() == args.out.resolve():
            cli.error("--out must differ from --baseline; the reference result must not be overwritten")
        try:
            baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            cli.error(f"Cannot read baseline JSON: {exc}")
        if not isinstance(baseline, dict) or baseline.get("schema_version") != SCHEMA_VERSION or not isinstance(baseline.get("cases"), list):
            cli.error("--baseline must be a result JSON from this suite's schema version")
    if args.source_tree:
        source = args.source_tree.resolve()
        if not (source / "echotime/__init__.py").is_file():
            cli.error("--source-tree must contain echotime/__init__.py")
        sys.path.insert(0, str(source))
    start = time.perf_counter()
    import echotime
    from echotime import _native

    import_seconds = time.perf_counter() - start
    if args.backend == "native" and not _native.native_available():
        cli.error("The native backend was requested but is unavailable; build the extension first")
    # High-level public APIs do not all expose n_jobs; their default must agree
    # with explicitly threaded batch/search tasks in the same measurement.
    os.environ["ECHOTIME_NUM_THREADS"] = str(args.n_jobs)
    _native.set_similarity_backend(args.backend)
    backend_info = _native.similarity_backend_info()
    if args.profile in {"server", "full"} and backend_info["effective"] != "native" and not args.allow_slow_python:
        cli.error("Large Python-reference workloads require --allow-slow-python; use --profile smoke or build native")
    output = {
        "schema_version": SCHEMA_VERSION, "created_utc": datetime.now(timezone.utc).isoformat(),
        "run": {"profile": args.profile, "backend": args.backend, "n_jobs": args.n_jobs,
                "seed": args.seed, "repeats": args.repeats, "warmups": args.warmups,
                "strategy": args.strategy, "bounds": args.bounds, "filters": {"cases": args.case, "groups": args.group},
                "import_seconds": import_seconds, "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "argv": sys.argv[1:] if argv is None else argv},
        "environment": environment(echotime, backend_info), "cases": [],
    }
    begin = time.perf_counter()
    for number, case in enumerate(cases, start=1):
        print(f"[{number}/{len(cases)}] {case.id}", flush=True)
        record = run_case(case, args)
        output["cases"].append(record)
        if record["status"] != "ok":
            print(f"  {record['status']}: {record.get('reason', record.get('error'))}", flush=True)
        # Each finished case is checkpointed so interrupted server runs retain evidence.
        _write_json(args.out, output)
    output["run"]["total_seconds"] = time.perf_counter() - begin
    if baseline is not None:
        compare_baseline(output, baseline)
    output["summary"] = {status: sum(case["status"] == status for case in output["cases"])
                         for status in ("ok", "unavailable", "error")}
    _write_json(args.out, output)
    args.out.with_suffix(".md").write_text(markdown(output), encoding="utf-8")
    print(f"Saved {args.out} and {args.out.with_suffix('.md')}")
    print(json.dumps(output["summary"], sort_keys=True))
    return 1 if output["summary"]["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
