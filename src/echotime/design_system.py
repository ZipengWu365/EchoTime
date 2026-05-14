"""Shared brand tokens and page shells for EchoTime.

This module keeps the static homepage, playground, launchpad, and HTML reports
visually aligned around one bright, research-lab-style design language.
"""

from __future__ import annotations

from html import escape

FONT_LINKS = """
<link rel='preconnect' href='https://fonts.googleapis.com'>
<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>
<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap' rel='stylesheet'>
""".strip()

COLOR_TOKENS = {
    "sun_500": "#FFC83D",
    "sun_300": "#FFE27A",
    "sun_100": "#FFF4C2",
    "sun_700": "#C7950A",
    "blue_600": "#2F6BFF",
    "blue_700": "#2554CC",
    "text_900": "#1F2937",
    "text_600": "#6B7280",
    "border": "#E5E7EB",
    "card": "#FAFAFA",
    "page": "#FFFFFF",
}

BASE_CSS = f"""
:root {{
  --page-bg: {COLOR_TOKENS['page']};
  --surface: {COLOR_TOKENS['card']};
  --surface-strong: #FFFFFF;
  --surface-sun: {COLOR_TOKENS['sun_100']};
  --surface-sun-strong: #FFF9E4;
  --sun-500: {COLOR_TOKENS['sun_500']};
  --sun-300: {COLOR_TOKENS['sun_300']};
  --sun-100: {COLOR_TOKENS['sun_100']};
  --sun-700: {COLOR_TOKENS['sun_700']};
  --blue-600: {COLOR_TOKENS['blue_600']};
  --blue-700: {COLOR_TOKENS['blue_700']};
  --text-900: {COLOR_TOKENS['text_900']};
  --text-600: {COLOR_TOKENS['text_600']};
  --border: {COLOR_TOKENS['border']};
  --shadow-sm: 0 10px 30px rgba(31, 41, 55, 0.06);
  --shadow-md: 0 18px 50px rgba(31, 41, 55, 0.08);
  --radius-lg: 28px;
  --radius-md: 20px;
  --radius-sm: 14px;
  --max-width: 980px;
}}
* {{
  box-sizing: border-box;
}}
html {{
  scroll-behavior: smooth;
}}
body {{
  margin: 0;
  background:
    radial-gradient(circle at top right, rgba(255, 226, 122, 0.16), transparent 24%),
    linear-gradient(180deg, #fffef9 0%, var(--page-bg) 12%, var(--page-bg) 100%);
  color: var(--text-900);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  line-height: 1.6;
  overflow-x: hidden;
}}
a {{
  color: var(--blue-600);
  text-decoration: none;
}}
a:hover {{
  color: var(--blue-700);
}}
code, pre {{
  font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}}
select, input, textarea {{
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-strong);
  color: var(--text-900);
  font: inherit;
}}
.shell {{
  width: min(var(--max-width), calc(100vw - 20px));
  margin: 0 auto;
}}
svg, img {{
  max-width: 100%;
  height: auto;
}}
.topbar {{
  position: sticky;
  top: 0;
  z-index: 20;
  border-bottom: 1px solid rgba(229, 231, 235, 0.94);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px) saturate(180%);
}}
.topbar-inner {{
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}}
.brand {{
  display: flex;
  align-items: center;
  gap: 14px;
}}
.brand-mark {{
  width: 18px;
  height: 18px;
  border-radius: 6px;
  background: linear-gradient(135deg, var(--sun-500), var(--sun-300));
  box-shadow: inset 0 0 0 1px rgba(31, 41, 55, 0.06);
}}
.brand-copy strong {{
  display: block;
  font-size: 1.12rem;
  letter-spacing: -0.02em;
}}
.brand-copy span {{
  color: var(--text-600);
  font-size: 0.95rem;
}}
.nav {{
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 0.95rem;
}}
.nav a {{
  color: var(--text-600);
  font-weight: 500;
}}
.nav a:hover {{
  color: var(--text-900);
}}
.section {{
  padding: 26px 0 18px;
}}
.section-head {{
  display: grid;
  gap: 8px;
  margin-bottom: 18px;
}}
.eyebrow {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 200, 61, 0.38);
  background: var(--surface-sun);
  color: var(--sun-700);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}
.hero {{
  padding: 42px 0 18px;
}}
.hero-grid, .grid-2, .grid-3 {{
  display: grid;
  gap: 20px;
}}
.hero-grid {{
  grid-template-columns: 1.1fr 0.9fr;
  align-items: start;
}}
.grid-2 {{
  grid-template-columns: 1fr 1fr;
}}
.grid-3 {{
  grid-template-columns: repeat(3, minmax(0, 1fr));
}}
.card {{
  background: var(--surface-strong);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 22px 24px;
  box-shadow: var(--shadow-sm);
  min-width: 0;
  overflow: hidden;
}}
.card.sun {{
  background: linear-gradient(180deg, #fffdfa 0%, var(--surface-sun-strong) 100%);
}}
.card.soft {{
  background: var(--surface);
}}
.feature-card {{
  display: grid;
  gap: 10px;
}}
.feature-card p,
.card p {{
  margin: 0;
}}
.badge-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}}
.trust-strip {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}}
.logo-chip {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.92);
  color: var(--text-600);
  font-size: 0.86rem;
  font-weight: 700;
}}
.logo-dot {{
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--sun-500), var(--blue-600));
}}
.pill {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 11px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-600);
  font-size: 0.86rem;
  font-weight: 700;
}}
.pill.sun {{
  border-color: rgba(255, 200, 61, 0.42);
  background: var(--surface-sun);
  color: var(--sun-700);
}}
.pill.blue {{
  border-color: rgba(47, 107, 255, 0.18);
  background: rgba(47, 107, 255, 0.08);
  color: var(--blue-700);
}}
.button-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}}
.button {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 46px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface-strong);
  color: var(--text-900);
  font-weight: 700;
  box-shadow: var(--shadow-sm);
}}
.button:hover {{
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}}
.button.primary {{
  border-color: rgba(255, 200, 61, 0.48);
  background: linear-gradient(180deg, #ffd65f 0%, var(--sun-500) 100%);
  color: var(--text-900);
}}
.button.secondary {{
  border-color: rgba(47, 107, 255, 0.18);
  background: rgba(47, 107, 255, 0.08);
  color: var(--blue-700);
}}
.button.ghost {{
  background: transparent;
  box-shadow: none;
}}
.button.text {{
  padding: 0;
  min-height: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
  color: var(--blue-700);
}}
h1, h2, h3 {{
  margin: 0;
  letter-spacing: -0.03em;
}}
h1 {{
  font-size: clamp(2.6rem, 5vw, 4.5rem);
  line-height: 0.98;
}}
h2 {{
  font-size: clamp(1.45rem, 2.4vw, 2.1rem);
}}
h3 {{
  font-size: 1.08rem;
}}
.subhead, .lead, .muted {{
  color: var(--text-600);
}}
.subhead {{
  max-width: 46rem;
  font-size: 1.12rem;
}}
.lead {{
  margin: 0;
  max-width: 68rem;
}}
.hero-stat {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}}
.hero-stage {{
  display: grid;
  gap: 18px;
}}
.stat {{
  border: 1px solid rgba(255, 200, 61, 0.28);
  border-radius: var(--radius-sm);
  background: rgba(255, 244, 194, 0.55);
  padding: 12px 14px;
}}
.stat strong {{
  display: block;
  font-size: 1.2rem;
}}
.panel-list {{
  margin: 0;
  padding-left: 1.1rem;
}}
.workflow {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}}
.step {{
  position: relative;
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface-strong);
}}
.step-number {{
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--sun-500);
  color: var(--text-900);
  font-weight: 800;
}}
.code-block, pre {{
  margin: 0;
  padding: 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: #fffef8;
  color: var(--text-900);
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}}
.surface-frame {{
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface-strong);
  box-shadow: var(--shadow-sm);
  min-width: 0;
  overflow: hidden;
}}
.surface-frame.pad {{
  padding: 16px;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--surface-strong);
  box-shadow: var(--shadow-sm);
  display: block;
  overflow-x: auto;
}}
th, td {{
  padding: 12px 14px;
  text-align: left;
  vertical-align: top;
  border-bottom: 1px solid var(--border);
}}
th {{
  background: #fffdf6;
  color: var(--text-600);
  font-size: 0.92rem;
}}
tr:last-child td {{
  border-bottom: none;
}}
iframe.demo {{
  width: 100%;
  min-height: 460px;
  border: 0;
  border-radius: var(--radius-md);
  background: var(--surface-strong);
}}
img.brand-card {{
  width: 100%;
  max-width: 460px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface-strong);
  box-shadow: var(--shadow-sm);
}}
.footer {{
  padding: 28px 0 54px;
  color: var(--text-600);
}}
.footer-grid {{
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 18px;
  align-items: start;
}}
.diagram {{
  display: grid;
  gap: 14px;
}}
.diagram-flow {{
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}}
.diagram-arrow {{
  color: var(--blue-700);
  font-weight: 800;
}}
.diagram-band {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}}
.diagram-card {{
  padding: 18px;
  border: 1px dashed rgba(47, 107, 255, 0.22);
  border-radius: var(--radius-sm);
  background: linear-gradient(180deg, rgba(255, 244, 194, 0.38) 0%, #ffffff 100%);
}}
.note-box {{
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface);
}}
.note-box.info {{
  border-color: rgba(47, 107, 255, 0.18);
  background: rgba(47, 107, 255, 0.05);
}}
.note-box.warn {{
  border-color: rgba(255, 200, 61, 0.45);
  background: rgba(255, 244, 194, 0.66);
}}
.author-meta {{
  display: grid;
  gap: 6px;
  margin-top: 14px;
}}
.callout {{
  padding: 18px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(255, 200, 61, 0.42);
  background: linear-gradient(180deg, #fff9e4 0%, #ffffff 100%);
  box-shadow: var(--shadow-sm);
}}
@media (max-width: 980px) {{
  .topbar-inner {{
    padding: 12px 0;
    align-items: flex-start;
  }}
  .hero-grid, .grid-2, .grid-3, .workflow, .diagram-band, .hero-stat, .footer-grid {{
    grid-template-columns: 1fr;
  }}
}}
"""


def page_head(title: str, *, extra_css: str = "") -> str:
    return (
        "<head>"
        "<meta charset='utf-8'/>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'/>"
        f"{FONT_LINKS}"
        f"<title>{escape(title)}</title>"
        f"<style>{BASE_CSS}{extra_css}</style>"
        "</head>"
    )


def report_shell_css(accent: str) -> str:
    return f"""
    :root {{
      --accent: {accent};
    }}
    body {{
      background:
        radial-gradient(circle at top right, rgba(255, 226, 122, 0.14), transparent 22%),
        linear-gradient(180deg, #fffef9 0%, #ffffff 14%, #ffffff 100%);
    }}
    .report-header {{
      border-bottom: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.94);
      backdrop-filter: blur(10px) saturate(180%);
    }}
    .report-header-inner {{
      max-width: var(--max-width);
      margin: 0 auto;
      padding: 16px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .brand-mark {{
      background: linear-gradient(135deg, var(--sun-500), var(--sun-300));
    }}
    .report-grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 20px;
    }}
    .metric-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(47, 107, 255, 0.08);
      color: var(--blue-700);
      font-size: 0.84rem;
      font-weight: 700;
    }}
    @media (max-width: 920px) {{
      .report-grid {{
        grid-template-columns: 1fr;
      }}
      .report-header-inner {{
        padding: 14px 18px;
      }}
    }}
    """
