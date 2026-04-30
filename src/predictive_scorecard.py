#!/usr/bin/env python3
"""Build an empirical forward scorecard for the active pair.

The scorecard deliberately separates three claims:
1. Historical spread validation
2. Current empirical setup
3. Forward predictive thesis

That prevents the deck from overstating an adverse backtest while still using
market data, fundamentals, and AI-classified evidence as predictive inputs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.company_facts import COMPANY_FACTS
from src.pair_config import LONG_LEG, SHORT_LEG


ROOT = Path("/Users/skumyol/Documents/GitHub/ubs")
VAL_DIR = ROOT / "data" / "processed" / "valuation"
OUT_DIR = ROOT / "outputs" / "tables"


def _read_one(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return {}
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


def _fmt(value: Any, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if isinstance(value, float):
        return f"{value:.1f}{suffix}"
    return f"{value}{suffix}"


def build_predictive_scorecard(
    valuation_dir: Path = VAL_DIR,
    output_dir: Path = OUT_DIR,
) -> pd.DataFrame:
    """Create a forward-looking empirical scorecard."""
    dongfang = COMPANY_FACTS["dongfang"]
    short = COMPANY_FACTS["sungrow"]
    pair = _read_one(valuation_dir / "pair_trade_summary.csv")
    trader = _read_one(valuation_dir / "trader_analysis.csv")
    backtest = _read_one(valuation_dir / "oil_sungrow_backtest.csv")

    pe_gap = short["pe_ttm"] - dongfang["pe_ttm"]
    pb_gap = short["pb"] - dongfang["pb"]
    short_52w = trader.get("technicals_sungrow_pct_52w_high")
    dongfang_52w = trader.get("technicals_dongfang_pct_52w_high")
    short_rsi = trader.get("technicals_sungrow_rsi")
    dongfang_rsi = trader.get("technicals_dongfang_rsi")
    pair_backtest = backtest.get("pair_final_pnl_pct")
    short_2y = backtest.get("short_2y_return")
    dongfang_2y = backtest.get("long_2y_return")
    spread = pair.get("pair_spread_return_pct")

    rows = [
        {
            "pillar": "Historical spread test",
            "evidence": (
                f"2Y simulated pair P&L was {_fmt(pair_backtest, '%')}; "
                f"{LONG_LEG.name} 2Y return {_fmt(dongfang_2y, '%')} vs {SHORT_LEG.name} {_fmt(short_2y, '%')}."
            ),
            "signal": "Risk / contradiction",
            "submission_language": (
                "Do not present the trade as historically validated. Use the backtest as evidence "
                "that the short leg was a crowded same-sector winner and the trade needs a forward catalyst."
            ),
        },
        {
            "pillar": "Earnings durability",
            "evidence": (
                f"{LONG_LEG.name} delivered 2025 net profit growth of {dongfang['net_profit_growth_2025']*100:.1f}% on "
                f"{dongfang['revenue_growth_2025']*100:.1f}% revenue growth, backed by order visibility, while "
                f"{SHORT_LEG.name} moved from +22.0% full-year profit growth to -40.1% YoY in Q1 2026."
            ),
            "signal": f"Supports long {LONG_LEG.name} / short {SHORT_LEG.name}",
            "submission_language": (
                "The predictive view is durability versus normalization: Dongfang offers cleaner "
                "grid-integration exposure while Sungrow faces normalization risk after being priced as a structural compounder."
            ),
        },
        {
            "pillar": "Valuation stretch",
            "evidence": (
                f"{SHORT_LEG.name} trades at a {pe_gap:.1f}x P/E premium and {pb_gap:.1f}x P/B gap "
                f"to {LONG_LEG.name} ({short['pe_ttm']:.1f}x/{short['pb']:.1f}x vs "
                f"{dongfang['pe_ttm']:.1f}x/{dongfang['pb']:.1f}x)."
            ),
            "signal": f"Supports short {SHORT_LEG.name} if margin recovery disappoints",
            "submission_language": (
                "The short is not a low-quality-company claim; it is a mispriced-expectations "
                "claim after a large rerating."
            ),
        },
        {
            "pillar": "Technical setup",
            "evidence": (
                f"{SHORT_LEG.name} is at {_fmt(short_52w, '%')} of its 52-week high with RSI "
                f"{_fmt(short_rsi)}, while {LONG_LEG.name} is at {_fmt(dongfang_52w, '%')} "
                f"with RSI {_fmt(dongfang_rsi)}."
            ),
            "signal": "Supports timing discipline",
            "submission_language": (
                f"Entry should be staged: wait for {SHORT_LEG.name} weakness or {LONG_LEG.name} confirmation, "
                "rather than claiming the backtest already proves the spread."
            ),
        },
        {
            "pillar": "Scenario valuation",
            "evidence": f"Probability-weighted modeled pair spread is {_fmt(spread, '%')}.",
            "signal": "Forward prediction",
            "submission_language": (
                "Use the scenario model as the predictive engine and disclose that it depends on "
                f"grid capex conversion, {LONG_LEG.name} margin delivery, and {SHORT_LEG.name} multiple compression."
            ),
        },
    ]

    df = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = valuation_dir / "predictive_scorecard.csv"
    md_path = output_dir / "predictive_scorecard.md"
    df.to_csv(csv_path, index=False)

    lines = [
        "# Empirical & Predictive Scorecard",
        "",
        "This is a forward-looking predictive framework, not a claim that the historical spread already worked.",
        "",
        "| Pillar | Evidence | Signal | Submission Language |",
        "|---|---|---|---|",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['pillar']} | {row['evidence']} | {row['signal']} | {row['submission_language']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[SAVED] {csv_path}")
    print(f"[SAVED] {md_path}")
    return df


def main() -> None:
    build_predictive_scorecard()


if __name__ == "__main__":
    main()
