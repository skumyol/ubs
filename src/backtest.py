#!/usr/bin/env python3
"""Oil price vs Dongfang/Jereh correlation backtest.

Shows historical divergence between oil prices and oilfield services stocks
vs grid infrastructure stocks — proving the "higher oil != higher service earnings" thesis.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from src.pair_config import LONG_LEG, SHORT_LEG

# Config
OUTPUT_DIR = Path("outputs/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Ticker mapping
OIL_TICKER = "CL=F"  # Crude Oil Futures
SHORT_TICKER = SHORT_LEG.ticker
LONG_TICKER = LONG_LEG.ticker


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


def calculate_normalized_returns(df: pd.DataFrame) -> pd.Series:
    """Calculate normalized returns (base 100)."""
    if df is None or df.empty:
        return pd.Series()
    returns = df['Close'].pct_change().dropna()
    normalized = (1 + returns).cumprod() * 100
    return normalized


def calculate_correlation(series1: pd.Series, series2: pd.Series) -> float:
    """Calculate rolling correlation between two price series."""
    # Align dates
    aligned = pd.concat([series1, series2], axis=1, sort=False).dropna()
    if len(aligned) < 30:
        return 0.0
    return aligned.iloc[:, 0].corr(aligned.iloc[:, 1])


def calculate_pair_trade_pnl(
    long_data: pd.DataFrame,
    short_data: pd.DataFrame,
    long_weight: float = 0.5,
    short_weight: float = 0.5
) -> pd.Series:
    """Calculate pair trade P&L: long Dongfang, short Jereh.
    
    Args:
        long_data: Long leg price data
        short_data: Short leg price data
        long_weight: Capital allocation to long (default 50%)
        short_weight: Capital allocation to short (default 50%)
        
    Returns:
        Cumulative P&L series (base 100)
    """
    if long_data is None or short_data is None or long_data.empty or short_data.empty:
        return pd.Series()
    
    # Normalize both to base 100
    long_norm = (long_data['Close'] / long_data['Close'].iloc[0]) * 100
    short_norm = (short_data['Close'] / short_data['Close'].iloc[0]) * 100
    
    # Align dates
    aligned = pd.DataFrame({
        'long': long_norm,
        'short': short_norm
    }).dropna()
    
    if aligned.empty:
        return pd.Series()
    
    # Pair = long - short (dollar-neutral, equal-weighted)
    # Long leg contributes +, short leg contributes -
    pair_pnl = long_weight * (aligned['long'] - 100) - short_weight * (aligned['short'] - 100)
    
    return pair_pnl


def create_pair_trade_chart(
    long_data: pd.DataFrame,
    short_data: pd.DataFrame,
    output_path: Path,
    long_weight: float = 0.5,
    short_weight: float = 0.5
) -> Dict:
    """Create pair trade P&L chart.
    
    Args:
        long_data: Long leg (Dongfang)
        short_data: Short leg (Jereh)
        output_path: Where to save chart
        long_weight: Capital weight
        short_weight: Capital weight
        
    Returns:
        Chart info dict
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
    
    # Top chart: Individual legs normalized
    ax1 = axes[0]
    
    if long_data is not None and not long_data.empty:
        long_norm = (long_data['Close'] / long_data['Close'].iloc[0]) * 100
        ax1.plot(long_norm.index, long_norm.values, label=f'Long: {LONG_LEG.name} ({LONG_LEG.ticker})', 
                color='green', linewidth=2)
    
    if short_data is not None and not short_data.empty:
        short_norm = (short_data['Close'] / short_data['Close'].iloc[0]) * 100
        ax1.plot(short_norm.index, short_norm.values, label=f'Short: {SHORT_LEG.name}', 
                color='red', linewidth=2)
    
    ax1.axhline(y=100, color='gray', linestyle='--', alpha=0.5)
    ax1.set_title('Individual Leg Performance (Base 100)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Normalized Price')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Bottom chart: Pair trade P&L
    ax2 = axes[1]
    
    pair_pnl = calculate_pair_trade_pnl(long_data, short_data, long_weight, short_weight)
    if not pair_pnl.empty:
        ax2.plot(pair_pnl.index, pair_pnl.values, label='Pair Trade P&L', 
                color='blue', linewidth=2.5)
        ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax2.fill_between(pair_pnl.index, pair_pnl.values, 0,
                        where=(pair_pnl.values > 0), alpha=0.3, color='green')
        ax2.fill_between(pair_pnl.index, pair_pnl.values, 0,
                        where=(pair_pnl.values < 0), alpha=0.3, color='red')
        
        # Annotate final P&L
        final_pnl = pair_pnl.iloc[-1]
        ax2.annotate(f'Final P&L: +{final_pnl:.1f}%',
                    xy=(pair_pnl.index[-1], final_pnl),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen' if final_pnl > 0 else 'lightcoral',
                             alpha=0.8))
    
    ax2.set_title(f'Pair Trade Spread: Long {LONG_LEG.name} / Short {SHORT_LEG.name} ({long_weight*100:.0f}%-{short_weight*100:.0f}% weight)', 
                 fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cumulative P&L (%)')
    ax2.set_xlabel('Date')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[SAVED] Pair trade chart: {output_path}")
    
    # Calculate statistics
    stats = {}
    if not pair_pnl.empty:
        stats['pair_final_pnl_pct'] = round(pair_pnl.iloc[-1], 1)
        stats['pair_max_pnl_pct'] = round(pair_pnl.max(), 1)
        stats['pair_min_pnl_pct'] = round(pair_pnl.min(), 1)
        stats['pair_volatility'] = round(pair_pnl.std(), 1)
        # Sharpe-like ratio (annualized return / annualized vol)
        if len(pair_pnl) > 1:
            daily_return = pair_pnl.iloc[-1] / len(pair_pnl)
            annualized_return = daily_return * 252
            annualized_vol = pair_pnl.std() * np.sqrt(252)
            stats['pair_sharpe_approx'] = round(annualized_return / annualized_vol, 2) if annualized_vol > 0 else 0
    
    return stats


def create_correlation_chart(
    oil_data: pd.DataFrame,
    short_data: pd.DataFrame,
    long_data: Optional[pd.DataFrame],
    output_path: Path
) -> Dict:
    """Create correlation divergence chart."""
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
    
    # Calculate normalized prices (base 100)
    oil_norm = calculate_normalized_returns(oil_data)
    short_norm = calculate_normalized_returns(short_data)
    
    # Top chart: Price comparison
    ax1 = axes[0]
    ax1.plot(oil_norm.index, oil_norm.values, label='Oil (CL=F)', color='black', linewidth=2)
    ax1.plot(short_norm.index, short_norm.values, label=f'{SHORT_LEG.name} ({SHORT_LEG.ticker})', color='red', linewidth=2)
    
    if long_data is not None and not long_data.empty:
        long_norm = calculate_normalized_returns(long_data)
        ax1.plot(long_norm.index, long_norm.values, label=f'{LONG_LEG.name} ({LONG_LEG.ticker})', color='green', linewidth=2)
    
    ax1.set_title(f'Price Performance: Oil vs {SHORT_LEG.name} vs {LONG_LEG.name} (Base 100)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Normalized Price (Base 100)')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Bottom chart: Rolling correlation (6-month)
    ax2 = axes[1]
    
    # Calculate rolling correlation
    if len(oil_norm) > 0 and len(short_norm) > 0:
        # Align and calculate rolling correlation
        aligned = pd.DataFrame({
            'oil': oil_norm.reindex(short_norm.index, method='ffill'),
            'short': short_norm
        }).dropna()
        
        if len(aligned) > 60:
            rolling_corr = aligned['oil'].rolling(window=60).corr(aligned['short'])
            ax2.plot(rolling_corr.index, rolling_corr.values, label=f'Oil-{SHORT_LEG.name} Correlation', color='red', linewidth=2)
            ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            ax2.fill_between(rolling_corr.index, rolling_corr.values, 0, 
                            where=(rolling_corr.values > 0), alpha=0.3, color='green')
            ax2.fill_between(rolling_corr.index, rolling_corr.values, 0, 
                            where=(rolling_corr.values < 0), alpha=0.3, color='red')
    
    ax2.set_title(f'6-Month Rolling Correlation: Oil vs {SHORT_LEG.name}', fontsize=12)
    ax2.set_ylabel('Correlation')
    ax2.set_xlabel('Date')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(-1, 1)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[SAVED] Correlation chart: {output_path}")
    
    return {
        'chart_path': str(output_path),
        'oil_data_points': len(oil_data) if oil_data is not None else 0,
        'short_data_points': len(short_data) if short_data is not None else 0,
    }


def create_divergence_summary(
    oil_data: pd.DataFrame,
    short_data: pd.DataFrame,
    long_data: Optional[pd.DataFrame]
) -> Dict:
    """Create summary statistics for the divergence analysis."""
    results = {}
    
    if oil_data is not None and not oil_data.empty:
        oil_return = (oil_data['Close'].iloc[-1] / oil_data['Close'].iloc[0] - 1) * 100
        results['oil_2y_return'] = round(oil_return, 1)
    else:
        results['oil_2y_return'] = None
    
    if short_data is not None and not short_data.empty:
        short_return = (short_data['Close'].iloc[-1] / short_data['Close'].iloc[0] - 1) * 100
        results['short_2y_return'] = round(short_return, 1)
    else:
        results['short_2y_return'] = None
    
    if long_data is not None and not long_data.empty:
        long_return = (long_data['Close'].iloc[-1] / long_data['Close'].iloc[0] - 1) * 100
        results['long_2y_return'] = round(long_return, 1)
    else:
        results['long_2y_return'] = None
    
    # Calculate correlation
    if oil_data is not None and short_data is not None:
        oil_norm = calculate_normalized_returns(oil_data)
        short_norm = calculate_normalized_returns(short_data)
        corr = calculate_correlation(oil_norm, short_norm)
        results['oil_short_correlation'] = round(corr, 3)
    else:
        results['oil_short_correlation'] = None
    
    # Thesis insight
    if results.get('oil_2y_return') and results.get('short_2y_return'):
        if results['oil_2y_return'] > 0 and results['short_2y_return'] < 0:
            results['thesis_validation'] = f"✓ VALIDATED: Oil up, {SHORT_LEG.name} down — supports short thesis"
        elif results['oil_2y_return'] > 0 and results['short_2y_return'] > 0:
            results['thesis_validation'] = f"⚠ Oil up, {SHORT_LEG.name} up — correlation still positive"
        else:
            results['thesis_validation'] = "⚠ Oil down — cycle not captured in period"
    
    return results


def save_backtest_results(results: Dict, output_path: Path):
    """Save backtest results to CSV."""
    df = pd.DataFrame([results])
    df.to_csv(output_path, index=False)
    print(f"[SAVED] Backtest results: {output_path}")


def main():
    """Run the full backtest analysis."""
    print("="*60)
    print(f"OIL PRICE vs {SHORT_LEG.name}/{LONG_LEG.name} BACKTEST")
    print("="*60)
    
    # Fetch data
    print("\n[1] Fetching price data...")
    oil_data = fetch_price_data(OIL_TICKER, period="2y")
    short_data = fetch_price_data(SHORT_TICKER, period="2y")
    long_data = fetch_price_data(LONG_TICKER, period="2y")
    
    if oil_data is None or short_data is None:
        print(f"[ERROR] Failed to fetch required data (oil or {SHORT_LEG.name})")
        return
    
    # Create correlation chart
    print("\n[2] Creating correlation chart...")
    chart_path = OUTPUT_DIR / "oil_jereh_correlation.png"
    chart_info = create_correlation_chart(oil_data, short_data, long_data, chart_path)
    
    # Create pair trade chart
    print("\n[3] Creating pair trade backtest chart...")
    pair_chart_path = OUTPUT_DIR / "pair_trade_backtest.png"
    pair_stats = create_pair_trade_chart(long_data, short_data, pair_chart_path)
    
    # Generate summary
    print("\n[4] Generating summary statistics...")
    summary = create_divergence_summary(oil_data, short_data, long_data)
    summary.update(chart_info)
    summary.update(pair_stats)
    
    # Print results
    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    for key, value in summary.items():
        if key != 'chart_path':
            print(f"  {key}: {value}")
    
    # Save results
    results_path = Path("data/processed/valuation/oil_jereh_backtest.csv")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    save_backtest_results(summary, results_path)
    
    print("\n" + "="*60)
    print("BACKTEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
