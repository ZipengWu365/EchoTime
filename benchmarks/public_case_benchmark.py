"""Cross-domain showcase benchmark for bundled public-style cases.

This is still a product benchmark, not a publication benchmark. The purpose is
more concrete than the synthetic decision-impact story: show that tsontology can
produce stable, low-latency artifacts across heterogeneous shipped cases.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from tsontology import compare_series, profile_dataset

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples" / "data"
RESULTS = ROOT / "benchmarks" / "results"


def run() -> dict:
    cases = []

    df = pd.read_csv(DATA / "single_sensor_drift.csv")
    prof = profile_dataset(df["value"].to_numpy(), domain="engineering")
    cases.append({
        "case": "single_sensor_drift",
        "mode": "profile",
        "headline": prof.to_summary_card_markdown().splitlines()[1],
        "top_axes": prof.metadata.get("dominant_axes", ""),
        "ok": True,
    })

    df = pd.read_csv(DATA / "inflation_search_interest.csv")
    rep = compare_series(df["inflation"].to_numpy(), df["search_interest"].to_numpy(), left_name="inflation", right_name="search_interest")
    cases.append({
        "case": "inflation_search_interest",
        "mode": "compare",
        "headline": rep.interpretation,
        "similarity": float(rep.similarity_score),
        "ok": True,
    })

    df = pd.read_csv(DATA / "industrial_sensor_network.csv")
    prof = profile_dataset(df[["sensor_a", "sensor_b", "sensor_c"]].to_numpy(), domain="industrial")
    cases.append({
        "case": "industrial_sensor_network",
        "mode": "profile",
        "headline": prof.to_summary_card_markdown().splitlines()[1],
        "top_axes": prof.metadata.get("dominant_axes", ""),
        "ok": True,
    })

    return {
        "version": "0.17.0",
        "summary": "tsontology produced stable profile/compare artifacts across shipped cross-domain CSV cases.",
        "cases": cases,
        "n_cases": len(cases),
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    payload = run()
    (RESULTS / "public_case_benchmark.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# Public-style showcase benchmark", "", payload["summary"], ""]
    for case in payload["cases"]:
        lines.append(f"- {case['case']}: {case['headline']}")
    (RESULTS / "public_case_benchmark.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
