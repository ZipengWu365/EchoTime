"""Unified compare-first launchpad page for EchoTime v0.17.1."""

from __future__ import annotations

from html import escape

from .copydeck import (
    DISPLAY_NAME,
    DOCTOR_HEADING,
    HEADLINE,
    LIVE_DEMO_HEADING,
    PACKAGE_VERSION,
    QUICKSTART_INSTALL,
    QUICKSTART_ONE_LINER,
    START_HERE_HEADING,
    TAGLINE,
    ZERO_INSTALL_OPTIONS,
)
from .design_system import page_head


def project_launchpad_html(*, version: str = PACKAGE_VERSION) -> str:
    zero_cards = "".join(
        "<div class='card feature-card'>"
        f"<span class='pill blue'>{escape(item['title'])}</span>"
        f"<p>{escape(item['why'])}</p>"
        "</div>"
        for item in ZERO_INSTALL_OPTIONS
    )
    extra_css = """
    .launch-grid { display:grid; gap:20px; }
    .command-grid { display:grid; grid-template-columns: 1fr 1fr; gap:20px; }
    @media (max-width: 980px) {
      .command-grid { grid-template-columns: 1fr; }
    }
    """
    return f"""<!doctype html>
<html lang='en'>
{page_head(f"{DISPLAY_NAME} - {START_HERE_HEADING}", extra_css=extra_css)}
<body>
<header class='topbar'>
  <div class='shell topbar-inner'>
    <div class='brand'>
      <span class='brand-mark'></span>
      <div class='brand-copy'>
        <strong>{escape(DISPLAY_NAME)}</strong>
        <span>{escape(TAGLINE)}</span>
      </div>
    </div>
    <nav class='nav'>
      <a href='index.html'>Homepage</a>
      <a href='playground.html'>Playground</a>
      <a href='reports/github_breakout_similarity.html'>Flagship report</a>
    </nav>
  </div>
</header>
<main class='shell section launch-grid'>
  <section class='hero'>
    <div class='hero-grid'>
      <div class='card sun feature-card'>
        <div class='eyebrow'>Variant B · Productized open source</div>
        <h1>{escape(START_HERE_HEADING)}</h1>
        <p class='subhead'>{escape(HEADLINE)} This page compresses the repo into a small set of first moves: static preview, local live demo, quickstart, environment doctor, and Pages export.</p>
        <div class='button-row'>
          <a class='button primary' href='playground.html'>Open static playground</a>
          <a class='button secondary' href='local_demo.html'>View local demo surface</a>
          <a class='button ghost' href='index.html'>Open homepage</a>
        </div>
      </div>
      <div class='card feature-card'>
        <span class='pill blue'>{escape(LIVE_DEMO_HEADING)}</span>
        <ul class='panel-list'>
          <li>Use the playground if you want zero-install proof first.</li>
          <li>Use the live demo if you want real computation on pasted arrays.</li>
          <li>Use the quickstart if you already have Python ready.</li>
          <li>Use the doctor and compatibility preset when your environment is crowded.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class='command-grid'>
    <div class='card feature-card'>
      <span class='pill sun'>One-line quickstart</span>
      <pre><code>{escape(QUICKSTART_INSTALL)}
{escape(QUICKSTART_ONE_LINER)}</code></pre>
    </div>
    <div class='card feature-card'>
      <span class='pill blue'>{escape(DOCTOR_HEADING)}</span>
      <pre><code>echotime --guide doctor
# or
python -m echotime.cli --guide doctor</code></pre>
      <p>Use this when you suspect encoding issues, mixed scientific-stack packages, or resolver noise.</p>
    </div>
  </section>

  <section class='grid-3'>
    {zero_cards}
  </section>

  <section class='command-grid'>
    <div class='card feature-card'>
      <span class='pill sun'>Local live demo</span>
      <pre><code>echotime-demo --open-browser
# or
python -m echotime.demo_server --open-browser</code></pre>
    </div>
    <div class='card feature-card'>
      <span class='pill blue'>Compatibility preset</span>
      <pre><code>echotime --write-constraints constraints/mixed-scientific-stack.txt `
  --constraint-profile mixed-scientific-stack
pip install -c constraints/mixed-scientific-stack.txt echotime</code></pre>
    </div>
  </section>

  <section class='command-grid'>
    <div class='card feature-card'>
      <span class='pill blue'>GitHub Pages export</span>
      <pre><code>echotime --export-pages docs
# then publish docs/ with GitHub Pages</code></pre>
    </div>
    <div class='callout'>
      <strong>Why this page exists</strong>
      <p>Open-source adoption improves when the first decision is easy. This launchpad reduces the repo to a small number of explicit next steps instead of making users decode the entire codebase before they can try it.</p>
    </div>
  </section>
</main>
<footer class='shell footer'>
  Productized open-source entry point for EchoTime. White-background-first, optimistic, and designed for fast technical comprehension.
</footer>
</body>
</html>"""


__all__ = ["project_launchpad_html"]
