"""The explanatory layer must cover, link and preserve its actual examples."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import struct
from urllib.parse import urlsplit

import numpy as np

from echotime.method_animations import animation_assets, animation_catalog, animation_root, method_animations_html
from echotime.similarity_method_atlas import extracted_similarity_methods, native_similarity_methods


class AnimationHTML(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.images = []
        self.links = []
        self.play_buttons = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        item = dict(attrs)
        if item.get("id"):
            self.ids.append(item["id"])
        if tag == "img":
            self.images.append(item)
        if tag == "a":
            self.links.append(item.get("href", ""))
        if tag == "button" and item.get("class") == "animation-play":
            self.play_buttons.append(item)


def test_animation_catalog_covers_current_atlas_without_duplicate_methods():
    entries = animation_catalog()["methods"]
    wanted = {row["name"] for row in extracted_similarity_methods() + native_similarity_methods()}
    assert len(entries) == len(wanted)
    assert {entry["id"] for entry in entries} == wanted
    assert all(len(entry["steps_en"]) == len(entry["steps_zh"]) == 4 for entry in entries)
    assert all(entry["intro_en"] and entry["intro_zh"] and entry["sources"] for entry in entries)
    assert all(entry["definition"] in {"echotime", "reference", "protocol"} for entry in entries)


def test_committed_animation_media_and_traces_match_recorded_hashes():
    root = animation_root()
    manifest = json.loads((root / "manifest.json").read_text())
    assert len(manifest["rendered"]) == len(animation_catalog()["methods"])
    for rel, expected in manifest["files_sha256"].items():
        assert hashlib.sha256((root / rel).read_bytes()).hexdigest() == expected, rel
    for entry in animation_catalog()["methods"]:
        gif = (root / "media" / f"{entry['id']}.gif").read_bytes()
        assert gif[:6] in {b"GIF87a", b"GIF89a"}
        assert struct.unpack("<HH", gif[6:10]) == (1000, 650)
        assert (root / "media" / f"{entry['id']}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        trace = json.loads((root / "traces" / f"{entry['id']}.json").read_text())
        assert trace["result"] == entry["result"]
        assert trace["parameters"] == entry["parameters"]
        assert {frame["phase"] for frame in trace["frames"]} == {0, 1, 2, 3}
        assert len(trace["frames"]) >= 16
        assert np.isfinite(trace["result"]["value"])


def test_animations_are_static_and_every_download_resolves_in_export():
    assets = animation_assets()
    html = method_animations_html()
    parsed = AnimationHTML(html)
    entries = animation_catalog()["methods"]
    assert len(parsed.images) == len(parsed.play_buttons) == len(entries)
    assert len(parsed.ids) == len(set(parsed.ids))
    for entry in entries:
        assert f"animation-{entry['id']}" in parsed.ids
    for item in parsed.images:
        assert item["src"].endswith(".png")  # Loading the page must not animate.
        assert item["loading"] == "lazy"
        assert item["alt"]
        for attr in ("src", "data-poster", "data-gif"):
            target = posixpath.normpath(posixpath.join("guide", item[attr]))
            assert target in assets, target
    assert all(button["aria-pressed"] == "false" for button in parsed.play_buttons)
    for link in parsed.links:
        if not urlsplit(link).scheme:
            assert posixpath.normpath(posixpath.join("guide", link)) in assets, link
    assert "prefers-reduced-motion" in html and "visibilitychange" in html
    assert "<noscript>" in html and "lang='zh-CN'" in html


def test_markdown_media_and_trace_links_are_real_repository_files():
    root = Path(__file__).resolve().parents[1]
    for path in (root / "docs/method-animations").glob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            parts = urlsplit(target)
            if parts.scheme or not parts.path:
                continue
            assert (path.parent / parts.path).resolve().is_file(), (path, target)


def test_simple_reference_trace_retains_actual_input_arithmetic():
    root = animation_root() / "traces"
    euclidean = json.loads((root / "euclidean.json").read_text())
    x, y = np.asarray(euclidean["x"]), np.asarray(euclidean["y"])
    assert np.isclose(euclidean["result"]["value"], np.linalg.norm(x - y))
    squared = json.loads((root / "squared_euclidean.json").read_text())
    assert np.isclose(squared["result"]["value"], euclidean["result"]["value"] ** 2)
    # A lower bound of zero can coexist with a nonzero symbolic mismatch.
    sax = json.loads((root / "sax_mindist.json").read_text())
    hamming = json.loads((root / "sax_hamming_distance.json").read_text())
    assert sax["result"]["value"] == 0
    assert hamming["result"]["value"] > 0
