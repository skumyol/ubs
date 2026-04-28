#!/usr/bin/env python3
"""Build submission-hardening artifacts for quant/trader review."""

from pathlib import Path
from typing import Dict

import pandas as pd

from src.config import OUTPUTS_DIR, PROCESSED_DIR


def _safe_read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _val_or_default(df: pd.DataFrame, key: str, default: str = "N/A") -> str:
    if df.empty or key not in df.columns:
        return default
    value = df.iloc[0][key]
    return str(value)


def build_submission_pack() -> Dict:
    submission_dir = OUTPUTS_DIR / "submission"
    submission_dir.mkdir(parents=True, exist_ok=True)

    valuation_dir = PROCESSED_DIR / "valuation"
    pair = _safe_read(valuation_dir / "pair_trade_summary.csv")
    trader = _safe_read(valuation_dir / "trader_analysis.csv")
    long_sc = _safe_read(valuation_dir / "long_scenarios.csv")
    short_sc = _safe_read(valuation_dir / "short_scenarios.csv")
    peer = _safe_read(valuation_dir / "peer_comps.csv")

    long_ret = _val_or_default(pair, "long_expected_return_pct", "0")
    short_move = _val_or_default(pair, "short_expected_move_pct", "0")
    pair_ret = _val_or_default(pair, "pair_spread_return_pct", "0")

    rec_notional_mm = _val_or_default(trader, "position_sizing_recommended_notional_mm", "N/A")
    rec_position_pct = _val_or_default(trader, "position_sizing_recommended_position_pct", "N/A")
    pair_vol = _val_or_default(trader, "volatilities_pair_vol", "N/A")
    net_carry_low = _val_or_default(trader, "carry_cost_low_borrow_net_carry_cost", "N/A")
    net_carry_high = _val_or_default(trader, "carry_cost_high_borrow_net_carry_cost", "N/A")

    trade_plan = [
        "# Trade Construction Plan",
        "",
        "## Position Framework",
        "",
        "- Structure: Long Sieyuan / Short Halliburton",
        f"- Expected spread return (prob-weighted): {pair_ret}%",
        f"- Recommended notional: ${rec_notional_mm}mm ({rec_position_pct}% of portfolio)",
        f"- Pair annualized volatility estimate: {pair_vol}%",
        "",
        "## Entry & Rebalance",
        "",
        "- Entry trigger: open when HAL near resistance and Sieyuan not overbought.",
        "- Rebalance: monthly or when leg weight drifts >10% from target.",
        "- Holding window: 6-12 months unless thesis invalidation occurs.",
        "",
        "## Execution Constraints",
        "",
        "- Use limit orders over multiple slices; cap participation at <=10% ADV.",
        "- Confirm borrow availability and fee before short entry.",
        "- Respect market access constraints for A-share execution.",
    ]
    (submission_dir / "trade_construction.md").write_text("\n".join(trade_plan), encoding="utf-8")

    risk_memo = [
        "# Risk Memo",
        "",
        "## Primary Risks",
        "",
        "- Oil shock risk: HAL rallies despite weak operational quality.",
        "- Grid policy delay: pushes out order conversion for the long leg.",
        "- China multiple compression: hurts long valuation even with stable earnings.",
        "",
        "## Risk Limits",
        "",
        "- Max portfolio risk per trade: 2%.",
        "- Stop-loss trigger: spread drawdown >12% from entry.",
        "- De-risk trigger: borrow cost spikes above expected spread carry budget.",
        "",
        "## Carry & Financing",
        "",
        f"- Estimated net carry cost (low borrow): ${net_carry_low}K over 180 days.",
        f"- Estimated net carry cost (high borrow): ${net_carry_high}K over 180 days.",
    ]
    (submission_dir / "risk_memo.md").write_text("\n".join(risk_memo), encoding="utf-8")

    catalyst_calendar = [
        "# Catalyst Calendar (Next 180 Days)",
        "",
        "| Window | Catalyst | Expected Spread Impact | What Confirms Thesis |",
        "|---|---|---|---|",
        "| Q2 earnings | HAL margin guidance / rig commentary | Positive if weak | Lower service margin outlook |",
        "| Q2-Q3 | Sieyuan overseas order disclosures | Positive if strong | Backlog/order momentum acceleration |",
        "| Policy cycle | Grid capex announcements | Positive if supportive | Multi-year grid budget visibility |",
        "| Q3 updates | Oil majors capex tone | Positive if cautious | Slower OFS demand outlook |",
    ]
    (submission_dir / "catalyst_calendar.md").write_text("\n".join(catalyst_calendar), encoding="utf-8")

    valuation_assumptions = [
        "# Valuation Assumptions",
        "",
        "## Pair Output",
        "",
        f"- Long expected return: {long_ret}%",
        f"- Short expected move: {short_move}%",
        f"- Pair spread expected return: {pair_ret}%",
        "",
        "## Scenario Inputs",
        "",
        "### Long (Sieyuan)",
    ]
    if not long_sc.empty:
        valuation_assumptions.append("| Scenario | EPS Growth | Target P/E | Target Price | Probability |")
        valuation_assumptions.append("|---|---:|---:|---:|---:|")
        for _, row in long_sc.iterrows():
            valuation_assumptions.append(
                f"| {row['scenario']} | {row['eps_growth']} | {row['target_pe']} | {row['target_price']} | {row['probability']} |"
            )

    valuation_assumptions.extend(["", "### Short (HAL)"])
    if not short_sc.empty:
        valuation_assumptions.append("| Scenario | EPS Growth | Target P/E | Target Price | Probability |")
        valuation_assumptions.append("|---|---:|---:|---:|---:|")
        for _, row in short_sc.iterrows():
            valuation_assumptions.append(
                f"| {row['scenario']} | {row['eps_growth']} | {row['target_pe']} | {row['target_price']} | {row['probability']} |"
            )

    valuation_assumptions.extend([
        "",
        "## Peer Basis",
        "",
        "Target multiples are anchored to current peer comp ranges generated in `peer_comps.csv`, then stress-tested by scenario.",
    ])
    (submission_dir / "valuation_assumptions.md").write_text("\n".join(valuation_assumptions), encoding="utf-8")

    checklist = [
        "# Submission Readiness Checklist",
        "",
        "## Data Integrity",
        "",
        "- [ ] All evidence tied to auditable source files/URLs",
        "- [ ] Invalid/future dates removed or excluded",
        "- [ ] Date audit exported",
        "",
        "## Tradeability",
        "",
        "- [ ] Position sizing and risk budget documented",
        "- [ ] Borrow/carry assumptions documented",
        "- [ ] Kill-switch criteria documented",
        "",
        "## Valuation & Catalysts",
        "",
        "- [ ] Scenario assumptions explicitly shown",
        "- [ ] Peer-based multiple rationale shown",
        "- [ ] 180-day catalyst calendar included",
        "",
        "## Required Files",
        "",
        "- `outputs/submission/trade_construction.md`",
        "- `outputs/submission/risk_memo.md`",
        "- `outputs/submission/catalyst_calendar.md`",
        "- `outputs/submission/valuation_assumptions.md`",
        "- `outputs/quality/data_quality_report.md`",
    ]
    (submission_dir / "submission_readiness_checklist.md").write_text("\n".join(checklist), encoding="utf-8")

    return {
        "trade_construction": str(submission_dir / "trade_construction.md"),
        "risk_memo": str(submission_dir / "risk_memo.md"),
        "catalyst_calendar": str(submission_dir / "catalyst_calendar.md"),
        "valuation_assumptions": str(submission_dir / "valuation_assumptions.md"),
        "readiness_checklist": str(submission_dir / "submission_readiness_checklist.md"),
    }


if __name__ == "__main__":
    outputs = build_submission_pack()
    print("=" * 60)
    print("SUBMISSION PACK GENERATED")
    print("=" * 60)
    for name, path in outputs.items():
        print(f"{name}: {path}")
