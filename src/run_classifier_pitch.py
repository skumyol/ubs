#!/usr/bin/env python3
"""Run REAL LLM classification for pitch class demonstration.

Uses DeepSeek API for cost-effective classification.
Processes 30 representative paragraphs for pitch demo.
"""

import os
import sys
import time
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

from src.config import (
    PARAGRAPH_DATASET_PATH,
    CLASSIFIED_PARAGRAPHS_PATH,
    LLM_DELAY_SECONDS,
)
from src.classifier import build_classification_prompt, parse_ai_response

load_dotenv()

# Classification categories
CATEGORIES = [
    "Oil Supply Disruption",
    "Oilfield Cost Pressure",
    "Grid Resilience",
    "Electricity Demand",
    "Policy-Backed Capex",
    "Margin/Earnings Risk",
    "Not Relevant",
]


def get_deepseek_caller():
    """Get DeepSeek API caller."""
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_key:
        raise ValueError("DEEPSEEK_API_KEY not found in environment")

    try:
        from openai import OpenAI
    except ImportError:
        print("Installing openai package...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "openai", "-q"])
        from openai import OpenAI

    client = OpenAI(
        api_key=deepseek_key,
        base_url="https://api.deepseek.com/v1",
    )

    def call_deepseek(prompt: str) -> str:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an expert equity research analyst specializing in energy infrastructure. Classify text into exactly one category."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=150,
        )
        return resp.choices[0].message.content

    return call_deepseek


def classify_with_llm(text: str, llm_caller) -> tuple:
    """Classify a single paragraph using LLM."""
    # Build simple prompt
    categories_str = "\n".join([f"{i+1}. {cat}" for i, cat in enumerate(CATEGORIES)])

    # Escape quotes in text for JSON safety
    safe_text = text[:800].replace('"', "'")

    prompt = f"""Classify this energy sector text into exactly one category:

Text: "{safe_text}"

Categories:
{categories_str}

Respond with ONLY the category name and confidence (0.0-1.0) in this format:
Category: <category_name>
Confidence: <0.00-1.00>
Sentiment: <positive/negative/neutral>
"""

    try:
        response = llm_caller(prompt)

        # Parse response
        category = "Not Relevant"
        confidence = 0.5
        sentiment = "neutral"

        for line in response.split('\n'):
            line = line.strip()
            if line.lower().startswith('category:'):
                category = line.split(':', 1)[1].strip()
            elif line.lower().startswith('confidence:'):
                try:
                    confidence = float(line.split(':', 1)[1].strip())
                except:
                    confidence = 0.5
            elif line.lower().startswith('sentiment:'):
                sentiment = line.split(':', 1)[1].strip().lower()

        # Validate category
        if category not in CATEGORIES:
            # Find closest match
            for valid_cat in CATEGORIES:
                if valid_cat.lower() in category.lower():
                    category = valid_cat
                    break
            else:
                category = "Not Relevant"

        return category, round(confidence, 2), sentiment

    except Exception as e:
        print(f"  LLM error: {e}")
        return "Not Relevant", 0.0, "neutral"


def main():
    """Run classification on all unclassified paragraphs."""
    print("=" * 60)
    print("UBS Pitch Class - Real LLM Classification")
    print("=" * 60)

    # Check API key
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("\n[ERROR] DEEPSEEK_API_KEY not found in .env")
        print("Add it to .env: DEEPSEEK_API_KEY=sk-...")
        return

    # Load data
    if not PARAGRAPH_DATASET_PATH.exists():
        print(f"[ERROR] No dataset found at {PARAGRAPH_DATASET_PATH}")
        return

    df = pd.read_csv(PARAGRAPH_DATASET_PATH)
    print(f"\nLoaded {len(df)} paragraphs")

    # Load existing classifications
    existing_classified = pd.DataFrame()
    if CLASSIFIED_PARAGRAPHS_PATH.exists():
        existing_classified = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
        print(f"Already classified: {len(existing_classified)} paragraphs")

    # Filter out already classified
    if len(existing_classified) > 0:
        classified_ids = set(existing_classified['paragraph_id'])
        df = df[~df['paragraph_id'].isin(classified_ids)]

    print(f"Unclassified to process: {len(df)} paragraphs")

    if len(df) == 0:
        print("\n✓ All paragraphs already classified!")
        return

    # Prioritize Oilfield Services (HAL/SLB) for short leg evidence
    oilfield_mask = df['doc_id'].str.contains('hal_|slb_', case=False, na=False)
    oilfield_df = df[oilfield_mask]
    other_df = df[~oilfield_mask]

    # Also check source_name for oilfield content
    oilfield_source_mask = df['source_name'].str.contains('halliburton|schlumberger|slb|oilfield|drilling', case=False, na=False)
    oilfield_source_df = df[oilfield_source_mask & ~oilfield_mask]

    # Combine oilfield sources, then other docs
    sample_df = pd.concat([oilfield_df, oilfield_source_df, other_df]).reset_index(drop=True)

    # Limit batch size to avoid excessive API calls (process 100 at a time)
    batch_size = min(100, len(sample_df))
    sample_df = sample_df.head(batch_size)

    print(f"Processing batch: {len(sample_df)} paragraphs")
    print(f"  - HAL/SLB transcripts: {len(oilfield_df)}")
    print(f"  - Oilfield sources: {len(oilfield_source_df)}")
    print(f"  - Other documents: {len(other_df.head(batch_size - len(oilfield_df) - len(oilfield_source_df)))}")

    # Get LLM
    print("\nConnecting to DeepSeek API...")
    llm_caller = get_deepseek_caller()
    print("✓ Connected")

    # Classify
    print(f"\nClassifying {len(sample_df)} paragraphs...")
    results = []

    for idx, row in tqdm(sample_df.iterrows(), total=len(sample_df)):
        text = str(row.get("text", ""))
        if len(text) < 50:
            continue

        category, confidence, sentiment = classify_with_llm(text, llm_caller)

        results.append({
            **row.to_dict(),
            "category": category,
            "confidence": confidence,
            "sentiment": sentiment,
            "model": "deepseek-chat",
            "classified_at": pd.Timestamp.now().isoformat(),
        })

        # Rate limiting
        time.sleep(LLM_DELAY_SECONDS)

    # Save results (append to existing)
    result_df = pd.DataFrame(results)

    if len(existing_classified) > 0:
        combined_df = pd.concat([existing_classified, result_df], ignore_index=True)
        # Remove duplicates based on paragraph_id
        combined_df = combined_df.drop_duplicates(subset=['paragraph_id'], keep='last')
        combined_df.to_csv(CLASSIFIED_PARAGRAPHS_PATH, index=False)
        print(f"\n[SAVED] {len(results)} new + {len(existing_classified)} existing = {len(combined_df)} total classifications")
    else:
        result_df.to_csv(CLASSIFIED_PARAGRAPHS_PATH, index=False)
        print(f"\n[SAVED] {len(results)} classifications to {CLASSIFIED_PARAGRAPHS_PATH}")

    # Summary
    print("\n" + "=" * 60)
    print("CLASSIFICATION SUMMARY")
    print("=" * 60)
    print(f"\nTotal classified: {len(results)}")
    print(f"\nBy Category:")
    print(result_df["category"].value_counts())
    print(f"\nBy Sector:")
    print(result_df["sector"].value_counts())
    print(f"\nBy Sentiment:")
    print(result_df["sentiment"].value_counts())
    print(f"\nAvg Confidence: {result_df['confidence'].mean():.2f}")

    # Check thesis alignment
    grid_positive = len(result_df[
        (result_df["sector"] == "Grid Infrastructure") &
        (result_df["sentiment"] == "positive")
    ])
    oilfield_negative = len(result_df[
        (result_df["sector"] == "Oilfield Services") &
        (result_df["sentiment"] == "negative")
    ])

    grid_total = len(result_df[result_df["sector"] == "Grid Infrastructure"])
    oilfield_total = len(result_df[result_df["sector"] == "Oilfield Services"])

    if grid_total > 0 and oilfield_total > 0:
        print(f"\n" + "=" * 60)
        print("THESIS VALIDATION")
        print("=" * 60)
        print(f"Grid Infrastructure: {grid_positive}/{grid_total} positive ({grid_positive/grid_total*100:.0f}%)")
        print(f"Oilfield Services: {oilfield_negative}/{oilfield_total} negative ({oilfield_negative/oilfield_total*100:.0f}%)")


if __name__ == "__main__":
    main()
