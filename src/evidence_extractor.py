"""Extract killer quotes for each slide from classified paragraphs.

Judges remember specific, quantified quotes from source documents.
This module pulls the best 1-3 supporting quotes per slide/category.
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List

# Slide -> categories mapping
# max_quotes is pre-dedupe candidate count; final count after dedupe may be lower
SLIDE_EVIDENCE_MAP = {
    "slide_3_variant_view": {
        "title": "Variant View: Grid Resilience is the Real Energy Security Trade",
        "categories": ["Electricity Demand", "Grid Resilience"],
        "min_confidence": 0.70,
        "max_quotes": 6,
    },
    "slide_4_industry_outlook": {
        "title": "Electricity Continuity is Becoming Strategic Infrastructure",
        "categories": ["Electricity Demand", "Grid Resilience", "Policy-Backed Capex"],
        "min_confidence": 0.70,
        "max_quotes": 8,
    },
    "slide_5_long_case": {
        "title": "Sieyuan Electric: Direct Beneficiary of Grid Hardening",
        "categories": ["Grid Resilience", "Policy-Backed Capex"],
        "min_confidence": 0.70,
        "max_quotes": 6,
    },
    "slide_7_short_case": {
        "title": "Oilfield-Service Peer: Exposed to Fragile Energy Logistics",
        "categories": ["Oil Supply Disruption", "Oilfield Cost Pressure", "Margin/Earnings Risk"],
        "min_confidence": 0.60,
        "max_quotes": 8,
    },
    "slide_8_short_upside": {
        "title": "Higher Oil Prices Do Not Guarantee Service Earnings",
        "categories": ["Margin/Earnings Risk", "Oilfield Cost Pressure"],
        "min_confidence": 0.60,
        "max_quotes": 8,
    },
    "slide_10_ai_module": {
        "title": "AI Signal Tracker: Capex Language Moving to Grid",
        "categories": ["Electricity Demand", "Grid Resilience", "Policy-Backed Capex",
                       "Oil Supply Disruption", "Oilfield Cost Pressure", "Margin/Earnings Risk"],
        "min_confidence": 0.75,
        "max_quotes": 6,  # One per category
    },
}

# How many quotes to actually display per slide after dedupe
SLIDE_DISPLAY_LIMIT = {
    "slide_3_variant_view": 3,
    "slide_4_industry_outlook": 3,
    "slide_5_long_case": 2,
    "slide_7_short_case": 3,
    "slide_8_short_upside": 2,
    "slide_10_ai_module": 6,
}


# Patterns that indicate boilerplate metadata, not real evidence
BOILERPLATE_PATTERNS = [
    r"^\s*Date\s+\w+\.\s+\d+,\s*\d{4}",  # "Date Jan. 21, 2026"
    r"at\s+\d+\s*a\.m\.\s*ET",  # "at 9 a.m. ET"
    r"Call participants",
    r"Need a quote from a Motley Fool",
    r"Motley Fool Transcribing",
    r"By\s*\n",  # "By\n Motley Fool..."
    r"Earnings Transcript\s*$",  # Page title
    r"Executive Vice President and (?:Chief Financial Officer|CFO)",  # Title-only lines
    r"Chairman,?\s+President,?\s+and (?:Chief Executive Officer|CEO)",
    r"^\s*(?:Table of Contents|Introduction|Appendix|References)\s*$",
    r"^(?:Source|Note|Figure|Table|Chart)\s*\d+",
    r"PAGE\s*\|\s*\d+",  # IEA page markers
    r"CC BY\s+\d+\.\d+",  # Creative Commons tags
    r"^\s*\d+\s*$",  # Just page numbers
]

# Boilerplate keyword markers
BOILERPLATE_KEYWORDS = [
    "cookie", "subscribe", "sign up", "privacy policy",
    "all rights reserved", "click here", "direct naar",
    "motley fool", "accept", "reject all", "list of partners",
    "terms of use", "disclosure policy",
]


def is_boilerplate(text: str) -> bool:
    """Check if a quote is boilerplate metadata rather than substantive content."""
    # Match boilerplate patterns
    for pattern in BOILERPLATE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            return True

    # Keyword density check
    text_lower = text.lower()
    boilerplate_hits = sum(1 for kw in BOILERPLATE_KEYWORDS if kw in text_lower)
    if boilerplate_hits >= 2:
        return True

    # Reject if mostly just names/titles (no verbs indicating action/claim)
    action_verbs = [
        "grew", "rose", "fell", "increased", "decreased", "expanded", "contracted",
        "reported", "announced", "expects", "forecast", "projected", "drove",
        "gained", "lost", "surged", "declined", "led", "benefit", "suffered",
        "is", "are", "was", "were", "will", "would", "could", "should",
        "means", "shows", "indicates", "suggests", "plans", "targets", "drives",
    ]
    words = text_lower.split()
    if len(words) < 10:
        return True  # Too short to be substantive
    has_verb = any(verb in words for verb in action_verbs)
    if not has_verb:
        return True

    return False


def score_quote(text: str, confidence: float, slide_id: str = "") -> float:
    """Score a quote by quality heuristics.

    Prefers quotes that are:
    - Specific (contains numbers, percentages, dollar amounts)
    - Named entities (companies, places)
    - Moderate length (50-400 chars)
    - High confidence
    - Substantive (not boilerplate metadata)
    - For short thesis: contradicts the consensus narrative
    """
    # Hard reject boilerplate
    if is_boilerplate(text):
        return -1000.0

    score = confidence * 100

    # Reward quantification
    if re.search(r'\d+%', text):
        score += 20
    if re.search(r'\$[\d,.]+[BMK]?', text):
        score += 20
    if re.search(r'\d+[,]\d+', text):
        score += 10

    # Reward proper nouns / named entities (rough proxy: capitalized multi-word)
    proper_nouns = len(re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}', text))
    score += min(proper_nouns * 5, 25)

    # Length penalty/reward
    length = len(text)
    if 80 <= length <= 400:
        score += 15
    elif length < 50:
        score -= 30
    elif length > 600:
        score -= 10

    # Consensus contradiction bonus (critical for short thesis)
    # Quotes that show oil price disconnect from service earnings get major bonus
    if slide_id == "slide_8_short_upside":
        contradiction_markers = [
            "margin", "cost", "pressure", "compress", "decline", "delay", "defer",
            "rig count", "utilization", "backlog", "not correlated", "lag", "disconnect",
            "even though", "despite", "in spite of", "challenging", "difficult",
            "logistics", "supply chain", "inflation", "pricing power",
        ]
        text_lower = text.lower()
        contradiction_hits = sum(1 for m in contradiction_markers if m in text_lower)
        if contradiction_hits >= 2:
            score += 50  # Strong contradiction signal
        elif contradiction_hits == 1:
            score += 20
        
        # Extra bonus for explicit management guidance on decline
        if any(m in text_lower for m in ["revenue to decline", "earnings to decline", "guidance", "expect"]):
            score += 30
    
    # For short case slide, boost margin/earnings risk evidence
    if slide_id == "slide_7_short_case":
        risk_markers = ["margin", "cost", "earnings", "revenue decline", "pressure", "compress"]
        text_lower = text.lower()
        risk_hits = sum(1 for m in risk_markers if m in text_lower)
        if risk_hits >= 2:
            score += 25

    # Penalize navigation/boilerplate markers
    if any(marker in text.lower() for marker in BOILERPLATE_KEYWORDS):
        score -= 100

    return score


def clean_quote(text: str, max_length: int = 300) -> str:
    """Clean a quote for presentation."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Truncate intelligently at sentence boundary
    if len(text) > max_length:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        result = ""
        for s in sentences:
            if len(result) + len(s) + 1 <= max_length:
                result += (" " + s) if result else s
            else:
                break
        text = result if result else text[:max_length] + "..."

    return text


def extract_evidence(
    classified_df: pd.DataFrame,
    slide_config: Dict,
    slide_id: str = "",
) -> List[Dict]:
    """Extract top quotes for a slide based on its config."""
    categories = slide_config["categories"]
    min_conf = slide_config["min_confidence"]
    max_quotes = slide_config["max_quotes"]

    # Filter relevant paragraphs
    df = classified_df[
        (classified_df["category"].isin(categories)) &
        (classified_df["confidence"] >= min_conf)
    ].copy()

    if df.empty:
        return []

    # Score each quote (pass slide_id for context-aware scoring)
    df["quality_score"] = df.apply(
        lambda r: score_quote(str(r["text"]), float(r["confidence"]), slide_id),
        axis=1,
    )

    # For slide_10 (AI module), pick top quote per category
    if slide_config["title"].startswith("AI Signal"):
        quotes = []
        for cat in categories:
            cat_df = df[df["category"] == cat].nlargest(1, "quality_score")
            for _, row in cat_df.iterrows():
                quotes.append({
                    "category": row["category"],
                    "sentiment": row.get("sentiment", "neutral"),
                    "confidence": round(float(row["confidence"]), 2),
                    "source": row.get("title", row.get("source_name", "Unknown")),
                    "quote": clean_quote(str(row["text"])),
                    "quality_score": round(float(row["quality_score"]), 1),
                })
        return quotes

    # Otherwise top N by quality
    top_df = df.nlargest(max_quotes, "quality_score")
    return [
        {
            "category": row["category"],
            "sentiment": row.get("sentiment", "neutral"),
            "confidence": round(float(row["confidence"]), 2),
            "source": row.get("title", row.get("source_name", "Unknown")),
            "quote": clean_quote(str(row["text"])),
            "quality_score": round(float(row["quality_score"]), 1),
        }
        for _, row in top_df.iterrows()
    ]


def build_evidence_pack(
    classified_df: pd.DataFrame,
    output_path: Path,
) -> Dict[str, List[Dict]]:
    """Build complete evidence pack for all slides.

    Saves JSON and Markdown for deck integration.
    Each quote appears on at most one slide (dedupes across slides).
    """
    import json

    evidence = {}
    used_quotes = set()  # Track (first 120 chars) to dedupe across slides

    for slide_id, config in SLIDE_EVIDENCE_MAP.items():
        all_quotes = extract_evidence(classified_df, config, slide_id)

        # Dedupe: drop quotes already used on another slide
        unique_quotes = []
        for q in all_quotes:
            quote_key = q["quote"][:120].strip().lower()
            if quote_key not in used_quotes:
                used_quotes.add(quote_key)
                unique_quotes.append(q)

        # Apply display limit after dedupe
        display_limit = SLIDE_DISPLAY_LIMIT.get(slide_id, 3)
        unique_quotes = unique_quotes[:display_limit]

        evidence[slide_id] = {
            "title": config["title"],
            "quotes": unique_quotes,
        }

    # Save JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_path.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(evidence, f, indent=2)

    # Save Markdown for easy pasting into deck
    md_path = output_path.with_suffix(".md")
    with open(md_path, "w") as f:
        f.write("# Evidence Pack for UBS Pitch Deck\n\n")
        f.write("*Auto-generated from AI-classified paragraphs*\n\n")

        for slide_id, slide_data in evidence.items():
            f.write(f"## {slide_data['title']}\n\n")
            f.write(f"**Slide ID:** `{slide_id}`\n\n")

            if not slide_data["quotes"]:
                f.write("_No evidence found. Collect more data._\n\n")
                continue

            for i, q in enumerate(slide_data["quotes"], 1):
                f.write(f"### Quote {i} — {q['category']}\n\n")
                f.write(f"> {q['quote']}\n\n")
                f.write(f"- **Source:** {q['source']}\n")
                f.write(f"- **Sentiment:** {q['sentiment']}\n")
                f.write(f"- **Confidence:** {q['confidence']}\n")
                f.write(f"- **Quality Score:** {q['quality_score']}\n\n")

            f.write("---\n\n")

    print(f"[SAVED] {json_path}")
    print(f"[SAVED] {md_path}")

    return evidence


if __name__ == "__main__":
    from src.config import CLASSIFIED_PARAGRAPHS_PATH, OUTPUTS_DIR

    if not CLASSIFIED_PARAGRAPHS_PATH.exists():
        print(f"[ERROR] No classifications found at {CLASSIFIED_PARAGRAPHS_PATH}")
        print("Run: python -m src.run_classifier_pitch")
        exit(1)

    df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
    print(f"Loaded {len(df)} classified paragraphs")

    output = OUTPUTS_DIR / "tables" / "evidence_pack"
    evidence = build_evidence_pack(df, output)

    print("\n" + "=" * 60)
    print("EVIDENCE PACK SUMMARY")
    print("=" * 60)
    for slide_id, slide_data in evidence.items():
        n = len(slide_data["quotes"])
        print(f"  {slide_id}: {n} quotes for '{slide_data['title']}'")
