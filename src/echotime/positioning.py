"""Ecosystem positioning, capability coverage, and agent-facing routing guides.

This module makes echotime's scope explicit relative to nearby time-series
packages. The goal is not to claim that echotime replaces forecasting,
classification, DTW, or matrix-profile libraries; it is to help users and
agents choose the right first tool and understand when echotime should be
used before, with, or after the rest of the ecosystem.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

GuideFormat = Literal["markdown", "text", "json", "object"]


@dataclass(frozen=True, slots=True)
class EcosystemEntry:
    name: str
    family: str
    official_positioning: str
    strongest_for: tuple[str, ...]
    echotime_relation: str
    choose_it_when: str
    pairing_pattern: str
    source_label: str
    source_url: str


@dataclass(frozen=True, slots=True)
class CoverageRow:
    capability: str
    echotime_role: str
    best_companions: tuple[str, ...]
    notes: str


@dataclass(frozen=True, slots=True)
class ToolingRoute:
    detected_task: str
    confidence: str
    primary_packages: tuple[str, ...]
    echotime_role: str
    first_step: str
    next_steps: tuple[str, ...]
    caution: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        lines = [
            "# EchoTime tooling route",
            "",
            f"**detected task:** {self.detected_task}",
            f"**confidence:** {self.confidence}",
            f"**primary packages:** {', '.join(self.primary_packages)}",
            "",
            "## EchoTime's role",
            "",
            self.echotime_role,
            "",
            "## Recommended first step",
            "",
            self.first_step,
            "",
            "## Recommended next steps",
            "",
        ]
        for item in self.next_steps:
            lines.append(f"- {item}")
        lines.extend(["", "## Caution", "", self.caution])
        return "\n".join(lines)


ECOSYSTEM_ENTRIES: tuple[EcosystemEntry, ...] = (
    EcosystemEntry(
        name="tsfresh",
        family="feature extraction",
        official_positioning=(
            "Automatically calculates a large number of time-series characteristics and includes methods to evaluate their explaining power for regression or classification tasks."
        ),
        strongest_for=(
            "large handcrafted feature extraction",
            "feature filtering",
            "series-as-features pipelines",
        ),
        echotime_relation=(
            "EchoTime is not a feature-zoo replacement; it is dataset-first structural profiling. Use echotime when the first question is 'what kind of temporal dataset is this?' and tsfresh when you need a broad handcrafted feature matrix for downstream supervised learning."
        ),
        choose_it_when=(
            "Choose tsfresh first when your immediate output needs to be a wide feature table for classification or regression."
        ),
        pairing_pattern=(
            "Run echotime before tsfresh to characterize the dataset, document benchmark structure, and produce a human-readable summary; then run tsfresh if you still need engineered features."
        ),
        source_label="tsfresh docs",
        source_url="https://tsfresh.readthedocs.io/en/latest/",
    ),
    EcosystemEntry(
        name="aeon",
        family="time-series machine learning toolkit",
        official_positioning=(
            "A scikit-learn compatible toolkit for time-series tasks such as forecasting, classification, regression, clustering, anomaly detection, similarity search, and benchmarking."
        ),
        strongest_for=(
            "estimators and pipelines",
            "benchmarking",
            "forecasting / classification / regression / clustering",
            "similarity search",
        ),
        echotime_relation=(
            "echotime sits earlier in the workflow: dataset characterization, ontology axes, summary cards, and compact context for collaborators or agents. aeon is the modelling-and-evaluation toolbox you use once you already know what sort of problem you have."
        ),
        choose_it_when=(
            "Choose aeon first when you need estimators, benchmarking, or algorithm comparison across time-series ML tasks."
        ),
        pairing_pattern=(
            "Use echotime before aeon in benchmark curation or cross-domain work, then pass the profiled dataset into aeon for modelling and evaluation."
        ),
        source_label="aeon docs",
        source_url="https://www.aeon-toolkit.org/en/v0.9.0/",
    ),
    EcosystemEntry(
        name="sktime",
        family="unified time-series ML framework",
        official_positioning=(
            "A unified toolbox for machine learning with time series, including algorithms, transformations, pipelining, tuning, ensembling, and forecasting/classification workflows."
        ),
        strongest_for=(
            "forecasting pipelines",
            "composite estimators",
            "time-series transformations",
            "evaluation and tuning",
        ),
        echotime_relation=(
            "EchoTime is for structural triage, communication, and dataset cards; sktime is for building, tuning, and evaluating models."
        ),
        choose_it_when=(
            "Choose sktime first when your main question is how to build or tune a forecasting or time-series ML pipeline."
        ),
        pairing_pattern=(
            "Use echotime to audit dataset structure and produce a shareable summary before handing the data to sktime pipelines."
        ),
        source_label="sktime docs",
        source_url="https://www.sktime.net/en/stable/user_guide/introduction.html",
    ),
    EcosystemEntry(
        name="tslearn",
        family="time-series ML toolkit",
        official_positioning=(
            "A Python package that provides machine-learning tools for the analysis of time series."
        ),
        strongest_for=(
            "time-series clustering",
            "classification and regression",
            "distance-based learning",
        ),
        echotime_relation=(
            "EchoTime is not primarily a learner library. It focuses on understanding and comparing datasets before or beside modelling, while tslearn focuses on machine-learning algorithms over time-series objects."
        ),
        choose_it_when=(
            "Choose tslearn first when the main task is clustering, classification, or regression on time-series arrays."
        ),
        pairing_pattern=(
            "Use echotime to understand structure and heterogeneity, then tslearn if you need distance-aware learning or clustering."
        ),
        source_label="tslearn docs",
        source_url="https://tslearn.readthedocs.io/en/stable/",
    ),
    EcosystemEntry(
        name="DTAIDistance",
        family="distance / alignment",
        official_positioning=(
            "A library for time-series distances such as Dynamic Time Warping, with Python and faster C-backed implementations."
        ),
        strongest_for=(
            "DTW distance",
            "alignment paths",
            "pairwise distance matrices",
            "distance-based clustering",
        ),
        echotime_relation=(
            "echotime does include high-level similarity summaries, but it is not a dedicated DTW engine. Use DTAIDistance when alignment paths, distance matrices, or lower-level DTW controls are the main deliverable."
        ),
        choose_it_when=(
            "Choose DTAIDistance first when you need exact or scalable DTW-oriented distance computation."
        ),
        pairing_pattern=(
            "Use echotime when you need an interpretable similarity story and dataset card; use DTAIDistance when you need the alignment machinery itself."
        ),
        source_label="DTAIDistance docs",
        source_url="https://dtaidistance.readthedocs.io/en/latest/",
    ),
    EcosystemEntry(
        name="STUMPY",
        family="matrix profile / subsequence mining",
        official_positioning=(
            "Efficiently computes the matrix profile, a representation built from nearest-neighbor distances among subsequences within a time series."
        ),
        strongest_for=(
            "motif discovery",
            "subsequence anomaly search",
            "matrix-profile workflows",
        ),
        echotime_relation=(
            "EchoTime is not a matrix-profile or subsequence-mining library. It helps you profile whole datasets and summarize temporal structure at the dataset or pairwise-comparison level."
        ),
        choose_it_when=(
            "Choose STUMPY first when the question is about repeated motifs, discords, or subsequence nearest neighbors."
        ),
        pairing_pattern=(
            "Use echotime first to explain whether a dataset is regime-switching, bursty, or rhythmic; then use STUMPY for subsequence-level motif or anomaly mining."
        ),
        source_label="STUMPY docs",
        source_url="https://stumpy.readthedocs.io/en/latest/Tutorial_The_Matrix_Profile.html",
    ),
    EcosystemEntry(
        name="Darts",
        family="forecasting / anomaly detection",
        official_positioning=(
            "A user-friendly library for forecasting and anomaly detection on time series, with classical and deep models under a common fit/predict interface."
        ),
        strongest_for=(
            "forecasting models",
            "backtesting",
            "anomaly detection",
            "probabilistic forecasting",
        ),
        echotime_relation=(
            "echotime does not train forecasting models. It helps decide whether the data look trend-dominant, rhythmic, bursty, nonstationary, heterogeneous, or irregular before forecasting choices are made."
        ),
        choose_it_when=(
            "Choose Darts first when the main output is a forecasting or anomaly-detection model."
        ),
        pairing_pattern=(
            "Use echotime before Darts to characterize the dataset, explain modelling difficulty to non-specialists, and attach a dataset card to the forecasting project."
        ),
        source_label="Darts docs",
        source_url="https://unit8co.github.io/darts/",
    ),
    EcosystemEntry(
        name="Kats",
        family="general time-series analysis toolkit",
        official_positioning=(
            "A one-stop shop for time-series analysis including detection, forecasting, TSFeatures, multivariate analysis, and utilities."
        ),
        strongest_for=(
            "forecasting",
            "detection",
            "TSFeatures",
            "general-purpose analysis workflows",
        ),
        echotime_relation=(
            "Kats spans multiple analysis tasks; EchoTime is narrower and more explicit about dataset ontology, structural profiling, agent context, and plain-language dataset reports."
        ),
        choose_it_when=(
            "Choose Kats first when you want one toolkit that already includes forecasting, detection, and TSFeatures under one roof."
        ),
        pairing_pattern=(
            "Use echotime when dataset profiling, structural similarity, or human-readable dataset cards are the missing layer around a Kats workflow."
        ),
        source_label="Kats docs",
        source_url="https://facebookresearch.github.io/Kats/",
    ),
)


COVERAGE_ROWS: tuple[CoverageRow, ...] = (
    CoverageRow(
        capability="Dataset-first structural profiling",
        echotime_role="Primary",
        best_companions=(),
        notes="echotime's main job is to turn a dataset into ontology axes, archetypes, reliability summaries, and task hints.",
    ),
    CoverageRow(
        capability="Dataset card JSON / Markdown",
        echotime_role="Primary",
        best_companions=(),
        notes="Useful for benchmark curation, cross-team handoff, and plain-language documentation.",
    ),
    CoverageRow(
        capability="Plain-language summary card and narrative report",
        echotime_role="Primary",
        best_companions=(),
        notes="Built for non-method collaborators, dataset owners, and cross-disciplinary teams.",
    ),
    CoverageRow(
        capability="Explicit agent-driving and compact context",
        echotime_role="Primary",
        best_companions=(),
        notes="Helps an LLM or agent choose a lean path and emit a compact reusable context bundle.",
    ),
    CoverageRow(
        capability="Raw feature extraction matrix",
        echotime_role="Complementary",
        best_companions=("tsfresh", "Kats TSFeatures"),
        notes="echotime intentionally avoids becoming a giant feature zoo.",
    ),
    CoverageRow(
        capability="Forecasting models and backtesting",
        echotime_role="Out of scope",
        best_companions=("Darts", "sktime", "aeon", "Kats"),
        notes="Use echotime before or beside forecasting, not instead of it.",
    ),
    CoverageRow(
        capability="Classification / regression / clustering estimators",
        echotime_role="Out of scope",
        best_companions=("aeon", "tslearn", "sktime"),
        notes="echotime profiles datasets and compares trajectories; it does not train supervised estimators.",
    ),
    CoverageRow(
        capability="DTW engine and alignment paths",
        echotime_role="Complementary",
        best_companions=("DTAIDistance",),
        notes="echotime surfaces similarity summaries; DTAIDistance is for distance computation and warping control.",
    ),
    CoverageRow(
        capability="Subsequence motif discovery / matrix profile",
        echotime_role="Out of scope",
        best_companions=("STUMPY",),
        notes="echotime works at dataset and whole-series levels, not matrix-profile subsequence mining.",
    ),
    CoverageRow(
        capability="Irregular, event-stream, and longitudinal typed wrappers",
        echotime_role="Primary",
        best_companions=("pandas", "xarray", "MNE", "nilearn", "clinical ETL pipelines"),
        notes="The goal is to preserve observation semantics before analysis rather than silently flattening them away.",
    ),
)


AGENT_MANIFEST: dict[str, Any] = {
    "name": "echotime",
    "positioning": "dataset-first structural profiling and similarity triage for time-series data",
    "good_for": [
        "profile a dataset before model selection",
        "compare two curves and decide whether they are similar enough to discuss together",
        "write dataset cards, summary cards, and narrative reports",
        "compress results into a compact context bundle for a downstream LLM step",
        "handle dense arrays, irregular observations, event streams, longitudinal tables, and neuro-style wrappers",
    ],
    "not_for": [
        "training forecasting models",
        "training classification, clustering, or regression estimators",
        "serving as a full DTW or matrix-profile engine",
        "replacing domain libraries such as MNE, nilearn, pandas, xarray, Darts, aeon, or sktime",
    ],
    "routing_policy": {
        "profile_or_document_dataset": "use profile_dataset first",
        "compare_two_whole_curves": "use compare_series first; upgrade to compare_profiles only if structure matters or raw similarity is ambiguous",
        "need_a_compact_llm_context": "use AgentDriver or agent_drive",
        "need_forecasting": "pair echotime with Darts, sktime, aeon, or Kats",
        "need_feature_matrix": "pair echotime with tsfresh or Kats TSFeatures",
        "need_dtw_paths": "pair echotime with DTAIDistance",
        "need_motifs_or_discords": "pair echotime with STUMPY",
    },
    "budget_paths": {
        "lean": [
            "profile_dataset or compare_series",
            "summary card or compact context only",
            "stop early if the signal is already clear",
        ],
        "balanced": [
            "profile_dataset or compare_series",
            "upgrade to compare_profiles if helpful",
            "export narrative report or dataset card",
        ],
        "deep": [
            "run profile_dataset and compare_profiles when relevant",
            "use rolling_similarity for regime-sensitive comparisons",
            "export both machine-readable card and human-readable report",
        ],
    },
    "signature_outputs": [
        "ontology axes and subdimensions",
        "archetypes",
        "reliability summaries",
        "plain-language summary card",
        "narrative report",
        "compact agent context",
    ],
}


def _task_category(task: str) -> tuple[str, str]:
    text = (task or "").strip().lower()
    if not text:
        return "dataset_profiling", "medium"
    keyword_groups = [
        ("dataset_docs", ["dataset card", "summary card", "narrative", "report", "document", "explain dataset"]),
        ("dataset_profiling", ["profile", "characterize", "characterise", "ontology", "structure", "what kind of data"]),
        ("similarity_triage", ["similar", "resemble", "compare", "same kind of curve", "same kind of data", "token", "compact context", "agent"]),
        ("forecasting", ["forecast", "predict next", "horizon", "backtest", "future values", "prediction interval"]),
        ("feature_extraction", ["feature matrix", "extract features", "handcrafted features", "feature selection"]),
        ("classification_clustering_regression", ["classify", "classification", "cluster", "clustering", "regression model", "train model"]),
        ("distance_alignment", ["dtw", "warping", "alignment", "distance matrix"]),
        ("subsequence_motif", ["motif", "discord", "subsequence", "matrix profile", "pattern search"]),
    ]
    for category, keywords in keyword_groups:
        if any(keyword in text for keyword in keywords):
            return category, "high"
    return "dataset_profiling", "low"


def tooling_router(task: str, *, format: GuideFormat = "markdown") -> str | dict[str, Any] | ToolingRoute:
    category, confidence = _task_category(task)
    route_map: dict[str, ToolingRoute] = {
        "dataset_docs": ToolingRoute(
            detected_task="dataset documentation / explanation",
            confidence=confidence,
            primary_packages=("echotime",),
            echotime_role="Primary. This is exactly where EchoTime is strongest: summary cards, narrative reports, dataset cards, and collaborator-facing communication.",
            first_step="Run profile_dataset, then export to_summary_card_markdown(), to_narrative_report(), or to_card_json().",
            next_steps=(
                "Share the summary card with non-method collaborators.",
                "Attach the dataset card JSON to your benchmark or repository.",
                "Use AgentDriver if another LLM step only needs the compact gist.",
            ),
            caution="Do not confuse explanation with modelling; if you need forecasts or classifiers, pair echotime with a modelling library afterward.",
        ),
        "dataset_profiling": ToolingRoute(
            detected_task="dataset structural profiling",
            confidence=confidence,
            primary_packages=("echotime",),
            echotime_role="Primary. EchoTime is built to profile the dataset itself before model selection.",
            first_step="Run profile_dataset on the raw dataset or typed wrapper that best preserves its observation semantics.",
            next_steps=(
                "Inspect axes, archetypes, heterogeneity, and reliability.",
                "Export a dataset card for benchmark or handoff use.",
                "Only after profiling, choose a modelling library if one is needed.",
            ),
            caution="A structural profile is a triage layer, not a trained predictive model.",
        ),
        "similarity_triage": ToolingRoute(
            detected_task="whole-series similarity triage",
            confidence=confidence,
            primary_packages=("echotime", "DTAIDistance (optional)"),
            echotime_role="Primary for interpretable similarity triage and compact reporting; complementary to lower-level DTW tooling when you need alignment control.",
            first_step="Run compare_series first. If the shape result is ambiguous or scales differ, upgrade to compare_profiles or use AgentDriver.",
            next_steps=(
                "Use to_summary_card_markdown() or to_narrative_report() to communicate the comparison.",
                "If you need alignment paths or DTW tuning, hand off to DTAIDistance.",
                "If the relationship changes over time, add rolling_similarity.",
            ),
            caution="echotime compares whole trajectories and profiles; it is not a full subsequence-search or DTW-engine replacement.",
        ),
        "forecasting": ToolingRoute(
            detected_task="forecasting / prediction",
            confidence=confidence,
            primary_packages=("Darts", "sktime", "aeon", "Kats"),
            echotime_role="Optional but useful before modelling. Use EchoTime to audit trendness, rhythmicity, drift, irregularity, and heterogeneity before choosing the forecasting stack.",
            first_step="Pick a forecasting library as the modelling backbone; optionally run echotime first for dataset triage and communication.",
            next_steps=(
                "Use echotime summary cards to explain why the forecasting task may be easy or hard.",
                "Carry echotime dataset cards into benchmark curation or model comparison reports.",
                "Use echotime again after modelling to contextualize failures across datasets.",
            ),
            caution="Do not expect echotime to fit or backtest forecasting models by itself.",
        ),
        "feature_extraction": ToolingRoute(
            detected_task="feature extraction for downstream ML",
            confidence=confidence,
            primary_packages=("tsfresh", "Kats TSFeatures"),
            echotime_role="Complementary. Use EchoTime before or beside feature extraction when you want dataset characterization, structural archetypes, or dataset cards.",
            first_step="Generate the feature matrix with tsfresh or Kats TSFeatures, and use echotime if you also need a dataset-level structural summary.",
            next_steps=(
                "Attach echotime summary cards to explain the feature-extraction project to collaborators.",
                "Use echotime heterogeneity and reliability outputs to contextualize model performance.",
            ),
            caution="echotime intentionally avoids becoming another giant feature-zoo package.",
        ),
        "classification_clustering_regression": ToolingRoute(
            detected_task="time-series ML estimators",
            confidence=confidence,
            primary_packages=("aeon", "tslearn", "sktime"),
            echotime_role="Optional but useful before benchmark design or cross-domain dataset selection.",
            first_step="Use a modelling toolkit for estimator training; optionally profile datasets with echotime first.",
            next_steps=(
                "Use echotime to compare whether two benchmarks are structurally similar.",
                "Use dataset cards to document training datasets and cohorts.",
            ),
            caution="echotime does not train classification, clustering, or regression models.",
        ),
        "distance_alignment": ToolingRoute(
            detected_task="DTW / alignment / distance computation",
            confidence=confidence,
            primary_packages=("DTAIDistance",),
            echotime_role="Complementary. Use EchoTime only if you also want an interpretable comparison story or a structural profile around the aligned series.",
            first_step="Use DTAIDistance or another distance library for the alignment computation itself.",
            next_steps=(
                "Bring the aligned or compared series back into echotime if you want a narrative report or summary card.",
            ),
            caution="EchoTime is not designed to expose the full DTW parameter surface or alignment paths.",
        ),
        "subsequence_motif": ToolingRoute(
            detected_task="motif / discord / subsequence search",
            confidence=confidence,
            primary_packages=("STUMPY",),
            echotime_role="Complementary. Use EchoTime for dataset context, not for matrix-profile computations.",
            first_step="Use STUMPY or another matrix-profile library for subsequence mining.",
            next_steps=(
                "Use echotime to explain dataset-level burstiness, rhythmicity, or regime switching around the subsequence results.",
            ),
            caution="echotime works at the whole-series and dataset levels, not motif-discovery scale.",
        ),
    }
    route = route_map[category]
    if format == "json":
        return route.to_dict()
    if format == "object":
        return route
    if format == "text":
        return route.to_markdown().replace("# EchoTime tooling route\n\n", "")
    return route.to_markdown()



_REFERENCE_NOTE = (
    "Positioning notes below are based on official documentation pages consulted on 2026-03-08. "
    "They describe what the packages publicly emphasize, not every edge capability they may contain."
)


def ecosystem_positioning(*, format: GuideFormat = "markdown") -> str | dict[str, Any]:
    if format == "json":
        return {
            "note": _REFERENCE_NOTE,
            "entries": [asdict(entry) for entry in ECOSYSTEM_ENTRIES],
        }
    lines = [
        "# EchoTime in the time-series Python ecosystem",
        "",
        _REFERENCE_NOTE,
        "",
        "EchoTime is **dataset-first**. It profiles, compares, and explains time-series datasets before or beside modelling. It does not try to replace the forecasting, estimator, DTW, or matrix-profile libraries that already do those jobs well.",
        "",
        "## Honest positioning",
        "",
        "| package | official emphasis | strongest fit | how echotime relates |",
        "|---|---|---|---|",
    ]
    for entry in ECOSYSTEM_ENTRIES:
        strongest = ", ".join(entry.strongest_for)
        lines.append(
            f"| {entry.name} | {entry.official_positioning} | {strongest} | {entry.echotime_relation} |"
        )
    lines.extend([
        "",
        "## When to choose echotime first",
        "",
        "- You need to understand **what kind of temporal dataset** you have before selecting a modelling stack.",
        "- You need a **dataset card**, **summary card**, or **narrative report** for non-method collaborators.",
        "- You want to compare two curves or two datasets and keep the result interpretable.",
        "- You want an **agent-friendly**, compact, low-token intermediate representation of the result.",
        "",
        "## When echotime should be paired with other libraries",
        "",
        "- Pair with **tsfresh** or **Kats TSFeatures** when you need a wide handcrafted feature matrix.",
        "- Pair with **aeon**, **sktime**, or **tslearn** when you need estimators, pipelines, benchmarking, clustering, or supervised learning.",
        "- Pair with **Darts**, **aeon**, **sktime**, or **Kats** when the main job is forecasting or anomaly detection.",
        "- Pair with **DTAIDistance** for explicit DTW distance matrices or alignment paths.",
        "- Pair with **STUMPY** for motif, discord, or matrix-profile workflows.",
        "",
        "## Sources consulted",
        "",
    ])
    for entry in ECOSYSTEM_ENTRIES:
        lines.append(f"- {entry.name}: {entry.source_label} — {entry.source_url}")
    return "\n".join(lines)


def coverage_matrix(*, format: GuideFormat = "markdown") -> str | dict[str, Any]:
    if format == "json":
        return {
            "note": "Primary means EchoTime is a first-class solution. Complementary means echotime can help but another package usually does the heavy lifting. Out of scope means the job should be handed to another package family.",
            "rows": [asdict(row) for row in COVERAGE_ROWS],
        }
    lines = [
        "# EchoTime capability coverage",
        "",
        "Primary means EchoTime is a first-class solution. Complementary means echotime helps but another package usually does the heavy lifting. Out of scope means the job should be handed to another package family.",
        "",
        "| capability | echotime role | best companion packages | notes |",
        "|---|---|---|---|",
    ]
    for row in COVERAGE_ROWS:
        companions = ", ".join(row.best_companions) if row.best_companions else "—"
        lines.append(f"| {row.capability} | {row.echotime_role} | {companions} | {row.notes} |")
    return "\n".join(lines)


def agent_manifest(*, format: GuideFormat = "json") -> str | dict[str, Any]:
    if format == "json":
        return AGENT_MANIFEST
    lines = [
        "# EchoTime agent manifest",
        "",
        f"**positioning:** {AGENT_MANIFEST['positioning']}",
        "",
        "## Good for",
        "",
    ]
    for item in AGENT_MANIFEST["good_for"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Not for", ""])
    for item in AGENT_MANIFEST["not_for"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Routing policy", ""])
    for key, value in AGENT_MANIFEST["routing_policy"].items():
        lines.append(f"- **{key}:** {value}")
    lines.extend(["", "## Budget paths", ""])
    for key, steps in AGENT_MANIFEST["budget_paths"].items():
        lines.append(f"### {key}")
        for step in steps:
            lines.append(f"- {step}")
        lines.append("")
    lines.append("## Signature outputs")
    lines.append("")
    for item in AGENT_MANIFEST["signature_outputs"]:
        lines.append(f"- {item}")
    text = "\n".join(lines)
    if format == "text":
        return text.replace("# EchoTime agent manifest\n\n", "")
    return text


GITHUB_README_TEMPLATE = """# EchoTime

**Dataset-first structural profiling, similarity triage, and agent-friendly reporting for time-series data.**

`echotime` helps you answer questions that most time-series libraries intentionally leave open:

- What kind of time-series dataset do I actually have?
- Is it rhythmic, bursty, regime-switching, noisy, heterogeneous, irregular, or strongly coupled?
- Do two curves resemble each other only in shape, or are they the same kind of temporal problem?
- How do I explain the dataset to a collaborator who does not want raw metrics?
- If an agent is using this package, what is the **smallest useful workflow** and what **compact context** should be passed to the next step?

It is **not** a forecasting library, not a classifier, not a DTW engine, and not another giant feature-zoo package. It sits **before or beside** modelling.

## Why this exists

Most Python time-series packages are optimized for one of these jobs:

- feature extraction
- forecasting / anomaly detection
- classification / clustering / regression
- DTW distances and alignment
- motif discovery and subsequence mining

Those are all valuable jobs. But cross-disciplinary teams still need a missing layer:

> **dataset characterization and communication**

That is the layer `echotime` targets.

## What you get

- ontology axis scores and subdimensions
- archetype labels
- reliability summaries and evidence
- dataset card JSON / Markdown
- plain-language summary cards
- narrative reports
- raw-series and profile-level similarity reports
- compact agent context bundles

## Core entry points

```python
from echotime import profile_dataset, compare_series, compare_profiles, AgentDriver

profile = profile_dataset(data, domain="traffic")
print(profile.to_summary_card_markdown())

series_report = compare_series(series_a, series_b, left_name="Repo A", right_name="Repo B")
print(series_report.to_narrative_report())

profile_report = compare_profiles(dataset_a, dataset_b)
print(profile_report.to_markdown())

driver = AgentDriver(
    goal="Decide whether these two curves are similar and keep the answer compact",
    budget="lean",
)
result = driver.run(series_a, series_b)
print(result.to_context_markdown())
```

## Ecosystem positioning

The notes below are based on official documentation pages consulted on 2026-03-08. They summarize what the packages publicly emphasize; they are not meant to erase edge cases or advanced extensions.

| Package family | What the official docs emphasize | Where EchoTime fits |
|---|---|---|
| **tsfresh** | automatic extraction of many time-series characteristics plus feature relevance for regression/classification | use echotime when the first need is dataset profiling, dataset cards, or collaborator-facing summaries; pair with tsfresh when you need a wide handcrafted feature matrix |
| **aeon** | scikit-learn-compatible time-series ML toolkit for forecasting, classification, regression, clustering, anomaly detection, similarity search, and benchmarking | use echotime before aeon when you want to characterize the dataset or benchmark before estimator work |
| **sktime** | unified toolbox for machine learning with time series, including transformations, pipelines, tuning, and forecasting/classification workflows | use echotime for structural triage and documentation, then sktime for modelling workflows |
| **tslearn** | machine-learning tools for time-series analysis | use echotime for dataset-level understanding and tslearn for learning algorithms |
| **DTAIDistance** | DTW distances and alignment-focused tooling | use echotime for interpretable similarity triage, DTAIDistance for alignment machinery |
| **STUMPY** | matrix-profile-based subsequence nearest-neighbor, motif, and discord workflows | use echotime for whole-dataset context, STUMPY for subsequence mining |
| **Darts / Kats** | forecasting, anomaly detection, and broader time-series analysis workflows | use echotime before or beside forecasting when you need a structural audit and a shareable dataset story |

## Honest scope

**EchoTime is primary for:**

- dataset-first structural profiling
- dataset card generation
- summary cards and narrative reports
- interpretable curve-to-curve similarity triage
- agent-facing compact context outputs
- irregular / event-stream / longitudinal wrappers that preserve observation semantics

**EchoTime is complementary for:**

- feature extraction pipelines
- forecasting projects
- estimator benchmarking
- DTW alignment workflows

**EchoTime is out of scope for:**

- training forecasting models
- training classification / clustering / regression estimators
- acting as a full DTW engine
- acting as a matrix-profile or motif-discovery engine

## Agent-friendly by design

`echotime` includes an explicit agent-driving layer so an LLM does not have to spend tokens rediscovering the same workflow each time.

```python
from echotime import agent_manifest, tooling_router, AgentDriver

print(agent_manifest(format="json"))
print(tooling_router("forecast the next 14 days", format="markdown"))

result = AgentDriver(
    goal="Decide whether repo A resembles repo B and keep the answer compact",
    budget="lean",
).run(series_a, series_b)
```

The design goal is simple:

- start with the cheapest informative move
- stop early when the signal is already clear
- emit a compact reusable context bundle
- avoid recomputing heavy steps just to write a report

## Use cases that play well on GitHub, in blogs, and in demos

- GitHub project stars over time
- product launch traffic and signup curves
- BTC / gold / oil price trajectories
- energy load curves
- wearable longitudinal monitoring
- clinical irregular monitoring
- fMRI / EEG cohort summaries

## Installation

```bash
pip install echotime
```

Or, for local artifacts produced in a release workflow:

```bash
pip install echotime-0.17.1-py3-none-any.whl
```

## CLI

```bash
echotime my_data.npy --format summary-card --domain traffic

echotime left.npy --reference right.npy --format similarity-summary

echotime --guide ecosystem

echotime --guide coverage

echotime --guide github-readme > README.generated.md
```

## Project philosophy

`echotime` is designed for the space between **raw data** and **task models**:

```text
raw dataset
  -> echotime profile / similarity / summary / compact context
  -> modelling stack (aeon / sktime / Darts / tslearn / tsfresh / STUMPY / DTAIDistance / Kats)
  -> downstream evaluation and communication
```

## Sources consulted for the ecosystem table

- tsfresh docs — https://tsfresh.readthedocs.io/en/latest/
- aeon docs — https://www.aeon-toolkit.org/en/v0.9.0/
- sktime docs — https://www.sktime.net/en/stable/user_guide/introduction.html
- tslearn docs — https://tslearn.readthedocs.io/en/stable/
- DTAIDistance docs — https://dtaidistance.readthedocs.io/en/latest/
- STUMPY docs — https://stumpy.readthedocs.io/en/latest/Tutorial_The_Matrix_Profile.html
- Darts docs — https://unit8co.github.io/darts/
- Kats docs — https://facebookresearch.github.io/Kats/
"""


def github_readme(*, format: GuideFormat = "markdown") -> str | dict[str, Any]:
    from .repo_docs import github_readme as _github_readme
    return _github_readme(format=format)
