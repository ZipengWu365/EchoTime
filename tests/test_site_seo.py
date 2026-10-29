from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from xml.etree import ElementTree

import pytest

from echotime.seo import DESCRIPTIONS, SITE_URL, canonical_url, search_metadata
from echotime.sitebundle import project_pages_bundle


class Head(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.metadata: dict[str, list[str]] = {}
        self.links: dict[str, list[str]] = {}
        self.h1_count = 0
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "meta":
            key = attr.get("name") or attr.get("property")
            if key:
                self.metadata.setdefault(key, []).append(attr.get("content") or "")
        if tag == "link":
            self.links.setdefault(attr.get("rel") or "", []).append(attr.get("href") or "")
        if tag == "h1":
            self.h1_count += 1


@pytest.fixture(scope="module")
def bundle() -> dict:
    return project_pages_bundle(version="0.17.1")


def test_every_published_page_has_unique_metadata_and_valid_schema(bundle: dict) -> None:
    descriptions = []
    for path, html in bundle.items():
        if not path.endswith(".html") or path == "404.html":
            continue
        head = Head(html)
        assert head.links["canonical"] == [canonical_url(path)], path
        assert head.metadata["description"] == [DESCRIPTIONS[path]], path
        assert head.metadata["og:url"] == head.links["canonical"], path
        assert head.metadata["og:image"] == [SITE_URL + "social/echotime_title_card.png"], path
        assert head.metadata["robots"] == ["index, follow, max-image-preview:large"], path
        assert head.h1_count == 1, path
        schema = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        assert len(schema) == 1
        payload = json.loads(schema[0])
        assert payload["@context"] == "https://schema.org"
        assert any(node["@type"] == "WebPage" and node["url"] == canonical_url(path) for node in payload["@graph"])
        descriptions.append(head.metadata["description"][0])
    assert len(descriptions) == len(DESCRIPTIONS) == len(set(descriptions))


def test_sitemap_contains_exactly_the_indexable_canonical_pages(bundle: dict) -> None:
    root = ElementTree.fromstring(bundle["sitemap.xml"])
    urls = [item.text for item in root.findall("{*}url/{*}loc")]
    expected = {canonical_url(path) for path in bundle if path.endswith(".html") and path != "404.html"}
    assert len(urls) == len(set(urls)) == len(DESCRIPTIONS)
    assert set(urls) == expected
    assert all(url.startswith("https://zipengwu.me/EchoTime/") for url in urls)
    assert not any("index.html" in url or "404.html" in url for url in urls)
    assert "robots.txt" not in bundle  # Only the owner origin can control it.


def test_custom_domain_project_scope_and_social_asset(bundle: dict) -> None:
    manifest = json.loads(bundle["site.webmanifest"])
    assert manifest["start_url"] == manifest["scope"] == manifest["id"] == "/EchoTime/"
    assert bundle["social/echotime_title_card.png"].startswith(b"\x89PNG")
    assert canonical_url("index.html") == SITE_URL
    assert canonical_url("guide/index.html") == SITE_URL + "guide/"


def test_error_page_is_not_indexable_or_canonicalized_to_valid_page(bundle: dict) -> None:
    head = Head(bundle["404.html"])
    assert head.metadata["robots"] == ["noindex, follow"]
    assert "canonical" not in head.links


def test_enrichment_is_idempotent_and_preserves_body_and_design() -> None:
    original = "<!doctype html><html lang='en'><head><title>EchoTime</title><style>body{color:red}</style></head><body><h1>Compare two curves</h1><p>Original text.</p></body></html>"
    enriched = search_metadata(original, "index.html")
    assert search_metadata(enriched, "index.html") == enriched
    assert enriched[enriched.index("<body>"):] == original[original.index("<body>"):]
    assert "<style>body{color:red}</style>" in enriched
    with pytest.raises(KeyError):
        search_metadata(original, "guide/new-page.html")
