"""Agent-driving helpers for token-efficient EchoTime workflows.

This module adds a thin orchestration layer on top of profiling and similarity
analysis. The goal is not to replace an external agent framework, but to help
an agent or application choose the smallest useful EchoTime workflow and to
emit a compact context bundle that is cheap to pass back into an LLM.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

import numpy as np

from .profile import DatasetProfile, SeriesProfile, profile_dataset
from .similarity import SimilarityReport, compare_profiles, compare_series, rolling_similarity

Budget = Literal["lean", "balanced", "deep"]
GuideFormat = Literal["markdown", "text", "json"]


@dataclass(slots=True)
class AgentStep:
    name: str
    status: str
    reason: str
    output_kind: str
    stop_here: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "reason": self.reason,
            "output_kind": self.output_kind,
            "stop_here": self.stop_here,
        }


@dataclass(slots=True)
class AgentDriveResult:
    goal: str
    budget: Budget
    audience: str
    mode: str
    headline: str
    steps: list[AgentStep]
    compact_context: dict[str, Any]
    token_saving_rationale: list[str]
    next_actions: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    objects: dict[str, Any] = field(default_factory=dict, repr=False)

    def get(self, name: str) -> Any:
        return self.objects.get(name)

    def to_dict(self) -> dict[str, Any]:
        payload_objects: dict[str, Any] = {}
        for key, value in self.objects.items():
            if hasattr(value, "to_dict"):
                payload_objects[key] = value.to_dict()
            elif isinstance(value, list):
                payload_objects[key] = [
                    item.to_dict() if hasattr(item, "to_dict") else item for item in value
                ]
            else:
                payload_objects[key] = value
        return {
            "goal": self.goal,
            "budget": self.budget,
            "audience": self.audience,
            "mode": self.mode,
            "headline": self.headline,
            "steps": [step.to_dict() for step in self.steps],
            "compact_context": self.compact_context,
            "token_saving_rationale": list(self.token_saving_rationale),
            "next_actions": list(self.next_actions),
            "metadata": dict(self.metadata),
            "objects": payload_objects,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_context_markdown(self) -> str:
        lines = [
            "# EchoTime agent context",
            "",
            f"**goal:** {self.goal}",
            f"**mode:** {self.mode}",
            f"**budget:** {self.budget}",
            "",
            f"**headline:** {self.headline}",
            "",
            "## Compact context",
            "",
        ]
        compact = self.compact_context
        if compact.get("type") == "profile":
            lines.append(f"- archetypes: {', '.join(compact.get('archetypes', []))}")
            lines.append(f"- reliability: {compact.get('reliability', {}).get('score', 'n/a')} ({compact.get('reliability', {}).get('level', 'n/a')})")
            for item in compact.get("top_axes", []):
                lines.append(f"- axis: {item['axis']} = {item['score']:0.3f} ({item['level']})")
            for hint in compact.get("task_hints", [])[:3]:
                lines.append(f"- task hint: {hint}")
        elif compact.get("type") == "similarity":
            lines.append(f"- overall similarity: {compact.get('overall_similarity', 0.0):0.3f} ({compact.get('qualitative_label', 'n/a')})")
            for item in compact.get("top_components", []):
                lines.append(f"- component: {item['name']} = {item['score']:0.3f}")
            if compact.get("profile_similarity") is not None:
                lines.append(f"- profile similarity: {compact['profile_similarity']:0.3f}")
            if compact.get("rolling_summary"):
                lines.append(f"- rolling summary: {compact['rolling_summary']}")
        else:
            lines.append("- no compact context available")
        if self.next_actions:
            lines.extend(["", "## Next actions", ""])
            for item in self.next_actions:
                lines.append(f"- {item}")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        lines = [
            "# EchoTime agent-driven report",
            "",
            f"**goal:** {self.goal}  ",
            f"**mode:** {self.mode}  ",
            f"**budget:** {self.budget}  ",
            f"**audience:** {self.audience}",
            "",
            "## Headline",
            "",
            self.headline,
            "",
            "## Steps executed",
            "",
            "| step | status | output | stop here | reason |",
            "|---|---|---|---|---|",
        ]
        for step in self.steps:
            lines.append(f"| {step.name} | {step.status} | {step.output_kind} | {step.stop_here} | {step.reason} |")
        lines.extend(["", "## Token-saving rationale", ""])
        for item in self.token_saving_rationale:
            lines.append(f"- {item}")
        lines.extend(["", "## Compact context", "", "```json", json.dumps(self.compact_context, indent=2), "```", ""])
        if self.next_actions:
            lines.extend(["## Suggested next actions", ""])
            for item in self.next_actions:
                lines.append(f"- {item}")
            lines.append("")
        if self.metadata:
            lines.extend(["## Metadata", "", "| field | value |", "|---|---|"])
            for key, value in self.metadata.items():
                lines.append(f"| {key} | {value} |")
        return "\n".join(lines)


@dataclass(slots=True)
class AgentDriver:
    goal: str = "understand_dataset"
    budget: Budget = "lean"
    audience: str = "general"
    domain: str | None = None
    rolling_window: int | None = None
    rolling_step: int = 1
    stop_on_clear_signal: bool = True

    def plan(self, *, has_reference: bool = False) -> dict[str, Any]:
        mode = _goal_mode(self.goal, has_reference)
        steps: list[dict[str, Any]] = []
        if mode == "compare":
            steps.append({
                "name": "compare_series",
                "why": "Two candidate trajectories are available, so the cheapest informative first move is raw-series similarity.",
            })
            if self.budget != "lean" or _goal_mentions_profile(self.goal):
                steps.append({
                    "name": "compare_profiles",
                    "why": "Run only if raw similarity is ambiguous or the question is structural rather than purely shape-based.",
                })
            if self.budget == "deep" or _goal_mentions_rolling(self.goal):
                steps.append({
                    "name": "rolling_similarity",
                    "why": "Use only when the question is regime-sensitive or window-sensitive.",
                })
        else:
            steps.append({
                "name": "profile_dataset",
                "why": "The goal is understanding one dataset, so dataset-level profiling is the cheapest comprehensive entry point.",
            })
            if self.budget != "lean" or _goal_mentions_narrative(self.goal) or self.audience != "general":
                steps.append({
                    "name": "summary_card / narrative",
                    "why": "Generate a plain-language artifact only after the structural profile exists.",
                })
        return {
            "goal": self.goal,
            "mode": mode,
            "budget": self.budget,
            "audience": self.audience,
            "planned_steps": steps,
        }

    def run(
        self,
        data: Any,
        reference: Any | None = None,
        *,
        timestamps: Any | None = None,
        reference_timestamps: Any | None = None,
    ) -> AgentDriveResult:
        mode = _goal_mode(self.goal, reference is not None)
        if mode == "compare" and reference is not None:
            return _run_compare_mode(
                data,
                reference,
                goal=self.goal,
                budget=self.budget,
                audience=self.audience,
                timestamps=timestamps,
                reference_timestamps=reference_timestamps,
                rolling_window=self.rolling_window,
                rolling_step=self.rolling_step,
                stop_on_clear_signal=self.stop_on_clear_signal,
            )
        return _run_profile_mode(
            data,
            goal=self.goal,
            budget=self.budget,
            audience=self.audience,
            domain=self.domain,
            timestamps=timestamps,
        )


# ---------------------------------------------------------------------------
# Compact context helpers
# ---------------------------------------------------------------------------


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


def _goal_mode(goal: str, has_reference: bool) -> str:
    goal_l = (goal or "").strip().lower()
    if has_reference:
        return "compare"
    compare_terms = (
        "compare",
        "similar",
        "similarity",
        "analogue",
        "analog",
        "nearest",
        "vs",
        "versus",
        "like",
        "match",
    )
    if any(term in goal_l for term in compare_terms):
        return "compare"
    return "profile"


def _goal_mentions_profile(goal: str) -> bool:
    goal_l = goal.lower()
    return any(term in goal_l for term in ("structural", "profile", "same kind", "cross-domain", "ontology", "dataset card"))


def _goal_mentions_rolling(goal: str) -> bool:
    goal_l = goal.lower()
    return any(term in goal_l for term in ("rolling", "window", "regime", "change over time", "when", "timing shift"))


def _goal_mentions_narrative(goal: str) -> bool:
    goal_l = goal.lower()
    return any(term in goal_l for term in ("explain", "summary", "narrative", "non-technical", "plain language", "report"))


def _approx_length(data: Any) -> int:
    try:
        arr = np.asarray(data)
    except Exception:
        return 0
    if arr.ndim == 0:
        return 1
    return int(arr.shape[0])


def _component_variability(components: Mapping[str, float]) -> float:
    vals = [float(v) for v in components.values() if np.isfinite(v)]
    if len(vals) < 2:
        return 0.0
    return float(np.std(vals))


def _similarity_is_ambiguous(report: SimilarityReport) -> bool:
    score = float(report.similarity_score)
    spread = _component_variability(report.component_scores)
    return (0.40 <= score <= 0.72) or (spread >= 0.18)


def _top_mapping_items(mapping: Mapping[str, float], *, n: int) -> list[dict[str, Any]]:
    items = [
        {"name": key, "score": float(value), "level": _level(float(value))}
        for key, value in mapping.items()
        if np.isfinite(value)
    ]
    items.sort(key=lambda item: item["score"], reverse=True)
    return items[:n]


def _profile_context(profile: DatasetProfile | SeriesProfile, *, budget: Budget, audience: str) -> dict[str, Any]:
    top_n = 3 if budget == "lean" else 4 if budget == "balanced" else 6
    top_axes = [
        {"axis": item["name"], "score": item["score"], "level": item["level"]}
        for item in _top_mapping_items(profile.axes, n=top_n)
    ]
    hints_n = 2 if budget == "lean" else 4 if budget == "balanced" else 6
    notes_n = 1 if budget == "lean" else 2 if budget == "balanced" else 4
    return {
        "type": "profile",
        "audience": audience,
        "headline": f"{profile.metadata.get('domain', 'generic')} {profile.kind} with {', '.join(profile.archetypes[:2]) or 'generic'} tendencies",
        "archetypes": list(profile.archetypes[:3 if budget == 'lean' else 5]),
        "top_axes": top_axes,
        "task_hints": list(profile.task_hints[:hints_n]),
        "reliability": {
            "score": float(profile.reliability.get("overall_score", 0.0)),
            "level": str(profile.reliability.get("overall_level", "n/a")),
        },
        "notes": list(profile.notes[:notes_n]),
    }


def _similarity_context(
    report: SimilarityReport,
    *,
    budget: Budget,
    profile_similarity: float | None = None,
    rolling_summary: str | None = None,
) -> dict[str, Any]:
    top_n = 3 if budget == "lean" else 4 if budget == "balanced" else 6
    return {
        "type": "similarity",
        "headline": report.interpretation,
        "overall_similarity": float(report.similarity_score),
        "qualitative_label": report.qualitative_label,
        "top_components": _top_mapping_items(report.component_scores, n=top_n),
        "profile_similarity": None if profile_similarity is None else float(profile_similarity),
        "rolling_summary": rolling_summary,
        "suggestions": list(report.suggestions[:2 if budget == 'lean' else 4]),
        "notes": list(report.notes[:1 if budget == 'lean' else 3]),
    }


def agent_context(
    obj: DatasetProfile | SeriesProfile | SimilarityReport,
    *,
    budget: Budget = "lean",
    audience: str = "general",
    format: Literal["dict", "markdown", "json"] = "dict",
) -> dict[str, Any] | str:
    if isinstance(obj, (DatasetProfile, SeriesProfile)):
        payload = _profile_context(obj, budget=budget, audience=audience)
    elif isinstance(obj, SimilarityReport):
        payload = _similarity_context(obj, budget=budget)
    else:
        raise TypeError("agent_context expects a DatasetProfile, SeriesProfile, or SimilarityReport.")

    if format == "dict":
        return payload
    if format == "json":
        return json.dumps(payload, indent=2)
    lines = ["# EchoTime compact agent context", "", f"**type:** {payload['type']}", "", payload.get("headline", ""), ""]
    if payload["type"] == "profile":
        for item in payload.get("top_axes", []):
            lines.append(f"- {item['axis']}: {item['score']:0.3f} ({item['level']})")
        for item in payload.get("task_hints", []):
            lines.append(f"- task hint: {item}")
    else:
        lines.append(f"- overall similarity: {payload['overall_similarity']:0.3f} ({payload['qualitative_label']})")
        for item in payload.get("top_components", []):
            lines.append(f"- {item['name']}: {item['score']:0.3f}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Agent-run heuristics
# ---------------------------------------------------------------------------


def _rolling_summary(windows: list[dict[str, Any]]) -> str:
    if not windows:
        return "no rolling windows computed"
    scores = [float(item.get("similarity_score", np.nan)) for item in windows if np.isfinite(item.get("similarity_score", np.nan))]
    if not scores:
        return "rolling windows were computed but similarity scores were not finite"
    return f"mean={float(np.mean(scores)):0.3f}, min={float(np.min(scores)):0.3f}, max={float(np.max(scores)):0.3f}, windows={len(scores)}"


def _run_compare_mode(
    left: Any,
    right: Any,
    *,
    goal: str,
    budget: Budget,
    audience: str,
    timestamps: Any | None,
    reference_timestamps: Any | None,
    rolling_window: int | None,
    rolling_step: int,
    stop_on_clear_signal: bool,
) -> AgentDriveResult:
    steps: list[AgentStep] = []
    objects: dict[str, Any] = {}
    token_rationale: list[str] = [
        "Started with raw-series similarity because it is the cheapest informative comparison when two candidate trajectories are already available.",
    ]

    series_report = compare_series(
        left,
        right,
        left_timestamps=timestamps,
        right_timestamps=reference_timestamps,
        left_name="left",
        right_name="right",
    )
    objects["series_similarity"] = series_report
    ambiguous = _similarity_is_ambiguous(series_report)
    clear_signal = not ambiguous and (series_report.similarity_score >= 0.72 or series_report.similarity_score <= 0.32)
    stop_now = stop_on_clear_signal and budget == "lean" and clear_signal and not _goal_mentions_profile(goal) and not _goal_mentions_rolling(goal)
    steps.append(
        AgentStep(
            name="compare_series",
            status="executed",
            reason="A direct shape-aware comparison gives the fastest first answer.",
            output_kind="SimilarityReport",
            stop_here=stop_now,
        )
    )

    profile_report: SimilarityReport | None = None
    if stop_now:
        token_rationale.append("Skipped deeper structural comparison because raw similarity already gave a decisive signal under a lean token budget.")
    elif budget != "lean" or _goal_mentions_profile(goal) or ambiguous:
        profile_report = compare_profiles(left, right, left_name="left", right_name="right")
        objects["profile_similarity"] = profile_report
        steps.append(
            AgentStep(
                name="compare_profiles",
                status="executed",
                reason="Added ontology-level comparison because the question is structural or the raw result was not decisive.",
                output_kind="SimilarityReport",
            )
        )
        token_rationale.append("Profile similarity ran only after the cheaper raw-series comparison left structural uncertainty or the goal explicitly asked for structure-level comparison.")

    windows: list[dict[str, Any]] | None = None
    enough_length = min(_approx_length(left), _approx_length(right)) >= 32
    if (budget == "deep" or _goal_mentions_rolling(goal)) and enough_length:
        auto_window = rolling_window or max(12, min(_approx_length(left), _approx_length(right)) // 4)
        windows = rolling_similarity(
            left,
            right,
            window=auto_window,
            step=max(1, rolling_step),
            left_timestamps=timestamps,
            right_timestamps=reference_timestamps,
        )
        objects["rolling_similarity"] = windows
        steps.append(
            AgentStep(
                name="rolling_similarity",
                status="executed",
                reason="Computed windowed similarity because the goal is regime-sensitive or the budget allowed a deeper pass.",
                output_kind="list[window summary]",
            )
        )
        token_rationale.append("Rolling similarity is expensive and verbose, so it ran only because the goal mentioned regimes/windows or the budget was deep.")
    elif _goal_mentions_rolling(goal) and not enough_length:
        steps.append(
            AgentStep(
                name="rolling_similarity",
                status="skipped",
                reason="Skipped because the available trajectories are too short for stable rolling windows.",
                output_kind="none",
            )
        )

    rolling_text = None if windows is None else _rolling_summary(windows)
    context = _similarity_context(
        series_report,
        budget=budget,
        profile_similarity=None if profile_report is None else profile_report.similarity_score,
        rolling_summary=rolling_text,
    )
    next_actions = list(series_report.suggestions[:2 if budget == "lean" else 4])
    if profile_report is not None:
        next_actions.append("Use the profile-level report when scales differ or you need to explain mechanism rather than surface shape.")
    if windows is not None:
        next_actions.append("Inspect the rolling windows around the strongest divergences instead of relying only on the aggregate score.")

    return AgentDriveResult(
        goal=goal,
        budget=budget,
        audience=audience,
        mode="compare",
        headline=series_report.interpretation,
        steps=steps,
        compact_context=context,
        token_saving_rationale=token_rationale,
        next_actions=next_actions,
        metadata={
            "series_similarity": f"{series_report.similarity_score:0.3f}",
            "profile_similarity": "n/a" if profile_report is None else f"{profile_report.similarity_score:0.3f}",
            "rolling_windows": 0 if windows is None else len(windows),
        },
        objects=objects,
    )


def _run_profile_mode(
    data: Any,
    *,
    goal: str,
    budget: Budget,
    audience: str,
    domain: str | None,
    timestamps: Any | None,
) -> AgentDriveResult:
    steps: list[AgentStep] = []
    token_rationale: list[str] = [
        "Used dataset profiling as the first move because the goal is to understand one dataset, and that single call already exposes axes, archetypes, reliability, and task hints.",
    ]
    profile = profile_dataset(data, domain=domain, timestamps=timestamps)
    steps.append(
        AgentStep(
            name="profile_dataset",
            status="executed",
            reason="Dataset profiling is the minimal full-coverage structural audit.",
            output_kind="DatasetProfile",
        )
    )

    if budget == "lean" and not _goal_mentions_narrative(goal) and audience == "general":
        token_rationale.append("Skipped the longer narrative layer because a compact summary card is enough under a lean budget.")
    else:
        steps.append(
            AgentStep(
                name="summary_card / narrative",
                status="materialized-on-demand",
                reason="A human-facing communication layer is useful for the requested audience, but it is derived from the profile rather than recomputed.",
                output_kind="markdown report",
            )
        )
        token_rationale.append("Did not rerun analytics to build the summary card or narrative report; both are rendered from the existing profile to save work and tokens.")

    context = _profile_context(profile, budget=budget, audience=audience)
    hints_n = 2 if budget == "lean" else 4
    next_actions = list(profile.task_hints[:hints_n])
    if budget != "lean":
        next_actions.append("Export both a summary card and narrative report if the result needs to travel to non-method collaborators.")

    return AgentDriveResult(
        goal=goal,
        budget=budget,
        audience=audience,
        mode="profile",
        headline=context["headline"],
        steps=steps,
        compact_context=context,
        token_saving_rationale=token_rationale,
        next_actions=next_actions,
        metadata={
            "domain": str(profile.metadata.get("domain", "generic")),
            "reliability": f"{profile.reliability.get('overall_score', 0.0):0.3f}",
        },
        objects={"profile": profile},
    )


def agent_drive(
    data: Any,
    reference: Any | None = None,
    *,
    goal: str = "understand_dataset",
    budget: Budget = "lean",
    audience: str = "general",
    domain: str | None = None,
    timestamps: Any | None = None,
    reference_timestamps: Any | None = None,
    rolling_window: int | None = None,
    rolling_step: int = 1,
    stop_on_clear_signal: bool = True,
) -> AgentDriveResult:
    driver = AgentDriver(
        goal=goal,
        budget=budget,
        audience=audience,
        domain=domain,
        rolling_window=rolling_window,
        rolling_step=rolling_step,
        stop_on_clear_signal=stop_on_clear_signal,
    )
    return driver.run(data, reference, timestamps=timestamps, reference_timestamps=reference_timestamps)


# ---------------------------------------------------------------------------
# Guide content
# ---------------------------------------------------------------------------

AGENT_DRIVING_GUIDE = {
    "title": "EchoTime agent-driving guide",
    "why_it_exists": (
        "Agent-driving is a lightweight orchestration layer that helps an LLM or application choose the smallest useful EchoTime workflow and export a compact context bundle."
    ),
    "token_saving_principles": (
        "Start with the cheapest informative move.",
        "Stop early when the signal is already clear.",
        "Upgrade to structural comparison only when raw shape is ambiguous or the question is structural.",
        "Render summary cards and narratives from existing profiles instead of recomputing analysis.",
        "Pass compact context bundles back into the agent instead of full raw reports when the next step only needs the gist.",
    ),
    "main_api": (
        "AgentDriver(goal=..., budget='lean|balanced|deep')",
        "agent_drive(data, reference=None, goal=..., budget=...)",
        "agent_context(profile_or_similarity_report, budget='lean')",
    ),
    "budgets": {
        "lean": "Do the cheapest sufficient move and stop when the signal is clear.",
        "balanced": "Add structural/profile comparison when ambiguity remains.",
        "deep": "Allow rolling similarity and a fuller context bundle for regime-sensitive questions.",
    },
    "good_goals": (
        "Explain this dataset to a non-technical collaborator",
        "Decide whether repo A's growth curve resembles repo B",
        "Compare these two assets but keep the context compact for another LLM step",
        "Find out whether two datasets are the same kind of temporal problem",
    ),
}


def agent_driving_guide_dict() -> dict[str, Any]:
    return AGENT_DRIVING_GUIDE


def agent_driving_guide(*, format: GuideFormat = "markdown") -> str:
    payload = AGENT_DRIVING_GUIDE
    if format == "json":
        return json.dumps(payload, indent=2)
    lines = [
        f"# {payload['title']}",
        "",
        payload["why_it_exists"],
        "",
        "## Token-saving principles",
        "",
    ]
    for item in payload["token_saving_principles"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Main API", ""])
    for item in payload["main_api"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Budget modes", ""])
    for key, value in payload["budgets"].items():
        lines.append(f"- **{key}:** {value}")
    lines.extend(["", "## Good goal prompts", ""])
    for item in payload["good_goals"]:
        lines.append(f"- {item}")
    return "\n".join(lines)
