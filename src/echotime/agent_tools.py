"""Stable agent-first tool wrappers and schemas for echotime.

The purpose of this module is to expose a *small, stable, low-token* surface
for external agents. The wrappers are intentionally narrower than the full
package API and return a consistent success/error envelope.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Literal

import numpy as np

from .agent import agent_context
from .communication import summary_card_dict
from .positioning import tooling_router
from .profile import profile_dataset
from .similarity import compare_profiles, compare_series, rolling_similarity

TOOL_SCHEMA_VERSION = "2.4.0"
ToolFormat = Literal["dict", "json"]
Budget = Literal["lean", "balanced", "deep"]
CompareMode = Literal["auto", "series", "profile"]
InputKind = Literal[
    "auto",
    "array",
    "table",
    "irregular",
    "event_stream",
    "path_or_uri",
    "dataframe_like",
    "typed_wrapper",
]


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



def _confidence_from_reliability(value: float) -> str:
    if value >= 0.8:
        return "high"
    if value >= 0.55:
        return "moderate"
    return "low"



def _profile_limitations(profile: Any) -> list[str]:
    caveats: list[str] = []
    rel = profile.reliability.get("axes", {})
    for axis, info in rel.items():
        if float(info.get("score", 0.0)) < 0.45:
            for note in info.get("caveats", [])[:1]:
                caveats.append(f"{axis}: {note}")
    caveats.extend(profile.notes[:2])
    if not caveats:
        caveats.append(
            "This is a structural summary, not a task-specific guarantee."
        )
    return caveats[:4]



def _similarity_ambiguous(report: Any) -> bool:
    score = float(report.similarity_score)
    vals = [float(v) for v in report.component_scores.values() if np.isfinite(v)]
    spread = float(np.std(vals)) if len(vals) >= 2 else 0.0
    return (0.40 <= score <= 0.72) or (spread >= 0.18)



def _infer_ref_kind(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, (str, Path, os.PathLike)):
        return "path_or_uri"
    cls_name = value.__class__.__name__.lower()
    if cls_name in {"fmriinput", "eeginput", "irregulartimeseriesinput", "irregularsubjectinput", "eventstreaminput"}:
        return "typed_wrapper"
    if hasattr(value, "columns"):
        return "dataframe_like"
    if hasattr(value, "dims") or hasattr(value, "coords"):
        return "xarray_like"
    if hasattr(value, "get_data"):
        return "typed_wrapper"
    if isinstance(value, np.ndarray):
        return "array"
    if hasattr(value, "__array__"):
        return "array_like"
    if isinstance(value, dict):
        return "mapping"
    if isinstance(value, (list, tuple)):
        return "list_like"
    return cls_name or "object"



def _materialize_ref(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        try:
            return np.asarray(value, dtype=float)
        except Exception:
            return np.asarray(value)
    return value


def _stable_digest(value: Any) -> str:
    try:
        if value is None:
            payload = b'none'
        elif isinstance(value, (str, Path, os.PathLike)):
            payload = f'path:{Path(value)}'.encode('utf-8', errors='ignore')
        elif isinstance(value, np.ndarray) or hasattr(value, '__array__'):
            arr = np.asarray(value)
            flat = arr.reshape(-1) if arr.size else arr
            head = flat[:64].astype(float, copy=False).tolist() if flat.size else []
            tail = flat[-64:].astype(float, copy=False).tolist() if flat.size else []
            summary = {
                'shape': tuple(arr.shape),
                'dtype': str(arr.dtype),
                'head': head,
                'tail': tail,
                'mean': float(np.nanmean(arr)) if arr.size else 0.0,
                'std': float(np.nanstd(arr)) if arr.size else 0.0,
            }
            payload = json.dumps(summary, sort_keys=True).encode('utf-8')
        elif hasattr(value, 'to_dict'):
            payload = json.dumps(value.to_dict(), sort_keys=True, default=str).encode('utf-8')
        elif hasattr(value, 'columns'):
            payload = f'dataframe_like:{getattr(value, "shape", None)}:{list(getattr(value, "columns", []))[:16]}'.encode('utf-8')
        else:
            payload = repr(type(value)).encode('utf-8')
    except Exception:
        payload = repr(type(value)).encode('utf-8')
    return hashlib.sha1(payload).hexdigest()[:16]


def _cache_key(tool: str, *parts: str) -> str:
    raw = ':'.join([tool, *parts])
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()[:20]


def _artifact_uri(tool: str, cache_key: str) -> str:
    return f'artifact://echotime/{tool}/{cache_key}.json'


def _cost_hint(*, budget: str, primary: Any, secondary: Any | None = None) -> str:
    size = 0
    try:
        size += int(np.asarray(primary).size)
    except Exception:
        size += 0
    if secondary is not None:
        try:
            size += int(np.asarray(secondary).size)
        except Exception:
            size += 0
    if budget == 'lean' and size < 50_000:
        return 'low'
    if budget == 'deep' or size >= 250_000:
        return 'high'
    return 'medium'


def _input_contract(
    *,
    primary: Any | None = None,
    secondary: Any | None = None,
    timestamps: Any | None = None,
    reference_timestamps: Any | None = None,
    input_kind: str = "auto",
    mode: str | None = None,
    budget: str | None = None,
    domain: str | None = None,
    audience: str | None = None,
    available_inputs: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    return {
        "accepted_input_kinds": [
            "array",
            "dataframe_like",
            "table",
            "typed_wrapper",
            "path_or_uri",
            "irregular",
            "event_stream",
        ],
        "requested_input_kind": input_kind,
        "resolved_input_kind": _infer_ref_kind(primary),
        "resolved_reference_kind": _infer_ref_kind(secondary) if secondary is not None else None,
        "has_timestamps": timestamps is not None,
        "has_reference_timestamps": reference_timestamps is not None,
        "mode": mode,
        "budget": budget,
        "domain": domain,
        "audience": audience,
        "available_inputs": list(available_inputs) if available_inputs is not None else None,
    }



def _success_envelope(tool: str, *, input_contract: dict[str, Any], artifact_uri: str | None = None, cost_hint: str | None = None, input_digest: str | None = None, cache_key: str | None = None, **payload: Any) -> dict[str, Any]:
    base = {
        "schema_version": TOOL_SCHEMA_VERSION,
        "tool": tool,
        "ok": True,
        "input_contract": input_contract,
        "artifact_uri": artifact_uri,
        "cost_hint": cost_hint,
        "input_digest": input_digest,
        "cache_key": cache_key,
        "error": None,
    }
    base.update(payload)
    return base



def _error_envelope(tool: str, *, input_contract: dict[str, Any], code: str, message: str, input_digest: str | None = None, cache_key: str | None = None, cost_hint: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": TOOL_SCHEMA_VERSION,
        "tool": tool,
        "ok": False,
        "input_contract": input_contract,
        "artifact_uri": None,
        "cost_hint": cost_hint,
        "input_digest": input_digest,
        "cache_key": cache_key,
        "error": {"code": code, "message": message},
        "limitations": [message],
        "recommended_next_step": "Check the input contract and retry with a supported reference or in-memory object.",
        "next_actions": [
            "Verify the input reference resolves to supported time-series data.",
            "Retry with explicit timestamps if the data are irregular.",
        ],
    }



def ts_profile(
    data_ref: Any,
    *,
    input_kind: InputKind = "auto",
    timestamps_ref: Any | None = None,
    domain: str | None = None,
    budget: Budget = "lean",
    audience: str = "agent",
    safe: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    input_contract = _input_contract(
        primary=data_ref,
        timestamps=timestamps_ref,
        input_kind=input_kind,
        budget=budget,
        domain=domain,
        audience=audience,
    )
    input_digest = _stable_digest(data_ref)
    cache_key = _cache_key("ts_profile", input_digest, _stable_digest(timestamps_ref), str(domain or "generic"), budget)
    try:
        profile = profile_dataset(_materialize_ref(data_ref), domain=domain, timestamps=timestamps_ref, **kwargs)
        card = summary_card_dict(profile, audience=audience)
        next_actions = card["recommended_next_actions"][: (3 if budget == "lean" else 5)]
        evidence = {
            "domain": str(profile.metadata.get("domain", domain or "generic")),
            "observation_mode": str(profile.metadata.get("observation_mode", "dense")),
            "n_subjects": int(profile.metadata.get("n_subjects", 1) or 1),
            "n_channels_median": int(profile.metadata.get("n_channels_median", 1) or 1),
            "length_median": int(profile.metadata.get("length_median", profile.metadata.get("length", 0)) or 0),
            "dominant_axes": str(profile.metadata.get("dominant_axes", "")),
            "top_axis_scores": [
                {
                    "axis": item["axis"],
                    "score": float(item["score"]),
                    "level": str(item["level"]),
                }
                for item in card["top_structure_axes"][: (3 if budget == "lean" else 5)]
            ],
        }
        return _success_envelope(
            "ts_profile",
            input_contract=input_contract,
            artifact_uri=_artifact_uri("ts_profile", cache_key),
            cost_hint=_cost_hint(budget=budget, primary=data_ref),
            input_digest=input_digest,
            cache_key=cache_key,
            headline=card["executive_summary"],
            archetypes=list(profile.archetypes[:4]),
            top_axes=card["top_structure_axes"][: (3 if budget == "lean" else 5)],
            reliability={
                "score": float(profile.reliability.get("overall_score", 0.0)),
                "level": str(profile.reliability.get("overall_level", "unknown")),
                "method": str(profile.reliability.get("method", "heuristic")),
            },
            confidence=_confidence_from_reliability(float(profile.reliability.get("overall_score", 0.0))),
            limitations=_profile_limitations(profile),
            evidence=evidence,
            recommended_next_step=next_actions[0] if next_actions else "Review the summary card and inspect the strongest axes.",
            next_actions=next_actions,
            compact_context=agent_context(profile, budget=budget, audience=audience, format="dict"),
        )
    except Exception as exc:  # pragma: no cover - safety path only
        if not safe:
            raise
        return _error_envelope(
            "ts_profile",
            input_contract=input_contract,
            code="profiling_failed",
            message=str(exc),
            input_digest=input_digest,
            cache_key=cache_key,
            cost_hint=_cost_hint(budget=budget, primary=data_ref),
        )



def ts_compare(
    left_ref: Any,
    right_ref: Any,
    *,
    left_timestamps_ref: Any | None = None,
    right_timestamps_ref: Any | None = None,
    mode: CompareMode = "auto",
    budget: Budget = "lean",
    safe: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    input_contract = _input_contract(
        primary=left_ref,
        secondary=right_ref,
        timestamps=left_timestamps_ref,
        reference_timestamps=right_timestamps_ref,
        mode=mode,
        budget=budget,
    )
    left_digest = _stable_digest(left_ref)
    right_digest = _stable_digest(right_ref)
    input_digest = f"{left_digest}:{right_digest}"
    cache_key = _cache_key("ts_compare", input_digest, _stable_digest(left_timestamps_ref), _stable_digest(right_timestamps_ref), mode, budget)
    try:
        series_report = compare_series(
            _materialize_ref(left_ref),
            _materialize_ref(right_ref),
            left_timestamps=left_timestamps_ref,
            right_timestamps=right_timestamps_ref,
            **kwargs,
        )
        profile_report = None
        stop_here = False
        if mode == "profile":
            profile_report = compare_profiles(_materialize_ref(left_ref), _materialize_ref(right_ref), **kwargs)
        elif mode == "auto":
            ambiguous = _similarity_ambiguous(series_report)
            stop_here = budget == "lean" and not ambiguous and (
                series_report.similarity_score >= 0.72 or series_report.similarity_score <= 0.32
            )
            if not stop_here and budget != "lean":
                profile_report = compare_profiles(_materialize_ref(left_ref), _materialize_ref(right_ref), **kwargs)
        verdict = str(series_report.interpretation)
        next_actions = list(series_report.suggestions[: (2 if budget == "lean" else 4)])
        if profile_report is not None:
            next_actions.append("Inspect profile-level differences when raw shape alone is not enough.")
        confidence = "high" if stop_here or series_report.similarity_score >= 0.75 or series_report.similarity_score <= 0.25 else "moderate"
        evidence = {
            "series_similarity": float(series_report.similarity_score),
            "qualitative_label": str(series_report.qualitative_label),
            "top_component_scores": [
                {"name": key, "score": float(value), "level": _level(float(value))}
                for key, value in sorted(series_report.component_scores.items(), key=lambda kv: kv[1], reverse=True)[: (3 if budget == "lean" else 5)]
            ],
            "left_length": int(np.asarray(left_ref).reshape(-1).size) if hasattr(np.asarray(left_ref), "reshape") else None,
            "right_length": int(np.asarray(right_ref).reshape(-1).size) if hasattr(np.asarray(right_ref), "reshape") else None,
        }
        payload = _success_envelope(
            "ts_compare",
            input_contract=input_contract,
            artifact_uri=_artifact_uri("ts_compare", cache_key),
            cost_hint=_cost_hint(budget=budget, primary=left_ref, secondary=right_ref),
            input_digest=input_digest,
            cache_key=cache_key,
            headline=verdict,
            verdict=verdict,
            overall_similarity=float(series_report.similarity_score),
            qualitative_label=str(series_report.qualitative_label),
            top_components=evidence["top_component_scores"],
            stop_here=stop_here,
            confidence=confidence,
            limitations=list(series_report.notes[:3]) or ["Similarity is a summary and can hide local mismatches."],
            evidence=evidence,
            recommended_next_step=next_actions[0] if next_actions else "Overlay the two series and inspect the component scores.",
            next_actions=next_actions,
            compact_context=agent_context(series_report, budget=budget, format="dict"),
        )
        if profile_report is not None:
            payload["profile_similarity"] = float(profile_report.similarity_score)
        if budget == "deep":
            left_arr = np.asarray(left_ref).reshape(-1)
            right_arr = np.asarray(right_ref).reshape(-1)
            window = max(12, min(len(left_arr), len(right_arr)) // 4)
            windows = rolling_similarity(
                left_ref,
                right_ref,
                left_timestamps=left_timestamps_ref,
                right_timestamps=right_timestamps_ref,
                window=window,
                step=2,
            )
            scores = [float(item.get("similarity_score", np.nan)) for item in windows if np.isfinite(item.get("similarity_score", np.nan))]
            if scores:
                payload["rolling_similarity"] = {
                    "mean": float(np.mean(scores)),
                    "min": float(np.min(scores)),
                    "max": float(np.max(scores)),
                    "windows": len(scores),
                }
        return payload
    except Exception as exc:  # pragma: no cover - safety path only
        if not safe:
            raise
        return _error_envelope(
            "ts_compare",
            input_contract=input_contract,
            code="comparison_failed",
            message=str(exc),
            input_digest=input_digest,
            cache_key=cache_key,
            cost_hint=_cost_hint(budget=budget, primary=left_ref, secondary=right_ref),
        )



def ts_route(
    task: str,
    *,
    available_inputs: list[str] | tuple[str, ...] | None = None,
    has_reference: bool | None = None,
    safe: bool = True,
) -> dict[str, Any]:
    available_inputs = list(available_inputs or [])
    if has_reference is None:
        has_reference = any(item in {"right_ref", "reference", "comparison_pair", "two_series", "left_ref"} for item in available_inputs)
    input_contract = _input_contract(
        available_inputs=available_inputs,
        mode="routing",
        budget="lean",
    )
    input_digest = _stable_digest(task)
    cache_key = _cache_key("ts_route", input_digest, json.dumps(sorted(available_inputs)), str(has_reference))
    try:
        route = tooling_router(task, format="object")
        route_dict = route.to_dict()
        primary = list(route_dict.get("primary_packages", []))
        detected_task = str(route_dict.get("detected_task", task))
        task_l = task.lower()
        compare_like = has_reference or any(token in task_l for token in ["compare", "similar", "similarity", "vs", "versus", "analog", "match", "relative to", "reference"])
        if compare_like:
            recommended_tool = "ts_compare"
            route_class = "comparison"
            why_echotime = "Use echotime first when you need a compact, human-readable similarity verdict before dropping into lower-level distance tooling."
            expected_output = "compact similarity verdict with evidence, confidence, and next actions"
            recommended_next_step = "Call ts_compare with left_ref and right_ref."
        else:
            recommended_tool = "ts_profile"
            route_class = "profiling"
            why_echotime = "Use echotime first when you need a plain-English structural report before choosing a modelling stack."
            expected_output = "compact structural report with headline, top axes, reliability, and next actions"
            recommended_next_step = "Call ts_profile with data_ref."
        next_actions = list(route_dict.get("next_steps", []))[:3]
        if not next_actions:
            next_actions = [recommended_next_step]
        return _success_envelope(
            "ts_route",
            input_contract=input_contract,
            artifact_uri=_artifact_uri("ts_route", cache_key),
            cost_hint="low",
            input_digest=input_digest,
            cache_key=cache_key,
            recommended_tool=recommended_tool,
            reason=str(route_dict.get("echotime_role", route_dict.get("first_step", ""))),
            expected_output=expected_output,
            confidence=str(route_dict.get("confidence", "moderate")),
            limitations=[str(route_dict.get("caution", "Routing is heuristic and should be reviewed for high-stakes use."))],
            evidence={
                "detected_task": detected_task,
                "first_step": str(route_dict.get("first_step", "")),
                "ecosystem_companions": primary,
                "routing_rule": route_class,
                "fallback_used": False,
            },
            recommended_next_step=recommended_next_step,
            next_actions=next_actions,
            ecosystem_companions=primary,
            route_class=route_class,
            why_echotime=why_echotime,
            stable_contract=True,
            route_status="stable",
        )
    except Exception as exc:  # pragma: no cover - safety path only
        if not safe:
            raise
        return _error_envelope(
            "ts_route",
            input_contract=input_contract,
            code="routing_failed",
            message=str(exc),
            input_digest=input_digest,
            cache_key=cache_key,
            cost_hint="low",
        )



def _data_ref_schema(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "oneOf": [
            {"type": "string", "description": "Path, URI, or caller-managed handle."},
            {"type": "array", "description": "Inline array-like numeric values."},
            {"type": "object", "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."},
        ],
    }



def tool_schemas(*, format: ToolFormat = "dict") -> dict[str, Any] | str:
    success_envelope = {
        "type": "object",
        "required": [
            "schema_version",
            "tool",
            "ok",
            "input_contract",
            "artifact_uri",
            "cost_hint",
            "input_digest",
            "cache_key",
            "confidence",
            "limitations",
            "recommended_next_step",
            "next_actions",
            "error",
        ],
        "properties": {
            "schema_version": {"type": "string"},
            "tool": {"type": "string"},
            "ok": {"type": "boolean"},
            "input_contract": {"type": "object"},
            "artifact_uri": {"oneOf": [{"type": "null"}, {"type": "string"}]},
            "cost_hint": {"oneOf": [{"type": "null"}, {"type": "string"}]},
            "input_digest": {"oneOf": [{"type": "null"}, {"type": "string"}]},
            "cache_key": {"oneOf": [{"type": "null"}, {"type": "string"}]},
            "confidence": {"type": "string"},
            "limitations": {"type": "array", "items": {"type": "string"}},
            "evidence": {"type": "object"},
            "recommended_next_step": {"type": "string"},
            "next_actions": {"type": "array", "items": {"type": "string"}},
            "error": {"oneOf": [{"type": "null"}, {"type": "object"}]},
        },
    }
    schemas = {
        "schema_version": TOOL_SCHEMA_VERSION,
        "tools": [
            {
                "name": "ts_profile",
                "description": "Profile a time-series dataset for modelling handoff and return a compact structural summary.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data_ref": _data_ref_schema("Array-like data, typed wrapper, DataFrame-like table, or a caller-managed path/URI."),
                        "input_kind": {"type": "string", "enum": ["auto", "array", "table", "irregular", "event_stream", "path_or_uri", "dataframe_like", "typed_wrapper"]},
                        "timestamps_ref": _data_ref_schema("Optional timestamps aligned with data_ref for irregular or explicitly timed series."),
                        "domain": {"type": "string", "description": "Optional domain hint such as generic, traffic, clinical, wearable, fmri, or eeg."},
                        "budget": {"type": "string", "enum": ["lean", "balanced", "deep"]},
                        "audience": {"type": "string", "description": "general, agent, clinical, product, neuroscience, etc."},
                        "safe": {"type": "boolean"},
                    },
                    "required": ["data_ref"],
                    "additionalProperties": True,
                },
                "output_schema": {
                    **success_envelope,
                    "required": success_envelope["required"] + ["headline", "archetypes", "top_axes", "reliability"],
                },
            },
            {
                "name": "ts_compare",
                "description": "Compare two time-series inputs and stop early if the signal is already clear.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "left_ref": _data_ref_schema("Primary series or dataset reference."),
                        "right_ref": _data_ref_schema("Reference series or dataset to compare against."),
                        "left_timestamps_ref": _data_ref_schema("Optional timestamps for left_ref."),
                        "right_timestamps_ref": _data_ref_schema("Optional timestamps for right_ref."),
                        "mode": {"type": "string", "enum": ["auto", "series", "profile"]},
                        "budget": {"type": "string", "enum": ["lean", "balanced", "deep"]},
                        "safe": {"type": "boolean"},
                    },
                    "required": ["left_ref", "right_ref"],
                    "additionalProperties": True,
                },
                "output_schema": {
                    **success_envelope,
                    "required": success_envelope["required"] + ["verdict", "overall_similarity", "qualitative_label", "top_components", "stop_here"],
                },
            },
            {
                "name": "ts_route",
                "description": "Route a natural-language time-series task to the smallest useful echotime tool and expected output.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                        "available_inputs": {"type": "array", "items": {"type": "string"}, "description": "Optional caller-side hints such as ['data_ref'] or ['left_ref', 'right_ref']."},
                        "has_reference": {"type": "boolean"},
                        "safe": {"type": "boolean"},
                    },
                    "required": ["task"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    **success_envelope,
                    "required": success_envelope["required"] + ["recommended_tool", "reason", "expected_output"],
                },
            },
        ],
    }
    return schemas if format == "dict" else json.dumps(schemas, indent=2)



def openai_function_schemas(*, format: ToolFormat = "dict") -> dict[str, Any] | str:
    payload = {
        "schema_version": TOOL_SCHEMA_VERSION,
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in tool_schemas(format="dict")["tools"]
        ],
    }
    return payload if format == "dict" else json.dumps(payload, indent=2)



def mcp_tool_descriptors(*, format: ToolFormat = "dict") -> dict[str, Any] | str:
    payload = {
        "schema_version": TOOL_SCHEMA_VERSION,
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["input_schema"],
            }
            for tool in tool_schemas(format="dict")["tools"]
        ],
    }
    return payload if format == "dict" else json.dumps(payload, indent=2)
