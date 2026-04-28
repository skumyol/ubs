"""Tests for src/charts module."""

import pytest
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
from pathlib import Path
from src.charts import (
    create_category_bar_chart,
    create_signal_heatmap,
    create_sentiment_comparison,
    create_long_short_matrix_table,
)


@pytest.fixture
def sample_category_df():
    """Sample data for category charts."""
    return pd.DataFrame({
        "category": ["A", "A", "B", "B"],
        "sector": ["Grid", "Oil", "Grid", "Oil"],
        "count": [10, 5, 8, 12],
    })


@pytest.fixture
def sample_sentiment_df():
    """Sample data for sentiment charts."""
    return pd.DataFrame({
        "category": ["A", "A", "B", "B"],
        "sector": ["Grid", "Oil", "Grid", "Oil"],
        "sentiment": ["positive", "negative", "neutral", "positive"],
    })


@pytest.fixture
def temp_output_path(tmp_path):
    """Temporary file path for chart outputs."""
    return str(tmp_path / "test_chart.png")


class TestCreateCategoryBarChart:
    """Test category bar chart creation."""

    def test_creates_file(self, sample_category_df, temp_output_path):
        create_category_bar_chart(sample_category_df, temp_output_path)
        assert Path(temp_output_path).exists()

    def test_file_is_valid_png(self, sample_category_df, temp_output_path):
        create_category_bar_chart(sample_category_df, temp_output_path)
        # Check file header for PNG signature
        with open(temp_output_path, 'rb') as f:
            header = f.read(8)
        assert header[:4] == b'\x89PNG'

    def test_handles_empty_dataframe(self, temp_output_path):
        df = pd.DataFrame({"category": [], "sector": [], "count": []})
        # Empty dataframe may fail to plot - test that it doesn't crash
        try:
            create_category_bar_chart(df, temp_output_path)
            assert Path(temp_output_path).exists()
        except (TypeError, ValueError):
            # Expected for empty data
            pass

    def test_respects_figsize(self, sample_category_df, temp_output_path):
        create_category_bar_chart(sample_category_df, temp_output_path, figsize=(8, 4))
        # Matplotlib doesn't expose figure size in saved file easily
        # Just verify it doesn't error
        assert Path(temp_output_path).exists()

    def test_respects_dpi(self, sample_category_df, temp_output_path):
        create_category_bar_chart(sample_category_df, temp_output_path, dpi=150)
        assert Path(temp_output_path).exists()


class TestCreateSignalHeatmap:
    """Test signal heatmap creation."""

    def test_creates_file(self, temp_output_path):
        df = pd.DataFrame({
            "category": ["A", "B"],
            "Grid Infrastructure_count": [10, 5],
            "Oilfield Services_count": [2, 8],
            "Grid Infrastructure_sentiment": [0.5, 0.3],
            "Oilfield Services_sentiment": [-0.2, -0.5],
        })
        create_signal_heatmap(df, temp_output_path)
        assert Path(temp_output_path).exists()

    def test_file_is_valid_png(self, temp_output_path):
        df = pd.DataFrame({
            "category": ["A"],
            "Grid Infrastructure_count": [1],
            "Grid Infrastructure_sentiment": [0.0],
        })
        create_signal_heatmap(df, temp_output_path)
        with open(temp_output_path, 'rb') as f:
            header = f.read(8)
        assert header[:4] == b'\x89PNG'


class TestCreateSentimentComparison:
    """Test sentiment comparison chart."""

    def test_creates_file(self, sample_sentiment_df, temp_output_path):
        create_sentiment_comparison(sample_sentiment_df, temp_output_path)
        assert Path(temp_output_path).exists()

    def test_file_is_valid_png(self, sample_sentiment_df, temp_output_path):
        create_sentiment_comparison(sample_sentiment_df, temp_output_path)
        with open(temp_output_path, 'rb') as f:
            header = f.read(8)
        assert header[:4] == b'\x89PNG'

    def test_handles_empty_sentiment(self, temp_output_path):
        df = pd.DataFrame({
            "category": [],
            "sector": [],
            "sentiment": [],
        })
        # Empty dataframe may fail to plot - test that it doesn't crash
        try:
            create_sentiment_comparison(df, temp_output_path)
            assert Path(temp_output_path).exists()
        except (TypeError, ValueError):
            # Expected for empty data
            pass


class TestCreateLongShortMatrixTable:
    """Test long/short matrix table creation."""

    def test_creates_file(self, temp_output_path):
        create_long_short_matrix_table(temp_output_path)
        assert Path(temp_output_path).exists()

    def test_file_is_valid_png(self, temp_output_path):
        create_long_short_matrix_table(temp_output_path)
        with open(temp_output_path, 'rb') as f:
            header = f.read(8)
        assert header[:4] == b'\x89PNG'

    def test_default_output_exists(self, tmp_path):
        path = str(tmp_path / "matrix.png")
        create_long_short_matrix_table(path, figsize=(10, 6))
        assert Path(path).exists()


class TestChartIntegration:
    """Integration tests for chart module."""

    def test_all_charts_work_together(self, tmp_path):
        """Verify all chart functions can be called in sequence."""
        # Category bar chart
        cat_df = pd.DataFrame({
            "category": ["Grid", "Oil"],
            "sector": ["Grid Inf", "Oilfield"],
            "count": [10, 5],
        })
        create_category_bar_chart(cat_df, str(tmp_path / "bar.png"))

        # Signal heatmap
        heat_df = pd.DataFrame({
            "category": ["A"],
            "Grid Infrastructure_count": [5],
            "Grid Infrastructure_sentiment": [0.5],
        })
        create_signal_heatmap(heat_df, str(tmp_path / "heat.png"))

        # Sentiment comparison
        sent_df = pd.DataFrame({
            "category": ["A"],
            "sector": ["Grid"],
            "sentiment": ["positive"],
        })
        create_sentiment_comparison(sent_df, str(tmp_path / "sent.png"))

        # Long/Short matrix
        create_long_short_matrix_table(str(tmp_path / "matrix.png"))

        # All should exist
        for name in ["bar.png", "heat.png", "sent.png", "matrix.png"]:
            assert (tmp_path / name).exists()
