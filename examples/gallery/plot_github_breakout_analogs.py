from pathlib import Path

import pandas as pd
from echotime import compare_series, rolling_similarity

data_path = Path(__file__).resolve().parents[1] / "data" / "real_ai_attention_breakouts.csv"
df = pd.read_csv(data_path)

threads_report = compare_series(
    df["deepseek_cumulative"],
    df["threads_cumulative"],
    left_name="DeepSeek",
    right_name="Threads",
)
chatgpt_report = compare_series(
    df["deepseek_cumulative"],
    df["chatgpt_cumulative"],
    left_name="DeepSeek",
    right_name="ChatGPT",
)
windows = rolling_similarity(df["deepseek_cumulative"], df["threads_cumulative"], window=20, step=5)

print(threads_report.to_summary_card_markdown())
print(
    {
        "threads_similarity": round(threads_report.similarity_score, 3),
        "chatgpt_similarity": round(chatgpt_report.similarity_score, 3),
        "rolling_windows": len(windows),
    }
)
