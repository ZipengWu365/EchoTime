"""Build the cited reading pages from their Markdown sources, without network I/O.

The generated files are bundled with the wheel so ``echotime --export-pages``
also works outside a source checkout. Markdown is a documentation-build extra,
not a new dependency of the numerical package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import shutil
from html import escape, unescape
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src" / "echotime" / "data" / "knowledge"
REPOSITORY = "https://github.com/ZipengWu365/EchoTime/blob/main/"
SITE_PREFIX = "/EchoTime/"
FIXED_PAGES = {
    "docs/articles/README.md": ("articles/index.html", "en"),
    "docs/references/time-series-similarity-literature.md": (
        "references/time-series-similarity-literature.html", "en"
    ),
}
ARTICLE_INDEX_MARKER = "<!-- echotime:article-index -->"


def _metadata_value(metadata: dict[str, list[str]], name: str) -> str:
    value = " ".join(metadata.get(name, [])).strip()
    # Markdown's metadata extension retains YAML-style surrounding quotes.
    if len(value) > 1 and value[0] == value[-1] and value[0] in {"\"", "'"}:
        value = value[1:-1]
    return value


def article_details(source: str) -> dict[str, str]:
    text = (ROOT / source).read_text(encoding="utf-8")
    reader = markdown.Markdown(extensions=["meta"])
    body = reader.convert(text)
    heading = re.search(r"^# (.+)$", text, re.M)
    if not heading:
        raise ValueError(f"Missing article heading: {source}")
    title = _metadata_value(reader.Meta, "title") or heading[1].strip()
    language = _metadata_value(reader.Meta, "lang") or _metadata_value(reader.Meta, "language")
    if not language:
        stem = Path(source).stem.lower()
        if stem.endswith((".zh-cn", ".zh", "_zh")):
            language = "zh-CN"
        elif stem.endswith(".en"):
            language = "en"
        else:
            cjk = len(re.findall(r"[\u3400-\u9fff]", heading[1]))
            latin = len(re.findall(r"[A-Za-z]", heading[1]))
            language = "zh-CN" if cjk > latin else "en"
    if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", language):
        raise ValueError(f"Invalid article language in {source}: {language}")
    summary = _metadata_value(reader.Meta, "description")
    if not summary:
        first_paragraph = re.search(r"<p>(.*?)</p>", body, re.S)
        summary = unescape(re.sub(r"<[^>]+>", "", first_paragraph[1])) if first_paragraph else title
        summary = " ".join(summary.split())
        if len(summary) > 240:
            summary = summary[:237].rsplit(" ", 1)[0] + "…"
    return {"title": title, "language": language, "description": summary}


def discover_pages() -> dict[str, tuple[str, str]]:
    """Publish article Markdown automatically, retaining its filename in the URL."""
    pages = dict(FIXED_PAGES)
    for path in sorted((ROOT / "docs" / "articles").glob("*.md")):
        name = path.name.lower()
        if (name in {"readme.md", "index.md"} or name.startswith(("_", ".", "draft", "internal"))
                or ".draft." in name):
            continue
        source = path.relative_to(ROOT).as_posix()
        details = article_details(source)
        pages[source] = ("articles/" + path.with_suffix(".html").name, details["language"])
    return pages

DOWNLOADS = (
    "docs/references/time-series-similarity-literature.json",
    "docs/references/time-series-similarity-literature.bib",
)

STYLE = """
:root { color-scheme:light; --ink:#172336; --muted:#53647b; --blue:#235bcc; }
* { box-sizing:border-box; } body { margin:0; color:var(--ink); background:#f5f7fb;
font:17px/1.75 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
main { width:min(1080px,calc(100% - 32px)); margin:32px auto; padding:36px 48px;
background:white; border:1px solid #dce3ef; border-radius:16px; }
nav { display:flex; flex-wrap:wrap; gap:10px 24px; padding-bottom:20px;
border-bottom:1px solid #dce3ef; font-size:14px; } a { color:var(--blue); }
h1 { font-size:clamp(28px,4vw,42px); line-height:1.2; letter-spacing:-.025em; }
h2 { margin-top:2.1em; line-height:1.3; } h3 { line-height:1.4; }
table { display:block; width:100%; overflow-x:auto; border-collapse:collapse;
font-size:15px; line-height:1.55; } th,td { padding:12px; min-width:140px;
text-align:left; vertical-align:top; border:1px solid #dce3ef; }
th { background:#edf2fc; } code { font-size:.88em; background:#f1f4fa;
padding:2px 4px; border-radius:3px; } pre { overflow-x:auto; padding:18px;
background:#f1f4fa; border-left:3px solid var(--blue); } pre code { padding:0; }
img { max-width:100%; height:auto; } blockquote { margin-left:0; padding:8px 20px;
border-left:3px solid #d9b84c; background:#fffbef; }
.source { color:var(--muted); font-size:14px; } :target { scroll-margin-top:24px; }
@media(max-width:640px) { main { margin:12px auto; padding:22px 18px; }
body { font-size:16px; } th,td { min-width:150px; } }
"""


def _output_path(source: str, pages: dict[str, tuple[str, str]] | None = None) -> str:
    pages = pages if pages is not None else discover_pages()
    return pages[source][0] if source in pages else source.removeprefix("docs/")


def _rewrite_link(value: str, source: str, destination: str, *, image: bool = False,
                  pages: dict[str, tuple[str, str]] | None = None) -> str:
    parsed = urlsplit(value)
    if (parsed.netloc == "zipengwu.me" and parsed.scheme in {"http", "https"}
            and parsed.path.startswith(SITE_PREFIX)):
        # Keep versioned site links and images inside a locally exported bundle.
        target = parsed.path.removeprefix(SITE_PREFIX)
        if not target or target.endswith("/"):
            target += "index.html"
        path = posixpath.relpath(target, posixpath.dirname(destination))
        return urlunsplit(("", "", path, parsed.query, parsed.fragment))
    if parsed.scheme or parsed.netloc or not parsed.path:
        return value
    resolved = (ROOT / source).parent.joinpath(parsed.path).resolve()
    try:
        target = resolved.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise ValueError(f"Link leaves repository in {source}: {value}") from exc
    if not resolved.exists():
        raise ValueError(f"Missing local link target in {source}: {value}")
    pages = pages if pages is not None else discover_pages()
    if target in pages or target in DOWNLOADS:
        path = posixpath.relpath(_output_path(target, pages), posixpath.dirname(destination))
    else:
        path = ("https://raw.githubusercontent.com/ZipengWu365/EchoTime/main/" if image else REPOSITORY) + target
    return urlunsplit(("", "", path, parsed.query, parsed.fragment))


class _Links(Treeprocessor):
    def __init__(self, md: markdown.Markdown, source: str, destination: str,
                 pages: dict[str, tuple[str, str]]) -> None:
        super().__init__(md)
        self.source = source
        self.destination = destination
        self.pages = pages

    def run(self, root):
        for element in root.iter():
            for attribute in ("href", "src"):
                if attribute in element.attrib:
                    element.set(attribute, _rewrite_link(
                        element.attrib[attribute], self.source, self.destination, image=attribute == "src",
                        pages=self.pages
                    ))
        return root


class _LinkExtension(Extension):
    def __init__(self, source: str, destination: str, pages: dict[str, tuple[str, str]]) -> None:
        self.source = source
        self.destination = destination
        self.pages = pages
        super().__init__()

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        md.treeprocessors.register(_Links(md, self.source, self.destination, self.pages), "repo_links", 1)


def _render(source: str, destination: str, language: str,
            pages: dict[str, tuple[str, str]] | None = None) -> str:
    pages = pages if pages is not None else discover_pages()
    text = (ROOT / source).read_text(encoding="utf-8")
    details = article_details(source)
    title = details["title"]
    if source == "docs/articles/README.md":
        rows = []
        for article, (target, article_language) in pages.items():
            if not article.startswith("docs/articles/") or article.endswith("/README.md"):
                continue
            article_title = article_details(article)["title"]
            rows.append(f"- [{article_title}]({Path(article).name}) · {article_language}")
        if ARTICLE_INDEX_MARKER not in text:
            raise ValueError("Article index needs its automatic catalog marker")
        text = text.replace(ARTICLE_INDEX_MARKER, "\n".join(rows))
    body = markdown.markdown(text, extensions=[
        "meta", "tables", "fenced_code", "toc", "footnotes", _LinkExtension(source, destination, pages)
    ], output_format="html")
    return f"""<!doctype html>
<html lang="{language}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | EchoTime</title><meta name="description" content="{escape(details['description'], quote=True)}"><style>{STYLE}</style></head>
<body><main>
<nav aria-label="Reading navigation"><a href="../index.html">EchoTime</a>
<a href="../articles/index.html">Reading guide</a>
<a href="../articles/time-series-similarity-guide.en.html" lang="en">English</a>
<a href="../articles/time-series-similarity-guide.zh-CN.html" lang="zh-CN">中文</a>
<a href="../articles/what-time-series-similarity-measures.en.html">Mechanism tour</a>
<a href="../guide/similarity-lab.html">Interactive lab</a>
<a href="../references/time-series-similarity-literature.html">Paper index</a>
<a href="https://github.com/ZipengWu365/EchoTime/discussions">Discuss the methods</a></nav>
<nav aria-label="Zipeng Wu projects" style="padding:12px 0;font-size:13px;gap:8px 20px;">
<a href="https://zipengwu.me/">Zipeng Wu</a>
<a href="https://zipengwu.me/software.html">Projects</a>
<a href="https://zipengwu.me/articles/">All articles</a>
<a href="https://zipengwu.me/detime/">DeTime</a>
<a href="https://zipengwu.me/tomc/">TOMC Memory</a></nav>
{body}
<hr><p class="source">Built from <a href="{REPOSITORY}{source}">the versioned Markdown source</a>.
Share questions, corrections and reproducible examples in
<a href="https://github.com/ZipengWu365/EchoTime/discussions">GitHub Discussions</a>.</p>
</main></body></html>
"""


def expected_bundle() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    pages = discover_pages()
    for source, (destination, language) in pages.items():
        files[destination] = _render(source, destination, language, pages).encode("utf-8")
    for source in DOWNLOADS:
        files[_output_path(source, pages)] = (ROOT / source).read_bytes()
    sources = list(pages) + list(DOWNLOADS)
    manifest = {
        "description": "Generated reading pages; edit the Markdown/JSON/BibTeX sources.",
        "sources": {source: hashlib.sha256((ROOT / source).read_bytes()).hexdigest()
                    for source in sources},
        "articles": [{"source": source, "path": destination, **article_details(source)}
                     for source, (destination, _) in pages.items()
                     if source.startswith("docs/articles/") and not source.endswith("/README.md")],
    }
    files["manifest/knowledge_sources.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    catalog = {"articles": [{key: value for key, value in item.items() if key != "source"}
                            for item in manifest["articles"]]}
    files["articles/catalog.json"] = (json.dumps(catalog, indent=2, ensure_ascii=False) + "\n").encode()
    return files


def build_knowledge_pages(*, check: bool = False) -> list[str]:
    files = expected_bundle()
    if check:
        stale = [name for name, content in files.items()
                 if not (BUNDLE / name).is_file() or (BUNDLE / name).read_bytes() != content]
        extra = [p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob("*")
                 if p.is_file() and p.relative_to(BUNDLE).as_posix() not in files]
        if stale or extra:
            raise SystemExit("Stale reading bundle; run python tools/build_knowledge_pages.py: "
                             + ", ".join(stale + extra))
    else:
        # This directory contains only generated artifacts, never authoring sources.
        if BUNDLE.exists():
            shutil.rmtree(BUNDLE)
        for name, content in files.items():
            target = BUNDLE / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    return list(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if bundled files are stale")
    args = parser.parse_args()
    names = build_knowledge_pages(check=args.check)
    print(f"Reading bundle {'verified' if args.check else 'built'}: {len(names)} files")


if __name__ == "__main__":
    main()
