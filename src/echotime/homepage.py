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
    slug_to_href = {
        "openclaw_breakout_analogs": "blog/github_breakout_analogs.html",
        "btc_gold_oil_shocks": "blog/btc_vs_gold_under_shocks.html",
        "energy_load_heatwave": "blog/heatwave_vs_grid_load.html",
    }
    return "".join(
        f"<a href='{slug_to_href.get(item['slug'], '#')}' style='text-decoration: none; color: inherit; display: flex; flex-direction: column; height: 100%;'>"
        "<div class='card feature-card' style='display: flex; flex-direction: column; flex-grow: 1; transition: transform 0.2s, box-shadow 0.2s; cursor: pointer;' onmouseover='this.style.transform=\"translateY(-2px)\"; this.style.boxShadow=\"var(--shadow-md)\"' onmouseout='this.style.transform=\"none\"; this.style.boxShadow=\"var(--shadow-sm)\"'>"
        f"<span class='pill blue'>{escape(item['title'])}</span>"
        f"<p style='flex-grow: 1;'>{escape(item['story'])}</p>"
        f"<div class='note-box info'>{escape(item['social_hook'])}</div>"
        "</div></a>"
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
    .intuition-panel { display:grid; grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr); gap: 0; align-items: stretch; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--surface); overflow: hidden; box-shadow: var(--shadow-sm); }
    .timeline-stage { position: relative; min-height: 420px; padding: 34px; background: radial-gradient(circle at 22% 22%, rgba(255, 200, 61, 0.1), transparent 30%), linear-gradient(180deg, #111111 0%, #070707 100%); overflow: hidden; }
    .timeline-stage::before { content: ""; position: absolute; inset: 34px; background-image: linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px); background-size: 46px 46px; mask-image: linear-gradient(180deg, rgba(0,0,0,0.95), rgba(0,0,0,0.2)); pointer-events: none; }
    .timeline-stage svg { position: relative; z-index: 1; width: 100%; height: 100%; min-height: 310px; display: block; }
    .series-fill { opacity: 0.16; }
    .series-line { fill: none; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 760; animation: traceLine 5.5s ease-in-out infinite; }
    .series-line.reference { stroke: var(--sun-500); filter: drop-shadow(0 0 10px rgba(255, 200, 61, 0.45)); }
    .series-line.candidate { stroke: var(--blue-600); stroke-dasharray: 720; animation-delay: 0.45s; filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.35)); }
    .window-band { animation: driftWindow 5.5s ease-in-out infinite; }
    .pulse-node { transform-origin: center; animation: pulseNode 2.8s ease-in-out infinite; }
    .pulse-node.delay-1 { animation-delay: 0.4s; }
    .pulse-node.delay-2 { animation-delay: 0.8s; }
    .metric-strip { position: absolute; left: 34px; right: 34px; bottom: 28px; z-index: 2; display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
    .metric-tile { border: 1px solid rgba(255,255,255,0.1); border-radius: var(--radius-sm); background: rgba(10,10,10,0.72); backdrop-filter: blur(10px); padding: 12px; min-width: 0; }
    .metric-tile strong { display:block; font-size: 0.94rem; color: var(--text-900); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .metric-tile span { display:block; margin-top: 2px; color: var(--text-600); font-size: 0.78rem; line-height: 1.35; }
    .timeline-label { position: absolute; top: 28px; left: 34px; z-index: 2; color: var(--text-600); font-size: 0.82rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
    .intuition-points { display:flex; flex-direction: column; justify-content: center; gap: 22px; padding: 40px 36px; border-left: 1px solid var(--border); background: #0a0a0a; }
    .intuition-point { display:grid; grid-template-columns: 16px minmax(0, 1fr); gap: 14px; align-items: start; }
    .point-dot { width: 10px; height: 10px; margin-top: 8px; border-radius: 999px; background: var(--sun-500); box-shadow: 0 0 12px rgba(255, 200, 61, 0.55); }
    .intuition-point:nth-child(2) .point-dot { background: var(--blue-600); box-shadow: 0 0 12px rgba(59, 130, 246, 0.45); }
    .intuition-point:nth-child(3) .point-dot { background: var(--text-900); box-shadow: 0 0 12px rgba(255, 255, 255, 0.3); }
    .intuition-point h3 { margin: 0 0 6px; font-size: 1.08rem; letter-spacing: 0; }
    .intuition-point p { margin: 0; color: var(--text-600); font-size: 0.94rem; line-height: 1.55; }
    @media (max-width: 980px) {
      .home-grid, .home-grid-2, .home-grid-3, .intuition-panel { grid-template-columns: 1fr; }
      .intuition-points { border-left: 0; border-top: 1px solid var(--border); }
      .timeline-stage { min-height: 360px; padding: 24px; }
      .metric-strip { left: 24px; right: 24px; bottom: 22px; grid-template-columns: 1fr; }
    }
    @keyframes traceLine { 0% { stroke-dashoffset: 760; opacity: 0.35; } 35%, 72% { stroke-dashoffset: 0; opacity: 1; } 100% { stroke-dashoffset: -760; opacity: 0.4; } }
    @keyframes driftWindow { 0%, 100% { transform: translateX(0); opacity: 0.22; } 50% { transform: translateX(92px); opacity: 0.42; } }
    @keyframes pulseNode { 0%, 100% { r: 5; opacity: 0.75; } 50% { r: 8; opacity: 1; } }
    @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 200, 61, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 15px rgba(255, 200, 61, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 200, 61, 0); } }
    @keyframes scanline { 0% { top: -10px; } 100% { top: 100%; } }
    """

    return f"""<!doctype html>
<html lang='en'>
{page_head(f"{DISPLAY_NAME} - {TAGLINE}", extra_css=extra_css)}
<body>
<header class='topbar'>
  <div class='shell topbar-inner'>
    <div class='brand' style='display: flex; align-items: center; gap: 14px;'>
      <img src='logo.png' alt='EchoTime logo' style='width: 140px; height: auto; object-fit: contain;'>
      <span style='color: var(--text-600); font-size: 0.95rem; font-weight: 500;'>Explainable time-series similarity for humans and agents.</span>
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
    <!-- Dynamic Canvas Animation -->
    <div class="hero-canvas-container">
      <canvas id="hero-canvas"></canvas>
    </div>
    
    <div class="hero-content">
      <div class='eyebrow'>EchoTime 1.0</div>
      <h1 class="scanline-text">{escape(HEADLINE)}</h1>
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
    </div>
  </section>

  

    <section class='section'>
    <div class='section-head'>
      <div class='eyebrow'>Why EchoTime?</div>
      <h2>Designed for human intuition and agent reasoning</h2>
      <p class='lead section-copy'>Stop trusting black-box scalars. EchoTime breaks down structural similarity into explainable components.</p>
    </div>
    <div class='intuition-panel'>
      <div class='timeline-stage' aria-label='Animated EchoTime time-series comparison'>
        <div class='timeline-label'>rolling similarity timeline</div>
        <svg viewBox='0 0 680 360' role='img' aria-label='Two time-series curves being compared over rolling windows'>
          <defs>
            <linearGradient id='reference-fill' x1='0' y1='0' x2='0' y2='1'>
              <stop offset='0%' stop-color='var(--sun-500)' stop-opacity='0.55'/>
              <stop offset='100%' stop-color='var(--sun-500)' stop-opacity='0'/>
            </linearGradient>
            <linearGradient id='candidate-fill' x1='0' y1='0' x2='0' y2='1'>
              <stop offset='0%' stop-color='var(--blue-600)' stop-opacity='0.45'/>
              <stop offset='100%' stop-color='var(--blue-600)' stop-opacity='0'/>
            </linearGradient>
          </defs>
          <rect class='window-band' x='88' y='60' width='118' height='210' rx='18' fill='var(--sun-500)' opacity='0.26'/>
          <path class='series-fill' fill='url(#reference-fill)' d='M40 260 C90 238 110 158 165 170 C224 183 242 88 306 102 C360 114 374 210 430 194 C486 178 504 94 560 110 C610 124 632 184 650 154 L650 300 L40 300 Z'/>
          <path class='series-fill' fill='url(#candidate-fill)' d='M40 274 C100 250 116 194 165 202 C228 212 252 130 306 138 C370 146 382 232 430 220 C500 204 510 128 560 142 C608 154 632 214 650 178 L650 300 L40 300 Z'/>
          <path class='series-line reference' d='M40 260 C90 238 110 158 165 170 C224 183 242 88 306 102 C360 114 374 210 430 194 C486 178 504 94 560 110 C610 124 632 184 650 154'/>
          <path class='series-line candidate' d='M40 274 C100 250 116 194 165 202 C228 212 252 130 306 138 C370 146 382 232 430 220 C500 204 510 128 560 142 C608 154 632 214 650 178'/>
          <line x1='40' y1='300' x2='650' y2='300' stroke='rgba(255,255,255,0.16)'/>
          <line x1='40' y1='66' x2='40' y2='300' stroke='rgba(255,255,255,0.16)'/>
          <circle class='pulse-node' cx='306' cy='102' r='5' fill='var(--sun-500)'/>
          <circle class='pulse-node delay-1' cx='430' cy='220' r='5' fill='var(--blue-600)'/>
          <circle class='pulse-node delay-2' cx='560' cy='110' r='5' fill='var(--sun-500)'/>
          <text x='48' y='332'>raw signal</text>
          <text x='296' y='332'>profile</text>
          <text x='552' y='332'>agent context</text>
        </svg>
        <div class='metric-strip'>
          <div class='metric-tile'><strong>Profile</strong><span>dataset structure first</span></div>
          <div class='metric-tile'><strong>Compare</strong><span>shape, trend, rhythm</span></div>
          <div class='metric-tile'><strong>Explain</strong><span>JSON plus narrative</span></div>
        </div>
      </div>
      <div class='intuition-points'>
        <div class='intuition-point'>
          <span class='point-dot'></span>
          <div>
            <h3>Explainable by default</h3>
            <p>Similarity is shown as components a person can inspect, not just one opaque score.</p>
          </div>
        </div>
        <div class='intuition-point'>
          <span class='point-dot'></span>
          <div>
            <h3>Domain agnostic</h3>
            <p>The same workflow fits finance, healthcare, traffic, climate, logs, and research cohorts.</p>
          </div>
        </div>
        <div class='intuition-point'>
          <span class='point-dot'></span>
          <div>
            <h3>Agent ready</h3>
            <p>Compact outputs let tool-calling agents carry the result without dragging around oversized reports.</p>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class='section'>
    <div class='section-head'>
      <div class='eyebrow'>Quickstart</div>
      <h2>The first interaction is obvious</h2>
    </div>
    <div class='home-grid-2' style='grid-template-columns: 1fr 1fr; gap: 20px;'>
      <div class='card feature-card'>
        <span class='pill sun'>Installation & Copy-paste</span>
        <pre style='font-size: 0.8rem; padding: 16px; margin: 0;'><code>{escape(QUICKSTART_INSTALL)}
{escape(QUICKSTART_ONE_LINER)}</code></pre>
      </div>
      <div class='card feature-card'>
        <span class='pill blue'>Expected output</span>
        <pre style='font-size: 0.8rem; padding: 16px; margin: 0;'><code>{quick_expected}</code></pre>
      </div>
    </div>
  </section>

  <section class='section'>
    <div class='section-head'>
      <div class='eyebrow'>Showcase</div>
      <h2>One strong example, then deeper material in docs</h2>
      <p class='lead section-copy'>The homepage only needs enough proof to earn a click into the docs. It should not carry the whole manual.</p>
    </div>
    <div class='home-grid-2' style='grid-template-columns: 1fr 1fr; gap: 20px;'>
      <div class='card feature-card' style='padding: 0; overflow: hidden; display: flex; flex-direction: column;'>
        <div style='background: var(--surface-strong); border-bottom: 1px solid var(--border); padding: 20px; display: flex; justify-content: center; align-items: center;'>
          {overlay}
        </div>
        <div style='padding: 24px; flex-grow: 1;'>
          <span class='pill blue'>Explainable Similarity</span>
          <h3 style='margin-top: 12px;'>Plain-English similarity preview</h3>
          <pre style='font-size: 0.8rem; padding: 16px; margin: 16px 0 0 0;'><code>{summary_preview}</code></pre>
        </div>
      </div>
      <div class='card feature-card' style='padding: 0; overflow: hidden; display: flex; flex-direction: column;'>
        <div style='background: var(--surface-strong); border-bottom: 1px solid var(--border); padding: 20px; display: flex; justify-content: center; align-items: center;'>
          {comp}
        </div>
        <div style='padding: 24px; flex-grow: 1;'>
          <span class='pill sun'>Diagnostics</span>
          <h3 style='margin-top: 12px;'>Similarity components</h3>
          <p style='margin-top: 8px; color: var(--text-600); font-size: 0.95rem; line-height: 1.6;'>Understand exactly which structural elements match and which don't, breaking down the similarity score. Trace the origin of the similarity index to specific time-series characteristics.</p>
        </div>
      </div>
    <div class='card feature-card' style='padding: 0; overflow: hidden; display: flex; flex-direction: column; margin-top: 20px;'>
      <div style='background: var(--surface-strong); border-bottom: 1px solid var(--border); padding: 20px; display: flex; justify-content: center; align-items: center; overflow-x: auto;'>
        {roll}
      </div>
      <div style='padding: 24px; flex-grow: 1;'>
        <span class='pill blue'>Stability over time</span>
        <h3 style='margin-top: 12px;'>Rolling component mean</h3>
        <p style='margin-top: 8px; color: var(--text-600); font-size: 0.95rem; line-height: 1.6;'>Analyze how the similarity between the two series evolves over time. The breakdown shows whether the structural relationship is durable or just a short-lived artifact.</p>
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
  <div>
    EchoTime homepage for product overview. Tutorials and reference content live in the <a href='guide/index.html'>documentation section</a>.
  </div>
  <div>
    Maintainers: <a href="mailto:zxw365@student.bham.ac.uk">Zipeng Wu</a>, The University of Birmingham &nbsp;|&nbsp; <a href="mailto:jc15u24@soton.ac.uk">Jiajun Chen</a>, The University of Southampton
  </div>
</footer>

<script>
  // 3D Cube + Particles Animation
  const canvas = document.getElementById('hero-canvas');
  const ctx = canvas.getContext('2d');
  let w, h;
  
  function resize() {{
    const rect = canvas.parentElement.getBoundingClientRect();
    w = canvas.width = rect.width;
    h = canvas.height = rect.height;
  }}
  
  window.addEventListener('resize', resize);
  resize();

  class Particle {{
    constructor(x, y, vx, vy, life) {{
      this.x = x;
      this.y = y;
      this.vx = vx;
      this.vy = vy;
      this.life = life;
      this.maxLife = life;
      this.size = Math.random() * 2 + 1;
    }}
    
    update() {{
      this.x += this.vx;
      this.y += this.vy;
      this.life--;
      this.vy += 0.02; // slight gravity
      this.vx *= 0.98; // air resistance
    }}
    
    draw(ctx) {{
      const alpha = (this.life / this.maxLife) * 0.7;
      ctx.fillStyle = `rgba(255, 200, 61, ${{alpha}})`;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fill();
    }}
  }}

  let particles = [];

  const vertices = [
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
  ];
  
  const edges = [
    [0, 1], [1, 2], [2, 3], [3, 0], // back
    [4, 5], [5, 6], [6, 7], [7, 4], // front
    [0, 4], [1, 5], [2, 6], [3, 7]  // connecting
  ];

  let angleX = 0;
  let angleY = 0;

  function project(x, y, z) {{
    const scale = Math.min(w, h) * 0.35;
    const distance = 3;
    const zProjected = 1 / (distance - z);
    const px = x * zProjected * scale + w / 2;
    const py = y * zProjected * scale + h / 2;
    return [px, py];
  }}

  function rotateX(v, angle) {{
    const [x, y, z] = v;
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    return [x, y * cos - z * sin, y * sin + z * cos];
  }}

  function rotateY(v, angle) {{
    const [x, y, z] = v;
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    return [x * cos + z * sin, y, -x * sin + z * cos];
  }}
  
  function rotateZ(v, angle) {{
    const [x, y, z] = v;
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    return [x * cos - y * sin, x * sin + y * cos, z];
  }}

  function emitParticles() {{
    if (Math.random() < 0.3) {{
      const emission = Math.floor(Math.random() * 2) + 1;
      for (let i = 0; i < emission; i++) {{
        const x = w / 2 + (Math.random() - 0.5) * (Math.min(w, h) * 0.9);
        const y = h / 2 + (Math.random() - 0.5) * (Math.min(w, h) * 0.9);
        const vx = (Math.random() - 0.5) * 1.5;
        const vy = (Math.random() - 0.5) * 1.5 - 0.5;
        particles.push(new Particle(x, y, vx, vy, Math.random() * 60 + 40));
      }}
    }}
    
    particles = particles.filter(p => p.life > 0);
    particles.forEach(p => {{
      p.update();
      p.draw(ctx);
    }});
  }}

  function animate(time) {{
    ctx.clearRect(0, 0, w, h);
    
    angleX += 0.002;
    angleY += 0.003;
    const angleZ = Math.sin(time * 0.0005) * 0.2;
    
    ctx.strokeStyle = 'rgba(255, 200, 61, 0.7)';
    ctx.lineWidth = 1.5;
    ctx.shadowBlur = 15;
    ctx.shadowColor = 'rgba(255, 200, 61, 0.5)';
    ctx.lineJoin = 'round';
    
    const projected = vertices.map(v => {{
      let r = rotateX(v, angleX);
      r = rotateY(r, angleY);
      r = rotateZ(r, angleZ);
      return project(...r);
    }});
    
    ctx.beginPath();
    edges.forEach(edge => {{
      const [p1, p2] = edge;
      ctx.moveTo(projected[p1][0], projected[p1][1]);
      ctx.lineTo(projected[p2][0], projected[p2][1]);
    }});
    ctx.stroke();
    ctx.shadowBlur = 0;
    
    ctx.fillStyle = '#FFFFFF';
    projected.forEach(p => {{
      ctx.beginPath();
      ctx.arc(p[0], p[1], 2, 0, Math.PI * 2);
      ctx.fill();
    }});

    emitParticles();
    
    requestAnimationFrame(animate);
  }}
  
  requestAnimationFrame(animate);
</script>


</body>
</html>"""


__all__ = ["project_homepage_html"]
