"""High-attention case gallery and similarity playbooks for echotime."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

GuideFormat = Literal["markdown", "text", "json"]


@dataclass(frozen=True, slots=True)
class HotCase:
    key: str
    title: str
    why_now: str
    likely_window: str
    data_to_track: tuple[str, ...]
    similarity_questions: tuple[str, ...]
    recommended_api: tuple[str, ...]
    what_non_method_users_should_see: tuple[str, ...]
    notes: tuple[str, ...]


HOT_CASES: tuple[HotCase, ...] = (
    HotCase(
        key="openclaw_star_velocity",
        title="OpenClaw GitHub stars and star-velocity bursts",
        why_now=(
            "This is a classic hype-cycle time series: a fast open-source project with social amplification, release-driven bursts, and potential security/event shocks."
        ),
        likely_window="March–May 2026",
        data_to_track=(
            "daily star count",
            "daily new stars",
            "fork count",
            "release dates",
            "security/advisory dates",
            "docs traffic or install traffic if you have it",
        ),
        similarity_questions=(
            "Does the current 14-day growth curve look more like an organic climb or a short viral spike?",
            "Do post-release star surges resemble earlier release windows?",
            "How similar is OpenClaw's growth to another breakout GitHub project?",
        ),
        recommended_api=(
            "compare_series(current_window, historical_window)",
            "rolling_similarity(repo_a_daily_stars, repo_b_daily_stars, window=14)",
            "compare_profiles(dataset_a, dataset_b)",
        ),
        what_non_method_users_should_see=(
            "a similarity summary saying whether this looks like another sustainable growth window or just a spike",
            "a narrative report explaining whether rhythm, trend, or burstiness is driving the resemblance",
        ),
        notes=(
            "Use cumulative stars and daily star increments side by side; they answer different questions.",
            "Keep event annotations such as releases, tweets, and advisories instead of only storing the numeric series.",
        ),
    ),
    HotCase(
        key="github_breakout_repo_benchmarks",
        title="Breakout GitHub projects: compare star curves across launches",
        why_now=(
            "Developers, investors, and open-source founders all understand star-growth charts quickly, so they travel well across disciplines and social channels."
        ),
        likely_window="March–May 2026",
        data_to_track=(
            "daily stars for several repositories",
            "daily issues and pull requests",
            "release cadence",
            "referral traffic or docs sessions if available",
        ),
        similarity_questions=(
            "Which new repo most resembles a previous breakout launch in its first 30 days?",
            "Do two repos share the same long-tail decay pattern after the initial spike?",
            "Is a repo's community growth more similar to a consumer-product launch than to a typical open-source release?",
        ),
        recommended_api=(
            "compare_series(repo_a_daily_stars, repo_b_daily_stars)",
            "compare_profiles(repo_a_panel, repo_b_panel)",
            "rolling_similarity(repo_a_daily_stars, repo_b_daily_stars, window=30)",
        ),
        what_non_method_users_should_see=(
            "a leaderboard of nearest historical analogs",
            "a simple summary of whether two launches match in trend, timing, and volatility",
        ),
        notes=(
            "Normalize by launch day or first 1,000 stars when comparing early-stage growth curves.",
        ),
    ),
    HotCase(
        key="btc_vs_gold_vs_oil",
        title="BTC vs gold vs oil under shock and macro headlines",
        why_now=(
            "This is a high-traffic financial story because the three series often react differently to risk, inflation, liquidity, and geopolitical shocks."
        ),
        likely_window="March–May 2026",
        data_to_track=(
            "daily close or hourly close for BTC",
            "spot gold or gold ETF close",
            "Brent or WTI close",
            "major policy or geopolitical timestamps",
        ),
        similarity_questions=(
            "When does BTC move more like a risk asset and when does it resemble a stress-sensitive macro series?",
            "Do gold and oil share the same shock windows or only the same broad trend?",
            "Which pair becomes more similar during geopolitical escalation?",
        ),
        recommended_api=(
            "compare_series(btc_returns, gold_returns)",
            "rolling_similarity(gold_returns, oil_returns, window=20)",
            "compare_profiles(window_a, window_b)",
        ),
        what_non_method_users_should_see=(
            "a rolling similarity chart for pairs of assets",
            "a narrative report translating similarity changes into regime language",
        ),
        notes=(
            "Use returns or z-scored prices when scales differ wildly.",
            "Rolling windows are usually more informative than one all-period average for the whole year.",
        ),
    ),
    HotCase(
        key="launch_traffic_vs_signup_conversion",
        title="Launch-week traffic, signup bursts, and docs demand",
        why_now=(
            "This is one of the fastest routes to a shareable time-series story because product teams, founders, and growth marketers immediately understand the plots."
        ),
        likely_window="Any 90-day launch or campaign window",
        data_to_track=(
            "daily sessions",
            "daily signups",
            "docs traffic",
            "GitHub stars or waitlist growth",
            "campaign timestamps",
        ),
        similarity_questions=(
            "Did this launch behave more like a community release or a paid campaign burst?",
            "Are docs-traffic spikes synchronized with signup spikes?",
            "Which earlier launch is the nearest analog to the current one?",
        ),
        recommended_api=(
            "compare_series(signups, docs_sessions)",
            "rolling_similarity(launch_a_sessions, launch_b_sessions, window=7)",
            "compare_profiles(product_a_dataset, product_b_dataset)",
        ),
        what_non_method_users_should_see=(
            "a one-page launch summary with shared peaks, lagged peaks, and watchouts",
            "plain-language notes on whether the launch looks healthy or purely burst-driven",
        ),
        notes=(
            "Keep campaign/event markers and channel labels if you want to explain the patterns later.",
        ),
    ),
)


def hot_case_gallery_dict(*, audience: str = "general", window: str = "next_90_days") -> dict[str, Any]:
    return {
        "package": "echotime",
        "audience": audience,
        "window": window,
        "cases": [asdict(case) for case in HOT_CASES],
    }


SIMILARITY_PLAYBOOK = {
    "name": "echotime similarity playbook",
    "what_similarity_means": (
        "Similarity in EchoTime is not one thing. Sometimes you care about raw point-by-point shape, sometimes about shared rhythm, and sometimes about structural similarity at the dataset level."
    ),
    "when_to_use_raw_series_similarity": (
        "Use raw-series similarity when two trajectories live on roughly compatible time scales and you want to ask whether the visible shape or timing is alike."
    ),
    "when_to_use_profile_similarity": (
        "Use profile similarity when the datasets come from different scales, units, or observation modes, but you still want to compare their structural character."
    ),
    "best_first_moves": (
        "Decide whether you are comparing levels, returns, increments, or z-scored shape.",
        "Preserve timestamps and event annotations instead of stripping them away.",
        "Use rolling similarity for regimes that probably change over time.",
        "Show both the numeric similarity report and a simple overlay plot.",
    ),
    "api_pattern": (
        "compare_series(left, right) for direct shape comparison",
        "rolling_similarity(left, right, window=...) for changing relationships over time",
        "compare_profiles(left, right) for dataset-level structural analogies",
    ),
    "non_method_translation": (
        "High shape similarity means the curves visibly move alike.",
        "High spectral similarity means the rhythms match even if peaks happen at slightly different times.",
        "High profile similarity means the datasets behave like the same kind of temporal problem even if the raw numbers differ.",
    ),
}


def similarity_playbook_dict() -> dict[str, Any]:
    return SIMILARITY_PLAYBOOK


def _render_hot_cases_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# EchoTime hot case gallery",
        "",
        f"**window:** {payload['window']}  ",
        f"**audience:** {payload['audience']}",
        "",
        "These are high-attention cases chosen for shareability, public interest, and clear time-series storytelling.",
        "",
    ]
    for case in payload["cases"]:
        lines.extend([
            f"## {case['title']}",
            "",
            f"**case key:** `{case['key']}`  ",
            f"**Likely attention window:** {case['likely_window']}",
            "",
            f"**Why this can travel:** {case['why_now']}",
            "",
            "**Data to track:**",
            "",
        ])
        for item in case["data_to_track"]:
            lines.append(f"- {item}")
        lines.extend(["", "**Similarity questions worth asking:**", ""])
        for item in case["similarity_questions"]:
            lines.append(f"- {item}")
        lines.extend(["", "**Recommended API:**", ""])
        for item in case["recommended_api"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "**What non-method users should see:**", ""])
        for item in case["what_non_method_users_should_see"]:
            lines.append(f"- {item}")
        lines.extend(["", "**Notes:**", ""])
        for item in case["notes"]:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def _render_similarity_playbook_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# EchoTime similarity guide",
        "",
        payload["what_similarity_means"],
        "",
        "## When to use raw-series similarity",
        "",
        payload["when_to_use_raw_series_similarity"],
        "",
        "## When to use profile similarity",
        "",
        payload["when_to_use_profile_similarity"],
        "",
        "## Best first moves",
        "",
    ]
    for item in payload["best_first_moves"]:
        lines.append(f"- {item}")
    lines.extend(["", "## API pattern", ""])
    for item in payload["api_pattern"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## How to explain the outputs to non-method users", ""])
    for item in payload["non_method_translation"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def hot_case_gallery(*, audience: str = "general", window: str = "next_90_days", format: GuideFormat = "markdown") -> str:
    payload = hot_case_gallery_dict(audience=audience, window=window)
    if format == "json":
        return json.dumps(payload, indent=2)
    markdown = _render_hot_cases_markdown(payload)
    if format == "text":
        return markdown
    return markdown


def similarity_playbook(*, format: GuideFormat = "markdown") -> str:
    payload = similarity_playbook_dict()
    if format == "json":
        return json.dumps(payload, indent=2)
    markdown = _render_similarity_playbook_markdown(payload)
    if format == "text":
        return markdown
    return markdown
