"""Tests for src/analysis module."""

import pytest
import pandas as pd
from src.analysis import (
    sentiment_score,
    category_counts,
    sentiment_by_category,
    build_signal_tracker,
)


class TestSentimentScore:
    """Test sentiment_score function."""

    def test_positive_returns_1(self):
        assert sentiment_score("positive") == 1
        assert sentiment_score("POSITIVE") == 1
        assert sentiment_score("Positive") == 1

    def test_neutral_returns_0(self):
        assert sentiment_score("neutral") == 0
        assert sentiment_score("NEUTRAL") == 0
        assert sentiment_score("Neutral") == 0

    def test_negative_returns_minus_1(self):
        assert sentiment_score("negative") == -1
        assert sentiment_score("NEGATIVE") == -1
        assert sentiment_score("Negative") == -1

    def test_invalid_returns_0(self):
        assert sentiment_score("unknown") == 0
        assert sentiment_score("") == 0
        assert sentiment_score(None) == 0


class TestCategoryCounts:
    """Test category_counts function."""

    def test_counts_by_sector_and_category(self):
        df = pd.DataFrame({
            "sector": ["Grid", "Grid", "Oilfield", "Grid"],
            "category": ["A", "A", "B", "A"],
        })
        result = category_counts(df)
        # Grid+A=3, Oilfield+B=1 - that's 2 unique combinations
        assert len(result) == 2
        grid_count = result[result["sector"] == "Grid"]["count"].sum()
        assert grid_count == 3

    def test_missing_columns_raises_error(self):
        df = pd.DataFrame({"other": [1, 2, 3]})
        with pytest.raises(ValueError):
            category_counts(df)

    def test_empty_dataframe_returns_empty(self):
        df = pd.DataFrame({"sector": [], "category": []})
        result = category_counts(df)
        assert len(result) == 0

    def test_handles_na_values(self):
        df = pd.DataFrame({
            "sector": ["Grid", None, "Grid"],
            "category": ["A", "B", "A"],
        })
        result = category_counts(df)
        # Result contains combinations as found - Grid+A and NaN+B
        assert len(result) >= 1

    def test_result_is_sorted(self):
        df = pd.DataFrame({
            "sector": ["B", "A", "A", "B", "A"],
            "category": ["X", "Y", "Y", "X", "Y"],
        })
        result = category_counts(df)
        # B+X (row 0,3) = 2, A+Y (row 1,2,4) = 3 -> only 2 unique combos
        assert len(result) == 2
        # Should be sorted by sector then count
        assert result.iloc[0]["sector"] <= result.iloc[1]["sector"]


class TestSentimentByCategory:
    """Test sentiment_by_category function."""

    def test_calculates_average_sentiment(self):
        df = pd.DataFrame({
            "category": ["A", "A", "A"],
            "sentiment": ["positive", "positive", "negative"],
        })
        result = sentiment_by_category(df)
        assert len(result) == 1
        assert result.iloc[0]["avg_sentiment"] == pytest.approx(0.333, rel=0.01)

    def test_counts_paragraphs(self):
        df = pd.DataFrame({
            "category": ["A", "A", "B"],
            "sentiment": ["positive", "neutral", "negative"],
        })
        result = sentiment_by_category(df)
        a_row = result[result["category"] == "A"].iloc[0]
        assert a_row["paragraph_count"] == 2

    def test_sorted_by_sentiment(self):
        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "sentiment": ["negative", "positive", "neutral"],
        })
        result = sentiment_by_category(df)
        assert result.iloc[0]["category"] == "B"  # Most positive first

    def test_all_neutral_returns_zero(self):
        df = pd.DataFrame({
            "category": ["A", "A"],
            "sentiment": ["neutral", "neutral"],
        })
        result = sentiment_by_category(df)
        assert result.iloc[0]["avg_sentiment"] == 0


class TestBuildSignalTracker:
    """Test build_signal_tracker function."""

    def test_creates_pivot_table(self):
        df = pd.DataFrame({
            "category": ["Grid", "Grid", "Oil"],
            "sector": ["Grid Inf", "Grid Inf", "Oilfield"],
            "sentiment": ["positive", "positive", "negative"],
        })
        result = build_signal_tracker(df)
        assert "category" in result.columns
        assert "Grid Infrastructure_count" in result.columns or "Grid Inf_count" in result.columns

    def test_calculates_sentiment_scores(self):
        df = pd.DataFrame({
            "category": ["A", "A"],
            "sector": ["Grid Infrastructure", "Grid Infrastructure"],
            "sentiment": ["positive", "positive"],
        })
        result = build_signal_tracker(df)
        grid_col = [c for c in result.columns if "Grid" in c and "sentiment" in c][0]
        assert result.iloc[0][grid_col] == 1.0

    def test_handles_missing_sectors(self):
        df = pd.DataFrame({
            "category": ["A"],
            "sector": ["Unknown"],
            "sentiment": ["neutral"],
        })
        result = build_signal_tracker(df)
        # Should still produce output with zero counts for expected sectors
        assert len(result) >= 1

    def test_empty_dataframe(self):
        df = pd.DataFrame({
            "category": [],
            "sector": [],
            "sentiment": [],
        })
        result = build_signal_tracker(df)
        # Empty dataframe produces empty result (no categories to pivot)
        assert len(result) == 0  # No rows when input is empty

    def test_multiple_categories(self):
        df = pd.DataFrame({
            "category": ["A", "B", "A", "B"],
            "sector": ["Grid", "Grid", "Oil", "Oil"],
            "sentiment": ["positive", "negative", "positive", "negative"],
        })
        result = build_signal_tracker(df)
        assert len(result) >= 2  # At least 2 categories
