"""Static GitHub-Pages-friendly playground for EchoTime starter cases."""

from __future__ import annotations

import json
from html import escape

from .copydeck import DISPLAY_NAME, HEADLINE, PACKAGE_VERSION, PLAYGROUND_HEADING, TAGLINE
from .datasets import starter_dataset
from .design_system import page_head
from .product import explain_dataset, explain_similarity
from .profile import profile_dataset
from .similarity import compare_series
from .visuals import (
    profile_html_report,
    profile_radar_svg,
    profile_social_card_svg,
    similarity_html_report,
    similarity_social_card_svg,
)


def _build_cases() -> dict[str, dict[str, str]]:
    weekly = starter_dataset("weekly_website_traffic")
    weekly_profile = profile_dataset(
        weekly["values"],
        domain="traffic",
        timestamps=weekly["timestamps"],
        channel_names=weekly["channels"],
    )

    clinical = starter_dataset("irregular_patient_vitals")
    clinical_profile = profile_dataset(clinical["values"], domain="clinical")

    wearable = starter_dataset("wearable_recovery_cohort")
    wearable_profile = profile_dataset(
        wearable["values"],
        domain="wearable",
        timestamps=wearable["timestamps"],
        channel_names=wearable["channels"],
    )

    energy = starter_dataset("energy_load_heatwave")
    energy_profile = profile_dataset(
        energy["values"],
        domain="energy",
        timestamps=energy["timestamps"],
        channel_names=energy["channels"],
    )

    github_case = starter_dataset("github_breakout_analogs")
    github_similarity = compare_series(
        github_case["target"],
        github_case["durable_breakout"],
        left_name="OpenClaw-style candidate",
        right_name="durable breakout analog",
    )

    market_case = starter_dataset("btc_gold_oil_shocks")
    market_similarity = compare_series(
        market_case["btc"],
        market_case["gold"],
        left_name="BTC",
        right_name="Gold",
    )

    return {
        "weekly_website_traffic": {
            "title": "Weekly website traffic",
            "kind": "profile",
            "why": "Product-style rhythm, trend, and launch bursts.",
            "summary": explain_dataset(weekly["values"], domain="traffic"),
            "html": profile_html_report(weekly_profile, audience="general", title="Weekly website traffic"),
            "visual": profile_radar_svg(weekly_profile, width=360, height=340),
            "social": profile_social_card_svg(weekly_profile, title="Website traffic report"),
            "command": "python -c \"from echotime import starter_dataset, profile_dataset; case=starter_dataset('weekly_website_traffic'); print(profile_dataset(case['values'], domain='traffic').to_summary_card_markdown())\"",
        },
        "irregular_patient_vitals": {
            "title": "Irregular patient vitals",
            "kind": "profile",
            "why": "Show why timestamps and channel asynchrony matter.",
            "summary": explain_dataset(clinical["values"], domain="clinical"),
            "html": profile_html_report(clinical_profile, audience="clinical", title="Irregular patient vitals"),
            "visual": profile_radar_svg(clinical_profile, width=360, height=340),
            "social": profile_social_card_svg(clinical_profile, title="Irregular patient vitals"),
            "command": "python -c \"from echotime import starter_dataset, profile_dataset; case=starter_dataset('irregular_patient_vitals'); print(profile_dataset(case['values'], domain='clinical').to_summary_card_markdown())\"",
        },
        "wearable_recovery_cohort": {
            "title": "Wearable recovery cohort",
            "kind": "profile",
            "why": "Longitudinal cohort demo for adherence and heterogeneity.",
            "summary": explain_dataset(wearable["values"], domain="wearable"),
            "html": profile_html_report(wearable_profile, audience="general", title="Wearable recovery cohort"),
            "visual": profile_radar_svg(wearable_profile, width=360, height=340),
            "social": profile_social_card_svg(wearable_profile, title="Wearable recovery report"),
            "command": "python -c \"from echotime import starter_dataset, profile_dataset; case=starter_dataset('wearable_recovery_cohort'); print(profile_dataset(case['values'], domain='wearable').to_summary_card_markdown())\"",
        },
        "energy_load_heatwave": {
            "title": "Heatwave vs grid load",
            "kind": "profile",
            "why": "Grid-shift story with drift and rhythm.",
            "summary": explain_dataset(energy["values"], domain="energy"),
            "html": profile_html_report(energy_profile, audience="operations", title="Heatwave vs grid load"),
            "visual": profile_radar_svg(energy_profile, width=360, height=340),
            "social": profile_social_card_svg(energy_profile, title="Heatwave vs grid load"),
            "command": "python -c \"from echotime import starter_dataset, profile_dataset; case=starter_dataset('energy_load_heatwave'); print(profile_dataset(case['values'], domain='energy').to_summary_card_markdown())\"",
        },
        "openclaw_breakout_analogs": {
            "title": "OpenClaw-style GitHub breakout analogs",
            "kind": "similarity",
            "why": "Ask whether a new repo looks durable or just briefly viral.",
            "summary": explain_similarity(
                github_case["target"],
                github_case["durable_breakout"],
                left_name="OpenClaw-style candidate",
                right_name="durable breakout analog",
            ),
            "html": similarity_html_report(
                github_similarity,
                left_series=github_case["target"],
                right_series=github_case["durable_breakout"],
                title="OpenClaw-style GitHub breakout analogs",
            ),
            "visual": f"<pre><code>{escape(github_similarity.to_summary_card_markdown())}</code></pre>",
            "social": similarity_social_card_svg(github_similarity, title="GitHub breakout analogs"),
            "command": "python -c \"from echotime import starter_dataset, explain_similarity; case=starter_dataset('github_breakout_analogs'); print(explain_similarity(case['target'], case['durable_breakout'], left_name='candidate', right_name='durable'))\"",
        },
        "btc_gold_oil_shocks": {
            "title": "BTC vs gold under shocks",
            "kind": "similarity",
            "why": "Macro-regime similarity story for a broad audience.",
            "summary": explain_similarity(market_case["btc"], market_case["gold"], left_name="BTC", right_name="Gold"),
            "html": similarity_html_report(
                market_similarity,
                left_series=market_case["btc"],
                right_series=market_case["gold"],
                title="BTC vs gold under shocks",
            ),
            "visual": f"<pre><code>{escape(market_similarity.to_summary_card_markdown())}</code></pre>",
            "social": similarity_social_card_svg(market_similarity, title="BTC vs Gold under shocks"),
            "command": "python -c \"from echotime import starter_dataset, explain_similarity; case=starter_dataset('btc_gold_oil_shocks'); print(explain_similarity(case['btc'], case['gold'], left_name='BTC', right_name='Gold'))\"",
        },
    }


def project_playground_html(*, version: str = PACKAGE_VERSION) -> str:
    cases = _build_cases()
    first_key = next(iter(cases))
    first = cases[first_key]
    case_options = "\n".join(
        f"<option value='{escape(key)}'>{escape(value['title'])}</option>" for key, value in cases.items()
    )
    cases_json = json.dumps(cases)
    extra_css = """
    .play-layout { display:grid; gap:20px; }
    .play-toolbar { display:flex; flex-wrap:wrap; gap:12px; }
    .play-grid { display:grid; grid-template-columns: 320px minmax(0, 1fr); gap:20px; align-items:start; }
    .sticky-column { display:grid; gap:20px; position: sticky; top: 20px; align-content:start; }
    .content-column { display:grid; gap:20px; }
    .grid-2 { display:grid; grid-template-columns: 1fr 1fr; gap:20px; align-items:start; }
    .case-summary { min-height: 200px; }
    .case-visual { min-height: 340px; display:grid; place-items:center; }
    @media (max-width: 980px) {
      .play-grid, .grid-2 { grid-template-columns: 1fr; }
      .sticky-column { position: static; }
    }
    """
    return f"""<!doctype html>
<html lang='en'>
{page_head(f"{DISPLAY_NAME} playground - {TAGLINE}", extra_css=extra_css)}
<body>
<header class='topbar'>
  <div class='shell topbar-inner'>
    <div class='brand' style='display: flex; align-items: center; gap: 14px;'>
      <img src='logo.png' alt='EchoTime logo' style='width: 140px; height: auto; object-fit: contain;'>
      <span style='color: var(--text-600); font-size: 0.95rem; font-weight: 500;'>Explainable time-series similarity for humans and agents.</span>
    </div>
    
    <nav class='nav'>
      <a href='index.html'>Homepage</a>
      <a href='start-here.html'>Start here</a>
      <a href='#report-frame'>Report</a>
    </nav>
  </div>
</header>
<main class='shell section play-layout'>
  <section class='hero'>
    <div style='margin-bottom: 16px;'><a href='index.html' class='pill ghost' style='text-decoration: none;'>&larr; Back to docs</a></div>
    <div class='hero-grid'>
      <div class='card sun feature-card'>
        <div class='eyebrow'>Variant C · Benchmark / dashboard</div>
        <h1>{escape(PLAYGROUND_HEADING)}</h1>
        <p class='subhead'>{escape(HEADLINE)} This page is optimized for technical scanning: switch cases, inspect the artifact, copy the command, and keep the white-background scientific brand consistent with the rest of the ecosystem.</p>
        <div class='play-toolbar'>
          <a class='button primary' href='#case-select'>Choose a case</a>
          <a class='button secondary' href='reports/github_breakout_similarity.html'>Open flagship report</a>
          <a class='button ghost' href='index.html'>Back to homepage</a>
        </div>
      </div>
      <div class='card feature-card'>
        <span class='pill blue'>How to use this page</span>
        <ul class='panel-list'>
          <li>Open it locally for a zero-install preview.</li>
          <li>Publish it via GitHub Pages for a live shareable demo URL.</li>
          <li>Pass <code>?case=btc_gold_oil_shocks</code> or another key to deep-link a scenario.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class='play-grid'>
    <div class='sticky-column'>
      <div class='card feature-card'>
        <span class='pill sun'>Starter case</span>
        <label for='case-select'><strong>Switch demo scenario</strong></label>
        <select id='case-select'>{case_options}</select>
        <p id='case-why' class='lead'>{escape(first['why'])}</p>
      </div>
      <div class='card case-visual'>
        <div id='case-visual'>{first['visual']}</div>
      </div>
      <div class='card feature-card'>
        <span class='pill blue'>Copyable command</span>
        <pre id='command'><code>{escape(first['command'])}</code></pre>
      </div>
    </div>

    <div class='content-column'>
      <div class='card feature-card case-summary'>
        <span class='pill blue'>Plain-language summary</span>
        <pre id='summary'><code>{escape(first['summary'])}</code></pre>
      </div>
      <div class='surface-frame'>
        <iframe id='report-frame' class='demo' srcdoc="{escape(first['html'])}" title='EchoTime report preview' style='width:100%; height: 600px; border:none; border-radius: 12px;'></iframe>
      </div>
      <div class='grid-2'>
        <div class='surface-frame pad'>
          <div id='social-card'>{first['social']}</div>
        </div>
        <div class='card feature-card'>
          <span class='pill sun'>Why this fits the brand</span>
          <p>Variant C stays denser than the homepage, but it still uses the same sunny tokens, muted borders, and premium white surfaces. The result feels consistent across docs, dashboards, and demos.</p>
        </div>
      </div>
    </div>
  </section>
</main>
<footer class='shell footer'>
  Playground for starter similarity cases. Fast to scan, easy to share, and consistent with the broader EchoTime ecosystem.
</footer>
<script>
const CASES = {cases_json};
const select = document.getElementById('case-select');
const whyEl = document.getElementById('case-why');
const visualEl = document.getElementById('case-visual');
const summaryEl = document.getElementById('summary');
const commandEl = document.getElementById('command');
const frame = document.getElementById('report-frame');
const social = document.getElementById('social-card');

function renderCase(key) {{
  const item = CASES[key];
  if (!item) return;
  whyEl.textContent = item.why;
  visualEl.innerHTML = item.visual;
  summaryEl.textContent = item.summary;
  commandEl.textContent = item.command;
  frame.srcdoc = item.html;
  social.innerHTML = item.social;
  const url = new URL(window.location.href);
  url.searchParams.set('case', key);
  window.history.replaceState({{}}, '', url.toString());
}}

select.addEventListener('change', (event) => renderCase(event.target.value));
const queryCase = new URL(window.location.href).searchParams.get('case');
if (queryCase && CASES[queryCase]) {{
  select.value = queryCase;
}}
renderCase(select.value);
</script>
</body>
</html>"""


__all__ = ["project_playground_html"]
