"""Verify that the mechanism article and lab survive static bundle export."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from echotime.sitebundle import _knowledge_pages, _similarity_lab_pages, write_pages_bundle


class ResourceLinks(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.links: list[str] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs):
        attributes = dict(attrs)
        attribute = "href" if tag == "a" else "src" if tag in {"img", "script"} else None
        if attribute and attributes.get(attribute):
            self.links.append(attributes[attribute])


def test_six_lab_resources_are_mapped_and_match_the_manifest():
    pages = _similarity_lab_pages()
    assert set(pages) == {
        "guide/similarity-lab.html",
        "assets/similarity-lab/lab.js",
        "assets/similarity-lab/states.json",
        "assets/similarity-lab/manifest.json",
        "assets/similarity-lab/mechanism-comparison.gif",
        "assets/similarity-lab/mechanism-comparison.png",
    }
    manifest = json.loads(pages["assets/similarity-lab/manifest.json"])
    assert manifest["states"] == 147
    assert manifest["methods"] == 11
    for name, expected in manifest["sha256"].items():
        path = "guide/" + name if name.endswith(".html") else "assets/similarity-lab/" + name
        content = pages[path]
        data = content.encode("utf-8") if isinstance(content, str) else content
        assert hashlib.sha256(data).hexdigest() == expected
    assert pages["assets/similarity-lab/mechanism-comparison.gif"].startswith(b"GIF89a")
    assert pages["assets/similarity-lab/mechanism-comparison.png"].startswith(b"\x89PNG")


def test_exported_lab_and_article_use_real_local_resources(tmp_path):
    root = write_pages_bundle(tmp_path / "site")
    for page in ("guide/similarity-lab.html", "articles/what-time-series-similarity-measures.en.html"):
        html = (root / page).read_text(encoding="utf-8")
        for href in ResourceLinks(html).links:
            parts = urlsplit(href)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(page), parts.path))
            assert (root / target).is_file(), (page, href)
    article = (root / "articles/what-time-series-similarity-measures.en.html").read_text()
    assert 'src="../assets/similarity-lab/mechanism-comparison.gif"' in article
    assert 'href="../guide/similarity-lab.html"' in article
    assert (root / "assets/similarity-lab/states.json").is_file()


def test_article_formulas_remain_readable_without_a_math_runtime():
    article = _knowledge_pages()["articles/what-time-series-similarity-measures.en.html"]
    formulas = re.findall(r'<pre><code class="language-text">(.*?)</code></pre>', article, re.S)
    assert len(formulas) == 6
    assert any("D[i,j]" in formula for formula in formulas)
    assert any("Σπ" in formula for formula in formulas)
    assert all("<em>" not in formula and "<strong>" not in formula for formula in formulas)
    assert "$$" not in article and r"\frac" not in article
