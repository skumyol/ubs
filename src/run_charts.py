"""Export charts and tables for PowerPoint deck."""

import pandas as pd
from pathlib import Path

from src.config import (
    CATEGORY_COUNTS_PATH,
    CLASSIFIED_PARAGRAPHS_PATH,
    CATEGORY_BAR_CHART_PATH,
    SIGNAL_HEATMAP_PATH,
    SENTIMENT_COMPARISON_PATH,
    LONG_SHORT_MATRIX_PATH,
    TABLES_DIR,
)
from src.charts import (
    create_category_bar_chart,
    create_signal_heatmap,
    create_sentiment_comparison,
    create_long_short_matrix_table,
)
from src.analysis import sentiment_score


def main():
    # Ensure output dirs exist
    CATEGORY_BAR_CHART_PATH.parent.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Category frequency bar chart
    if CATEGORY_COUNTS_PATH.exists():
        counts_df = pd.read_csv(CATEGORY_COUNTS_PATH)
        create_category_bar_chart(counts_df, str(CATEGORY_BAR_CHART_PATH))
        print(f"Saved: {CATEGORY_BAR_CHART_PATH}")
    else:
        print(f"[SKIP] {CATEGORY_COUNTS_PATH} not found. Run run_analysis.py first.")

    # 2. Signal heatmap
    if CLASSIFIED_PARAGRAPHS_PATH.exists():
        df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
        from src.analysis import build_signal_tracker

        tracker = build_signal_tracker(df)
        create_signal_heatmap(tracker, str(SIGNAL_HEATMAP_PATH))
        print(f"Saved: {SIGNAL_HEATMAP_PATH}")
    else:
        print(f"[SKIP] {CLASSIFIED_PARAGRAPHS_PATH} not found.")

    # 3. Sentiment comparison
    if CLASSIFIED_PARAGRAPHS_PATH.exists():
        df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
        df["sentiment_score"] = df["sentiment"].apply(sentiment_score)
        create_sentiment_comparison(df, str(SENTIMENT_COMPARISON_PATH))
        print(f"Saved: {SENTIMENT_COMPARISON_PATH}")

    # 4. Long/Short matrix table
    create_long_short_matrix_table(str(LONG_SHORT_MATRIX_PATH))
    print(f"Saved: {LONG_SHORT_MATRIX_PATH}")

    print("\nAll deck-ready outputs exported.")
    print(f"Charts: {CATEGORY_BAR_CHART_PATH.parent}")
    print(f"Tables: {TABLES_DIR}")


if __name__ == "__main__":
    main()
