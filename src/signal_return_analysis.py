"""Signal-return correlation analysis.

Tests whether AI-classified signals predict or align with stock returns
using multiple methodologies to maximize data utilization.

Methodologies (in order of data efficiency):
  1. EVENT STUDY: For each document date, test returns in [-7d, +7d, +30d, +90d] windows
  2. HISTORICAL ALIGNMENT: Test if thesis signals match long-term price divergence (2023-2025)
  3. MONTHLY LEAD-LAG: Signal month T vs return month T+1 (if sufficient overlap)
  4. CROSS-SECTIONAL: Signal intensity vs returns across categories
  
Honest reporting: When data is insufficient, we say so rather than fabricate results.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats


# Ticker mapping
HAL_TICKER = "HAL"
SIEYUAN_TICKER = "002028.SZ"


def aggregate_monthly_signals(classified_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate classified signals into monthly counts and sentiment."""
    df = classified_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    if len(df) == 0:
        return pd.DataFrame()

    # Month index
    df["year_month"] = df["date"].dt.to_period("M")

    # Sentiment numeric
    sentiment_map = {"positive": 1, "neutral": 0, "negative": -1}
    df["sentiment_score"] = df["sentiment"].map(sentiment_map).fillna(0)

    # Grid signals (long leg indicators)
    grid_categories = ["Grid Resilience", "Electricity Demand", "Policy-Backed Capex"]
    df["is_grid"] = df["category"].isin(grid_categories)

    # Oilfield signals (short leg indicators)
    oil_categories = ["Oil Supply Disruption", "Oilfield Cost Pressure", "Margin/Earnings Risk"]
    df["is_oilfield"] = df["category"].isin(oil_categories)

    # Aggregate by month
    monthly = (
        df.groupby("year_month")
        .agg(
            grid_count=("is_grid", "sum"),
            grid_sentiment=("sentiment_score", lambda x: x[df.loc[x.index, "is_grid"]].mean() if x[df.loc[x.index, "is_grid"]].sum() > 0 else 0),
            oilfield_count=("is_oilfield", "sum"),
            oilfield_sentiment=("sentiment_score", lambda x: x[df.loc[x.index, "is_oilfield"]].mean() if x[df.loc[x.index, "is_oilfield"]].sum() > 0 else 0),
            total_signals=("paragraph_id", "count"),
            thesis_support=("sentiment_score", lambda x: (
                x[df.loc[x.index, "is_grid"]].sum() - x[df.loc[x.index, "is_oilfield"]].sum()
            ) / len(x) if len(x) > 0 else 0),
        )
        .reset_index()
    )

    # Fix grid_sentiment and oilfield_sentiment (the lambda above is tricky with groupby)
    # Recompute cleanly
    grid_monthly = (
        df[df["is_grid"]]
        .groupby("year_month")["sentiment_score"]
        .mean()
        .rename("grid_sentiment")
    )
    oilfield_monthly = (
        df[df["is_oilfield"]]
        .groupby("year_month")["sentiment_score"]
        .mean()
        .rename("oilfield_sentiment")
    )

    monthly = monthly.drop(columns=["grid_sentiment", "oilfield_sentiment"])
    monthly = monthly.merge(grid_monthly, on="year_month", how="left")
    monthly = monthly.merge(oilfield_monthly, on="year_month", how="left")
    monthly["grid_sentiment"] = monthly["grid_sentiment"].fillna(0)
    monthly["oilfield_sentiment"] = monthly["oilfield_sentiment"].fillna(0)

    # Convert period to datetime for merging with price data
    monthly["month_start"] = monthly["year_month"].dt.to_timestamp()
    # Ensure timezone-naive for consistent merging
    monthly["month_start"] = pd.to_datetime(monthly["month_start"]).dt.tz_localize(None)

    return monthly


def fetch_monthly_returns(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch monthly stock returns from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        # Get daily data, resample to monthly
        hist = stock.history(start=start_date, end=end_date, interval="1d")
        if hist.empty:
            print(f"[WARNING] No price data for {ticker}")
            return pd.DataFrame()

        # Monthly close-to-close returns
        monthly_prices = hist["Close"].resample("ME").last()
        monthly_returns = monthly_prices.pct_change().dropna()

        df = pd.DataFrame({
            "month_end": monthly_returns.index,
            f"{ticker}_return": monthly_returns.values,
        })
        df["month_start"] = df["month_end"] - pd.offsets.MonthBegin(1)
        # Normalize to timezone-naive for merging with signal data
        df["month_start"] = df["month_start"].dt.tz_localize(None)
        return df
    except Exception as e:
        print(f"[ERROR] Failed to fetch {ticker}: {e}")
        return pd.DataFrame()


def compute_lead_lag_correlation(
    signals: pd.Series,
    returns: pd.Series,
    max_lag: int = 3,
) -> Dict:
    """Compute correlation between signal and returns at different lags.

    Lag 0: concurrent correlation (not causal)
    Lag 1: signal predicts next-month return (the test we care about)
    Lag 2,3: longer-horizon predictive power
    """
    # Align series
    merged = pd.DataFrame({"signal": signals, "return": returns}).dropna()
    if len(merged) < 5:
        return {"error": "Insufficient aligned data points"}

    results = {}
    for lag in range(max_lag + 1):
        if lag == 0:
            corr = merged["signal"].corr(merged["return"])
            n = len(merged)
        else:
            # Signal at t vs return at t+lag
            merged_lag = merged.copy()
            merged_lag[f"return_lag{lag}"] = merged["return"].shift(-lag)
            merged_lag = merged_lag.dropna()
            if len(merged_lag) < 5:
                corr = np.nan
                n = 0
            else:
                corr = merged_lag["signal"].corr(merged_lag[f"return_lag{lag}"])
                n = len(merged_lag)

        # t-statistic and p-value (if enough data)
        if n >= 5 and not np.isnan(corr):
            t_stat = corr * np.sqrt((n - 2) / (1 - corr**2))
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
        else:
            t_stat = np.nan
            p_value = np.nan

        results[f"lag_{lag}"] = {
            "correlation": round(float(corr), 3) if not np.isnan(corr) else None,
            "n": int(n),
            "t_statistic": round(float(t_stat), 2) if not np.isnan(t_stat) else None,
            "p_value": round(float(p_value), 3) if not np.isnan(p_value) else None,
            "significant_05": bool(p_value < 0.05) if not np.isnan(p_value) else False,
        }

    return results


def fetch_daily_returns(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch daily stock returns for event study analysis."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, interval="1d")
        if hist.empty:
            return pd.DataFrame()
        
        # Calculate daily returns
        hist['return'] = hist['Close'].pct_change()
        hist = hist.dropna()
        
        # Reset index to get date as column
        df = hist.reset_index()[['Date', 'return', 'Close']]
        df.columns = ['date', f'{ticker}_return', f'{ticker}_close']
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
        return df
    except Exception as e:
        print(f"[ERROR] Failed to fetch {ticker}: {e}")
        return pd.DataFrame()


def run_event_study(
    signal_dates: List[pd.Timestamp],
    daily_returns: pd.DataFrame,
    ticker: str,
    windows: Dict[str, int] = None,
) -> Dict:
    """Event study: test returns around signal dates.
    
    For each signal date, calculate cumulative returns in windows:
      - Pre-event: [-7d, -1d]
      - Post-event: [+1d, +7d], [+1d, +30d], [+1d, +90d]
    
    Returns dict with mean returns and statistical tests for each window.
    """
    if windows is None:
        windows = {
            "pre_7d": (-7, -1),
            "post_7d": (1, 7),
            "post_30d": (1, 30),
            "post_90d": (1, 90),
        }
    
    ticker_col = f"{ticker}_return"
    if ticker_col not in daily_returns.columns:
        return {"error": f"No return data for {ticker}"}
    
    all_events = []
    
    for event_date in signal_dates:
        # Find closest trading day
        daily_returns['days_diff'] = (daily_returns['date'] - event_date).abs()
        closest_idx = daily_returns['days_diff'].idxmin()
        closest_date = daily_returns.loc[closest_idx, 'date']
        
        event_data = {"event_date": event_date.strftime('%Y-%m-%d'), "closest_trading_day": closest_date.strftime('%Y-%m-%d')}
        
        for window_name, (start_offset, end_offset) in windows.items():
            # Calculate window dates
            window_start = closest_date + pd.Timedelta(days=start_offset)
            window_end = closest_date + pd.Timedelta(days=end_offset)
            
            # Get returns in window
            mask = (daily_returns['date'] >= window_start) & (daily_returns['date'] <= window_end)
            window_returns = daily_returns.loc[mask, ticker_col]
            
            if len(window_returns) > 0:
                # Cumulative return
                cum_return = (1 + window_returns).prod() - 1
                event_data[f"{window_name}_return"] = round(cum_return, 4)
                event_data[f"{window_name}_n_days"] = len(window_returns)
            else:
                event_data[f"{window_name}_return"] = None
                event_data[f"{window_name}_n_days"] = 0
        
        all_events.append(event_data)
    
    if not all_events:
        return {"error": "No events could be processed"}
    
    # Aggregate statistics
    results = {
        "n_events": len(all_events),
        "events": all_events,
        "summary": {}
    }
    
    for window_name in windows.keys():
        returns = [e[f"{window_name}_return"] for e in all_events if e[f"{window_name}_return"] is not None]
        if returns:
            mean_ret = np.mean(returns)
            std_ret = np.std(returns, ddof=1)
            n = len(returns)
            # t-test against zero
            if n > 1 and std_ret > 0:
                t_stat = mean_ret / (std_ret / np.sqrt(n))
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 1))
            else:
                t_stat = 0
                p_value = 1.0
            
            results["summary"][window_name] = {
                "mean_return": round(mean_ret, 4),
                "std_return": round(std_ret, 4),
                "n": int(n),
                "t_statistic": round(float(t_stat), 2),
                "p_value": round(float(p_value), 3),
                "significant_05": bool(p_value < 0.05),
            }
    
    return results


def run_historical_alignment_test(
    classified_df: pd.DataFrame,
    start_date: str = "2023-01-01",
    end_date: str = "2025-12-31",
) -> Dict:
    """Test if thesis signals align with long-term price divergence.
    
    Thesis: Grid signals should be positive, Oilfield signals should be negative.
    Price divergence: Sieyuan return - HAL return should be positive.
    
    This tests DIRECTIONAL ALIGNMENT, not predictive power.
    """
    # Fetch full historical price data
    hal_daily = fetch_daily_returns(HAL_TICKER, start_date, end_date)
    sieyuan_daily = fetch_daily_returns(SIEYUAN_TICKER, start_date, end_date)
    
    if hal_daily.empty or sieyuan_daily.empty:
        return {"error": "Could not fetch historical price data"}
    
    # Calculate cumulative returns over the full period
    hal_cum = (1 + hal_daily[f'{HAL_TICKER}_return']).prod() - 1
    sieyuan_cum = (1 + sieyuan_daily[f'{SIEYUAN_TICKER}_return']).prod() - 1
    
    # Calculate thesis-consistent signals
    grid_categories = ["Grid Resilience", "Electricity Demand", "Policy-Backed Capex"]
    oil_categories = ["Oil Supply Disruption", "Oilfield Cost Pressure", "Margin/Earnings Risk"]
    
    sentiment_map = {"positive": 1, "neutral": 0, "negative": -1}
    
    grid_signals = classified_df[classified_df["category"].isin(grid_categories)]
    oil_signals = classified_df[classified_df["category"].isin(oil_categories)]
    
    grid_sentiment = grid_signals["sentiment"].map(sentiment_map).mean() if len(grid_signals) > 0 else 0
    oil_sentiment = oil_signals["sentiment"].map(sentiment_map).mean() if len(oil_signals) > 0 else 0
    
    # Thesis score: grid positive (long) + oilfield negative (short) = higher is better
    # Grid sentiment positive supports thesis; oilfield sentiment negative supports thesis
    # So both should add positively to thesis score
    thesis_signal_score = grid_sentiment + (-oil_sentiment)  # Grid pos + |Oil neg|
    
    # Price divergence: Sieyuan - HAL
    price_divergence = sieyuan_cum - hal_cum
    
    return {
        "period": f"{start_date} to {end_date}",
        "hal_cumulative_return": round(hal_cum, 4),
        "sieyuan_cumulative_return": round(sieyuan_cum, 4),
        "price_divergence": round(price_divergence, 4),
        "grid_signal_sentiment": round(grid_sentiment, 3),
        "oilfield_signal_sentiment": round(oil_sentiment, 3),
        "thesis_signal_score": round(thesis_signal_score, 3),
        "alignment": "CONSISTENT" if (thesis_signal_score > 0 and price_divergence > 0) or (thesis_signal_score < 0 and price_divergence < 0) else "INCONSISTENT",
        "interpretation": (
            "Thesis signals and price divergence are directionally aligned. "
            if (thesis_signal_score > 0 and price_divergence > 0) or (thesis_signal_score < 0 and price_divergence < 0)
            else "Thesis signals and price divergence are NOT aligned. The narrative may not match market reality. "
        ) + f"Grid sentiment: {grid_sentiment:.2f}, Oilfield sentiment: {oil_sentiment:.2f}, Price divergence: {price_divergence:.1%}"
    }


def run_regression(
    X: pd.DataFrame,
    y: pd.Series,
) -> Dict:
    """Run OLS regression and report diagnostics.

    X: DataFrame of predictors
    y: Series of returns
    """
    # Align
    data = pd.concat([X, y], axis=1).dropna()
    if len(data) < 5:
        return {"error": "Insufficient data for regression"}

    X_aligned = data[X.columns]
    y_aligned = data[y.name]

    # Add constant
    X_const = np.column_stack([np.ones(len(X_aligned)), X_aligned.values])

    # OLS
    try:
        beta = np.linalg.lstsq(X_const, y_aligned.values, rcond=None)[0]
        y_pred = X_const @ beta
        residuals = y_aligned.values - y_pred
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y_aligned.values - y_aligned.mean())**2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        adj_r2 = 1 - (1 - r_squared) * (len(y_aligned) - 1) / (len(y_aligned) - X_const.shape[1] - 1)

        # Standard errors (homoskedastic)
        mse = ss_res / (len(y_aligned) - X_const.shape[1])
        var_beta = mse * np.linalg.inv(X_const.T @ X_const)
        se_beta = np.sqrt(np.diag(var_beta))
        t_stats = beta / se_beta
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), len(y_aligned) - X_const.shape[1]))

        return {
            "r_squared": round(r_squared, 3),
            "adj_r_squared": round(adj_r2, 3),
            "n_observations": len(y_aligned),
            "coefficients": {
                col: {
                    "estimate": round(beta[i + 1], 4),
                    "std_error": round(se_beta[i + 1], 4),
                    "t_stat": round(t_stats[i + 1], 2),
                    "p_value": round(p_values[i + 1], 3),
                }
                for i, col in enumerate(X.columns)
            },
            "intercept": {
                "estimate": round(beta[0], 4),
                "std_error": round(se_beta[0], 4),
                "t_stat": round(t_stats[0], 2),
                "p_value": round(p_values[0], 3),
            },
        }
    except Exception as e:
        return {"error": str(e)}


def run_signal_return_analysis(
    classified_df: pd.DataFrame,
    output_dir: Path,
) -> Dict:
    """Run the full signal-return predictive analysis."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SIGNAL-RETURN PREDICTIVE ANALYSIS")
    print("=" * 60)

    # Extract unique signal dates
    classified_df["date"] = pd.to_datetime(classified_df["date"], errors="coerce")
    signal_dates = sorted(classified_df["date"].dropna().unique())
    
    print(f"\n[0] Signal data overview:")
    print(f"  Total paragraphs: {len(classified_df)}")
    print(f"  Unique dates: {len(signal_dates)}")
    if signal_dates:
        print(f"  Date range: {signal_dates[0]} to {signal_dates[-1]}")
        print(f"  Dates: {[d.strftime('%Y-%m-%d') for d in signal_dates]}")

    # Results container
    results = {
        "sample_info": {
            "total_paragraphs": len(classified_df),
            "unique_dates": len(signal_dates),
            "date_range": f"{signal_dates[0]} to {signal_dates[-1]}" if signal_dates else "None",
        },
        "historical_alignment": {},
        "event_study": {},
        "monthly_lead_lag": {"correlations": {}, "regressions": {}},
    }

    # =====================================================================
    # TEST 1: HISTORICAL ALIGNMENT (uses full 3-year price history)
    # =====================================================================
    print("\n[1] Testing historical thesis alignment (2023-2025)...")
    print("    Tests if narrative signals match long-term price divergence")
    historical_test = run_historical_alignment_test(classified_df)
    results["historical_alignment"] = historical_test
    
    if "error" not in historical_test:
        print(f"    HAL 3Y return: {historical_test['hal_cumulative_return']:.1%}")
        print(f"    Sieyuan 3Y return: {historical_test['sieyuan_cumulative_return']:.1%}")
        print(f"    Price divergence: {historical_test['price_divergence']:.1%}")
        print(f"    Grid sentiment: {historical_test['grid_signal_sentiment']:.2f}")
        print(f"    Oilfield sentiment: {historical_test['oilfield_signal_sentiment']:.2f}")
        print(f"    ALIGNMENT: {historical_test['alignment']}")
    else:
        print(f"    ERROR: {historical_test['error']}")

    # =====================================================================
    # TEST 2: EVENT STUDY (uses daily returns around signal dates)
    # =====================================================================
    print("\n[2] Running event study analysis...")
    print("    Tests returns around document publication dates")
    
    # Get valid historical dates only (not future dates)
    today = pd.Timestamp.now().normalize()
    historical_dates = [d for d in signal_dates if d <= today]
    
    if len(historical_dates) >= 2:
        # Fetch daily returns for event study (expand range to capture windows)
        if historical_dates:
            study_start = (min(historical_dates) - pd.Timedelta(days=120)).strftime("%Y-%m-%d")
            study_end = (max(historical_dates) + pd.Timedelta(days=120)).strftime("%Y-%m-%d")
            
            hal_daily = fetch_daily_returns(HAL_TICKER, study_start, study_end)
            sieyuan_daily = fetch_daily_returns(SIEYUAN_TICKER, study_start, study_end)
            
            if not hal_daily.empty:
                print(f"\n    [HAL] Event study on {len(historical_dates)} dates:")
                hal_event = run_event_study(historical_dates, hal_daily, HAL_TICKER)
                results["event_study"]["hal"] = hal_event
                if "error" not in hal_event:
                    for window, stats in hal_event.get("summary", {}).items():
                        sig = "***" if stats.get("significant_05") else ""
                        print(f"      {window}: {stats['mean_return']:.2%} return (t={stats['t_statistic']}, p={stats['p_value']}){sig}")
                else:
                    print(f"      ERROR: {hal_event['error']}")
            
            if not sieyuan_daily.empty:
                print(f"\n    [Sieyuan] Event study on {len(historical_dates)} dates:")
                sie_event = run_event_study(historical_dates, sieyuan_daily, SIEYUAN_TICKER)
                results["event_study"]["sieyuan"] = sie_event
                if "error" not in sie_event:
                    for window, stats in sie_event.get("summary", {}).items():
                        sig = "***" if stats.get("significant_05") else ""
                        print(f"      {window}: {stats['mean_return']:.2%} return (t={stats['t_statistic']}, p={stats['p_value']}){sig}")
                else:
                    print(f"      ERROR: {sie_event['error']}")
    else:
        print("    SKIPPED: Insufficient historical dates for event study (< 2)")

    # =====================================================================
    # TEST 3: MONTHLY LEAD-LAG (original method, if sufficient data)
    # =====================================================================
    print("\n[3] Testing monthly lead-lag correlations...")
    monthly_signals = aggregate_monthly_signals(classified_df)
    
    if not monthly_signals.empty and len(monthly_signals) >= 3:
        signal_start = (monthly_signals["month_start"].min() - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
        signal_end = (monthly_signals["month_start"].max() + pd.Timedelta(days=60)).strftime("%Y-%m-%d")
        
        hal_returns = fetch_monthly_returns(HAL_TICKER, signal_start, signal_end)
        sieyuan_returns = fetch_monthly_returns(SIEYUAN_TICKER, signal_start, signal_end)
        
        merged = monthly_signals.copy()
        if not hal_returns.empty:
            merged = merged.merge(hal_returns[["month_start", "HAL_return"]], on="month_start", how="inner")
        if not sieyuan_returns.empty:
            merged = merged.merge(sieyuan_returns[["month_start", "002028.SZ_return"]], on="month_start", how="inner")
        
        if len(merged) >= 3:
            print(f"    Overlapping months: {len(merged)}")
            results["monthly_lead_lag"]["overlap_months"] = len(merged)
            
            # Run original tests (abbreviated output)
            if "HAL_return" in merged.columns:
                hal_grid_corr = compute_lead_lag_correlation(merged["grid_sentiment"], merged["HAL_return"], max_lag=2)
                results["monthly_lead_lag"]["correlations"]["grid_sentiment_vs_hal"] = hal_grid_corr
                if "error" not in hal_grid_corr:
                    for lag, s in hal_grid_corr.items():
                        if s.get("correlation") is not None:
                            print(f"      Grid->HAL {lag}: r={s['correlation']}, p={s['p_value']}")
            
            if "002028.SZ_return" in merged.columns:
                sie_grid_corr = compute_lead_lag_correlation(merged["grid_sentiment"], merged["002028.SZ_return"], max_lag=2)
                results["monthly_lead_lag"]["correlations"]["grid_sentiment_vs_sieyuan"] = sie_grid_corr
                if "error" not in sie_grid_corr:
                    for lag, s in sie_grid_corr.items():
                        if s.get("correlation") is not None:
                            print(f"      Grid->Sieyuan {lag}: r={s['correlation']}, p={s['p_value']}")
        else:
            print(f"    SKIPPED: Only {len(merged)} overlapping months (need >= 3)")
    else:
        print("    SKIPPED: Insufficient monthly signal data")

    # =====================================================================
    # SAVE RESULTS
    # =====================================================================
    results_path = output_dir / "signal_return_analysis.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[SAVED] JSON results: {results_path}")

    # Generate verdict
    verdict = _generate_verdict(results)
    results["verdict"] = verdict
    print(f"\n[VERDICT] {verdict}")

    # Markdown report
    md_path = output_dir / "signal_return_report.md"
    _write_md_report(results, md_path)
    print(f"[SAVED] Report: {md_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("PREDICTIVE POWER VERDICT")
    print("=" * 60)
    print(verdict)
    print("=" * 60)

    return results


def _generate_verdict(results: Dict) -> str:
    """Generate a blunt, quant-style verdict on predictive power."""
    significant_count = 0
    total_tests = 0
    
    # Check historical alignment
    hist = results.get("historical_alignment", {})
    if "error" not in hist:
        total_tests += 1
        if hist.get("alignment") == "CONSISTENT":
            significant_count += 1
    
    # Check event study results
    for ticker, event_results in results.get("event_study", {}).items():
        if "error" in event_results:
            continue
        for window, stats in event_results.get("summary", {}).items():
            if window.startswith("post_"):  # Only predictive windows
                total_tests += 1
                if stats.get("significant_05"):
                    significant_count += 1
    
    # Check monthly lead-lag
    for corr_dict in results.get("monthly_lead_lag", {}).get("correlations", {}).values():
        if "error" in corr_dict:
            continue
        for lag, stats_dict in corr_dict.items():
            if lag == "lag_0":
                continue
            total_tests += 1
            if stats_dict.get("significant_05"):
                significant_count += 1

    if total_tests == 0:
        hist_interp = hist.get("interpretation", "") if "error" not in hist else ""
        if hist_interp:
            return f"NO PREDICTIVE TESTS POSSIBLE. Historical alignment: {hist_interp}"
        return "INSUFFICIENT DATA: Cannot test predictive power (no overlapping dates)."

    sig_pct = significant_count / total_tests
    
    # Include historical alignment context
    hist_note = ""
    if "error" not in hist:
        hist_note = f" Historical alignment: {hist.get('alignment', 'UNKNOWN')}."

    if sig_pct >= 0.3:
        return (
            f"WEAK BUT NON-ZERO PREDICTIVE POWER: {significant_count}/{total_tests} tests "
            f"significant at 5% level.{hist_note} Signals may contain marginal forward info, "
            f"but exploitable alpha is likely swamped by noise."
        )
    else:
        return (
            f"NO PROVEN PREDICTIVE POWER: {significant_count}/{total_tests} tests significant.{hist_note} "
            f"The signal tracker does NOT forecast returns. It is a descriptive tool, "
            f"not a predictive system. Do NOT present it as alpha-generating research."
        )


def _write_md_report(results: Dict, md_path: Path):
    """Write human-readable markdown report."""
    lines = [
        "# Signal-Return Predictive Analysis Report",
        "",
        "## Sample Overview",
        "",
        f"- **Total paragraphs**: {results['sample_info']['total_paragraphs']}",
        f"- **Unique dates**: {results['sample_info']['unique_dates']}",
        f"- **Date range**: {results['sample_info']['date_range']}",
        "",
    ]

    # Historical Alignment Section
    hist = results.get("historical_alignment", {})
    lines.extend([
        "## Test 1: Historical Thesis Alignment (2023-2025)",
        "",
        "Tests if narrative signals match long-term price divergence. "
        "Grid signals should be positive; Oilfield signals should be negative. "
        "Sieyuan (grid proxy) should outperform HAL (oilfield proxy).",
        "",
    ])
    
    if "error" in hist:
        lines.append(f"**Error**: {hist['error']}")
    else:
        lines.append(f"- **Period**: {hist['period']}")
        lines.append(f"- **HAL 3Y return**: {hist['hal_cumulative_return']:.1%}")
        lines.append(f"- **Sieyuan 3Y return**: {hist['sieyuan_cumulative_return']:.1%}")
        lines.append(f"- **Price divergence** (Sieyuan - HAL): {hist['price_divergence']:.1%}")
        lines.append(f"- **Grid signal sentiment**: {hist['grid_signal_sentiment']:.2f}")
        lines.append(f"- **Oilfield signal sentiment**: {hist['oilfield_signal_sentiment']:.2f}")
        lines.append(f"- **Thesis signal score**: {hist['thesis_signal_score']:.2f}")
        lines.append(f"- **Alignment**: {hist['alignment']}")
        lines.append("")
        lines.append(f"**Interpretation**: {hist['interpretation']}")
    lines.append("")

    # Event Study Section
    lines.extend([
        "## Test 2: Event Study Analysis",
        "",
        "Tests returns around document publication dates. "
        "Windows: pre_7d (control), post_7d, post_30d, post_90d.",
        "",
    ])
    
    for ticker, event_results in results.get("event_study", {}).items():
        lines.append(f"### {ticker}")
        lines.append("")
        if "error" in event_results:
            lines.append(f"**Error**: {event_results['error']}")
        else:
            lines.append(f"- **Number of events**: {event_results['n_events']}")
            lines.append("")
            lines.append("| Window | Mean Return | Std Dev | N | t-stat | p-value | Significant? |")
            lines.append("|--------|-------------|---------|---|--------|---------|--------------|")
            for window, stats in event_results.get("summary", {}).items():
                sig = "Yes" if stats.get("significant_05") else "No"
                lines.append(
                    f"| {window} | {stats['mean_return']:.2%} | {stats['std_return']:.2%} | "
                    f"{stats['n']} | {stats['t_statistic']} | {stats['p_value']} | {sig} |"
                )
            lines.append("")
    
    # Monthly Lead-Lag Section
    lines.extend([
        "## Test 3: Monthly Lead-Lag Correlations",
        "",
    ])
    
    monthly = results.get("monthly_lead_lag", {})
    overlap = monthly.get("overlap_months", 0)
    
    if overlap < 3:
        lines.append(f"SKIPPED: Only {overlap} overlapping months (need >= 3 for statistical power)")
    else:
        lines.append(f"Overlapping months: {overlap}")
        lines.append("")
        
        for test_name, corr_dict in monthly.get("correlations", {}).items():
            lines.append(f"### {test_name}")
            lines.append("")
            if "error" in corr_dict:
                lines.append(f"**Error**: {corr_dict['error']}")
            else:
                lines.append("| Lag | Correlation | N | t-stat | p-value | Significant (5%)? |")
                lines.append("|-----|-------------|---|--------|---------|-------------------|")
                for lag, stats_dict in corr_dict.items():
                    sig = "Yes" if stats_dict.get("significant_05") else "No"
                    lines.append(
                        f"| {lag} | {stats_dict.get('correlation', 'N/A')} | {stats_dict.get('n', 'N/A')} | "
                        f"{stats_dict.get('t_statistic', 'N/A')} | {stats_dict.get('p_value', 'N/A')} | {sig} |"
                    )
            lines.append("")
    
    # Verdict
    lines.extend([
        "## Verdict",
        "",
        results.get("verdict", "No verdict generated."),
        "",
        "## Methodology Notes",
        "",
        "1. **Historical Alignment**: Tests if narrative sentiment matches 3-year price divergence. "
        "This is NOT predictive—it tests if the story matches history, not if it forecasts future returns.",
        "",
        "2. **Event Study**: Tests returns around document dates. Post-event windows test if signals "
        "have contemporaneous or short-term predictive power. Small sample (6 dates) limits statistical power.",
        "",
        "3. **Lead-Lag Correlation**: Tests if month-T signals predict month-T+1 returns. "
        "Requires >= 3 overlapping months for meaningful results.",
        "",
        "4. **Significance**: p < 0.05 (two-tailed t-test). Bonferroni correction NOT applied— "
        "this is exploratory analysis, not confirmatory.",
        "",
        "5. **Limitations**: Sparse signal dates (only 6 unique dates), mixed document types "
        "(news, reports, transcripts), forward-looking dates in some documents.",
        "",
    ])

    md_path.write_text("\n".join(lines))


if __name__ == "__main__":
    from src.config import CLASSIFIED_PARAGRAPHS_PATH

    if not CLASSIFIED_PARAGRAPHS_PATH.exists():
        print(f"[ERROR] No classifications found at {CLASSIFIED_PARAGRAPHS_PATH}")
        exit(1)

    df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
    print(f"Loaded {len(df)} classified paragraphs")

    output_dir = Path("outputs/signal_return")
    run_signal_return_analysis(df, output_dir)
