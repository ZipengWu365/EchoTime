"""Resolve repository assets when EchoTime runs from source or from an installed wheel."""

from __future__ import annotations

from pathlib import Path


def resolve_repo_subdir(*parts: str, sentinel: str | None = None) -> Path:
    relative = Path(*parts)
    candidates = [
        Path(__file__).resolve().parents[2] / relative,
        Path.cwd() / relative,
    ]
    for candidate in candidates:
        if sentinel is None and candidate.exists():
            return candidate
        if sentinel is not None and (candidate / sentinel).exists():
            return candidate
    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Could not locate repository path {relative}. Searched: {searched}")
