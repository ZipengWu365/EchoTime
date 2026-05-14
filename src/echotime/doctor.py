"""Environment diagnostics and installation guidance for echotime."""

from __future__ import annotations

import importlib.metadata as metadata
import locale
import os
import platform
import sys
from typing import Any, Literal

from .compat import COMPATIBILITY_PROFILES

DoctorFormat = Literal["markdown", "text", "json", "dict"]
_CHECK_PACKAGES = ("numpy", "scipy", "pandas", "aeon", "sktime", "numba")


def _version_or_none(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def environment_doctor(*, format: DoctorFormat = "markdown") -> str | dict[str, Any]:
    pkg_versions = {name: _version_or_none(name) for name in _CHECK_PACKAGES}
    stdout_encoding = getattr(sys.stdout, "encoding", None) or locale.getpreferredencoding(False) or "unknown"
    preferred = locale.getpreferredencoding(False) or "unknown"
    in_venv = (getattr(sys, "base_prefix", sys.prefix) != sys.prefix) or bool(os.environ.get("VIRTUAL_ENV"))
    warnings: list[str] = []
    actions: list[str] = []
    recommended_profile = "clean-venv"
    if stdout_encoding and stdout_encoding.lower() not in {"utf-8", "utf8"}:
        warnings.append(
            f"stdout encoding is {stdout_encoding}; HTML-heavy guide output should go to a file or browser instead of the terminal."
        )
        actions.append(
            "Use `--output file.html`, `--export-pages docs`, or `echotime-demo --open-browser` instead of printing raw HTML to the terminal."
        )
    if any(pkg_versions.get(name) for name in ("aeon", "sktime", "numba")):
        warnings.append(
            "mixed scientific-stack packages are present (aeon/sktime/numba); resolver warnings are more likely in an existing environment."
        )
        actions.append(
            "Use the mixed scientific-stack constraints profile instead of a bare install."
        )
        recommended_profile = "mixed-scientific-stack"
    if not in_venv:
        warnings.append("no active virtual environment detected.")
        actions.append(
            "Create a dedicated environment for the cleanest install experience."
        )
    if not actions:
        actions.append("Your environment looks straightforward for a normal install and CLI use.")
    actions.extend([
        "Use `echotime-demo --open-browser` to evaluate the product surface without wiring echotime into an existing notebook stack.",
        "Use `echotime --export-pages docs` to generate a GitHub-Pages-ready static demo bundle.",
        f"Use `echotime --write-constraints constraints/{recommended_profile}.txt --constraint-profile {recommended_profile}` to export a concrete constraints file.",
    ])
    payload = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "stdout_encoding": stdout_encoding,
        "preferred_encoding": preferred,
        "virtual_environment": in_venv,
        "packages": pkg_versions,
        "warnings": warnings,
        "recommended_actions": actions,
        "recommended_profile": recommended_profile,
        "constraint_profiles": COMPATIBILITY_PROFILES,
        "recommended_install_commands": COMPATIBILITY_PROFILES[recommended_profile]["install_commands"],
        "summary": (
            "Environment looks clean."
            if not warnings
            else "Environment is usable, but echotime recommends safer install and HTML-output paths for this stack."
        ),
    }
    if format in {"json", "dict"}:
        return payload
    lines = [
        "# Environment doctor",
        "",
        payload["summary"],
        "",
        "## Runtime",
        "",
        f"- Python: {payload['python']}",
        f"- Platform: {payload['platform']}",
        f"- stdout encoding: {payload['stdout_encoding']}",
        f"- preferred encoding: {payload['preferred_encoding']}",
        f"- virtual environment: {'yes' if payload['virtual_environment'] else 'no'}",
        "",
        "## Package snapshot",
        "",
    ]
    for name, version in payload["packages"].items():
        lines.append(f"- {name}: {version or 'not installed'}")
    lines += ["", "## Watchouts", ""]
    if warnings:
        lines += [f"- {item}" for item in warnings]
    else:
        lines.append("- No immediate environment watchouts detected.")
    lines += ["", "## Recommended compatibility profile", ""]
    lines.append(f"- {recommended_profile}: {COMPATIBILITY_PROFILES[recommended_profile]['summary']}")
    lines += ["", "## Recommended install / export commands", ""]
    lines += [f"- {item}" for item in payload["recommended_install_commands"]]
    lines += ["", "## Recommended next steps", ""]
    lines += [f"- {item}" for item in actions]
    return "\n".join(lines)


__all__ = ["environment_doctor"]
