"""Generate analysis outputs from classified paragraphs."""

import pandas as pd
from pathlib import Path

from src.config import (
    CLASSIFIED_PARAGRAPHS_PATH,
    CATEGORY_COUNTS_PATH,
    SIGNAL_TRACKER_PATH,
    KEYWORD_FREQUENCY_PATH,
)
from src.analysis import category_counts, sentiment_by_category, build_signal_tracker


def extract_keywords(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Simple keyword extraction from classified paragraphs."""
    from collections import Counter
    import re

    keywords = {
        "Oil Supply Disruption": [
            "hormuz", "middle east", "opec", "sanction", "embargo",
            "attack", "disruption", "supply cut", "production",
        ],
        "Oilfield Cost Pressure": [
            "logistics", "freight", "supply chain", "inflation",
            "delay", "material", "cost pressure",
        ],
        "Grid Resilience": [
            "transmission", "substation", "transformer", "switchgear",
            "grid", "upgrade", "hardening", "resilience",
        ],
        "Electricity Demand": [
            "data center", "ev charging", "electrification", "cooling",
            "ai power", "renewable", "demand",
        ],
        "Policy-Backed Capex": [
            "infrastructure", "investment", "policy", "government",
            "capex", "bill", "mandate",
        ],
        "Margin / Earnings Risk": [
            "margin", "earnings", "guidance", "utilization", "pricing",
            "compression", "pressure",
        ],
    }

    rows = []
    for category, terms in keywords.items():
        cat_df = df[df["category"] == category]
        text = " ".join(cat_df["text"].astype(str).str.lower())

        counts = Counter()
        for term in terms:
            counts[term] = len(re.findall(rf"\b{re.escape(term)}\b", text))

        for term, count in counts.most_common(top_n):
            if count > 0:
                rows.append({
                    "category": category,
                    "keyword": term,
                    "mention_count": count,
                })

    return pd.DataFrame(rows).sort_values(
        ["category", "mention_count"], ascending=[True, False]
    )


def main():
    if not CLASSIFIED_PARAGRAPHS_PATH.exists():
        raise FileNotFoundError(
            f"Classified paragraphs not found: {CLASSIFIED_PARAGRAPHS_PATH}\n"
            "Run run_classifier.py first."
        )

    df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
    print(f"Loaded {len(df)} classified paragraphs")

    # 1. Category counts
    counts = category_counts(df)
    counts.to_csv(CATEGORY_COUNTS_PATH, index=False)
    print(f"\nSaved category counts: {CATEGORY_COUNTS_PATH}")
    print(counts.head(10))

    # 2. Sentiment by category
    sentiment = sentiment_by_category(df)
    print("\nSentiment by category:")
    print(sentiment)

    # 3. Signal tracker
    tracker = build_signal_tracker(df)
    tracker.to_csv(SIGNAL_TRACKER_PATH, index=False)
    print(f"\nSaved signal tracker: {SIGNAL_TRACKER_PATH}")
    print(tracker)

    # 4. Keyword frequency
    keywords = extract_keywords(df)
    keywords.to_csv(KEYWORD_FREQUENCY_PATH, index=False)
    print(f"\nSaved keyword frequency: {KEYWORD_FREQUENCY_PATH}")
    print(keywords.head(10))

    print("\nAnalysis complete. Outputs ready for chart generation.")


if __name__ == "__main__":
    main()
