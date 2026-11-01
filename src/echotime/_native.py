"""Backend selection for EchoTime's compiled kernels.

The C++ extension ``echotime._echotime_native`` is optional. When it is
missing (no compiler at install time, unsupported platform) every function
falls back to the pure-Python reference, which remains the definition of the
numbers: the native kernels are tested to reproduce it bit for bit.

Selection, in order of precedence:

1. ``set_similarity_backend("python" | "native" | "auto")`` in the process;
2. the ``ECHOTIME_BACKEND`` environment variable (same values);
3. ``"auto"``: native when available, otherwise Python.

Thread count for batch APIs: an explicit ``n_jobs``; else
``ECHOTIME_NUM_THREADS``; else the CPUs this process may run on
(``os.sched_getaffinity``, which respects Slurm/cgroup allocations).
"""

from __future__ import annotations

import os
from typing import Any

try:  # pragma: no cover - depends on the build
    from . import _echotime_native as _ext

    _IMPORT_ERROR: str | None = None
except Exception as exc:  # pragma: no cover - depends on the build
    _ext = None
    _IMPORT_ERROR = f"{type(exc).__name__}: {exc}"

_VALID = ("auto", "native", "python")
_override: str | None = None


def native_available() -> bool:
    return _ext is not None


def _requested() -> str:
    if _override is not None:
        return _override
    env = os.environ.get("ECHOTIME_BACKEND", "auto").strip().lower() or "auto"
    if env not in _VALID:
        raise ValueError(f"ECHOTIME_BACKEND must be one of {_VALID}, got {env!r}.")
    return env


def set_similarity_backend(name: str | None) -> None:
    """Force ``"python"`` or ``"native"`` kernels, or restore ``"auto"`` (also ``None``)."""

    global _override
    if name is None:
        _override = None
        return
    name = str(name).strip().lower()
    if name not in _VALID:
        raise ValueError(f"backend must be one of {_VALID}.")
    if name == "native" and _ext is None:
        raise RuntimeError(f"the native extension is not available ({_IMPORT_ERROR}).")
    _override = None if name == "auto" else name


def resolve_backend(backend: str | None = None) -> str:
    """Return ``"native"`` or ``"python"`` for a call-level ``backend`` argument."""

    choice = _requested() if backend is None else str(backend).strip().lower()
    if choice not in _VALID:
        raise ValueError(f"backend must be one of {_VALID}.")
    if choice == "native":
        if _ext is None:
            raise RuntimeError(f"the native extension is not available ({_IMPORT_ERROR}).")
        return "native"
    if choice == "python":
        return "python"
    return "native" if _ext is not None else "python"


def use_native(backend: str | None = None) -> bool:
    return resolve_backend(backend) == "native"


def default_threads(n_jobs: int | None = None) -> int:
    if n_jobs is not None:
        value = int(n_jobs)
        if value == 0:
            raise ValueError("n_jobs must be a positive integer, -1, or None.")
        if value > 0:
            return value
    env = os.environ.get("ECHOTIME_NUM_THREADS")
    if env and (n_jobs is None):
        try:
            value = int(env)
            if value > 0:
                return value
        except ValueError:
            pass
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except (AttributeError, OSError):  # pragma: no cover - non-Linux
        return max(1, os.cpu_count() or 1)


def similarity_backend_info() -> dict[str, Any]:
    """Which kernels run and why (for logs and provenance)."""

    return {
        "native_available": _ext is not None,
        "native_import_error": _IMPORT_ERROR,
        "native_abi_version": None if _ext is None else int(getattr(_ext, "ABI_VERSION", 0)),
        "requested": _requested(),
        "effective": resolve_backend(None),
        "default_threads": default_threads(None),
        "env": {key: os.environ.get(key) for key in ("ECHOTIME_BACKEND", "ECHOTIME_NUM_THREADS")},
    }


def ext() -> Any:
    if _ext is None:
        raise RuntimeError(f"the native extension is not available ({_IMPORT_ERROR}).")
    return _ext


__all__ = [
    "default_threads",
    "ext",
    "native_available",
    "resolve_backend",
    "set_similarity_backend",
    "similarity_backend_info",
    "use_native",
]
