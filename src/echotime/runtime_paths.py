"""Resolve repository assets when EchoTime runs from source or from an installed wheel."""

from __future__ import annotations

from pathlib import Path


def resolve_repo_subdir(*parts: str, sentinel: str | None = None) -> Path:
    """Prefer source assets, then the wheel's frozen runtime resources.

    The working-directory fallback remains available for legacy layouts, but
    installed packages do not require a repository alongside the caller.
    """
    relative = Path(*parts)
    candidates = [
        Path(__file__).resolve().parents[2] / relative,
        Path(__file__).resolve().parent / "data" / "runtime" / relative,
        Path.cwd() / relative,
    ]
    for candidate in candidates:
        if sentinel is None and candidate.exists():
            return candidate
        if sentinel is not None and (candidate / sentinel).exists():
            return candidate
    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Could not locate repository path {relative}. Searched: {searched}")
