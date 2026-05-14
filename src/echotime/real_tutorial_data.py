"""Load real public datasets used by the human-facing tutorial pages."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .runtime_paths import resolve_repo_subdir

DATA_DIR = resolve_repo_subdir("examples", "data", sentinel="real_example_sources.json")


def _read_csv_rows(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def treasury_yields_2024() -> dict[str, Any]:
    rows = _read_csv_rows("real_treasury_yields_2024.csv")
    dgs10 = np.asarray([float(row["dgs10"]) for row in rows], dtype=float)
    dgs2 = np.asarray([float(row["dgs2"]) for row in rows], dtype=float)
    return {
        "dates": [row["date"] for row in rows],
        "dgs10": dgs10,
        "dgs2": dgs2,
        "values": np.column_stack([dgs10, dgs2]),
        "channels": ["dgs10", "dgs2"],
        "local_csv": "examples/data/real_treasury_yields_2024.csv",
        "source_url": "https://fred.stlouisfed.org/graph/?g=1Ht6O",
    }


def python_javascript_pageviews_2024() -> dict[str, Any]:
    rows = _read_csv_rows("real_python_javascript_pageviews_2024.csv")
    python_views = np.asarray([float(row["python_views"]) for row in rows], dtype=float)
    javascript_views = np.asarray([float(row["javascript_views"]) for row in rows], dtype=float)
    return {
        "dates": [row["date"] for row in rows],
        "python_views": python_views,
        "javascript_views": javascript_views,
        "values": np.column_stack([python_views, javascript_views]),
        "channels": ["python_views", "javascript_views"],
        "local_csv": "examples/data/real_python_javascript_pageviews_2024.csv",
        "source_url": "https://wikimedia.org/api/rest_v1/#/Pageviews%20data",
    }


def ai_attention_breakouts() -> dict[str, Any]:
    rows = _read_csv_rows("real_ai_attention_breakouts.csv")
    return {
        "day": np.asarray([float(row["day"]) for row in rows], dtype=float),
        "deepseek_daily": np.asarray([float(row["deepseek_daily"]) for row in rows], dtype=float),
        "chatgpt_daily": np.asarray([float(row["chatgpt_daily"]) for row in rows], dtype=float),
        "threads_daily": np.asarray([float(row["threads_daily"]) for row in rows], dtype=float),
        "deepseek_cumulative": np.asarray([float(row["deepseek_cumulative"]) for row in rows], dtype=float),
        "chatgpt_cumulative": np.asarray([float(row["chatgpt_cumulative"]) for row in rows], dtype=float),
        "threads_cumulative": np.asarray([float(row["threads_cumulative"]) for row in rows], dtype=float),
        "local_csv": "examples/data/real_ai_attention_breakouts.csv",
        "source_url": "https://wikimedia.org/api/rest_v1/#/Pageviews%20data",
    }


def usgs_earthquakes_ca_ak_2024() -> dict[str, Any]:
    rows = _read_csv_rows("real_usgs_earthquakes_ca_ak_2024.csv")
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    event_records: list[dict[str, Any]] = []

    for row in rows:
        date_key = row["date"]
        region = row["region"]
        magnitude = float(row["magnitude"])
        grouped[region][date_key] += 1
        timestamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).timestamp()
        event_records.append(
            {
                "timestamp": timestamp,
                "subject": region,
                "value": magnitude,
                "event_type": "M4+" if magnitude >= 4.0 else "M2.5-4",
            }
        )

    dates = sorted({row["date"] for row in rows})
    california = np.asarray([grouped["California"].get(day, 0) for day in dates], dtype=float)
    alaska = np.asarray([grouped["Alaska"].get(day, 0) for day in dates], dtype=float)
    california_records = [record for record in event_records if record["subject"] == "California"]
    alaska_records = [record for record in event_records if record["subject"] == "Alaska"]
    return {
        "dates": dates,
        "california_counts": california,
        "alaska_counts": alaska,
        "count_values": np.column_stack([california, alaska]),
        "count_channels": ["california_counts", "alaska_counts"],
        "california_timestamps": np.asarray([float(record["timestamp"]) for record in california_records], dtype=float),
        "alaska_timestamps": np.asarray([float(record["timestamp"]) for record in alaska_records], dtype=float),
        "california_magnitudes": np.asarray([float(record["value"]) for record in california_records], dtype=float),
        "alaska_magnitudes": np.asarray([float(record["value"]) for record in alaska_records], dtype=float),
        "event_records": event_records,
        "local_csv": "examples/data/real_usgs_earthquakes_ca_ak_2024.csv",
        "source_url": "https://earthquake.usgs.gov/fdsnws/event/1/",
    }


def btc_oil_vix_2024() -> dict[str, Any]:
    rows = _read_csv_rows("real_btc_oil_vix_2024.csv")
    btc = np.asarray([float(row["btc_usd"]) for row in rows], dtype=float)
    brent = np.asarray([float(row["brent_usd"]) for row in rows], dtype=float)
    vix = np.asarray([float(row["vix"]) for row in rows], dtype=float)
    return {
        "dates": [row["date"] for row in rows],
        "btc_usd": btc,
        "brent_usd": brent,
        "vix": vix,
        "values": np.column_stack([btc, brent, vix]),
        "channels": ["btc_usd", "brent_usd", "vix"],
        "local_csv": "examples/data/real_btc_oil_vix_2024.csv",
        "source_url": "https://fred.stlouisfed.org/",
    }


def heatwave_city_temps_2024() -> dict[str, Any]:
    rows = _read_csv_rows("real_heatwave_city_temps_2024.csv")
    phoenix = np.asarray([float(row["phoenix_temp_max"]) for row in rows], dtype=float)
    vegas = np.asarray([float(row["las_vegas_temp_max"]) for row in rows], dtype=float)
    values = np.column_stack([phoenix, vegas])
    return {
        "dates": [row["date"] for row in rows],
        "phoenix_temp_max": phoenix,
        "las_vegas_temp_max": vegas,
        "values": values,
        "channels": ["phoenix_temp_max", "las_vegas_temp_max"],
        "local_csv": "examples/data/real_heatwave_city_temps_2024.csv",
        "source_url": "https://open-meteo.com/en/docs/historical-weather-api",
    }


__all__ = [
    "ai_attention_breakouts",
    "btc_oil_vix_2024",
    "heatwave_city_temps_2024",
    "python_javascript_pageviews_2024",
    "treasury_yields_2024",
    "usgs_earthquakes_ca_ak_2024",
]
