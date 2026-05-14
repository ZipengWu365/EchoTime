"""Docs-style pages for EchoTime.

These pages separate landing-page content from documentation content, closer
to a scikit-learn-style information architecture: a lightweight homepage and
dedicated tutorial / API / scenario pages with a persistent sidebar.
"""

from __future__ import annotations

from collections import defaultdict
from html import escape
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .agent_tools import TOOL_SCHEMA_VERSION
from .copydeck import (
    AGENT_HEADING,
    AUTHOR_AFFILIATION,
    AUTHOR_EMAIL,
    AUTHOR_NAME,
    BEGINNER_EXAMPLES,
    DISPLAY_NAME,
    ECOSYSTEM_HEADING,
    FLAGSHIP_DEMOS,
    HEADLINE,
    PACKAGE_VERSION,
    PROJECT_DOCUMENTATION_URL,
    PROJECT_REPOSITORY_URL,
    QUICKSTART_EXPECTED_LINES,
    QUICKSTART_INSTALL,
    QUICKSTART_ONE_LINER,
    TAGLINE,
    ZERO_INSTALL_OPTIONS,
)
from .datasets import list_starter_datasets
from .design_system import page_head
from .guide import API_ENTRIES, SCENARIOS
from .positioning import coverage_matrix, ecosystem_positioning
from .profile import profile_dataset
from .real_tutorial_data import (
    ai_attention_breakouts,
    btc_oil_vix_2024,
    heatwave_city_temps_2024,
    python_javascript_pageviews_2024,
    treasury_yields_2024,
    usgs_earthquakes_ca_ak_2024,
)
from .runtime_paths import resolve_repo_subdir
from .similarity_method_atlas import similarity_method_atlas_dict
from .similarity import compare_series, rolling_similarity
from .visuals import (
    axis_bar_svg,
    profile_radar_svg,
    rolling_similarity_svg,
    series_overlay_svg,
    similarity_components_svg,
    similarity_radar_svg,
)

DOC_PAGES = (
    ("index", "Docs Home"),
    ("getting-started", "Getting Started"),
    ("tutorials", "Tutorials"),
    ("api", "API Reference"),
    ("methods", "Methods Atlas"),
    ("scenarios", "Scenarios"),
    ("ecosystem", "Ecosystem"),
    ("agents", "Agent Tools"),
)

_EXAMPLES_DIR = resolve_repo_subdir("examples", "gallery", sentinel="plot_weekly_traffic_similarity.py")


def _clean(text: str) -> str:
    return (
        str(text)
        .replace("echotime", DISPLAY_NAME)
        .replace("TSontology", DISPLAY_NAME)
        .replace("¡Á", " x ")
        .replace("脳", " x ")
        .replace("鈥", "-")
        .replace("dataset-first structural profiling", "explainable structural similarity")
        .replace("Dataset-first structural profiling", "Dataset structure and similarity context")
    )


def _pill(label: str, tone: str = "") -> str:
    cls = "pill"
    if tone:
        cls += f" {tone}"
    return f"<span class='{cls}'>{escape(label)}</span>"


def _doc_shell(
    *,
    page_key: str,
    title: str,
    lead: str,
    body: str,
    extra_css: str = "",
    sidebar_sections: Iterable[str] = (),
    hero_html: str | None = None,
) -> str:
    sidebar = []
    for key, label in DOC_PAGES:
        href = "index.html" if key == "index" else f"{key}.html"
        active = " active" if key == page_key else ""
        sidebar.append(f"<a class='doc-link{active}' href='{href}'>{escape(label)}</a>")
    base_css = """
    .docs-wrap { display:grid; grid-template-columns: 240px minmax(0, 1fr); gap: 18px; padding: 24px 0 36px; }
    .docs-sidebar { position: sticky; top: 88px; align-self: start; display:grid; gap:14px; min-width: 0; }
    .sidebar-card { background: var(--surface-strong); border:1px solid var(--border); border-radius: var(--radius-md); padding: 16px; box-shadow: var(--shadow-sm); overflow: hidden; }
    .sidebar-title { margin:0 0 10px; font-size: 0.86rem; color: var(--text-600); font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
    .doc-link { display:block; padding: 10px 12px; border-radius: 12px; color: var(--text-600); font-weight: 600; word-break: break-word; }
    .doc-link:hover { background: rgba(47,107,255,0.06); color: var(--text-900); }
    .doc-link.active { background: rgba(255, 244, 194, 0.78); color: var(--text-900); border:1px solid rgba(255,200,61,0.38); }
    .docs-main { display:grid; gap: 24px; min-width: 0; }
    .docs-hero { display:grid; gap: 12px; }
    .docs-hero h1 { font-size: clamp(2.1rem, 4vw, 3.3rem); line-height: 1.02; }
    .docs-card { background: var(--surface-strong); border:1px solid var(--border); border-radius: var(--radius-md); padding: 20px; box-shadow: var(--shadow-sm); display:grid; gap: 12px; min-width: 0; overflow: hidden; }
    .docs-grid-2, .docs-grid-3 { display:grid; gap: 20px; }
    .docs-grid-2 { grid-template-columns: 1fr 1fr; }
    .docs-grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .meta-line { display:flex; flex-wrap:wrap; gap: 10px; min-width: 0; }
    .meta-chip { display:inline-flex; align-items:center; gap:6px; padding: 6px 10px; border-radius: 999px; background: var(--surface); border:1px solid var(--border); color: var(--text-600); font-size: 0.84rem; font-weight: 700; min-width: 0; }
    .meta-chip strong { color: var(--text-900); }
    .entry-stack { display:grid; gap: 16px; }
    .entry { border-top: 1px solid var(--border); padding-top: 16px; }
    .entry:first-child { border-top: 0; padding-top: 0; }
    .entry h3 { font-size: 1.1rem; }
    .inline-code { display: inline-block; max-width: 100%; overflow-x: auto; vertical-align: bottom; white-space: nowrap; font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace; background: #fffef8; border:1px solid var(--border); padding: 2px 6px; border-radius: 8px; }
    .small-table { width:100%; border-collapse:collapse; display:block; overflow-x:auto; }
    .small-table th, .small-table td { padding: 11px 12px; text-align:left; border-bottom:1px solid var(--border); vertical-align: top; }
    .small-table th { background: #fffdf6; color: var(--text-600); font-size: 0.9rem; }
    .small-table tr:last-child td { border-bottom: 0; }
    .toc-note { font-size: 0.92rem; color: var(--text-600); }
    .example-card { align-content: start; }
    .example-preview { border: 1px solid var(--border); border-radius: 16px; background: linear-gradient(180deg, #fffdfa 0%, #ffffff 100%); padding: 12px; overflow: hidden; }
    .example-preview svg { display: block; width: 100%; height: auto; }
    .example-link-row { display:flex; flex-wrap:wrap; gap:10px; margin-top: 4px; }
    .example-figure-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:20px; }
    .example-figure-wide { grid-column: 1 / -1; }
    .asset-list { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .asset-link { display:grid; gap:4px; padding: 14px 16px; border-radius: 14px; border:1px solid var(--border); background: var(--surface); color: var(--text-900); }
    .asset-link:hover { border-color: rgba(47,107,255,0.18); background: rgba(47,107,255,0.04); color: var(--text-900); }
    .asset-link strong { font-size: 0.96rem; }
    .asset-link span { color: var(--text-600); font-size: 0.88rem; }
    .gallery-section { display:grid; gap: 14px; }
    .gallery-section h2 { font-size: 1.18rem; }
    .gallery-grid { display:grid; gap: 16px; }
    .gallery-card { display:grid; grid-template-columns: 220px minmax(0, 1fr); gap: 18px; align-items: start; padding: 16px 18px; border:1px solid var(--border); border-radius: 18px; background: var(--surface-strong); box-shadow: var(--shadow-sm); }
    .gallery-thumb { display:block; border: 1px solid var(--border); border-radius: 16px; padding: 10px; background: linear-gradient(180deg, #fffdfa 0%, #ffffff 100%); overflow: hidden; }
    .gallery-thumb svg { display:block; width: 100%; height: auto; }
    .gallery-body { display:grid; gap: 8px; min-width: 0; }
    .gallery-body h3 { font-size: 1.2rem; line-height: 1.25; }
    .gallery-body p { margin: 0; }
    .gallery-links { display:flex; flex-wrap:wrap; gap: 12px; font-weight: 700; }
    .gallery-links a { color: var(--blue-700); }
    .gallery-links a:hover { text-decoration: underline; }
    .gallery-kicker { font-size: 0.8rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-600); }
    .example-page-intro { display:grid; gap: 16px; }
    .example-breadcrumb { font-size: 0.9rem; color: var(--text-600); }
    .example-head { display:grid; gap: 10px; }
    .example-head h1 { font-size: clamp(1.8rem, 3vw, 2.55rem); line-height: 1.08; }
    .example-summary-grid { display:grid; grid-template-columns: 1.15fr 0.85fr; gap: 18px; }
    .example-teaser { display:grid; gap: 14px; }
    .example-score { font-size: 2.5rem; line-height: 0.95; font-weight: 800; letter-spacing: -0.05em; color: var(--text-900); }
    .example-score-label { font-size: 0.95rem; color: var(--text-600); font-weight: 700; }
    .component-list { display:grid; gap: 10px; }
    .component-row { display:grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: center; }
    .component-row span { color: var(--text-600); }
    .component-track { grid-column: 1 / -1; height: 8px; border-radius: 999px; background: #f3f4f6; overflow: hidden; }
    .component-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--sun-500), #f1b62a); }
    @media (max-width: 1180px) {
      .docs-grid-3 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .example-figure-grid, .asset-list { grid-template-columns: 1fr; }
    }
    @media (max-width: 980px) {
      .docs-wrap { grid-template-columns: 1fr; }
      .docs-sidebar { position: static; }
      .docs-grid-2, .docs-grid-3 { grid-template-columns: 1fr; }
      .example-figure-grid { grid-template-columns: 1fr; }
      .gallery-card, .example-summary-grid { grid-template-columns: 1fr; }
    }
    """
    return f"""<!doctype html>
<html lang='en'>
{page_head(f"{DISPLAY_NAME} docs - {title}", extra_css=base_css + extra_css)}
<body>
<header class='topbar'>
  <div class='shell topbar-inner'>
    <div class='brand'>
      <span class='brand-mark'></span>
      <div class='brand-copy'>
        <strong>{DISPLAY_NAME}</strong>
        <span>{escape(TAGLINE)}</span>
      </div>
    </div>
    <nav class='nav'>
      <a href='../index.html'>Home</a>
      <a href='index.html'>Docs</a>
      <a href='tutorials.html'>Tutorials</a>
      <a href='api.html'>API</a>
      <a href='../playground.html'>Playground</a>
      <a href='{escape(PROJECT_REPOSITORY_URL)}'>GitHub</a>
    </nav>
  </div>
</header>
<main class='shell docs-wrap'>
  <aside class='docs-sidebar'>
    <div class='sidebar-card'>
      <div class='sidebar-title'>Documentation</div>
      {"".join(sidebar)}
    </div>
    <div class='sidebar-card'>
      <div class='sidebar-title'>Quick links</div>
      <a class='doc-link' href='../playground.html'>Static playground</a>
      <a class='doc-link' href='../start-here.html'>Start here</a>
      <a class='doc-link' href='../reports/github_breakout_similarity.html'>Real-data flagship report</a>
    </div>
    <div class='sidebar-card'>
      <div class='sidebar-title'>Maintainer</div>
      <div class='toc-note'><strong>{escape(AUTHOR_NAME)}</strong><br>{escape(AUTHOR_AFFILIATION)}<br><a href='mailto:{escape(AUTHOR_EMAIL)}'>{escape(AUTHOR_EMAIL)}</a></div>
    </div>
    {"".join(sidebar_sections)}
  </aside>
  <section class='docs-main'>
    {hero_html or f"<div class='docs-hero'><div class='eyebrow'>Documentation</div><h1>{escape(title)}</h1><p class='subhead'>{escape(lead)}</p></div>"}
    {body}
  </section>
</main>
</body>
</html>"""


def _overview_cards() -> str:
    cards = [
        ("Getting Started", "Start with your own CSV, DataFrame, or two columns and get to a first result quickly.", "getting-started.html", "sun"),
        ("Tutorials", "Runnable examples in the style of a human tutorial: load data, call a function, inspect the result.", "tutorials.html", "blue"),
        ("API Reference", "The public compare/profile surface and the result objects you will actually call from Python.", "api.html", "sun"),
        ("Methods Atlas", "Audit EchoTime's current similarity stack, the 127 extracted methods from ts_similarity_package_v2_pkg, and the formulas behind each one.", "methods.html", "blue"),
        ("Scenarios", "Where EchoTime fits across medicine, engineering, product, and research.", "scenarios.html", "blue"),
        ("Ecosystem", "How EchoTime complements sktime, tsfresh, DTAIDistance, and others.", "ecosystem.html", "sun"),
        ("Advanced Integrations", "Tool-calling and agent wrappers live here when you need them, not before.", "agents.html", "blue"),
    ]
    return "".join(
        "<div class='docs-card'>"
        f"{_pill(label, tone)}"
        f"<h3>{escape(label)}</h3>"
        f"<p>{escape(text)}</p>"
        f"<a class='button ghost' href='{href}'>Open page</a>"
        "</div>"
        for label, text, href, tone in cards
    )


def _repo_blob_href(relpath: str) -> str:
    normalized = relpath.replace("\\", "/").lstrip("/")
    return f"{PROJECT_REPOSITORY_URL}/blob/main/{normalized}"


def _load_example_source(filename: str) -> str:
    path = _EXAMPLES_DIR / filename
    if not path.exists():
        return "# example source unavailable\n"
    return path.read_text(encoding="utf-8")


def _asset_link(label: str, href: str, caption: str) -> str:
    return (
        f"<a class='asset-link' href='{escape(href)}'>"
        f"<strong>{escape(label)}</strong>"
        f"<span>{escape(caption)}</span>"
        "</a>"
    )


def _example_sidebar(entries: list[dict[str, Any]], active_href: str) -> str:
    links = []
    for entry in entries:
        active = " active" if entry["href"] == active_href else ""
        links.append(f"<a class='doc-link{active}' href='{entry['href']}'>{escape(entry['title'])}</a>")
    return (
        "<div class='sidebar-card'>"
        "<div class='sidebar-title'>Example gallery</div>"
        + "".join(links)
        + "</div>"
    )


def _example_report_href(entry: dict[str, Any]) -> str:
    return next(
        (
            asset["href"]
            for asset in entry["assets"]
            if asset["label"] in {"Standalone report", "Related report", "Clinical report"}
        ),
        "",
    )


def _tutorial_assets(
    *,
    code_filename: str,
    local_csv: str,
    source_url: str,
    extra_assets: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    assets = [
        {
            "label": "Python source",
            "href": _repo_blob_href(f"examples/gallery/{code_filename}"),
            "caption": "The exact script used for this example.",
        },
        {
            "label": "Real CSV snapshot",
            "href": _repo_blob_href(local_csv),
            "caption": "The frozen CSV snapshot used to generate this page.",
        },
        {
            "label": "Original source",
            "href": source_url,
            "caption": "The public upstream source used to refresh the CSV snapshot.",
        },
    ]
    if extra_assets:
        assets.extend(extra_assets)
    return assets


def _example_source_href(entry: dict[str, Any]) -> str:
    return _repo_blob_href(f"examples/gallery/{entry['code_filename']}")


def _component_rows(entry: dict[str, Any], *, limit: int = 4) -> str:
    report = entry["report"]
    rows = []
    for label, value in sorted(report.component_scores.items(), key=lambda kv: kv[1], reverse=True)[:limit]:
        rows.append(
            "<div class='component-row'>"
            f"<span>{escape(label.replace('_', ' '))}</span>"
            f"<strong>{float(value):0.2f}</strong>"
            f"<div class='component-track'><div class='component-fill' style='width:{max(0.0, min(100.0, float(value) * 100.0)):0.1f}%'></div></div>"
            "</div>"
        )
    return "".join(rows)


def _report_metric(report: Any, key: str) -> float:
    return float(getattr(report, "reference_metrics", {}).get(key, np.nan))


def _report_metric_summary(report: Any) -> str:
    parts = []
    for label, key in (("Pearson", "pearson_r"), ("Spearman", "spearman_rho"), ("Mutual info", "normalized_mutual_information"), ("Kendall", "kendall_tau")):
        value = _report_metric(report, key)
        if np.isfinite(value):
            parts.append(f"{label} {value:.2f}")
    return " / ".join(parts[:3]) if parts else f"Component mean {float(getattr(report, 'component_mean', np.nan)):.2f}"


def _reference_metric_chips(report: Any, *, limit: int = 4) -> str:
    items = []
    metric_map = (
        ("Pearson", "pearson_r"),
        ("Spearman", "spearman_rho"),
        ("Mutual info", "normalized_mutual_information"),
        ("Diff r", "first_difference_r"),
        ("Kendall", "kendall_tau"),
    )
    for label, key in metric_map:
        value = _report_metric(report, key)
        if np.isfinite(value):
            items.append(f"<span class='meta-chip'><strong>{escape(label)}</strong> {value:.2f}</span>")
    return "".join(items[:limit])


def _example_workflow_list(entry: dict[str, Any]) -> str:
    items = "".join(f"<li>{escape(item)}</li>" for item in entry["workflow_steps"])
    return f"<ol class='panel-list'>{items}</ol>"


def _example_own_data_list(entry: dict[str, Any]) -> str:
    items = "".join(f"<li>{escape(item)}</li>" for item in entry["own_data_tips"])
    return f"<ul class='panel-list'>{items}</ul>"


def _render_example_page(entry: dict[str, Any], entries: list[dict[str, Any]]) -> str:
    report_href = _example_report_href(entry)
    figures_html = "".join(
        "<div class='docs-card"
        + (" example-figure-wide" if figure.get("wide") else "")
        + "'>"
        + _pill(figure["label"], figure.get("tone", "blue"))
        + f"<div class='example-preview'>{figure['svg']}</div>"
        + f"<p class='muted'>{escape(figure['caption'])}</p>"
        + "</div>"
        for figure in entry["figures"]
    )
    assets_html = "".join(
        _asset_link(asset["label"], asset["href"], asset["caption"])
        for asset in entry["assets"]
    )
    highlights = "".join(f"<li>{escape(item)}</li>" for item in entry["highlights"])
    hero_html = f"""
    <div class='example-page-intro'>
      <div class='example-breadcrumb'><a href='tutorials.html'>Examples</a> / {escape(entry['category'])}</div>
      <div class='example-head'>
        <div class='eyebrow'>{escape(entry['category'])}</div>
        <h1>{escape(entry['title'])}</h1>
        <p class='subhead'>{escape(entry['lead'])}</p>
      </div>
    </div>
    """
    body = f"""
    <div class='example-summary-grid'>
      <div class='docs-card example-teaser'>
        {_pill('Question', 'blue')}
        <p><strong>{escape(entry['question'])}</strong></p>
        <p>{escape(entry['deck'])}</p>
        <div class='meta-line'>
          <span class='meta-chip'><strong>Input</strong> {escape(entry['input_shape'])}</span>
          <span class='meta-chip'><strong>Call</strong> {escape(entry['main_call'])}</span>
          <span class='meta-chip'><strong>Output</strong> {escape(entry['output_shape'])}</span>
        </div>
        {_example_workflow_list(entry)}
        <div class='gallery-links'>
          <a href='{entry['href']}'>Permalink</a>
          {f"<a href='{report_href}'>Open report</a>" if report_href else ""}
          <a href='{_example_source_href(entry)}'>Open script</a>
        </div>
      </div>
      <div class='docs-card'>
        {_pill('Result at a glance', 'sun')}
        <div class='meta-line'>{_reference_metric_chips(entry['report'])}</div>
        <div class='example-score-label'>Component mean {entry['report'].component_mean:.2f} across {len(entry['report'].component_scores)} time-series metrics</div>
        <p>{escape(entry['report'].interpretation)}</p>
        <div class='component-list'>{_component_rows(entry)}</div>
      </div>
    </div>
    <div class='docs-grid-2'>
      <div class='docs-card'>
        {_pill('Runnable example', 'blue')}
        <p>This is the minimal script a human user would actually run: load data, call EchoTime, inspect the returned object.</p>
        <pre><code>{escape(entry['code'])}</code></pre>
      </div>
      <div class='docs-card'>
        {_pill('What you should see', 'sun')}
        <p>{escape(entry['expected_result'])}</p>
        <pre><code>{escape(entry['summary'])}</code></pre>
        <ul class='panel-list'>{highlights}</ul>
      </div>
    </div>
    <div class='docs-card'>
      {_pill('Use your own data', 'blue')}
      <p>{escape(entry['own_data_intro'])}</p>
      {_example_own_data_list(entry)}
    </div>
    <div class='example-figure-grid'>
      {figures_html}
    </div>
    <div class='docs-card'>
      {_pill('Data and outputs', 'sun')}
      <div class='asset-list'>{assets_html}</div>
    </div>
    """
    return _doc_shell(
        page_key="tutorials",
        title=entry["title"],
        lead=entry["lead"],
        body=body,
        sidebar_sections=(_example_sidebar(entries, entry["href"]),),
        hero_html=hero_html,
    )


def _tutorial_examples() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    treasury = treasury_yields_2024()
    treasury_report = compare_series(treasury["dgs10"], treasury["dgs2"], left_name="10Y Treasury", right_name="2Y Treasury")
    treasury_roll = rolling_similarity(treasury["dgs10"], treasury["dgs2"], window=30, step=10)
    entries.append(
        {
            "href": "example-two-curves-similarity.html",
            "slug": "treasury_yields",
            "title": "US Treasury 10Y and 2Y yields in 2024",
            "lead": "A first real-data example: read two columns from a CSV snapshot, compare them, and inspect how stable the relationship stays across the year.",
            "deck": "This page uses a frozen FRED snapshot of the 2024 daily 10Y and 2Y Treasury yields. The workflow is intentionally plain: read the CSV, call compare_series(...), then add rolling_similarity(...) when you want to see whether the relationship drifts.",
            "category": "Beginner example",
            "tone": "sun",
            "mode": "compare_series",
            "score_text": _report_metric_summary(treasury_report),
            "summary": treasury_report.to_summary_card_markdown(),
            "report": treasury_report,
            "code_filename": "plot_two_curves_similarity.py",
            "code": _load_example_source("plot_two_curves_similarity.py"),
            "highlights": [
                f"{_report_metric_summary(treasury_report)} says the two Treasury curves move together strongly at the level and rank level.",
                "Trend and spectral agreement stay high, which is what you would expect from two rates embedded in the same macro regime.",
                "Rolling similarity stays elevated through most of the year instead of collapsing after one short window.",
            ],
            "figures": [
                {
                    "label": "Series overlay",
                    "tone": "blue",
                    "svg": series_overlay_svg(treasury["dgs10"], treasury["dgs2"], left_label="10Y", right_label="2Y"),
                    "caption": "The overlay is generated from the real 2024 Treasury yield curves after EchoTime normalizes scale.",
                },
                {
                    "label": "Similarity radar",
                    "tone": "sun",
                    "svg": similarity_radar_svg(treasury_report),
                    "caption": "The radar shows which time-series-specific metrics stay high instead of hiding everything inside one opaque number.",
                },
                {
                    "label": "Rolling component mean",
                    "tone": "blue",
                    "svg": rolling_similarity_svg(treasury_roll),
                    "caption": "Rolling windows show where the average across the similarity metrics stays tight and where it loosens.",
                    "wide": True,
                },
            ],
            "assets": _tutorial_assets(
                code_filename="plot_two_curves_similarity.py",
                local_csv=treasury["local_csv"],
                source_url=treasury["source_url"],
            ),
            "preview_svg": series_overlay_svg(treasury["dgs10"], treasury["dgs2"], width=520, height=200, left_label="10Y", right_label="2Y"),
        }
    )

    pageviews = python_javascript_pageviews_2024()
    pageview_report = compare_series(
        pageviews["python_views"],
        pageviews["javascript_views"],
        left_name="Python pageviews",
        right_name="JavaScript pageviews",
    )
    pageview_roll = rolling_similarity(pageviews["python_views"], pageviews["javascript_views"], window=28, step=7)
    entries.append(
        {
            "href": "example-weekly-traffic-signals.html",
            "slug": "pageviews",
            "title": "Python and JavaScript pageviews move together, but not identically",
            "lead": "A clean two-column workflow on real Wikimedia traffic data: read a table, compare two series, then inspect how the relationship changes over rolling windows.",
            "deck": "This example uses daily 2024 Wikipedia pageviews for Python and JavaScript. It is the same shape as a normal user workflow on their own CSV: one date column, two numeric columns, one call to compare_series(...), and then a rolling view if you want time-local context.",
            "category": "Beginner example",
            "tone": "blue",
            "mode": "compare_series",
            "score_text": _report_metric_summary(pageview_report),
            "summary": pageview_report.to_summary_card_markdown(),
            "report": pageview_report,
            "code_filename": "plot_weekly_traffic_similarity.py",
            "code": _load_example_source("plot_weekly_traffic_similarity.py"),
            "highlights": [
                f"{_report_metric_summary(pageview_report)} shows the curves move together, but the first-difference match is weaker than the broad trend.",
                "Trend agreement is stronger than spectral agreement, which means the shared direction is clearer than the fine-grained cadence.",
                "This is a real table you can inspect and swap out for your own CSV with almost no code changes.",
            ],
            "figures": [
                {
                    "label": "Python vs JavaScript",
                    "tone": "blue",
                    "svg": series_overlay_svg(pageviews["python_views"], pageviews["javascript_views"], left_label="Python", right_label="JavaScript"),
                    "caption": "The daily pageview curves share broad shape, but the peaks and dips do not line up perfectly.",
                },
                {
                    "label": "Similarity radar",
                    "tone": "sun",
                    "svg": similarity_radar_svg(pageview_report),
                    "caption": "The radar makes it obvious which kinds of agreement are strong and which are only moderate.",
                },
                {
                    "label": "Rolling component mean",
                    "tone": "blue",
                    "svg": rolling_similarity_svg(pageview_roll),
                    "caption": "Rolling windows show when the average across the similarity metrics stays high and when the two topics separate.",
                    "wide": True,
                },
            ],
            "assets": _tutorial_assets(
                code_filename="plot_weekly_traffic_similarity.py",
                local_csv=pageviews["local_csv"],
                source_url=pageviews["source_url"],
                extra_assets=[
                    {
                        "label": "Related report",
                        "href": "../reports/weekly_website_traffic_report.html",
                        "caption": "A real-data profile report built from the same pageview snapshot.",
                    }
                ],
            ),
            "preview_svg": series_overlay_svg(pageviews["python_views"], pageviews["javascript_views"], width=520, height=200, left_label="Python", right_label="JavaScript"),
        }
    )

    earthquakes = usgs_earthquakes_ca_ak_2024()
    quake_report = compare_series(
        earthquakes["california_magnitudes"],
        earthquakes["alaska_magnitudes"],
        left_timestamps=earthquakes["california_timestamps"],
        right_timestamps=earthquakes["alaska_timestamps"],
        left_name="California earthquakes",
        right_name="Alaska earthquakes",
    )
    quake_profile = profile_dataset(earthquakes["event_records"], domain="earth_science")
    entries.append(
        {
            "href": "example-irregular-patient-similarity.html",
            "slug": "irregular_events",
            "title": "Irregular earthquake streams can still be compared",
            "lead": "A real irregular-data example using 2024 USGS earthquakes from California and Alaska, with explicit timestamps kept in the comparison instead of being flattened away.",
            "deck": "This page loads a long event table, keeps the real event timestamps for the pairwise comparison, and then profiles the same table as an event-stream dataset. The point is not the domain; the point is that EchoTime can work on genuinely irregular observations without pretending they came from a tidy grid.",
            "category": "Cross-disciplinary example",
            "tone": "sun",
            "mode": "compare_series + profile_dataset",
            "score_text": _report_metric_summary(quake_report),
            "summary": quake_report.to_summary_card_markdown(),
            "report": quake_report,
            "code_filename": "plot_irregular_patient_similarity.py",
            "code": _load_example_source("plot_irregular_patient_similarity.py"),
            "highlights": [
                f"{_report_metric_summary(quake_report)} is only part of the story; the event-timestamp handling matters just as much here.",
                "The comparison respects event timing instead of forcing both regions onto a regular daily grid first.",
                "The dataset profile adds event-stream context around burstiness, irregularity, and heterogeneity.",
            ],
            "figures": [
                {
                    "label": "California vs Alaska magnitudes",
                    "tone": "blue",
                    "svg": series_overlay_svg(
                        earthquakes["california_magnitudes"],
                        earthquakes["alaska_magnitudes"],
                        left_label="California",
                        right_label="Alaska",
                    ),
                    "caption": "The overlay is shown in event order, but the actual comparison also uses the real timestamps from the USGS feed.",
                },
                {
                    "label": "Similarity radar",
                    "tone": "sun",
                    "svg": similarity_radar_svg(quake_report),
                    "caption": "The radar keeps the irregular-event comparison interpretable without pretending one scalar is enough.",
                },
                {
                    "label": "Event-stream axes",
                    "tone": "blue",
                    "svg": axis_bar_svg(quake_profile),
                    "caption": "The profile makes burstiness, irregularity, and heterogeneity visible before you start modelling.",
                    "wide": True,
                },
            ],
            "assets": _tutorial_assets(
                code_filename="plot_irregular_patient_similarity.py",
                local_csv=earthquakes["local_csv"],
                source_url=earthquakes["source_url"],
                extra_assets=[
                    {
                        "label": "Related report",
                        "href": "../reports/irregular_patient_vitals_report.html",
                        "caption": "A real-data event-stream report built from the same USGS snapshot.",
                    }
                ],
            ),
            "preview_svg": similarity_radar_svg(quake_report, width=520, height=220),
        }
    )

    attention = ai_attention_breakouts()
    attention_report = compare_series(attention["deepseek_cumulative"], attention["threads_cumulative"], left_name="DeepSeek", right_name="Threads")
    attention_alt = compare_series(attention["deepseek_cumulative"], attention["chatgpt_cumulative"], left_name="DeepSeek", right_name="ChatGPT")
    attention_roll = rolling_similarity(attention["deepseek_cumulative"], attention["threads_cumulative"], window=20, step=5)
    entries.append(
        {
            "href": "example-github-breakout-analogs.html",
            "slug": "attention_breakout",
            "title": "AI attention breakout analogs",
            "lead": "A flagship real-data example asking which historical attention curve DeepSeek looked more like over its first breakout window: ChatGPT or Threads.",
            "deck": "The data here are real Wikimedia pageviews aligned to the early breakout periods for DeepSeek, ChatGPT, and Threads. EchoTime compares the cumulative attention curves and makes the analog choice explicit instead of leaving it as a vibes-only story.",
            "category": "Flagship demo",
            "tone": "blue",
            "mode": "compare_series + rolling_similarity",
            "score_text": _report_metric_summary(attention_report),
            "summary": attention_report.to_summary_card_markdown(),
            "report": attention_report,
            "code_filename": "plot_github_breakout_analogs.py",
            "code": _load_example_source("plot_github_breakout_analogs.py"),
            "highlights": [
                f"DeepSeek vs Threads: {_report_metric_summary(attention_report)}; against ChatGPT: {_report_metric_summary(attention_alt)}.",
                "The rolling view makes the analog choice inspectable instead of hiding disagreement behind one opaque number.",
                "This is a real analog-selection workflow on public data, not a hand-drawn breakout curve.",
            ],
            "figures": [
                {
                    "label": "DeepSeek vs Threads",
                    "tone": "blue",
                    "svg": series_overlay_svg(attention["deepseek_cumulative"], attention["threads_cumulative"], left_label="DeepSeek", right_label="Threads"),
                    "caption": "The cumulative attention curves stay close enough that the analog is visible before you read the coefficients and radar.",
                },
                {
                    "label": "Similarity radar",
                    "tone": "sun",
                    "svg": similarity_radar_svg(attention_report),
                    "caption": "The analog call is backed by multiple time-series metrics rather than a single scalar.",
                },
                {
                    "label": "Rolling component mean",
                    "tone": "blue",
                    "svg": rolling_similarity_svg(attention_roll),
                    "caption": "Rolling component mean shows whether the match survives beyond the initial breakout surge.",
                    "wide": True,
                },
            ],
            "assets": _tutorial_assets(
                code_filename="plot_github_breakout_analogs.py",
                local_csv=attention["local_csv"],
                source_url=attention["source_url"],
                extra_assets=[
                    {
                        "label": "Standalone report",
                        "href": "../reports/github_breakout_similarity.html",
                        "caption": "Open the full real-data similarity report.",
                    },
                    {
                        "label": "Story page",
                        "href": "../blog/github_breakout_analogs.html",
                        "caption": "Open the blog-style explainer for the same real-data result.",
                    },
                    {
                        "label": "Social card",
                        "href": "../social/github_breakout_card.svg",
                        "caption": "Open the shareable card generated from the same run.",
                    },
                ],
            ),
            "preview_svg": similarity_radar_svg(attention_report, width=520, height=220),
        }
    )

    markets = btc_oil_vix_2024()
    market_report = compare_series(markets["btc_usd"], markets["vix"], left_name="BTC", right_name="VIX")
    market_alt = compare_series(markets["btc_usd"], markets["brent_usd"], left_name="BTC", right_name="Brent")
    market_roll = rolling_similarity(markets["btc_usd"], markets["vix"], window=30, step=10)
    entries.append(
        {
            "href": "example-btc-gold-under-shocks.html",
            "slug": "btc_oil_vix",
            "title": "BTC, Brent, and VIX in 2024",
            "lead": "A macro example on real FRED data asking whether BTC behaved more like oil or more like implied volatility across 2024.",
            "deck": "This page loads daily BTC, Brent, and VIX series from a local CSV snapshot built from FRED. The result is intentionally not dramatic: EchoTime shows that BTC is somewhat closer to VIX than to Brent, but the analogy is only moderate and changes across windows.",
            "category": "Flagship demo",
            "tone": "sun",
            "mode": "compare_series + rolling_similarity",
            "score_text": _report_metric_summary(market_report),
            "summary": market_report.to_summary_card_markdown(),
            "report": market_report,
            "code_filename": "plot_btc_gold_under_shocks.py",
            "code": _load_example_source("plot_btc_gold_under_shocks.py"),
            "highlights": [
                f"BTC vs VIX: {_report_metric_summary(market_report)}; BTC vs Brent: {_report_metric_summary(market_alt)}.",
                "The rolling curve shows that the analogy is regime-dependent rather than something you should treat as globally stable.",
                "This is a better external demo than a hand-picked market anecdote because the claim is explicit and reproducible.",
            ],
            "figures": [
                {
                    "label": "BTC vs VIX",
                    "tone": "blue",
                    "svg": series_overlay_svg(markets["btc_usd"], markets["vix"], left_label="BTC", right_label="VIX"),
                    "caption": "The raw scales differ, so EchoTime normalizes before comparing shared structure.",
                },
                {
                    "label": "Similarity radar",
                    "tone": "sun",
                    "svg": similarity_radar_svg(market_report),
                    "caption": "The radar shows where the BTC-VIX analogy is real and where it stays weak.",
                },
                {
                    "label": "Rolling component mean",
                    "tone": "blue",
                    "svg": rolling_similarity_svg(market_roll),
                    "caption": "Rolling windows show when the average across the similarity metrics strengthens and when it fades.",
                    "wide": True,
                },
            ],
            "assets": _tutorial_assets(
                code_filename="plot_btc_gold_under_shocks.py",
                local_csv=markets["local_csv"],
                source_url=markets["source_url"],
                extra_assets=[
                    {
                        "label": "Standalone report",
                        "href": "../reports/btc_vs_gold_similarity.html",
                        "caption": "Open the full real-data similarity report.",
                    },
                    {
                        "label": "Story page",
                        "href": "../blog/btc_vs_gold_under_shocks.html",
                        "caption": "Open the blog-style explainer for the same market run.",
                    },
                    {
                        "label": "Social card",
                        "href": "../social/btc_vs_gold_card.svg",
                        "caption": "Open the shareable card generated from the same run.",
                    },
                ],
            ),
            "preview_svg": similarity_radar_svg(market_report, width=520, height=220),
        }
    )

    heatwave = heatwave_city_temps_2024()
    heat_report = compare_series(heatwave["phoenix_temp_max"], heatwave["las_vegas_temp_max"], left_name="Phoenix max temp", right_name="Las Vegas max temp")
    heat_profile = profile_dataset(heatwave["values"], domain="climate", channel_names=heatwave["channels"])
    entries.append(
        {
            "href": "example-heatwave-grid-load.html",
            "slug": "heatwave_city_temps",
            "title": "Southwest heatwave city temperatures",
            "lead": "A wide-table example using Phoenix and Las Vegas daily maximum temperatures during the 2024 summer heatwave window.",
            "deck": "This page reads a real two-column climate table, compares Phoenix and Las Vegas directly, and then profiles the full panel. It is the same pattern you would use for two sensors, two regions, or two business metrics in one wide CSV.",
            "category": "Flagship demo",
            "tone": "blue",
            "mode": "compare_series + profile_dataset",
            "score_text": _report_metric_summary(heat_report),
            "summary": heat_report.to_summary_card_markdown(),
            "report": heat_report,
            "code_filename": "plot_heatwave_grid_load.py",
            "code": _load_example_source("plot_heatwave_grid_load.py"),
            "highlights": [
                f"{_report_metric_summary(heat_report)} shows the two cities track each other closely through the heatwave window.",
                "The supporting dataset profile shows the broader structural context behind that pairwise comparison.",
                "This is a realistic wide-table workflow you can reuse for any small panel of real measurements.",
            ],
            "figures": [
                {
                    "label": "Phoenix vs Las Vegas",
                    "tone": "blue",
                    "svg": series_overlay_svg(heatwave["phoenix_temp_max"], heatwave["las_vegas_temp_max"], left_label="Phoenix", right_label="Las Vegas"),
                    "caption": "The two city temperature curves share broad movement, but day-to-day changes are not identical.",
                },
                {
                    "label": "Similarity radar",
                    "tone": "sun",
                    "svg": similarity_radar_svg(heat_report),
                    "caption": "The radar shows where the two temperature curves agree most strongly.",
                },
                {
                    "label": "Dataset structure",
                    "tone": "blue",
                    "svg": profile_radar_svg(heat_profile),
                    "caption": "The dataset profile reveals the broader structure of the full temperature panel.",
                    "wide": True,
                },
            ],
            "assets": _tutorial_assets(
                code_filename="plot_heatwave_grid_load.py",
                local_csv=heatwave["local_csv"],
                source_url=heatwave["source_url"],
                extra_assets=[
                    {
                        "label": "Standalone report",
                        "href": "../reports/energy_load_heatwave_report.html",
                        "caption": "Open the full real-data panel report.",
                    },
                    {
                        "label": "Story page",
                        "href": "../blog/heatwave_vs_grid_load.html",
                        "caption": "Open the blog-style explainer for the same heatwave run.",
                    },
                    {
                        "label": "Social card",
                        "href": "../social/energy_load_card.svg",
                        "caption": "Open the shareable card generated from the same run.",
                    },
                ],
            ),
            "preview_svg": axis_bar_svg(heat_profile, width=520, height=220),
        }
    )

    human_fields = {
        "treasury_yields": {
            "question": "How tightly did the 10Y and 2Y Treasury yield curves move together across 2024?",
            "input_shape": "two numeric columns from one CSV",
            "main_call": "compare_series(df['dgs10'], df['dgs2'])",
            "output_shape": "SimilarityReport + rolling windows",
            "workflow_steps": [
                "Read the local CSV snapshot with pandas.",
                "Select the two yield columns you want to compare.",
                "Run compare_series(...) first, then rolling_similarity(...) if you want time-local context.",
            ],
            "expected_result": "You should get a very high but not perfect match because the two rates move together strongly without collapsing into the same curve.",
            "own_data_intro": "This is the simplest way to use EchoTime on your own two-column CSV.",
            "own_data_tips": [
                "Swap df['dgs10'] and df['dgs2'] for the two numeric columns you care about.",
                "If your file has timestamps, keep them in the DataFrame even if the first compare_series(...) call does not require them.",
                "Write report.to_html_report() to disk when you need something you can hand to a teammate.",
            ],
        },
        "pageviews": {
            "question": "Are Python and JavaScript attention curves moving together strongly enough to treat them as the same traffic story?",
            "input_shape": "two numeric columns from one table",
            "main_call": "compare_series(df['python_views'], df['javascript_views'])",
            "output_shape": "SimilarityReport + rolling windows",
            "workflow_steps": [
                "Load the pageview table with pandas.",
                "Select the two columns you want to compare.",
                "Run compare_series(...) and optionally rolling_similarity(...) to see where the relationship changes.",
            ],
            "expected_result": "You should see high Pearson and Spearman agreement, with weaker local-change alignment than the broad attention trend.",
            "own_data_intro": "This is the pattern most users will follow with their own CSV.",
            "own_data_tips": [
                "Read your table with pandas, then pass the two numeric columns into compare_series(...).",
                "If your file also has dates, keep them for rolling plots or report annotations even if the basic comparison works without them.",
                "Write report.to_html_report() to disk when you need something you can hand to a teammate.",
            ],
        },
        "irregular_events": {
            "question": "Can you compare irregular event streams without pretending the data are evenly sampled?",
            "input_shape": "irregular values plus explicit timestamps",
            "main_call": "compare_series(..., left_timestamps=..., right_timestamps=...)",
            "output_shape": "SimilarityReport + DatasetProfile",
            "workflow_steps": [
                "Load the long event table with pandas.",
                "Split out the two irregular trajectories you want to compare and keep their timestamps.",
                "Run compare_series(...) for the pair and profile_dataset(...) on the long table for context.",
            ],
            "expected_result": "You should get a usable similarity verdict plus an event-stream profile explaining why irregularity and burstiness matter.",
            "own_data_intro": "This is the right pattern when your own data live in a long table with real timestamps.",
            "own_data_tips": [
                "Rename long-table columns to subject, timestamp, channel, and value before calling profile_dataset(df, domain='generic').",
                "If you want to compare two specific trajectories directly, pass both the values and their timestamps into compare_series(...).",
                "Do not regularize away the gaps before the first pass; EchoTime is designed to read them.",
            ],
        },
        "attention_breakout": {
            "question": "Which historical breakout curve is closest to the new one you care about?",
            "input_shape": "one target series plus one or more analog curves",
            "main_call": "compare_series(target, analog)",
            "output_shape": "SimilarityReport + rolling windows",
            "workflow_steps": [
                "Load the target curve and the analog curves.",
                "Compare the target against each analog with compare_series(...).",
                "Use rolling_similarity(...) to see whether the match survives beyond the initial spike.",
            ],
            "expected_result": "You should see one analog with consistently stronger Pearson, Spearman, and DTW evidence than the others, plus rolling windows that support the choice.",
            "own_data_intro": "This workflow generalizes to any \"which historical analog is closest?\" question.",
            "own_data_tips": [
                "Replace the example curves with your own daily installs, signups, traffic, or attention series.",
                "Compare against several historical candidates, not just one, if you want a defensible analog story.",
                "Keep event dates such as releases or campaigns nearby even if the first pass only compares the numeric curves.",
            ],
        },
        "btc_oil_vix": {
            "question": "Was BTC structurally closer to oil or to volatility in 2024?",
            "input_shape": "two or more aligned market series",
            "main_call": "compare_series(df['btc_usd'], df['vix'])",
            "output_shape": "SimilarityReport + rolling windows",
            "workflow_steps": [
                "Load the market series you want to compare.",
                "Run compare_series(...) for the pair you care about first.",
                "Use rolling_similarity(...) when you suspect the relationship changes across regimes.",
            ],
            "expected_result": "You should get mixed evidence rather than a clean analog: some metrics stay moderate, and the rolling view should show where the relationship strengthens or breaks.",
            "own_data_intro": "This is the same workflow you would use for returns, prices, search trends, or any pair of aligned signals.",
            "own_data_tips": [
                "For very different scales, compare returns or z-scored values instead of raw levels.",
                "Use rolling_similarity(...) for regime questions; a single whole-period average is usually too blunt.",
                "If your series come from a CSV, load them with pandas and pass the numeric columns directly into compare_series(...).",
            ],
        },
        "heatwave_city_temps": {
            "question": "How similar were Phoenix and Las Vegas daily maximum temperatures during the 2024 heatwave window?",
            "input_shape": "wide table or multichannel array with timestamps",
            "main_call": "compare_series(left, right) + profile_dataset(data)",
            "output_shape": "SimilarityReport + DatasetProfile",
            "workflow_steps": [
                "Load the wide table with pandas.",
                "Compare the two columns you care about with compare_series(...).",
                "Profile the full dataset with profile_dataset(...) to see the wider structural context.",
            ],
            "expected_result": "You should see high pairwise correlation metrics plus a dataset profile explaining the broader panel structure.",
            "own_data_intro": "This is the most useful pattern when you have a whole panel, not just one pair of curves.",
            "own_data_tips": [
                "For a CSV, keep one timestamp column and one numeric column per city, region, or sensor.",
                "Use compare_series(...) for the one pair you want to talk about, then profile_dataset(...) for the full panel.",
                "If you need something shareable, write both the similarity and profile HTML reports to disk.",
            ],
        },
    }
    for entry in entries:
        entry.update(human_fields[entry["slug"]])

    for entry in entries:
        entry["page_html"] = _render_example_page(entry, entries)
    return entries


def project_docs_home_html(*, version: str = PACKAGE_VERSION) -> str:
    expected = escape("\n".join(QUICKSTART_EXPECTED_LINES))
    body = f"""
    <div class='docs-grid-2'>
      <div class='docs-card'>
        {_pill('Docs home', 'sun')}
        <p><strong>Start here if you want to use EchoTime as a normal Python package.</strong> The human path is: load data, call one function, inspect the returned object, then export HTML only if you need to share the result.</p>
        <div class='meta-line'>
          <span class='meta-chip'><strong>Version</strong> {escape(version)}</span>
          <span class='meta-chip'><strong>Audience</strong> researchers, engineers, analysts</span>
        </div>
      </div>
      <div class='docs-card'>
        {_pill('Human path', 'blue')}
        <pre><code>import pandas as pd
from echotime import profile_dataset

df = pd.read_csv("my_timeseries.csv").rename(columns={{"date": "timestamp"}})
profile = profile_dataset(df, domain="energy")
print(profile.to_summary_card_markdown())</code></pre>
      </div>
    </div>
    <div class='docs-grid-2'>
      <div class='docs-card'>
        {_pill('60-second quickstart', 'sun')}
        <pre><code>{escape(QUICKSTART_INSTALL)}
{escape(QUICKSTART_ONE_LINER)}</code></pre>
      </div>
      <div class='docs-card'>
        {_pill('Three first moves', 'blue')}
        <ul class='panel-list'>
          <li>If you already have your own table, open Getting Started first.</li>
          <li>If you want runnable worked examples, open Tutorials.</li>
          <li>If you only need integration details later, keep Advanced Integrations for last.</li>
        </ul>
      </div>
    </div>
    <div class='docs-grid-3'>
      {_overview_cards()}
    </div>
    <div class='docs-card'>
      {_pill('Expected output', 'sun')}
      <pre><code>{expected}</code></pre>
    </div>
    """
    return _doc_shell(
        page_key="index",
        title="Documentation Home",
        lead="A docs-first entry point inspired by scikit-learn: separate pages, strong left navigation, and clear boundaries between tutorials, API reference, and ecosystem guidance.",
        body=body,
    )


def project_getting_started_html(*, version: str = PACKAGE_VERSION) -> str:
    expected = escape("\n".join(QUICKSTART_EXPECTED_LINES))
    zero_cards = "".join(
        "<div class='docs-card'>"
        f"{_pill(item['title'], 'blue')}"
        f"<p>{escape(item['why'])}</p>"
        "</div>"
        for item in ZERO_INSTALL_OPTIONS
    )
    body = f"""
    <div class='docs-grid-2'>
      <div class='docs-card'>
        {_pill('Install', 'sun')}
        <pre><code>{escape(QUICKSTART_INSTALL)}</code></pre>
        <p>EchoTime keeps the install surface light, but mixed scientific Python stacks can still produce resolver noise. Use a clean environment when possible, and use the compatibility / doctor flow when you cannot.</p>
      </div>
      <div class='docs-card'>
        {_pill('What this page is for', 'blue')}
        <ul class='panel-list'>
          <li>Read data with pandas or NumPy.</li>
          <li>Call one EchoTime function.</li>
          <li>Print a summary card first; export HTML second.</li>
        </ul>
      </div>
    </div>
    <div class='docs-grid-2'>
      <div class='docs-card'>
        {_pill('Compare two columns', 'sun')}
        <pre><code>import pandas as pd
from echotime import compare_series

df = pd.read_csv("my_metrics.csv")
report = compare_series(df["sessions"], df["signups"])
print(report.to_summary_card_markdown())</code></pre>
        <p>Use this when your question is "does column A move like column B?"</p>
      </div>
      <div class='docs-card'>
        {_pill('Profile a wide table', 'blue')}
        <pre><code>import pandas as pd
from echotime import profile_dataset

df = pd.read_csv("my_timeseries.csv").rename(columns={{"date": "timestamp"}})
profile = profile_dataset(df, domain="energy")
print(profile.to_summary_card_markdown())</code></pre>
        <p>Use this when you have one timestamp column and multiple numeric measurements.</p>
      </div>
    </div>
    <div class='docs-grid-2'>
      <div class='docs-card'>
        {_pill('Profile an irregular long table', 'sun')}
        <pre><code>import pandas as pd
from echotime import profile_dataset

df = pd.read_csv("patient_vitals.csv").rename(columns={{
    "patient_id": "subject",
    "charttime": "timestamp",
    "lab_name": "channel",
    "lab_value": "value",
}})
profile = profile_dataset(df, domain="clinical")
print(profile.to_summary_card_markdown())</code></pre>
        <p>Use this when your data are sparse or irregular and live in rows instead of a clean matrix.</p>
      </div>
      <div class='docs-card'>
        {_pill('Expected output', 'blue')}
        <pre><code>{expected}</code></pre>
        <p>Once the summary card looks sensible, write <span class='inline-code'>to_html_report()</span> to disk if you want a shareable artifact.</p>
      </div>
    </div>
    <div class='docs-grid-2'>
      {zero_cards}
    </div>
    <div class='docs-card'>
      {_pill('Practical notes', 'blue')}
      <ul class='panel-list'>
        <li>Core install is intentionally small: numpy and scipy.</li>
        <li>Older aeon / sktime / numba-heavy stacks may still surface resolver warnings.</li>
        <li>If your column names differ, rename them to aliases like timestamp, subject, channel, and value before the first run.</li>
        <li>If you only need proof of value first, use the static Pages bundle or local demo instead of installing into a crowded environment immediately.</li>
      </ul>
    </div>
    """
    return _doc_shell(
        page_key="getting-started",
        title="Getting Started",
        lead="The job of this page is simple: make the first successful EchoTime interaction obvious, fast, and realistic.",
        body=body,
    )


def project_tutorials_html(*, version: str = PACKAGE_VERSION) -> str:
    examples = _tutorial_examples()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in examples:
        grouped[entry["category"]].append(entry)

    group_order = [
        ("Beginner example", "Short, low-friction walkthroughs that make the package legible in a few minutes."),
        ("Cross-disciplinary example", "Examples where timestamps, cohorts, or domain structure matter enough to change the similarity story."),
        ("Flagship demo", "Examples built to travel in talks, README sections, social posts, and benchmark discussions."),
    ]
    sections = []
    for category, blurb in group_order:
        group_entries = grouped.get(category, [])
        if not group_entries:
            continue
        cards = []
        for entry in group_entries:
            report_href = _example_report_href(entry)
            cards.append(
                "<article class='gallery-card'>"
                f"<a class='gallery-thumb' href='{entry['href']}'>{entry['preview_svg']}</a>"
                "<div class='gallery-body'>"
                f"<div class='gallery-kicker'>{escape(category)}</div>"
                f"<h3><a href='{entry['href']}'>{escape(entry['title'])}</a></h3>"
                f"<p>{escape(entry['lead'])}</p>"
                f"<div class='meta-line'><span class='meta-chip'><strong>Input</strong> {escape(entry['input_shape'])}</span><span class='meta-chip'><strong>Result</strong> {escape(entry['score_text'])}</span></div>"
                "<div class='gallery-links'>"
                f"<a href='{entry['href']}'>Open example</a>"
                + (f"<a href='{report_href}'>Open report</a>" if report_href else "")
                + f"<a href='{_example_source_href(entry)}'>View source</a>"
                + "</div>"
                "</div>"
                "</article>"
            )
        sections.append(
            "<section class='gallery-section'>"
            f"<div><h2>{escape(category)}s</h2><p class='muted'>{escape(blurb)}</p></div>"
            f"<div class='gallery-grid'>{''.join(cards)}</div>"
            "</section>"
        )
    rows = "\n".join(
        f"<tr><td><strong>{escape(item['title'])}</strong><br><span class='muted'>{escape(item['name'])}</span></td><td>{escape(item['domain'])}</td><td>{escape(item['kind'])}</td><td>{escape(item['why'])}</td></tr>"
        for item in list_starter_datasets()
    )
    hero_html = """
    <div class='example-page-intro'>
      <div class='example-head'>
        <div class='eyebrow'>Examples gallery</div>
        <h1>Tutorials and runnable examples</h1>
        <p class='subhead'>A scikit-learn-style example index: each page starts from a concrete question, shows the runnable code, and then shows the result.</p>
      </div>
    </div>
    """
    body = f"""
    <div class='docs-card'>
      {_pill('Tutorial map', 'sun')}
      <p>This page is a real example gallery built from frozen snapshots of public data. Every entry below links to a dedicated page generated from an actual EchoTime run, with visual outputs, runnable source code, local CSV snapshots, and links to reports or story assets where they exist.</p>
    </div>
    {"".join(sections)}
    <div class='docs-card'>
      {_pill('Built-in starter datasets', 'sun')}
      <p>The examples above use real public data. The table below is different: these are the small built-in starter datasets that ship with EchoTime for offline smoke tests and quick local experiments.</p>
      <table class='small-table'>
        <thead><tr><th>Dataset</th><th>Domain</th><th>Kind</th><th>Why it exists</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return _doc_shell(
        page_key="tutorials",
        title="Tutorials and Examples",
        lead="Begin with real public-data examples, then move to richer reports and story assets when you need them.",
        body=body,
        sidebar_sections=(_example_sidebar(examples, ""),),
        hero_html=hero_html,
    )


def project_api_reference_html(*, version: str = PACKAGE_VERSION) -> str:
    grouped = defaultdict(list)
    for entry in API_ENTRIES:
        grouped[_clean(entry.category)].append(entry)
    sections = []
    for category, entries in grouped.items():
        entry_html = []
        for entry in entries:
            accepted = "".join(f"<li>{escape(_clean(item))}</li>" for item in entry.accepted_inputs)
            outputs = "".join(f"<li>{escape(_clean(item))}</li>" for item in entry.outputs_to_inspect)
            envs = ", ".join(_clean(item) for item in entry.recommended_environments)
            entry_html.append(
                "<div class='entry'>"
                f"<h3><span class='inline-code'>{escape(entry.name)}</span></h3>"
                f"<p><strong>Signature:</strong> <span class='inline-code'>{escape(_clean(entry.signature))}</span></p>"
                f"<p><strong>Purpose:</strong> {escape(_clean(entry.purpose))}</p>"
                f"<p><strong>Why this exists:</strong> {escape(_clean(entry.why_exists))}</p>"
                f"<p><strong>When to use it:</strong> {escape(_clean(entry.when_to_use))}</p>"
                f"<p><strong>Returns:</strong> {escape(_clean(entry.returns))}</p>"
                f"<p><strong>Recommended environments:</strong> {escape(envs)}</p>"
                "<div class='docs-grid-2'>"
                f"<div><strong>Accepted inputs</strong><ul class='panel-list'>{accepted}</ul></div>"
                f"<div><strong>Inspect these outputs</strong><ul class='panel-list'>{outputs}</ul></div>"
                "</div>"
                "</div>"
            )
        sections.append(
            "<div class='docs-card'>"
            f"{_pill(category, 'blue')}"
            f"<div class='entry-stack'>{''.join(entry_html)}</div>"
            "</div>"
        )
    body = "".join(sections)
    return _doc_shell(
        page_key="api",
        title="API Reference",
        lead="The public API surface is intentionally small and role-based: compare, profile, summarize, and hand off.",
        body=body,
    )


def _atlas_status_tone(label: str) -> str:
    if label == "Implemented in EchoTime":
        return "sun"
    if label == "High-fit addition":
        return "sun"
    if label == "Conceptually covered":
        return "blue"
    if label == "Possible addition":
        return ""
    return ""


def _formula_html(formula: str) -> str:
    return f"<code class='formula-chip'>{escape(formula)}</code>"


def project_similarity_methods_html(*, version: str = PACKAGE_VERSION) -> str:
    atlas = similarity_method_atlas_dict()
    summary = atlas["summary"]
    native_methods = atlas["native_methods"]
    recommended = atlas["recommended_additions"]
    families = atlas["families"]
    counts_by_status = summary["counts_by_status"]

    extra_css = """
    .formula-chip { display:block; font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace; white-space: normal; overflow-wrap: anywhere; line-height: 1.5; background: #fffef8; border:1px solid var(--border); border-radius: 12px; padding: 10px 12px; }
    .native-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
    .native-card { display:grid; gap: 10px; }
    .status-stack { display:flex; flex-wrap:wrap; gap: 10px; }
    .table-note { color: var(--text-600); font-size: 0.92rem; }
    @media (max-width: 980px) {
      .native-grid { grid-template-columns: 1fr; }
    }
    """

    status_order = (
        "Implemented in EchoTime",
        "High-fit addition",
        "Conceptually covered",
        "Possible addition",
        "Low-priority addition",
    )
    status_chips = "".join(
        f"<span class='meta-chip'><strong>{escape(label)}</strong> {count}</span>"
        for label in status_order
        if label in counts_by_status
        for count in (counts_by_status[label],)
    )
    native_cards = "".join(
        "<article class='docs-card native-card'>"
        f"{_pill(entry['name'], 'blue' if 'reference metric' in entry['family'].lower() else 'sun')}"
        f"<p><strong>Family:</strong> {escape(entry['family'])}</p>"
        f"<p><strong>Kind:</strong> {escape(entry['kind'])}</p>"
        f"{_formula_html(entry['formula'])}"
        f"<p>{escape(entry['notes'])}</p>"
        "</article>"
        for entry in native_methods
    )
    recommended_rows = "".join(
        "<tr>"
        f"<td><strong>{escape(entry['name'])}</strong><br><span class='muted'>{escape(entry['family'])}</span></td>"
        f"<td><span class='pill {_atlas_status_tone(entry['echotime_status'])}'>{escape(entry['echotime_status'])}</span></td>"
        f"<td><span class='inline-code'>{escape(entry['echotime_api'] or '-')}</span></td>"
        f"<td>{_formula_html(entry['formula'])}</td>"
        f"<td>{escape(entry['echotime_rationale'])}</td>"
        "</tr>"
        for entry in recommended
    )

    family_sections = []
    for family in families:
        rows = "".join(
            "<tr>"
            f"<td><strong>{escape(entry['name'])}</strong></td>"
            f"<td>{escape(entry['kind'])}</td>"
            f"<td>{escape(entry['metric'])}</td>"
            f"<td>{escape(entry['complexity'])}</td>"
            f"<td>{escape(entry['unequal_length'])}</td>"
            f"<td>{escape(entry['multivariate'])}</td>"
            f"<td>{escape(entry['implementation'])}</td>"
            f"<td><span class='pill {_atlas_status_tone(entry['echotime_status'])}'>{escape(entry['echotime_status'])}</span></td>"
            f"<td><span class='inline-code'>{escape(entry['echotime_api'] or '-')}</span></td>"
            f"<td>{_formula_html(entry['formula'])}</td>"
            f"<td>{escape(entry['notes'])}</td>"
            "</tr>"
            for entry in family["entries"]
        )
        family_sections.append(
            "<section class='docs-card'>"
            f"{_pill(family['name'], 'sun')}"
            f"<p>{escape(family['description'])}</p>"
            "<table class='small-table'>"
            "<thead><tr><th>Method</th><th>Output</th><th>Metric</th><th>Complexity</th><th>Unequal length</th><th>Multivariate</th><th>Implementation</th><th>EchoTime fit</th><th>EchoTime API</th><th>Formula</th><th>Note</th></tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
            "</section>"
        )

    body = f"""
    <div class='docs-grid-2'>
      <div class='docs-card'>
        {_pill('Audit summary', 'sun')}
        <p><strong>This page imports the full method registry from `ts_similarity_package_v2_pkg` and audits which parts fit EchoTime's report-first product direction.</strong></p>
        <div class='meta-line'>
          <span class='meta-chip'><strong>EchoTime native</strong> {summary['native_method_count']}</span>
          <span class='meta-chip'><strong>Extracted methods</strong> {summary['extracted_method_count']}</span>
          <span class='meta-chip'><strong>Families</strong> {summary['family_count']}</span>
          <span class='meta-chip'><strong>High-fit / implemented</strong> {summary['recommended_method_count']}</span>
          <span class='meta-chip'><strong>Version</strong> {escape(version)}</span>
        </div>
        <div class='status-stack'>{status_chips}</div>
      </div>
      <div class='docs-card'>
        {_pill('What EchoTime now exposes', 'blue')}
        <ul class='panel-list'>
          <li><strong>max_ncc / best_shift / sbd</strong> now cover explicit lead-lag and shift-aware similarity.</li>
          <li><strong>independent_max_ncc / independent_sbd</strong> now cover the channel-independent multivariate sliding variants highlighted by the v2 package.</li>
          <li><strong>periodogram_distance</strong> and <strong>trend_distance</strong> now add direct frequency-domain and trend-feature distances.</li>
          <li><strong>ordinal_pattern_js_distance</strong> and <strong>linear_trend_model_distance</strong> now cover symbolic rhythm comparison and lightweight trend-model comparison.</li>
          <li><strong>twed_distance</strong> now covers timestamp-aware elastic comparison for irregular series.</li>
          <li><strong>erp_distance</strong>, <strong>lcss_similarity</strong>, <strong>lcss_distance</strong>, and <strong>edr_distance</strong> now cover robust partial-match and gap-aware elastic matching.</li>
          <li><strong>acf_distance</strong> now adds a rhythm-focused structural distance beside the existing report-level spectral view.</li>
        </ul>
      </div>
    </div>
    <div class='docs-card'>
      {_pill('Current EchoTime comparison layer', 'sun')}
      <p class='table-note'>These are the similarity characterizations EchoTime already uses in raw-series comparison reports. Every entry below includes the mathematical expression used or approximated by the current code path.</p>
      <div class='native-grid'>{native_cards}</div>
    </div>
    <div class='docs-card'>
      {_pill('Operating modes for elastic methods', 'blue')}
      <ul class='panel-list'>
        <li><strong>`mode=\"exact\"`</strong> keeps the full elastic score path and stays the default when you need a final value for a report, notebook, or paper.</li>
        <li><strong>`mode=\"fast\"`</strong> is the screening path for large candidate pools and interactive shortlist work; it favors speed over exact-path fidelity.</li>
        <li><strong>`window=...`</strong> is available on `lcss_similarity`, `lcss_distance`, `edr_distance`, `erp_distance`, and `twed_distance` so you can keep the dynamic-programming path local when large warps are not plausible.</li>
        <li><strong>Recommended workflow:</strong> score all candidates with `mode="fast"` first, then rerun the shortlisted pairs with `mode="exact"` before you present the result as a final analog claim.</li>
      </ul>
    </div>
    <div class='docs-card'>
      {_pill('Implemented and high-fit additions from ts_similarity_package_v2_pkg', 'blue')}
      <p class='table-note'>This table stays selective: it shows only the methods already added to EchoTime and the strongest candidates from the 127-method v2 registry. In the current build, the full high-fit shortlist is already implemented.</p>
      <table class='small-table'>
        <thead><tr><th>Method</th><th>EchoTime fit</th><th>EchoTime API</th><th>Formula</th><th>Why it fits</th></tr></thead>
        <tbody>{recommended_rows}</tbody>
      </table>
    </div>
    {''.join(family_sections)}
    """
    return _doc_shell(
        page_key="methods",
        title="Similarity Methods Atlas",
        lead="A full audit of EchoTime's current comparison math plus the 127 extracted time-series similarity methods from ts_similarity_package_v2_pkg, each with an explicit mathematical expression.",
        body=body,
        extra_css=extra_css,
    )


def project_scenarios_html(*, version: str = PACKAGE_VERSION) -> str:
    cards = []
    for scenario in SCENARIOS:
        environments = ", ".join(_clean(item) for item in scenario.environments)
        domains = ", ".join(_clean(item) for item in scenario.domains)
        inputs = "".join(f"<li>{escape(_clean(item))}</li>" for item in scenario.typical_inputs)
        actions = "".join(f"<li>{escape(_clean(item))}</li>" for item in scenario.what_you_can_do)
        caveats = "".join(f"<li>{escape(_clean(item))}</li>" for item in scenario.caveats)
        cards.append(
            "<div class='docs-card'>"
            f"{_pill(scenario.title, 'sun')}"
            f"<div class='meta-line'><span class='meta-chip'><strong>Domains</strong> {escape(domains)}</span><span class='meta-chip'><strong>Environments</strong> {escape(environments)}</span></div>"
            f"<p><strong>Data shape:</strong> {escape(_clean(scenario.data_shape))}</p>"
            f"<p><strong>Where EchoTime helps:</strong> {escape(_clean(scenario.echotime_role))}</p>"
            "<div class='docs-grid-2'>"
            f"<div><strong>Typical inputs</strong><ul class='panel-list'>{inputs}</ul></div>"
            f"<div><strong>What you can do</strong><ul class='panel-list'>{actions}</ul></div>"
            "</div>"
            f"<div><strong>Caveats</strong><ul class='panel-list'>{caveats}</ul></div>"
            "</div>"
        )
    body = "".join(cards)
    return _doc_shell(
        page_key="scenarios",
        title="Scenarios",
        lead="Use this page the way scikit-learn users use problem-oriented documentation: find your domain, then jump into the right entrypoint.",
        body=body,
    )


def project_ecosystem_html(*, version: str = PACKAGE_VERSION) -> str:
    eco = ecosystem_positioning(format="json")
    eco_rows = "\n".join(
        f"<tr><td><strong>{escape(entry['name'])}</strong></td><td>{escape(_clean(entry['family']))}</td><td>{escape(', '.join(entry['strongest_for'][:3]))}</td><td>{escape(_clean(entry['echotime_relation']))}</td></tr>"
        for entry in eco["entries"]
    )
    cov = coverage_matrix(format="json")
    cov_rows = "\n".join(
        f"<tr><td>{escape(_clean(row['capability']))}</td><td>{escape(_clean(row['echotime_role']))}</td><td>{escape(', '.join(row['best_companions']) if row['best_companions'] else '-')}</td><td>{escape(_clean(row['notes']))}</td></tr>"
        for row in cov["rows"]
    )
    body = f"""
    <div class='docs-card'>
      {_pill(ECOSYSTEM_HEADING, 'sun')}
      <table class='small-table'>
        <thead><tr><th>Package</th><th>Family</th><th>Strongest fit</th><th>How EchoTime fits</th></tr></thead>
        <tbody>{eco_rows}</tbody>
      </table>
    </div>
    <div class='docs-card'>
      {_pill('Capability coverage', 'blue')}
      <table class='small-table'>
        <thead><tr><th>Capability</th><th>Role</th><th>Companion packages</th><th>Notes</th></tr></thead>
        <tbody>{cov_rows}</tbody>
      </table>
    </div>
    """
    return _doc_shell(
        page_key="ecosystem",
        title="Ecosystem and Scope",
        lead="This page exists to keep the package honest. EchoTime should be easy to place next to sktime, tsfresh, DTAIDistance, STUMPY, and other neighboring tools.",
        body=body,
    )


def project_agents_html(*, version: str = PACKAGE_VERSION) -> str:
    body = f"""
    <div class='docs-card'>
      {_pill(AGENT_HEADING, 'sun')}
      <p><strong>EchoTime is agent-friendly because the outer surface is small and stable.</strong> The point is not to be a full orchestration platform. The point is to make the domain task cheap to route and easy to consume.</p>
      <pre><code>ts_profile({{data_ref, input_kind, timestamps_ref, domain, budget, audience}})
ts_compare({{left_ref, right_ref, left_timestamps_ref, right_timestamps_ref, mode, budget}})
ts_route({{task, available_inputs, has_reference}})</code></pre>
      <div class='meta-line'>
        <span class='meta-chip'><strong>Schema version</strong> {escape(TOOL_SCHEMA_VERSION)}</span>
        <span class='meta-chip'><strong>Surface</strong> compare-first</span>
      </div>
    </div>
    <div class='docs-grid-2'>
      <div class='docs-card'>
        {_pill('Stable envelope', 'blue')}
        <ul class='panel-list'>
          <li>schema_version</li>
          <li>tool</li>
          <li>ok</li>
          <li>confidence</li>
          <li>limitations</li>
          <li>evidence</li>
          <li>recommended_next_step</li>
          <li>next_actions</li>
        </ul>
      </div>
      <div class='docs-card'>
        {_pill('Why this matters', 'sun')}
        <ul class='panel-list'>
          <li>Agents do not need to scrape notebook prose.</li>
          <li>Routers can choose compare vs profile without guessing the whole package surface.</li>
          <li>Downstream apps can cache on compact, stable payloads.</li>
        </ul>
      </div>
    </div>
    """
    return _doc_shell(
        page_key="agents",
        title="Agent Tools",
        lead="A dedicated page for the function-calling and routing surface. This keeps agent material out of the homepage while still making it easy to discover.",
        body=body,
    )


def project_docs_pages(*, version: str = PACKAGE_VERSION) -> dict[str, str]:
    examples = _tutorial_examples()
    pages = {
        "guide/index.html": project_docs_home_html(version=version),
        "guide/getting-started.html": project_getting_started_html(version=version),
        "guide/tutorials.html": project_tutorials_html(version=version),
        "guide/api.html": project_api_reference_html(version=version),
        "guide/methods.html": project_similarity_methods_html(version=version),
        "guide/scenarios.html": project_scenarios_html(version=version),
        "guide/ecosystem.html": project_ecosystem_html(version=version),
        "guide/agents.html": project_agents_html(version=version),
    }
    for entry in examples:
        pages[f"guide/{entry['href']}"] = entry["page_html"]
    return pages


__all__ = [
    "project_docs_home_html",
    "project_getting_started_html",
    "project_tutorials_html",
    "project_api_reference_html",
    "project_similarity_methods_html",
    "project_scenarios_html",
    "project_ecosystem_html",
    "project_agents_html",
    "project_docs_pages",
]
