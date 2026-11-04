#!/usr/bin/env python3
"""Optional CUDA readiness measurements; this is NOT an EchoTime GPU backend.

Requires a CUDA-capable PyTorch installation selected for the server's driver.
It records actual FP32/FP64 GEMM and transfer measurements to inform P4; these
numbers must never be reported as DTW or EchoTime end-to-end speedups.
"""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
import subprocess
from time import perf_counter


def inventory():
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                                capture_output=True, text=True, timeout=10, check=False)
        return {"returncode": result.returncode, "output": result.stdout.strip(), "error": result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def run(size=1024, repeats=7):
    report = {"schema_version": 1, "purpose": "hardware readiness, not EchoTime GPU acceleration",
              "platform": platform.platform(), "python": platform.python_version(),
              "nvidia_smi": inventory(), "size": size, "repeats": repeats}
    try:
        import torch
    except ImportError:
        return {**report, "status": "unavailable", "reason": "PyTorch is not installed; no GPU computation was performed"}
    report.update(torch_version=torch.__version__, cuda_runtime=torch.version.cuda,
                  cpu_threads=torch.get_num_threads(), cuda_available=torch.cuda.is_available())
    if not torch.cuda.is_available():
        return {**report, "status": "unavailable", "reason": "PyTorch has no available CUDA device; no GPU computation was performed"}
    device = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(device)
    report["device"] = {"name": props.name, "total_memory_bytes": props.total_memory,
                        "compute_capability": list(torch.cuda.get_device_capability(device)),
                        "multiprocessors": props.multi_processor_count}
    torch.backends.cuda.matmul.allow_tf32 = False
    report["allow_tf32"] = False
    generator = torch.Generator(device="cpu").manual_seed(20261104)
    left = torch.randn((size, size), generator=generator, dtype=torch.float64)
    right = torch.randn((size, size), generator=generator, dtype=torch.float64)
    reference = left @ right
    report["measurements"] = []
    for name, dtype in (("float32", torch.float32), ("float64", torch.float64)):
        host_a, host_b = left.to(dtype=dtype), right.to(dtype=dtype)
        a, b = host_a.to(device="cuda"), host_b.to(device="cuda")
        for _ in range(2):
            output = a @ b
        torch.cuda.synchronize()
        samples, end_to_end = [], []
        for _ in range(repeats):
            torch.cuda.synchronize()
            t = perf_counter()
            output = a @ b
            torch.cuda.synchronize()
            samples.append(perf_counter() - t)
        actual = output.cpu().to(dtype=torch.float64)
        error = (actual - reference).abs()
        for _ in range(repeats):
            torch.cuda.synchronize()
            t = perf_counter()
            uploaded_a, uploaded_b = host_a.to(device="cuda"), host_b.to(device="cuda")
            downloaded = (uploaded_a @ uploaded_b).cpu()
            torch.cuda.synchronize()
            end_to_end.append(perf_counter() - t)
            del uploaded_a, uploaded_b, downloaded
        samples.sort()
        end_to_end.sort()
        median = samples[len(samples) // 2]
        report["measurements"].append({"operation": "dense_gemm", "dtype": name,
            "resident_seconds": samples, "resident_median_seconds": median,
            "upload_compute_download_seconds": end_to_end,
            "end_to_end_median_seconds": end_to_end[len(end_to_end) // 2],
            "observed_gflops": 2 * size ** 3 / median / 1e9,
            "max_absolute_error_vs_cpu_fp64": float(error.max()),
            "relative_frobenius_error_vs_cpu_fp64": float(torch.linalg.vector_norm(error) / torch.linalg.vector_norm(reference)),
            "allocated_bytes": torch.cuda.memory_allocated(device)})
        del a, b, output, actual, error
    report["status"] = "measured"
    report["echotime_gpu_backend"] = "not implemented in this branch"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--size", type=int, default=1024)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--require-gpu", action="store_true")
    args = parser.parse_args(argv)
    if not 16 <= args.size <= 8192 or not 1 <= args.repeats <= 100:
        parser.error("size must be in [16, 8192] and repeats in [1, 100]")
    report = run(args.size, args.repeats)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(args.out), "purpose": report["purpose"]}))
    return 2 if args.require_gpu and report["status"] != "measured" else 0


if __name__ == "__main__":
    raise SystemExit(main())
