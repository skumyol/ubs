"""Auto-generate Q&A defense document with evidence citations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from src.pair_config import LONG_LEG, SHORT_LEG

PAIR_MARKERS = [
    "dongfang", "jereh", "china", "state grid", "grid", "transmission",
    "substation", "transformer", "switchgear", "power equipment",
]

UNRELATED_MARKERS = [
    "halliburton", "schlumberger", "slb", "baker hughes", "nov",
    "alaska", "nuclear", "reactor", "winnipeg", "east windsor", "qts",
]


QNA_QUESTIONS = [
    {
        "question": "The 2-year backtest shows pair P&L of -25.3%. Why is the backtest unfavorable?",
        "base_answer": (
            "The unfavorable backtest is not a flaw — it is the core of our variant view. "
            "In 2021-2024, both legs benefited from a unified energy capex boom where oil and green capex moved together. "
            "This produced positive correlation (+0.83) and both stocks rallied +300%. "
            "The 15th Five-Year Plan decouples grid infrastructure (RMB 4T State Grid investment) from fossil fuel capex. "
            "We are betting on the BREAKDOWN of this historical correlation via policy-driven divergence, not its continuation. "
            "This is a forward-looking regime shift trade, not a historically validated statistical arbitrage."
        ),
    },

    {
        "question": "Q1. Why not long oil if energy logistics are vulnerable?",
        "base_answer": (
            "Because higher oil prices do not automatically create durable earnings upside for "
            "oilfield-service companies. Disruption raises logistics costs, delays projects, and "
            "reduces operating visibility. The more durable response to energy insecurity is "
            "investment in electricity continuity and grid resilience."
        ),
    },
    {
        "question": "Q2. Why Dongfang Electric rather than another grid stock?",
        "base_answer": (
            "Dongfang gives direct exposure to grid integration, transmission equipment, storage, "
            "and flexibility buildout tied to China's new-type power system. It combines policy "
            "support, visible order backlog, and a catalyst-rich technology story that is more "
            "specific than a generic electrification basket."
        ),
    },
    {
        "question": "Q3. Why short Yantai Jereh instead of an oil producer?",
        "base_answer": (
            "Oil producers can benefit directly from oil price spikes. Oilfield-service companies "
            "are more exposed to customer capex timing, utilization rates, logistics, and project "
            "execution. That makes them a better short candidate for the view that the market is "
            "over-simplifying the benefit of oil disruption."
        ),
    },
    {
        "question": "Q4. What would make your thesis wrong?",
        "base_answer": (
            "Three scenarios: (1) oilfield-service pricing power rises faster than logistics costs, "
            "(2) upstream capex accelerates significantly with durable margin expansion, "
            "(3) grid capex is delayed by regulatory bottlenecks. We monitor this through "
            f"{LONG_LEG.name} order backlog, {SHORT_LEG.name} margin trends, and policy announcements."
        ),
    },
    {
        "question": "Q5. Is this a macro pitch or a stock pitch?",
        "base_answer": (
            "It starts with a macro dislocation but the trade is stock-specific. Dongfang has direct "
            "exposure to grid equipment and overseas growth. Yantai Jereh has specific margin and "
            "operating risks. The pair trade isolates the earnings-quality gap within the broader "
            "energy-transition theme."
        ),
    },
    {
        "question": "Q6. How reliable is your text analysis?",
        "base_answer": (
            "The text analysis is reliable as a structured empirical input, not as an autonomous "
            "trading model. It surfaces quotes, organizes documents into categories, and feeds the "
            "predictive scorecard alongside fundamentals, valuation, technicals, and catalysts. "
            "Human review still separates durable signal from narrative noise."
        ),
    },
    {
        "question": "Q7. What does the text analysis add that a traditional analyst could not do?",
        "base_answer": (
            "Three things: scale, consistency, and traceability. It compiles documents quickly, "
            "applies the same categorization framework across all docs, and preserves a source trail "
            "for every quote. The predictive contribution is not magic forecasting; it is a repeatable "
            "way to convert messy policy and company text into scored inputs for the forward thesis."
        ),
    },
    {
        "question": "Q8. How conservative is your valuation?",
        "base_answer": (
            "Scenarios use probability-weighted EPS growth and target multiples anchored to peer "
            "ranges. The base case assumes the thesis works through earnings and backlog visibility, "
            "not heroic multiple expansion. Bull case requires both operating delivery and a partial "
            "re-rating."
        ),
    },
]


def load_killer_quotes(evidence_pack_path: Path) -> Dict[str, list]:
    if not evidence_pack_path.exists():
        return {}
    try:
        with open(evidence_pack_path, encoding="utf-8") as f:
            evidence = json.load(f)
        quotes_by_category: Dict[str, list] = {}
        for slide_data in evidence.values():
            for quote in slide_data.get("quotes", []):
                cat = quote.get("category", "Unknown")
                quote_text = quote.get("text") or quote.get("quote") or ""
                text = f"{quote_text} {quote.get('source', '')}".lower()
                if not text.strip():
                    continue
                if any(marker in text for marker in UNRELATED_MARKERS):
                    continue
                if not any(marker in text for marker in PAIR_MARKERS):
                    continue
                quotes_by_category.setdefault(cat, []).append(quote)
        for cat in quotes_by_category:
            quotes_by_category[cat].sort(key=lambda x: x.get("quality_score", x.get("score", 0)), reverse=True)
        return quotes_by_category
    except Exception as exc:
        print(f"[WARN] Could not load evidence pack: {exc}")
        return {}


def extract_top_quote(
    df: pd.DataFrame,
    categories: list,
    killer_quotes: Dict[str, list],
    min_words: int = 15,
) -> Optional[Dict]:
    if not categories:
        return None

    for cat in categories:
        if cat in killer_quotes and killer_quotes[cat]:
            for q in killer_quotes[cat]:
                text = q.get("text") or q.get("quote") or ""
                if len(text.split()) >= min_words:
                    return {
                        "text": text[:280],
                        "source": q.get("source", "Unknown"),
                        "category": cat,
                        "confidence": q.get("confidence", 1.0),
                        "score": q.get("score", 0),
                        "source_type": "killer_quote",
                    }

    subset = df[df["category"].isin(categories)] if not df.empty else pd.DataFrame()
    if subset.empty:
        return None

    def score_row(row):
        text = str(row.get("text", ""))
        source_text = f"{row.get('title', '')} {row.get('source_name', '')} {text}".lower()
        if any(marker in source_text for marker in UNRELATED_MARKERS):
            return -1000
        base_score = float(row.get("confidence", 0.5)) * 100
        if any(marker in source_text for marker in PAIR_MARKERS):
            base_score += 80
        else:
            return -1000
        if any(token in text.lower() for token in ["%", "$", "million", "billion"]):
            base_score += 30
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    killer_quotes = load_killer_quotes(evidence_pack_path) if evidence_pack_path and evidence_pack_path.exists() else {}

    lines = [
        "# Q&A Defense Sheet",
        f"## UBS Pitch: Long {LONG_LEG.name}, Short {SHORT_LEG.name}",
        "",
        "*Auto-generated with live evidence citations.*",
        "",
        "---",
        "",
    ]

    if valuation_summary or narrative_shift:
        lines.extend(["## Key Numbers to Memorize", ""])
        if valuation_summary:
            lines.extend(
                [
                    f"- **Long {LONG_LEG.name} expected return**: {valuation_summary.get('long_expected_return', 'N/A')}%",
                    f"- **Short {SHORT_LEG.name} expected move**: {valuation_summary.get('short_expected_return', 'N/A')}%",
                    f"- **Pair spread return**: {valuation_summary.get('pair_spread_return', 'N/A')}%",
                ]
            )
        if narrative_shift:
            lines.extend(
                [
                    f"- **Total AI signals analyzed**: {narrative_shift.get('total_signals', 0)}",
                    f"- **Grid signal share**: {narrative_shift.get('grid_signal_share', 0)*100:.0f}%",
                    f"- **Oil signal share**: {narrative_shift.get('oil_signal_share', 0)*100:.0f}%",
                    f"- **Thesis support score**: {narrative_shift.get('thesis_support_score', 0)}",
                    f"- **Interpretation**: {narrative_shift.get('interpretation', 'N/A')}",
                ]
            )
        lines.extend(["", "---", ""])

    for q in QNA_QUESTIONS:
        lines.extend([f"## {q['question']}", "", f"**Answer:** {q['base_answer']}", ""])
        lines.extend(["**Supporting Evidence:**", ""])

        if classified_df is not None and not classified_df.empty:
            if "category" in classified_df.columns:
                categories = []
                if "grid" in q["question"].lower() or "dongfang" in q["question"].lower():
                    categories = ["Grid Resilience", "Electricity Demand", "Policy-Backed Capex"]
                elif "jereh" in q["question"].lower() or "oil" in q["question"].lower():
                    categories = ["Oil Supply Disruption", "Oilfield Cost Pressure", "Margin/Earnings Risk"]
                else:
                    categories = []

                top = extract_top_quote(classified_df, categories, killer_quotes) if categories else None
                if top:
                    lines.extend(
                        [
                            f'> "{top["text"]}"',
                            "",
                            f"— Source: *{top['source']}* | Category: `{top['category']}` | Confidence: {top['confidence']:.2f}",
                        ]
                    )
                else:
                    lines.append("_No specific quote selected for this question._")
            else:
                lines.append("_Classification data does not contain category labels._")
        else:
            lines.append("_No classification data available._")

        lines.extend(["", "---", ""])

    lines.extend(
        [
            "## Appendix: Top Evidence Quotes by Category",
            "",
        ]
    )
    for category in sorted(killer_quotes.keys()):
        if not killer_quotes[category]:
            continue
        top = killer_quotes[category][0]
        text = top.get("text", "")
        text = text or top.get("quote", "")
        source = top.get("source", "Unknown")
        if not text.strip() or any(marker in f"{text} {source}".lower() for marker in UNRELATED_MARKERS):
            continue
        lines.extend(
            [
                f"### {category}",
                "",
                f'> "{text[:300]}"',
                "",
                f"— {source} | conf {top.get('confidence', 0):.2f}",
                "",
            ]
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVED] Q&A defense: {output_path}")
    return output_path


if __name__ == "__main__":
    build_qna_doc(None, None, None, Path("docs/qna_defense.md"))
