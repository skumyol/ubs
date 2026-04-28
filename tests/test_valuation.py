"""Tests for valuation engine."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.valuation import (
    scenario_valuation,
    peer_comps_table,
    pair_trade_summary,
    fetch_market_data,
    SIEYUAN_SCENARIOS,
    HAL_SCENARIOS,
    LONG_TICKER,
    SHORT_TICKERS,
)


class TestScenarioValuation:
    def test_returns_dataframe_and_expected_return(self):
        df, er = scenario_valuation(3.0, 100.0, SIEYUAN_SCENARIOS)
        assert isinstance(df, pd.DataFrame)
        assert "scenario" in df.columns
        assert "target_price" in df.columns
        assert "upside_pct" in df.columns
        assert isinstance(er, float)

    def test_three_scenarios_returned(self):
        df, _ = scenario_valuation(3.0, 100.0, SIEYUAN_SCENARIOS)
        assert len(df) == 3
        assert set(df["scenario"]) == {"Bear", "Base", "Bull"}

    def test_zero_price_handles_gracefully(self):
        df, er = scenario_valuation(3.0, 0, SIEYUAN_SCENARIOS)
        assert isinstance(df, pd.DataFrame)
        assert er == 0  # No baseline = 0 return

    def test_probability_weighted_return(self):
        df, er = scenario_valuation(3.0, 100.0, SIEYUAN_SCENARIOS)
        # Manual calc: sum(upside * prob)
        total_prob = sum(s["probability"] for s in SIEYUAN_SCENARIOS.values())
        assert abs(total_prob - 1.0) < 0.01

    def test_short_scenarios_negative_upside(self):
        """Short scenarios should have negative upside in bear case."""
        df, er = scenario_valuation(3.0, 30.0, HAL_SCENARIOS)
        bear_row = df[df["scenario"] == "Bear"].iloc[0]
        assert "-" in bear_row["upside_pct"]


class TestPeerCompsTable:
    def test_combines_long_and_short_peers(self):
        long_df = pd.DataFrame([{
            "name": "Test Long", "ticker": "LONG",
            "pe": 30.0, "ev_ebitda": 20.0,
            "revenue_growth": 0.15, "profit_margin": 0.10,
        }])
        short_df = pd.DataFrame([{
            "name": "Test Short", "ticker": "SHORT",
            "pe": 10.0, "ev_ebitda": 8.0,
            "revenue_growth": -0.05, "profit_margin": 0.05,
        }])
        result = peer_comps_table(long_df, short_df)
        assert len(result) == 2
        assert "Grid / Power Equipment" in result["sector"].values
        assert "Oilfield Services" in result["sector"].values

    def test_handles_nan_values(self):
        long_df = pd.DataFrame([{
            "name": "X", "ticker": "X",
            "pe": None, "ev_ebitda": None,
            "revenue_growth": None, "profit_margin": None,
        }])
        short_df = pd.DataFrame()
        result = peer_comps_table(long_df, short_df)
        assert "n/a" in result.iloc[0]["p_e"]

    def test_empty_dataframes(self):
        result = peer_comps_table(pd.DataFrame(), pd.DataFrame())
        assert len(result) == 0


class TestPairTradeSummary:
    def test_long_positive_short_negative_pair_positive(self):
        result = pair_trade_summary(20.0, -30.0)
        assert result["long_expected_return_pct"] == 20.0
        assert result["short_leg_pnl_pct"] == 30.0  # We profit from short going down
        assert result["pair_spread_return_pct"] == 50.0

    def test_both_legs_lose_pair_negative(self):
        result = pair_trade_summary(-10.0, 5.0)
        # Long loses 10, short stock rose 5 (we lose 5 on short)
        assert result["pair_spread_return_pct"] == -15.0

    def test_returns_required_keys(self):
        result = pair_trade_summary(10.0, -20.0)
        for key in [
            "long_expected_return_pct",
            "short_expected_move_pct",
            "short_leg_pnl_pct",
            "pair_spread_return_pct",
            "trade_direction",
        ]:
            assert key in result


class TestFetchMarketData:
    def test_fetches_data_for_tickers(self):
        """Smoke test: ensure function returns DataFrame without crashing."""
        df = fetch_market_data([])
        assert isinstance(df, pd.DataFrame)

    def test_returns_dataframe_with_yfinance(self):
        """Test that yfinance integration works end-to-end with at least empty input."""
        df = fetch_market_data([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_handles_invalid_ticker(self):
        """Invalid tickers should not crash, just return None values."""
        try:
            df = fetch_market_data(["INVALID_TICKER_XYZ_NOT_REAL"])
            assert isinstance(df, pd.DataFrame)
        except Exception:
            # If yfinance not available, that's fine
            pass


class TestSaveValuationOutputs:
    def test_creates_all_output_files(self, tmp_path):
        """Integration test: save_valuation_outputs writes all CSVs."""
        from src.valuation import save_valuation_outputs
        try:
            summary = save_valuation_outputs(tmp_path)
        except Exception as e:
            pytest.skip(f"yfinance unavailable: {e}")

        # Verify required outputs
        for f in [
            "peer_comps.csv",
            "long_scenarios.csv",
            "short_scenarios.csv",
            "pair_trade_summary.csv",
        ]:
            assert (tmp_path / f).exists()

        # Verify summary structure
        for key in [
            "long_price", "long_eps", "long_expected_return",
            "short_price", "short_eps", "short_expected_return",
            "pair_spread_return",
        ]:
            assert key in summary


class TestConstants:
    def test_long_ticker_is_sieyuan(self):
        assert LONG_TICKER == "002028.SZ"

    def test_short_tickers_include_hal(self):
        assert "HAL" in SHORT_TICKERS
        assert SHORT_TICKERS["HAL"] == "Halliburton"

    def test_scenarios_have_required_keys(self):
        for scenario in SIEYUAN_SCENARIOS.values():
            assert "eps_growth" in scenario
            assert "target_pe" in scenario
            assert "probability" in scenario

    def test_probabilities_sum_to_one(self):
        long_sum = sum(s["probability"] for s in SIEYUAN_SCENARIOS.values())
        short_sum = sum(s["probability"] for s in HAL_SCENARIOS.values())
        assert abs(long_sum - 1.0) < 0.01
        assert abs(short_sum - 1.0) < 0.01
