"""Rendering utilities for profiles and dataset cards."""

from __future__ import annotations

import json
from typing import Mapping

from .axes import AXIS_DESCRIPTIONS, AXIS_ORDER
from .schema import schema_dict


def _level(score: float) -> str:
    if score >= 0.75:
        return "very high"
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "moderate"
    if score >= 0.15:
        return "low"
    return "very low"


def _bar(score: float, width: int = 20) -> str:
    filled = int(round(score * width))
    return "█" * filled + "·" * (width - filled)


def card_dict(profile: "BaseRenderableProfile") -> dict[str, object]:
    return {
        "schema_version": getattr(profile, "schema_version", "0.6.0"),
        "package": "echotime",
        "package_version": getattr(profile, "package_version", "0.6.0"),
        "kind": profile.kind,
        "domain": str(profile.metadata.get("domain", "generic")),
        "archetypes": list(profile.archetypes),
        "metadata": dict(profile.metadata),
        "evidence": dict(profile.evidence),
        "reliability": dict(profile.reliability),
        "axes": {
            axis: {
                "score": float(profile.axes.get(axis, 0.0)),
                "level": _level(float(profile.axes.get(axis, 0.0))),
                "meaning": AXIS_DESCRIPTIONS[axis],
                "contributors": dict(profile.axis_details.get(axis, {})),
                "subdimensions": {
                    name: {
                        "score": float(value),
                        "contributors": dict(profile.subdimension_details.get(axis, {}).get(name, {})),
                    }
                    for name, value in sorted(profile.subdimensions.get(axis, {}).items())
                },
            }
            for axis in AXIS_ORDER
        },
        "task_hints": list(profile.task_hints),
        "notes": list(profile.notes),
        "plugin_metrics": dict(profile.plugin_metrics),
        "ontology_schema": schema_dict(),
    }


def format_text(profile: "BaseRenderableProfile") -> str:
    lines = [
        f"kind: {profile.kind}",
        f"domain: {profile.metadata.get('domain', 'generic')}",
        f"archetypes: {', '.join(profile.archetypes)}",
        f"reliability: {profile.reliability.get('overall_score', 0.0):0.3f} ({profile.reliability.get('overall_level', 'n/a')})",
        "axes:",
    ]
    for axis in AXIS_ORDER:
        score = profile.axes.get(axis, 0.0)
        rel = profile.reliability.get("axes", {}).get(axis, {}).get("score", 0.0)
        lines.append(f"  - {axis:26s} {score:0.3f}  {_bar(score, 16)}  rel={rel:0.2f}")
    if profile.plugin_metrics:
        lines.append("plugins:")
        for plugin_name, metrics in profile.plugin_metrics.items():
            lines.append(f"  - {plugin_name}: {len(metrics)} metrics")
    return "\n".join(lines)


def format_markdown(profile: "BaseRenderableProfile") -> str:
    lines = [
        f"# EchoTime {profile.kind} report",
        "",
        "## Structural archetypes",
        "",
        ", ".join(profile.archetypes),
        "",
        "## Metadata",
        "",
        "| field | value |",
        "|---|---:|",
    ]
    for key, value in profile.metadata.items():
        lines.append(f"| {key} | {value} |")
    lines.extend([
        "",
        "## Reliability and evidence",
        "",
        f"**overall reliability:** {profile.reliability.get('overall_score', 0.0):0.3f} ({profile.reliability.get('overall_level', 'n/a')})  ",
        f"**method:** {profile.reliability.get('method', 'n/a')}",
        "",
        "| evidence field | value |",
        "|---|---:|",
    ])
    for key, value in profile.evidence.items():
        lines.append(f"| {key} | {value} |")
    lines.extend([
        "",
        "## Ontology axes",
        "",
        "| axis | score | level | reliability | meaning |",
        "|---|---:|---|---:|---|",
    ])
    for axis in AXIS_ORDER:
        score = profile.axes.get(axis, 0.0)
        rel = profile.reliability.get("axes", {}).get(axis, {}).get("score", 0.0)
        lines.append(f"| {axis} | {score:0.3f} | {_level(score)} | {rel:0.3f} | {AXIS_DESCRIPTIONS[axis]} |")
    lines.extend([
        "",
        "## Subdimensions",
        "",
        "| axis | subdimension | score | top contributors |",
        "|---|---|---:|---|",
    ])
    for axis in AXIS_ORDER:
        for name, score in sorted(profile.subdimensions.get(axis, {}).items()):
            items = sorted(profile.subdimension_details.get(axis, {}).get(name, {}).items(), key=lambda kv: kv[1], reverse=True)
            shown = ", ".join(f"{metric}={value:0.3f}" for metric, value in items[:3]) if items else "n/a"
            lines.append(f"| {axis} | {name} | {score:0.3f} | {shown} |")
    lines.extend([
        "",
        "## Axis contributors",
        "",
        "| axis | top contributors |",
        "|---|---|",
    ])
    for axis in AXIS_ORDER:
        items = sorted(profile.axis_details.get(axis, {}).items(), key=lambda kv: kv[1], reverse=True)
        shown = ", ".join(f"{name}={value:0.3f}" for name, value in items[:4]) if items else "n/a"
        lines.append(f"| {axis} | {shown} |")
    lines.extend([
        "",
        "## Reliability by axis",
        "",
        "| axis | reliability | proxy coverage | data support | interval | caveats |",
        "|---|---:|---:|---:|---|---|",
    ])
    for axis in AXIS_ORDER:
        info = profile.reliability.get("axes", {}).get(axis, {})
        ci_low = info.get("ci_low")
        ci_high = info.get("ci_high")
        interval = "n/a" if ci_low is None or ci_high is None else f"[{ci_low:0.3f}, {ci_high:0.3f}]"
        caveats = "; ".join(info.get("caveats", [])) or ""
        lines.append(
            f"| {axis} | {info.get('score', 0.0):0.3f} | {info.get('proxy_coverage', 0.0):0.3f} | {info.get('data_support', 0.0):0.3f} | {interval} | {caveats} |"
        )
    lines.extend([
        "",
        "## Top raw proxies",
        "",
        "| metric | value |",
        "|---|---:|",
    ])
    raw_items = sorted(
        profile.metrics.items(),
        key=lambda kv: (0 if isinstance(kv[1], (int, float)) else 1, abs(float(kv[1])) if isinstance(kv[1], (int, float)) else 0),
        reverse=True,
    )
    shown = 0
    for key, value in raw_items:
        if isinstance(value, (int, float)):
            lines.append(f"| {key} | {float(value):0.4f} |")
            shown += 1
            if shown >= 20:
                break

    if profile.plugin_metrics:
        lines.extend([
            "",
            "## Plugin metrics",
            "",
            "| plugin | metric | value |",
            "|---|---|---:|",
        ])
        for plugin_name, metrics in profile.plugin_metrics.items():
            for metric_name, value in sorted(metrics.items()):
                lines.append(f"| {plugin_name} | {metric_name} | {float(value):0.4f} |")

    lines.extend([
        "",
        "## Task hints",
        "",
    ])
    for hint in profile.task_hints:
        lines.append(f"- {hint}")

    if profile.notes:
        lines.extend(["", "## Notes", ""])
        for note in profile.notes:
            lines.append(f"- {note}")
    return "\n".join(lines)


def format_card_markdown(profile: "BaseRenderableProfile") -> str:
    card = card_dict(profile)
    lines = [
        "# EchoTime dataset card",
        "",
        f"**kind:** {card['kind']}",
        f"**domain:** {card['domain']}",
        f"**archetypes:** {', '.join(card['archetypes'])}",
        f"**reliability:** {card['reliability']['overall_score']:0.3f} ({card['reliability']['overall_level']})",
        "",
        "## Axes",
        "",
        "| axis | score | level | reliability |",
        "|---|---:|---|---:|",
    ]
    for axis in AXIS_ORDER:
        axis_info = card["axes"][axis]
        reliability = card["reliability"]["axes"][axis]["score"]
        lines.append(f"| {axis} | {axis_info['score']:0.3f} | {axis_info['level']} | {reliability:0.3f} |")
    lines.extend(["", "## Task hints", ""])
    for hint in card["task_hints"]:
        lines.append(f"- {hint}")
    return "\n".join(lines)


def format_card_json(profile: "BaseRenderableProfile", *, indent: int = 2) -> str:
    return json.dumps(card_dict(profile), indent=indent)


class BaseRenderableProfile:
    kind: str
    metadata: Mapping[str, object]
    axes: Mapping[str, float]
    subdimensions: Mapping[str, Mapping[str, float]]
    axis_details: Mapping[str, Mapping[str, float]]
    subdimension_details: Mapping[str, Mapping[str, Mapping[str, float]]]
    metrics: Mapping[str, float]
    archetypes: list[str]
    task_hints: list[str]
    reliability: Mapping[str, object]
    evidence: Mapping[str, object]
    notes: list[str]
    plugin_metrics: Mapping[str, Mapping[str, float]]
    package_version: str
    schema_version: str
