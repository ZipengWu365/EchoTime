"""Reference atlas for time-series similarity methods and EchoTime fit."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

GuideFormat = Literal["markdown", "dict"]


@dataclass(frozen=True, slots=True)
class EchoTimeNativeMethod:
    name: str
    family: str
    kind: str
    formula: str
    notes: str


@dataclass(frozen=True, slots=True)
class ExtractedMethod:
    name: str
    family: str
    kind: str
    metric: str
    complexity: str
    unequal_length: str
    multivariate: str
    implementation: str
    formula: str
    notes: str
    echotime_status: str
    echotime_rationale: str
    echotime_api: str


_FAMILY_ORDER = (
    "lock-step",
    "sliding",
    "elastic",
    "kernel",
    "feature-based",
    "model-based",
    "embedding",
)

_FAMILY_DESCRIPTIONS = {
    "lock-step": "Pointwise comparison on an already aligned timeline.",
    "sliding": "Shift-aware comparison under pure translation or lead-lag offsets.",
    "elastic": "Dynamic-programming alignments that allow local stretching or compression.",
    "kernel": "Similarity through kernel scores rather than direct distances.",
    "feature-based": "Compare derived features instead of raw waveforms.",
    "model-based": "Compare fitted dynamics or transition structure.",
    "embedding": "Encode first, then compare in a latent or compressed space.",
}

_DEFAULT_STATUS_BY_FAMILY = {
    "lock-step": (
        "Low-priority addition",
        "EchoTime already exposes familiar pointwise statistics, so adding more lock-step baselines is usually duplication rather than product leverage.",
        "",
    ),
    "sliding": (
        "Possible addition",
        "Shift-aware comparisons fit EchoTime's compare-first story, but EchoTime should only add the variants that remain clearly interpretable in reports.",
        "",
    ),
    "elastic": (
        "Possible addition",
        "Elastic methods are a strong thematic fit, but EchoTime should only add the variants that stay explainable for non-specialists.",
        "",
    ),
    "kernel": (
        "Low-priority addition",
        "Kernel scores can be useful downstream, but they are less legible than report-friendly distances or similarities.",
        "",
    ),
    "feature-based": (
        "Possible addition",
        "Feature-space methods can strengthen explainability when the representation itself is explicit and stable.",
        "",
    ),
    "model-based": (
        "Possible addition",
        "Model-based distances can be valuable for advanced users, but they depend on stronger modeling assumptions than EchoTime's current default surface.",
        "",
    ),
    "embedding": (
        "Low-priority addition",
        "Generic encoder adapters are flexible, but they are too open-ended for EchoTime's default public surface.",
        "",
    ),
}

_IMPLEMENTED_METHODS_BY_SOURCE_NAME = {
    "max_normalized_cross_correlation": "max_ncc",
    "sbd": "sbd",
    "independent_max_ncc": "independent_max_ncc",
    "independent_sbd": "independent_sbd",
    "acf_distance": "acf_distance",
    "periodogram_distance": "periodogram_distance",
    "trend_distance": "trend_distance",
    "ordinal_pattern_js_distance": "ordinal_pattern_js_distance",
    "linear_trend_model_distance": "linear_trend_model_distance",
    "lcss_similarity": "lcss_similarity",
    "lcss_distance": "lcss_distance",
    "edr": "edr_distance",
    "erp": "erp_distance",
    "twed": "twed_distance",
}

_STATUS_OVERRIDES = {
    "pearson_similarity": (
        "Conceptually covered",
        "EchoTime already surfaces Pearson r directly as a familiar reference metric.",
        "pearson_r",
    ),
    "pearson_distance": (
        "Conceptually covered",
        "EchoTime already exposes Pearson r, so the distance transform is trivial and does not need a separate public method.",
        "pearson_r",
    ),
    "spearman_similarity": (
        "Conceptually covered",
        "EchoTime already exposes Spearman rho directly as a rank-robust reference metric.",
        "spearman_rho",
    ),
    "spearman_distance": (
        "Conceptually covered",
        "EchoTime already exposes Spearman rho, so the distance transform is not worth a separate public method.",
        "spearman_rho",
    ),
    "kendall_similarity": (
        "Conceptually covered",
        "EchoTime already exposes Kendall tau directly as a rank-order agreement reference metric.",
        "kendall_tau",
    ),
    "kendall_distance": (
        "Conceptually covered",
        "EchoTime already exposes Kendall tau, so the distance transform is not worth a separate public method.",
        "kendall_tau",
    ),
    "dtw": (
        "Conceptually covered",
        "EchoTime already reports a constrained DTW-based similarity component.",
        "dtw_similarity",
    ),
    "cdtw": (
        "Conceptually covered",
        "EchoTime's DTW similarity already uses a constrained warping path rather than unconstrained DTW.",
        "dtw_similarity",
    ),
    "ddtw": (
        "Conceptually covered",
        "EchoTime's DTW similarity already mixes in derivative-space warping.",
        "dtw_similarity",
    ),
    "spectral_cosine_similarity": (
        "Conceptually covered",
        "EchoTime already includes a spectral similarity component, although the current formula blends spectral JS overlap with structural correlation.",
        "spectral_similarity",
    ),
    "jensen_shannon": (
        "Conceptually covered",
        "EchoTime already uses Jensen-Shannon overlap inside its spectral similarity component.",
        "spectral_similarity",
    ),
    "shift_pearson_similarity": (
        "Conceptually covered",
        "EchoTime already exposes a best-lag Pearson metric for shift-aware linear relationships.",
        "best_lag_pearson_r",
    ),
    "shift_pearson_distance": (
        "Conceptually covered",
        "EchoTime already exposes a best-lag Pearson metric, so the distance transform is not worth a separate public method.",
        "best_lag_pearson_r",
    ),
    "periodogram_distance": (
        "High-fit addition",
        "A direct periodogram distance would complement EchoTime's current blended spectral component with a simpler frequency-domain baseline.",
        "",
    ),
    "trend_distance": (
        "High-fit addition",
        "A direct trend-feature distance fits EchoTime's trend-first explanation style and would be easy to describe in reports.",
        "",
    ),
    "ordinal_pattern_js_distance": (
        "High-fit addition",
        "Ordinal-pattern distribution distance would give EchoTime a robust symbolic rhythm comparator that stays explainable.",
        "",
    ),
    "linear_trend_model_distance": (
        "High-fit addition",
        "A lightweight trend-model distance matches EchoTime's structural language better than heavier model-based distances.",
        "",
    ),
}

_NATIVE_METHODS = (
    EchoTimeNativeMethod(
        name="shape_similarity",
        family="EchoTime native component",
        kind="similarity",
        formula="s_shape = GM(clip(r(x,y), 0, 1), clip(r(Delta x, Delta y), 0, 1))",
        notes="Combines level correlation with first-difference correlation so the headline match does not ignore local dynamics.",
    ),
    EchoTimeNativeMethod(
        name="dtw_similarity",
        family="EchoTime native component",
        kind="similarity",
        formula="s_dtw = GM(exp(-DTW_w(x,y)/0.45), exp(-DTW_w(Delta x, Delta y)/0.35))",
        notes="Turns constrained DTW distances into a similarity score and blends level-space and derivative-space warping.",
    ),
    EchoTimeNativeMethod(
        name="trend_similarity",
        family="EchoTime native component",
        kind="similarity",
        formula="s_trend = GM(clip(r(T(x), T(y)), 0, 1), clip(r(Delta T(x), Delta T(y)), 0, 1))",
        notes="Smooths both series first, then compares both the trend level and the trend slope.",
    ),
    EchoTimeNativeMethod(
        name="derivative_similarity",
        family="EchoTime native component",
        kind="similarity",
        formula="s_diff = clip(r(Delta x, Delta y), 0, 1)",
        notes="Focuses on whether local changes move together even when the levels differ.",
    ),
    EchoTimeNativeMethod(
        name="spectral_similarity",
        family="EchoTime native component",
        kind="similarity",
        formula="s_spec = GM(1 - JSD(P_x, P_y), clip(r(P_x - U, P_y - U), 0, 1))",
        notes="Compares normalized spectra of differenced series, mixing JS overlap with structural similarity relative to a uniform spectrum U.",
    ),
    EchoTimeNativeMethod(
        name="pearson_r",
        family="EchoTime reference metric",
        kind="similarity",
        formula="r(x,y) = sum_t (x_t - x_bar)(y_t - y_bar) / sqrt(sum_t (x_t - x_bar)^2 sum_t (y_t - y_bar)^2)",
        notes="Familiar linear correlation exposed directly in every raw-series similarity report.",
    ),
    EchoTimeNativeMethod(
        name="spearman_rho",
        family="EchoTime reference metric",
        kind="similarity",
        formula="rho(x,y) = corr(rank(x), rank(y))",
        notes="Rank-order correlation used as a robustness check against nonlinear monotone relationships.",
    ),
    EchoTimeNativeMethod(
        name="kendall_tau",
        family="EchoTime reference metric",
        kind="similarity",
        formula="tau(x,y) = (C - D) / choose(n, 2)",
        notes="Pairwise concordance measure that stays interpretable when rank ordering matters more than amplitude.",
    ),
    EchoTimeNativeMethod(
        name="best_lag_pearson_r",
        family="EchoTime reference metric",
        kind="similarity",
        formula="max_lag_r(x,y) = max_ell r(x_t, y_{t-ell})",
        notes="Searches over a bounded lag window to show whether a shift-aware linear relationship is stronger than the aligned one.",
    ),
    EchoTimeNativeMethod(
        name="normalized_mutual_information",
        family="EchoTime reference metric",
        kind="similarity",
        formula="NMI(X,Y) = I(X;Y) / sqrt(H(X) H(Y))",
        notes="Histogram-based nonlinear dependence score used as a familiar cross-check against linear metrics.",
    ),
)


def _registry_path() -> Path:
    return Path(__file__).with_name("data") / "ts_similarity_package_v2_registry.csv"


def _status_for(name: str, family: str) -> tuple[str, str, str]:
    if name in _IMPLEMENTED_METHODS_BY_SOURCE_NAME:
        api_name = _IMPLEMENTED_METHODS_BY_SOURCE_NAME[name]
        return (
            "Implemented in EchoTime",
            "This method is now available as a public low-level EchoTime similarity function.",
            api_name,
        )
    if name in _STATUS_OVERRIDES:
        return _STATUS_OVERRIDES[name]
    return _DEFAULT_STATUS_BY_FAMILY[family]


@lru_cache(maxsize=1)
def _registry_rows() -> tuple[dict[str, str], ...]:
    path = _registry_path()
    if not path.exists():
        raise FileNotFoundError(f"Expected vendored similarity registry at {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [
            {
                "name": row["name"].strip(),
                "family": row["family"].strip(),
                "kind": row["kind"].strip(),
                "metric": row["metric"].strip(),
                "complexity": row["complexity"].strip(),
                "unequal_length": row["unequal_length"].strip(),
                "multivariate": row["multivariate"].strip(),
                "implementation": row["implementation"].strip(),
                "formula": (row.get("formula_en") or row.get("formula_cn") or "").strip(),
                "notes": (row.get("notes_en") or row.get("notes_cn") or "").strip(),
            }
            for row in reader
        ]
    return tuple(rows)


def native_similarity_methods() -> list[dict[str, str]]:
    return [asdict(row) for row in _NATIVE_METHODS]


def extracted_similarity_methods() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in _registry_rows():
        status, rationale, api_name = _status_for(row["name"], row["family"])
        rows.append(
            asdict(
                ExtractedMethod(
                    name=row["name"],
                    family=row["family"],
                    kind=row["kind"],
                    metric=row["metric"],
                    complexity=row["complexity"],
                    unequal_length=row["unequal_length"],
                    multivariate=row["multivariate"],
                    implementation=row["implementation"],
                    formula=row["formula"],
                    notes=row["notes"],
                    echotime_status=status,
                    echotime_rationale=rationale,
                    echotime_api=api_name,
                )
            )
        )
    return rows


def similarity_method_atlas_dict() -> dict[str, object]:
    extracted = extracted_similarity_methods()
    native = native_similarity_methods()
    by_family = {
        family: [row for row in extracted if row["family"] == family]
        for family in _FAMILY_ORDER
    }
    status_order = {
        "Implemented in EchoTime": 0,
        "High-fit addition": 1,
        "Conceptually covered": 2,
        "Possible addition": 3,
        "Low-priority addition": 4,
    }
    recommended = sorted(
        [row for row in extracted if row["echotime_status"] in {"Implemented in EchoTime", "High-fit addition"}],
        key=lambda row: (status_order[row["echotime_status"]], _FAMILY_ORDER.index(row["family"]), row["name"]),
    )
    counts_by_status: dict[str, int] = {}
    for row in extracted:
        counts_by_status[row["echotime_status"]] = counts_by_status.get(row["echotime_status"], 0) + 1
    return {
        "summary": {
            "native_method_count": len(native),
            "extracted_method_count": len(extracted),
            "family_count": len(_FAMILY_ORDER),
            "family_descriptions": dict(_FAMILY_DESCRIPTIONS),
            "counts_by_status": counts_by_status,
            "source_package": "ts_similarity_package_v2_pkg",
            "source_registry": _registry_path().name,
            "recommended_method_count": len(recommended),
        },
        "native_methods": native,
        "recommended_additions": recommended,
        "families": [
            {
                "name": family,
                "description": _FAMILY_DESCRIPTIONS[family],
                "entries": by_family[family],
            }
            for family in _FAMILY_ORDER
        ],
    }


def _md_cell(text: str) -> str:
    return str(text).replace("|", r"\|")


def similarity_method_atlas_guide(*, format: GuideFormat = "markdown") -> str | dict:
    payload = similarity_method_atlas_dict()
    if format == "dict":
        return payload

    lines = [
        "# EchoTime similarity method atlas",
        "",
        "This guide audits EchoTime's current raw-series similarity stack, then imports the full method registry from `ts_similarity_package_v2_pkg` and marks which methods fit EchoTime's product direction.",
        "",
        "## Current EchoTime comparison layer",
        "",
    ]
    for entry in payload["native_methods"]:  # type: ignore[index]
        lines.extend(
            [
                f"### {entry['name']}",
                "",
                f"- family: {entry['family']}",
                f"- kind: {entry['kind']}",
                f"- formula: `{entry['formula']}`",
                f"- note: {entry['notes']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Implemented and high-fit additions from ts_similarity_package_v2_pkg",
            "",
            "| method | family | EchoTime fit | EchoTime API | formula | why it matters |",
            "|---|---|---|---|---|---|",
        ]
    )
    for entry in payload["recommended_additions"]:  # type: ignore[index]
        api_name = entry["echotime_api"] or "-"
        lines.append(
            f"| {entry['name']} | {entry['family']} | {entry['echotime_status']} | `{_md_cell(api_name)}` | `{_md_cell(entry['formula'])}` | {_md_cell(entry['echotime_rationale'])} |"
        )

    lines.extend(["", "## Full extracted atlas", ""])
    for family in payload["families"]:  # type: ignore[index]
        lines.extend(
            [
                f"### {family['name']}",
                "",
                family["description"],
                "",
                "| method | output | metric | complexity | unequal length | multivariate | implementation | EchoTime fit | EchoTime API | formula | note |",
                "|---|---|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for entry in family["entries"]:
            api_name = entry["echotime_api"] or "-"
            lines.append(
                f"| {entry['name']} | {entry['kind']} | {entry['metric']} | {entry['complexity']} | {entry['unequal_length']} | {entry['multivariate']} | {entry['implementation']} | {entry['echotime_status']} | `{_md_cell(api_name)}` | `{_md_cell(entry['formula'])}` | {_md_cell(entry['notes'])} |"
            )
        lines.append("")

    return "\n".join(lines)


__all__ = [
    "native_similarity_methods",
    "extracted_similarity_methods",
    "similarity_method_atlas_dict",
    "similarity_method_atlas_guide",
]
