"""Check that reading assets survive packaging and link to their actual targets."""

from __future__ import annotations

import json
import posixpath
import re
import importlib.util
from html.parser import HTMLParser
from pathlib import Path
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


@pytest.fixture
def article_builder(tmp_path, monkeypatch):
    pytest.importorskip("markdown")
    spec = importlib.util.spec_from_file_location(
        "echotime_article_builder", Path(__file__).resolve().parents[1] / "tools" / "build_knowledge_pages.py"
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    articles = tmp_path / "docs" / "articles"
    articles.mkdir(parents=True)
    (articles / "README.md").write_text("# Articles\n\n<!-- echotime:article-index -->\n", encoding="utf-8")
    for name in ["time-series-similarity-guide.en", "time-series-similarity-guide.zh-CN", "what-time-series-similarity-measures.en"]:
        (articles / (name + ".md")).write_text(f"# {name}\n\nA retained article.\n", encoding="utf-8")
    references = tmp_path / "docs" / "references"
    references.mkdir()
    (references / "time-series-similarity-literature.md").write_text("# References\n\nPrimary references.\n", encoding="utf-8")
    for suffix in ["json", "bib"]:
        (references / ("time-series-similarity-literature." + suffix)).write_text("{}", encoding="utf-8")
    return builder, articles


def test_new_article_is_discovered_indexed_and_gets_canonical_metadata(article_builder):
    builder, articles = article_builder
    (articles / "new-method.en.md").write_text(
        '---\ntitle: "A new similarity method"\ndescription: "Inspect a newly documented alignment method."\nlang: en\n---\n\n'
        '# A new similarity method\n\nA new explanation. '
        '[Prior guide](time-series-similarity-guide.en.md).\n', encoding="utf-8"
    )
    (articles / "new-method.zh-CN.md").write_text("# 新的时序比较方法\n\n这是一篇新文章。\n", encoding="utf-8")
    for name in ["draft-plan.md", "_internal.md", "index.md"]:
        (articles / name).write_text("# Unpublished notes\n", encoding="utf-8")
    files = builder.expected_bundle()
    for name in ["time-series-similarity-guide.en", "time-series-similarity-guide.zh-CN", "what-time-series-similarity-measures.en"]:
        assert f"articles/{name}.html" in files
    assert 'new-method.en.html' in files["articles/index.html"].decode()
    assert 'new-method.zh-CN.html' in files["articles/index.html"].decode()
    assert "articles/draft-plan.html" not in files
    assert "articles/_internal.html" not in files
    path = "articles/new-method.en.html"
    page = search_metadata(files[path].decode(), path)
    assert 'href="time-series-similarity-guide.en.html"' in page
    assert 'href="https://zipengwu.me/EchoTime/articles/new-method.en.html"' in page
    assert page.count('name="description"') == 1
    assert 'content="Inspect a newly documented alignment method."' in page
    assert search_metadata(page, path) == page
    from echotime.seo import enrich_pages_bundle
    bundle = enrich_pages_bundle({path: files[path].decode()})
    assert "https://zipengwu.me/EchoTime/articles/new-method.en.html" in bundle["sitemap.xml"]
    manifest = json.loads(files["manifest/knowledge_sources.json"])
    record = next(row for row in manifest["articles"] if row["path"] == "articles/new-method.zh-CN.html")
    assert record["language"] == "zh-CN"
    assert record["source"] == "docs/articles/new-method.zh-CN.md"
    catalog = json.loads(files["articles/catalog.json"])
    published = next(row for row in catalog["articles"] if row["path"] == "articles/new-method.en.html")
    assert published == {
        "path": "articles/new-method.en.html", "title": "A new similarity method",
        "language": "en", "description": "Inspect a newly documented alignment method.",
    }


def test_article_update_and_relative_image_are_reflected_without_registry_edit(article_builder):
    builder, articles = article_builder
    (articles / "example.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    source = articles / "recent.en.md"
    source.write_text("# First title\n\nFirst explanation.\n\n![Plot](example.svg)\n", encoding="utf-8")
    first = builder.expected_bundle()["articles/recent.en.html"].decode()
    assert "https://raw.githubusercontent.com/ZipengWu365/EchoTime/main/docs/articles/example.svg" in first
    source.write_text("# Updated title\n\nUpdated explanation.\n", encoding="utf-8")
    updated = builder.expected_bundle()["articles/recent.en.html"].decode()
    assert "<title>Updated title | EchoTime</title>" in updated
    assert 'content="Updated explanation."' in updated
