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


def generate_short_thesis(jereh_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate investment thesis for Yantai Jereh (Short). Raises exception if LLM fails."""
    context = f"""
Company: Yantai Jereh (002353.SZ)
Sector: Oilfield services, fracturing equipment, drilling

2025 Financials:
- Revenue: RMB 16.22 billion (+21.5% YoY)
- Net Profit: RMB 2.68 billion (+2.0% YoY) - much slower than revenue
- Q1 2026: Revenue RMB 3.29B (+22.5%), Net Profit RMB 590M (+26.3%)

Key Risks:
- Heavy exposure to fossil oilfield services
- Cyclical industry with overcapacity cuts
- Policy headwinds: fossil substitution acceleration
- Margin compression despite revenue growth

Structural Challenges:
- China's clean energy transition away from fossil fuels
- OFS sector dependent on volatile upstream capex
- Less strategic than grid infrastructure in policy priorities
"""
    return generate_investment_thesis("Yantai Jereh", context, bull_bear=True)


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

SHORT: Yantai Jereh (Oilfield Services)
- Bear points: {json.dumps(short_thesis.get('key_bear_points', []))}
- Expected return: {valuation_metrics.get('short_expected_return', 'N/A')}%

Pair Spread Expected Return: {valuation_metrics.get('pair_spread_return', 'N/A')}%

Requirements:
- Start with "We recommend LONG Dongfang Electric / SHORT Yantai Jereh..."
- Explain WHY this spread exists (variant view)
- Mention the RMB 4 trillion State Grid catalyst
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

Yantai Jereh:
- 2025 revenue +21.5% but profit only +2% (margin pressure)
- Q1 2026 showing improvement but cyclical risks remain
- Oilfield services exposure vs clean energy transition
"""
    prompt = f"""Act as an AI Equity Research Analyst. Analyze this Energy Transition pair:

{context}

Tasks:
1. Identify the KEY NON-CONSENSUS insight (what market is missing)
2. Cluster themes: Grid Equipment vs Oilfield Services positioning
3. Extract sentiment signals for "new-type power system" vs "fossil services"
4. Generate 3 scenarios (base/bull/bear) with probability-weighted outcomes
5. List clear AI limitations (data gaps, recency bias, policy optimism)

Return ONLY valid JSON with structure:
{{
  "non_consensus_insight": "string",
  "theme_clusters": {{"grid": ["list"], "oilfield": ["list"]}},
  "sentiment_analysis": {{"grid_sentiment": "bullish/bearish", "oilfield_sentiment": "bullish/bearish"}},
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
        prompt = f"""Answer this investor Q&A question about the LONG Dongfang / SHORT Jereh pair trade:

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
    long_thesis = generate_long_thesis({})
    short_thesis = generate_short_thesis({})

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
    ai_module = generate_ai_analyst_module()
    with open(output_dir / "ai_analyst_module.json", "w") as f:
        json.dump(ai_module, f, indent=2, ensure_ascii=False)
    saved["ai_module"] = output_dir / "ai_analyst_module.json"
    print(f"  ✓ Non-consensus insight: {ai_module.get('non_consensus_insight', 'N/A')[:60]}...")

    # 3. Generate slide content
    print("\n[3] Generating slide content...")
    slides_config = [
        {
            "title": "Executive Summary",
            "context": "One-pager: Grid infrastructure long vs Oilfield services short. State Grid RMB 4T capex catalyst.",
            "bullets": 6,
        },
        {
            "title": "Consensus View",
            "context": "Market currently believes energy security = oil exposure. Explain why this is wrong.",
            "bullets": 5,
        },
        {
            "title": "Variant View",
            "context": "Energy security = grid resilience. Data centers, EVs, electrification stress the grid.",
            "bullets": 5,
        },
        {
            "title": "Long Case: Dongfang Electric",
            "context": "Power equipment, grid integration, synchronous condensers, RMB 140B backlog",
            "bullets": 6,
        },
        {
            "title": "Short Case: Yantai Jereh",
            "context": "Oilfield services, fossil exposure, cyclical, margin pressure despite revenue growth",
            "bullets": 6,
        },
    ]

    slide_content = generate_slide_content_batch(slides_config)
    with open(output_dir / "slide_content.json", "w") as f:
        json.dump(slide_content, f, indent=2, ensure_ascii=False)
    saved["slide_content"] = output_dir / "slide_content.json"
    print(f"  ✓ Generated content for {len(slide_content)} slides")

    # 4. Generate Q&A defense - raises exception if LLM fails
    print("\n[4] Generating Q&A defense responses...")
    qa_questions = [
        "What if oil prices spike and Jereh rallies?",
        "Is Dongfang's 30% profit growth sustainable?",
        "What's the borrow cost for shorting Jereh?",
        "How does the pair trade protect against market drawdowns?",
        "What's the thesis kill switch?",
    ]
    thesis_ctx = f"Long Dongfang (grid) / Short Jereh (oilfield). Spread target 100%+"
    qa_responses = generate_qa_responses(qa_questions, thesis_ctx)
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
