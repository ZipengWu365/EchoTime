"""Plain-language summary cards and narrative reports for non-method users."""

from __future__ import annotations

import json
from typing import Mapping, Any

from .axes import AXIS_ORDER
from .schema import AXIS_DESCRIPTIONS

_AXIS_LABELS = {
    "sampling_irregularity": "observation irregularity",
    "noise_contamination": "noise contamination",
    "predictability": "predictability",
    "drift_nonstationarity": "drift and nonstationarity",
    "trendness": "trend strength",
    "rhythmicity": "rhythmicity",
    "complexity": "complexity",
    "nonlinearity_chaoticity": "nonlinearity",
    "eventness_burstiness": "eventness and burstiness",
    "regime_switching": "regime switching",
    "coupling_networkedness": "coupling and network structure",
    "heterogeneity": "heterogeneity",
}

_AXIS_WHAT_IT_MEANS = {
    "sampling_irregularity": "measurements do not arrive on a clean, even grid, so timing and missingness matter",
    "noise_contamination": "a noticeable share of the variation looks rough, noisy, or artifact-like",
    "predictability": "recent history carries usable information about what comes next",
    "drift_nonstationarity": "the data-generating behavior changes over time rather than staying stable",
    "trendness": "there is meaningful slow movement or baseline shift rather than pure fluctuation",
    "rhythmicity": "the data contain repeating or oscillatory patterns that may support seasonal or frequency-aware analysis",
    "complexity": "the signal contains rich local variation rather than one simple repeating template",
    "nonlinearity_chaoticity": "linear summaries alone probably miss important parts of the dynamics",
    "eventness_burstiness": "rare bursts or event-like excursions dominate the behavior more than smooth continuous change",
    "regime_switching": "the system appears to move between distinct states or operating modes",
    "coupling_networkedness": "channels or regions move together in a structured multivariate way",
    "heterogeneity": "subjects, units, or channels differ enough that one average pattern may be misleading",
}

_AXIS_ACTIONS = {
    "sampling_irregularity": "Keep explicit timestamps and avoid blindly forcing the data onto a regular grid too early.",
    "noise_contamination": "Treat denoising, QC, or robust preprocessing as first-class steps rather than afterthoughts.",
    "predictability": "Simple baselines and short-horizon forecasting are worth trying before more complex models.",
    "drift_nonstationarity": "Prefer time-aware validation and inspect whether earlier and later windows behave differently.",
    "trendness": "Include detrending or low-frequency structure checks in the workflow and compare trend-aware baselines.",
    "rhythmicity": "Try frequency-aware, seasonal, or cycle-aware summaries before assuming the data are memoryless.",
    "complexity": "Expect single-number summaries to miss part of the structure; representation learning may help.",
    "nonlinearity_chaoticity": "Do not rely only on linear correlations or AR-style summaries if the task stakes are high.",
    "eventness_burstiness": "Add event-centered summaries because averages can hide the bursts that actually matter.",
    "regime_switching": "Look for state segmentation, change-point analysis, or validation by operating phase.",
    "coupling_networkedness": "Use multivariate or network-aware models instead of treating each channel as independent.",
    "heterogeneity": "Report subgroup or subject-level variation and choose validation splits that respect those differences.",
}

_RISK_AXES = {"sampling_irregularity", "noise_contamination", "drift_nonstationarity", "eventness_burstiness", "regime_switching", "heterogeneity"}
_OPPORTUNITY_AXES = {"predictability", "rhythmicity", "trendness", "coupling_networkedness"}


def _level(score: float) -> str:
    score = float(score)
    if score >= 0.75:
        return "very high"
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "moderate"
    if score >= 0.15:
        return "low"
    return "very low"


def _top_axes(axes: Mapping[str, float], n: int = 3) -> list[tuple[str, float]]:
    return sorted(((axis, float(score)) for axis, score in axes.items()), key=lambda kv: kv[1], reverse=True)[:n]


def _top_filtered_axes(axes: Mapping[str, float], candidates: set[str], n: int = 3) -> list[tuple[str, float]]:
    subset = [(axis, float(axes.get(axis, 0.0))) for axis in candidates]
    subset.sort(key=lambda kv: kv[1], reverse=True)
    return subset[:n]


def _salient_axes(axes: Mapping[str, float], *, n: int = 3, threshold: float = 0.2) -> list[tuple[str, float]]:
    ranked = _top_axes(axes, n=len(axes))
    chosen = [(axis, score) for axis, score in ranked if score >= threshold][:n]
    if chosen:
        return chosen
    return ranked[: max(1, min(n, len(ranked)))]


def _domain_sentence(profile: Any) -> str:
    domain = str(profile.metadata.get("domain", "generic")).lower()
    obs = str(profile.metadata.get("observation_mode", "dense"))
    n_subjects = int(profile.metadata.get("n_subjects", 1) or 1)
    n_channels = int(profile.metadata.get("n_channels_median", 1) or 1)
    if domain == "fmri":
        return f"This looks like a multiregion brain-imaging dataset with about {n_subjects} subject(s) and roughly {n_channels} ROI/channel(s) per subject."
    if domain == "eeg":
        return f"This looks like a multichannel electrophysiology dataset with about {n_subjects} subject(s) and roughly {n_channels} channel(s) per recording."
    if domain == "clinical":
        if obs == "event_stream":
            return f"This looks like a clinical event log or intervention stream spanning about {n_subjects} subject(s)."
        return f"This looks like a clinical monitoring dataset spanning about {n_subjects} subject(s) with roughly {n_channels} signal channel(s) per subject."
    if domain == "wearable":
        return f"This looks like a wearable or digital biomarker cohort with about {n_subjects} participant(s) and roughly {n_channels} signal channel(s) per participant."
    if obs == "event_stream":
        return f"This looks like a sparse event stream with about {n_subjects} subject/group(s) represented."
    if "traffic" in domain or "product" in domain or "web" in domain:
        return f"This looks like a product, app, or web-traffic time-series dataset with about {n_subjects} group(s) and roughly {n_channels} metric channel(s)."
    if "energy" in domain:
        return f"This looks like an energy or operations time-series dataset with about {n_subjects} unit(s) and roughly {n_channels} channel(s)."
    return f"This looks like a time-series dataset with about {n_subjects} subject/unit(s) and roughly {n_channels} channel(s) per unit."


def _plain_axis_phrase(axis: str, score: float) -> str:
    label = _AXIS_LABELS.get(axis, axis.replace('_', ' '))
    return f"{label} is {_level(score)}"


def _make_executive_summary(profile: Any) -> str:
    top = _salient_axes(profile.axes, n=3, threshold=0.2)
    phrases = [_plain_axis_phrase(axis, score) for axis, score in top]
    reliability = profile.reliability.get("overall_level", "unknown")
    if len(phrases) == 1:
        middle = f" The clearest structural signal is that {phrases[0]}; most other axes are comparatively weak or task-specific."
    elif len(phrases) == 2:
        middle = f" In plain language, the strongest signals in its structure are that {phrases[0]} and {phrases[1]}."
    else:
        middle = " In plain language, the strongest signals in its structure are that " + ", ".join(phrases[:-1] + ["and " + phrases[-1]]) + "."
    return _domain_sentence(profile) + middle + f" Overall evidence quality for this profile is {reliability}."


def _takeaways(profile: Any) -> list[str]:
    top = _salient_axes(profile.axes, n=3, threshold=0.2)
    out = []
    for axis, score in top:
        out.append(f"{_AXIS_LABELS.get(axis, axis)}: {_AXIS_WHAT_IT_MEANS.get(axis, AXIS_DESCRIPTIONS.get(axis, ''))}.")
    return out


def _watchouts(profile: Any) -> list[str]:
    out = []
    for axis, score in _top_filtered_axes(profile.axes, _RISK_AXES, n=3):
        if score >= 0.2:
            out.append(f"Watch { _AXIS_LABELS.get(axis, axis) }: {_AXIS_WHAT_IT_MEANS.get(axis, '') }.")
    if not out:
        out.append("No single structural risk axis dominates strongly; basic baseline checks are still recommended.")
    return out


def _opportunities(profile: Any) -> list[str]:
    out = []
    for axis, score in _top_filtered_axes(profile.axes, _OPPORTUNITY_AXES, n=3):
        if score >= 0.2:
            out.append(f"Opportunity in { _AXIS_LABELS.get(axis, axis) }: {_AXIS_WHAT_IT_MEANS.get(axis, '') }.")
    if not out:
        out.append("The structure does not point to one easy modelling shortcut; exploratory baseline comparisons are important.")
    return out


def _next_actions(profile: Any) -> list[str]:
    actions: list[str] = []
    for axis, score in _top_axes(profile.axes, n=4):
        action = _AXIS_ACTIONS.get(axis)
        if action and action not in actions:
            actions.append(action)
    for hint in getattr(profile, 'task_hints', [])[:3]:
        if hint not in actions:
            actions.append(hint)
    return actions[:6]


def summary_card_dict(profile: Any, *, audience: str = "general") -> dict[str, Any]:
    top_axes = [
        {
            "axis": axis,
            "plain_label": _AXIS_LABELS.get(axis, axis),
            "score": float(score),
            "level": _level(score),
            "meaning": _AXIS_WHAT_IT_MEANS.get(axis, AXIS_DESCRIPTIONS.get(axis, "")),
        }
        for axis, score in _salient_axes(profile.axes, n=4, threshold=0.15)
    ]
    concern_axes = [
        {
            "axis": axis,
            "plain_label": _AXIS_LABELS.get(axis, axis),
            "score": float(score),
            "level": _level(score),
            "meaning": _AXIS_WHAT_IT_MEANS.get(axis, AXIS_DESCRIPTIONS.get(axis, "")),
        }
        for axis, score in _top_filtered_axes(profile.axes, _RISK_AXES, n=4)
    ]
    return {
        "package": "echotime",
        "package_version": getattr(profile, "package_version", "unknown"),
        "schema_version": getattr(profile, "schema_version", "unknown"),
        "audience": audience,
        "kind": getattr(profile, "kind", "dataset"),
        "domain": str(profile.metadata.get("domain", "generic")),
        "observation_mode": str(profile.metadata.get("observation_mode", "dense")),
        "executive_summary": _make_executive_summary(profile),
        "dataset_facts": {
            "n_subjects": int(profile.metadata.get("n_subjects", 1) or 1),
            "n_channels_median": int(profile.metadata.get("n_channels_median", 1) or 1),
            "length_median": int(profile.metadata.get("length_median", profile.metadata.get("length", 0)) or 0),
            "dominant_axes": str(profile.metadata.get("dominant_axes", "")),
            "reliability": {
                "score": float(profile.reliability.get("overall_score", 0.0)),
                "level": str(profile.reliability.get("overall_level", "unknown")),
            },
        },
        "top_structure_axes": top_axes,
        "main_takeaways": _takeaways(profile),
        "main_watchouts": _watchouts(profile),
        "analysis_opportunities": _opportunities(profile),
        "recommended_next_actions": _next_actions(profile),
        "archetypes": list(getattr(profile, "archetypes", [])),
        "task_hints": list(getattr(profile, "task_hints", [])),
        "notes": list(getattr(profile, "notes", [])),
    }


def format_summary_card_json(profile: Any, *, audience: str = "general", indent: int = 2) -> str:
    return json.dumps(summary_card_dict(profile, audience=audience), indent=indent)


def format_summary_card_markdown(profile: Any, *, audience: str = "general") -> str:
    card = summary_card_dict(profile, audience=audience)
    lines = [
        "# EchoTime summary card",
        "",
        f"**audience:** {card['audience']}  ",
        f"**domain:** {card['domain']}  ",
        f"**observation mode:** {card['observation_mode']}  ",
        f"**overall reliability:** {card['dataset_facts']['reliability']['score']:.3f} ({card['dataset_facts']['reliability']['level']})",
        "",
        "## Executive summary",
        "",
        card["executive_summary"],
        "",
        "## Dataset facts",
        "",
        "| field | value |",
        "|---|---:|",
    ]
    for key, value in card["dataset_facts"].items():
        if isinstance(value, dict):
            lines.append(f"| {key} | {value['score']:.3f} ({value['level']}) |")
        else:
            lines.append(f"| {key} | {value} |")
    lines.extend([
        "",
        "## Top structure axes",
        "",
        "| axis | plain-language label | score | level | what it usually means |",
        "|---|---|---:|---|---|",
    ])
    for item in card["top_structure_axes"]:
        lines.append(f"| {item['axis']} | {item['plain_label']} | {item['score']:.3f} | {item['level']} | {item['meaning']} |")
    lines.extend(["", "## Main takeaways", ""])
    for item in card["main_takeaways"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Main watchouts", ""])
    for item in card["main_watchouts"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Analysis opportunities", ""])
    for item in card["analysis_opportunities"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended next actions", ""])
    for idx, item in enumerate(card["recommended_next_actions"], start=1):
        lines.append(f"{idx}. {item}")
    if card["archetypes"]:
        lines.extend(["", "## Structural archetypes", "", ", ".join(card["archetypes"])])
    if card["notes"]:
        lines.extend(["", "## Interpretation notes", ""])
        for note in card["notes"]:
            lines.append(f"- {note}")
    return "\n".join(lines)


def format_narrative_report(profile: Any, *, audience: str = "general") -> str:
    top = _salient_axes(profile.axes, n=4, threshold=0.15)
    top_risks = _top_filtered_axes(profile.axes, _RISK_AXES, n=3)
    top_ops = _top_filtered_axes(profile.axes, _OPPORTUNITY_AXES, n=3)
    lines = [
        "# EchoTime narrative report",
        "",
        f"**audience:** {audience}  ",
        f"**domain:** {profile.metadata.get('domain', 'generic')}  ",
        f"**kind:** {getattr(profile, 'kind', 'dataset')}",
        "",
        "## What this dataset is, in everyday language",
        "",
        _make_executive_summary(profile),
        "",
        "## What stands out structurally",
        "",
    ]
    for axis, score in top:
        lines.append(f"- **{_AXIS_LABELS.get(axis, axis)} ({score:.3f}, {_level(score)})**: {_AXIS_WHAT_IT_MEANS.get(axis, AXIS_DESCRIPTIONS.get(axis, ''))}.")
    lines.extend(["", "## Why this matters for common analysis tasks", ""])
    added_opportunity = False
    if top_ops:
        for axis, score in top_ops:
            if score >= 0.2:
                added_opportunity = True
                lines.append(f"- Because **{_AXIS_LABELS.get(axis, axis)}** is {_level(score)}, {_AXIS_ACTIONS.get(axis, 'this structure should influence your workflow')} ")
    if not added_opportunity:
        lines.append("- No single opportunity axis strongly simplifies the analysis, so benchmarking several baselines and validation designs is sensible.")
    lines.extend(["", "## What could go wrong if you ignore the structure", ""])
    warned = False
    for axis, score in top_risks:
        if score >= 0.2:
            warned = True
            lines.append(f"- If you ignore **{_AXIS_LABELS.get(axis, axis)}**, you may understate that {_AXIS_WHAT_IT_MEANS.get(axis, '')}.")
    if not warned:
        lines.append("- There is no single dominant structural failure mode, but routine checks for drift, noise, and data support are still worth doing.")
    lines.extend(["", "## Practical next steps", ""])
    for idx, step in enumerate(_next_actions(profile), start=1):
        lines.append(f"{idx}. {step}")
    lines.extend(["", "## Task hints from the profiler", ""])
    if getattr(profile, 'task_hints', None):
        for hint in profile.task_hints:
            lines.append(f"- {hint}")
    else:
        lines.append("- No task-specific hint was generated.")
    lines.extend(["", "## Reliability and interpretation guardrails", "", f"Overall reliability is **{profile.reliability.get('overall_score', 0.0):.3f} ({profile.reliability.get('overall_level', 'unknown')})**."])
    if profile.notes:
        lines.append("")
        for note in profile.notes[:8]:
            lines.append(f"- {note}")
    return "\n".join(lines)


def summary_card(profile: Any, *, audience: str = "general", format: str = "markdown") -> str:
    if format == "json":
        return format_summary_card_json(profile, audience=audience)
    if format == "dict":
        return json.dumps(summary_card_dict(profile, audience=audience), indent=2)
    return format_summary_card_markdown(profile, audience=audience)


def narrative_report(profile: Any, *, audience: str = "general", format: str = "markdown") -> str:
    if format == "json":
        return json.dumps({
            "audience": audience,
            "markdown": format_narrative_report(profile, audience=audience),
        }, indent=2)
    return format_narrative_report(profile, audience=audience)
