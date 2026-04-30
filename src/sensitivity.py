#!/usr/bin/env python3
"""Dongfang Electric (1072.HK) EPS Sensitivity Analysis.

Models EPS sensitivity to:
- Overseas revenue mix (%)
- Gross margin (%)
- R&D / SG&A as % of revenue
- CNY/USD FX rate

Outputs sensitivity tables and tornado charts for Slide 11 (Valuation).
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

OUTPUT_DIR = Path("outputs/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Dongfang Electric base case assumptions (from 2025 annual report)
# 2025 actuals: Revenue RMB 78.61B (+12.8% YoY), Net Profit RMB 3.83B (+31.1% YoY)
# EPS ~RMB 1.15 on roughly 3.33B shares.
# Base case reflects normalized FCF generation from RMB 140.31B order backlog
BASE_CASE = {
    "revenue_cny_mm": 78610,  # ~78.6B CNY revenue (2025 actual, +12.8% YoY)
    "overseas_mix": 0.25,     # 25% overseas revenue (growing toward 30%)
    "gross_margin": 0.18,     # ~18% gross margin (2025 actual, improving)
    "r_and_d_pct": 0.05,      # ~5% R&D
    "sg_and_a_pct": 0.09,     # ~9% SG&A
    "tax_rate": 0.15,         # 15% effective tax (SOE + high-tech)
    "shares_outstanding": 3330,  # ~3.33B shares
    "fx_cny_usd": 7.2,        # CNY/USD rate (HKD leg)
}

# Overseas vs domestic margin differential
OVERSEAS_PREMIUM = 0.05  # 5% higher margin on overseas (better pricing power)


def calculate_eps(
    revenue: float,
    overseas_mix: float,
    gross_margin: float,
    r_and_d_pct: float,
    sg_and_a_pct: float,
    tax_rate: float,
    shares: float,
    fx_rate: float = 7.2
) -> float:
    """Calculate EPS given assumptions.
    
    Args:
        revenue: Total revenue in CNY millions (at base FX rate of 7.2)
        overseas_mix: % of revenue from overseas (0-1)
        gross_margin: Gross margin (0-1)
        r_and_d_pct: R&D as % of revenue (0-1)
        sg_and_a_pct: SG&A as % of revenue (0-1)
        tax_rate: Effective tax rate (0-1)
        shares: Shares outstanding in millions
        fx_rate: CNY/USD exchange rate
        
    Returns:
        EPS in CNY
    """
    # FX impact on overseas revenue
    # Base FX = 7.2 CNY/USD
    fx_impact = (fx_rate / 7.2 - 1) * overseas_mix
    adjusted_revenue = revenue * (1 + fx_impact)
    
    # Blended gross margin (overseas gets premium)
    blended_gm = gross_margin + (overseas_mix * OVERSEAS_PREMIUM)
    
    # Gross profit
    gross_profit = adjusted_revenue * blended_gm
    
    # Operating expenses
    r_and_d = adjusted_revenue * r_and_d_pct
    sg_and_a = adjusted_revenue * sg_and_a_pct
    
    # Operating income (EBIT)
    ebit = gross_profit - r_and_d - sg_and_a
    
    # Net income
    net_income = ebit * (1 - tax_rate)
    
    # EPS
    eps = net_income / shares
    
    return eps


def generate_sensitivity_table(
    base_case: Dict,
    variable: str,
    range_pct: Tuple[float, float] = (-0.30, 0.30),
    steps: int = 5
) -> pd.DataFrame:
    """Generate sensitivity table for one variable.
    
    Args:
        base_case: Base case assumptions
        variable: Variable to sensitize
        range_pct: Range as % change from base (e.g., -30% to +30%)
        steps: Number of steps
        
    Returns:
        DataFrame with variable values and resulting EPS
    """
    base_value = base_case[variable]
    
    # Create range
    changes = np.linspace(range_pct[0], range_pct[1], steps)
    
    results = []
    for change in changes:
        # Calculate new value
        if variable == "overseas_mix":
            # Overseas mix is bounded 0-1
            new_value = max(0, min(1, base_value * (1 + change)))
        elif variable in ["gross_margin", "r_and_d_pct", "sg_and_a_pct", "tax_rate"]:
            # Percentages bounded 0-1
            new_value = max(0, min(1, base_value * (1 + change)))
        else:
            new_value = base_value * (1 + change)
        
        # Calculate EPS with this variable changed
        test_case = base_case.copy()
        test_case[variable] = new_value
        
        eps = calculate_eps(
            revenue=test_case["revenue_cny_mm"],
            overseas_mix=test_case["overseas_mix"],
            gross_margin=test_case["gross_margin"],
            r_and_d_pct=test_case["r_and_d_pct"],
            sg_and_a_pct=test_case["sg_and_a_pct"],
            tax_rate=test_case["tax_rate"],
            shares=test_case["shares_outstanding"],
            fx_rate=test_case["fx_cny_usd"]
        )
        
        results.append({
            "variable": variable,
            "change_pct": round(change * 100, 1),
            "value": round(new_value, 3) if variable != "revenue_cny_mm" else round(new_value, 0),
            "eps_cny": round(eps, 2),
            "eps_change_pct": round((eps / calculate_eps_from_dict(base_case) - 1) * 100, 1)
        })
    
    return pd.DataFrame(results)


def calculate_eps_from_dict(params: Dict) -> float:
    """Helper to calculate EPS from parameter dict."""
    return calculate_eps(
        revenue=params["revenue_cny_mm"],
        overseas_mix=params["overseas_mix"],
        gross_margin=params["gross_margin"],
        r_and_d_pct=params["r_and_d_pct"],
        sg_and_a_pct=params["sg_and_a_pct"],
        tax_rate=params["tax_rate"],
        shares=params["shares_outstanding"],
        fx_rate=params["fx_cny_usd"]
    )


def create_tornado_chart(sensitivities: Dict[str, pd.DataFrame], output_path: Path):
    """Create tornado chart showing EPS sensitivity by variable.
    
    Args:
        sensitivities: Dict of variable name -> sensitivity DataFrame
        output_path: Where to save chart
    """
    # Calculate EPS impact range for each variable
    impacts = []
    for var, df in sensitivities.items():
        eps_range = df["eps_cny"].max() - df["eps_cny"].min()
        base_eps = df[df["change_pct"] == 0]["eps_cny"].values[0]
        impacts.append({
            "variable": var,
            "impact_range": eps_range,
            "base_eps": base_eps,
            "low_eps": df["eps_cny"].min(),
            "high_eps": df["eps_cny"].max()
        })
    
    impact_df = pd.DataFrame(impacts).sort_values("impact_range", ascending=True)
    
    # Create chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Variable labels (clean names)
    var_labels = {
        "overseas_mix": "Overseas Revenue Mix",
        "gross_margin": "Gross Margin",
        "r_and_d_pct": "R&D Spend",
        "sg_and_a_pct": "SG&A Spend",
        "fx_cny_usd": "CNY/USD Rate"
    }
    
    y_pos = np.arange(len(impact_df))
    
    # Plot horizontal bars
    for i, row in impact_df.iterrows():
        idx = y_pos[i]
        var = row["variable"]
        low = row["low_eps"]
        high = row["high_eps"]
        base = row["base_eps"]
        
        # Bar from low to high
        ax.barh(idx, high - low, left=low, height=0.6, 
                color='#1f77b4' if high > base else '#d62728', alpha=0.7)
        
        # Base case marker
        ax.plot(base, idx, 'k|', markersize=15, markeredgewidth=2)
    
    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels([var_labels.get(v, v) for v in impact_df["variable"]])
    ax.set_xlabel("EPS (CNY)")
    ax.set_title("Dongfang Electric EPS Sensitivity Analysis\n(Base case marked with |)", 
                 fontsize=14, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)
    ax.axvline(x=impact_df["base_eps"].iloc[0], color='black', linestyle='--', alpha=0.5, label='Base case')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[SAVED] Tornado chart: {output_path}")


def create_sensitivity_matrix(
    base_case: Dict,
    var1: str,
    var2: str,
    output_path: Path
):
    """Create 2D sensitivity matrix for two variables.
    
    Args:
        base_case: Base assumptions
        var1: First variable (rows)
        var2: Second variable (cols)
        output_path: Save path
    """
    # Ranges
    changes = [-0.20, -0.10, 0, 0.10, 0.20]
    
    matrix = []
    for c1 in changes:
        row = []
        for c2 in changes:
            test = base_case.copy()
            test[var1] = base_case[var1] * (1 + c1)
            test[var2] = base_case[var2] * (1 + c2)
            eps = calculate_eps_from_dict(test)
            row.append(eps)
        matrix.append(row)
    
    df = pd.DataFrame(matrix, 
                      index=[f"{int(c*100)}%" for c in changes],
                      columns=[f"{int(c*100)}%" for c in changes])
    
    # Heatmap
    fig, ax = plt.subplots(figsize=(8, 6))
    
    im = ax.imshow(df.values, cmap='RdYlGn', aspect='auto')
    
    # Labels
    ax.set_xticks(np.arange(len(changes)))
    ax.set_yticks(np.arange(len(changes)))
    ax.set_xticklabels([f"{int(c*100)}%" for c in changes])
    ax.set_yticklabels([f"{int(c*100)}%" for c in changes])
    
    # Add values
    for i in range(len(changes)):
        for j in range(len(changes)):
            text = ax.text(j, i, f'{df.values[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=10)
    
    ax.set_xlabel(f"{var2} Change")
    ax.set_ylabel(f"{var1} Change")
    ax.set_title(f"EPS Sensitivity: {var1} vs {var2}\n(Base case at center)", 
                 fontsize=12, fontweight='bold')
    
    plt.colorbar(im, ax=ax, label='EPS (CNY)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[SAVED] Sensitivity matrix: {output_path}")
    
    return df


def save_sensitivity_tables(sensitivities: Dict[str, pd.DataFrame], output_dir: Path):
    """Save all sensitivity tables to CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Combined table
    combined = pd.concat(sensitivities.values(), ignore_index=True)
    combined_path = output_dir / "sensitivity_all_variables.csv"
    combined.to_csv(combined_path, index=False)
    print(f"[SAVED] Combined sensitivity: {combined_path}")
    
    # Summary table (just -10%, base, +10%)
    summary_rows = []
    for var, df in sensitivities.items():
        for _, row in df.iterrows():
            if row["change_pct"] in [-10, 0, 10]:
                summary_rows.append(row)
    
    summary_df = pd.DataFrame(summary_rows)
    summary_path = output_dir / "sensitivity_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"[SAVED] Sensitivity summary: {summary_path}")


def main():
    """Run full sensitivity analysis."""
    print("="*60)
    print("DONGFANG ELECTRIC EPS SENSITIVITY ANALYSIS")
    print("="*60)
    
    # Base case EPS
    base_eps = calculate_eps_from_dict(BASE_CASE)
    print(f"\n[Base Case EPS]: {base_eps:.2f} CNY")
    print(f"  Revenue: {BASE_CASE['revenue_cny_mm']:,.0f}M CNY")
    print(f"  Overseas mix: {BASE_CASE['overseas_mix']*100:.0f}%")
    print(f"  Gross margin: {BASE_CASE['gross_margin']*100:.0f}%")
    
    # Generate sensitivities
    print("\n[1] Generating sensitivity tables...")
    variables = ["overseas_mix", "gross_margin", "r_and_d_pct", "sg_and_a_pct", "fx_cny_usd"]
    sensitivities = {}
    
    for var in variables:
        df = generate_sensitivity_table(BASE_CASE, var)
        sensitivities[var] = df
        print(f"\n  {var}:")
        print(df[["change_pct", "eps_cny", "eps_change_pct"]].to_string(index=False))
    
    # Create tornado chart
    print("\n[2] Creating tornado chart...")
    tornado_path = OUTPUT_DIR / "sensitivity_tornado.png"
    create_tornado_chart(sensitivities, tornado_path)
    
    # Create 2D sensitivity matrix (overseas mix vs gross margin)
    print("\n[3] Creating 2D sensitivity matrix...")
    matrix_path = OUTPUT_DIR / "sensitivity_matrix_overseas_margin.png"
    create_sensitivity_matrix(BASE_CASE, "overseas_mix", "gross_margin", matrix_path)
    
    # Save tables
    print("\n[4] Saving sensitivity tables...")
    tables_dir = Path("data/processed/valuation")
    save_sensitivity_tables(sensitivities, tables_dir)
    
    # Summary stats
    print("\n" + "="*60)
    print("SENSITIVITY SUMMARY")
    print("="*60)
    print(f"Base case EPS: {base_eps:.2f} CNY")
    print(f"\nEPS Range by Variable (±20% change):")
    for var, df in sensitivities.items():
        eps_min = df["eps_cny"].min()
        eps_max = df["eps_cny"].max()
        print(f"  {var}: {eps_min:.2f} - {eps_max:.2f} (±{((eps_max-eps_min)/base_eps*50):.1f}%)")
    
    print("\n" + "="*60)
    print("SENSITIVITY ANALYSIS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
