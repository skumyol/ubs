#!/usr/bin/env python3
"""DCF Analysis for Dongfang Electric / Sungrow pair trade.

Run this script to generate DCF valuations and sensitivity tables.
Uses exact numbers from the UBS Finance Challenge submission.
"""

import pandas as pd
import numpy as np
from typing import Dict, List


def simple_dcf(fcf0: float, growth_rate: float, terminal_growth: float, wacc: float, years: int = 5) -> float:
    """Compute a simple DCF on normalized free cash flow.
    
    Args:
        fcf0: Normalized FCF base (RMB billions)
        growth_rate: High-growth period CAGR
        terminal_growth: Terminal growth rate
        wacc: Weighted average cost of capital
        years: High-growth period length
    
    Returns:
        Enterprise value in RMB billions
    """
    cash_flows = []
    pv_cash_flows = []
    
    for year in range(1, years + 1):
        fcf = fcf0 * ((1 + growth_rate) ** year)
        pv = fcf / ((1 + wacc) ** year)
        cash_flows.append(round(fcf, 3))
        pv_cash_flows.append(round(pv, 3))
    
    terminal_fcf = fcf0 * ((1 + growth_rate) ** years)
    terminal_value = terminal_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
    pv_terminal = terminal_value / ((1 + wacc) ** years)
    enterprise_value = sum(pv_cash_flows) + pv_terminal
    
    return round(enterprise_value, 2)


def generate_sensitivity_table(fcf0: float, growth_rates: List[float], wacc_rates: List[float], 
                                terminal_growth: float, years: int = 5) -> pd.DataFrame:
    """Generate sensitivity table for DCF analysis.
    
    Args:
        fcf0: Normalized FCF base
        growth_rates: List of growth rate assumptions to test
        wacc_rates: List of WACC assumptions to test
        terminal_growth: Terminal growth rate
        years: High-growth period length
    
    Returns:
        DataFrame with sensitivity results
    """
    results = []
    for g in growth_rates:
        row = []
        for w in wacc_rates:
            ev = simple_dcf(fcf0, g, terminal_growth, w, years)
            row.append(ev)
        results.append(row)
    
    df = pd.DataFrame(
        results,
        index=[f"{g*100:.0f}%" for g in growth_rates],
        columns=[f"{w*100:.1f}%" for w in wacc_rates]
    )
    return df


def main():
    """Run DCF analysis for Dongfang Electric and Sungrow."""
    
    print("=" * 70)
    print("DCF ANALYSIS - Dongfang Electric / Sungrow Pair Trade")
    print("=" * 70)
    print()
    
    # Dongfang Electric DCF (Long - Bullish on grid tailwind)
    print("DONGFANG ELECTRIC (LONG)")
    print("-" * 70)
    dongfang_fcf0 = 2.8  # RMB billions
    dongfang_growth = 0.17  # 17% CAGR
    dongfang_terminal = 0.04  # 4%
    dongfang_wacc = 0.085  # 8.5%
    
    dongfang_ev_base = simple_dcf(dongfang_fcf0, dongfang_growth, dongfang_terminal, dongfang_wacc)
    print(f"Assumptions:")
    print(f"  Normalized FCF base: RMB {dongfang_fcf0} bn")
    print(f"  High-growth CAGR: {dongfang_growth*100:.0f}%")
    print(f"  Terminal growth: {dongfang_terminal*100:.0f}%")
    print(f"  WACC: {dongfang_wacc*100:.1f}%")
    print(f"  Growth period: 5 years")
    print()
    print(f"Base Case Enterprise Value: RMB {dongfang_ev_base} bn")
    print()
    
    # Sensitivity table for Dongfang
    print("Sensitivity Table - Dongfang Electric (Growth Rate vs WACC):")
    print("(Enterprise Value in RMB billions)")
    dongfang_growth_rates = [0.15, 0.17, 0.20]
    dongfang_wacc_rates = [0.08, 0.085, 0.09]
    dongfang_sensitivity = generate_sensitivity_table(
        dongfang_fcf0, dongfang_growth_rates, dongfang_wacc_rates, dongfang_terminal
    )
    print(dongfang_sensitivity)
    print()
    
    # Sungrow DCF (Short - Conservative)
    print("SUNGROW (SHORT)")
    print("-" * 70)
    sungrow_fcf0 = 8.0  # RMB billions
    sungrow_growth = 0.08  # 8% CAGR
    sungrow_terminal = 0.03  # 3%
    sungrow_wacc = 0.095  # 9.5%
    
    sungrow_ev = simple_dcf(sungrow_fcf0, sungrow_growth, sungrow_terminal, sungrow_wacc)
    print(f"Assumptions:")
    print(f"  Normalized FCF base: RMB {sungrow_fcf0} bn")
    print(f"  High-growth CAGR: {sungrow_growth*100:.0f}%")
    print(f"  Terminal growth: {sungrow_terminal*100:.0f}%")
    print(f"  WACC: {sungrow_wacc*100:.1f}%")
    print(f"  Growth period: 5 years")
    print()
    print(f"Conservative Case Enterprise Value: RMB {sungrow_ev} bn")
    print()
    
    # Comparison
    print("=" * 70)
    print("DCF COMPARISON SUMMARY")
    print("=" * 70)
    print(f"Dongfang EV: RMB {dongfang_ev_base} bn (bullish: grid capex tailwind)")
    print(f"Sungrow EV: RMB {sungrow_ev} bn (conservative: demand normalization)")
    print()
    print("Interpretation:")
    print("- Dongfang's EV reflects re-rating potential from backlog conversion")
    print("- Sungrow's EV assumes growth slowdown and higher discount rate")
    print("- DCF used as cross-check against scenario-based P/E valuation")
    print()


if __name__ == "__main__":
    main()
