from pathlib import Path

import pandas as pd
from echotime import compare_series, profile_dataset


data_path = Path(__file__).resolve().parents[1] / "data" / "real_usgs_earthquakes_ca_ak_2024.csv"
df = pd.read_csv(data_path)
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="mixed").astype("int64") / 1_000_000_000
df["event_type"] = df["magnitude"].map(lambda value: "M4+" if value >= 4.0 else "M2.5-4")

california = df.loc[df["region"] == "California"].sort_values("timestamp")
alaska = df.loc[df["region"] == "Alaska"].sort_values("timestamp")

report = compare_series(
    california["magnitude"],
    alaska["magnitude"],
    left_timestamps=california["timestamp"],
    right_timestamps=alaska["timestamp"],
    left_name="California earthquakes",
    right_name="Alaska earthquakes",
)
profile = profile_dataset(
    df.rename(columns={"region": "subject", "magnitude": "value"})[["timestamp", "value", "subject", "event_type"]],
    domain="earth_science",
)

print(report.to_summary_card_markdown())
print(profile.to_summary_card_markdown())
