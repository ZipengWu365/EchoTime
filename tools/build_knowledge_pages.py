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
import shutil
from html import escape
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src" / "echotime" / "data" / "knowledge"
REPOSITORY = "https://github.com/ZipengWu365/EchoTime/blob/main/"
PAGES = {
    "docs/articles/README.md": ("articles/index.html", "en"),
    "docs/articles/time-series-similarity-guide.en.md": (
        "articles/time-series-similarity-guide.en.html", "en"
    ),
    "docs/articles/time-series-similarity-guide.zh-CN.md": (
        "articles/time-series-similarity-guide.zh-CN.html", "zh-CN"
    ),
    "docs/references/time-series-similarity-literature.md": (
        "references/time-series-similarity-literature.html", "en"
    ),
}
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


def _output_path(source: str) -> str:
    return PAGES[source][0] if source in PAGES else source.removeprefix("docs/")


def _rewrite_link(value: str, source: str, destination: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return value
    resolved = (ROOT / source).parent.joinpath(parsed.path).resolve()
    try:
        target = resolved.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise ValueError(f"Link leaves repository in {source}: {value}") from exc
    if not resolved.exists():
        raise ValueError(f"Missing local link target in {source}: {value}")
    if target in PAGES or target in DOWNLOADS:
        path = posixpath.relpath(_output_path(target), posixpath.dirname(destination))
    else:
        path = REPOSITORY + target
    return urlunsplit(("", "", path, parsed.query, parsed.fragment))


class _Links(Treeprocessor):
    def __init__(self, md: markdown.Markdown, source: str, destination: str) -> None:
        super().__init__(md)
        self.source = source
        self.destination = destination

    def run(self, root):
        for element in root.iter():
            for attribute in ("href", "src"):
                if attribute in element.attrib:
                    element.set(attribute, _rewrite_link(
                        element.attrib[attribute], self.source, self.destination
                    ))
        return root


class _LinkExtension(Extension):
    def __init__(self, source: str, destination: str) -> None:
        self.source = source
        self.destination = destination
        super().__init__()

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        md.treeprocessors.register(_Links(md, self.source, self.destination), "repo_links", 1)


def _render(source: str, destination: str, language: str) -> str:
    text = (ROOT / source).read_text(encoding="utf-8")
    title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), "")
    if not title:
        raise ValueError(f"Missing article heading: {source}")
    body = markdown.markdown(text, extensions=[
        "tables", "fenced_code", "toc", "footnotes", _LinkExtension(source, destination)
    ], output_format="html")
    return f"""<!doctype html>
<html lang="{language}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | EchoTime</title><style>{STYLE}</style></head>
<body><main>
<nav aria-label="Reading navigation"><a href="../index.html">EchoTime</a>
<a href="../articles/index.html">Reading guide</a>
<a href="../articles/time-series-similarity-guide.en.html" lang="en">English</a>
<a href="../articles/time-series-similarity-guide.zh-CN.html" lang="zh-CN">中文</a>
<a href="../references/time-series-similarity-literature.html">Paper index</a></nav>
{body}
<hr><p class="source">Built from <a href="{REPOSITORY}{source}">the versioned Markdown source</a>.
Corrections and reproducible examples are welcome in the repository.</p>
</main></body></html>
"""


def expected_bundle() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for source, (destination, language) in PAGES.items():
        files[destination] = _render(source, destination, language).encode("utf-8")
    for source in DOWNLOADS:
        files[_output_path(source)] = (ROOT / source).read_bytes()
    sources = list(PAGES) + list(DOWNLOADS)
    manifest = {
        "description": "Generated reading pages; edit the Markdown/JSON/BibTeX sources.",
        "sources": {source: hashlib.sha256((ROOT / source).read_bytes()).hexdigest()
                    for source in sources},
    }
    files["manifest/knowledge_sources.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
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
