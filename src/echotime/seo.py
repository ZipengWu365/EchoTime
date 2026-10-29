"""Search metadata for the published EchoTime project site.

This layer only changes document heads and discovery files, never report data
or presentation. robots.txt belongs to the origin root, not /EchoTime/.
"""

from __future__ import annotations

import json
import re
from html import escape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin
from xml.sax.saxutils import escape as xml_escape

from .copydeck import AUTHOR_NAME, PACKAGE_VERSION, PROJECT_DOCUMENTATION_URL, PROJECT_REPOSITORY_URL

SITE_URL = PROJECT_DOCUMENTATION_URL
SOCIAL_IMAGE = urljoin(SITE_URL, "social/echotime_title_card.png")
_START = "<!-- echotime-search-metadata:start -->"
_END = "<!-- echotime-search-metadata:end -->"

DESCRIPTIONS = {
    "articles/index.html": "Read a cited guide to time-series similarity: task definitions, method selection, software comparisons, and verified primary references in English and Chinese.",
    "articles/time-series-similarity-guide.en.html": "Compare Euclidean distance, DTW, matrix profiles, learned representations, and Python tools by task, assumptions, invariances, and evidence limits.",
    "articles/time-series-similarity-guide.zh-CN.html": "时序相似性方法选型指南：比较欧氏距离、DTW、矩阵轮廓、学习表征和 Python 工具，说明任务定义、不变性、适用条件与证据边界。",
    "articles/what-time-series-similarity-measures.en.html": "Understand what time-series similarity methods retain, ignore and deform: original-paper mechanisms, controlled transformations, numerical examples and research questions.",
    "references/time-series-similarity-literature.html": "Explore a verified time-series similarity reading list with primary-source links, claim boundaries, recent research, and downloadable JSON and BibTeX references.",
    "index.html": "EchoTime is an open-source Python library for explainable time-series and dataset similarity, with component metrics, rolling comparisons, and HTML reports.",
    "start-here.html": "Get started with EchoTime: install the Python package, try a similarity example, open the static playground, and check your scientific Python environment.",
    "playground.html": "Explore EchoTime's static time-series similarity playground with example comparisons, component metrics, visual reports, and Python commands to reproduce them.",
    "guide/index.html": "EchoTime documentation: learn explainable time-series similarity, compare datasets, inspect methods, and integrate structured outputs with agent tools.",
    "guide/getting-started.html": "Install EchoTime and compare your first time series in Python. Learn input formats, starter datasets, interpretable metrics, and HTML report workflows.",
    "guide/tutorials.html": "Follow EchoTime tutorials for two-curve comparison, rolling similarity, irregular observations, dataset structure, market signals, and traffic examples.",
    "guide/api.html": "EchoTime Python API reference for time-series comparison, rolling similarity, structural profiling, report generation, starter datasets, and agent tools.",
    "guide/methods.html": "Browse EchoTime's time-series similarity methods atlas: assumptions, comparison families, practical trade-offs, limitations, and literature references.",
    "guide/similarity-lab.html": "Change one shared time-series pair and compare eleven similarity mechanisms through real alignments, features, contributions and reproducible numerical states.",
    "guide/scenarios.html": "Choose an EchoTime workflow for regular or irregular time series, event streams, missing data, multichannel datasets, and interpretable analog search.",
    "guide/ecosystem.html": "Understand EchoTime's role alongside forecasting, time-series similarity, feature extraction, and scientific Python libraries, including scope and limitations.",
    "guide/agents.html": "Use EchoTime agent tools with structured JSON envelopes, input contracts, tool schemas, caching metadata, and explainable time-series comparison results.",
    "guide/example-two-curves-similarity.html": "Compare two curves with EchoTime in Python and interpret familiar statistics, time-series-specific component metrics, and the limits of a similarity verdict.",
    "guide/example-weekly-traffic-signals.html": "Work through EchoTime's traffic-signal example: inspect series structure, compare related curves, and reproduce the visual similarity report in Python.",
    "guide/example-irregular-patient-similarity.html": "Explore EchoTime's irregular-observation tutorial, including explicit timestamps, sampling gaps, structural profiles, and reproducible Python examples.",
    "guide/example-github-breakout-analogs.html": "Reproduce an EchoTime attention-breakout comparison using public data, normalized curves, rolling similarity, and interpretable component diagnostics.",
    "guide/example-btc-gold-under-shocks.html": "Follow EchoTime's market-series tutorial using a public-data snapshot, rolling comparisons, component metrics, and explicit limits on analog interpretation.",
    "guide/example-heatwave-grid-load.html": "Inspect public heatwave temperature data with EchoTime's structural profiling tutorial, visual diagnostics, and reproducible Python source examples.",
    "blog/github_breakout_analogs.html": "Explore a reproducible attention-breakout case study with EchoTime: compare curve shapes, inspect rolling diagnostics, and open the data and Python source.",
    "blog/btc_vs_gold_under_shocks.html": "Read EchoTime's market-series case study with public source data, normalized overlays, rolling similarity, component diagnostics, and interpretation guardrails.",
    "blog/heatwave_vs_grid_load.html": "Explore a public-data heatwave case study with EchoTime: compare temperature patterns, inspect structural profiles, and reproduce the visual report.",
    "reports/weekly_website_traffic_report.html": "Inspect an EchoTime traffic and pageview dataset report with structural axes, visual diagnostics, context for comparison, and interpretation notes.",
    "reports/irregular_patient_vitals_report.html": "Inspect an EchoTime irregular event-stream report with sampling structure, visual diagnostics, structural axes, and explicit interpretation notes.",
    "reports/github_breakout_similarity.html": "View EchoTime's attention-breakout similarity report with curve overlays, rolling windows, component metrics, familiar statistics, and comparison guardrails.",
    "reports/btc_vs_gold_similarity.html": "View EchoTime's market-series similarity report with curve overlays, rolling windows, component diagnostics, familiar statistics, and interpretation limits.",
    "reports/energy_load_heatwave_report.html": "View EchoTime's heatwave temperature dataset report with structural profiles, visual axes, sampling context, and interpretation notes.",
}


class _TitleParser(HTMLParser):
    """Read the HTML document title without mistaking SVG titles for it."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_title = False
        self.parts: list[str] = []
        self.language = "en"

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "html":
            self.language = dict(attrs).get("lang") or "en"
        elif tag == "head":
            self.in_head = True
        elif tag == "title" and self.in_head:
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "head":
            self.in_head = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.parts.append(data)


def canonical_url(path: str) -> str:
    if path == "index.html":
        path = ""
    elif path.endswith("/index.html"):
        path = path[:-len("index.html")]
    return urljoin(SITE_URL, path)


def search_metadata(html: str, path: str, *, version: str = PACKAGE_VERSION) -> str:
    """Attach one idempotent metadata block to a published HTML page."""
    html = re.sub(re.escape(_START) + r".*?" + re.escape(_END) + r"\n?", "", html, flags=re.S)
    if path == "404.html":
        block = f'{_START}\n<meta name="robots" content="noindex, follow">\n{_END}'
    else:
        parser = _TitleParser()
        parser.feed(html)
        title = " ".join("".join(parser.parts).split())
        if not title:
            raise ValueError(f"Missing document title: {path}")
        # New pages should get an intentional summary, not a duplicated default.
        description = DESCRIPTIONS[path]
        url = canonical_url(path)
        page: dict[str, Any] = {
            "@type": "WebPage", "@id": url + "#webpage", "url": url,
            "name": title, "description": description, "inLanguage": parser.language,
            "isPartOf": {"@id": SITE_URL + "#website"},
        }
        graph: list[dict[str, Any]] = [
            {"@type": "WebSite", "@id": SITE_URL + "#website", "url": SITE_URL, "name": "EchoTime"},
            page,
        ]
        if path == "index.html":
            graph.append({
                "@type": "SoftwareSourceCode", "@id": SITE_URL + "#software",
                "name": "EchoTime", "description": description, "url": SITE_URL,
                "codeRepository": PROJECT_REPOSITORY_URL, "programmingLanguage": "Python",
                "version": version, "license": "https://opensource.org/license/mit/",
                "author": {"@type": "Person", "name": AUTHOR_NAME},
            })
            page["about"] = {"@id": SITE_URL + "#software"}
        else:
            crumbs = [{"@type": "ListItem", "position": 1, "name": "EchoTime", "item": SITE_URL}]
            if path.startswith("guide/") and path != "guide/index.html":
                crumbs.append({"@type": "ListItem", "position": 2, "name": "Documentation", "item": canonical_url("guide/index.html")})
            crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1, "name": title, "item": url})
            graph.append({"@type": "BreadcrumbList", "@id": url + "#breadcrumbs", "itemListElement": crumbs})
            page["breadcrumb"] = {"@id": url + "#breadcrumbs"}
        schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("<", "\\u003c")
        tags = [
            f'<meta name="description" content="{escape(description, quote=True)}">',
            f'<link rel="canonical" href="{escape(url, quote=True)}">',
            '<meta name="robots" content="index, follow, max-image-preview:large">',
            '<meta property="og:type" content="website">',
            '<meta property="og:site_name" content="EchoTime">',
            f'<meta property="og:title" content="{escape(title, quote=True)}">',
            f'<meta property="og:description" content="{escape(description, quote=True)}">',
            f'<meta property="og:url" content="{escape(url, quote=True)}">',
            f'<meta property="og:image" content="{SOCIAL_IMAGE}">',
            '<meta property="og:image:alt" content="EchoTime: explainable time-series similarity">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{escape(title, quote=True)}">',
            f'<meta name="twitter:description" content="{escape(description, quote=True)}">',
            f'<meta name="twitter:image" content="{SOCIAL_IMAGE}">',
            f'<link rel="sitemap" type="application/xml" href="{SITE_URL}sitemap.xml">',
            f'<link rel="manifest" href="{SITE_URL}site.webmanifest">',
            f'<script type="application/ld+json">{schema}</script>',
        ]
        block = _START + "\n" + "\n".join(tags) + "\n" + _END
    if "</head>" not in html:
        raise ValueError(f"Missing document head: {path}")
    return html.replace("</head>", block + "\n</head>", 1)


def enrich_pages_bundle(bundle: dict[str, Any], *, version: str = PACKAGE_VERSION) -> dict[str, Any]:
    """Add discovery metadata without adding a project-scoped robots.txt."""
    result = dict(bundle)
    urls: list[str] = []
    for path, content in bundle.items():
        if path.endswith(".html"):
            result[path] = search_metadata(content, path, version=version)
            if path != "404.html":
                urls.append(canonical_url(path))
    entries = "\n".join(f"  <url><loc>{xml_escape(url)}</loc></url>" for url in sorted(set(urls)))
    result["sitemap.xml"] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + entries + "\n</urlset>\n"
    return result
