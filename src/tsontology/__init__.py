"""Compatibility shim for the historical ``tsontology`` package name."""

from __future__ import annotations

from importlib import import_module
import sys

from echotime import *  # noqa: F401,F403

_SUBMODULES = (
    "adapters",
    "agent",
    "agent_tools",
    "archetypes",
    "axes",
    "communication",
    "compat",
    "consistency",
    "context",
    "copydeck",
    "datasets",
    "doctor",
    "gallery",
    "guide",
    "homepage",
    "hotcases",
    "launchpad",
    "longitudinal",
    "metrics",
    "network",
    "playground",
    "plugins",
    "positioning",
    "product",
    "profile",
    "registry",
    "report",
    "repo_docs",
    "schema",
    "similarity",
    "similarity_method_atlas",
    "similarity_methods",
    "sitebundle",
    "tabular",
    "visuals",
)

for _name in _SUBMODULES:
    sys.modules[f"{__name__}.{_name}"] = import_module(f"echotime.{_name}")

__all__ = [name for name in globals() if not name.startswith("_")]
