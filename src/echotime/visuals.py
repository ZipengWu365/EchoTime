
"""Visual and HTML reporting helpers for EchoTime.

These helpers keep runtime dependencies light by emitting standalone SVG/HTML
artifacts. The goal is not publication-grade plotting; it is fast, shareable,
GitHub-friendly report generation that works in ordinary Python environments.
"""

from __future__ import annotations

import json
from html import escape
from math import cos, pi, sin
from typing import Any, Iterable, Mapping

import numpy as np

from .communication import summary_card_dict
from .design_system import COLOR_TOKENS, page_head, report_shell_css
from .schema import AXIS_DESCRIPTIONS

_AXIS_LABELS = {
    "sampling_irregularity": "Irregularity",
    "noise_contamination": "Noise",
    "predictability": "Predictability",
    "drift_nonstationarity": "Drift",
    "trendness": "Trend",
    "rhythmicity": "Rhythmicity",
    "complexity": "Complexity",
    "nonlinearity_chaoticity": "Nonlinearity",
    "eventness_burstiness": "Burstiness",
    "regime_switching": "Regimes",
    "coupling_networkedness": "Coupling",
    "heterogeneity": "Heterogeneity",
}

_SIMILARITY_LABELS = {
    "shape_similarity": "Shape",
    "dtw_similarity": "DTW",
    "trend_similarity": "Trend",
    "derivative_similarity": "Derivative",
    "spectral_similarity": "Spectral",
    "pearson_r": "Pearson r",
    "spearman_rho": "Spearman rho",
    "kendall_tau": "Kendall tau",
    "best_lag_pearson_r": "Best-lag r",
    "normalized_mutual_information": "Mutual info",
    "first_difference_r": "Diff r",
}

_SUN_FILL = "rgba(255, 200, 61, 0.24)"
_SUN_STROKE = COLOR_TOKENS["sun_700"]
_BLUE = COLOR_TOKENS["blue_600"]
_BLUE_DARK = COLOR_TOKENS["blue_700"]
_TEXT = COLOR_TOKENS["text_900"]
_MUTED = COLOR_TOKENS["text_600"]
_BORDER = COLOR_TOKENS["border"]


def _level(score: float) -> str:
    score = float(score)
    if score >= 0.75:
        return "very high"
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "moderate"
    if score >= 0.15:
        return "low"
    return "very low"


def _nice_label(name: str) -> str:
    return _AXIS_LABELS.get(name, name.replace("_", " ").title())


def _similarity_label(name: str) -> str:
    return _SIMILARITY_LABELS.get(name, name.replace("_", " ").title())


def _svg_wrap(body: str, *, width: int, height: int, title: str | None = None) -> str:
    title_node = f"<title>{escape(title)}</title>" if title else ""
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
        f"viewBox='0 0 {width} {height}' role='img' aria-label='{escape(title or 'EchoTime visual')}'>"
        f"{title_node}{body}</svg>"
    )


def _polygon_points(values: Iterable[float], *, cx: float, cy: float, radius: float) -> str:
    vals = list(values)
    n = max(1, len(vals))
    pts = []
    for i, value in enumerate(vals):
        angle = -pi / 2 + 2 * pi * i / n
        r = radius * float(np.clip(value, 0.0, 1.0))
        x = cx + r * cos(angle)
        y = cy + r * sin(angle)
        pts.append(f"{x:.1f},{y:.1f}")
    return " ".join(pts)


def profile_radar_svg(profile: Any, *, width: int = 420, height: int = 420) -> str:
    axes = list(profile.axes.keys())
    if not axes:
        return _svg_wrap("<text x='20' y='30'>No axes available.</text>", width=width, height=height, title="EchoTime axis radar")
    values = [float(profile.axes[a]) for a in axes]
    cx = width / 2
    cy = height / 2 + 8
    radius = min(width, height) * 0.31
    grid = []
    for level in (0.25, 0.5, 0.75, 1.0):
        pts = _polygon_points([level] * len(axes), cx=cx, cy=cy, radius=radius)
        grid.append(f"<polygon points='{pts}' fill='none' stroke='{_BORDER}' stroke-width='1'/>")
    spokes = []
    labels = []
    for i, axis in enumerate(axes):
        angle = -pi / 2 + 2 * pi * i / len(axes)
        x = cx + radius * cos(angle)
        y = cy + radius * sin(angle)
        spokes.append(f"<line x1='{cx:.1f}' y1='{cy:.1f}' x2='{x:.1f}' y2='{y:.1f}' stroke='{_BORDER}' stroke-width='1'/>")
        lx = cx + (radius + 20) * cos(angle)
        ly = cy + (radius + 20) * sin(angle)
        anchor = 'middle'
        if lx < cx - 18:
            anchor = 'end'
        elif lx > cx + 18:
            anchor = 'start'
        labels.append(
            f"<text x='{lx:.1f}' y='{ly:.1f}' font-size='11' fill='{_MUTED}' text-anchor='{anchor}' dominant-baseline='middle'>{escape(_nice_label(axis))}</text>"
        )
    profile_pts = _polygon_points(values, cx=cx, cy=cy, radius=radius)
    body = (
        "<rect width='100%' height='100%' fill='white'/>"
        f"<text x='18' y='24' font-size='16' font-weight='700' fill='{_TEXT}'>Axis radar</text>"
        f"<text x='18' y='42' font-size='11' fill='{_MUTED}'>Higher means the axis is more structurally dominant.</text>"
        + "".join(grid)
        + "".join(spokes)
        + f"<polygon points='{profile_pts}' fill='{_SUN_FILL}' stroke='{_BLUE}' stroke-width='2'/>"
        + "".join(labels)
    )
    return _svg_wrap(body, width=width, height=height, title="EchoTime axis radar")


def axis_bar_svg(profile: Any, *, width: int = 560, height: int = 300, top_n: int = 6) -> str:
    items = sorted(((k, float(v)) for k, v in profile.axes.items()), key=lambda kv: kv[1], reverse=True)[:top_n]
    if not items:
        return _svg_wrap("<text x='20' y='30'>No axes available.</text>", width=width, height=height, title="EchoTime top axes")
    left = 170
    right = width - 20
    top = 48
    step = max(30, (height - top - 20) / len(items))
    bar_w = right - left
    rows = []
    for idx, (axis, score) in enumerate(items):
        y = top + idx * step
        filled = bar_w * float(np.clip(score, 0.0, 1.0))
        rows.append(f"<text x='16' y='{y + 14:.1f}' font-size='12' fill='{_TEXT}'>{escape(_nice_label(axis))}</text>")
        rows.append(f"<rect x='{left}' y='{y:.1f}' width='{bar_w:.1f}' height='16' rx='8' fill='#F3F4F6'/>")
        rows.append(f"<rect x='{left}' y='{y:.1f}' width='{filled:.1f}' height='16' rx='8' fill='{_BLUE}'/>")
        rows.append(f"<text x='{right - 2:.1f}' y='{y + 13:.1f}' font-size='11' fill='{_MUTED}' text-anchor='end'>{score:.2f}</text>")
    body = (
        "<rect width='100%' height='100%' fill='white'/>"
        f"<text x='16' y='24' font-size='16' font-weight='700' fill='{_TEXT}'>Top structure axes</text>"
        f"<text x='16' y='40' font-size='11' fill='{_MUTED}'>The axes most likely to shape modelling and communication choices.</text>"
        + "".join(rows)
    )
    return _svg_wrap(body, width=width, height=height, title="EchoTime top axes")


def similarity_components_svg(report: Any, *, width: int = 560, height: int = 280) -> str:
    items = sorted(((k, float(v)) for k, v in report.component_scores.items()), key=lambda kv: kv[1], reverse=True)
    if not items:
        return _svg_wrap("<text x='20' y='30'>No components available.</text>", width=width, height=height, title="EchoTime similarity components")
    left = 160
    right = width - 20
    top = 48
    step = max(28, (height - top - 18) / len(items))
    bar_w = right - left
    rows = []
    for idx, (name, score) in enumerate(items):
        y = top + idx * step
        filled = bar_w * float(np.clip(score, 0.0, 1.0))
        rows.append(f"<text x='16' y='{y + 14:.1f}' font-size='12' fill='{_TEXT}'>{escape(_similarity_label(name))}</text>")
        rows.append(f"<rect x='{left}' y='{y:.1f}' width='{bar_w:.1f}' height='16' rx='8' fill='#F3F4F6'/>")
        rows.append(f"<rect x='{left}' y='{y:.1f}' width='{filled:.1f}' height='16' rx='8' fill='{COLOR_TOKENS['sun_500']}'/>")
        rows.append(f"<text x='{right - 2:.1f}' y='{y + 13:.1f}' font-size='11' fill='{_MUTED}' text-anchor='end'>{score:.2f}</text>")
    component_mean = float(getattr(report, "component_mean", np.nan))
    subtitle = (
        f"Component mean {component_mean:.2f} across {len(items)} time-series metrics."
        if np.isfinite(component_mean)
        else "Read the bars alongside Pearson and Spearman rather than as one verdict."
    )
    body = (
        "<rect width='100%' height='100%' fill='white'/>"
        f"<text x='16' y='24' font-size='16' font-weight='700' fill='{_TEXT}'>Similarity components</text>"
        f"<text x='16' y='40' font-size='11' fill='{_MUTED}'>{escape(subtitle)}</text>"
        + "".join(rows)
    )
    return _svg_wrap(body, width=width, height=height, title="EchoTime similarity components")


def similarity_radar_svg(report: Any, *, width: int = 560, height: int = 320) -> str:
    order = [
        "shape_similarity",
        "dtw_similarity",
        "trend_similarity",
        "derivative_similarity",
        "spectral_similarity",
    ]
    items = [(name, float(report.component_scores.get(name, np.nan))) for name in order]
    items = [(name, value) for name, value in items if np.isfinite(value)]
    if not items:
        return _svg_wrap("<text x='20' y='30'>No similarity metrics available.</text>", width=width, height=height, title="Similarity radar")
    values = [value for _, value in items]
    cx = width / 2
    cy = height / 2 + 12
    radius = min(width, height) * 0.29
    grid = []
    for level in (0.25, 0.5, 0.75, 1.0):
        pts = _polygon_points([level] * len(items), cx=cx, cy=cy, radius=radius)
        grid.append(f"<polygon points='{pts}' fill='none' stroke='{_BORDER}' stroke-width='1'/>")
    spokes = []
    labels = []
    for idx, (name, _) in enumerate(items):
        angle = -pi / 2 + 2 * pi * idx / len(items)
        x = cx + radius * cos(angle)
        y = cy + radius * sin(angle)
        spokes.append(f"<line x1='{cx:.1f}' y1='{cy:.1f}' x2='{x:.1f}' y2='{y:.1f}' stroke='{_BORDER}' stroke-width='1'/>")
        lx = cx + (radius + 20) * cos(angle)
        ly = cy + (radius + 20) * sin(angle)
        anchor = "middle"
        if lx < cx - 18:
            anchor = "end"
        elif lx > cx + 18:
            anchor = "start"
        labels.append(
            f"<text x='{lx:.1f}' y='{ly:.1f}' font-size='11' fill='{_MUTED}' text-anchor='{anchor}' dominant-baseline='middle'>{escape(_similarity_label(name))}</text>"
        )
    points = _polygon_points(values, cx=cx, cy=cy, radius=radius)
    body = (
        "<rect width='100%' height='100%' fill='white'/>"
        f"<text x='16' y='24' font-size='16' font-weight='700' fill='{_TEXT}'>Similarity radar</text>"
        f"<text x='16' y='40' font-size='11' fill='{_MUTED}'>Radar over the time-series metrics. Read it together with Pearson, Spearman, and mutual info.</text>"
        + "".join(grid)
        + "".join(spokes)
        + f"<polygon points='{points}' fill='{_SUN_FILL}' stroke='{_BLUE}' stroke-width='2'/>"
        + "".join(labels)
    )
    return _svg_wrap(body, width=width, height=height, title="Similarity radar")


def _reference_metric_items(report: Any) -> list[tuple[str, float]]:
    order = (
        "pearson_r",
        "spearman_rho",
        "normalized_mutual_information",
        "first_difference_r",
        "kendall_tau",
        "best_lag_pearson_r",
    )
    items = []
    metrics = getattr(report, "reference_metrics", {}) or {}
    for key in order:
        value = float(metrics.get(key, np.nan))
        if np.isfinite(value):
            items.append((key, value))
    return items


def series_overlay_svg(left: Any, right: Any | None = None, *, width: int = 720, height: int = 240, left_label: str = "left", right_label: str = "right") -> str:
    l = np.asarray(left, dtype=float).reshape(-1)
    r = None if right is None else np.asarray(right, dtype=float).reshape(-1)
    if l.size == 0:
        return _svg_wrap("<text x='20' y='30'>No series available.</text>", width=width, height=height, title="EchoTime series preview")
    if r is not None and r.size > 0:
        n = min(len(l), len(r))
        l = l[:n]
        r = r[:n]
    data = l if r is None else np.concatenate([l, r])
    finite = data[np.isfinite(data)]
    if finite.size == 0:
        finite = np.array([0.0, 1.0])
    ymin = float(np.min(finite))
    ymax = float(np.max(finite))
    if ymax - ymin < 1e-9:
        ymax = ymin + 1.0
    def _path(values: np.ndarray) -> str:
        xs = np.linspace(40, width - 20, len(values))
        ys = height - 28 - ((values - ymin) / (ymax - ymin)) * (height - 52)
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
        return pts
    body = ["<rect width='100%' height='100%' fill='white'/>", f"<text x='16' y='24' font-size='16' font-weight='700' fill='{_TEXT}'>Series preview</text>"]
    body.append(f"<line x1='40' y1='24' x2='40' y2='212' stroke='{_BORDER}'/><line x1='40' y1='212' x2='700' y2='212' stroke='{_BORDER}'/>")
    body.append(f"<polyline points='{_path(l)}' fill='none' stroke='{_BLUE}' stroke-width='2.5'/>")
    body.append(f"<text x='46' y='42' font-size='11' fill='{_BLUE}'>{escape(left_label)}</text>")
    if r is not None:
        body.append(f"<polyline points='{_path(r)}' fill='none' stroke='{_SUN_STROKE}' stroke-width='2.5' stroke-dasharray='5 4'/>")
        body.append(f"<text x='120' y='42' font-size='11' fill='{_SUN_STROKE}'>{escape(right_label)}</text>")
    return _svg_wrap("".join(body), width=width, height=height, title="EchoTime series preview")


def rolling_similarity_svg(windows: Iterable[Mapping[str, Any]], *, width: int = 720, height: int = 240) -> str:
    items = list(windows)
    scores = [float(item.get("component_mean", item.get("similarity_score", np.nan))) for item in items]
    scores = [s for s in scores if np.isfinite(s)]
    if not scores:
        return _svg_wrap("<text x='20' y='30'>No rolling windows available.</text>", width=width, height=height, title="Rolling component mean")
    arr = np.asarray(scores, dtype=float)
    xs = np.linspace(40, width - 20, len(arr))
    ys = height - 28 - arr * (height - 84)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    body = (
        "<rect width='100%' height='100%' fill='white'/>"
        f"<text x='16' y='24' font-size='16' font-weight='700' fill='{_TEXT}'>Rolling component mean</text>"
        f"<line x1='40' y1='24' x2='40' y2='212' stroke='{_BORDER}'/><line x1='40' y1='212' x2='700' y2='212' stroke='{_BORDER}'/>"
        "<line x1='40' y1='134' x2='700' y2='134' stroke='#F3F4F6' stroke-dasharray='4 4'/>"
        f"<polyline points='{pts}' fill='none' stroke='{_BLUE}' stroke-width='2.5'/>"
        f"<text x='40' y='42' font-size='13' fill='{_BLUE_DARK}'>mean={float(np.mean(arr)):.2f}, min={float(np.min(arr)):.2f}, max={float(np.max(arr)):.2f} across per-window metric means</text>"
    )
    return _svg_wrap(body, width=width, height=height, title="Rolling component mean")


def _brand_shell(*, title: str, body: str, accent: str = "#0b6cff") -> str:
    return f"""<!doctype html>
<html lang='en'>
{page_head(title, extra_css=report_shell_css(accent))}
<body>
<header class='report-header'><div class='report-header-inner'><div style='display:flex; align-items:center; gap: 14px;'><a href='../index.html' class='pill ghost' style='text-decoration:none;'>&larr; Back to docs</a><div class='brand' style='display:flex;align-items:center;gap:14px;'><img src='../logo.png' alt='EchoTime logo' style='width:140px;height:auto;object-fit:contain;'><span style='color:var(--text-600);font-size:0.95rem;font-weight:500;'>Explainable time-series similarity for humans and agents.</span></div></div><div class='pill sun'>Scientific report surface</div></div></header>
<div class='shell' style='padding:28px 0 40px'>{body}</div>
</body>
</html>"""


def profile_html_report(profile: Any, *, title: str | None = None, audience: str = "general") -> str:
    card = summary_card_dict(profile, audience=audience)
    reliability = card["dataset_facts"]["reliability"]
    radar = profile_radar_svg(profile)
    bars = axis_bar_svg(profile)
    top_rows = "".join(
        f"<tr><td>{escape(item['plain_label'])}</td><td>{item['score']:.2f}</td><td>{escape(item['level'])}</td><td>{escape(item['meaning'])}</td></tr>"
        for item in card["top_structure_axes"]
    )
    takeaways = "".join(f"<li>{escape(item)}</li>" for item in card["main_takeaways"])
    watchouts = "".join(f"<li>{escape(item)}</li>" for item in card["main_watchouts"])
    actions = "".join(f"<li>{escape(item)}</li>" for item in card["recommended_next_actions"])
    compact = escape(profile.to_agent_context_json(budget="lean"))
    archetypes = ", ".join(card["archetypes"][:4]) if card["archetypes"] else "No strong archetype label dominates yet."
    subtitle = title or f"EchoTime profile - {card['domain']}"
    body = f"""
  <section class='hero'>
    <div class='card'>
      <span class='pill sun'>EchoTime</span><span class='pill'>{escape(str(card['domain']))}</span><span class='pill blue'>{escape(str(card['observation_mode']))}</span>
      <h1>{escape(card['executive_summary'])}</h1>
      <p class='lead'>Generate plain-English structural context you can compare, share, and hand off.</p>
      <div class='facts'>
        <div class='fact'><span class='muted'>Reliability</span><strong>{reliability['score']:.2f}</strong><span class='muted'>{escape(reliability['level'])}</span></div>
        <div class='fact'><span class='muted'>Subjects / units</span><strong>{card['dataset_facts']['n_subjects']}</strong><span class='muted'>cohort size</span></div>
        <div class='fact'><span class='muted'>Median channels</span><strong>{card['dataset_facts']['n_channels_median']}</strong><span class='muted'>per unit</span></div>
        <div class='fact'><span class='muted'>Median length</span><strong>{card['dataset_facts']['length_median']}</strong><span class='muted'>samples</span></div>
      </div>
      <h2 style='margin-top:22px'>What this looks like structurally</h2>
      <p>{escape(archetypes)}</p>
      <h2 style='margin-top:22px'>Recommended next actions</h2>
      <ul>{actions}</ul>
      <div class='signature'>Generated by EchoTime for an audience of <strong>{escape(audience)}</strong>. Use this as a structural context and dataset-comparison artifact, not as a modelling guarantee.</div>
    </div>
    <div class='card'>{radar}</div>
  </section>
  <section class='grid'>
    <div class='card'>{bars}</div>
    <div class='card'>
      <h2>Top structure axes</h2>
      <table><thead><tr><th>Axis</th><th>Score</th><th>Level</th><th>What it means</th></tr></thead><tbody>{top_rows}</tbody></table>
    </div>
  </section>
  <section class='grid'>
    <div class='card'><h2>Main takeaways</h2><ul>{takeaways}</ul></div>
    <div class='card'><h2>Main watchouts</h2><ul>{watchouts}</ul></div>
  </section>
  <section class='grid'>
    <div class='card'><h2>Why the score is trustworthy</h2><p><strong>Overall reliability:</strong> {reliability['score']:.2f} ({escape(reliability['level'])})</p><p class='muted'>A higher reliability score means more proxy coverage and stronger data support for the reported structure.</p></div>
    <div class='card'><h2>Compact agent context</h2><pre>{compact}</pre></div>
  </section>
"""
    return _brand_shell(title=subtitle, body=body, accent=_BLUE)



def similarity_html_report(report: Any, *, title: str | None = None, left_series: Any | None = None, right_series: Any | None = None, rolling_windows: Iterable[Mapping[str, Any]] | None = None) -> str:
    bars = similarity_components_svg(report)
    radar = similarity_radar_svg(report)
    overlay = series_overlay_svg(left_series, right_series, left_label=report.left_name, right_label=report.right_name) if left_series is not None and right_series is not None else ""
    rolling = rolling_similarity_svg(rolling_windows) if rolling_windows else ""
    suggestions = "".join(f"<li>{escape(item)}</li>" for item in report.suggestions)
    notes = "".join(f"<li>{escape(item)}</li>" for item in report.notes)
    compact = escape(report.to_agent_context_json(budget="lean"))
    title_text = title or f"EchoTime similarity report - {report.left_name} vs {report.right_name}"
    overlay_card = f"<div class='card'>{overlay}</div>" if overlay else ""
    rolling_card = f"<div class='card'>{rolling}</div>" if rolling else ""
    metric_tiles = []
    metric_descriptions = {
        "pearson_r": "linear level match",
        "spearman_rho": "rank-order match",
        "normalized_mutual_information": "nonlinear dependence",
        "kendall_tau": "pairwise order match",
        "best_lag_pearson_r": "best shifted level match",
        "first_difference_r": "local change match",
    }
    for key, value in _reference_metric_items(report)[:4]:
        metric_tiles.append(
            f"<div class='stat'><span class='muted'>{escape(_similarity_label(key))}</span><strong>{value:.2f}</strong><span class='muted'>{escape(metric_descriptions.get(key, 'reference metric'))}</span></div>"
        )
    reference_rows = "".join(
        f"<tr><td>{escape(_similarity_label(key))}</td><td>{value:.2f}</td></tr>"
        for key, value in _reference_metric_items(report)
    )
    component_mean = float(getattr(report, "component_mean", np.nan))
    component_note = (
        f"Component mean {component_mean:.2f} across {len(report.component_scores)} time-series-specific metrics."
        if np.isfinite(component_mean)
        else "Read the component panel as a metric family rather than a single scalar."
    )
    body = f"""
  <section class='hero'>
    <div class='card'>
      <span class='pill sun'>similarity</span><span class='pill blue'>{escape(report.mode)}</span>
      <h1>{escape(report.interpretation)}</h1>
      <p class='lead'>Start with familiar coefficients, then inspect the time-series radar and component bars. This page does not treat the internal aggregate score as the main verdict.</p>
      <div class='hero-stat'>{"".join(metric_tiles)}</div>
      <p class='muted'>{escape(component_note)}</p>
      <h2 style='margin-top:18px'>Recommended next actions</h2>
      <ul>{suggestions}</ul>
      <div class='signature'>Use this as an interpretable comparison summary. If you need alignment paths or distance matrices, pair the result with a lower-level similarity library.</div>
    </div>
    <div class='card'>{radar}</div>
  </section>
  <section class='grid'>
    {overlay_card}
    <div class='card'>{bars}</div>
  </section>
  <section class='grid'>
    {rolling_card}
    <div class='card'><h2>Familiar statistics</h2><table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>{reference_rows}</tbody></table></div>
    <div class='card'><h2>Notes and guardrails</h2><ul>{notes or '<li>No major notes.</li>'}</ul></div>
    <div class='card'><h2>Compact agent context</h2><pre>{compact}</pre></div>
  </section>
"""
    return _brand_shell(title=title_text, body=body, accent=COLOR_TOKENS["sun_500"])


def _social_card_shell(*, title: str, subtitle: str, bullets: list[str], accent: str, width: int = 1200, height: int = 630) -> str:
    bullets_svg = "".join(
        f"<text x='70' y='{225 + 58*i}' font-size='30' fill='#17324d'>&#8226; {escape(item)}</text>" for i, item in enumerate(bullets[:4])
    )
    return _svg_wrap(
        f"<defs><linearGradient id='bg' x1='0' x2='1' y1='0' y2='1'><stop offset='0%' stop-color='#fffef9'/><stop offset='100%' stop-color='{COLOR_TOKENS['sun_100']}'/></linearGradient></defs>"
        f"<rect width='100%' height='100%' fill='url(#bg)'/>"
        f"<rect x='40' y='38' width='{width-80}' height='{height-76}' rx='32' fill='white' stroke='{_BORDER}'/>"
        f"<rect x='40' y='38' width='14' height='{height-76}' rx='7' fill='{accent}'/>"
        f"<text x='84' y='108' font-size='34' font-weight='700' fill='{_TEXT}'>EchoTime</text>"
        f"<text x='84' y='152' font-size='54' font-weight='800' fill='{_TEXT}'>{escape(title)}</text>"
        f"<text x='84' y='192' font-size='28' fill='{_MUTED}'>{escape(subtitle)}</text>"
        f"{bullets_svg}"
        f"<text x='84' y='{height-74}' font-size='24' fill='{_MUTED}'>explainable time-series similarity for humans and agents</text>",
        width=width,
        height=height,
        title=f"EchoTime social card - {title}",
    )


def profile_social_card_svg(profile: Any, *, title: str | None = None) -> str:
    card = summary_card_dict(profile, audience="general")
    bullets = [item["plain_label"] for item in card["top_structure_axes"][:3]]
    return _social_card_shell(
        title=title or "Plain-English structural report",
        subtitle=f"{card['domain']} | reliability {card['dataset_facts']['reliability']['score']:.2f}",
        bullets=[f"Top axis: {b}" for b in bullets] + ["Structural context for better matching"],
        accent=COLOR_TOKENS["sun_500"],
    )


def similarity_social_card_svg(report: Any, *, title: str | None = None) -> str:
    bullets = [f"{_similarity_label(key)} {value:.2f}" for key, value in _reference_metric_items(report)[:3]]
    if "dtw_similarity" in report.component_scores:
        bullets.append(f"DTW {float(report.component_scores['dtw_similarity']):.2f}")
    return _social_card_shell(
        title=title or "Similarity verdict",
        subtitle=f"{report.left_name} vs {report.right_name}",
        bullets=bullets,
        accent=_BLUE,
    )

