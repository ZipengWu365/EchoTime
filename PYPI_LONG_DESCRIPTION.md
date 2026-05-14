# EchoTime

**Explainable time-series similarity for humans and agents.**

[![PyPI version](https://img.shields.io/pypi/v/echotime?style=flat-square)](https://pypi.org/project/echotime/)
[![Python versions](https://img.shields.io/pypi/pyversions/echotime?style=flat-square)](https://pypi.org/project/echotime/)
[![License: MIT](https://img.shields.io/badge/license-MIT-ffc83d?style=flat-square)](LICENSE)
[![Status: Beta](https://img.shields.io/badge/status-beta-2f6bff?style=flat-square)](https://github.com/ZipengWu365/EchoWave)
[![Docs: GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-2f6bff?style=flat-square)](https://zipengwu365.github.io/EchoWave/)

EchoTime compares time series and time-series datasets, explains why they match or differ, and emits compact JSON plus shareable HTML reports.

## Why this package exists

Most time-series tooling helps after you decide what to model. EchoTime helps one step earlier: compare two signals clearly, compare two datasets structurally, and emit a result that a human or an agent can actually act on.

## Quickstart

```bash
pip install echotime
python -c "import numpy as np; from echotime import compare_series; x=np.sin(np.linspace(0,8*np.pi,128)); y=np.sin(np.linspace(0,8*np.pi,128)+0.2); print(compare_series(x,y).to_summary_card_markdown())"
```

Expected output starts like this:

```text
# EchoTime similarity summary
overall similarity: ...
top components: shape similarity, trend similarity, spectral similarity
```

## Use your own data

EchoTime is meant to run on real files, not just toy arrays.

- single numeric column -> `profile_series(...)`
- wide table with one `timestamp` column and one or more numeric columns -> `profile_dataset(df, domain=...)`
- irregular long table -> rename columns to `subject`, `timestamp`, `channel`, `value`, then call `profile_dataset(...)`
- two columns to compare -> `compare_series(df["left"], df["right"])`

Tabular inputs are auto-detected from names such as `timestamp` / `time`, `value` / `measurement`, `channel` / `sensor` / `metric`, and `subject` / `patient` / `participant`.

```python
from pathlib import Path

import pandas as pd
from echotime import profile_dataset

df = pd.read_csv("my_timeseries.csv").rename(columns={"date": "timestamp"})
profile = profile_dataset(df, domain="energy")
print(profile.to_summary_card_markdown())
Path("my_dataset_report.html").write_text(profile.to_html_report(), encoding="utf-8")
```


## What ships in v0.17.0

- compare-first public package surface
- agent-ready JSON wrappers with stable envelopes
- GitHub Pages-ready docs bundle
- local live demo for pasted arrays
- starter datasets, notebooks, and flagship demos
- compatibility presets and environment doctor guidance for mixed scientific stacks

## Common entry points

- `echotime-demo --open-browser`
- `echotime --guide quickstart`
- `echotime --guide doctor`
- `echotime --export-pages docs`

## Links

- README: `README.md`
- Start here: `START_HERE.md`
- Compatibility: `COMPATIBILITY.md`
- Local live demo: `LIVE_DEMO.md`
- Agent input contract: `AGENT_INPUT_CONTRACT.md`

## Maintainer

- **Zipeng Wu**
- The University of Birmingham
- zxw365@student.bham.ac.uk
- https://github.com/ZipengWu365/EchoWave
