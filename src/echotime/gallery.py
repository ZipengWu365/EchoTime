"""Cross-disciplinary case gallery for echotime."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

GuideFormat = Literal["markdown", "text", "json"]


@dataclass(frozen=True, slots=True)
class CaseStudy:
    key: str
    title: str
    domains: tuple[str, ...]
    audiences: tuple[str, ...]
    environments: tuple[str, ...]
    why_people_care: str
    typical_data: str
    common_questions: tuple[str, ...]
    where_echotime_helps: str
    recommended_entrypoints: tuple[str, ...]
    what_to_show_non_method_users: tuple[str, ...]
    practical_value: tuple[str, ...]


CASES: tuple[CaseStudy, ...] = (
    CaseStudy(
        key="web_product_traffic",
        title="Web/app traffic and product analytics",
        domains=("generic", "product", "web", "traffic"),
        audiences=("general", "product", "operations", "cross-disciplinary"),
        environments=("notebook", "python_script", "pandas_pipeline", "cli_batch"),
        why_people_care="Traffic, conversion, and usage metrics are easy to explain to broad audiences and are often the first time-series many teams operationalize.",
        typical_data="Hourly or daily sessions, clicks, conversions, campaign spikes, release-day shocks, and multi-metric product dashboards.",
        common_questions=(
            "Is this mostly trend plus seasonality, or is it dominated by launches and bursts?",
            "Should we trust simple forecasting baselines, or is the system drifting too much?",
            "Which metrics move together strongly enough to justify multivariate modelling?",
        ),
        where_echotime_helps="It gives a plain-language structural readout before teams jump into forecasting, anomaly detection, or KPI attribution debates.",
        recommended_entrypoints=(
            "profile_dataset(dataframe, domain='traffic')",
            "profile_dataset(array, domain='product')",
            "profile.to_summary_card_markdown()",
        ),
        what_to_show_non_method_users=(
            "summary card with top axes and plain-language meanings",
            "narrative report explaining whether the data are steady, seasonal, bursty, or drifting",
            "dataset card attached to experiment or dashboard documentation",
        ),
        practical_value=(
            "Explain why weekly seasonality matters before model selection.",
            "Flag that campaign bursts can distort average-based summaries.",
            "Communicate when traffic is stable enough for lightweight baselines.",
        ),
    ),
    CaseStudy(
        key="retail_demand_operations",
        title="Retail demand, inventory, and operations planning",
        domains=("generic", "retail", "operations", "supply_chain"),
        audiences=("general", "operations", "cross-disciplinary"),
        environments=("notebook", "python_script", "pandas_pipeline", "cli_batch"),
        why_people_care="Demand planning is a high-visibility time-series use case because it directly affects stockouts, staffing, and revenue.",
        typical_data="Store- or SKU-level sales, promotion calendars, replenishment signals, and holiday-driven demand waves.",
        common_questions=(
            "How strong is the predictable seasonality relative to promo shocks?",
            "How heterogeneous are stores or SKUs?",
            "Should validation split by time only, or by store/product group as well?",
        ),
        where_echotime_helps="It clarifies whether the dataset is mostly rhythmic, drift-heavy, bursty, or highly heterogeneous across units.",
        recommended_entrypoints=(
            "profile_dataset(dataframe, domain='operations')",
            "profile.to_summary_card_markdown()",
            "profile.to_narrative_report()",
        ),
        what_to_show_non_method_users=(
            "one-page summary card for merchants or operators",
            "narrative report that translates axes into replenishment implications",
        ),
        practical_value=(
            "Separate seasonality-heavy planning problems from campaign-shock problems.",
            "Justify store-aware or SKU-aware validation.",
            "Document when heterogeneity makes one pooled model hard to trust.",
        ),
    ),
    CaseStudy(
        key="energy_load_and_smart_metering",
        title="Energy load, smart metering, and grid operations",
        domains=("generic", "energy", "operations", "environmental"),
        audiences=("general", "operations", "cross-disciplinary"),
        environments=("notebook", "python_script", "pandas_pipeline", "ml_benchmark"),
        why_people_care="Energy load is a classic public-facing time-series use case with clear seasonality, weather sensitivity, and operational stakes.",
        typical_data="Building load curves, feeder demand, smart-meter cohorts, distributed sensors, and weather-linked covariates.",
        common_questions=(
            "How much of the signal is predictable daily/weekly rhythm?",
            "Do sites behave similarly enough to pool them?",
            "Are drifts or regime changes strong enough to break static models?",
        ),
        where_echotime_helps="It turns those questions into a structured profile that is easy to compare across sites or benchmark datasets.",
        recommended_entrypoints=(
            "profile_dataset(array, domain='energy')",
            "profile_dataset(dataframe, domain='energy')",
            "profile.to_card_json()",
        ),
        what_to_show_non_method_users=(
            "plain-language summary of rhythm, drift, and heterogeneity",
            "dataset card for benchmark governance or site comparison",
        ),
        practical_value=(
            "Show when seasonality dominates enough for strong baseline models.",
            "Flag when regime changes or drifts make historic averages unreliable.",
        ),
    ),
    CaseStudy(
        key="wearable_longitudinal_cohort",
        title="Wearable, digital biomarker, or recovery cohort",
        domains=("wearable", "clinical"),
        audiences=("general", "clinical", "cross-disciplinary"),
        environments=("notebook", "python_script", "pandas_pipeline", "cli_batch"),
        why_people_care="Wearables are one of the highest-traffic modern time-series domains because they connect research, product, health, and consumer reporting.",
        typical_data="Heart rate, activity, sleep, recovery, repeated visits, device adherence gaps, and subject-level timelines.",
        common_questions=(
            "Is the problem dominated by adherence gaps and irregular follow-up?",
            "Are people more different from each other than days are within each person?",
            "Should evaluation split by subject, visit, or time?",
        ),
        where_echotime_helps="It exposes longitudinal instability, dropout imbalance, and heterogeneity in a way clinicians and product teams can both read.",
        recommended_entrypoints=(
            "profile_dataset(dataframe, domain='wearable')",
            "profile.to_summary_card_markdown()",
            "profile.to_narrative_report()",
        ),
        what_to_show_non_method_users=(
            "summary card for study coordinators or clinicians",
            "narrative report explaining adherence, subject differences, and validation implications",
        ),
        practical_value=(
            "Make longitudinal cohort quality visible before model building.",
            "Show whether individual fingerprint structure is strong enough to matter.",
        ),
    ),
    CaseStudy(
        key="icu_irregular_monitoring",
        title="ICU, hospital telemetry, and irregular monitoring",
        domains=("clinical",),
        audiences=("general", "clinical", "cross-disciplinary"),
        environments=("notebook", "python_script", "pandas_pipeline", "cli_batch"),
        why_people_care="Irregular clinical monitoring is high-impact because timestamp quality, sparsity, and bursts of interventions strongly affect downstream claims.",
        typical_data="Irregular vitals, labs, interventions, alarms, asynchronous channels, and mixed event-plus-signal timelines.",
        common_questions=(
            "Are timing irregularity and missingness the main difficulty?",
            "Does the dataset behave like a sparse event process or a dense physiological signal?",
            "How much do patients differ structurally?",
        ),
        where_echotime_helps="It keeps observation structure honest and gives non-method collaborators a reasoned explanation for why naive regular-grid assumptions may fail.",
        recommended_entrypoints=(
            "profile_dataset(IrregularTimeSeriesInput(...), domain='clinical')",
            "profile_dataset(records_or_dataframe, domain='clinical')",
            "profile.to_narrative_report()",
        ),
        what_to_show_non_method_users=(
            "narrative report for clinicians, data stewards, or protocol teams",
            "summary card that highlights irregularity, burstiness, and reliability caveats",
        ),
        practical_value=(
            "Document why explicit timestamps must be preserved.",
            "Flag when event bursts dominate over smooth trends.",
        ),
    ),
    CaseStudy(
        key="resting_state_fmri",
        title="Resting-state or task fMRI cohort",
        domains=("fmri", "neuro"),
        audiences=("general", "neuroscience", "cross-disciplinary"),
        environments=("notebook", "python_script", "neuro_stack", "ml_benchmark"),
        why_people_care="fMRI is a flagship scientific time-series setting where multivariate coupling and cohort heterogeneity matter as much as single-node signals.",
        typical_data="Subject × time × ROI matrices, network labels, resting-state or task blocks, and cohort-level comparisons.",
        common_questions=(
            "How networked is the dataset?",
            "How much do subjects differ in temporal organization?",
            "Should models be framed as multivariate/network-aware rather than independent ROI series?",
        ),
        where_echotime_helps="It turns networked temporal structure into a dataset card that non-method collaborators can actually read.",
        recommended_entrypoints=(
            "profile_dataset(FMRIInput(...))",
            "profile.to_summary_card_markdown()",
            "profile.to_narrative_report()",
        ),
        what_to_show_non_method_users=(
            "plain-language summary of coupling, heterogeneity, and rhythmic low-frequency structure",
            "narrative report suitable for supplements, preregistration, or lab onboarding",
        ),
        practical_value=(
            "Communicate why multivariate structure cannot be ignored.",
            "Summarize cohort-level differences before benchmarking new models.",
        ),
    ),
)


def case_gallery_dict(*, domain: str | None = None, audience: str | None = None, environment: str | None = None) -> dict[str, Any]:
    chosen = []
    domain_norm = None if domain is None else domain.lower()
    audience_norm = None if audience is None else audience.lower()
    environment_norm = None if environment is None else environment.lower()
    for case in CASES:
        if domain_norm is not None and domain_norm not in {d.lower() for d in case.domains}:
            continue
        if audience_norm is not None and audience_norm not in {a.lower() for a in case.audiences}:
            continue
        if environment_norm is not None and environment_norm not in {e.lower() for e in case.environments}:
            continue
        chosen.append(asdict(case))
    return {
        "package": "echotime",
        "filters": {"domain": domain, "audience": audience, "environment": environment},
        "cases": chosen,
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = ["# EchoTime case gallery", "", "These are high-visibility, cross-disciplinary time-series cases where EchoTime is meant to be useful.", ""]
    active = {k: v for k, v in payload["filters"].items() if v is not None}
    if active:
        lines.append(f"**filters:** {active}")
        lines.append("")
    if not payload["cases"]:
        lines.append("No case matched the requested filters.")
        return "\n".join(lines)
    for case in payload["cases"]:
        lines.extend([
            f"## {case['title']}",
            "",
            f"**case key:** `{case['key']}`  ",
            f"**domains:** {', '.join(case['domains'])}  ",
            f"**audiences:** {', '.join(case['audiences'])}  ",
            f"**environments:** {', '.join(case['environments'])}",
            "",
            f"**Why people care:** {case['why_people_care']}",
            "",
            f"**Typical data:** {case['typical_data']}",
            "",
            "**Common questions:**",
            "",
        ])
        for item in case["common_questions"]:
            lines.append(f"- {item}")
        lines.extend(["", f"**Where EchoTime helps:** {case['where_echotime_helps']}", "", "**Recommended entrypoints:**", ""])
        for item in case["recommended_entrypoints"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "**What to show non-method users:**", ""])
        for item in case["what_to_show_non_method_users"]:
            lines.append(f"- {item}")
        lines.extend(["", "**Practical value:**", ""])
        for item in case["practical_value"]:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def case_gallery(*, domain: str | None = None, audience: str | None = None, environment: str | None = None, format: GuideFormat = "markdown") -> str:
    payload = case_gallery_dict(domain=domain, audience=audience, environment=environment)
    if format == "json":
        return json.dumps(payload, indent=2)
    markdown = _render_markdown(payload)
    if format == "text":
        return markdown
    return markdown
