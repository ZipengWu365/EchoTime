from __future__ import annotations

import sys
import textwrap
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties, findfont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from echotime.communication import summary_card_dict
from echotime.datasets import starter_dataset
from echotime.profile import profile_dataset
from echotime.similarity import compare_series, rolling_similarity

PAGE = "#FFFFFF"
PAGE_SOFT = "#FFFDF4"
CARD = "#FAFAFA"
BORDER = "#E5E7EB"
TEXT = "#1F2937"
MUTED = "#6B7280"
SUN = "#FFC83D"
SUN_SOFT = "#FFE27A"
SUN_DEEP = "#C7950A"
BLUE = "#2F6BFF"
BLUE_DEEP = "#2554CC"


def _font(size: int, *, mono: bool = False) -> ImageFont.FreeTypeFont:
    family = "DejaVu Sans Mono" if mono else "DejaVu Sans"
    path = findfont(FontProperties(family=family))
    return ImageFont.truetype(path, size=size)


def _card_canvas(width: int, height: int, *, accent: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), PAGE_SOFT)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 28, width - 28, height - 28), radius=28, fill=PAGE, outline=BORDER, width=2)
    draw.rounded_rectangle((28, 28, 48, height - 28), radius=10, fill=accent)
    return image, draw


def _draw_wrapped(draw: ImageDraw.ImageDraw, text: str, *, x: int, y: int, width: int, font: ImageFont.FreeTypeFont, fill: str) -> int:
    lines: list[str] = []
    for raw in text.splitlines():
        if not raw:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(raw, width=max(18, width // max(7, font.size // 2)), replace_whitespace=False))
    line_height = int(font.size * 1.55)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def _render_text_card(*, title: str, subtitle: str, body: str, accent: str, mono: bool = False, size: tuple[int, int] = (1280, 720)) -> Image.Image:
    image, draw = _card_canvas(*size, accent=accent)
    title_font = _font(34)
    subtitle_font = _font(20)
    body_font = _font(22, mono=mono)
    draw.text((72, 72), title, font=title_font, fill=TEXT)
    draw.text((72, 126), subtitle, font=subtitle_font, fill=MUTED)
    _draw_wrapped(draw, body, x=72, y=190, width=size[0] - 144, font=body_font, fill=TEXT)
    return image


def _save_figure(path: Path, build_fn) -> None:
    fig = plt.figure(figsize=(10.5, 6.0), dpi=140)
    try:
        build_fn(fig)
        fig.tight_layout()
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=140, facecolor="white")
    finally:
        plt.close(fig)


def _save_profile_radar(path: Path) -> None:
    weekly = starter_dataset("weekly_website_traffic")
    profile = profile_dataset(weekly["values"], domain="traffic", timestamps=weekly["timestamps"], channel_names=weekly["channels"])
    axes = list(profile.axes.keys())
    values = [float(profile.axes[name]) for name in axes]
    values = values + values[:1]
    angles = np.linspace(0, 2 * np.pi, len(axes), endpoint=False).tolist()
    angles = angles + angles[:1]

    def _build(fig):
        ax = fig.add_subplot(111, polar=True)
        ax.plot(angles, values, linewidth=2.8, color=BLUE)
        ax.fill(angles, values, color=SUN, alpha=0.22)
        ax.set_ylim(0, 1.0)
        ax.set_title("Dataset profile context", fontsize=18, pad=26)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(
            [
                "irregularity",
                "noise",
                "predictability",
                "drift",
                "trend",
                "rhythmicity",
                "complexity",
                "nonlinearity",
                "burstiness",
                "regimes",
                "coupling",
                "heterogeneity",
            ],
            fontsize=9,
        )
        ax.set_yticklabels([])
        ax.grid(color=BORDER)

    _save_figure(path, _build)


def _save_rolling_similarity(path: Path) -> None:
    github = starter_dataset("github_breakout_analogs")
    windows = rolling_similarity(github["target"], github["durable_breakout"], window=20, step=5)
    scores = [float(item["similarity_score"]) for item in windows]

    def _build(fig):
        ax = fig.add_subplot(111)
        ax.plot(range(len(scores)), scores, color=BLUE, linewidth=2.8)
        ax.set_ylim(0.0, 1.0)
        ax.set_title("Rolling similarity over time", fontsize=18)
        ax.set_xlabel("window")
        ax.set_ylabel("similarity")
        ax.grid(alpha=0.3)

    _save_figure(path, _build)


def _save_github_preview(path: Path) -> None:
    github = starter_dataset("github_breakout_analogs")
    report = compare_series(github["target"], github["durable_breakout"], left_name="candidate", right_name="durable analog")

    def _build(fig):
        ax = fig.add_subplot(111)
        ax.plot(github["target"], label="candidate", linewidth=2.6, color=BLUE)
        ax.plot(github["durable_breakout"], label="durable analog", linewidth=2.6, color=SUN_DEEP)
        ax.set_title(f"GitHub breakout analog search (similarity {report.similarity_score:.2f})", fontsize=18)
        ax.set_xlabel("time")
        ax.set_ylabel("value")
        ax.grid(alpha=0.28)
        ax.legend(frameon=False)

    _save_figure(path, _build)


def _save_markets_preview(path: Path) -> None:
    markets = starter_dataset("btc_gold_oil_shocks")

    def _build(fig):
        ax = fig.add_subplot(111)
        ax.plot(markets["btc"], label="BTC", linewidth=2.5, color=BLUE)
        ax.plot(markets["gold"], label="Gold", linewidth=2.5, color=SUN_DEEP)
        ax.plot(markets["oil"], label="Oil", linewidth=2.5, color=BLUE_DEEP)
        ax.set_title("BTC / Gold / Oil comparison", fontsize=18)
        ax.set_xlabel("time")
        ax.set_ylabel("value")
        ax.grid(alpha=0.28)
        ax.legend(frameon=False)

    _save_figure(path, _build)


def _save_summary_preview(path: Path) -> None:
    x = np.sin(np.linspace(0, 8 * np.pi, 128))
    y = np.sin(np.linspace(0, 8 * np.pi, 128) + 0.2)
    report = compare_series(x, y, left_name="query", right_name="shifted analog")
    lines = [
        "# EchoTime similarity summary",
        "",
        f"overall similarity: {report.similarity_score:.2f}",
        f"label: {report.qualitative_label}",
        "top components:",
    ]
    for name, score in list(report.component_scores.items())[:4]:
        lines.append(f"- {name.replace('_', ' ')}: {score:.2f}")
    lines.extend(["", "why:", report.interpretation])
    image = _render_text_card(
        title="EchoTime similarity card preview",
        subtitle="A compare-first quicklook for humans and agents",
        body="\n".join(lines),
        accent=SUN,
        mono=True,
        size=(1280, 760),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def _save_title_card(path: Path) -> None:
    body = (
        "EchoTime\n\n"
        "Compare time series and datasets with explainable structural similarity.\n\n"
        "Quickstart:\n"
        "pip install echotime\n"
        "echotime-demo --open-browser\n\n"
        "Ships with Pages-ready demos, starter datasets, and agent-ready JSON."
    )
    image = _render_text_card(
        title="EchoTime release surface",
        subtitle="v0.17.0 formal release draft",
        body=body,
        accent=BLUE,
        mono=False,
        size=(1280, 720),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def _save_quickstart_gif(path: Path) -> None:
    x = np.sin(np.linspace(0, 8 * np.pi, 128))
    y = np.sin(np.linspace(0, 8 * np.pi, 128) + 0.2)
    report = compare_series(x, y, left_name="x", right_name="y")

    frames = [
        _render_text_card(
            title="Quickstart: compare two curves",
            subtitle="Copy, paste, and get a similarity verdict in seconds",
            body=(
                "pip install echotime\n"
                "python -c \"import numpy as np; from echotime import compare_series; "
                "x=np.sin(np.linspace(0,8*np.pi,128)); "
                "y=np.sin(np.linspace(0,8*np.pi,128)+0.2); "
                "print(compare_series(x,y).to_summary_card_markdown())\""
            ),
            accent=BLUE,
            mono=True,
        ),
        _render_text_card(
            title="Similarity verdict",
            subtitle="Readable output instead of one opaque score",
            body=(
                "# EchoTime similarity summary\n\n"
                f"overall similarity: {report.similarity_score:.2f}\n"
                f"label: {report.qualitative_label}\n"
                f"top components: {', '.join(name.replace('_', ' ') for name in list(report.component_scores)[:3])}\n"
                f"why: {report.interpretation}"
            ),
            accent=SUN,
            mono=True,
        ),
        _render_text_card(
            title="Agent-ready envelope",
            subtitle="Move from a readable report to compact JSON handoff",
            body=(
                "from echotime import ts_compare\n\n"
                "payload = ts_compare(x, y)\n"
                "print(payload['tool'])\n"
                "print(payload['verdict'])\n\n"
                f"confidence: {report.qualitative_label}"
            ),
            accent=BLUE_DEEP,
            mono=True,
        ),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=[1300, 1400, 1400], loop=0)


def _social_card_png(*, title: str, subtitle: str, bullets: list[str], accent: str) -> Image.Image:
    image, draw = _card_canvas(1200, 630, accent=accent)
    title_font = _font(32)
    hero_font = _font(54)
    subtitle_font = _font(25)
    bullet_font = _font(28)
    draw.text((84, 76), "EchoTime", font=title_font, fill=TEXT)
    draw.text((84, 140), title, font=hero_font, fill=TEXT)
    draw.text((84, 204), subtitle, font=subtitle_font, fill=MUTED)
    y = 278
    for bullet in bullets[:4]:
        draw.text((84, y), f"- {bullet}", font=bullet_font, fill=TEXT)
        y += 64
    draw.text((84, 548), "explainable time-series similarity for humans and agents", font=_font(22), fill=MUTED)
    return image


def _animated_pack_preview(title: str, subtitle: str, bullets: list[str], accent: str, path: Path) -> None:
    frames = []
    for count in (2, 3, 4):
        frames.append(_social_card_png(title=title, subtitle=subtitle, bullets=bullets[:count], accent=accent))
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=[900, 900, 1100], loop=0)


def _write_demo_pack_bitmaps(root: Path) -> None:
    github = starter_dataset("github_breakout_analogs")
    github_report = compare_series(github["target"], github["durable_breakout"], left_name="candidate", right_name="durable analog")
    markets = starter_dataset("btc_gold_oil_shocks")
    market_report = compare_series(markets["btc"], markets["gold"], left_name="BTC", right_name="Gold")
    energy = starter_dataset("energy_load_heatwave")
    energy_profile = profile_dataset(energy["values"], domain="energy", timestamps=energy["timestamps"], channel_names=energy["channels"])
    energy_card = summary_card_dict(energy_profile, audience="operations")

    packs = {
        "github_breakout_analogs": {
            "title": "GitHub breakout analogs",
            "subtitle": f"candidate vs durable analog - similarity {github_report.similarity_score:.2f}",
            "bullets": [
                f"label: {github_report.qualitative_label}",
                f"shape similarity: {github_report.component_scores['shape_similarity']:.2f}",
                f"dtw similarity: {github_report.component_scores['dtw_similarity']:.2f}",
                "ask whether growth is durable or just viral",
            ],
            "accent": SUN,
        },
        "btc_vs_gold_under_shocks": {
            "title": "BTC vs Gold under shocks",
            "subtitle": f"BTC vs Gold - similarity {market_report.similarity_score:.2f}",
            "bullets": [
                f"label: {market_report.qualitative_label}",
                f"shape similarity: {market_report.component_scores['shape_similarity']:.2f}",
                f"spectral similarity: {market_report.component_scores['spectral_similarity']:.2f}",
                "show how analogies shift under stress",
            ],
            "accent": SUN,
        },
        "heatwave_vs_grid_load": {
            "title": "Heatwave vs grid load",
            "subtitle": "energy profile context for comparison and handoff",
            "bullets": [
                f"top axis: {energy_card['top_structure_axes'][0]['plain_label']}",
                f"top axis: {energy_card['top_structure_axes'][1]['plain_label']}",
                f"reliability: {energy_card['dataset_facts']['reliability']['score']:.2f}",
                "use profile context to explain similarity",
            ],
            "accent": BLUE,
        },
    }

    for pack, meta in packs.items():
        folder = root / "examples" / "demo_packs" / pack
        card = _social_card_png(
            title=meta["title"],
            subtitle=meta["subtitle"],
            bullets=meta["bullets"],
            accent=meta["accent"],
        )
        card.save(folder / "social_card.png")
        _animated_pack_preview(meta["title"], meta["subtitle"], meta["bullets"], meta["accent"], folder / "preview.gif")


def generate_preview_assets(root: Path = ROOT) -> None:
    assets = root / "assets"
    _save_summary_preview(assets / "summary_card_preview.png")
    _save_title_card(assets / "echotime_title_card.png")
    _save_profile_radar(assets / "report_radar_preview.png")
    _save_rolling_similarity(assets / "rolling_similarity_preview.png")
    _save_github_preview(assets / "github_breakout_preview.png")
    _save_markets_preview(assets / "markets_preview.png")
    _save_quickstart_gif(assets / "quickstart.gif")
    _write_demo_pack_bitmaps(root)


def main() -> None:
    generate_preview_assets(ROOT)
    print("preview assets updated")


if __name__ == "__main__":
    main()
