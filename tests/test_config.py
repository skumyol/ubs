"""Tests for src/config module."""

import pytest
from pathlib import Path
from src import config


class TestConfigPaths:
    """Test configuration paths exist and are valid."""

    def test_root_is_path(self):
        assert isinstance(config.ROOT, Path)

    def test_data_dir_is_path(self):
        assert isinstance(config.DATA_DIR, Path)

    def test_raw_text_dir_is_path(self):
        assert isinstance(config.RAW_TEXT_DIR, Path)

    def test_raw_pdf_dir_is_path(self):
        assert isinstance(config.RAW_PDF_DIR, Path)

    def test_processed_dir_is_path(self):
        assert isinstance(config.PROCESSED_DIR, Path)

    def test_document_index_path_is_path(self):
        assert isinstance(config.DOCUMENT_INDEX_PATH, Path)

    def test_paragraph_dataset_path_is_path(self):
        assert isinstance(config.PARAGRAPH_DATASET_PATH, Path)


class TestConfigParameters:
    """Test configuration parameters."""

    def test_min_paragraph_chars_is_positive(self):
        assert config.MIN_PARAGRAPH_CHARS > 0
        assert isinstance(config.MIN_PARAGRAPH_CHARS, int)

    def test_max_paragraph_chars_is_positive(self):
        assert config.MAX_PARAGRAPH_CHARS > 0
        assert isinstance(config.MAX_PARAGRAPH_CHARS, int)

    def test_max_greater_than_min(self):
        assert config.MAX_PARAGRAPH_CHARS > config.MIN_PARAGRAPH_CHARS

    def test_user_agent_is_string(self):
        assert isinstance(config.USER_AGENT, str)
        assert len(config.USER_AGENT) > 0

    def test_llm_delay_is_positive(self):
        assert config.LLM_DELAY_SECONDS >= 0
        assert isinstance(config.LLM_DELAY_SECONDS, (int, float))


class TestPathConsistency:
    """Test path relationships are consistent."""

    def test_raw_text_inside_data(self):
        assert config.RAW_TEXT_DIR.is_relative_to(config.DATA_DIR) or \
               str(config.RAW_TEXT_DIR).startswith(str(config.DATA_DIR))

    def test_raw_pdf_inside_data(self):
        assert config.RAW_PDF_DIR.is_relative_to(config.DATA_DIR) or \
               str(config.RAW_PDF_DIR).startswith(str(config.DATA_DIR))

    def test_processed_inside_data(self):
        assert config.PROCESSED_DIR.is_relative_to(config.DATA_DIR) or \
               str(config.PROCESSED_DIR).startswith(str(config.DATA_DIR))

    def test_document_index_in_processed(self):
        assert config.DOCUMENT_INDEX_PATH.parent == config.PROCESSED_DIR

    def test_paragraph_dataset_in_processed(self):
        assert config.PARAGRAPH_DATASET_PATH.parent == config.PROCESSED_DIR


class TestChartPaths:
    """Test chart output paths."""

    def test_charts_dir_is_path(self):
        assert isinstance(config.CHARTS_DIR, Path)

    def test_tables_dir_is_path(self):
        assert isinstance(config.TABLES_DIR, Path)

    def test_charts_inside_outputs(self):
        assert config.CHARTS_DIR.is_relative_to(config.OUTPUTS_DIR) or \
               str(config.CHARTS_DIR).startswith(str(config.OUTPUTS_DIR))

    def test_category_bar_chart_path_is_path(self):
        assert isinstance(config.CATEGORY_BAR_CHART_PATH, Path)

    def test_signal_heatmap_path_is_path(self):
        assert isinstance(config.SIGNAL_HEATMAP_PATH, Path)
