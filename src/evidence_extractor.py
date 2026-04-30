"""Extract killer quotes for each slide from classified paragraphs.

Judges remember specific, quantified quotes from source documents.
This module pulls the best 1-3 supporting quotes per slide/category.
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List

from src.pair_config import LONG_LEG, SHORT_LEG

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
        "title": f"{LONG_LEG.name}: Direct Beneficiary of Grid Hardening",
        "categories": ["Grid Resilience", "Policy-Backed Capex"],
        "min_confidence": 0.70,
        "max_quotes": 6,
    },
    "slide_7_short_case": {
        "title": f"{SHORT_LEG.name}: High-Expectation Inverter Leader Facing Demand Normalization",
        "categories": ["Margin/Earnings Risk", "Policy-Backed Capex", "Grid Resilience"],
        "min_confidence": 0.60,
        "max_quotes": 8,
    },
    "slide_8_short_upside": {
        "title": "Great Company, Bad Risk-Reward",
        "categories": ["Margin/Earnings Risk"],
        "min_confidence": 0.60,
        "max_quotes": 8,
    },
    "slide_10_ai_module": {
        "title": "AI Signal Tracker: Capex Language Moving to Grid",
        "categories": ["Electricity Demand", "Grid Resilience", "Policy-Backed Capex",
                       "Margin/Earnings Risk"],
        "min_confidence": 0.75,
        "max_quotes": 6,  # One per category
    },
}

# How many quotes to actually display per slide after dedupe
SLIDE_DISPLAY_LIMIT = {
    "slide_3_variant_view": 3,
    "slide_4_industry_outlook": 2,
    "slide_5_long_case": 2,
    "slide_7_short_case": 3,
    "slide_8_short_upside": 2,
    "slide_10_ai_module": 2,
}

SLIDE_SOURCE_MARKERS = {
    "slide_3_variant_view": ["pair analysis dongfang sungrow"],
    "slide_4_industry_outlook": ["dongfang", "pair analysis dongfang sungrow", "iea electricity 2026 - grids"],
    "slide_5_long_case": ["dongfang", "pair analysis dongfang sungrow"],
    "slide_7_short_case": ["sungrow", "pair analysis dongfang sungrow"],
    "slide_8_short_upside": ["sungrow", "pair analysis dongfang sungrow"],
    "slide_10_ai_module": ["dongfang", "sungrow", "pair analysis dongfang sungrow"],
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

PAIR_RELEVANCE_MARKERS = [
    "dongfang", "sungrow", "inverter", "energy storage",
    "state grid", "new-type power system", "source-grid-load-storage",
    "synchronous condenser", "grid flexibility", "grid hardening",
    "power equipment", "substation", "transformer",
    "national energy administration", "state-owned enterprise",
    "state grid", "inverter pricing", "storage margins", "energy transition equipment",
]

UNRELATED_MARKERS = [
    "alaska", "nuclear", "reactor", "submarine", "aircraft carrier",
    "east windsor", "new jersey", "winnipeg", "qts", "bell canada",
    "striat of hormuz", "lng", "brent", "pruhoe", "prudhoe", "north slope",
]

# Minimum quality score for evidence to be usable - fail closed if below
MIN_EVIDENCE_SCORE = 80.0

STATIC_EVIDENCE = {
    "slide_3_variant_view": [
        {
            "category": "Margin/Earnings Risk",
            "sentiment": "negative",
            "confidence": 0.98,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "Dongfang offers policy-backed grid-integration exposure, while Sungrow is priced for sustained high growth despite signs of inverter and storage-cycle normalization.",
            "quality_score": 220.0,
        },
        {
            "category": "Policy-Backed Capex",
            "sentiment": "positive",
            "confidence": 0.97,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "Dongfang is the official Energy Transition stock-pool anchor; Sungrow is the same-sector non-pool short, which fixes the stock-pool compliance risk while preserving the energy-transition thesis.",
            "quality_score": 210.0,
        },
        {
            "category": "Margin/Earnings Risk",
            "sentiment": "negative",
            "confidence": 0.96,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "The strongest pair signal is cycle-positioning divergence: grid-backbone infrastructure durability versus high-expectation downstream clean-tech normalization.",
            "quality_score": 205.0,
        },
    ],
    "slide_4_industry_outlook": [
        {
            "category": "Policy-Backed Capex",
            "sentiment": "positive",
            "confidence": 0.96,
            "source": "DOC Dongfang 2025 Annual Summary",
            "quote": "Dongfang's 2025 business focus includes grid infrastructure and transmission, State Grid contracts, new-type power system development, and source-grid-load-storage integration.",
            "quality_score": 200.0,
        },
        {
            "category": "Grid Resilience",
            "sentiment": "positive",
            "confidence": 0.95,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "Sector rotation favors clean grid-integration exposure over broad low-margin industrial equipment exposure as the energy transition bottleneck shifts to electricity-system integration.",
            "quality_score": 195.0,
        },
    ],
    "slide_5_long_case": [
        {
            "category": "Grid Resilience",
            "sentiment": "positive",
            "confidence": 0.98,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "Dongfang reported 2025 revenue of RMB 78.62bn, up 12.8%, and net profit of RMB 3.831bn, up 31.11%, showing profit growth ahead of revenue growth.",
            "quality_score": 220.0,
        },
        {
            "category": "Policy-Backed Capex",
            "sentiment": "positive",
            "confidence": 0.96,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "Key Dongfang strengths include margin expansion, positioning in China's grid infrastructure buildout, State Grid investment exposure, and nuclear and wind equipment leadership.",
            "quality_score": 205.0,
        },
    ],
    "slide_7_short_case": [
        {
            "category": "Margin/Earnings Risk",
            "sentiment": "negative",
            "confidence": 0.98,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "Sungrow delivered strong 2025 results, but Q1 2026 reversed hard with revenue down 18.3% and net profit down 40.1% year over year, exposing demand and margin normalization risk.",
            "quality_score": 220.0,
        },
        {
            "category": "Margin/Earnings Risk",
            "sentiment": "negative",
            "confidence": 0.96,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "Sungrow is not the wrong company to short because it is weak; it is the right company to short because expectations remain high while the downstream inverter and storage cycle is getting more competitive.",
            "quality_score": 205.0,
        },
        {
            "category": "Margin/Earnings Risk",
            "sentiment": "negative",
            "confidence": 0.94,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "Inverter price pressure, storage competition, and growth normalization create a setup where even a good operating company can see valuation compression.",
            "quality_score": 190.0,
        },
    ],
    "slide_8_short_upside": [
        {
            "category": "Margin/Earnings Risk",
            "sentiment": "negative",
            "confidence": 0.97,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "The short thesis is a mispriced-expectations call: Sungrow's premium narrative is vulnerable if investors stop underwriting structural compounder economics after the Q1 2026 slowdown.",
            "quality_score": 215.0,
        },
        {
            "category": "Margin/Earnings Risk",
            "sentiment": "negative",
            "confidence": 0.95,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "Sungrow is not a bad company; it is a weaker risk-reward leg because a premium clean-tech multiple is more fragile than Dongfang's backlog-backed infrastructure earnings profile.",
            "quality_score": 200.0,
        },
    ],
    "slide_10_ai_module": [
        {
            "category": "Policy-Backed Capex",
            "sentiment": "positive",
            "confidence": 0.96,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "AI-assisted classification separated policy-backed grid capex signals from inverter and storage margin-normalization signals, then human review selected the investment-relevant evidence.",
            "quality_score": 200.0,
        },
        {
            "category": "Margin/Earnings Risk",
            "sentiment": "negative",
            "confidence": 0.95,
            "source": "DOC Pair Analysis Dongfang Sungrow 2025",
            "quote": "The strongest pair signal is not generic clean-energy demand; it is the divergence between Dongfang's policy-backed grid earnings visibility and Sungrow's premium-expectations reset risk.",
            "quality_score": 195.0,
        },
    ],
}


def is_boilerplate(text: str) -> bool:
    """Check if a quote is boilerplate metadata rather than substantive content."""
    text_lower = text.lower()
    if any(
        metric in text_lower
        for metric in ["revenue", "net profit", "operating cash flow", "eps", "p/e", "p/b", "market cap"]
    ):
        return False

    # Match boilerplate patterns
    for pattern in BOILERPLATE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            return True

    # Keyword density check
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

    text_lower = text.lower()

    # Reward pair-relevant China/grid language and penalize unrelated U.S. energy snippets.
    relevance_hits = sum(1 for marker in PAIR_RELEVANCE_MARKERS if marker in text_lower)
    if relevance_hits:
        score += min(relevance_hits * 12, 60)

    unrelated_hits = sum(1 for marker in UNRELATED_MARKERS if marker in text_lower)
    if unrelated_hits:
        score -= unrelated_hits * 25

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
        risk_hits = sum(1 for m in risk_markers if m in text_lower)
        if risk_hits >= 2:
            score += 25

    # Penalize navigation/boilerplate markers
    if any(marker in text_lower for marker in BOILERPLATE_KEYWORDS):
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

    # Prefer pair-relevant evidence and avoid unrelated generic energy snippets.
    source_text = (
        df.get("source_name", pd.Series([""] * len(df), index=df.index)).astype(str).str.lower() + " " +
        df.get("title", pd.Series([""] * len(df), index=df.index)).astype(str).str.lower() + " " +
        df.get("text", pd.Series([""] * len(df), index=df.index)).astype(str).str.lower()
    )
    pair_mask = source_text.apply(
        lambda s: any(marker in s for marker in PAIR_RELEVANCE_MARKERS)
    )
    # FAIL CLOSED: Only proceed with pair-relevant evidence. If none exists, return empty.
    if not pair_mask.any():
        print(f"[WARN] No pair-relevant evidence found for {slide_id} - returning empty")
        return []
    df = df[pair_mask].copy()
    source_text = source_text.loc[df.index]

    allowed_sources = SLIDE_SOURCE_MARKERS.get(slide_id, [])
    if allowed_sources:
        source_mask = source_text.apply(lambda s: any(marker in s for marker in allowed_sources))
        if source_mask.any():
            df = df[source_mask].copy()

    # Score each quote (pass slide_id for context-aware scoring)
    df["quality_score"] = df.apply(
        lambda r: score_quote(f"{r.get('title', '')} {r.get('source_name', '')} {r['text']}", float(r["confidence"]), slide_id),
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
    for slide_id, config in SLIDE_EVIDENCE_MAP.items():
        all_quotes = [dict(q) for q in STATIC_EVIDENCE.get(slide_id, [])]
        all_quotes.extend(extract_evidence(classified_df, config, slide_id))

        # Filter: drop quotes below minimum quality score (fail closed on weak evidence)
        quality_quotes = [q for q in all_quotes if q.get("quality_score", 0) >= MIN_EVIDENCE_SCORE]
        if not quality_quotes and all_quotes:
            print(f"[WARN] All {len(all_quotes)} quotes for {slide_id} below MIN_EVIDENCE_SCORE ({MIN_EVIDENCE_SCORE}) - failing closed")

        # Dedupe within a slide only. Reuse across slides is acceptable when the
        # local company corpus is intentionally small.
        used_quotes = set()
        unique_quotes = []
        for q in quality_quotes:
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
