from pathlib import Path

import pandas as pd
from echotime import compare_series, profile_dataset

data_path = Path(__file__).resolve().parents[1] / "data" / "real_heatwave_city_temps_2024.csv"
df = pd.read_csv(data_path)

report = compare_series(df["phoenix_temp_max"], df["las_vegas_temp_max"], left_name="Phoenix max temp", right_name="Las Vegas max temp")
profile = profile_dataset(df[["phoenix_temp_max", "las_vegas_temp_max"]], domain="climate")

print(report.to_summary_card_markdown())
print(profile.to_summary_card_markdown())
