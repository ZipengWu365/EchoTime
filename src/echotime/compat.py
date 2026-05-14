"""Compatibility presets and constraints helpers for echotime.

These helpers do not claim to solve every resolver conflict in an existing
scientific Python environment. They exist to provide a *concrete, reproducible*
installation strategy instead of only warning about potential conflicts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

GuideFormat = Literal["markdown", "text", "json", "dict"]
ConstraintProfile = Literal["clean-venv", "mixed-scientific-stack", "pages-only"]

COMPATIBILITY_PROFILES: dict[str, dict[str, Any]] = {
    "clean-venv": {
        "title": "Clean virtual environment",
        "summary": "Recommended for first-time installs, CI, and reproducible examples.",
        "packages": [
            "numpy>=1.22,<2.3",
            "scipy>=1.8,<1.16",
            "pandas>=2.0 ; extra == 'io'",
            "pyarrow>=14.0 ; extra == 'parquet'",
        ],
        "install_commands": [
            "python -m venv .venv",
            "# Windows: .venv\\Scripts\\activate",
            "# macOS/Linux: source .venv/bin/activate",
            "pip install -c constraints/clean-venv.txt echotime",
        ],
        "when": "Use when you want the cleanest installation and can isolate echotime from an existing modelling stack.",
    },
    "mixed-scientific-stack": {
        "title": "Mixed scientific stack",
        "summary": "Conservative pins for environments that already contain aeon, sktime, numba, or broader notebook tooling.",
        "packages": [
            "numpy>=1.22,<2.2",
            "scipy>=1.8,<1.15",
            "pandas>=2.0,<2.3",
            "numba>=0.58,<0.62",
            "aeon>=0.11,<1.0",
            "sktime>=0.27,<0.40",
        ],
        "install_commands": [
            "pip install -c constraints/mixed-scientific-stack.txt echotime",
            "# or create a dedicated reporting env and keep your modelling env separate",
        ],
        "when": "Use when echotime must coexist with broader time-series / scientific tooling and you want fewer resolver surprises.",
    },
    "pages-only": {
        "title": "Zero-install / Pages-only",
        "summary": "Preview the product surface without installing echotime into Python at all.",
        "packages": [],
        "install_commands": [
            "Open docs/index.html locally or publish docs/ to GitHub Pages.",
            "Run echotime-demo in a disposable environment only if you need live computation.",
        ],
        "when": "Use when you need evaluation, screenshots, or stakeholder review before installation.",
    },
}


def compatibility_constraints(profile: ConstraintProfile = "mixed-scientific-stack") -> str:
    spec = COMPATIBILITY_PROFILES[profile]
    lines = [
        "# EchoTime compatibility constraints",
        f"# profile: {profile}",
        f"# purpose: {spec['summary']}",
        "",
    ]
    lines.extend(spec["packages"])
    lines.append("")
    return "\n".join(lines)


def write_compatibility_constraints(path: str | Path, *, profile: ConstraintProfile = "mixed-scientific-stack") -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(compatibility_constraints(profile), encoding="utf-8")
    return target


def compatibility_guide(*, format: GuideFormat = "markdown") -> str | dict[str, Any]:
    payload = {
        "summary": "echotime now ships concrete compatibility presets for clean venv installs, mixed scientific stacks, and zero-install Pages evaluation.",
        "profiles": COMPATIBILITY_PROFILES,
        "recommended_default": "mixed-scientific-stack",
        "write_examples": {
            "mixed-scientific-stack": "echotime --write-constraints constraints/mixed-scientific-stack.txt --constraint-profile mixed-scientific-stack",
            "clean-venv": "echotime --write-constraints constraints/clean-venv.txt --constraint-profile clean-venv",
        },
    }
    if format in {"json", "dict"}:
        return payload
    lines = [
        "# Compatibility presets",
        "",
        payload["summary"],
        "",
        f"Recommended default: `{payload['recommended_default']}`",
        "",
    ]
    for slug, spec in COMPATIBILITY_PROFILES.items():
        lines += [
            f"## {spec['title']} (`{slug}`)",
            "",
            spec["summary"],
            "",
            f"When to use: {spec['when']}",
            "",
            "Install / export commands:",
            "",
            "```bash",
            *spec["install_commands"],
            "```",
        ]
        if spec["packages"]:
            lines += ["", "Constraints:", ""]
            lines += [f"- `{item}`" for item in spec["packages"]]
        lines += [""]
    lines += [
        "## Export constraints files",
        "",
        "```bash",
        payload["write_examples"]["mixed-scientific-stack"],
        payload["write_examples"]["clean-venv"],
        "```",
    ]
    return "\n".join(lines)


__all__ = [
    "COMPATIBILITY_PROFILES",
    "compatibility_constraints",
    "write_compatibility_constraints",
    "compatibility_guide",
]
