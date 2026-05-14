"""Shared product copy and asset promises for EchoTime.

This module keeps the README, homepage, playground, start-here page, and
release artifacts aligned around one public story: compare time series and
time-series datasets with explainable structural similarity.
"""

from __future__ import annotations

DISPLAY_NAME = "EchoTime"
PACKAGE_NAME = "echotime"
PACKAGE_VERSION = "0.17.0"
PACKAGE_STAGE = "Beta"
AUTHOR_NAME = "Zipeng Wu"
AUTHOR_EMAIL = "zxw365@student.bham.ac.uk"
AUTHOR_GITHUB_HANDLE = "ZipengWu365"
AUTHOR_AFFILIATION = "The University of Birmingham"
PROJECT_REPOSITORY_URL = "https://github.com/ZipengWu365/EchoWave"
PROJECT_DOCUMENTATION_URL = "https://zipengwu365.github.io/EchoWave/"
PROJECT_PYPI_URL = "https://pypi.org/project/echotime/"
UNIVERSITY_URL = "https://www.birmingham.ac.uk/"

LIVE_DEMO_HEADING = "Local live demo"

HEADLINE = "Compare time series and datasets with explainable structural similarity."
TAGLINE = "Explainable time-series similarity for humans and agents."
ONE_LINE_VALUE = (
    "Turn two curves or two datasets into a similarity verdict you can hand to"
    " a collaborator, product teammate, researcher, or downstream agent."
)
PRODUCT_PROMISE = (
    "EchoTime compares time series and time-series datasets, explains why"
    " they match or differ, and emits compact JSON plus shareable HTML"
    " reports."
)

QUICKSTART_INSTALL = "pip install echotime"
QUICKSTART_ONE_LINER = (
    'python -c "import numpy as np; from echotime import compare_series; '
    'x=np.sin(np.linspace(0,8*np.pi,128)); '
    'y=np.sin(np.linspace(0,8*np.pi,128)+0.2); '
    'print(compare_series(x,y).to_summary_card_markdown())"'
)
QUICKSTART_EXPECTED_LINES = (
    "# EchoTime similarity summary",
    "overall similarity: ...",
    "top components: shape similarity, trend similarity, spectral similarity",
)

ZERO_INSTALL_OPTIONS = (
    {
        "title": "Static playground",
        "slug": "playground",
        "why": "Preview similarity reports, visuals, and flagship cases without installing Python or starting a server.",
    },
    {
        "title": "Colab quickstart",
        "slug": "colab",
        "why": "Open a starter notebook in a hosted notebook environment.",
    },
    {
        "title": "uvx CLI",
        "slug": "uvx",
        "why": "Run the CLI in an isolated ephemeral environment when packaging allows it.",
    },
    {
        "title": "Local demo server",
        "slug": "local-demo",
        "why": "Run a tiny local web app that turns pasted values into similarity verdicts on your own machine.",
    },
)

CORE_CAPABILITIES = (
    "plain-English similarity summaries",
    "time-series and dataset-level structural comparison",
    "shareable HTML reports with visuals",
    "rolling similarity and component breakdowns",
    "compact agent JSON with stable envelopes",
    "starter datasets, notebooks, and GitHub Pages-ready similarity demos",
    "a local live demo server for pasted arrays and quick comparisons",
    "compatibility presets and environment doctor guidance for mixed scientific stacks",
)

BEGINNER_EXAMPLES = (
    {
        "slug": "single_column_csv_to_report",
        "title": "Single-column CSV -> similarity-ready signal",
        "why": "Show that one numeric column is enough to try the package.",
    },
    {
        "slug": "timestamps_values_irregularity",
        "title": "Timestamps + missingness -> why irregularity matters",
        "why": "Show why explicit timestamps and gaps can change a similarity verdict.",
    },
    {
        "slug": "two_curves_similarity_verdict",
        "title": "Two curves -> similarity verdict",
        "why": "Show the simplest possible similarity workflow without ontology jargon.",
    },
    {
        "slug": "inflation_search_interest",
        "title": "Inflation + search interest -> regime similarity",
        "why": "Show a macro-adjacent beginner case without assuming a finance background.",
    },
    {
        "slug": "single_sensor_drift_watchouts",
        "title": "Single sensor drift -> structural watchouts",
        "why": "Show how slow drift changes what a meaningful analog looks like in engineering data.",
    },
    {
        "slug": "daily_survey_sentiment_irregular",
        "title": "Daily survey sentiment -> irregularity and burstiness",
        "why": "Show how sparse observational signals differ from smooth telemetry.",
    },
)

FLAGSHIP_DEMOS = (
    {
        "slug": "openclaw_breakout_analogs",
        "title": "OpenClaw-style GitHub breakout analogs",
        "story": "Ask whether a new repo looks like a durable breakout or a short viral spike.",
        "social_hook": "Is this a real breakout or just a viral spike?",
    },
    {
        "slug": "btc_gold_oil_shocks",
        "title": "BTC vs gold vs oil under shocks",
        "story": "Ask which assets become more similar during macro or geopolitical stress.",
        "social_hook": "When stress hits, does BTC behave more like gold or oil?",
    },
    {
        "slug": "energy_load_heatwave",
        "title": "Heatwave vs grid load",
        "story": "Ask which load curves drift or switch regime under extreme weather.",
        "social_hook": "Which grid loses structural stability first in a heatwave?",
    },
)

STARTER_SCENARIOS = (
    "sine vs noise",
    "weekly website traffic",
    "irregular patient vitals",
    "GitHub breakout analogs",
    "BTC / gold / oil shocks",
    "energy load vs heatwave",
    "wearable recovery cohort",
)

INTEGRATIONS = (
    "pandas / parquet pipelines",
    "xarray-style data",
    "Jupyter notebooks",
    "CLI batch workflows",
    "OpenAI function calling",
    "MCP tool wrappers",
    "GitHub Pages static showcase",
)

ECOSYSTEM_HEADING = "Where EchoTime fits in the ecosystem"
COVERAGE_HEADING = "Capability coverage"
AGENT_HEADING = "Agent-ready by design"
INSTALL_HEADING = "Install"
PLAYGROUND_HEADING = "Live demo / playground"
TRUST_HEADING = "Trust layer"
PAGES_HEADING = "GitHub Pages-ready similarity demos"
BENCHMARK_HEADING = "Similarity benchmark reality"

START_HERE_HEADING = "Start here"
DOCTOR_HEADING = "Environment doctor"

README_BADGES = (
    f"[![PyPI version](https://img.shields.io/pypi/v/{PACKAGE_NAME}?style=flat-square)]({PROJECT_PYPI_URL})",
    f"[![Python versions](https://img.shields.io/pypi/pyversions/{PACKAGE_NAME}?style=flat-square)]({PROJECT_PYPI_URL})",
    "[![License: MIT](https://img.shields.io/badge/license-MIT-ffc83d?style=flat-square)](LICENSE)",
    f"[![Status: {PACKAGE_STAGE}](https://img.shields.io/badge/status-{PACKAGE_STAGE.lower()}-2f6bff?style=flat-square)]({PROJECT_REPOSITORY_URL})",
    f"[![Docs: GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-2f6bff?style=flat-square)]({PROJECT_DOCUMENTATION_URL})",
    f"[![Author: {AUTHOR_NAME}](https://img.shields.io/badge/author-Zipeng%20Wu-1f2937?style=flat-square)]({PROJECT_REPOSITORY_URL})",
    f"[![Affiliation: The University of Birmingham](https://img.shields.io/badge/The%20University%20of%20Birmingham-academic-a51c30?style=flat-square)]({UNIVERSITY_URL})",
)

HOMEPAGE_PILLS = (
    "MIT License",
    f"{PACKAGE_STAGE} release",
    "Agent tools",
    "GitHub Pages",
    AUTHOR_AFFILIATION,
)
