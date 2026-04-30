#!/usr/bin/env python3
"""Trader-focused risk and execution analysis.

Calculates:
- Position sizing based on volatility and max loss
- Carry cost (dividends, borrow)
- Liquidity/capacity constraints
- Technical entry signals
- Correlation stress scenarios
"""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

OUTPUT_DIR = Path("outputs/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Ticker mapping - NEW PAIR: Dongfang Electric / Sungrow
DONGFANG_TICKER = "1072.HK"  # HK ticker is more reliable in yfinance
DONGFANG_TICKER_CN = "600875.SH"  # China A-share equivalent
SUNGROW_TICKER = "300274.SZ"

# Trading assumptions
MAX_PORTFOLIO_RISK_PCT = 0.02  # 2% max loss on single trade
SUNGROW_BORROW_COST_LOW = 0.025  # 2.5% annual borrow cost (A-share short borrow assumption)
SUNGROW_BORROW_COST_HIGH = 0.07  # 7% annual borrow cost (worst case)
SUNGROW_DIVIDEND_YIELD = 0.035  # 3.5% annual dividend (short pays this, based on Sungrow facts)
DONGFANG_DIVIDEND_YIELD = 0.015  # 1.5% annual dividend (long receives)


def fetch_price_data(ticker: str, period: str = "2y") -> Optional[pd.DataFrame]:
    """Fetch historical price data from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            print(f"[WARNING] No data for {ticker}")
            return None
        return df
    except Exception as e:
        print(f"[ERROR] Failed to fetch {ticker}: {e}")
        return None


def calculate_volatility(df: pd.DataFrame, window: int = 63) -> float:
    """Calculate annualized volatility from daily returns (63d ~ 3 months)."""
    if df is None or df.empty:
        return 1.0  # Default 100% vol if no data
    
    daily_returns = df['Close'].pct_change().dropna()
    if len(daily_returns) < window:
        window = len(daily_returns)
    
    recent_returns = daily_returns.iloc[-window:]
    daily_vol = recent_returns.std()
    annualized_vol = daily_vol * np.sqrt(252)
    
    return annualized_vol


def calculate_position_sizing(
    dongfang_vol: float,
    sungrow_vol: float,
    pair_vol: float,
    portfolio_value: float = 100_000_000,  # $100M portfolio default
    max_risk_pct: float = MAX_PORTFOLIO_RISK_PCT,
    pair_exposure_pct: float = 0.10,  # 10% of portfolio in this trade
) -> Dict:
    """Calculate position sizing based on volatility and risk constraints.
    
    Args:
        dongfang_vol: Annualized volatility of Dongfang
        sungrow_vol: Annualized volatility of Sungrow
        pair_vol: Annualized volatility of pair trade spread
        portfolio_value: Total portfolio AUM
        max_risk_pct: Max loss as % of portfolio
        pair_exposure_pct: Target exposure to this pair trade
        
    Returns:
        Position sizing recommendations
    """
    max_loss_dollar = portfolio_value * max_risk_pct
    target_exposure = portfolio_value * pair_exposure_pct
    
    # Kelly-like sizing (simplified: half Kelly for conservatism)
    # Position size = (Expected return / Variance) / 2
    # Using 20% expected spread return, 25% vol = 0.20 / (0.25^2) / 2 = 1.6x 
    # But we cap at 10% of portfolio for risk management
    
    # Position based on pair volatility
    # If pair vol is 25%, a 2-sigma move is 50%. To limit loss to 2% of portfolio:
    # Position size = max_loss / (2 * pair_vol) = 0.02 / 0.50 = 4% of portfolio
    
    vol_based_size = max_loss_dollar / (2 * pair_vol)
    
    results = {
        "portfolio_value_mm": round(portfolio_value / 1_000_000, 1),
        "max_loss_dollar": round(max_loss_dollar / 1_000_000, 1),
        "dongfang_vol_annual": round(dongfang_vol * 100, 1),
        "sungrow_vol_annual": round(sungrow_vol * 100, 1),
        "pair_vol_annual": round(pair_vol * 100, 1),
        "target_exposure_mm": round(target_exposure / 1_000_000, 1),
        "vol_based_size_mm": round(vol_based_size / 1_000_000, 1),
        "recommended_notional_mm": round(min(vol_based_size, target_exposure) / 1_000_000, 1),
        "long_dongfang_notional_mm": round(min(vol_based_size, target_exposure) / 2 / 1_000_000, 1),
        "short_sungrow_notional_mm": round(min(vol_based_size, target_exposure) / 2 / 1_000_000, 1),
        "recommended_position_pct": round(min(vol_based_size, target_exposure) / portfolio_value * 100, 1),
    }
    
    return results


def calculate_carry_cost(
    sungrow_notional: float,
    borrow_cost: float = SUNGROW_BORROW_COST_LOW,
    holding_period_days: int = 180,
) -> Dict:
    """Calculate carry cost for the short leg.
    
    Args:
        sungrow_notional: Short Sungrow notional
        borrow_cost: Annual borrow cost
        holding_period_days: Expected holding period
    """
    # Short leg pays dividend
    sungrow_dividend_cost = sungrow_notional * SUNGROW_DIVIDEND_YIELD * (holding_period_days / 365)
    
    # Short leg pays borrow cost
    sungrow_borrow_cost = sungrow_notional * borrow_cost * (holding_period_days / 365)
    
    # Long leg receives dividend
    dongfang_notional = sungrow_notional  # Equal-weighted
    dongfang_dividend_income = dongfang_notional * DONGFANG_DIVIDEND_YIELD * (holding_period_days / 365)
    
    # Net carry
    net_carry_cost = sungrow_dividend_cost + sungrow_borrow_cost - dongfang_dividend_income
    
    return {
        "sungrow_notional": round(sungrow_notional / 1_000_000, 1),
        "holding_period_days": holding_period_days,
        "sungrow_dividend_cost": round(sungrow_dividend_cost / 1_000, 1),  # in thousands
        "sungrow_borrow_cost": round(sungrow_borrow_cost / 1_000, 1),
        "dongfang_dividend_income": round(dongfang_dividend_income / 1_000, 1),
        "net_carry_cost": round(net_carry_cost / 1_000, 1),
        "net_carry_pct_of_notional": round(net_carry_cost / (sungrow_notional * 2) * 100, 2),
    }


def calculate_liquidity_capacity(
    dongfang_data: pd.DataFrame,
    sungrow_data: pd.DataFrame,
    target_notional: float,
) -> Dict:
    """Calculate how much capacity the trade has based on volume.
    
    Args:
        dongfang_data: Dongfang price/volume data
        sungrow_data: Sungrow price/volume data
        target_notional: Target position size
        
    Returns:
        Liquidity analysis
    """
    results = {}
    
    # Dongfang liquidity
    if dongfang_data is not None and not dongfang_data.empty and 'Volume' in dongfang_data.columns:
        avg_volume_dongfang = dongfang_data['Volume'].mean()
        avg_price_dongfang = dongfang_data['Close'].mean()
        daily_dollar_volume_dongfang = avg_volume_dongfang * avg_price_dongfang
        
        # Target position as % of daily volume (aim for < 10% to minimize market impact)
        dongfang_target = target_notional / 2
        dongfang_days_to_execute = dongfang_target / (daily_dollar_volume_dongfang * 0.10)
        
        results["dongfang_avg_daily_volume_m"] = round(avg_volume_dongfang / 1_000_000, 2)
        results["dongfang_daily_dollar_volume_mm"] = round(daily_dollar_volume_dongfang / 1_000_000, 1)
        results["dongfang_target_notional_mm"] = round(dongfang_target / 1_000_000, 1)
        results["dongfang_days_to_execute"] = round(dongfang_days_to_execute, 1)
        results["dongfang_liquid"] = dongfang_days_to_execute < 5
    else:
        results["dongfang_liquid"] = False
        results["dongfang_note"] = "Volume data unavailable"
    
    # Sungrow liquidity (should be excellent)
    if sungrow_data is not None and not sungrow_data.empty and 'Volume' in sungrow_data.columns:
        avg_volume_sungrow = sungrow_data['Volume'].mean()
        avg_price_sungrow = sungrow_data['Close'].mean()
        daily_dollar_volume_sungrow = avg_volume_sungrow * avg_price_sungrow
        
        sungrow_target = target_notional / 2
        sungrow_days_to_execute = sungrow_target / (daily_dollar_volume_sungrow * 0.10)
        
        results["sungrow_avg_daily_volume_m"] = round(avg_volume_sungrow / 1_000_000, 2)
        results["sungrow_daily_dollar_volume_mm"] = round(daily_dollar_volume_sungrow / 1_000_000, 1)
        results["sungrow_target_notional_mm"] = round(sungrow_target / 1_000_000, 1)
        results["sungrow_days_to_execute"] = round(sungrow_days_to_execute, 1)
        results["sungrow_liquid"] = sungrow_days_to_execute < 2
    else:
        results["sungrow_liquid"] = False
        results["sungrow_note"] = "Volume data unavailable"
    
    return results


def calculate_technical_levels(df: pd.DataFrame, window: int = 20) -> Dict:
    """Calculate basic technical levels.
    
    Args:
        df: Price data
        window: Lookback window for moving average
        
    Returns:
        Technical indicators
    """
    if df is None or df.empty:
        return {}
    
    # Simple moving average
    df['SMA20'] = df['Close'].rolling(window=window).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # RSI (14-period)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    current_price = df['Close'].iloc[-1]
    sma20 = df['SMA20'].iloc[-1]
    sma50 = df['SMA50'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    
    # Distance from moving averages
    dist_from_sma20 = (current_price - sma20) / sma20 * 100
    dist_from_sma50 = (current_price - sma50) / sma50 * 100
    
    # 52-week high/low
    high_52w = df['Close'].rolling(window=252).max().iloc[-1]
    low_52w = df['Close'].rolling(window=252).min().iloc[-1]
    pct_of_52w_high = current_price / high_52w * 100
    
    return {
        "current_price": round(current_price, 2),
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2),
        "rsi": round(rsi, 1),
        "dist_from_sma20_pct": round(dist_from_sma20, 1),
        "dist_from_sma50_pct": round(dist_from_sma50, 1),
        "52w_high": round(high_52w, 2),
        "52w_low": round(low_52w, 2),
        "pct_of_52w_high": round(pct_of_52w_high, 1),
        "above_sma20": current_price > sma20,
        "above_sma50": current_price > sma50,
        "overbought": rsi > 70,
        "oversold": rsi < 30,
    }


def save_trader_analysis(results: Dict, output_path: Path):
    """Save trader analysis to CSV."""
    # Flatten nested dicts
    flat_results = {}
    for key, value in results.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flat_results[f"{key}_{sub_key}"] = sub_value
        else:
            flat_results[key] = value
    
    df = pd.DataFrame([flat_results])
    df.to_csv(output_path, index=False)
    print(f"[SAVED] Trader analysis: {output_path}")


def main():
    """Run trader-focused analysis."""
    print("="*60)
    print("TRADER RISK & EXECUTION ANALYSIS")
    print("="*60)
    
    # Fetch data
    print("\n[1] Fetching price data...")
    dongfang_data = fetch_price_data(DONGFANG_TICKER, period="2y")
    sungrow_data = fetch_price_data(SUNGROW_TICKER, period="2y")

    if dongfang_data is None or sungrow_data is None:
        print("[ERROR] Failed to fetch required data")
        return
    
    # Calculate volatilities
    print("\n[2] Calculating volatilities...")
    dongfang_vol = calculate_volatility(dongfang_data)
    sungrow_vol = calculate_volatility(sungrow_data)
    
    # Pair volatility (simplified: assume 0.5 correlation)
    assumed_corr = 0.5
    pair_vol = np.sqrt(dongfang_vol**2 + sungrow_vol**2 - 2 * assumed_corr * dongfang_vol * sungrow_vol)
    
    print(f"  Dongfang vol: {dongfang_vol*100:.1f}%")
    print(f"  Sungrow vol: {sungrow_vol*100:.1f}%")
    print(f"  Pair vol (est): {pair_vol*100:.1f}%")
    
    # Position sizing
    print("\n[3] Calculating position sizing...")
    sizing = calculate_position_sizing(dongfang_vol, sungrow_vol, pair_vol)
    for key, value in sizing.items():
        print(f"  {key}: {value}")
    
    # Carry cost
    print("\n[4] Calculating carry cost...")
    sungrow_notional = sizing["short_sungrow_notional_mm"] * 1_000_000
    carry_low = calculate_carry_cost(sungrow_notional, SUNGROW_BORROW_COST_LOW)
    carry_high = calculate_carry_cost(sungrow_notional, SUNGROW_BORROW_COST_HIGH)
    print(f"  Low borrow cost scenario: {carry_low['net_carry_cost']}K")
    print(f"  High borrow cost scenario: {carry_high['net_carry_cost']}K")
    
    # Liquidity
    print("\n[5] Analyzing liquidity...")
    target_notional = sizing["recommended_notional_mm"] * 1_000_000
    liquidity = calculate_liquidity_capacity(dongfang_data, sungrow_data, target_notional)
    for key, value in liquidity.items():
        print(f"  {key}: {value}")
    
    # Technicals
    print("\n[6] Technical analysis...")
    dongfang_tech = calculate_technical_levels(dongfang_data)
    sungrow_tech = calculate_technical_levels(sungrow_data)
    
    print(f"  Dongfang: RSI={dongfang_tech.get('rsi')}, % of 52w high={dongfang_tech.get('pct_of_52w_high')}%")
    print(f"  Sungrow: RSI={sungrow_tech.get('rsi')}, % of 52w high={sungrow_tech.get('pct_of_52w_high')}%")
    
    # Compile results
    results = {
        "volatilities": {
            "dongfang_vol": round(dongfang_vol * 100, 1),
            "sungrow_vol": round(sungrow_vol * 100, 1),
            "pair_vol": round(pair_vol * 100, 1),
        },
        "position_sizing": sizing,
        "carry_cost_low_borrow": carry_low,
        "carry_cost_high_borrow": carry_high,
        "liquidity": liquidity,
        "technicals": {
            "dongfang_rsi": dongfang_tech.get("rsi"),
            "dongfang_pct_52w_high": dongfang_tech.get("pct_of_52w_high"),
            "sungrow_rsi": sungrow_tech.get("rsi"),
            "sungrow_pct_52w_high": sungrow_tech.get("pct_of_52w_high"),
        },
    }
    
    # Save
    output_path = Path("data/processed/valuation/trader_analysis.csv")
    save_trader_analysis(results, output_path)
    
    print("\n" + "="*60)
    print("TRADER ANALYSIS COMPLETE")
    print("="*60)
    print("\nKey Takeaways for Traders:")
    print(f"1. Recommended position: {sizing['recommended_notional_mm']}mm ({sizing['recommended_position_pct']}% of portfolio)")
    print(f"2. Carry cost: {carry_low['net_carry_cost']}K - {carry_high['net_carry_cost']}K (depending on borrow)")
    print(f"3. Dongfang is {dongfang_tech.get('pct_of_52w_high')}% of 52-week high — {'extended' if dongfang_tech.get('pct_of_52w_high', 0) > 90 else 'reasonable entry' if dongfang_tech.get('pct_of_52w_high', 0) > 70 else 'potential oversold bounce'}")
    print(f"4. Liquidity: {'Sufficient' if liquidity.get('dongfang_liquid') else 'Check before sizing'}")


if __name__ == "__main__":
    main()
