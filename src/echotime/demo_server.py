"""Local live demo server for EchoTime.

This module provides a tiny standard-library-only web app so users can try the
product surface with pasted arrays or starter cases. It is intentionally local:
there is no cloud backend, no upload service, and no external dependency.
"""

from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from dataclasses import dataclass
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

import numpy as np

from .agent_tools import ts_compare, ts_profile
from .copydeck import HEADLINE, LIVE_DEMO_HEADING, PACKAGE_NAME, PACKAGE_VERSION
from .datasets import list_starter_datasets, starter_dataset
from .product import explain_dataset, explain_similarity
from .profile import profile_dataset
from .similarity import compare_series
from .visuals import profile_html_report, similarity_html_report


PROFILE_STARTERS = {
    "weekly_website_traffic",
    "irregular_patient_vitals",
    "wearable_recovery_cohort",
    "energy_load_heatwave",
}
COMPARE_STARTERS = {
    "sine_vs_noise",
    "github_breakout_analogs",
    "btc_gold_oil_shocks",
}


@dataclass(slots=True)
class DemoResponse:
    ok: bool
    payload: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps({"ok": self.ok, **self.payload}, indent=2)


def parse_numeric_text(text: str) -> np.ndarray:
    """Parse comma/space/newline separated numeric text into a 1D array."""
    cleaned = (
        text.replace(",", " ")
        .replace(";", " ")
        .replace("\t", " ")
        .replace("|", " ")
    )
    arr = np.fromstring(cleaned, sep=" ")
    if text.strip() and arr.size == 0:
        raise ValueError("Could not parse any numeric values from the provided text.")
    return arr.astype(float, copy=False)


def _starter_profile_payload(name: str) -> DemoResponse:
    case = starter_dataset(name)
    domain = str(case.get("domain", "generic"))
    values = case["values"]
    kwargs: dict[str, Any] = {"domain": domain}
    if "timestamps" in case:
        kwargs["timestamps"] = case["timestamps"]
    if "channels" in case:
        kwargs["channel_names"] = case["channels"]
    profile = profile_dataset(values, **kwargs)
    return DemoResponse(
        True,
        {
            "title": case["name"],
            "mode": "profile",
            "summary_markdown": profile.to_summary_card_markdown(),
            "plain_english": explain_dataset(values, domain=domain),
            "tool_json": ts_profile(values, domain=domain),
            "html_report": profile_html_report(profile, title=case["name"].replace("_", " ").title()),
        },
    )


def _starter_compare_payload(name: str) -> DemoResponse:
    case = starter_dataset(name)
    if name == "sine_vs_noise":
        left = case["left"]
        right = case["right"]
        left_name = case.get("left_name", "left")
        right_name = case.get("right_name", "right")
    elif name == "github_breakout_analogs":
        left = case["target"]
        right = case["durable_breakout"]
        left_name = "candidate"
        right_name = "durable breakout"
    elif name == "btc_gold_oil_shocks":
        left = case["btc"]
        right = case["gold"]
        left_name = "BTC"
        right_name = "Gold"
    else:
        raise KeyError(name)
    report = compare_series(left, right, left_name=left_name, right_name=right_name)
    return DemoResponse(
        True,
        {
            "title": case["name"],
            "mode": "compare",
            "summary_markdown": report.to_summary_card_markdown(),
            "plain_english": explain_similarity(left, right, left_name=left_name, right_name=right_name),
            "tool_json": ts_compare(left, right),
            "html_report": similarity_html_report(report, title=case["name"].replace("_", " ").title(), left_series=left, right_series=right),
        },
    )


def starter_demo_payload(name: str) -> DemoResponse:
    if name in PROFILE_STARTERS:
        return _starter_profile_payload(name)
    if name in COMPARE_STARTERS:
        return _starter_compare_payload(name)
    raise KeyError(f"Unknown starter case for demo server: {name}")


def profile_from_text(values_text: str, *, timestamps_text: str | None = None, domain: str = "generic", audience: str = "general") -> DemoResponse:
    values = parse_numeric_text(values_text)
    timestamps = parse_numeric_text(timestamps_text) if timestamps_text else None
    profile = profile_dataset(values, domain=domain, timestamps=timestamps)
    return DemoResponse(
        True,
        {
            "mode": "profile",
            "headline": explain_dataset(values, domain=domain, audience=audience),
            "summary_markdown": profile.to_summary_card_markdown(audience=audience),
            "tool_json": ts_profile(values, timestamps_ref=timestamps, domain=domain, audience=audience),
            "html_report": profile_html_report(profile, title="Interactive profile", audience=audience),
        },
    )


def compare_from_text(left_text: str, right_text: str, *, left_timestamps_text: str | None = None, right_timestamps_text: str | None = None, audience: str = "general") -> DemoResponse:
    left = parse_numeric_text(left_text)
    right = parse_numeric_text(right_text)
    left_ts = parse_numeric_text(left_timestamps_text) if left_timestamps_text else None
    right_ts = parse_numeric_text(right_timestamps_text) if right_timestamps_text else None
    report = compare_series(left, right, left_timestamps=left_ts, right_timestamps=right_ts, left_name="left", right_name="right")
    return DemoResponse(
        True,
        {
            "mode": "compare",
            "headline": explain_similarity(left, right, left_timestamps=left_ts, right_timestamps=right_ts),
            "summary_markdown": report.to_summary_card_markdown(),
            "tool_json": ts_compare(left, right, left_timestamps_ref=left_ts, right_timestamps_ref=right_ts),
            "html_report": similarity_html_report(report, title="Interactive comparison", left_series=left, right_series=right),
            "audience": audience,
        },
    )


def demo_server_html(*, version: str = PACKAGE_VERSION) -> str:
    options = "\n".join(
        f"<option value='{escape(item['name'])}'>{escape(item['title'])}</option>"
        for item in list_starter_datasets()
        if item["name"] in PROFILE_STARTERS | COMPARE_STARTERS
    )
    return f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>{PACKAGE_NAME} — {LIVE_DEMO_HEADING.lower()}</title>
<style>
:root {{ --bg:#f4f8fc; --ink:#102a43; --muted:#486581; --line:#d9e2ec; --panel:#ffffff; --brand:#0b6cff; --accent:#dd6b20; --shadow:0 1px 2px rgba(16,42,67,.05),0 12px 24px rgba(16,42,67,.08); --max:1200px; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; background:var(--bg); color:var(--ink); }}
.container {{ width:min(var(--max), calc(100vw - 28px)); margin:0 auto; padding:22px 0 36px; }}
.hero {{ display:grid; grid-template-columns:1.05fr .95fr; gap:18px; align-items:start; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:18px 20px; box-shadow:var(--shadow); }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:18px; }}
textarea, select, button, input {{ width:100%; font:inherit; }}
textarea {{ min-height:120px; padding:12px; border:1px solid var(--line); border-radius:12px; background:#fff; }}
select, input {{ padding:10px 12px; border:1px solid var(--line); border-radius:12px; background:#fff; }}
button {{ border:none; padding:12px 14px; border-radius:12px; background:var(--brand); color:#fff; font-weight:700; cursor:pointer; }}
button.alt {{ background:var(--accent); }}
pre {{ background:#f7fafc; border:1px solid var(--line); border-radius:12px; padding:14px; overflow:auto; white-space:pre-wrap; word-break:break-word; }}
iframe {{ width:100%; min-height:460px; border:1px solid var(--line); border-radius:14px; background:#fff; }}
.pill {{ display:inline-block; padding:4px 10px; border-radius:999px; background:#eef5ff; color:var(--brand); font-size:.88rem; font-weight:700; margin-right:8px; }}
.muted {{ color:var(--muted); }}
h1 {{ margin:0; font-size:clamp(2rem,4vw,3.3rem); line-height:1.02; letter-spacing:-.04em; }}
h2 {{ margin:0 0 8px; font-size:1.2rem; }}
.sub {{ color:var(--muted); margin-top:10px; }}
@media (max-width: 980px) {{ .hero,.grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<div class='container'>
  <section class='hero'>
    <div class='card'>
      <span class='pill'>Local live demo</span><span class='pill'>Version {escape(version)}</span>
      <h1>{escape(HEADLINE)}</h1>
      <p class='sub'>This server runs locally on your machine. Paste one curve for a plain-English structural report, or paste two curves for a similarity verdict. No cloud upload required.</p>
      <p class='sub'><strong>Why this exists:</strong> the static Pages playground is great for showcasing starter cases, but this local server gives you a real interactive product surface you can use with your own arrays right away.</p>
    </div>
    <div class='card'>
      <h2>Starter cases</h2>
      <p class='muted'>Load a prebuilt case into the viewer to see the product surface before trying your own data.</p>
      <select id='starter-select'>{options}</select>
      <div style='height:10px'></div>
      <button id='load-starter'>Load starter case</button>
      <div style='height:14px'></div>
      <pre id='starter-status'>Choose a starter case and click load.</pre>
    </div>
  </section>

  <section class='grid'>
    <div class='card'>
      <h2>Profile a dataset</h2>
      <p class='muted'>Paste a comma-, space-, or newline-separated numeric sequence.</p>
      <label>Values</label>
      <textarea id='profile-values'>1, 2, 3, 4, 5, 6, 7, 8</textarea>
      <label>Timestamps (optional)</label>
      <textarea id='profile-timestamps' placeholder='0, 1, 2, 3, 4, 5, 6, 7'></textarea>
      <label>Domain</label>
      <input id='profile-domain' value='generic'/>
      <div style='height:10px'></div>
      <button id='run-profile'>Generate report</button>
    </div>
    <div class='card'>
      <h2>Compare two curves</h2>
      <p class='muted'>Paste two sequences to get a plain-English similarity verdict.</p>
      <label>Left</label>
      <textarea id='compare-left'>1, 2, 3, 4, 5, 6</textarea>
      <label>Right</label>
      <textarea id='compare-right'>1.2, 2.0, 3.1, 4.1, 5.0, 6.2</textarea>
      <div style='height:10px'></div>
      <button class='alt' id='run-compare'>Compare curves</button>
    </div>
  </section>

  <section class='grid'>
    <div class='card'>
      <h2>Summary</h2>
      <pre id='summary-box'>Run a profile or comparison to see the summary card here.</pre>
      <h2 style='margin-top:18px'>Stable JSON</h2>
      <pre id='json-box'>The agent-ready JSON envelope will appear here.</pre>
    </div>
    <div class='card'>
      <h2>HTML report preview</h2>
      <iframe id='report-frame'></iframe>
    </div>
  </section>
</div>
<script>
async function postJSON(url, payload) {{
  const res = await fetch(url, {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(payload)}});
  if (!res.ok) throw new Error('Request failed: ' + res.status);
  return await res.json();
}}
function renderPayload(payload) {{
  document.getElementById('summary-box').textContent = payload.summary_markdown || payload.headline || 'No summary available.';
  document.getElementById('json-box').textContent = JSON.stringify(payload.tool_json || payload, null, 2);
  document.getElementById('report-frame').srcdoc = payload.html_report || '<p>No HTML report.</p>';
}}

document.getElementById('run-profile').addEventListener('click', async () => {{
  const payload = await postJSON('/api/profile', {{
    values: document.getElementById('profile-values').value,
    timestamps: document.getElementById('profile-timestamps').value,
    domain: document.getElementById('profile-domain').value || 'generic'
  }});
  renderPayload(payload);
}});

document.getElementById('run-compare').addEventListener('click', async () => {{
  const payload = await postJSON('/api/compare', {{
    left: document.getElementById('compare-left').value,
    right: document.getElementById('compare-right').value
  }});
  renderPayload(payload);
}});

document.getElementById('load-starter').addEventListener('click', async () => {{
  const name = document.getElementById('starter-select').value;
  const payload = await fetch('/api/starter?name=' + encodeURIComponent(name)).then(r => r.json());
  document.getElementById('starter-status').textContent = 'Loaded: ' + name;
  renderPayload(payload);
}});
</script>
</body>
</html>"""


class DemoRequestHandler(BaseHTTPRequestHandler):
    server_version = "echotime-demo/0.17.0"

    def _send(self, status: int, payload: str, content_type: str = "application/json; charset=utf-8") -> None:
        encoded = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send(200, demo_server_html(), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/starter":
            params = parse_qs(parsed.query)
            name = params.get("name", [""])[0]
            try:
                payload = starter_demo_payload(name)
                self._send(200, payload.to_json())
            except Exception as exc:
                self._send(400, json.dumps({"ok": False, "error": str(exc)}))
            return
        self._send(404, json.dumps({"ok": False, "error": "not_found"}))

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._read_json()
            if self.path == "/api/profile":
                payload = profile_from_text(
                    body.get("values", ""),
                    timestamps_text=body.get("timestamps") or None,
                    domain=body.get("domain", "generic") or "generic",
                )
                self._send(200, payload.to_json())
                return
            if self.path == "/api/compare":
                payload = compare_from_text(
                    body.get("left", ""),
                    body.get("right", ""),
                    left_timestamps_text=body.get("left_timestamps") or None,
                    right_timestamps_text=body.get("right_timestamps") or None,
                )
                self._send(200, payload.to_json())
                return
            self._send(404, json.dumps({"ok": False, "error": "not_found"}))
        except Exception as exc:  # pragma: no cover - network/error path
            self._send(400, json.dumps({"ok": False, "error": str(exc)}))

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def run_demo_server(*, host: str = "127.0.0.1", port: int = 8765, open_browser: bool = False) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), DemoRequestHandler)
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(f"http://{host}:{port}/")).start()
    print(f"EchoTime demo server listening on http://{host}:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual interrupt
        pass
    finally:
        server.server_close()
    return server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local EchoTime live demo server."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open-browser", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_demo_server(host=args.host, port=args.port, open_browser=args.open_browser)
    return 0


__all__ = [
    "DemoResponse",
    "parse_numeric_text",
    "starter_demo_payload",
    "profile_from_text",
    "compare_from_text",
    "demo_server_html",
    "run_demo_server",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
