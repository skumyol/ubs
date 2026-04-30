#!/usr/bin/env python3
"""Build an empirical forward scorecard for the Dongfang/Jereh pair.

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
    jereh = COMPANY_FACTS["jereh"]
    pair = _read_one(valuation_dir / "pair_trade_summary.csv")
    trader = _read_one(valuation_dir / "trader_analysis.csv")
    backtest = _read_one(valuation_dir / "oil_jereh_backtest.csv")

    profit_growth_gap = (
        dongfang["net_profit_growth_2025"] - jereh["net_profit_growth_2025"]
    ) * 100
    pe_gap = jereh["pe_ttm"] - dongfang["pe_ttm"]
    pb_gap = jereh["pb"] - dongfang["pb"]
    jereh_52w = trader.get("technicals_jereh_pct_52w_high")
    dongfang_52w = trader.get("technicals_dongfang_pct_52w_high")
    jereh_rsi = trader.get("technicals_jereh_rsi")
    dongfang_rsi = trader.get("technicals_dongfang_rsi")
    pair_backtest = backtest.get("pair_final_pnl_pct")
    jereh_2y = backtest.get("short_2y_return")
    dongfang_2y = backtest.get("long_2y_return")
    spread = pair.get("pair_spread_return_pct")

    rows = [
        {
            "pillar": "Historical spread test",
            "evidence": (
                f"2Y simulated pair P&L was {_fmt(pair_backtest, '%')}; "
                f"Dongfang 2Y return {_fmt(dongfang_2y, '%')} vs Jereh {_fmt(jereh_2y, '%')}."
            ),
            "signal": "Risk / contradiction",
            "submission_language": (
                "Do not present the trade as historically validated. Use the backtest as evidence "
                "that Jereh was a crowded winner and the trade needs a forward catalyst."
            ),
        },
        {
            "pillar": "Fundamental momentum",
            "evidence": (
                f"Dongfang net profit growth exceeded Jereh by {profit_growth_gap:.1f}pp "
                f"({dongfang['net_profit_growth_2025']*100:.1f}% vs "
                f"{jereh['net_profit_growth_2025']*100:.1f}%)."
            ),
            "signal": "Supports long Dongfang / short Jereh",
            "submission_language": (
                "The predictive view is earnings-quality convergence: Dongfang has the stronger "
                "profit acceleration while Jereh's revenue growth is not converting into profit."
            ),
        },
        {
            "pillar": "Valuation stretch",
            "evidence": (
                f"Jereh trades at a {pe_gap:.1f}x P/E premium and {pb_gap:.1f}x P/B premium "
                f"to Dongfang ({jereh['pe_ttm']:.1f}x/{jereh['pb']:.1f}x vs "
                f"{dongfang['pe_ttm']:.1f}x/{dongfang['pb']:.1f}x)."
            ),
            "signal": "Supports short Jereh if growth disappoints",
            "submission_language": (
                "The short is not a low-quality-company claim; it is a mispriced-expectations "
                "claim after a large rerating."
            ),
        },
        {
            "pillar": "Technical setup",
            "evidence": (
                f"Jereh is at {_fmt(jereh_52w, '%')} of its 52-week high with RSI "
                f"{_fmt(jereh_rsi)}, while Dongfang is at {_fmt(dongfang_52w, '%')} "
                f"with RSI {_fmt(dongfang_rsi)}."
            ),
            "signal": "Supports timing discipline",
            "submission_language": (
                "Entry should be staged: wait for Jereh weakness or Dongfang confirmation, "
                "rather than claiming the backtest already proves the spread."
            ),
        },
        {
            "pillar": "Scenario valuation",
            "evidence": f"Probability-weighted modeled pair spread is {_fmt(spread, '%')}.",
            "signal": "Forward prediction",
            "submission_language": (
                "Use the scenario model as the predictive engine and disclose that it depends on "
                "grid capex conversion, Dongfang margin delivery, and Jereh multiple compression."
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
