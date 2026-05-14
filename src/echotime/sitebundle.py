"""GitHub Pages-ready bundle helpers for EchoTime.

These helpers do not deploy anything by themselves. They generate a richer
static site bundle that can be published through GitHub Pages or any static
file host. The bundle now includes homepage, playground, flagship reports,
social cards, blog-style explainers, and a small manifest describing the demo
surface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .copydeck import FLAGSHIP_DEMOS, PACKAGE_VERSION
from .docs_site import project_docs_pages
from .homepage import project_homepage_html
from .launchpad import project_launchpad_html
from .playground import project_playground_html
from .profile import profile_dataset
from .real_tutorial_data import (
    ai_attention_breakouts,
    btc_oil_vix_2024,
    heatwave_city_temps_2024,
    python_javascript_pageviews_2024,
    usgs_earthquakes_ca_ak_2024,
)
from .runtime_paths import resolve_repo_subdir
from .similarity import compare_series, rolling_similarity
from .visuals import (
    axis_bar_svg,
    profile_html_report,
    profile_radar_svg,
    profile_social_card_svg,
    rolling_similarity_svg,
    series_overlay_svg,
    similarity_html_report,
    similarity_radar_svg,
    similarity_social_card_svg,
)


def _blog_page(
    *,
    title: str,
    deck: str,
    report_href: str,
    social_href: str,
    support_note: str,
    data_href: str,
    source_data_href: str,
    bullets: list[str],
    visuals: list[dict[str, str]],
    source_href: str,
) -> str:
    bullet_html = "".join(f"<li>{item}</li>" for item in bullets)
    visual_html = "".join(
        "<div class='visual-card'>"
        f"<div class='visual-label'>{item['label']}</div>"
        f"<div class='visual-frame'>{item['svg']}</div>"
        f"<p>{item['caption']}</p>"
        "</div>"
        for item in visuals
    )
    return f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>{title} - EchoTime demo story</title>
<style>
:root {{ --bg:#ffffff; --ink:#1F2937; --muted:#6B7280; --line:#E5E7EB; --panel:#ffffff; --panel-soft:#FAFAFA; --brand:#2F6BFF; --sun:#FFC83D; --shadow:0 1px 2px rgba(17,24,39,.04),0 14px 34px rgba(17,24,39,.08); --max:1024px; }}
* {{ box-sizing:border-box; }} body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; background:var(--bg); color:var(--ink); }}
.container {{ width:min(var(--max), calc(100vw - 28px)); margin:0 auto; padding:28px 0 42px; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:22px 24px; box-shadow:var(--shadow); margin-bottom:18px; }}
.hero {{ display:grid; gap:16px; }}
.hero-grid {{ display:grid; grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr); gap:18px; align-items:start; }}
.pill {{ display:inline-block; padding:4px 10px; border-radius:999px; background:#eef5ff; color:var(--brand); font-size:.88rem; font-weight:700; margin-right:8px; }}
.pill.sun {{ background:#fff4c2; color:#a16207; }}
a {{ color:var(--brand); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
h1 {{ margin:0 0 10px; font-size:clamp(2rem,4vw,3rem); line-height:1.05; letter-spacing:-.04em; }} h2 {{ margin:0 0 10px; font-size:1.22rem; }} p.lead {{ color:var(--muted); font-size:1.05rem; }} ul {{ margin:0; padding-left:1.2rem; }}
.meta {{ display:grid; gap:12px; }}
.metric {{ border:1px solid var(--line); background:var(--panel-soft); border-radius:16px; padding:14px 16px; }}
.metric strong {{ display:block; font-size:.82rem; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); margin-bottom:6px; }}
.metric span {{ font-size:1.6rem; font-weight:800; letter-spacing:-.03em; color:var(--ink); }}
.visual-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
.visual-card {{ background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:18px; box-shadow:var(--shadow); }}
.visual-card p {{ color:var(--muted); margin:12px 0 0; }}
.visual-label {{ display:inline-flex; align-items:center; padding:6px 12px; border-radius:999px; background:#fff4c2; color:#a16207; font-size:.84rem; font-weight:800; margin-bottom:12px; }}
.visual-frame {{ border:1px solid var(--line); border-radius:16px; background:linear-gradient(180deg,#fffdfa 0%,#ffffff 100%); padding:10px; overflow:hidden; }}
.visual-frame svg {{ display:block; width:100%; height:auto; }}
.asset-list {{ display:grid; gap:10px; }}
.asset-list a {{ display:block; padding:12px 14px; border-radius:14px; border:1px solid var(--line); background:var(--panel-soft); font-weight:700; }}
@media (max-width: 860px) {{ .hero-grid, .visual-grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<div class='container'>
  <div class='card hero'>
    <div><span class='pill sun'>flagship story</span><span class='pill'>EchoTime</span></div>
    <div class='hero-grid'>
      <div>
        <h1>{title}</h1>
        <p class='lead'>{deck}</p>
      </div>
      <div class='meta'>
        <div class='metric'><strong>Open assets</strong><span>Report + story + card</span></div>
        <div class='metric'><strong>Use case</strong><span>Explainable similarity demo</span></div>
      </div>
    </div>
  </div>
  <div class='card'>
    <h2>Why this demo travels</h2>
    <ul>{bullet_html}</ul>
  </div>
  <div class='visual-grid'>
    {visual_html}
  </div>
  <div class='card'>
    <h2>Open the assets</h2>
    <div class='asset-list'>
      <a href='../{report_href}'>Open the HTML report</a>
      <a href='../{social_href}'>Open the social card</a>
      <a href='{source_href}'>Open the Python source</a>
      <a href='{data_href}'>Open the local CSV snapshot</a>
      <a href='{source_data_href}'>Open the upstream public source</a>
    </div>
  </div>
  <div class='card'>
    <h2>Data note</h2>
    <p>{support_note}</p>
  </div>
</div>
</body>
</html>"""


def project_demo_manifest(*, version: str = PACKAGE_VERSION) -> dict[str, Any]:
    return {
        "version": version,
        "product_surface": "explainable time-series similarity for humans and agents",
        "pages": {
            "homepage": "index.html",
            "start_here": "start-here.html",
            "playground": "playground.html",
            "reports": {
                "weekly_website_traffic": "reports/weekly_website_traffic_report.html",
                "irregular_patient_vitals": "reports/irregular_patient_vitals_report.html",
                "github_breakout": "reports/github_breakout_similarity.html",
                "btc_vs_gold": "reports/btc_vs_gold_similarity.html",
                "energy_load_heatwave": "reports/energy_load_heatwave_report.html",
            },
            "blog": {
                "github_breakout": "blog/github_breakout_analogs.html",
                "btc_vs_gold": "blog/btc_vs_gold_under_shocks.html",
                "heatwave_grid_load": "blog/heatwave_vs_grid_load.html",
            },
        },
        "flagship_demos": list(FLAGSHIP_DEMOS),
        "notes": [
            "The Pages bundle is static and similarity-showcase-oriented.",
            "Use echotime-demo locally when you need real computation on pasted arrays.",
        ],
        "public_demo_url_hint": "https://<your-github-username>.github.io/EchoTime/",
        "external_evidence_status": "seeking public showcase submissions and third-party case studies",
    }


def project_pages_bundle(*, version: str = PACKAGE_VERSION) -> dict[str, str]:
    assets_root = resolve_repo_subdir("assets", sentinel="echotime_title_card.svg")
    title_card = (assets_root / "echotime_title_card.svg").read_text(encoding="utf-8") if (assets_root / "echotime_title_card.svg").exists() else ""
    mark_svg = (assets_root / "echotime_mark.svg").read_text(encoding="utf-8") if (assets_root / "echotime_mark.svg").exists() else ""
    affiliation_svg = (assets_root / "bham_affiliation_badge.svg").read_text(encoding="utf-8") if (assets_root / "bham_affiliation_badge.svg").exists() else ""
    pageviews = python_javascript_pageviews_2024()
    pageview_profile = profile_dataset(pageviews["values"], domain="traffic", channel_names=pageviews["channels"])

    earthquakes = usgs_earthquakes_ca_ak_2024()
    earthquake_profile = profile_dataset(earthquakes["event_records"], domain="earth_science")

    attention = ai_attention_breakouts()
    attention_report = compare_series(attention["deepseek_cumulative"], attention["threads_cumulative"], left_name="DeepSeek", right_name="Threads")
    attention_roll = rolling_similarity(attention["deepseek_cumulative"], attention["threads_cumulative"], window=20, step=5)

    markets = btc_oil_vix_2024()
    market_report = compare_series(markets["btc_usd"], markets["vix"], left_name="BTC", right_name="VIX")
    market_roll = rolling_similarity(markets["btc_usd"], markets["vix"], window=30, step=10)

    heatwave = heatwave_city_temps_2024()
    heat_profile = profile_dataset(heatwave["values"], domain="climate", channel_names=heatwave["channels"])

    manifest = json.dumps(project_demo_manifest(version=version), indent=2)

    return {
        "index.html": project_homepage_html(version=version),
        "start-here.html": project_launchpad_html(version=version),
        "playground.html": project_playground_html(version=version),
        "404.html": project_launchpad_html(version=version),
        ".nojekyll": "",
        "manifest/demo_manifest.json": manifest,
        "site.webmanifest": json.dumps({"name": "EchoTime", "short_name": "EchoTime", "start_url": "/", "display": "standalone"}, indent=2),
        "social/echotime_title_card.svg": title_card,
        "social/echotime_mark.svg": mark_svg,
        "social/bham_affiliation_badge.svg": affiliation_svg,
        "reports/weekly_website_traffic_report.html": profile_html_report(pageview_profile, title="Python and JavaScript pageviews"),
        "reports/irregular_patient_vitals_report.html": profile_html_report(earthquake_profile, title="California and Alaska earthquake streams"),
        "reports/github_breakout_similarity.html": similarity_html_report(
            attention_report,
            title="AI attention breakout analogs",
            left_series=attention["deepseek_cumulative"],
            right_series=attention["threads_cumulative"],
            rolling_windows=attention_roll,
        ),
        "reports/btc_vs_gold_similarity.html": similarity_html_report(
            market_report,
            title="BTC vs VIX in 2024",
            left_series=markets["btc_usd"],
            right_series=markets["vix"],
            rolling_windows=market_roll,
        ),
        "reports/energy_load_heatwave_report.html": profile_html_report(heat_profile, title="Southwest heatwave city temperatures"),
        "social/weekly_website_traffic_card.svg": profile_social_card_svg(pageview_profile, title="Python vs JavaScript pageviews"),
        "social/irregular_patient_vitals_card.svg": profile_social_card_svg(earthquake_profile, title="California vs Alaska earthquake streams"),
        "social/github_breakout_card.svg": similarity_social_card_svg(attention_report, title="AI attention breakout analogs"),
        "social/btc_vs_gold_card.svg": similarity_social_card_svg(market_report, title="BTC vs VIX in 2024"),
        "social/energy_load_card.svg": profile_social_card_svg(heat_profile, title="Southwest heatwave city temperatures"),
        "blog/github_breakout_analogs.html": _blog_page(
            title="AI attention breakout analogs",
            deck="A showcase story for asking which historical attention breakout DeepSeek looked most like over its first breakout window.",
            report_href="reports/github_breakout_similarity.html",
            social_href="social/github_breakout_card.svg",
            support_note="This story uses a frozen local CSV snapshot plus the upstream Wikimedia pageviews endpoint so the result stays reproducible.",
            data_href="https://github.com/ZipengWu365/EchoTime/blob/main/examples/data/real_ai_attention_breakouts.csv",
            source_data_href=attention["source_url"],
            bullets=[
                "The question is easy to understand even if the reader is not a time-series specialist.",
                "The report makes the analog choice explicit instead of leaving it at anecdote level.",
                "The same asset pack works in docs, social cards, and project updates.",
            ],
            visuals=[
                {
                    "label": "Series overlay",
                    "svg": series_overlay_svg(attention["deepseek_cumulative"], attention["threads_cumulative"], left_label="DeepSeek", right_label="Threads"),
                    "caption": "The closest analog stays shape-aligned enough that the story is visible before you read the verdict.",
                },
                {
                    "label": "Similarity radar",
                    "svg": similarity_radar_svg(attention_report),
                    "caption": "The radar shows which time-series metrics keep supporting the analog and which ones stay weaker.",
                },
                {
                    "label": "Rolling component mean",
                    "svg": rolling_similarity_svg(attention_roll),
                    "caption": "Windowed component means show whether the analog survives beyond the first surge of attention.",
                },
            ],
            source_href="https://github.com/ZipengWu365/EchoTime/blob/main/examples/gallery/plot_github_breakout_analogs.py",
        ),
        "blog/btc_vs_gold_under_shocks.html": _blog_page(
            title="BTC vs VIX in 2024",
            deck="A macro narrative that turns rolling window diagnostics and regime-aware comparison into a shareable story without pretending the analogy is stronger than it is.",
            report_href="reports/btc_vs_gold_similarity.html",
            social_href="social/btc_vs_gold_card.svg",
            support_note="This story uses a frozen local CSV snapshot built from FRED so the exact comparison can be regenerated later.",
            data_href="https://github.com/ZipengWu365/EchoTime/blob/main/examples/data/real_btc_oil_vix_2024.csv",
            source_data_href=markets["source_url"],
            bullets=[
                "The asset is understandable even if the reader is not a time-series specialist.",
                "The report shows where similarity is stable versus regime-dependent.",
                "The demo explains a comparison without claiming to replace market modelling libraries.",
            ],
            visuals=[
                {
                    "label": "Series overlay",
                    "svg": series_overlay_svg(markets["btc_usd"], markets["vix"], left_label="BTC", right_label="VIX"),
                    "caption": "The normalized overlay makes the shared structural windows visible despite the scale mismatch.",
                },
                {
                    "label": "Similarity radar",
                    "svg": similarity_radar_svg(market_report),
                    "caption": "The verdict stays interpretable because the radar shows whether the analogy is shape-, trend-, or shock-driven.",
                },
                {
                    "label": "Rolling component mean",
                    "svg": rolling_similarity_svg(market_roll),
                    "caption": "The rolling panel shows when the BTC-VIX analogy actually strengthens instead of pretending the relationship is constant.",
                },
            ],
            source_href="https://github.com/ZipengWu365/EchoTime/blob/main/examples/gallery/plot_btc_gold_under_shocks.py",
        ),
        "blog/heatwave_vs_grid_load.html": _blog_page(
            title="Southwest heatwave city temperatures",
            deck="An operations-friendly report story about drift, rhythm, and cross-city similarity under extreme weather.",
            report_href="reports/energy_load_heatwave_report.html",
            social_href="social/energy_load_card.svg",
            support_note="This story uses a frozen local CSV snapshot built from Open-Meteo archive data so the same panel can be reused in docs and reports.",
            data_href="https://github.com/ZipengWu365/EchoTime/blob/main/examples/data/real_heatwave_city_temps_2024.csv",
            source_data_href=heatwave["source_url"],
            bullets=[
                "This demo travels well because the narrative is operational, not purely methodological.",
                "The report makes panel structure legible before transfer or forecasting decisions begin.",
                "It is a good example of how EchoTime can turn a small wide-table handoff into an artifact someone else can act on.",
            ],
            visuals=[
                {
                    "label": "City temperatures",
                    "svg": series_overlay_svg(heatwave["phoenix_temp_max"], heatwave["las_vegas_temp_max"], left_label="Phoenix", right_label="Las Vegas"),
                    "caption": "The two city temperature curves still share rhythm, but the heatwave response is clearly not identical.",
                },
                {
                    "label": "Dataset radar",
                    "svg": profile_radar_svg(heat_profile),
                    "caption": "The profile radar adds context around drift, complexity, and coupling before any model handoff begins.",
                },
                {
                    "label": "Top axes",
                    "svg": axis_bar_svg(heat_profile),
                    "caption": "The axis view turns the dataset profile into something an operations or reliability team can scan quickly.",
                },
            ],
            source_href="https://github.com/ZipengWu365/EchoTime/blob/main/examples/gallery/plot_heatwave_grid_load.py",
        ),
        **project_docs_pages(version=version),
    }


def write_pages_bundle(path: str | Path, *, version: str = PACKAGE_VERSION) -> Path:
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in project_pages_bundle(version=version).items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


__all__ = [
    "project_demo_manifest",
    "project_pages_bundle",
    "write_pages_bundle",
]
