"""Tests for new analysis functions: plan_format_signal_tracker, narrative_shift_analysis."""

import pytest
import pandas as pd
from src.analysis import plan_format_signal_tracker, narrative_shift_analysis


class TestPlanFormatSignalTracker:
    def test_returns_high_medium_low_labels(self):
        df = pd.DataFrame([
            {"category": "Grid Resilience", "sector": "Grid Infrastructure",
             "sentiment": "positive"},
            {"category": "Grid Resilience", "sector": "Grid Infrastructure",
             "sentiment": "positive"},
            {"category": "Electricity Demand", "sector": "Grid Infrastructure",
             "sentiment": "positive"},
            {"category": "Oil Supply Disruption", "sector": "Oilfield Services",
             "sentiment": "negative"},
        ])
        result = plan_format_signal_tracker(df)
        assert "signal_cluster" in result.columns
        assert "Grid Equipment" in result.columns
        assert "Oilfield Services" in result.columns
        for val in result["Grid Equipment"]:
            assert val in ("High", "Medium", "Low")

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["category", "sector", "sentiment"])
        result = plan_format_signal_tracker(df)
        assert "signal_cluster" in result.columns

    def test_unknown_categories_filtered(self):
        df = pd.DataFrame([
            {"category": "Random Category", "sector": "Other", "sentiment": "neutral"},
        ])
        result = plan_format_signal_tracker(df)
        assert len(result) == 0

    def test_renames_grid_to_grid_equipment(self):
        df = pd.DataFrame([
            {"category": "Grid Resilience", "sector": "Grid Infrastructure",
             "sentiment": "positive"},
        ])
        result = plan_format_signal_tracker(df)
        assert "Grid Equipment" in result.columns


class TestNarrativeShiftAnalysis:
    def test_strong_grid_signals_high_thesis_score(self):
        df = pd.DataFrame([
            {"category": "Grid Resilience", "sector": "Grid Infrastructure",
             "sentiment": "positive"},
        ] * 10)
        result = narrative_shift_analysis(df)
        assert result["thesis_support_score"] > 0
        assert result["grid_signal_share"] == 1.0

    def test_returns_required_keys(self):
        df = pd.DataFrame([
            {"category": "Grid Resilience", "sector": "Grid Infrastructure",
             "sentiment": "positive"},
        ])
        result = narrative_shift_analysis(df)
        for key in [
            "total_signals",
            "grid_signal_share",
            "oil_signal_share",
            "grid_positive_rate",
            "oil_negative_rate",
            "thesis_support_score",
            "interpretation",
        ]:
            assert key in result

    def test_empty_dataframe_handled(self):
        df = pd.DataFrame(columns=["category", "sector", "sentiment"])
        result = narrative_shift_analysis(df)
        assert result["total_signals"] >= 1  # Falls back to 1 to avoid div/0

    def test_balanced_mix_moderate_score(self):
        df = pd.DataFrame([
            {"category": "Grid Resilience", "sector": "Grid Infrastructure",
             "sentiment": "positive"},
            {"category": "Oil Supply Disruption", "sector": "Oilfield Services",
             "sentiment": "negative"},
        ])
        result = narrative_shift_analysis(df)
        assert "interpretation" in result
        assert isinstance(result["interpretation"], str)
