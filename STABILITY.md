# Stability and release notes

**stage:** Beta

v0.17.0 focuses on cross-platform reliability and first-minute product polish:

- CLI output now degrades safely on non-UTF-8 consoles instead of failing on HTML-heavy guides.
- `python -m echotime.demo_server --help` no longer triggers the previous runpy warning path.
- `start-here.html` unifies static preview, local live demo, one-line quickstart, environment doctor, and Pages export.
- `echotime --export-pages docs` writes a GitHub-Pages-ready bundle with `index.html`, `start-here.html`, `playground.html`, flagship reports, social cards, and `404.html`.
- Agent contracts stay Beta-level and versioned at schema `2.4.0`.
