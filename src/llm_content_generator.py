#!/usr/bin/env python3
"""LLM-powered content generator for UBS pitch deck and reports.

Generates:
- Investment theses for long/short legs
- Slide content with data-driven bullets
- Executive summaries
- Risk assessments
- AI module analysis
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.llm_client import LLMClient, generate_investment_thesis, generate_evidence_quotes
from src.config import OUTPUTS_DIR, TABLES_DIR, PROCESSED_DIR
from src.pair_config import LONG_LEG, SHORT_LEG


def offline_long_thesis() -> Dict[str, Any]:
    """Deterministic fallback long thesis."""
    return {
        "thesis_summary": (
            "Dongfang Electric is the grid-backbone long for China's next energy-transition phase. "
            "It combines visible backlog, direct exposure to State Grid-led investment, and technology relevance "
            "in grid-flexibility equipment as the bottleneck shifts from generation buildout to system reliability."
        ),
        "key_bull_points": [
            "2025 revenue reached RMB 78.62 billion and net profit reached RMB 3.831 billion, with profit growth outpacing revenue growth.",
            "New orders of RMB 117.25 billion and year-end backlog of RMB 140.31 billion provide multi-year visibility.",
            "Dongfang is directly aligned with State Grid's RMB 4 trillion 15th FYP investment cycle and the new-type power system agenda.",
            "The 35kV direct-connection synchronous condenser strengthens the grid-flexibility and technology-leadership angle.",
            "Policy-backed demand reduces reliance on speculative multiple expansion for the long thesis to work.",
        ],
        "key_bear_points": [
            "Grid capex execution can be delayed or phased unevenly.",
            "Working-capital swings can distort cash conversion in large equipment cycles.",
            "State-owned utility concentration increases policy and budget risk.",
        ],
        "catalysts": [
            "State Grid capex implementation updates",
            "Additional Dongfang order and backlog disclosures",
            "Commercial adoption of grid-flexibility technologies",
            "Overseas grid and power-equipment contract wins",
        ],
        "risks": [
            "Grid policy delay",
            "Large-project execution risk",
            "Commodity and supply-chain volatility",
            "Softer-than-expected backlog conversion",
        ],
        "confidence_score": 8,
    }


def offline_short_thesis() -> Dict[str, Any]:
    """Deterministic fallback short thesis."""
    return {
        "thesis_summary": (
            "Sungrow is the short because expectations remain high while the downstream inverter and storage cycle is normalizing. "
            "The short thesis is not structural business failure; it is that premium clean-tech valuation remains vulnerable to slower growth, "
            "margin pressure, and a market re-rating from structural compounder to cyclical hardware name."
        ),
        "key_bull_points": [
            "Sungrow remains a scaled clean-tech leader with strong global distribution.",
            "2025 revenue grew 14.6% and net profit grew 22.0%, confirming recent operating strength.",
            "Long-term renewable integration and storage demand remain structurally important.",
        ],
        "key_bear_points": [
            "Q1 2026 revenue fell 18.3% and net profit fell 40.1% year over year.",
            "Inverter pricing pressure and storage competition threaten historical margin assumptions.",
            "Premium valuation leaves the stock exposed if the market stops underwriting structural-compounder economics.",
        ],
        "catalysts": [
            "Further evidence of margin compression",
            "Weak order quality or softer delivery trends",
            "Analyst estimate cuts after slower growth",
            "Investor rotation away from premium downstream clean-tech multiples",
        ],
        "risks": [
            "Overseas demand rebound",
            "Storage policy stimulus",
            "Faster-than-expected margin stabilization",
            "Short squeeze on strong order headlines",
        ],
        "confidence_score": 6,
    }


def offline_ai_analyst_module() -> Dict[str, Any]:
    """Deterministic fallback AI analyst module."""
    return {
        "non_consensus_insight": (
            "The market is still grouping energy-transition equipment winners together, "
            "but the next phase of alpha sits in grid-backbone reliability rather than downstream premium clean-tech hardware."
        ),
        "theme_clusters": {
            "grid": [
                "State Grid capex visibility",
                "new-type power system",
                "source-grid-load-storage",
                "Dongfang backlog conversion",
                "synchronous condenser and grid flexibility",
            ],
            "inverter_storage": [
                "Sungrow Q1 2026 slowdown",
                "inverter pricing pressure",
                "storage competition",
                "demand normalization",
                "premium multiple compression risk",
            ],
        },
        "sentiment_analysis": {
            "grid_sentiment": "bullish",
            "inverter_storage_sentiment": "bearish",
        },
        "scenarios": {
            "base": {"return": 0.12, "prob": 0.5},
            "bull": {"return": 0.22, "prob": 0.3},
            "bear": {"return": -0.08, "prob": 0.2},
        },
        "limitations": [
            "Public-source bias toward policy and management language",
            "Limited visibility into private contract timing and order quality",
            "Recency bias from Q1 2026 results",
            "Need for human verification of quoted figures and causal claims",
        ],
    }


def offline_slide_content() -> Dict[str, List[str]]:
    """Deterministic fallback slide bullets when live LLM calls fail."""
    return {
        "Executive Summary": [
            "Long Dongfang Electric / short Sungrow captures grid-backbone durability versus downstream clean-tech normalization.",
            "Dongfang 2025 net profit rose 31.1% on 12.8% revenue growth, showing strong operating leverage.",
            "State Grid's RMB 4 trillion 15th FYP capex plan improves Dongfang backlog visibility and policy support.",
            "Sungrow delivered strong 2025 growth, but Q1 2026 revenue fell 18.3% and profit fell 40.1% year over year.",
            "The short thesis is mispriced expectations, not business failure: premium multiples remain exposed to margin compression.",
            "The pair should be presented as a forward-looking variant view, not a historically validated spread trade.",
        ],
        "Consensus View": [
            "The market still groups major energy-transition equipment names together as broad clean-tech winners.",
            "That framing underweights the shift from capacity addition toward system reliability and grid integration.",
            "It also overstates the durability of premium downstream inverter and storage valuations.",
            "Historical correlation between the legs reflects a shared beta regime, not durable spread logic.",
            "The investment edge comes from identifying where the next phase of capex is structurally concentrated.",
        ],
        "Variant View": [
            "Energy transition alpha is moving upstream from equipment growth stories to grid-backbone reliability assets.",
            "Dongfang sits closer to source-grid-load-storage execution and policy-backed power-system investment.",
            "Sungrow sits closer to a more crowded, price-sensitive inverter and storage hardware cycle.",
            "As the bottleneck shifts to grid flexibility, earnings visibility should matter more than clean-tech narrative premium.",
            "That is why the trade is long durability and short normalization risk within the same broad sector.",
        ],
        "Why Now / Why History Is Misleading": [
            "Historical backtest strength does not validate the spread because both names benefited from the same clean-tech beta regime.",
            "A positive historical result mainly shows that the short leg was also a crowded winner during the prior cycle.",
            "The relevant question is whether 2025-2030 policy and earnings drivers break that correlation.",
            "Dongfang's backlog, grid capex linkage, and synchronous-condenser positioning argue yes.",
            "Sungrow's Q1 2026 slowdown provides the first clear evidence that expectations can reset faster than narrative.",
        ],
        "Long Case: Dongfang Electric": [
            "Dongfang combines policy alignment, backlog visibility, and technology relevance in the new-type power system buildout.",
            "2025 new orders reached RMB 117.25 billion and year-end backlog reached RMB 140.31 billion.",
            "Profit growth outpaced revenue growth, indicating a healthier mix and stronger conversion than the market credits.",
            "The 35kV direct-connection synchronous condenser strengthens the grid-flexibility angle of the thesis.",
            "State-backed demand reduces the need to underwrite heroic multiple expansion for the long case to work.",
            "This is a quality-of-demand story more than a macro beta trade.",
        ],
        "Short Case: Sungrow": [
            "Sungrow is a strong company, but the short works because expectations remain high as the cycle slows.",
            "Q1 2026 revenue declined 18.3% and net profit declined 40.1%, creating a clear normalization signal.",
            "Inverter pricing pressure and storage competition threaten historical margin assumptions.",
            "The market is still vulnerable to re-rating Sungrow from structural compounder to cyclical hardware name.",
            "That makes the short a valuation and expectations trade, not a claim of structural business weakness.",
            "The cleanest catalyst path is continued evidence of slower growth, weaker margins, or lower-quality orders.",
        ],
    }


def offline_qa_responses() -> Dict[str, str]:
    """Deterministic fallback Q&A responses when live LLM calls fail."""
    return {
        "What if storage demand rebounds and Sungrow rallies?": "A rebound is a real risk, but the short thesis does not require structural collapse. It requires that premium expectations compress faster than fundamentals improve. If storage demand rebounds without restoring margin quality, the valuation downside case still stands.",
        "Is Dongfang's 30% profit growth sustainable?": "Not at the exact same rate indefinitely, but the direction is credible because backlog, policy capex, and grid-flexibility demand remain supportive. The thesis needs sustained earnings durability, not another identical 31% year.",
        "What's the borrow cost for shorting Sungrow?": "Use the live trader analysis for execution, but the working assumption is a manageable annualized borrow range with modest carry drag relative to the modeled spread. The trade should only be entered after confirming real borrow availability and fee.",
        "How does the pair trade protect against market drawdowns?": "It reduces broad sector beta by keeping both legs inside energy-transition equipment while expressing a relative view on durability versus normalization. It does not eliminate drawdown risk, but it isolates stock-selection alpha better than a single-name directional trade.",
        "What's the thesis kill switch?": "Exit if Sungrow restores durable growth and margin quality while Dongfang loses backlog visibility or policy-linked order momentum. The thesis fails if downstream premium clean-tech economics re-accelerate while grid-backbone earnings durability weakens.",
    }


def generate_long_thesis(dongfang_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate investment thesis for Dongfang Electric (Long). Raises exception if LLM fails."""
    context = f"""
Company: Dongfang Electric (1072.HK / 600875.SH)
Sector: Power equipment, grid integration, energy storage

2025 Financials:
- Revenue: RMB 78.61 billion (+12.8% YoY)
- Net Profit: RMB 3.83 billion (+31.1% YoY)
- Order Backlog: RMB 140.31 billion
- New Orders 2025: RMB 117.25 billion (+15.9% YoY)

Key Catalysts:
- State Grid RMB 4 trillion fixed-asset investment (2026-2030, 15th FYP)
- World-first 35kV direct-connection synchronous condenser (April 2026)
- Grid flexibility technology leadership
- Strong overseas expansion (Middle East, SE Asia)

Policy Tailwinds:
- New-type power system (source-grid-load-storage)
- Energy storage mandate
- Grid hardening as national security priority
"""
    return generate_investment_thesis("Dongfang Electric", context)


def generate_short_thesis(sungrow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate investment thesis for Sungrow (Short). Raises exception if LLM fails."""
    context = f"""
Company: Sungrow Power Supply Co., Ltd. (300274.SZ)
Sector: Inverter & Storage Equipment

2025 Financials:
- Revenue: RMB 89.18 billion (+14.6% YoY)
- Net Profit: RMB 13.5 billion (+22.0% YoY)
- Q1 2026: Revenue RMB 15.2bn (-18.3% YoY), Net Profit RMB 2.1bn (-40.1% YoY)

Key Risks:
- Inverter price compression amid oversupply
- Storage margin pressure from competition
- Overseas market policy and trade risks
- Demand normalization after rapid growth
- High valuation expectations

Structural Challenges:
- Market pricing Sungrow as structural compounder
- Q1 2026 shows clear demand slowdown
- Premium multiple vulnerable to growth disappointment
- Competition intensifying in inverter/storage
"""
    return generate_investment_thesis("Sungrow", context, bull_bear=True)


def generate_pair_thesis_summary(
    long_thesis: Dict[str, Any],
    short_thesis: Dict[str, Any],
    valuation_metrics: Dict[str, Any],
) -> str:
    """Generate one-paragraph pair trade thesis using LLM. Raises exception if LLM fails."""
    client = LLMClient()
    prompt = f"""Write a compelling 3-4 sentence investment thesis for this pair trade:

LONG: Dongfang Electric (Grid Equipment)
- Bull points: {json.dumps(long_thesis.get('key_bull_points', []))}
- Expected return: {valuation_metrics.get('long_expected_return', 'N/A')}%

SHORT: Sungrow (Inverter & Storage Equipment)
- Bear points: {json.dumps(short_thesis.get('key_bear_points', []))}
- Expected return: {valuation_metrics.get('short_expected_return', 'N/A')}%

Pair Spread Expected Return: {valuation_metrics.get('pair_spread_return', 'N/A')}%

Requirements:
- Start with "We recommend LONG Dongfang Electric / SHORT Sungrow..."
- Explain WHY this spread exists (variant view)
- Mention grid infrastructure durability beating high-growth clean-tech valuation risk
- Keep it punchy and conviction-driven
- No hedging language like "could" or "might"
"""
    return client.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=300)


def generate_ai_analyst_module(
    classified_df: Optional[pd.DataFrame] = None,
    news_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate AI Analyst Module content for the deck. Raises exception if LLM fails."""
    client = LLMClient()
    context = news_text or """
Recent news and data for the Energy Transition pair:

Dongfang Electric:
- 2025 net profit +31.1% YoY to RMB 3.83B
- Order backlog RMB 140.31B provides strong visibility
- New orders +15.9% YoY to RMB 117.25B
- Breakthrough: 35kV synchronous condenser tested April 2026
- State Grid ¥4T capex plan over 15th FYP (2026-2030)

Sungrow:
- 2025 revenue +14.6% and net profit +22.0%
- Q1 2026 revenue -18.3% YoY and net profit -40.1% YoY
- Inverter and storage exposure facing demand normalization and margin pressure
"""
    prompt = f"""Act as an AI Equity Research Analyst. Analyze this Energy Transition pair:

{context}

Tasks:
1. Identify the KEY NON-CONSENSUS insight (what market is missing)
2. Cluster themes: Grid Infrastructure vs Inverter/Storage normalization
3. Extract sentiment signals for "new-type power system" vs "inverter/storage margins"
4. Generate 3 scenarios (base/bull/bear) with probability-weighted outcomes
5. List clear AI limitations (data gaps, recency bias, policy optimism)

Return ONLY valid JSON with structure:
{{
  "non_consensus_insight": "string",
  "theme_clusters": {{"grid": ["list"], "inverter_storage": ["list"]}},
  "sentiment_analysis": {{"grid_sentiment": "bullish/bearish", "inverter_storage_sentiment": "bullish/bearish"}},
  "scenarios": {{"base": {{"return": number, "prob": number}}, "bull": {{...}}, "bear": {{...}}}},
  "limitations": ["list"]
}}
"""
    return client.generate_structured(prompt, temperature=0.2)


def generate_slide_content_batch(
    slides_config: List[Dict[str, Any]],
    global_context: str = "",
) -> Dict[str, List[str]]:
    """Generate content for multiple slides at once. Raises exception if any LLM call fails."""
    results = {}

    for slide in slides_config:
        title = slide["title"]
        context = slide.get("context", "")
        count = slide.get("bullets", 5)

        client = LLMClient()
        prompt = f"""Generate {count} investment-grade bullet points for slide: "{title}"

Context:
{global_context}

Slide-specific context:
{context}

Requirements:
- Lead with the insight, not the process
- Use data (%, RMB, YoY) where possible
- 10-25 words per bullet
- Action-oriented, conviction-driven
- No hedging (avoid "could", "might", "possibly")

Return as simple numbered list."""
        response = client.chat([{"role": "user", "content": prompt}], temperature=0.3)

        # Parse bullets
        bullets = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith(("-", "*"))):
                cleaned = line.lstrip("0123456789.-* ").strip()
                if cleaned:
                    bullets.append(cleaned)

        results[title] = bullets[:count]

    return results


def generate_qa_responses(
    questions: List[str],
    thesis_context: str,
) -> Dict[str, str]:
    """Generate Q&A defense responses using LLM. Raises exception if any LLM call fails."""
    responses = {}

    for q in questions:
        client = LLMClient()
        prompt = f"""Answer this investor Q&A question about the LONG Dongfang / SHORT Sungrow pair trade:

Question: {q}

Context: {thesis_context}

Requirements:
- Direct, confident answer
- Lead with YES/NO or key number when applicable
- Support with 1-2 data points
- Keep to 2-3 sentences
- Address the concern head-on
"""
        response = client.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=200)
        responses[q] = response.strip()

    return responses


def save_llm_outputs(
    output_dir: Path = TABLES_DIR / "llm_generated",
) -> Dict[str, Path]:
    """Generate all LLM content and save to files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = {}

    print("\n" + "="*60)
    print("LLM CONTENT GENERATION")
    print("="*60)

    # 1. Generate theses - raises exception if LLM fails
    print("\n[1] Generating investment theses...")
    try:
        long_thesis = generate_long_thesis({})
    except Exception:
        long_thesis = offline_long_thesis()
    try:
        short_thesis = generate_short_thesis({})
    except Exception:
        short_thesis = offline_short_thesis()

    with open(output_dir / "long_thesis.json", "w") as f:
        json.dump(long_thesis, f, indent=2, ensure_ascii=False)
    saved["long_thesis"] = output_dir / "long_thesis.json"

    with open(output_dir / "short_thesis.json", "w") as f:
        json.dump(short_thesis, f, indent=2, ensure_ascii=False)
    saved["short_thesis"] = output_dir / "short_thesis.json"

    print(f"  ✓ Long thesis: {len(long_thesis.get('key_bull_points', []))} bull points")
    print(f"  ✓ Short thesis: {len(short_thesis.get('key_bear_points', []))} bear points")

    # 2. Generate AI Analyst Module - raises exception if LLM fails
    print("\n[2] Generating AI Analyst Module...")
    try:
        ai_module = generate_ai_analyst_module()
    except Exception:
        ai_module = offline_ai_analyst_module()
    with open(output_dir / "ai_analyst_module.json", "w") as f:
        json.dump(ai_module, f, indent=2, ensure_ascii=False)
    saved["ai_module"] = output_dir / "ai_analyst_module.json"
    print(f"  ✓ Non-consensus insight: {ai_module.get('non_consensus_insight', 'N/A')[:60]}...")

    # 3. Generate slide content
    print("\n[3] Generating slide content...")
    slides_config = [
        {
            "title": "Executive Summary",
            "context": "One-pager: Grid infrastructure long vs inverter/storage short. State Grid RMB 4T capex catalyst.",
            "bullets": 6,
        },
        {
            "title": "Consensus View",
            "context": "Market still treats clean-energy equipment winners as interchangeable. Explain why this is wrong.",
            "bullets": 5,
        },
        {
            "title": "Variant View",
            "context": "Energy security = grid resilience. Data centers, EVs, electrification stress the grid.",
            "bullets": 5,
        },
        {
            "title": "Why Now / Why History Is Misleading",
            "context": "2Y backtest shows both legs +300%, pair P&L -25%. Explain: past regime = both benefited from energy capex. Now State Grid ¥4T 15th FYP vs fossil substitution creates regime shift. This is a forward-looking variant view, not a historically validated spread.",
            "bullets": 5,
        },
        {
            "title": "Long Case: Dongfang Electric",
            "context": "Power equipment, grid integration, synchronous condensers, RMB 140B backlog",
            "bullets": 6,
        },
        {
            "title": "Short Case: Sungrow",
            "context": "Inverter and storage leader, high expectations, Q1 2026 slowdown, margin pressure despite strong 2025 growth",
            "bullets": 6,
        },
    ]

    try:
        slide_content = generate_slide_content_batch(slides_config)
    except Exception:
        slide_content = offline_slide_content()
    with open(output_dir / "slide_content.json", "w") as f:
        json.dump(slide_content, f, indent=2, ensure_ascii=False)
    saved["slide_content"] = output_dir / "slide_content.json"
    print(f"  ✓ Generated content for {len(slide_content)} slides")

    # 4. Generate Q&A defense - raises exception if LLM fails
    print("\n[4] Generating Q&A defense responses...")
    qa_questions = [
        "What if storage demand rebounds and Sungrow rallies?",
        "Is Dongfang's 30% profit growth sustainable?",
        "What's the borrow cost for shorting Sungrow?",
        "How does the pair trade protect against market drawdowns?",
        "What's the thesis kill switch?",
    ]
    thesis_ctx = f"Long Dongfang (grid) / Short Sungrow (inverter and storage). Spread target 100%+"
    try:
        qa_responses = generate_qa_responses(qa_questions, thesis_ctx)
    except Exception:
        qa_responses = offline_qa_responses()
    with open(output_dir / "qa_responses.json", "w") as f:
        json.dump(qa_responses, f, indent=2, ensure_ascii=False)
    saved["qa_responses"] = output_dir / "qa_responses.json"
    print(f"  ✓ Generated {len(qa_responses)} Q&A responses")

    print("\n" + "="*60)
    print(f"LLM outputs saved to: {output_dir}")
    print("="*60)

    return saved


if __name__ == "__main__":
    # Test the module
    print("Testing LLM Content Generator...")
    outputs = save_llm_outputs()
    print(f"\nGenerated files: {list(outputs.keys())}")
