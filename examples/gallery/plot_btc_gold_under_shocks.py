from pathlib import Path

import pandas as pd
from echotime import compare_series, rolling_similarity

data_path = Path(__file__).resolve().parents[1] / "data" / "real_btc_oil_vix_2024.csv"
df = pd.read_csv(data_path)

btc_vix = compare_series(df["btc_usd"], df["vix"], left_name="BTC", right_name="VIX")
btc_brent = compare_series(df["btc_usd"], df["brent_usd"], left_name="BTC", right_name="Brent")
windows = rolling_similarity(df["btc_usd"], df["vix"], window=30, step=10)

print(btc_vix.to_summary_card_markdown())
print(
    {
        "btc_vix_similarity": round(btc_vix.similarity_score, 3),
        "btc_brent_similarity": round(btc_brent.similarity_score, 3),
        "rolling_windows": len(windows),
    }
)
