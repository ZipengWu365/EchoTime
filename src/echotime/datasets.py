
"""Starter datasets and runnable demo generators for echotime.

These are intentionally small, dependency-light datasets that make the first
minute with the package concrete. They are not marketed as benchmark-quality
real-world corpora; they are starter datasets for examples, notebooks, and
GitHub demos.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from .adapters import IrregularSubjectInput, IrregularTimeSeriesInput


_STARTER_INFO = {
    "sine_vs_noise": {
        "title": "Sine vs noise",
        "kind": "comparison",
        "domain": "generic",
        "why": "The smallest possible demo for rhythmicity and predictability.",
    },
    "weekly_website_traffic": {
        "title": "Weekly website traffic",
        "kind": "dataset",
        "domain": "traffic",
        "why": "A product-style dataset with weekly rhythm, trend, and launch bursts.",
    },
    "irregular_patient_vitals": {
        "title": "Irregular patient vitals",
        "kind": "dataset",
        "domain": "clinical",
        "why": "A minimal irregularly sampled clinical-monitoring cohort.",
    },
    "github_breakout_analogs": {
        "title": "GitHub breakout analogs",
        "kind": "comparison",
        "domain": "product",
        "why": "A social-friendly stars-over-time demo for similarity analysis.",
    },
    "btc_gold_oil_shocks": {
        "title": "BTC / gold / oil under shocks",
        "kind": "comparison",
        "domain": "markets",
        "why": "A regime-aware market comparison demo.",
    },
    "energy_load_heatwave": {
        "title": "Grid load vs heatwave",
        "kind": "dataset",
        "domain": "energy",
        "why": "A small multivariate energy system demo with heatwave-driven shifts.",
    },
    "wearable_recovery_cohort": {
        "title": "Wearable recovery cohort",
        "kind": "dataset",
        "domain": "wearable",
        "why": "A longitudinal cohort demo for heterogeneity and adherence.",
    },
}


def _rng(seed: int | None = None) -> np.random.Generator:
    return np.random.default_rng(seed or 0)


def _sine_vs_noise(seed: int = 0) -> dict[str, Any]:
    rng = _rng(seed)
    t = np.linspace(0, 8 * np.pi, 128)
    left = np.sin(t) + 0.05 * rng.normal(size=t.size)
    right = rng.normal(scale=0.9, size=t.size)
    return {
        "name": "sine_vs_noise",
        "left": left,
        "right": right,
        "timestamps": np.arange(t.size),
        "left_name": "sine",
        "right_name": "noise",
        "domain": "generic",
    }


def _weekly_website_traffic(seed: int = 0) -> dict[str, Any]:
    rng = _rng(seed)
    n = 84
    t = np.arange(n)
    weekly = 1.2 + 0.45 * np.sin(2 * np.pi * t / 7 - 1.2)
    trend = 0.015 * t
    burst = np.zeros(n)
    burst[28:33] += np.array([0.6, 1.2, 1.8, 1.1, 0.5])
    burst[56:60] += np.array([0.4, 0.9, 0.6, 0.2])
    sessions = 1000 * (weekly + trend + burst + 0.08 * rng.normal(size=n))
    weekly_lagged = np.roll(weekly, 2)
    weekly_lagged[0] = weekly_lagged[1]
    weekly_lagged[1] = weekly_lagged[2]
    burst_lagged = np.zeros(n)
    burst_lagged[30:36] += np.array([0.12, 0.34, 0.74, 0.58, 0.24, 0.06])
    burst_lagged[58:63] += np.array([0.08, 0.20, 0.34, 0.18, 0.05])
    weekday_bias = np.where((t % 7 >= 1) & (t % 7 <= 3), 0.18, -0.12)
    saturation_drag = np.zeros(n)
    saturation_drag[31:37] -= np.array([0.00, 0.08, 0.22, 0.24, 0.14, 0.04])
    saturation_drag[58:63] -= np.array([0.00, 0.05, 0.13, 0.09, 0.03])
    signups = 92 * (
        0.24 * weekly_lagged
        + 0.08 * trend
        + 0.92 * burst_lagged
        + weekday_bias
        + saturation_drag
        + 0.18 * np.sin(2 * np.pi * t / 11 + 0.9)
        + 0.09 * np.cos(2 * np.pi * t / 19 + 0.2)
        + 1.1
        + 0.26 * rng.normal(size=n)
    )
    values = np.column_stack([sessions, signups])
    return {
        "name": "weekly_website_traffic",
        "values": values,
        "timestamps": t,
        "channels": ["sessions", "signups"],
        "domain": "traffic",
    }


def _irregular_patient_vitals(seed: int = 0) -> dict[str, Any]:
    rng = _rng(seed)
    subjects = []
    rows = []
    for subj_idx in range(3):
        base_hr = 96 - 6 * subj_idx
        base_spo2 = 93 + subj_idx
        t_hr = np.cumsum(rng.uniform(0.3, 2.2, size=36))
        t_spo2 = np.cumsum(rng.uniform(0.5, 2.8, size=30))
        hr = base_hr - 0.6 * t_hr + 4 * np.sin(t_hr / 3.5) + rng.normal(scale=1.8, size=t_hr.size)
        spo2 = base_spo2 + 0.15 * t_spo2 + 0.8 * np.sin(t_spo2 / 6.0) + rng.normal(scale=0.5, size=t_spo2.size)
        subject = IrregularSubjectInput(values=[hr, spo2], timestamps=[t_hr, t_spo2], channel_names=["heart_rate", "spo2"], metadata={"subject_id": f"p{subj_idx+1}"})
        subjects.append(subject)
        for tt, vv in zip(t_hr, hr):
            rows.append({"subject": f"p{subj_idx+1}", "timestamp": float(tt), "channel": "heart_rate", "value": float(vv)})
        for tt, vv in zip(t_spo2, spo2):
            rows.append({"subject": f"p{subj_idx+1}", "timestamp": float(tt), "channel": "spo2", "value": float(vv)})
    payload = IrregularTimeSeriesInput(subjects=subjects, channel_names=["heart_rate", "spo2"], domain="clinical")
    return {
        "name": "irregular_patient_vitals",
        "values": payload,
        "rows": rows,
        "domain": "clinical",
    }


def _github_breakout_analogs(seed: int = 0) -> dict[str, Any]:
    rng = _rng(seed)
    n = 120
    t = np.arange(n)
    target_daily = 12 + 3 * np.sin(2 * np.pi * t / 14) + rng.normal(scale=1.2, size=n)
    target_daily += np.exp(-0.08 * np.maximum(0, t - 15)) * 40
    target_daily[t > 35] += 6 + 0.12 * (t[t > 35] - 35)
    hype_daily = 10 + 2 * np.sin(2 * np.pi * t / 10) + rng.normal(scale=1.8, size=n)
    hype_daily += np.exp(-0.12 * np.maximum(0, t - 12)) * 52
    hype_daily[t > 30] *= 0.55
    durable_daily = 9 + 1.5 * np.sin(2 * np.pi * t / 13) + rng.normal(scale=1.1, size=n)
    durable_daily += np.exp(-0.07 * np.maximum(0, t - 18)) * 35
    durable_daily[t > 40] += 7 + 0.18 * (t[t > 40] - 40)
    target = np.cumsum(np.clip(target_daily, 0.0, None))
    hype = np.cumsum(np.clip(hype_daily, 0.0, None))
    durable = np.cumsum(np.clip(durable_daily, 0.0, None))
    return {
        "name": "github_breakout_analogs",
        "target": target,
        "short_hype": hype,
        "durable_breakout": durable,
        "timestamps": t,
        "domain": "product",
    }


def _btc_gold_oil_shocks(seed: int = 0) -> dict[str, Any]:
    rng = _rng(seed)
    n = 180
    t = np.arange(n)
    shock = np.zeros(n)
    shock[60:68] = np.array([0.01, 0.018, 0.028, 0.02, 0.015, 0.01, 0.006, 0.003])
    shock[120:127] = np.array([-0.005, 0.012, 0.02, 0.015, 0.009, 0.004, 0.002])
    btc_ret = 0.001 + 0.012 * np.sin(2 * np.pi * t / 20) + 1.6 * shock + rng.normal(scale=0.018, size=n)
    gold_ret = 0.0007 + 0.004 * np.sin(2 * np.pi * t / 28) + 0.8 * shock + rng.normal(scale=0.007, size=n)
    oil_ret = 0.0005 + 0.009 * np.sin(2 * np.pi * t / 18) + 1.2 * shock + rng.normal(scale=0.012, size=n)
    btc = 100 * np.exp(np.cumsum(btc_ret))
    gold = 100 * np.exp(np.cumsum(gold_ret))
    oil = 100 * np.exp(np.cumsum(oil_ret))
    return {
        "name": "btc_gold_oil_shocks",
        "btc": btc,
        "gold": gold,
        "oil": oil,
        "timestamps": t,
        "domain": "markets",
    }


def _energy_load_heatwave(seed: int = 0) -> dict[str, Any]:
    rng = _rng(seed)
    n = 96
    t = np.arange(n)
    base = 50 + 7 * np.sin(2 * np.pi * t / 24 - 0.6)
    weekly = 2.5 * np.sin(2 * np.pi * t / (24 * 7))
    heat = np.zeros(n)
    heat[52:76] = np.linspace(0.0, 9.0, 24)
    temp = 24 + 5 * np.sin(2 * np.pi * t / 24 - 1.2) + heat + rng.normal(scale=0.8, size=n)
    load_north = base + weekly + 0.6 * heat + rng.normal(scale=1.0, size=n)
    load_south = 0.95 * base + weekly + 1.1 * heat + rng.normal(scale=1.1, size=n)
    values = np.column_stack([load_north, load_south, temp])
    return {
        "name": "energy_load_heatwave",
        "values": values,
        "timestamps": t,
        "channels": ["load_north", "load_south", "temperature"],
        "domain": "energy",
    }


def _wearable_recovery_cohort(seed: int = 0) -> dict[str, Any]:
    rng = _rng(seed)
    n_subjects = 6
    n_time = 60
    t = np.arange(n_time)
    subjects = []
    for i in range(n_subjects):
        recovery_speed = 0.035 + 0.01 * rng.normal()
        adherence = 0.9 - 0.08 * (i % 3)
        hr = 80 - 16 * (1 - np.exp(-recovery_speed * t)) + 1.8 * rng.normal(size=n_time)
        sleep = 6.2 + 1.1 * (1 - np.exp(-0.03 * t)) + 0.25 * rng.normal(size=n_time)
        steps = 2000 + 4500 * (1 - np.exp(-(0.025 + 0.008 * rng.normal()) * t)) + 250 * rng.normal(size=n_time)
        subj = np.column_stack([hr, sleep, steps])
        mask = rng.random(size=subj.shape) < adherence
        subj = np.where(mask, subj, np.nan)
        subjects.append(subj)
    values = np.stack(subjects, axis=0)
    return {
        "name": "wearable_recovery_cohort",
        "values": values,
        "timestamps": t,
        "channels": ["resting_hr", "sleep_hours", "steps"],
        "domain": "wearable",
    }


_GENERATORS = {
    "sine_vs_noise": _sine_vs_noise,
    "weekly_website_traffic": _weekly_website_traffic,
    "irregular_patient_vitals": _irregular_patient_vitals,
    "github_breakout_analogs": _github_breakout_analogs,
    "btc_gold_oil_shocks": _btc_gold_oil_shocks,
    "energy_load_heatwave": _energy_load_heatwave,
    "wearable_recovery_cohort": _wearable_recovery_cohort,
}


def list_starter_datasets() -> list[dict[str, Any]]:
    out = []
    for key, info in _STARTER_INFO.items():
        item = {"name": key}
        item.update(info)
        out.append(item)
    return out


def starter_dataset(name: str, *, seed: int = 0) -> dict[str, Any]:
    key = name.strip().lower()
    if key not in _GENERATORS:
        raise KeyError(f"Unknown starter dataset: {name}")
    return _GENERATORS[key](seed=seed)


def write_starter_dataset(name: str, path: str | Path, *, seed: int = 0) -> Path:
    payload = starter_dataset(name, seed=seed)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if name == "irregular_patient_vitals":
        rows = payload["rows"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["subject", "timestamp", "channel", "value"])
            writer.writeheader()
            writer.writerows(rows)
        return path
    if name in {"weekly_website_traffic", "energy_load_heatwave", "wearable_recovery_cohort"}:
        values = np.asarray(payload["values"], dtype=float)
        timestamps = np.asarray(payload["timestamps"], dtype=float).reshape(-1)
        channels = payload.get("channels") or [f"channel_{i+1}" for i in range(values.shape[-1])]
        if values.ndim == 3:
            # long-format export for cohorts
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["subject", "time", "channel", "value"])
                for s in range(values.shape[0]):
                    for ti, tt in enumerate(timestamps):
                        for ci, ch in enumerate(channels):
                            writer.writerow([f"subject_{s+1}", float(tt), ch, float(values[s, ti, ci])])
            return path
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", *channels])
            for i, tt in enumerate(timestamps):
                writer.writerow([float(tt), *map(float, values[i])])
        return path
    if name in {"sine_vs_noise", "github_breakout_analogs", "btc_gold_oil_shocks"}:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if name == "sine_vs_noise":
                writer.writerow(["time", "sine", "noise"])
                for tt, lv, rv in zip(payload["timestamps"], payload["left"], payload["right"]):
                    writer.writerow([float(tt), float(lv), float(rv)])
            elif name == "github_breakout_analogs":
                writer.writerow(["time", "target", "short_hype", "durable_breakout"])
                for row in zip(payload["timestamps"], payload["target"], payload["short_hype"], payload["durable_breakout"]):
                    writer.writerow([float(v) for v in row])
            else:
                writer.writerow(["time", "btc", "gold", "oil"])
                for row in zip(payload["timestamps"], payload["btc"], payload["gold"], payload["oil"]):
                    writer.writerow([float(v) for v in row])
        return path
    path.write_text(json.dumps(payload, default=lambda x: x.tolist() if hasattr(x, 'tolist') else str(x), indent=2), encoding="utf-8")
    return path
