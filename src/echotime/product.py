
"""High-level product-style APIs for echotime.

These helpers make the package feel less like an ontology research prototype
and more like a report generator that is easy to try in the first minute.
"""

from __future__ import annotations

from typing import Any, Literal

from .profile import DatasetProfile, SeriesProfile, profile_dataset
from .similarity import SimilarityReport, compare_profiles, compare_series
from .visuals import profile_html_report, similarity_html_report


OutputFormat = Literal["profile", "summary-card", "summary-card-json", "narrative", "card-json", "card-markdown", "json", "markdown", "html"]
SimilarityFormat = Literal["report", "summary-card", "narrative", "json", "markdown", "html"]


def explain_dataset(
    data: Any,
    *,
    domain: str | None = None,
    audience: str = "general",
    format: OutputFormat = "summary-card",
    **kwargs: Any,
) -> DatasetProfile | SeriesProfile | str:
    """One-line entry point for the most common first question.

    Example
    -------
    >>> import numpy as np
    >>> from echotime import explain_dataset
    >>> x = np.sin(np.linspace(0, 8*np.pi, 128))
    >>> print(explain_dataset(x))
    """
    profile = profile_dataset(data, domain=domain, **kwargs)
    if format == "profile":
        return profile
    if format == "summary-card":
        return profile.to_summary_card_markdown(audience=audience)
    if format == "summary-card-json":
        return profile.to_summary_card_json(audience=audience)
    if format == "narrative":
        return profile.to_narrative_report(audience=audience)
    if format == "card-json":
        return profile.to_card_json()
    if format == "card-markdown":
        return profile.to_card_markdown()
    if format == "json":
        return profile.to_json()
    if format == "markdown":
        return profile.to_markdown()
    if format == "html":
        return profile_html_report(profile, audience=audience)
    raise ValueError(f"Unsupported format: {format}")


report_dataset = explain_dataset


def explain_similarity(
    left: Any,
    right: Any,
    *,
    mode: Literal["series", "profile"] = "series",
    left_name: str = "left",
    right_name: str = "right",
    left_timestamps: Any | None = None,
    right_timestamps: Any | None = None,
    format: SimilarityFormat = "summary-card",
) -> SimilarityReport | str:
    report = compare_profiles(left, right, left_name=left_name, right_name=right_name) if mode == "profile" else compare_series(left, right, left_timestamps=left_timestamps, right_timestamps=right_timestamps, left_name=left_name, right_name=right_name)
    if format == "report":
        return report
    if format == "summary-card":
        return report.to_summary_card_markdown()
    if format == "narrative":
        return report.to_narrative_report()
    if format == "json":
        return report.to_json()
    if format == "markdown":
        return report.to_markdown()
    if format == "html":
        return similarity_html_report(report, left_series=left, right_series=right)
    raise ValueError(f"Unsupported format: {format}")


report_similarity = explain_similarity
