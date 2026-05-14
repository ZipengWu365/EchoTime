"""Repository asset consistency checks for echotime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from .copydeck import PACKAGE_VERSION
from .sitebundle import project_demo_manifest

ReportFormat = Literal["dict", "json", "markdown"]


def asset_consistency_report(root: str | Path | None = None, *, format: ReportFormat = "dict") -> dict[str, Any] | str:
    base = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    expected_version = PACKAGE_VERSION
    checks: list[dict[str, Any]] = []

    def add(name: str, actual: Any, expected: Any) -> None:
        checks.append({
            "name": name,
            "actual": actual,
            "expected": expected,
            "ok": actual == expected,
        })

    pyproject = (base / "pyproject.toml").read_text(encoding="utf-8", errors="ignore") if (base / "pyproject.toml").exists() else ""
    if pyproject:
        marker = 'version = "'
        actual = pyproject.split(marker, 1)[1].split('"', 1)[0] if marker in pyproject else None
        add("pyproject.version", actual, expected_version)

    manifest_path = base / "DEMO_MANIFEST.json"
    if manifest_path.exists():
        actual = json.loads(manifest_path.read_text(encoding="utf-8"))
        add("DEMO_MANIFEST.version", actual.get("version"), expected_version)

    docs_manifest_path = base / "docs" / "manifest" / "demo_manifest.json"
    if docs_manifest_path.exists():
        actual = json.loads(docs_manifest_path.read_text(encoding="utf-8"))
        add("docs/manifest/demo_manifest.json.version", actual.get("version"), expected_version)

    generated = project_demo_manifest(version=expected_version)
    add("generated_manifest.version", generated.get("version"), expected_version)

    payload = {
        "expected_version": expected_version,
        "checks": checks,
        "ok": all(item["ok"] for item in checks),
        "summary": "All checked product/demo assets agree on the package version." if all(item["ok"] for item in checks) else "At least one checked product/demo asset drifted away from the package version.",
    }
    if format == "dict":
        return payload
    if format == "json":
        return json.dumps(payload, indent=2)
    lines = ["# Asset consistency", "", payload["summary"], ""]
    for item in checks:
        status = "OK" if item["ok"] else "DRIFT"
        lines.append(f"- {status}: {item['name']} -> actual={item['actual']} expected={item['expected']}")
    return "\n".join(lines)


__all__ = ["asset_consistency_report"]
