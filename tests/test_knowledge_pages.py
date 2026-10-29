"""Check that reading assets survive packaging and link to their actual targets."""

from __future__ import annotations

import json
import posixpath
import re
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

import pytest

from echotime.seo import search_metadata
from echotime.sitebundle import _knowledge_pages, project_pages_bundle


class Links(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.targets: list[str] = []
        self.ids: set[str] = set()
        self.feed(html)

    def handle_starttag(self, tag: str, attrs):
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        attribute = "href" if tag == "a" else "src" if tag in {"img", "script"} else None
        if attribute and attributes.get(attribute):
            self.targets.append(attributes[attribute])


@pytest.fixture(scope="module")
def exported_pages():
    return project_pages_bundle()


def test_reading_bundle_contains_articles_and_consistent_reference_downloads():
    pages = _knowledge_pages()
    assert "articles/time-series-similarity-guide.en.html" in pages
    assert "articles/time-series-similarity-guide.zh-CN.html" in pages
    assert "articles/what-time-series-similarity-measures.en.html" in pages
    payload = json.loads(pages["references/time-series-similarity-literature.json"])
    keys = [entry["id"] for entry in payload["references"]]
    assert len(keys) == len(set(keys)) == payload["record_count"]
    bibkeys = re.findall(r"@\w+\s*\{([^,]+),", pages["references/time-series-similarity-literature.bib"])
    assert set(keys) == set(bibkeys)
    assert "manifest/knowledge_sources.json" in pages


def test_reading_page_links_and_fragments_resolve(exported_pages):
    pages = _knowledge_pages()
    parsed = {path: Links(content) for path, content in pages.items() if path.endswith(".html")}
    for path, document in list(parsed.items()):
        for href in document.targets:
            parts = urlsplit(href)
            if parts.scheme or parts.netloc:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(path), unquote(parts.path))) if parts.path else path
            assert target in exported_pages, (path, href)
            if parts.fragment and target.endswith(".html"):
                if target not in parsed:
                    parsed[target] = Links(exported_pages[target])
                assert unquote(parts.fragment) in parsed[target].ids, (path, href)


def test_chinese_article_metadata_preserves_language():
    path = "articles/time-series-similarity-guide.zh-CN.html"
    enriched = search_metadata(_knowledge_pages()[path], path)
    schema = re.search(r'<script type="application/ld\+json">(.*?)</script>', enriched, re.S)
    payload = json.loads(schema.group(1))
    page = next(item for item in payload["@graph"] if item["@type"] == "WebPage")
    assert page["inLanguage"] == "zh-CN"
