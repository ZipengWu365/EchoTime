#!/usr/bin/env python3
"""Build reproducible, numerically specified GIF explanations for the atlas.

Run with ``--check`` to validate the committed asset bundle without rendering it.
The educational calculations live in method_animation_data; none become public
similarity APIs or benchmark results through this renderer.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
BUNDLE = ROOT / "src/echotime/data/method_animations"
DOCS = ROOT / "docs/method-animations"
WIDTH, HEIGHT = 1000, 650
BG = "#101e2b"
PANEL = "#172a3b"
GRID = "#2a4052"
TEXT = "#f1f5f8"
MUTED = "#acbdcc"
CYAN = "#5ad6d5"
CORAL = "#ff9d86"
GOLD = "#ffd16d"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")


def source_hashes() -> dict[str, str]:
    paths = [Path(__file__), *sorted((ROOT / "tools/method_animation_data").glob("*.py"))]
    paths += [ROOT / "src/echotime" / name for name in (
        "similarity_method_atlas.py", "similarity_methods.py", "similarity.py",
        "data/ts_similarity_package_v2_registry.csv",
    )]
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in paths if path.is_file()}


def load_examples() -> list[dict]:
    examples = []
    for name in ("pointwise_sliding", "elastic_kernel", "feature_model_embedding"):
        module = importlib.import_module("tools.method_animation_data." + name)
        examples.extend(module.build_examples())
    from echotime.similarity_method_atlas import extracted_similarity_methods, native_similarity_methods
    native = {row["name"]: row for row in native_similarity_methods()}
    registry = {row["name"]: row for row in extracted_similarity_methods()}
    expected = set(native) | set(registry)
    ids = [entry["id"] for entry in examples]
    if len(ids) != len(set(ids)) or set(ids) != expected:
        raise ValueError(f"Incomplete/duplicate animation coverage. Missing={sorted(expected-set(ids))}; extra={sorted(set(ids)-expected)}")
    for entry in examples:
        validate_example(entry)
        if entry["id"] in native:
            entry["echotime_status"] = "EchoTime report component / reference metric"
            entry["echotime_api"] = entry["id"]
        else:
            row = registry[entry["id"]]
            if entry["family"] != row["family"]:
                raise ValueError(f"Wrong family for {entry['id']}")
            entry["echotime_status"] = row["echotime_status"]
            entry["echotime_api"] = row["echotime_api"]
    order = {name: i for i, name in enumerate([*native, *registry])}
    return sorted(examples, key=lambda entry: order[entry["id"]])


def validate_example(entry: dict) -> None:
    required = ("id", "title", "family", "definition", "formula", "intro_en", "intro_zh", "steps_en", "steps_zh", "caveats_en", "caveats_zh", "sources", "x", "y", "parameters", "result", "frames")
    for key in required:
        if key not in entry:
            raise ValueError(f"{entry.get('id')}: missing {key}")
    if entry["definition"] not in {"echotime", "reference", "protocol"}:
        raise ValueError(f"{entry['id']}: invalid definition label")
    if len(entry["steps_en"]) != 4 or len(entry["steps_zh"]) != 4:
        raise ValueError(f"{entry['id']}: four explanatory stages required")
    if not entry["sources"] or not all(source["url"].startswith("https://") for source in entry["sources"]):
        raise ValueError(f"{entry['id']}: primary definition links required")
    if not math.isfinite(float(entry["result"]["value"])):
        raise ValueError(f"{entry['id']}: nonfinite final result")
    if len(entry["frames"]) < 12 or len({canonical_bytes(frame) for frame in entry["frames"]}) < 4:
        raise ValueError(f"{entry['id']}: insufficient calculation states")
    for frame in entry["frames"]:
        if frame["phase"] not in range(4):
            raise ValueError(f"{entry['id']}: invalid phase")
        if frame["panel"]["kind"] not in {"bars", "lines", "scatter", "matrix", "alignment", "pipeline"}:
            raise ValueError(f"{entry['id']}: unknown plot type")
    # Also rejects accidental NaNs/Infinity anywhere in inputs or traces.
    canonical_bytes(entry)


@lru_cache(maxsize=32)
def _font(size: int, bold: bool = False):
    from PIL import ImageFont
    stem = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    candidates = [Path("/usr/share/fonts/truetype/dejavu") / stem]
    if candidates[0].is_file():
        return ImageFont.truetype(str(candidates[0]), size=size)
    try:
        import matplotlib
        candidates.append(Path(matplotlib.get_data_path()) / "fonts/ttf" / stem)
    except ImportError:
        pass
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    raise RuntimeError("Install EchoTime's docs extra (including Matplotlib) for reproducible DejaVu fonts.")


def _wrap(draw, text: str, font, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in str(text).splitlines() or [""]:
        current = ""
        for word in paragraph.split():
            trial = (current + " " + word).strip()
            if draw.textlength(trial, font=font) <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = ""
                # Long identifiers must wrap too; never clip mathematical labels.
                for char in word:
                    if draw.textlength(current + char, font=font) > width and current:
                        lines.append(current)
                        current = ""
                    current += char
        lines.append(current)
    return lines


def _text(draw, xy, text, size=17, fill=TEXT, bold=False, width=None, max_lines=None, spacing=5):
    font = _font(size, bold)
    lines = _wrap(draw, str(text), font, width) if width else [str(text)]
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textlength(last + "…", font=font) > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    for index, line in enumerate(lines):
        draw.text((xy[0], xy[1] + index * (size + spacing)), line, font=font, fill=fill)
    return len(lines) * (size + spacing)


def _bounds(values, *, zero=False):
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if zero:
        finite.append(0.0)
    if not finite:
        return -1.0, 1.0
    low, high = min(finite), max(finite)
    pad = (high - low) * 0.1 if high > low else max(abs(high) * 0.1, 0.5)
    return low - pad, high + pad


def _number(value):
    return f"{float(value):.3g}"


def _axes(draw, rect, low, high, count=None):
    x0, y0, x1, y1 = rect
    for k in range(4):
        y = y0 + (y1 - y0) * k / 3
        value = high - (high - low) * k / 3
        draw.line((x0, y, x1, y), fill=GRID, width=1)
        _text(draw, (x0 - 41, y - 7), _number(value), 11, MUTED)
    if count:
        for index in sorted({0, (count - 1) // 2, count - 1}):
            x = x0 + (x1 - x0) * index / max(count - 1, 1)
            _text(draw, (x - 5, y1 + 5), str(index), 11, MUTED)


def _line(draw, values, rect, limits, color, marker=None, x_values=None, x_limits=None, width=3):
    if not len(values):
        return
    x0, y0, x1, y1 = rect
    low, high = limits
    xs = list(x_values) if x_values is not None else list(range(len(values)))
    xmin, xmax = x_limits if x_limits is not None else (min(xs), max(xs))
    points = []
    for x, value in zip(xs, values):
        if value is None:
            if len(points) > 1:
                draw.line(points, fill=color, width=width)
            points = []
            continue
        point = (x0 + (x1 - x0) * (x - xmin) / max(xmax - xmin, 1e-12), y1 - (y1 - y0) * (float(value) - low) / (high - low))
        points.append(point)
    if len(points) > 1:
        draw.line(points, fill=color, width=width)
    if len(values) <= 32:
        for x, y in points:
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=color)
    if marker is not None and 0 <= int(marker) < len(values) and values[int(marker)] is not None:
        i = int(marker)
        x = x0 + (x1 - x0) * (xs[i] - xmin) / max(xmax - xmin, 1e-12)
        y = y1 - (y1 - y0) * (float(values[i]) - low) / (high - low)
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=GOLD, outline=BG, width=2)


def _legend(draw, x, y, a_label, b_label=None):
    draw.line((x, y + 7, x + 18, y + 7), fill=CYAN, width=3)
    _text(draw, (x + 25, y - 2), a_label, 12, MUTED, width=250, max_lines=1)
    if b_label:
        draw.line((x + 295, y + 7, x + 313, y + 7), fill=CORAL, width=3)
        _text(draw, (x + 320, y - 2), b_label, 12, MUTED, width=255, max_lines=1)


def _raw_plot(draw, entry, frame):
    draw.rounded_rectangle((24, 105, 672, 297), radius=12, fill=PANEL)
    label = entry.get("input_label", "Illustrative input sequences · shared amplitude scale")
    _text(draw, (42, 114), label, 13, MUTED, width=610, max_lines=2, spacing=3)
    _legend(draw, 69, 149, "A", "B")
    x, y = entry["x"], entry["y"]
    low, high = _bounds(list(x) + list(y))
    rect = (69, 173, 648, 266)
    count = max(len(x), len(y))
    _axes(draw, rect, low, high, count)
    for index in frame.get("input_highlight", []):
        xpos = rect[0] + (rect[2] - rect[0]) * index / max(count - 1, 1)
        draw.line((xpos, rect[1], xpos, rect[3]), fill="#466075", width=2)
    for values, color in ((x, CYAN), (y, CORAL)):
        starts = [0] + [int(i) for i in entry.get("input_breaks", []) if 0 < i < len(values)]
        ends = starts[1:] + [len(values)]
        for start, end in zip(starts, ends):
            _line(draw, values[start:end], rect, (low, high), color,
                  x_values=list(range(start, end)), x_limits=(0, max(count - 1, 1)))


def _panel(draw, panel):
    draw.rounded_rectangle((24, 309, 672, 582), radius=12, fill=PANEL)
    _text(draw, (42, 321), panel.get("title", "Intermediate calculation"), 17, TEXT, True, width=610, max_lines=2)
    kind = panel["kind"]
    a, b = panel.get("a", []), panel.get("b", [])
    rect = (69, 385, 648, 549)
    if kind in {"lines", "bars"}:
        _legend(draw, 69, 363, panel.get("a_label", "A / contribution"), panel.get("b_label", "B") if b else None)
        low, high = _bounds(list(a) + list(b), zero=kind == "bars")
        count = max(len(a), len(b), 1)
        _axes(draw, rect, low, high)
        if kind == "lines":
            xs = panel.get("x")
            x_limits = (min(xs), max(xs)) if xs is not None else (0, max(count - 1, 1))
            _line(draw, a, rect, (low, high), CYAN, panel.get("marker"), xs, x_limits)
            _line(draw, b, rect, (low, high), CORAL, panel.get("marker"), xs if xs is not None and len(xs) == len(b) else None, x_limits)
            for fraction in (0, 0.5, 1):
                value = x_limits[0] + fraction * (x_limits[1] - x_limits[0])
                _text(draw, (rect[0] + fraction * (rect[2] - rect[0]) - 7, rect[3] + 5), _number(value), 11, MUTED)
        else:
            slot = (rect[2] - rect[0]) / count
            baseline = rect[3] - (rect[3] - rect[1]) * (0 - low) / (high - low)
            for series_index, values in enumerate((a, b) if b else (a,)):
                for i, value in enumerate(values):
                    if value is None:
                        continue
                    width = slot * (0.34 if b else 0.64)
                    cx = rect[0] + (i + 0.5) * slot + ((series_index - 0.5) * width if b else 0)
                    yy = rect[3] - (rect[3] - rect[1]) * (float(value) - low) / (high - low)
                    color = CORAL if series_index else CYAN
                    if panel.get("marker") == i:
                        color = GOLD
                    draw.rectangle((cx - width / 2, min(baseline, yy), cx + width / 2, max(baseline, yy) + 1), fill=color)
            labels = panel.get("labels", [str(i) for i in range(count)])
            stride = max(1, math.ceil(count / 9))
            for i in range(0, count, stride):
                if i < len(labels):
                    _text(draw, (rect[0] + i * slot, rect[3] + 5), labels[i], 10, MUTED, width=max(20, int(slot * stride)), max_lines=1)
    elif kind == "scatter":
        low, high = _bounds(b)
        xmin, xmax = _bounds(a)
        _axes(draw, rect, low, high)
        for i, (x, y) in enumerate(zip(a, b)):
            xx = rect[0] + (rect[2] - rect[0]) * (float(x) - xmin) / (xmax - xmin)
            yy = rect[3] - (rect[3] - rect[1]) * (float(y) - low) / (high - low)
            radius = 6 if panel.get("marker") == i else 4
            draw.ellipse((xx - radius, yy - radius, xx + radius, yy + radius), fill=GOLD if panel.get("marker") == i else CYAN)
        _text(draw, (69, 361), "Matched pairs: horizontal = A, vertical = B", 12, MUTED)
        for fraction in (0, 0.5, 1):
            _text(draw, (rect[0] + fraction * (rect[2] - rect[0]) - 7, rect[3] + 5), _number(xmin + fraction * (xmax - xmin)), 11, MUTED)
    elif kind == "matrix":
        values = panel["z"]
        rows, columns = len(values), len(values[0])
        finite = [v for row in values for v in row if v is not None]
        low, high = (min(finite), max(finite)) if finite else (0, 1)
        # Square cells make path slopes meaningful; preserve the aspect ratio.
        cell = min((rect[2] - rect[0]) / columns, (rect[3] - rect[1]) / rows)
        x0 = rect[0] + ((rect[2] - rect[0]) - columns * cell) / 2
        y0 = rect[1]
        for i, row in enumerate(values):
            for j, value in enumerate(row):
                color = "#0c1621" if value is None else _heat((value - low) / max(high - low, 1e-12))
                draw.rectangle((x0 + j * cell, y0 + i * cell, x0 + (j + 1) * cell - 1, y0 + (i + 1) * cell - 1), fill=color)
        path = [(x0 + (j + 0.5) * cell, y0 + (i + 0.5) * cell) for i, j in panel.get("path", [])]
        if len(path) > 1:
            draw.line(path, fill=GOLD, width=3)
        if panel.get("cursor") is not None:
            i, j = panel["cursor"]
            draw.rectangle((x0 + j * cell, y0 + i * cell, x0 + (j + 1) * cell, y0 + (i + 1) * cell), outline=TEXT, width=2)
        _text(draw, (69, 361), panel.get("row_label", "rows: A") + " · " + panel.get("col_label", "columns: B"), 12, MUTED, width=570, max_lines=1)
        _text(draw, (x0, rect[3] + 5), f"dark {low:.3g} → bright {high:.3g}; blank = unavailable", 11, MUTED, width=570, max_lines=1)
    elif kind == "alignment":
        low, high = _bounds(list(a) + list(b))
        top = (69, 378, 648, 432)
        bottom = (69, 477, 648, 531)
        def point(values, index, box):
            return (box[0] + (box[2] - box[0]) * index / max(len(values) - 1, 1), box[3] - (box[3] - box[1]) * (values[index] - low) / (high - low))
        for i, j in panel.get("pairs", []):
            draw.line((*point(a, i, top), *point(b, j, bottom)), fill="#657253", width=1)
        _line(draw, a, top, (low, high), CYAN)
        _line(draw, b, bottom, (low, high), CORAL)
        _text(draw, (45, 396), "A", 13, CYAN)
        _text(draw, (45, 494), "B", 13, CORAL)
        _text(draw, (69, 550), "Two vertical lanes · connections show matched indices", 11, MUTED)
    elif kind == "pipeline":
        labels = panel.get("labels", [])[:4]
        gap = 12
        box_width = (579 - gap * max(len(labels) - 1, 0)) / max(len(labels), 1)
        for i, label in enumerate(labels):
            xx = 69 + i * (box_width + gap)
            active = i == panel.get("active", 0)
            draw.rounded_rectangle((xx, 382, xx + box_width, 451), radius=7, outline=GOLD if active else GRID, width=2, fill="#20374a")
            _text(draw, (xx + 9, 395), label, 13, GOLD if active else TEXT, width=int(box_width - 18), max_lines=3)
            if i < len(labels) - 1:
                draw.line((xx + box_width, 416, xx + box_width + gap, 416), fill=MUTED, width=2)
        if a:
            low, high = _bounds(list(a) + list(b))
            _line(draw, a, (69, 482, 648, 545), (low, high), CYAN)
            _line(draw, b, (69, 482, 648, 545), (low, high), CORAL)


def _heat(t):
    t = max(0, min(1, float(t)))
    if t < 0.6:
        a, b, t = (23, 49, 67), (50, 166, 171), t / 0.6
    else:
        a, b, t = (50, 166, 171), (244, 212, 129), (t - 0.6) / 0.4
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def render_frame(entry: dict, frame: dict, index: int, total: int):
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    definition = {"echotime": "CHECKED ECHOTIME EXAMPLE", "reference": "REFERENCE FORMULA", "protocol": "SPECIFIED EXAMPLE PROTOCOL"}[entry["definition"]]
    _text(draw, (26, 18), "ECHOTIME  /  METHOD NOTES", 12, CYAN, True)
    _text(draw, (690, 18), definition, 11, MUTED, True, width=285, max_lines=1)
    _text(draw, (24, 41), entry["title"], 27, TEXT, True, width=940, max_lines=1)
    _text(draw, (26, 79), entry["id"] + "  ·  " + entry["family"], 12, MUTED, width=940, max_lines=1)
    _raw_plot(draw, entry, frame)
    _panel(draw, frame["panel"])
    draw.rounded_rectangle((690, 105, 976, 582), radius=12, fill=PANEL)
    _text(draw, (708, 119), "FOUR STAGES", 12, MUTED, True)
    for phase, step in enumerate(entry.get("animation_steps_en", entry["steps_en"])):
        y = 151 + phase * 75
        active = phase == frame["phase"]
        draw.rounded_rectangle((706, y, 960, y + 68), radius=7, fill="#254253" if active else PANEL)
        _text(draw, (716, y + 9), str(phase + 1), 15, GOLD if active else MUTED, True)
        _text(draw, (738, y + 8), step, 13, TEXT if active else MUTED, width=211, max_lines=3, spacing=4)
    draw.line((708, 462, 958, 462), fill=GRID, width=1)
    value = frame.get("value")
    label = frame.get("value_label", "Current calculation")
    if value is None:
        value = entry["result"]["value"]
        label = "Final example " + entry["result"]["label"]
    _text(draw, (708, 476), label, 13, MUTED, width=248, max_lines=2)
    _text(draw, (708, 515), f"{float(value):.6g}", 29, GOLD, True, width=248, max_lines=1)
    _text(draw, (708, 556), "Synthetic input · no ranking claim", 11, MUTED)
    _text(draw, (26, 595), f"{frame['phase'] + 1}/4  ·  {frame['caption']}", 16, TEXT, width=945, max_lines=2, spacing=3)
    draw.rectangle((24, 641, 976, 644), fill=GRID)
    draw.rectangle((24, 641, 24 + 952 * (index + 1) / total, 644), fill=CYAN)
    return image


def render_example(entry: dict, output: Path) -> dict:
    from PIL import Image
    media = output / "media"
    traces = output / "traces"
    media.mkdir(parents=True, exist_ok=True)
    traces.mkdir(parents=True, exist_ok=True)
    frames = [render_frame(entry, frame, i, len(entry["frames"])) for i, frame in enumerate(entry["frames"])]
    palette = Image.new("P", (1, 1))
    from PIL.ImageColor import getrgb
    colors = [getrgb(color) for color in (BG, PANEL, GRID, TEXT, MUTED, CYAN, CORAL, GOLD, "#254253", "#20374a", "#466075", "#657253", "#0c1621")]
    colors += [_heat(i / 100) for i in range(101)]
    colors += [(i, i, i) for i in range(0, 256, 8)]
    palette.putpalette([v for color in (colors + [(0, 0, 0)] * 256)[:256] for v in color])
    quantized = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    durations = [350] * len(frames)
    durations[0], durations[-1] = 900, 2000
    gif = media / (entry["id"] + ".gif")
    poster = media / (entry["id"] + ".png")
    quantized[0].save(gif, save_all=True, append_images=quantized[1:], duration=durations, loop=0, optimize=True, disposal=1)
    frames[-1].save(poster, optimize=True)
    trace = traces / (entry["id"] + ".json")
    trace.write_bytes(canonical_bytes(entry))
    with Image.open(gif) as decoded:
        actual_frames = decoded.n_frames
        for i in range(actual_frames):
            decoded.seek(i)
            decoded.load()
        if actual_frames < 4:
            raise ValueError(f"{entry['id']}: GIF has no useful animation")
    return {"id": entry["id"], "frames": actual_frames, "duration_ms": sum(durations), "width": WIDTH, "height": HEIGHT, "gif_bytes": gif.stat().st_size, "poster_bytes": poster.stat().st_size}


def write_markdown(examples: list[dict]) -> list[Path]:
    from echotime.method_animations import FAMILY_LABELS, DEFINITION_LABELS
    DOCS.mkdir(parents=True, exist_ok=True)
    written = []
    index = ["# Animated time-series similarity methods / 时序相似性方法动图", "", "137 individual explanations cover the existing 10 EchoTime report components and 127 imported atlas entries. Each has a GIF, static image, four calculation stages, limitations, primary definition links and a downloadable numerical trace.", "", "覆盖现有 10 个 EchoTime 原生分项和 127 个方法条目。每项包含 GIF、静态图、四步说明、使用边界、定义来源以及示例输入与计算过程。", "", "**Scope:** small deterministic teaching examples. `Checked against EchoTime` identifies actual implementation checks; `Reference-formula demonstration` specifies a mathematical variant; `Specified illustrative protocol` explains a concrete encoder/model choice. These examples do not implement all atlas methods as public APIs and provide no performance ranking.", "", "**Read on the website:** [Methods Atlas](https://zipengwu.me/EchoTime/guide/methods.html#method-animations). The existing page offers search, English/Chinese text, and click-to-play controls; all animations are static until requested.", "", "| Family / 类别 | Entries |", "|---|---:|"]
    for family, labels in FAMILY_LABELS.items():
        members = [entry for entry in examples if entry["family"] == family]
        index.append(f"| [{labels[0]} / {labels[1]}]({family}.md) | {len(members)} |")
        lines = [f"# {labels[0]} / {labels[1]}", "", "[All animation families](README.md) · [Existing web Methods Atlas](https://zipengwu.me/EchoTime/guide/methods.html#method-animations)", "", "The values below belong to the documented synthetic example. Animation coverage and EchoTime API coverage are separate.", ""]
        lines += [f"- [{entry['title']}](#{entry['id']})" for entry in members]
        lines.append("")
        for entry in members:
            name = entry["id"]
            base = "../../src/echotime/data/method_animations"
            value = entry["result"]
            lines += [f'<a id="{name}"></a>', f"## {entry['title']} · `{name}`", "", f"**Demonstration:** {DEFINITION_LABELS[entry['definition']][0]} / {DEFINITION_LABELS[entry['definition']][1]}", "", f"**EchoTime coverage:** {entry['echotime_status']}" + (f" · `{entry['echotime_api']}`" if entry.get("echotime_api") else ""), "", f"![{entry['title']}: four-stage numerical explanation]({base}/media/{name}.gif)", "", f"[Static image]({base}/media/{name}.png) · [Inputs and full calculation trace]({base}/traces/{name}.json) · [Open in the website](https://zipengwu.me/EchoTime/guide/methods.html#animation-{name})", "", entry["intro_en"], "", entry["intro_zh"], "", "### Calculation / 计算", "", "```text", entry["formula"], "```", ""]
            for i, (english, chinese) in enumerate(zip(entry["steps_en"], entry["steps_zh"]), 1):
                lines += [f"{i}. {english}  ", f"   {chinese}"]
            lines += ["", f"**Example {value['label']}:** `{value['value']:.8g}`. {value['detail']}", "", "**Parameters:**", "", "```json", json.dumps(entry["parameters"], indent=2, ensure_ascii=False), "```", "", "### Interpretation and limits / 解释与边界", ""]
            for english, chinese in zip(entry["caveats_en"], entry["caveats_zh"]):
                lines += [f"- {english} {chinese}"]
            lines += ["", "### Definition sources / 定义来源", ""]
            lines += [f"- [{source['label']}]({source['url']})" for source in entry["sources"]]
            lines.append("")
        path = DOCS / (family + ".md")
        path.write_text("\n".join(line.rstrip() for line in lines).rstrip() + "\n", encoding="utf-8")
        written.append(path)
    index += ["", "## Reproduce and validate / 复现与验证", "", "```bash", "python -m pip install -e '.[dev,docs]'", "python tools/build_method_animations.py", "python tools/build_method_animations.py --check", "echotime --export-pages docs", "```", "", "The renderer uses Pillow and the DejaVu fonts distributed with Matplotlib. Rendering needs only a CPU. Input traces retain the example parameters, intermediate matrices/vectors and output values. Runtime imports and website export use the prebuilt files, without plotting dependencies.", "", "**Visual convention:** A is cyan and B is coral. Gold marks the active contribution, state or alignment path. Matrix blank cells are unavailable/uncomputed as described by the frame; matrix color scales can change as the visible range changes. Distances, divergences, correlations and kernels keep their own units and direction. A large score has no cross-method interpretation.", "", "**中文阅读提示：** 青色为 A、珊瑚色为 B，金色标记当前贡献、状态或路径。矩阵空白格的含义见帧内说明；随着可见数值范围变化，矩阵色标可能调整。不同方法的数值单位和方向不同，不能直接横向比较分数大小。", ""]
    path = DOCS / "README.md"
    path.write_text("\n".join(index), encoding="utf-8")
    return written + [path]


def check_bundle() -> dict:
    from echotime.similarity_method_atlas import extracted_similarity_methods, native_similarity_methods
    manifest = json.loads((BUNDLE / "manifest.json").read_text())
    if manifest["source_sha256"] != source_hashes():
        raise SystemExit("Stale animation sources; run python tools/build_method_animations.py")
    catalog = json.loads((BUNDLE / "catalog.json").read_text())
    expected = {row["name"] for row in extracted_similarity_methods() + native_similarity_methods()}
    ids = [entry["id"] for entry in catalog["methods"]]
    if set(ids) != expected or len(ids) != len(expected):
        raise SystemExit("Animation catalog does not cover the complete current method atlas")
    for rel, checksum in manifest["files_sha256"].items():
        path = BUNDLE / rel
        if not path.is_file() or digest(path) != checksum:
            raise SystemExit(f"Stale/missing animation asset: {rel}")
    for rel, checksum in manifest["markdown_sha256"].items():
        if digest(ROOT / rel) != checksum:
            raise SystemExit(f"Stale animation explanation: {rel}")
    for entry in catalog["methods"]:
        for suffix in ("gif", "png"):
            rel = f"media/{entry['id']}.{suffix}"
            if rel not in manifest["files_sha256"]:
                raise SystemExit(f"Missing {rel}")
        trace = json.loads((BUNDLE / "traces" / f"{entry['id']}.json").read_text())
        validate_example(trace)
    return {"methods": len(ids), "assets": len(manifest["files_sha256"]), "markdown_pages": len(manifest["markdown_sha256"]), "gif_bytes": sum(row["gif_bytes"] for row in manifest["rendered"])}


def build_method_animations(*, force: bool = False, workers: int = 3) -> dict:
    if not force and (BUNDLE / "manifest.json").is_file():
        try:
            return check_bundle()
        except (SystemExit, FileNotFoundError, KeyError, ValueError):
            pass
    examples = load_examples()
    BUNDLE.mkdir(parents=True, exist_ok=True)
    rendered = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(lambda entry: render_example(entry, BUNDLE), examples):
            rendered.append(result)
            print(f"{len(rendered):3}/{len(examples)} {result['id']}: {result['frames']} frames, {result['gif_bytes']:,} bytes", flush=True)
    catalog = {"schema_version": 1, "count": len(examples), "canvas": {"width": WIDTH, "height": HEIGHT}, "methods": [{key: value for key, value in entry.items() if key not in {"frames", "x", "y"}} for entry in examples]}
    (BUNDLE / "catalog.json").write_bytes(canonical_bytes(catalog))
    markdown = write_markdown(examples)
    manifest = {"schema_version": 1, "source_sha256": source_hashes(), "files_sha256": {path.relative_to(BUNDLE).as_posix(): digest(path) for path in sorted(BUNDLE.rglob("*")) if path.is_file() and path.name != "manifest.json"}, "markdown_sha256": {path.relative_to(ROOT).as_posix(): digest(path) for path in markdown}, "rendered": rendered}
    (BUNDLE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return check_bundle()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(check_bundle() if args.check else build_method_animations(force=args.force, workers=args.workers), indent=2))
