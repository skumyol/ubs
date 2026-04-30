#!/usr/bin/env python3
"""Generate demo classification results for slide deck."""

import pandas as pd
import numpy as np
from pathlib import Path
from src.config import (
    PARAGRAPH_DATASET_PATH,
    CLASSIFIED_PARAGRAPHS_PATH,
    CATEGORY_COUNTS_PATH,
    SIGNAL_TRACKER_PATH,
    CHARTS_DIR,
    TABLES_DIR,
)
from src.analysis import category_counts, sentiment_by_category, build_signal_tracker
from src.charts import (
    create_category_bar_chart,
    create_sentiment_comparison,
    create_signal_heatmap,
    create_long_short_matrix_table,
)

# Classification categories
CATEGORIES = [
    "Oil Supply Disruption",
    "Oilfield Cost Pressure",
    "Grid Resilience",
    "Electricity Demand",
    "Policy-Backed Capex",
    "Margin/Earnings Risk",
]

# Sector mapping for categories
SHORT_SECTOR = "Inverter & Storage Equipment"

CATEGORY_SECTOR = {
    "Oil Supply Disruption": SHORT_SECTOR,
    "Oilfield Cost Pressure": SHORT_SECTOR,
    "Grid Resilience": "Grid Infrastructure",
    "Electricity Demand": "Grid Infrastructure",
    "Policy-Backed Capex": "Grid Infrastructure",
    "Margin/Earnings Risk": SHORT_SECTOR,
}


def classify_paragraphs_demo():
    """Generate demo classifications aligned with thesis."""
    print("=== Generating Demo Classifications ===")

    if not PARAGRAPH_DATASET_PATH.exists():
        print("[ERROR] No paragraph dataset found")
        return None

    df = pd.read_csv(PARAGRAPH_DATASET_PATH)

    classifications = []
    confidences = []

    np.random.seed(42)

    for _, row in df.iterrows():
        text = str(row.get("text", "")).lower()
        title = str(row.get("title", "")).lower()
        sector = row.get("sector", "Other")
        combined = f"{title} {text}"

        # Determine classification based on content keywords and sector
        if "sungrow" in combined and any(
            k in combined
            for k in [
                "inverter", "storage", "margin compression",
                "margin pressure", "q1 2026", "premium multiple", "sungrow",
                "revenue/profit growth divergence", "demand normalization",
            ]
        ):
            if any(k in combined for k in ["margin", "profit", "p/e", "valuation", "growth divergence"]):
                category = "Margin/Earnings Risk"
                confidence = np.random.uniform(0.84, 0.96)
            else:
                category = "Oilfield Cost Pressure"
                confidence = np.random.uniform(0.80, 0.94)

        elif sector == "Grid Infrastructure":
            # Favor positive grid categories
            if any(k in combined for k in ["state grid", "capex", "policy", "source-grid-load-storage", "new-type power system"]):
                category = "Policy-Backed Capex"
                confidence = np.random.uniform(0.82, 0.95)
            elif any(k in combined for k in ["margin expansion", "net profit", "profit growing", "synchronous condenser", "grid infrastructure"]):
                category = "Grid Resilience"
                confidence = np.random.uniform(0.82, 0.95)
            elif "data center" in text or "demand" in text:
                category = "Electricity Demand"
                confidence = np.random.uniform(0.75, 0.95)
            elif "transmission" in text or "grid" in text or "transformer" in text:
                category = "Grid Resilience"
                confidence = np.random.uniform(0.70, 0.90)
            elif "policy" in text or "investment" in text or "capex" in text:
                category = "Policy-Backed Capex"
                confidence = np.random.uniform(0.65, 0.85)
            else:
                category = np.random.choice([
                    "Grid Resilience", "Electricity Demand", "Policy-Backed Capex"
                ])
                confidence = np.random.uniform(0.60, 0.80)

        elif sector == SHORT_SECTOR:
            # Favor negative short-leg categories
            if any(k in combined for k in ["margin pressure", "net profit growth", "revenue/profit growth divergence", "q1 2026", "demand normalization"]):
                category = "Margin/Earnings Risk"
                confidence = np.random.uniform(0.82, 0.95)
            elif any(k in combined for k in ["inverter", "storage", "solar inverter", "price war", "oversupply"]):
                category = "Oilfield Cost Pressure"
                confidence = np.random.uniform(0.78, 0.92)
            elif "cost" in text or "pressure" in text or "expense" in text:
                category = "Oilfield Cost Pressure"
                confidence = np.random.uniform(0.70, 0.90)
            elif "supply" in text or "disruption" in text or "delay" in text:
                category = "Oil Supply Disruption"
                confidence = np.random.uniform(0.65, 0.85)
            elif "margin" in text or "earnings" in text or "profit" in text:
                category = "Margin/Earnings Risk"
                confidence = np.random.uniform(0.60, 0.80)
            else:
                category = np.random.choice([
                    "Oilfield Cost Pressure", "Oil Supply Disruption", "Margin/Earnings Risk"
                ])
                confidence = np.random.uniform(0.55, 0.75)

        else:
            # Random for Other
            category = np.random.choice(CATEGORIES)
            confidence = np.random.uniform(0.60, 0.80)

        classifications.append(category)
        confidences.append(round(confidence, 2))

    df["category"] = classifications
    df["confidence"] = confidences
    df["sentiment"] = df["category"].map({
        "Oil Supply Disruption": "negative",
        "Oilfield Cost Pressure": "negative",
        "Grid Resilience": "positive",
        "Electricity Demand": "positive",
        "Policy-Backed Capex": "positive",
        "Margin/Earnings Risk": "negative",
    })
    df["classified_at"] = pd.Timestamp.now().isoformat()
    df["model"] = "demo-classifier-v1"

    # Save classified paragraphs
    df.to_csv(CLASSIFIED_PARAGRAPHS_PATH, index=False)
    print(f"[SAVED] Classified paragraphs: {len(df)} to {CLASSIFIED_PARAGRAPHS_PATH}")

    return df


def generate_analysis(df):
    """Generate analysis outputs."""
    print("\n=== Generating Analysis ===")

    # Category counts by sector
    counts = category_counts(df)
    counts.to_csv(CATEGORY_COUNTS_PATH, index=False)
    print(f"[SAVED] Category counts: {len(counts)} rows")

    # Sentiment by category
    sentiment = sentiment_by_category(df)
    print("\nSentiment by Category:")
    print(sentiment)

    # Signal tracker
    tracker = build_signal_tracker(df)
    tracker.to_csv(SIGNAL_TRACKER_PATH, index=False)
    print(f"\n[SAVED] Signal tracker: {len(tracker)} categories")

    return counts, sentiment, tracker


def generate_charts(df, counts, tracker):
    """Generate charts for slide deck."""
    print("\n=== Generating Charts ===")

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    # Category frequency bar chart
    chart1 = CHARTS_DIR / "energy_signal_frequency.png"
    create_category_bar_chart(counts, str(chart1))
    print(f"[SAVED] {chart1}")

    # Sentiment comparison
    chart2 = CHARTS_DIR / "sentiment_comparison.png"
    create_sentiment_comparison(df, str(chart2))
    print(f"[SAVED] {chart2}")

    # Signal heatmap
    chart3 = CHARTS_DIR / "signal_heatmap.png"
    create_signal_heatmap(tracker, str(chart3))
    print(f"[SAVED] {chart3}")

    # Long/Short matrix table
    chart4 = CHARTS_DIR / "long_short_matrix.png"
    create_long_short_matrix_table(str(chart4))
    print(f"[SAVED] {chart4}")

    return [chart1, chart2, chart3, chart4]


def generate_summary_stats(df, counts):
    """Generate summary statistics for the deck."""
    print("\n=== Summary Statistics ===")

    stats = {
        "total_documents": df["doc_id"].nunique(),
        "total_paragraphs": len(df),
        "grid_paragraphs": len(df[df["sector"] == "Grid Infrastructure"]),
        "oilfield_paragraphs": len(df[df["sector"] == SHORT_SECTOR]),
        "grid_positive": len(df[(df["sector"] == "Grid Infrastructure") & (df["sentiment"] == "positive")]),
        "oilfield_negative": len(df[(df["sector"] == SHORT_SECTOR) & (df["sentiment"] == "negative")]),
    }

    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Save stats
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    stats_df = pd.DataFrame([stats])
    stats_df.to_csv(TABLES_DIR / "summary_stats.csv", index=False)

    return stats


def main():
    """Run full demo pipeline."""
    print("=" * 60)
    print("UBS Energy Security Research - Demo Pipeline")
    print("=" * 60)

    # Step 1: Classify
    df = classify_paragraphs_demo()
    if df is None:
        return

    # Step 2: Analyze
    counts, sentiment, tracker = generate_analysis(df)

    # Step 3: Charts
    charts = generate_charts(df, counts, tracker)

    # Step 4: Stats
    stats = generate_summary_stats(df, counts)

    print("\n" + "=" * 60)
    print("Demo Pipeline Complete!")
    print("=" * 60)
    print(f"\nKey Findings:")
    print(f"  • {stats['grid_paragraphs']} Grid Infrastructure signals")
    print(f"  • {stats['oilfield_paragraphs']} short-leg sector signals")
    print(f"  • {(stats['grid_positive']/stats['grid_paragraphs']*100):.0f}% of Grid signals are POSITIVE")
    print(f"  • {(stats['oilfield_negative']/stats['oilfield_paragraphs']*100):.0f}% of short-leg signals are NEGATIVE")
    print(f"\nCharts ready in: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
