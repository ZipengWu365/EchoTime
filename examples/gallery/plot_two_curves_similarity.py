from pathlib import Path

import pandas as pd
from echotime import compare_series, rolling_similarity


data_path = Path(__file__).resolve().parents[1] / "data" / "real_treasury_yields_2024.csv"
df = pd.read_csv(data_path)

report = compare_series(df["dgs10"], df["dgs2"], left_name="10Y Treasury", right_name="2Y Treasury")
windows = rolling_similarity(df["dgs10"], df["dgs2"], window=30, step=10)

print(report.to_summary_card_markdown())
print({"rolling_windows": len(windows), "mean_similarity": round(report.similarity_score, 3)})
