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
    "blue_600": "#3b82f6",
    "blue_700": "#2563eb",
    "text_900": "#FFFFFF",
    "text_600": "#A1A1AA",
    "border": "rgba(255, 255, 255, 0.1)",
    "card": "#0a0a0a",
    "page": "#000000",
}

BASE_CSS = f"""
:root {{
  --page-bg: {COLOR_TOKENS['page']};
  --surface: {COLOR_TOKENS['card']};
  --surface-strong: #111111;
  --surface-sun: rgba(255, 200, 61, 0.05);
  --surface-sun-strong: rgba(255, 200, 61, 0.1);
  --sun-500: {COLOR_TOKENS['sun_500']};
  --sun-300: {COLOR_TOKENS['sun_300']};
  --sun-100: {COLOR_TOKENS['sun_100']};
  --sun-700: {COLOR_TOKENS['sun_700']};
  --blue-600: {COLOR_TOKENS['blue_600']};
  --blue-700: {COLOR_TOKENS['blue_700']};
  --text-900: {COLOR_TOKENS['text_900']};
  --text-600: {COLOR_TOKENS['text_600']};
  --border: {COLOR_TOKENS['border']};
  --border-glow: rgba(255, 200, 61, 0.3);
  --shadow-sm: 0 4px 20px rgba(0, 0, 0, 0.5);
  --shadow-md: 0 8px 30px rgba(0, 0, 0, 0.6);
  --radius-lg: 28px;
  --radius-md: 16px;
  --radius-sm: 10px;
  --max-width: 1280px;
}}
* {{
  box-sizing: border-box;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}
html {{
  scroll-behavior: smooth;
}}
body {{
  margin: 0;
  background-color: var(--page-bg);
  background-image: radial-gradient(circle at 50% 0%, rgba(255, 200, 61, 0.08), transparent 50%),
                    radial-gradient(circle at 100% 100%, rgba(59, 130, 246, 0.05), transparent 50%);
  color: var(--text-900);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  line-height: 1.6;
  overflow-x: hidden;
}}
a {{
  color: var(--text-900);
  text-decoration: none;
  transition: color 0.2s ease;
}}
a:hover {{
  color: var(--sun-500);
}}
code, pre {{
  font-family: 'JetBrains Mono', monospace;
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
  width: min(var(--max-width), calc(100vw - 40px));
  margin: 0 auto;
}}
svg, img {{
  max-width: 100%;
  height: auto;
}}
.topbar {{
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid var(--border);
  background: rgba(0, 0, 0, 0.7);
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
  width: 38px;
  height: 38px;
  border-radius: 0px;
  background: transparent;
  box-shadow: none;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}}
.brand-mark img {{
  width: 100%;
  height: auto;
  object-fit: contain;
  filter: brightness(1.2);
}}
.brand-copy strong {{
  display: block;
  font-size: 1.12rem;
  letter-spacing: -0.02em;
}}
.brand-copy span {{
  display: none;
}}
@media (min-width: 768px) {{
  .brand-copy span {{
    display: block;
    color: var(--text-600);
    font-size: 0.85rem;
  }}
}}
.nav {{
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  font-size: 0.9rem;
}}
.nav a {{
  color: var(--text-600);
  font-weight: 500;
}}
.nav a:hover {{
  color: var(--text-900);
}}
.section {{
  padding: 80px 0 40px;
  position: relative;
}}
.section-head {{
  display: grid;
  gap: 12px;
  margin-bottom: 32px;
}}
.eyebrow {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 200, 61, 0.3);
  background: rgba(255, 200, 61, 0.1);
  color: var(--sun-500);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  box-shadow: 0 0 20px rgba(255, 200, 61, 0.1);
}}
.hero {{
  padding: 100px 0 60px;
  position: relative;
  overflow: hidden;
}}
.hero-canvas-container {{
  position: absolute;
  top: 0;
  right: -10%;
  width: 60%;
  height: 100%;
  z-index: -1;
  opacity: 0.8;
  pointer-events: none;
}}
@media (max-width: 1280px) {{
  .hero-canvas-container {{
    width: 100%;
    right: 0;
    opacity: 0.4;
  }}
}}
.hero-content {{
  max-width: 760px;
  position: relative;
  z-index: 2;
}}
.hero-content p {{
  margin-top: 24px;
}}
.hero-grid, .grid-2, .grid-3 {{
  display: grid;
  gap: 32px;
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
.showcase-split {{
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 40px;
  align-items: center;
}}
@media (max-width: 1280px) {{
  .showcase-split {{
    grid-template-columns: 1fr;
  }}
}}
.card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 32px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}}
.card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(circle at top left, rgba(255, 200, 61, 0.05), transparent 60%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}}
.card:hover {{
  border-color: rgba(255, 200, 61, 0.3);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(255, 200, 61, 0.05);
  transform: translateY(-2px);
}}
.card:hover::before {{
  opacity: 1;
}}
.card.sun {{
  background: var(--surface);
}}
.card.soft {{
  background: var(--surface);
}}
.feature-card {{
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
}}
.feature-card p,
.card p {{
  margin: 0;
  color: var(--text-600);
}}
.badge-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}}
.trust-strip, .trust-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}}
.logo-chip, .trust-chip {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-600);
  font-size: 0.85rem;
  font-weight: 500;
}}
.logo-dot, .trust-dot {{
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--sun-500);
  box-shadow: 0 0 8px var(--sun-500);
}}
.pill {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface-strong);
  color: var(--text-600);
  font-size: 0.82rem;
  font-weight: 600;
  transition: all 0.2s;
}}
.pill:hover {{
  border-color: rgba(255, 255, 255, 0.3);
  color: var(--text-900);
}}
.pill.sun {{
  border-color: rgba(255, 200, 61, 0.3);
  background: rgba(255, 200, 61, 0.05);
  color: var(--sun-500);
}}
.pill.blue {{
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(59, 130, 246, 0.05);
  color: var(--blue-600);
}}
.button-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 24px;
}}
.button {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 48px;
  padding: 0 24px;
  border-radius: 999px;
  font-size: 0.95rem;
  font-weight: 600;
  transition: all 0.2s ease;
  cursor: pointer;
  border: 1px solid transparent;
}}
.button.primary {{
  background: var(--text-900);
  color: var(--page-bg);
}}
.button.primary:hover {{
  background: var(--sun-500);
  box-shadow: 0 0 20px rgba(255, 200, 61, 0.4);
  transform: translateY(-2px);
}}
.button.secondary {{
  background: var(--surface-strong);
  color: var(--text-900);
  border-color: var(--border);
}}
.button.secondary:hover {{
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.05);
}}
.button.ghost {{
  background: transparent;
  color: var(--text-600);
}}
.button.ghost:hover {{
  color: var(--text-900);
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
  letter-spacing: -0.04em;
}}
h1 {{
  font-size: clamp(2rem, 4.5vw, 3.8rem);
  line-height: 1.1;
  font-weight: 900;
}}
.scanline-text {{
  background-image: 
    repeating-linear-gradient(transparent, transparent 2px, rgba(0,0,0,0.8) 2px, rgba(0,0,0,0.8) 4px),
    linear-gradient(180deg, #FFFFFF 0%, #a1a1aa 100%);
  background-size: 100% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: inline-block;
  padding-bottom: 0.1em;
}}
h2 {{
  font-size: clamp(1.8rem, 3vw, 2.8rem);
  font-weight: 700;
}}
h3 {{
  font-size: 1.2rem;
  font-weight: 600;
}}
.subhead, .lead, .muted {{
  color: var(--text-600);
}}
.subhead {{
  max-width: 48rem;
  font-size: 1.2rem;
  font-weight: 400;
}}
.lead {{
  margin: 0;
  max-width: 60rem;
  font-size: 1.1rem;
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
  background: rgba(255, 244, 194, 0.05);
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
  color: var(--page-bg);
  font-weight: 800;
}}
.code-block, pre {{
  margin: 0;
  padding: 20px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: #0d0d0d;
  color: #e5e7eb;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.9rem;
  box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
  position: relative;
}}
pre::before {{
  content: '';
  display: block;
  width: 10px; height: 10px;
  border-radius: 50%;
  background: #ff5f56;
  box-shadow: 18px 0 0 #ffbd2e, 36px 0 0 #27c93f;
  margin-bottom: 16px;
}}
.surface-frame {{
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface-strong);
  overflow: hidden;
}}
.surface-frame.pad {{
  padding: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #0d0d0d;
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
  background: #111111;
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
  padding: 40px 0 60px;
  color: var(--text-600);
  border-top: 1px solid var(--border);
  margin-top: 60px;
  font-size: 0.9rem;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
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
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-sm);
  background: rgba(255, 200, 61, 0.05);
}}
.note-box {{
  padding: 16px 20px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  background: transparent;
  font-size: 0.95rem;
  width: 100%;
  color: var(--sun-500);
  font-weight: 500;
  font-style: italic;
}}
.note-box.info {{
  border-left: 3px solid var(--sun-500);
  background: transparent;
  color: var(--sun-500);
}}
.note-box.warn {{
  border-color: rgba(255, 200, 61, 0.45);
  background: rgba(255, 244, 194, 0.05);
}}
.author-meta {{
  display: grid;
  gap: 6px;
  margin-top: 14px;
}}
.callout {{
  padding: 40px;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(255, 200, 61, 0.2);
  background: radial-gradient(circle at center, rgba(255, 200, 61, 0.08) 0%, #0a0a0a 100%);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}}
.callout .section-head {{
  align-items: center;
  text-align: center;
}}
@media (max-width: 1280px) {{
  .topbar-inner {{
    padding: 16px 0;
    align-items: flex-start;
    flex-direction: column;
  }}
  .hero-grid, .grid-2, .grid-3, .workflow, .diagram-band, .hero-stat, .footer-grid {{
    grid-template-columns: 1fr;
  }}
}}
svg text {{ fill: #A1A1AA; }}
svg text[fill='#1F2937'] {{ fill: #FFFFFF; }}
svg rect[fill='white'], svg rect[fill='#ffffff'] {{ fill: transparent; }}
svg rect[stroke='#E5E7EB'] {{ stroke: rgba(255, 255, 255, 0.1); }}
svg line[stroke='#E5E7EB'], svg line[stroke='#F3F4F6'] {{ stroke: rgba(255, 255, 255, 0.1); }}
svg rect[fill='#F3F4F6'] {{ fill: rgba(255, 255, 255, 0.05); }}
svg polyline[stroke='#2F6BFF'] {{ stroke: var(--sun-500); filter: drop-shadow(0 0 5px rgba(255, 200, 61, 0.5)); }}
svg polyline[stroke='#C7950A'] {{ stroke: var(--text-600); }}
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
      --page-bg: #000000;
      --surface: #0a0a0a;
      --surface-strong: #111111;
      --surface-sun: rgba(255, 200, 61, 0.05);
      --surface-sun-strong: rgba(255, 200, 61, 0.1);
      --sun-500: #FFC83D;
      --sun-300: #FFE27A;
      --sun-100: #FFF4C2;
      --sun-700: #C7950A;
      --blue-600: #3b82f6;
      --blue-700: #2563eb;
      --text-900: #FFFFFF;
      --text-600: #A1A1AA;
      --border: rgba(255, 255, 255, 0.1);
      --shadow-sm: 0 4px 20px rgba(0, 0, 0, 0.5);
      --shadow-md: 0 8px 30px rgba(0, 0, 0, 0.6);
      --radius-lg: 28px;
      --radius-md: 16px;
      --radius-sm: 10px;
      --max-width: 1280px;
    }}
    body {{
      background:
        radial-gradient(circle at top right, rgba(255, 200, 61, 0.08), transparent 22%),
        linear-gradient(180deg, #0a0a0a 0%, #000000 14%, #000000 100%);
    }}
    .report-header {{
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(0, 0, 0, 0.92);
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
      background: rgba(59, 130, 246, 0.15);
      color: var(--blue-600);
      font-size: 0.84rem;
      font-weight: 700;
    }}
    .back-nav {{ margin-bottom: 20px; }}
    .back-nav a {{ display: inline-flex; align-items: center; gap: 6px; color: var(--sun-500); font-weight: 600; text-decoration: none; font-size: 0.95rem; }}
    .back-nav a:hover {{ text-decoration: underline; }}
    @media (max-width: 920px) {{
      .report-grid {{
        grid-template-columns: 1fr;
      }}
      .report-header-inner {{
        padding: 14px 18px;
      }}
    }}
    """
