from pathlib import Path

import pandas as pd
from echotime import compare_series, rolling_similarity


data_path = Path(__file__).resolve().parents[1] / "data" / "real_python_javascript_pageviews_2024.csv"
df = pd.read_csv(data_path)

report = compare_series(df["python_views"], df["javascript_views"], left_name="Python pageviews", right_name="JavaScript pageviews")
windows = rolling_similarity(df["python_views"], df["javascript_views"], window=28, step=7)

print(report.to_summary_card_markdown())
print({"rolling_windows": len(windows), "mean_similarity": round(report.similarity_score, 3)})
