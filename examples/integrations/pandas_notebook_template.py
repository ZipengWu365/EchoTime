from __future__ import annotations

from pathlib import Path

import pandas as pd

from echotime import compare_series, profile_dataset, profile_series


def write_html(path: str, html: str) -> None:
    Path(path).write_text(html, encoding="utf-8")


def single_column_csv_example() -> None:
    """Fastest path when you have one numeric column in a CSV."""

    df = pd.read_csv("your_signal.csv")
    series = pd.to_numeric(df["load_kw"], errors="coerce").dropna().to_numpy()

    profile = profile_series(series, domain="energy")
    print(profile.to_summary_card_markdown())
    write_html("your_signal_report.html", profile.to_html_report())


def wide_table_example() -> None:
    """Profile a table with one timestamp column and multiple numeric measurements."""

    df = pd.read_csv("your_timeseries.csv")
    df = df.rename(columns={"date": "timestamp"})

    profile = profile_dataset(df, domain="energy")
    print(profile.to_summary_card_markdown())
    write_html("your_dataset_report.html", profile.to_html_report())


def long_table_example() -> None:
    """Profile irregular data stored as subject / timestamp / channel / value rows."""

    df = pd.read_csv("your_long_table.csv")
    df = df.rename(
        columns={
            "patient_id": "subject",
            "charttime": "timestamp",
            "lab_name": "channel",
            "lab_value": "value",
        }
    )

    profile = profile_dataset(df, domain="clinical")
    print(profile.to_summary_card_markdown())
    write_html("your_longitudinal_report.html", profile.to_html_report())


def compare_two_columns_example() -> None:
    """Compare two columns from your own table and write an HTML similarity report."""

    df = pd.read_csv("your_comparison.csv")

    report = compare_series(df["left_signal"], df["right_signal"])
    print(report.to_summary_card_markdown())
    write_html("your_similarity_report.html", report.to_html_report())


if __name__ == "__main__":
    # Uncomment the workflow that matches your data shape.
    # single_column_csv_example()
    # wide_table_example()
    # long_table_example()
    # compare_two_columns_example()
    pass
