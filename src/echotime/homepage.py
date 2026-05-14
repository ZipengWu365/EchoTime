"""Static homepage generator for EchoTime v0.17.1.

The homepage is now intentionally shorter and more product-like. Tutorials,
API material, and ecosystem detail live in dedicated docs pages with a sidebar.
"""

from __future__ import annotations

from html import escape

from .copydeck import (
    AUTHOR_AFFILIATION,
    AUTHOR_EMAIL,
    AUTHOR_NAME,
    DISPLAY_NAME,
    FLAGSHIP_DEMOS,
    HEADLINE,
    HOMEPAGE_PILLS,
    PACKAGE_STAGE,
    PACKAGE_VERSION,
    PRODUCT_PROMISE,
    PROJECT_DOCUMENTATION_URL,
    PROJECT_REPOSITORY_URL,
    QUICKSTART_EXPECTED_LINES,
    QUICKSTART_INSTALL,
    QUICKSTART_ONE_LINER,
    TAGLINE,
)
from .datasets import starter_dataset
from .design_system import page_head
from .product import explain_similarity
from .profile import profile_dataset
from .similarity import compare_series, rolling_similarity
from .visuals import (
    profile_social_card_svg,
    rolling_similarity_svg,
    series_overlay_svg,
    similarity_components_svg,
    similarity_social_card_svg,
)


def _flagship_cards() -> str:
    return "".join(
        "<div class='card feature-card'>"
        f"<span class='pill blue'>{escape(item['title'])}</span>"
        f"<p>{escape(item['story'])}</p>"
        f"<div class='note-box info'>{escape(item['social_hook'])}</div>"
        "</div>"
        for item in FLAGSHIP_DEMOS
    )


def project_homepage_html(*, version: str = PACKAGE_VERSION) -> str:
    github_case = starter_dataset("github_breakout_analogs")
    github_report = compare_series(
        github_case["target"],
        github_case["durable_breakout"],
        left_name="OpenClaw-style candidate",
        right_name="durable breakout analog",
    )
    windows = rolling_similarity(github_case["target"], github_case["durable_breakout"], window=20, step=5)

    traffic = starter_dataset("weekly_website_traffic")
    traffic_profile = profile_dataset(
        traffic["values"],
        domain="traffic",
        timestamps=traffic["timestamps"],
        channel_names=traffic["channels"],
    )

    overlay = series_overlay_svg(
        github_case["target"],
        github_case["durable_breakout"],
        left_label="OpenClaw-style candidate",
        right_label="durable breakout analog",
        width=620,
        height=250,
    )
    comp = similarity_components_svg(github_report, width=620, height=250)
    roll = rolling_similarity_svg(windows, width=620, height=250)
    summary_preview = escape(
        explain_similarity(
            github_case["target"],
            github_case["durable_breakout"],
            left_name="OpenClaw-style candidate",
            right_name="durable breakout analog",
        )
    )
    social_left = similarity_social_card_svg(github_report, title="GitHub breakout analogs")
    social_right = profile_social_card_svg(traffic_profile, title="Website traffic structure")
    homepage_pills = "".join(f"<span class='pill'>{escape(item)}</span>" for item in HOMEPAGE_PILLS)
    quick_expected = escape("\n".join(QUICKSTART_EXPECTED_LINES))
    flagship_cards = _flagship_cards()

    extra_css = """
    .home-grid { display:grid; grid-template-columns: 1.05fr 0.95fr; gap: 22px; align-items:start; }
    .home-grid-2, .home-grid-3 { display:grid; gap: 20px; }
    .home-grid-2 { grid-template-columns: 1fr 1fr; }
    .home-grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .trust-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; }
    .trust-chip { display:inline-flex; align-items:center; gap:8px; padding: 7px 12px; border-radius: 999px; border:1px solid var(--border); background: var(--surface-strong); color: var(--text-600); font-size:0.86rem; font-weight:700; }
    .trust-dot { width:8px; height:8px; border-radius:999px; background: linear-gradient(135deg, var(--sun-500), var(--blue-600)); }
    .docs-tiles { display:grid; gap: 16px; }
    .docs-tile { display:grid; gap: 8px; padding: 18px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--surface-strong); }
    .showcase-grid { display:grid; gap:20px; }
    .section-copy { max-width: 54rem; }
    @media (max-width: 980px) {
      .home-grid, .home-grid-2, .home-grid-3 { grid-template-columns: 1fr; }
    }
    """

    return f"""<!doctype html>
<html lang='en'>
{page_head(f"{DISPLAY_NAME} - {TAGLINE}", extra_css=extra_css)}
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
      <a href='guide/index.html'>Docs</a>
      <a href='guide/getting-started.html'>Getting started</a>
      <a href='guide/tutorials.html'>Tutorials</a>
      <a href='guide/api.html'>API</a>
      <a href='playground.html'>Playground</a>
      <a href='{escape(PROJECT_REPOSITORY_URL)}'>GitHub</a>
    </nav>
  </div>
</header>
<main class='shell'>
  <section class='hero'>
    <div class='home-grid'>
      <div class='card sun feature-card'>
        <div class='eyebrow'>Homepage</div>
        <h1>{escape(HEADLINE)}</h1>
        <p class='subhead'>{escape(PRODUCT_PROMISE)} The homepage is intentionally short. Tutorials, API material, and ecosystem detail now live in dedicated docs pages with a left sidebar.</p>
        <div class='badge-row'>{homepage_pills}</div>
        <div class='button-row'>
          <a class='button primary' href='guide/getting-started.html'>Read the getting-started guide</a>
          <a class='button secondary' href='guide/tutorials.html'>Browse tutorials</a>
          <a class='button ghost' href='playground.html?case=openclaw_breakout_analogs'>Open playground</a>
        </div>
        <div class='trust-row'>
          <span class='trust-chip'><span class='trust-dot'></span>MIT License</span>
          <span class='trust-chip'><span class='trust-dot'></span>{escape(PACKAGE_STAGE)} release</span>
          <span class='trust-chip'><span class='trust-dot'></span>{escape(AUTHOR_AFFILIATION)}</span>
        </div>
      </div>
      <div class='card feature-card'>
        <span class='pill blue'>Maintainer</span>
        <p><strong>{escape(AUTHOR_NAME)}</strong></p>
        <p>{escape(AUTHOR_AFFILIATION)}</p>
        <a href='mailto:{escape(AUTHOR_EMAIL)}'>{escape(AUTHOR_EMAIL)}</a>
        <a href='{escape(PROJECT_DOCUMENTATION_URL)}'>{escape(PROJECT_DOCUMENTATION_URL)}</a>
        <img class='brand-card' src='social/echotime_title_card.svg' alt='EchoTime title card'/>
      </div>
    </div>
  </section>

  <section class='section'>
    <div class='section-head'>
      <div class='eyebrow'>Product overview</div>
      <h2>One homepage, separate documentation, and a clearer information hierarchy</h2>
      <p class='lead section-copy'>This layout is closer to scikit-learn than to a single long landing page. The front page explains the product quickly; the docs area handles tutorials, API reference, scenarios, and ecosystem positioning with a persistent sidebar.</p>
    </div>
    <div class='home-grid-3 docs-tiles'>
      <a class='docs-tile' href='guide/getting-started.html'><strong>Getting Started</strong><span class='muted'>Install, zero-install paths, and the first successful command.</span></a>
      <a class='docs-tile' href='guide/tutorials.html'><strong>Tutorials</strong><span class='muted'>Beginner examples, flagship demos, and starter datasets.</span></a>
      <a class='docs-tile' href='guide/api.html'><strong>API Reference</strong><span class='muted'>Compare, profile, reports, and agent wrappers grouped by role.</span></a>
      <a class='docs-tile' href='guide/methods.html'><strong>Methods Atlas</strong><span class='muted'>All extracted similarity methods, fit assessment, and formulas in one place.</span></a>
      <a class='docs-tile' href='guide/scenarios.html'><strong>Scenarios</strong><span class='muted'>Medicine, engineering, product, and research entry points.</span></a>
      <a class='docs-tile' href='guide/ecosystem.html'><strong>Ecosystem</strong><span class='muted'>How EchoTime complements sktime, tsfresh, DTAIDistance, and others.</span></a>
      <a class='docs-tile' href='guide/agents.html'><strong>Agent Tools</strong><span class='muted'>Compact schemas and compare-first tool routing.</span></a>
    </div>
  </section>

  <section class='section'>
    <div class='section-head'>
      <div class='eyebrow'>Quickstart</div>
      <h2>The first interaction should still be obvious</h2>
    </div>
    <div class='home-grid-2'>
      <div class='card feature-card'>
        <span class='pill sun'>Copy-paste</span>
        <pre><code>{escape(QUICKSTART_INSTALL)}
{escape(QUICKSTART_ONE_LINER)}</code></pre>
      </div>
      <div class='card feature-card'>
        <span class='pill blue'>Expected output</span>
        <pre><code>{quick_expected}</code></pre>
      </div>
    </div>
  </section>

  <section class='section'>
    <div class='section-head'>
      <div class='eyebrow'>Showcase</div>
      <h2>One strong example, then deeper material in docs</h2>
      <p class='lead section-copy'>The homepage only needs enough proof to earn a click into the docs. It should not carry the whole manual.</p>
    </div>
    <div class='showcase-grid'>
      <div class='home-grid-2'>
        <div class='surface-frame pad'>{overlay}</div>
        <div class='card feature-card'>
          <span class='pill blue'>Plain-English similarity preview</span>
          <pre><code>{summary_preview}</code></pre>
        </div>
      </div>
      <div class='home-grid-2'>
        <div class='surface-frame pad'>{comp}</div>
        <div class='surface-frame pad'>{roll}</div>
      </div>
      <div class='home-grid-2'>
        <div class='surface-frame pad'>{social_left}</div>
        <div class='surface-frame pad'>{social_right}</div>
      </div>
    </div>
  </section>

  <section class='section'>
    <div class='section-head'>
      <div class='eyebrow'>Flagship demos</div>
      <h2>Built to travel beyond the docs</h2>
    </div>
    <div class='home-grid-3'>
      {flagship_cards}
    </div>
  </section>

  <section class='section'>
    <div class='callout'>
      <div class='section-head'>
        <div class='eyebrow'>Next step</div>
        <h2>Use the docs like a docs site, not like a landing page appendix</h2>
        <p class='lead'>If you want tutorials, API detail, or ecosystem guidance, go to the left-sidebar docs area. That separation is what makes the site easier to scan and easier to trust.</p>
      </div>
      <div class='button-row'>
        <a class='button primary' href='guide/index.html'>Open documentation</a>
        <a class='button secondary' href='guide/api.html'>Open API reference</a>
      </div>
    </div>
  </section>
</main>
<footer class='shell footer'>
  EchoTime homepage for product overview. Tutorials and reference content live in the documentation section at <a href='guide/index.html'>guide/index.html</a>.
</footer>
</body>
</html>"""


__all__ = ["project_homepage_html"]
