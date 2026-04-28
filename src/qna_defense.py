"""Auto-generate Q&A defense document with evidence citations.

Builds answers to expected judge questions using:
- Classified paragraph evidence
- Valuation numbers
- Signal tracker metrics
- Narrative shift analysis
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Optional


QNA_QUESTIONS = [
    {
        "id": "q1_why_not_long_oil",
        "question": "Q1. Why not long oil if energy logistics are vulnerable?",
        "evidence_categories": ["Margin/Earnings Risk", "Oilfield Cost Pressure"],
        "base_answer": (
            "Because higher oil prices do not automatically create durable earnings upside for "
            "oilfield-service companies. Disruption raises logistics costs, delays projects, and "
            "reduces operating visibility. The more durable response to energy insecurity is "
            "investment in electricity continuity and grid resilience."
        ),
    },
    {
        "id": "q2_why_sieyuan",
        "question": "Q2. Why Sieyuan rather than Dongfang Electric or Yantai Jereh?",
        "evidence_categories": ["Grid Resilience", "Electricity Demand"],
        "base_answer": (
            "Sieyuan offers the cleanest exposure to grid equipment and electricity infrastructure. "
            "Dongfang Electric has broader power-generation exposure including coal/gas/nuclear, "
            "while Yantai Jereh remains connected to oil and gas services. Since the thesis is "
            "about the shift from fuel security to electricity security, Sieyuan is the cleanest long."
        ),
    },
    {
        "id": "q3_why_short_hal",
        "question": "Q3. Why short Halliburton instead of an oil producer?",
        "evidence_categories": ["Oilfield Cost Pressure", "Margin/Earnings Risk"],
        "base_answer": (
            "Oil producers can benefit directly from oil price spikes. Oilfield-service companies "
            "are more exposed to customer capex timing, utilization rates, logistics, and project "
            "execution. That makes them a better short candidate for the view that the market is "
            "over-simplifying the benefit of oil disruption."
        ),
    },
    {
        "id": "q4_what_makes_thesis_wrong",
        "question": "Q4. What would make your thesis wrong?",
        "evidence_categories": [],
        "base_answer": (
            "Three scenarios: (1) Oilfield-service pricing power rises faster than logistics costs, "
            "(2) Upstream capex accelerates significantly with durable margin expansion, "
            "(3) Grid capex is delayed by regulatory bottlenecks. We monitor this through HAL "
            "earnings revisions, HAL margin trends, Sieyuan order backlog, and grid policy announcements."
        ),
    },
    {
        "id": "q5_macro_or_stock",
        "question": "Q5. Is this a macro pitch or a stock pitch?",
        "evidence_categories": [],
        "base_answer": (
            "It starts with a macro dislocation but the trade is stock-specific. Sieyuan has direct "
            "exposure to grid equipment and overseas growth. Halliburton has specific margin and "
            "operating risks. The pair trade isolates the earnings-quality gap within the broader "
            "energy-security theme."
        ),
    },
    {
        "id": "q6_ai_limitations",
        "question": "Q6. How reliable is your text analysis?",
        "evidence_categories": [],
        "base_answer": (
            "The text analysis is a thematic compilation tool, not a predictive system. "
            "It surfaces quotes and organizes 55 documents into categories for human review. "
            "Validation testing shows the classifier relies heavily on keyword patterns — "
            "accuracy against keyword baselines must be tested to claim incremental value. "
            "See validation_report.md for blind-test methodology and predictive power analysis. "
            "Sample size (330 paragraphs) limits statistical confidence."
        ),
    },
    {
        "id": "q7_ai_what_does_it_add",
        "question": "Q7. What does the text analysis add that a traditional analyst could not do?",
        "evidence_categories": [],
        "base_answer": (
            "Three things, with honest limits: (1) Scale: compiles 55 documents quickly, "
            "but manual review of key sources is still required. "
            "(2) Consistency: applies the same categorization framework across all docs, "
            "though keyword-driven consistency differs from semantic understanding. "
            "(3) Evidence trail: every quote has a source link for verification. "
            "Critically: the text analysis is DESCRIPTIVE, not predictive — "
            "it does NOT forecast returns. Signal-return correlation tests confirm this."
        ),
    },
    {
        "id": "q8_valuation_conservative",
        "question": "Q8. How conservative is your valuation?",
        "evidence_categories": [],
        "base_answer": (
            "Scenarios use probability-weighted EPS growth and target multiples anchored to "
            "5-year peer medians. Bear case applies a 15% multiple compression on both legs. "
            "Base case assumes no re-rating — thesis wins purely on EPS differential. "
            "Upside in bull case requires both margin expansion and multiple re-rating."
        ),
    },
]


def load_killer_quotes(evidence_pack_path: Path) -> Dict[str, list]:
    """Load killer quotes from evidence pack JSON.

    Returns dict of category -> list of quotes sorted by score.
    """
    if not evidence_pack_path.exists():
        return {}
    try:
        with open(evidence_pack_path) as f:
            evidence = json.load(f)
        # Flatten all quotes and organize by category
        quotes_by_category = {}
        for slide_id, slide_data in evidence.items():
            for quote in slide_data.get("quotes", []):
                cat = quote.get("category", "Unknown")
                if cat not in quotes_by_category:
                    quotes_by_category[cat] = []
                quotes_by_category[cat].append(quote)

        # Sort each category by score
        for cat in quotes_by_category:
            quotes_by_category[cat].sort(key=lambda x: x.get("score", 0), reverse=True)

        return quotes_by_category
    except Exception as e:
        print(f"[WARN] Could not load evidence pack: {e}")
        return {}


def extract_top_quote(
    df: pd.DataFrame,
    categories: list,
    killer_quotes: Dict[str, list],
    min_words: int = 15
) -> Optional[Dict]:
    """Get the best killer quote from a set of categories.

    Prioritizes:
    1. Killer quotes from evidence pack (pre-filtered, scored)
    2. Quotes with quantification (numbers, percentages)
    3. Minimum word count for substance
    """
    if not categories:
        return None

    # First try killer quotes from evidence pack
    for cat in categories:
        if cat in killer_quotes and killer_quotes[cat]:
            # Get the highest-scoring quote with minimum word count
            for q in killer_quotes[cat]:
                text = q.get("text", "")
                if len(text.split()) >= min_words:
                    return {
                        "text": text[:280],  # Slightly longer for Q&A
                        "source": q.get("source", "Unknown"),
                        "category": cat,
                        "confidence": q.get("confidence", 1.0),
                        "score": q.get("score", 0),
                        "source_type": "killer_quote",
                    }

    # Fallback to classified dataframe
    subset = df[df["category"].isin(categories)] if not df.empty else pd.DataFrame()
    if subset.empty:
        return None

    # Score rows by quantification (numbers = credibility)
    def score_row(row):
        text = str(row.get("text", ""))
        base_score = row.get("confidence", 0.5) * 100
        # Bonus for numbers/percentages
        import re
        if re.search(r'\d+%|\$[\d,.]+|million|billion', text, re.IGNORECASE):
            base_score += 30
        # Bonus for word count
        word_count = len(text.split())
        if 20 <= word_count <= 100:
            base_score += 20
        return base_score

    subset = subset.copy()
    subset["_quality_score"] = subset.apply(score_row, axis=1)
    top = subset.nlargest(1, "_quality_score").iloc[0]

    return {
        "text": str(top.get("text", ""))[:280],
        "source": top.get("title", top.get("source_name", "Unknown")),
        "category": top.get("category", ""),
        "confidence": float(top.get("confidence", 0)),
        "score": float(top.get("_quality_score", 0)),
        "source_type": "classified_data",
    }


def build_qna_doc(
    classified_df: Optional[pd.DataFrame],
    valuation_summary: Optional[Dict],
    narrative_shift: Optional[Dict],
    output_path: Path,
    evidence_pack_path: Optional[Path] = None,
) -> Path:
    """Build the Q&A defense markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load killer quotes from evidence pack
    killer_quotes = {}
    if evidence_pack_path and evidence_pack_path.exists():
        killer_quotes = load_killer_quotes(evidence_pack_path)

    lines = [
        "# Q&A Defense Sheet",
        "## UBS Pitch: Long the Grid, Short the Bottleneck",
        "",
        "*Auto-generated with live evidence citations.*",
        "",
        "---",
        "",
    ]

    # Key numbers upfront
    if valuation_summary or narrative_shift:
        lines.extend([
            "## Key Numbers to Memorize",
            "",
        ])
        if valuation_summary:
            lines.extend([
                f"- **Long Sieyuan expected return**: {valuation_summary.get('long_expected_return', 'N/A')}%",
                f"- **Short HAL expected move**: {valuation_summary.get('short_expected_return', 'N/A')}%",
                f"- **Pair spread return**: {valuation_summary.get('pair_spread_return', 'N/A')}%",
            ])
        if narrative_shift:
            lines.extend([
                f"- **Total AI signals analyzed**: {narrative_shift.get('total_signals', 0)}",
                f"- **Grid signal share**: {narrative_shift.get('grid_signal_share', 0)*100:.0f}%",
                f"- **Oil signal share**: {narrative_shift.get('oil_signal_share', 0)*100:.0f}%",
                f"- **Thesis support score**: {narrative_shift.get('thesis_support_score', 0)}",
                f"- **Interpretation**: {narrative_shift.get('interpretation', 'N/A')}",
            ])
        lines.extend(["", "---", ""])

    # Questions
    for q in QNA_QUESTIONS:
        lines.extend([
            f"## {q['question']}",
            "",
            f"**Answer:** {q['base_answer']}",
            "",
        ])

        # Add evidence citation if available
        if classified_df is not None and not classified_df.empty and q["evidence_categories"]:
            quote = extract_top_quote(classified_df, q["evidence_categories"], killer_quotes)
            if quote:
                lines.extend([
                    "**Supporting Evidence:**",
                    "",
                    f"> \"{quote['text']}\"",
                    "",
                    f"— Source: *{quote['source']}* | Category: `{quote['category']}` | Confidence: {quote['confidence']:.2f}",
                    "",
                ])

        lines.append("---")
        lines.append("")

    # Killer quotes appendix
    if classified_df is not None and not classified_df.empty:
        lines.extend([
            "## Appendix: Top Evidence Quotes by Category",
            "",
        ])
        for cat in [
            "Electricity Demand", "Grid Resilience", "Policy-Backed Capex",
            "Oil Supply Disruption", "Oilfield Cost Pressure", "Margin/Earnings Risk",
        ]:
            cat_df = classified_df[classified_df["category"] == cat]
            if not cat_df.empty:
                top = cat_df.nlargest(1, "confidence").iloc[0]
                lines.extend([
                    f"### {cat}",
                    "",
                    f"> \"{str(top.get('text', ''))[:250]}\"",
                    "",
                    f"— {top.get('title', 'Unknown')} | conf {top.get('confidence', 0):.2f}",
                    "",
                ])

    output_path.write_text("\n".join(lines))
    print(f"[SAVED] Q&A defense: {output_path}")
    return output_path


if __name__ == "__main__":
    from src.config import CLASSIFIED_PARAGRAPHS_PATH, PROCESSED_DIR
    from src.analysis import narrative_shift_analysis

    # Load data
    classified_df = None
    if CLASSIFIED_PARAGRAPHS_PATH.exists():
        try:
            classified_df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
        except pd.errors.EmptyDataError:
            pass

    narrative = None
    if classified_df is not None and not classified_df.empty:
        narrative = narrative_shift_analysis(classified_df)

    # Load valuation
    valuation_summary = None
    pair_path = PROCESSED_DIR / "valuation" / "pair_trade_summary.csv"
    if pair_path.exists():
        pair = pd.read_csv(pair_path).iloc[0].to_dict()
        valuation_summary = {
            "long_expected_return": pair.get("long_expected_return_pct", 0),
            "short_expected_return": pair.get("short_expected_move_pct", 0),
            "pair_spread_return": pair.get("pair_spread_return_pct", 0),
        }

    output = Path(__file__).parent.parent / "docs" / "qna_defense.md"
    evidence_pack = PROCESSED_DIR.parent / "outputs" / "tables" / "evidence_pack.json"
    build_qna_doc(classified_df, valuation_summary, narrative, output, evidence_pack)
