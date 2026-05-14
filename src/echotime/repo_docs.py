"""GitHub-first documentation strings for EchoTime v0.17.0."""

from __future__ import annotations

import json
from typing import Literal

from .agent_tools import mcp_tool_descriptors, openai_function_schemas, tool_schemas
from .copydeck import (
    AGENT_HEADING,
    AUTHOR_AFFILIATION,
    AUTHOR_EMAIL,
    AUTHOR_NAME,
    BENCHMARK_HEADING,
    BEGINNER_EXAMPLES,
    CORE_CAPABILITIES,
    COVERAGE_HEADING,
    DISPLAY_NAME,
    ECOSYSTEM_HEADING,
    FLAGSHIP_DEMOS,
    HEADLINE,
    INTEGRATIONS,
    PACKAGE_STAGE,
    PACKAGE_VERSION,
    PAGES_HEADING,
    PLAYGROUND_HEADING,
    PROJECT_DOCUMENTATION_URL,
    PROJECT_REPOSITORY_URL,
    START_HERE_HEADING,
    DOCTOR_HEADING,
    PRODUCT_PROMISE,
    QUICKSTART_EXPECTED_LINES,
    QUICKSTART_INSTALL,
    QUICKSTART_ONE_LINER,
    README_BADGES,
    STARTER_SCENARIOS,
    TAGLINE,
    TRUST_HEADING,
    ZERO_INSTALL_OPTIONS,
)
from .datasets import list_starter_datasets
from .positioning import coverage_matrix, ecosystem_positioning
from .doctor import environment_doctor

GuideFormat = Literal["markdown", "text", "json"]


def _render(payload: dict, *, title: str, bullets_key: str | None = None) -> str:
    lines = [f"# {title}", ""]
    if "summary" in payload:
        lines += [payload["summary"], ""]
    if bullets_key and bullets_key in payload:
        for item in payload[bullets_key]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def quickstart_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "headline": HEADLINE,
        "install": QUICKSTART_INSTALL,
        "one_liner": QUICKSTART_ONE_LINER,
        "expected_lines": list(QUICKSTART_EXPECTED_LINES),
    }
    if format == "json":
        return payload
    lines = [
        "# 60-second quickstart",
        "",
        payload["headline"],
        "",
        "```bash",
        payload["install"],
        payload["one_liner"],
        "```",
        "",
        "Expected output starts like this:",
        "",
        "```text",
        *payload["expected_lines"],
        "```",
    ]
    return "\n".join(lines)


def installation_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "summary": "Installation is intentionally minimal, but older scientific Python environments can still surface resolver noise.",
        "advice": [
            "Use a fresh environment when possible. aeon/sktime/numba ecosystems can produce resolver warnings even when echotime itself installs correctly.",
            "Core install stays intentionally small: numpy and scipy.",
            "For tabular IO use echotime[io]. For parquet support use echotime[parquet].",
            "For mixed scientific stacks, export a compatibility preset and install with constraints instead of doing a bare install.",
            "If you only want to evaluate product value first, use the static playground or starter notebooks before integrating into a larger stack.",
            "Zero-install and low-friction entry points in this version: static playground, local live demo server, Colab notebook, and uvx CLI pattern.",
        ],
    }
    if format == "json":
        return payload
    return _render(payload, title="Installation notes", bullets_key="advice")


def zero_install_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "summary": "Four ways to try the product surface before committing to a full environment install.",
        "options": [
            f"{item['title']}: {item['why']}" for item in ZERO_INSTALL_OPTIONS
        ],
        "examples": [
            "Open docs/index.html or playground.html locally to inspect the report layer without Python.",
            "Run `echotime-demo --open-browser` to launch the local live demo with pasted arrays and starter cases.",
            "Open examples/notebooks/11_colab_quickstart.ipynb in Colab or another hosted notebook service.",
            "Use `uvx --from echotime echotime --guide quickstart` when you want an ephemeral CLI path.",
        ],
    }
    if format == "json":
        return payload
    lines = ["# Zero-install and low-friction entry points", "", payload["summary"], "", "## Options", ""]
    lines += [f"- {item}" for item in payload["options"]]
    lines += ["", "## Example commands", ""]
    lines += [f"- {item}" for item in payload["examples"]]
    return "\n".join(lines)


def pages_deploy_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "summary": "This repository now ships a GitHub Pages-ready static site bundle and workflow files. Deployment itself still happens in your GitHub repository, not inside the Python package.",
        "steps": [
            "Push the repo with docs/ and .github/workflows/pages.yml included.",
            "Enable GitHub Pages in the repository settings or rely on the workflow to publish the docs bundle.",
            "Set the README live-demo link to the published Pages URL once the first deployment succeeds.",
            "Use docs/playground.html as the product demo landing page if you want a tighter viral loop than the full docs homepage.",
        ],
    }
    if format == "json":
        return payload
    return _render(payload, title=PAGES_HEADING, bullets_key="steps")


def trust_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "stage": PACKAGE_STAGE,
        "artifacts": [
            "LICENSE",
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            "CITATION.cff",
            "starter datasets",
            "flagship notebooks",
            "beginner notebooks",
            "visual report previews",
            "GitHub Pages-ready demo bundle",
            "social cards and GIF assets",
            "stable agent tool schemas",
            "reproducible decision-impact benchmark",
        ],
        "notes": [
            "The report surface and agent wrapper fields are treated as beta-level product surfaces.",
            "Benchmark claims remain deliberately modest; bundled benchmark assets are decision-support evidence, not publication claims.",
        ],
    }
    if format == "json":
        return payload
    lines = [f"# {TRUST_HEADING}", "", f"**status:** {PACKAGE_STAGE}", "", "## Artifacts", ""]
    lines += [f"- {item}" for item in payload["artifacts"]]
    lines += ["", "## Notes", ""]
    lines += [f"- {item}" for item in payload["notes"]]
    return "\n".join(lines)


def starter_datasets_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {"datasets": list_starter_datasets(), "starter_scenarios": list(STARTER_SCENARIOS)}
    if format == "json":
        return payload
    lines = [
        "# Starter datasets",
        "",
        "Small runnable example datasets bundled for notebooks, demos, social cards, and GitHub screenshots.",
        "",
        "| name | domain | kind | why it exists |",
        "|---|---|---|---|",
    ]
    for item in payload["datasets"]:
        lines.append(f"| {item['name']} | {item['domain']} | {item['kind']} | {item['why']} |")
    return "\n".join(lines)


def integration_templates_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "summary": "Copyable templates for bringing your own CSV or DataFrame into EchoTime, then scaling up to tool-calling or MCP when needed.",
        "templates": [
            "pandas notebook template: examples/integrations/pandas_notebook_template.py",
            "OpenAI tool-calling template: examples/integrations/openai_tool_calling_template.py",
            "MCP server template: examples/integrations/mcp_server_template.py",
            "local live demo entry: echotime-demo --open-browser",
        ],
        "notes": [
            "Use the pandas template when you already have a CSV, parquet file, or DataFrame and want the shortest path to a summary card plus HTML report.",
            "For wide tables, keep one `timestamp` column and one or more numeric measurement columns.",
            "For irregular long tables, rename columns to `subject`, `timestamp`, `channel`, and `value` before profiling.",
            "If your file uses different names, rename from aliases such as `time`, `measurement`, `sensor`, and `patient` before calling the API.",
        ],
    }
    if format == "json":
        return payload
    lines = ["# Integration templates", "", payload["summary"], "", "## Templates", ""]
    lines += [f"- {item}" for item in payload["templates"]]
    lines += ["", "## Bring your own data", ""]
    lines += [f"- {item}" for item in payload["notes"]]
    return "\n".join(lines)


def case_studies_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "summary": "This version ships similarity-first decision stories rather than pretending to have independent external case studies.",
        "stories": [
            "GitHub breakout analogs: the comparison separates durable breakouts from short-lived hype curves.",
            "BTC vs gold under shocks: the comparison turns a pairwise market question into a readable macro narrative.",
            "Heatwave vs grid load: the structural context explains why two load regimes should not be treated as interchangeable.",
        ],
    }
    if format == "json":
        return payload
    return _render(payload, title="Decision stories and showcase cases", bullets_key="stories")


def agent_schema_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "tool_schemas": tool_schemas(format="dict"),
        "openai_function_schemas": openai_function_schemas(format="dict"),
        "mcp_tool_descriptors": mcp_tool_descriptors(format="dict"),
    }
    if format == "json":
        return payload
    lines = [
        "# Agent and function-calling schemas",
        "",
        "v0.17.0 exposes a compare-first tool surface that stays callable from outside the package:",
        "",
        "- `ts_profile({data_ref, input_kind, timestamps_ref, domain, budget, audience})`",
        "- `ts_compare({left_ref, right_ref, left_timestamps_ref, right_timestamps_ref, mode, budget})`",
        "- `ts_route({task, available_inputs, has_reference})`",
        "",
        "All three tools return a stable envelope with:",
        "",
        "- `schema_version`",
        "- `tool`",
        "- `ok`",
        "- `input_contract`",
        "- `confidence`",
        "- `limitations`",
        "- `evidence`",
        "- `recommended_next_step`",
        "- `next_actions`",
        "- `error`",
        "",
        "## OpenAI-style function specs",
        "",
        "```json",
        json.dumps(payload["openai_function_schemas"], indent=2),
        "```",
        "",
        "## MCP-style tool descriptors",
        "",
        "```json",
        json.dumps(payload["mcp_tool_descriptors"], indent=2),
        "```",
    ]
    return "\n".join(lines)


def utility_benchmark_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "summary": "The benchmark shipped today is still a decision-impact benchmark, not a full similarity benchmark.",
        "note": "It answers a product question: does the structural report change a modelling decision often enough to matter? The next missing layer is a proper similarity robustness and retrieval benchmark.",
        "artifacts": [
            "benchmarks/decision_impact_benchmark.py",
            "benchmarks/results/decision_impact_benchmark.json",
            "benchmarks/results/decision_impact_benchmark.md",
        ],
    }
    if format == "json":
        return payload
    lines = [f"# {BENCHMARK_HEADING}", "", payload["summary"], "", payload["note"], "", "Artifacts:", ""]
    lines += [f"- {item}" for item in payload["artifacts"]]
    return "\n".join(lines)


def _bring_your_own_data_readme() -> str:
    return """## Use your own data

If you already have a file, start by matching it to one of these shapes:

| your data | what EchoTime expects | first API |
|---|---|---|
| one numeric series | a 1D array or one numeric pandas column | `profile_series(...)` |
| wide table | one `timestamp` column plus one or more numeric columns | `profile_dataset(df, domain=...)` |
| irregular long table | `subject`, `timestamp`, `channel`, `value` columns | `profile_dataset(df, domain=...)` |
| two series to compare | two arrays or two numeric columns | `compare_series(left, right)` |

Tabular inputs are auto-detected from names such as `timestamp` / `time`, `value` / `measurement`, `channel` / `sensor` / `metric`, and `subject` / `patient` / `participant`. If your file uses different names, rename them first. Sparse event tables can also use `timestamp`, `event_type`, `value`, and optional `subject`.

### 1) One CSV column -> first report

```python
from pathlib import Path

import pandas as pd
from echotime import profile_series

df = pd.read_csv("my_signal.csv")
series = pd.to_numeric(df["load_kw"], errors="coerce").dropna().to_numpy()

profile = profile_series(series, domain="energy")
print(profile.to_summary_card_markdown())
Path("my_signal_report.html").write_text(profile.to_html_report(), encoding="utf-8")
```

### 2) Wide DataFrame -> profile your own dataset

```python
from pathlib import Path

import pandas as pd
from echotime import profile_dataset

df = pd.read_csv("my_timeseries.csv")
df = df.rename(columns={"date": "timestamp"})  # only needed if your time column has a different name

profile = profile_dataset(df, domain="energy")
print(profile.to_summary_card_markdown())
Path("my_dataset_report.html").write_text(profile.to_html_report(), encoding="utf-8")
```

All remaining numeric columns are treated as channels or measurements in the same dataset.

### 3) Long irregular table -> keep timestamps honest

```python
from pathlib import Path

import pandas as pd
from echotime import profile_dataset

df = pd.read_csv("patient_vitals.csv")
df = df.rename(columns={
    "patient_id": "subject",
    "charttime": "timestamp",
    "lab_name": "channel",
    "lab_value": "value",
})

profile = profile_dataset(df, domain="clinical")
print(profile.to_summary_card_markdown())
Path("patient_vitals_report.html").write_text(profile.to_html_report(), encoding="utf-8")
```

Each `(subject, channel)` stream can stay irregular; EchoTime keeps the gaps instead of forcing a fake regular grid.

### 4) Compare two columns from your own file

```python
from pathlib import Path

import pandas as pd
from echotime import compare_series

df = pd.read_csv("load_by_region.csv")
report = compare_series(df["north_load_mw"], df["south_load_mw"])
print(report.to_summary_card_markdown())
Path("north_vs_south_similarity.html").write_text(report.to_html_report(), encoding="utf-8")
```

If you want a file you can edit in place, start with `examples/integrations/pandas_notebook_template.py`.
"""


def _bring_your_own_data_pypi() -> str:
    return """## Use your own data

EchoTime is meant to run on real files, not just toy arrays.

- single numeric column -> `profile_series(...)`
- wide table with one `timestamp` column and one or more numeric columns -> `profile_dataset(df, domain=...)`
- irregular long table -> rename columns to `subject`, `timestamp`, `channel`, `value`, then call `profile_dataset(...)`
- two columns to compare -> `compare_series(df["left"], df["right"])`

Tabular inputs are auto-detected from names such as `timestamp` / `time`, `value` / `measurement`, `channel` / `sensor` / `metric`, and `subject` / `patient` / `participant`.

```python
from pathlib import Path

import pandas as pd
from echotime import profile_dataset

df = pd.read_csv("my_timeseries.csv").rename(columns={"date": "timestamp"})
profile = profile_dataset(df, domain="energy")
print(profile.to_summary_card_markdown())
Path("my_dataset_report.html").write_text(profile.to_html_report(), encoding="utf-8")
```
"""


def _project_snapshot_readme() -> str:
    return f"""## Project snapshot

- **Package name:** `echotime`
- **Core promise:** {PRODUCT_PROMISE}
- **Best for:** analog search, regime comparison, irregular longitudinal data, and dataset-level similarity handoff
- **Primary outputs:** plain-English summaries, shareable HTML reports, and compact agent-ready JSON
- **Live docs and homepage:** {PROJECT_DOCUMENTATION_URL}
- **Repository:** {PROJECT_REPOSITORY_URL}
"""


def github_readme(*, format: GuideFormat = "markdown") -> str | dict:
    badges = "\n".join(README_BADGES)
    beginner_lines = "\n".join(f"- **{item['title']}** - {item['why']}" for item in BEGINNER_EXAMPLES)
    flagship_lines = "\n".join(f"- **{item['title']}** - {item['story']}" for item in FLAGSHIP_DEMOS)
    capabilities = "\n".join(f"- {item}" for item in CORE_CAPABILITIES)
    integrations = "\n".join(f"- {item}" for item in INTEGRATIONS)
    zero_install = "\n".join(f"- **{item['title']}** - {item['why']}" for item in ZERO_INSTALL_OPTIONS)
    expected_lines = "\n".join(QUICKSTART_EXPECTED_LINES)
    own_data = _bring_your_own_data_readme()
    project_snapshot = _project_snapshot_readme()
    text = f"""# {DISPLAY_NAME}

> **{HEADLINE}**

{badges}

![Quickstart preview](assets/quickstart.gif)
![EchoTime title card](assets/echotime_title_card.svg)
![Maintainer and affiliation](assets/bham_affiliation_badge.svg)

**EchoTime** is an **explainable time-series similarity package for humans and agents.** It is built for the moment when a raw distance score is not enough: compare trajectories, compare datasets at the structural level, and hand the result to another person or another agent.

**What it is:** {PRODUCT_PROMISE}

**What it is not:** a forecasting library, a classifier library, a fastest-possible DTW engine, or a motif-mining toolkit.

{project_snapshot}

## 60-second quickstart

```bash
{QUICKSTART_INSTALL}
{QUICKSTART_ONE_LINER}
```

Expected output starts like this:

```text
{expected_lines}
```

{own_data}

## Why teams use this before or beside a model

Because many time-series teams do not just need a distance score. They need to know whether two curves are similar enough to compare, whether two datasets are structurally similar enough to transfer intuition, and why the package thinks that.

## What you get right away

{capabilities}

## Low-level elastic shortcuts

The extracted elastic similarity functions now support two operating modes:

- `mode="exact"` keeps the full scoring behavior and remains the default for final reporting.
- `mode="fast"` is for screening and shortlist workflows where speed matters more than exact-path fidelity.
- `edr_distance`, `erp_distance`, and `twed_distance` also accept `window` so you can bound the dynamic-programming path when needed.
- A practical pattern is: run `mode="fast"` across many candidate pairs, then rerun only the shortlist with `mode="exact"` before you publish or defend the result.
- If you already know the alignment should stay local, pass `window=...` so the elastic path does not wander across the whole grid.

## Zero-install and low-friction entry points

{zero_install}

- **GitHub Pages-ready showcase** - open `docs/index.html` or publish the included Pages bundle.
- **Local live demo server** - run `echotime-demo --open-browser` for real similarity analysis on pasted arrays.
- **Local static preview** - open `playground.html` locally and switch between flagship similarity cases.
- **Compatibility presets** - export a constraints file before installing into a mixed scientific stack.

## Beginner examples

{beginner_lines}

## Flagship demos

{flagship_lines}

## Three copy-paste entry points

```python
import numpy as np
from echotime import compare_series, explain_similarity, ts_compare

x = np.sin(np.linspace(0, 8*np.pi, 128))
y = np.sin(np.linspace(0, 8*np.pi, 128) + 0.2)

print(compare_series(x, y).to_summary_card_markdown())
print(explain_similarity(x, y))
print(ts_compare(x, y))
```

## Example outputs in this repo

- [Weekly website traffic HTML report](examples/outputs/weekly_website_traffic_report.html)
- [Irregular patient vitals HTML report](examples/outputs/irregular_patient_vitals_report.html)
- [GitHub breakout similarity HTML report](examples/outputs/github_breakout_similarity.html)
- [BTC vs gold similarity HTML report](examples/outputs/btc_vs_gold_similarity.html)
- [Energy load vs heatwave HTML report](examples/outputs/energy_load_heatwave_report.html)
- [Wearable recovery HTML report](examples/outputs/wearable_recovery_report.html)

## Author

- **Maintainer:** {AUTHOR_NAME}
- **Email:** {AUTHOR_EMAIL}
- **Affiliation:** {AUTHOR_AFFILIATION}
- **Repository:** {PROJECT_REPOSITORY_URL}
- **Documentation:** {PROJECT_DOCUMENTATION_URL}

## Starter datasets, notebooks, and integration templates

- [Starter datasets](STARTER_DATASETS.md)
- [Compatibility guide](COMPATIBILITY.md)
- [Environment doctor](DOCTOR.md)
- [Example gallery](EXAMPLES_GALLERY.md)
- [Similarity method atlas](SIMILARITY_METHOD_ATLAS.md)
- [Notebooks](examples/notebooks)
- [Integration templates](INTEGRATIONS.md)
- [Decision stories](CASE_STUDIES.md)
- [Static playground](playground.html)
- [Local live demo guide](LIVE_DEMO.md)
- [Routing contracts](ROUTING_CONTRACTS.md)

## Agent-ready by design

This version exposes compare-first stable wrappers:

- `ts_profile`
- `ts_compare`
- `ts_route`

All wrappers ship an explicit input contract and a stable success/error envelope. They are meant to be the smallest useful tool surface for function calling, MCP, and multi-agent handoff.

See:

- [Agent schemas](AGENT_SCHEMAS.md)
- [OpenAI function schemas](OPENAI_FUNCTION_SCHEMAS.json)
- [MCP tool descriptors](MCP_TOOL_DESCRIPTORS.json)
- [Agent input contract](AGENT_INPUT_CONTRACT.md)

## Zero-install and deployment docs

- [Zero-install guide](ZERO_INSTALL.md)
- [GitHub Pages deployment](PAGES_DEPLOYMENT.md)
- [Playground guide](PLAYGROUND.md)
- [Local live demo guide](LIVE_DEMO.md)
- [PyPI long description](PYPI_LONG_DESCRIPTION.md)

<!-- Where EchoTime fits in the ecosystem -->
## {ECOSYSTEM_HEADING}

Use EchoTime first when you need **explainable structural similarity and comparison**.

Pair it with other libraries when you move into:

- feature extraction (`tsfresh`)
- forecasting (`Darts`, `sktime`, `aeon`, `Kats`)
- learning pipelines (`aeon`, `sktime`, `tslearn`)
- DTW alignment (`DTAIDistance`)
- motif / discord mining (`STUMPY`)

## Capability coverage

- **Primary:** series similarity, dataset similarity, similarity reports, agent context
- **Complementary:** structural profiling, benchmark curation, modelling handoff
- **Out of scope:** estimator training, backtesting, low-level DTW paths, subsequence mining

## Integrations

{integrations}

## Trust layer

- [LICENSE](LICENSE)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [CITATION.cff](CITATION.cff)
- beta-level agent schemas
- beginner and flagship notebooks
- Pages-ready demo bundle
- social cards and GIFs
- reproducible decision-impact benchmark

## License

MIT.
"""
    if format == "json":
        return {"markdown": text}
    return text


def pypi_long_description(*, format: GuideFormat = "markdown") -> str | dict:
    badges = "\n".join(README_BADGES[:5])
    expected_lines = "\n".join(QUICKSTART_EXPECTED_LINES)
    own_data = _bring_your_own_data_pypi()
    text = f"""# {DISPLAY_NAME}

**{TAGLINE}**

{badges}

{PRODUCT_PROMISE}

## Why this package exists

Most time-series tooling helps after you decide what to model. EchoTime helps one step earlier: compare two signals clearly, compare two datasets structurally, and emit a result that a human or an agent can actually act on.

## Quickstart

```bash
{QUICKSTART_INSTALL}
{QUICKSTART_ONE_LINER}
```

Expected output starts like this:

```text
{expected_lines}
```

{own_data}

## What ships in v0.17.0

- compare-first public package surface
- agent-ready JSON wrappers with stable envelopes
- GitHub Pages-ready docs bundle
- local live demo for pasted arrays
- starter datasets, notebooks, and flagship demos
- compatibility presets and environment doctor guidance for mixed scientific stacks

## Common entry points

- `echotime-demo --open-browser`
- `echotime --guide quickstart`
- `echotime --guide doctor`
- `echotime --export-pages docs`

## Links

- README: `README.md`
- Start here: `START_HERE.md`
- Compatibility: `COMPATIBILITY.md`
- Local live demo: `LIVE_DEMO.md`
- Agent input contract: `AGENT_INPUT_CONTRACT.md`

## Maintainer

- **{AUTHOR_NAME}**
- {AUTHOR_AFFILIATION}
- {AUTHOR_EMAIL}
- {PROJECT_REPOSITORY_URL}

"""
    if format == "json":
        return {"markdown": text}
    return text


def live_demo_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "summary": "Run the local EchoTime live demo when you want a real interactive similarity surface without building a web stack.",
        "commands": [
            "pip install echotime",
            "echotime-demo --open-browser",
            "echotime --serve-demo --open-browser",
            "python -m echotime.demo_server --open-browser",
        ],
        "notes": [
            "The local live demo is compute-backed: pasted arrays and starter cases generate real similarity verdicts and HTML reports.",
            "The GitHub Pages playground stays static and showcase-oriented; use the live demo when you need real computation.",
        ],
    }
    if format == "json":
        return payload
    lines = ["# Local live demo", "", payload["summary"], "", "## Commands", ""]
    lines += [f"- `{item}`" for item in payload["commands"]]
    lines += ["", "## Notes", ""]
    lines += [f"- {item}" for item in payload["notes"]]
    return "\n".join(lines)


def routing_contract_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "summary": "Stable compare-first input contracts for agent tools in v0.17.0.",
        "contracts": [
            "ts_profile({data_ref, input_kind, timestamps_ref, domain, budget, audience})",
            "ts_compare({left_ref, right_ref, left_timestamps_ref, right_timestamps_ref, mode, budget})",
            "ts_route({task, available_inputs, has_reference})",
        ],
        "required_output_fields": [
            "schema_version", "tool", "ok", "input_contract", "artifact_uri", "cost_hint", "input_digest", "cache_key", "confidence", "limitations", "evidence", "recommended_next_step", "next_actions", "error",
        ],
    }
    if format == "json":
        return payload
    lines = ["# Routing and tool contracts", "", payload["summary"], "", "## Stable tool surfaces", ""]
    lines += [f"- `{item}`" for item in payload["contracts"]]
    lines += ["", "## Required output fields", ""]
    lines += [f"- `{item}`" for item in payload["required_output_fields"]]
    return "\n".join(lines)


def start_here_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = {
        "summary": "A single landing point for compare-first quickstart, bringing your own data, zero-install preview, local live demo, environment diagnostics, and GitHub Pages export.",
        "entrypoints": [
            "Open start-here.html or docs/start-here.html to choose the fastest path.",
            "Use the static playground if you only want to inspect similarity demos and visuals.",
            "Run echotime-demo --open-browser when you want real computation on pasted arrays.",
            "Run echotime --guide doctor before installing into a noisy scientific environment.",
            "Run echotime --write-constraints constraints/mixed-scientific-stack.txt --constraint-profile mixed-scientific-stack before installing into a busy scientific stack.",
            "Use echotime --export-pages docs to generate a Pages bundle for GitHub publishing.",
        ],
        "own_data": [
            "Single numeric CSV column: load the column into pandas and call `profile_series(...)` for the fastest first report.",
            "Wide table: keep one `timestamp` column and one or more numeric columns, then call `profile_dataset(df, domain=...)`.",
            "Irregular long table: rename columns to `subject`, `timestamp`, `channel`, and `value`, then call `profile_dataset(df, domain=...)`.",
            "Two columns to compare: call `compare_series(df['left'], df['right'])` and write the HTML report to disk.",
            "If your names differ, rename from aliases such as `time`, `measurement`, `sensor`, and `patient` before calling the API.",
            "Edit `examples/integrations/pandas_notebook_template.py` when you want a concrete file instead of starting from a blank notebook.",
        ],
    }
    if format == "json":
        return payload
    lines = [f"# {START_HERE_HEADING}", "", payload["summary"], "", "## Fast paths", ""]
    lines += [f"- {item}" for item in payload["entrypoints"]]
    lines += ["", "## If you already have your own data", ""]
    lines += [f"- {item}" for item in payload["own_data"]]
    return "\n".join(lines)


def doctor_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = environment_doctor(format="dict")
    if format == "json":
        return payload
    lines = [f"# {DOCTOR_HEADING}", "", payload["summary"], "", "## Watchouts", ""]
    if payload["warnings"]:
        lines += [f"- {item}" for item in payload["warnings"]]
    else:
        lines.append("- No immediate watchouts detected.")
    lines += ["", "## Recommended next steps", ""]
    lines += [f"- {item}" for item in payload["recommended_actions"]]
    return "\n".join(lines)
