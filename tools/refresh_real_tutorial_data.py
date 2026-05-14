from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "examples" / "data"
USER_AGENT = "EchoTimeDocs/0.17 (+https://github.com/ZipengWu365/EchoWave)"


def _request_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8")


def _request_json(url: str) -> object:
    return json.loads(_request_text(url))


def _fetch_fred_series(series_id: str, start: str, end: str) -> dict[str, float]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start}&coed={end}"
    text = _request_text(url)
    out: dict[str, float] = {}
    for row in csv.DictReader(text.splitlines()):
        value = row.get(series_id)
        if not value or value == ".":
            continue
        out[row["observation_date"]] = float(value)
    return out


def _fetch_wikimedia_views(article: str, start: str, end: str) -> list[dict[str, object]]:
    safe_article = quote(article, safe="()_")
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia.org/all-access/user/{safe_article}/daily/{start}/{end}"
    )
    payload = _request_json(url)
    assert isinstance(payload, dict)
    items = payload["items"]
    assert isinstance(items, list)
    return [dict(item) for item in items]


def _fetch_usgs_events(
    *,
    region: str,
    start: str,
    end: str,
    min_magnitude: float,
    min_latitude: float,
    max_latitude: float,
    min_longitude: float,
    max_longitude: float,
) -> list[dict[str, object]]:
    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?"
        f"format=geojson&starttime={start}&endtime={end}&minmagnitude={min_magnitude}"
        f"&minlatitude={min_latitude}&maxlatitude={max_latitude}"
        f"&minlongitude={min_longitude}&maxlongitude={max_longitude}"
    )
    payload = _request_json(url)
    assert isinstance(payload, dict)
    features = payload["features"]
    assert isinstance(features, list)
    rows: list[dict[str, object]] = []
    for feature in features:
        props = feature["properties"]
        timestamp_ms = int(props["time"])
        dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
        rows.append(
            {
                "timestamp": dt.isoformat().replace("+00:00", "Z"),
                "date": dt.date().isoformat(),
                "region": region,
                "magnitude": float(props["mag"]),
                "place": str(props["place"]),
                "detail_url": str(props["url"]),
            }
        )
    rows.sort(key=lambda item: str(item["timestamp"]))
    return rows


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def refresh_treasury_yields() -> dict[str, object]:
    left = _fetch_fred_series("DGS10", "2024-01-01", "2024-12-31")
    right = _fetch_fred_series("DGS2", "2024-01-01", "2024-12-31")
    dates = sorted(set(left) & set(right))
    rows = [{"date": day, "dgs10": left[day], "dgs2": right[day]} for day in dates]
    _write_csv(DATA_DIR / "real_treasury_yields_2024.csv", ["date", "dgs10", "dgs2"], rows)
    return {
        "path": "examples/data/real_treasury_yields_2024.csv",
        "source_name": "FRED",
        "source_url": "https://fred.stlouisfed.org/graph/?g=1Ht6O",
    }


def refresh_python_javascript_pageviews() -> dict[str, object]:
    python_views = _fetch_wikimedia_views("Python_(programming_language)", "20240101", "20241231")
    javascript_views = _fetch_wikimedia_views("JavaScript", "20240101", "20241231")
    js_by_day = {str(item["timestamp"])[:8]: int(item["views"]) for item in javascript_views}
    rows = []
    for item in python_views:
        stamp = str(item["timestamp"])
        day = stamp[:8]
        if day not in js_by_day:
            continue
        rows.append(
            {
                "date": f"{day[:4]}-{day[4:6]}-{day[6:8]}",
                "python_views": int(item["views"]),
                "javascript_views": js_by_day[day],
            }
        )
    _write_csv(
        DATA_DIR / "real_python_javascript_pageviews_2024.csv",
        ["date", "python_views", "javascript_views"],
        rows,
    )
    return {
        "path": "examples/data/real_python_javascript_pageviews_2024.csv",
        "source_name": "Wikimedia Pageviews API",
        "source_url": "https://wikimedia.org/api/rest_v1/#/Pageviews%20data",
    }


def refresh_ai_attention_breakouts() -> dict[str, object]:
    deepseek = _fetch_wikimedia_views("DeepSeek", "20250115", "20250414")
    chatgpt = _fetch_wikimedia_views("ChatGPT", "20221130", "20230227")
    threads = _fetch_wikimedia_views("Threads_(social_network)", "20230705", "20230930")

    n = min(len(deepseek), len(chatgpt), len(threads))
    deepseek = deepseek[:n]
    chatgpt = chatgpt[:n]
    threads = threads[:n]

    cum_deepseek = 0
    cum_chatgpt = 0
    cum_threads = 0
    rows: list[dict[str, object]] = []
    for day in range(n):
        deepseek_daily = int(deepseek[day]["views"])
        chatgpt_daily = int(chatgpt[day]["views"])
        threads_daily = int(threads[day]["views"])
        cum_deepseek += deepseek_daily
        cum_chatgpt += chatgpt_daily
        cum_threads += threads_daily
        rows.append(
            {
                "day": day,
                "deepseek_daily": deepseek_daily,
                "chatgpt_daily": chatgpt_daily,
                "threads_daily": threads_daily,
                "deepseek_cumulative": cum_deepseek,
                "chatgpt_cumulative": cum_chatgpt,
                "threads_cumulative": cum_threads,
            }
        )
    _write_csv(
        DATA_DIR / "real_ai_attention_breakouts.csv",
        [
            "day",
            "deepseek_daily",
            "chatgpt_daily",
            "threads_daily",
            "deepseek_cumulative",
            "chatgpt_cumulative",
            "threads_cumulative",
        ],
        rows,
    )
    return {
        "path": "examples/data/real_ai_attention_breakouts.csv",
        "source_name": "Wikimedia Pageviews API",
        "source_url": "https://wikimedia.org/api/rest_v1/#/Pageviews%20data",
    }


def refresh_usgs_earthquakes() -> dict[str, object]:
    california = _fetch_usgs_events(
        region="California",
        start="2024-01-01",
        end="2024-06-30",
        min_magnitude=2.5,
        min_latitude=32.0,
        max_latitude=42.0,
        min_longitude=-125.0,
        max_longitude=-114.0,
    )
    alaska = _fetch_usgs_events(
        region="Alaska",
        start="2024-01-01",
        end="2024-06-30",
        min_magnitude=2.5,
        min_latitude=51.0,
        max_latitude=72.0,
        min_longitude=-170.0,
        max_longitude=-130.0,
    )
    rows = california + alaska
    rows.sort(key=lambda item: (str(item["timestamp"]), str(item["region"])))
    _write_csv(
        DATA_DIR / "real_usgs_earthquakes_ca_ak_2024.csv",
        ["timestamp", "date", "region", "magnitude", "place", "detail_url"],
        rows,
    )
    return {
        "path": "examples/data/real_usgs_earthquakes_ca_ak_2024.csv",
        "source_name": "USGS Earthquake Catalog",
        "source_url": "https://earthquake.usgs.gov/fdsnws/event/1/",
    }


def refresh_btc_oil_vix() -> dict[str, object]:
    btc = _fetch_fred_series("CBBTCUSD", "2024-01-01", "2024-12-31")
    oil = _fetch_fred_series("DCOILBRENTEU", "2024-01-01", "2024-12-31")
    vix = _fetch_fred_series("VIXCLS", "2024-01-01", "2024-12-31")
    dates = sorted(set(btc) & set(oil) & set(vix))
    rows = [{"date": day, "btc_usd": btc[day], "brent_usd": oil[day], "vix": vix[day]} for day in dates]
    _write_csv(DATA_DIR / "real_btc_oil_vix_2024.csv", ["date", "btc_usd", "brent_usd", "vix"], rows)
    return {
        "path": "examples/data/real_btc_oil_vix_2024.csv",
        "source_name": "FRED",
        "source_url": "https://fred.stlouisfed.org/",
    }


def refresh_heatwave_city_temps() -> dict[str, object]:
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        "latitude=33.45,36.17&longitude=-112.07,-115.14"
        "&start_date=2024-07-01&end_date=2024-08-31"
        "&daily=temperature_2m_max&timezone=UTC"
    )
    payload = _request_json(url)
    assert isinstance(payload, list) and len(payload) == 2
    phoenix = payload[0]["daily"]
    vegas = payload[1]["daily"]
    rows = [
        {
            "date": day,
            "phoenix_temp_max": phoenix["temperature_2m_max"][idx],
            "las_vegas_temp_max": vegas["temperature_2m_max"][idx],
        }
        for idx, day in enumerate(phoenix["time"])
    ]
    _write_csv(
        DATA_DIR / "real_heatwave_city_temps_2024.csv",
        ["date", "phoenix_temp_max", "las_vegas_temp_max"],
        rows,
    )
    return {
        "path": "examples/data/real_heatwave_city_temps_2024.csv",
        "source_name": "Open-Meteo archive API",
        "source_url": "https://open-meteo.com/en/docs/historical-weather-api",
    }


def refresh_source_manifest(entries: list[dict[str, object]]) -> None:
    manifest = {
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "sources": entries,
    }
    path = DATA_DIR / "real_example_sources.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    entries = [
        refresh_treasury_yields(),
        refresh_python_javascript_pageviews(),
        refresh_ai_attention_breakouts(),
        refresh_usgs_earthquakes(),
        refresh_btc_oil_vix(),
        refresh_heatwave_city_temps(),
    ]
    refresh_source_manifest(entries)
    print("real tutorial data refreshed")


if __name__ == "__main__":
    main()
