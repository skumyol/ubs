"""Additional tests for data_gatherer to reach 90%+ coverage."""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import sys

from src.data_gatherer import (
    gather_seed_urls,
    gather_rss,
    gather_gdelt_news,
    gather_local_pdfs,
    main,
    GDELT_QUERIES,
    STARTER_URLS,
    STARTER_RSS,
)
from src.config import (
    RAW_TEXT_DIR,
    RAW_PDF_DIR,
    PROCESSED_DIR,
    DOCUMENT_INDEX_PATH,
    PARAGRAPH_DATASET_PATH,
)


class TestGatherSeedUrls:
    """Test gather_seed_urls function."""

    @patch('src.data_gatherer.fetch_html')
    @patch('src.data_gatherer.extract_readable_text')
    @patch('src.data_gatherer.save_text_file')
    @patch('src.data_gatherer.ensure_seed_files')
    @patch('src.data_gatherer.pd.read_csv')
    def test_gathers_from_seed_urls(
        self, mock_read_csv, mock_ensure, mock_save, mock_extract, mock_fetch
    ):
        """Test the full gather_seed_urls workflow."""
        # Setup mock dataframe
        mock_df = pd.DataFrame([{
            "source_name": "Test Source",
            "url": "http://example.com",
            "company": "TestCo",
            "sector": "TestSector",
            "document_type": "Test",
            "theme": "TestTheme",
        }])
        mock_read_csv.return_value = mock_df

        mock_fetch.return_value = "<html>test</html>"
        mock_extract.return_value = "A" * 500  # >300 chars
        mock_save.return_value = "/path/to/file.txt"

        result = gather_seed_urls()

        assert isinstance(result, list)
        mock_fetch.assert_called_once()

    @patch('src.data_gatherer.fetch_html')
    @patch('src.data_gatherer.ensure_seed_files')
    @patch('src.data_gatherer.pd.read_csv')
    def test_skips_failed_fetches(self, mock_read_csv, mock_ensure, mock_fetch):
        """Test that failed fetches are skipped."""
        mock_df = pd.DataFrame([{
            "source_name": "Test",
            "url": "http://example.com",
            "company": "",
            "sector": "",
            "document_type": "",
            "theme": "",
        }])
        mock_read_csv.return_value = mock_df
        mock_fetch.return_value = None  # Failed fetch

        result = gather_seed_urls()
        assert result == []

    @patch('src.data_gatherer.fetch_html')
    @patch('src.data_gatherer.extract_readable_text')
    @patch('src.data_gatherer.ensure_seed_files')
    @patch('src.data_gatherer.pd.read_csv')
    def test_skips_short_text(self, mock_read_csv, mock_ensure, mock_extract, mock_fetch):
        """Test that short text is skipped."""
        mock_df = pd.DataFrame([{
            "source_name": "Test",
            "url": "http://example.com",
            "company": "",
            "sector": "",
            "document_type": "",
            "theme": "",
        }])
        mock_read_csv.return_value = mock_df
        mock_fetch.return_value = "<html></html>"
        mock_extract.return_value = "Short"  # <300 chars

        result = gather_seed_urls()
        assert result == []


class TestGatherRss:
    """Test gather_rss function."""

    @patch('src.data_gatherer.feedparser.parse')
    @patch('src.data_gatherer.fetch_article_text')
    @patch('src.data_gatherer.save_text_file')
    @patch('src.data_gatherer.ensure_seed_files')
    @patch('src.data_gatherer.pd.read_csv')
    def test_gathers_from_rss(
        self, mock_read_csv, mock_ensure, mock_save, mock_fetch_article, mock_parse
    ):
        """Test RSS feed gathering."""
        mock_df = pd.DataFrame([{
            "source_name": "Test Feed",
            "feed_url": "http://rss.example.com",
            "sector": "Test",
            "theme": "Test",
        }])
        mock_read_csv.return_value = mock_df

        # Mock parsed feed
        mock_entry = MagicMock()
        mock_entry.get.return_value = "http://article.example.com"
        mock_entry.title = "Test Article"
        mock_entry.published = "2024-01-01"

        mock_parsed = MagicMock()
        mock_parsed.entries = [mock_entry]
        mock_parse.return_value = mock_parsed

        mock_fetch_article.return_value = "A" * 500
        mock_save.return_value = "/path/to/file.txt"

        result = gather_rss(max_articles_per_feed=1)

        assert isinstance(result, list)

    @patch('src.data_gatherer.feedparser.parse')
    @patch('src.data_gatherer.ensure_seed_files')
    @patch('src.data_gatherer.pd.read_csv')
    def test_handles_parse_error(self, mock_read_csv, mock_ensure, mock_parse):
        """Test handling of RSS parse errors."""
        mock_df = pd.DataFrame([{
            "source_name": "Test Feed",
            "feed_url": "http://rss.example.com",
            "sector": "Test",
            "theme": "Test",
        }])
        mock_read_csv.return_value = mock_df
        mock_parse.side_effect = Exception("Parse error")

        result = gather_rss()
        assert result == []

    @patch('src.data_gatherer.feedparser.parse')
    @patch('src.data_gatherer.ensure_seed_files')
    @patch('src.data_gatherer.pd.read_csv')
    def test_skips_entries_without_url(self, mock_read_csv, mock_ensure, mock_parse):
        """Test skipping entries without URLs."""
        mock_df = pd.DataFrame([{
            "source_name": "Test Feed",
            "feed_url": "http://rss.example.com",
            "sector": "Test",
            "theme": "Test",
        }])
        mock_read_csv.return_value = mock_df

        mock_entry = MagicMock()
        mock_entry.get.return_value = None  # No URL

        mock_parsed = MagicMock()
        mock_parsed.entries = [mock_entry]
        mock_parse.return_value = mock_parsed

        result = gather_rss()
        assert result == []


class TestFetchArticleText:
    """Test fetch_article_text function."""

    @patch('src.data_gatherer.requests.get')
    @patch('src.data_gatherer.trafilatura.extract')
    def test_extracts_article_text(self, mock_extract, mock_get):
        """Test article text extraction."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Article content here.</body></html>"
        mock_get.return_value = mock_response
        mock_extract.return_value = "A" * 400

        from src.data_gatherer import fetch_article_text
        result = fetch_article_text("http://example.com")

        assert len(result) > 300

    @patch('src.data_gatherer.requests.get')
    def test_handles_request_error(self, mock_get):
        """Test handling of request errors."""
        mock_get.side_effect = Exception("Network error")

        from src.data_gatherer import fetch_article_text
        result = fetch_article_text("http://example.com")

        assert result is None


class TestGdeltNews:
    """Test GDELT news gathering."""

    @patch('src.data_gatherer.requests.get')
    @patch('src.data_gatherer.fetch_article_text')
    @patch('src.data_gatherer.save_text_file')
    def test_gathers_gdelt_news(self, mock_save, mock_fetch, mock_get):
        """Test GDELT news gathering."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "articles": [{
                "url": "http://example.com/article",
                "title": "Test Article",
                "sourceCommonName": "Test Source",
                "seendate": "20240101",
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        mock_fetch.return_value = "A" * 500
        mock_save.return_value = "/path/to/file.txt"

        result = gather_gdelt_news(max_records_per_query=1)

        assert isinstance(result, list)

    @patch('src.data_gatherer.requests.get')
    def test_handles_gdelt_error(self, mock_get):
        """Test handling of GDELT API errors."""
        mock_get.side_effect = Exception("API error")

        result = gather_gdelt_news()
        assert result == []


class TestMainFunction:
    """Test main function orchestration."""

    @patch('src.data_gatherer.gather_seed_urls')
    @patch('src.data_gatherer.gather_rss')
    @patch('src.data_gatherer.gather_gdelt_news')
    @patch('src.data_gatherer.gather_local_pdfs')
    @patch('src.data_gatherer.save_document_index')
    @patch('src.data_gatherer.build_paragraph_dataset')
    @patch('src.data_gatherer.print_summary')
    def test_main_calls_all_gatherers(
        self, mock_summary, mock_build, mock_save, mock_pdfs, mock_gdelt, mock_rss, mock_urls
    ):
        """Test that main calls all gathering functions."""
        mock_urls.return_value = [{"doc_id": "1"}]
        mock_rss.return_value = [{"doc_id": "2"}]
        mock_gdelt.return_value = [{"doc_id": "3"}]
        mock_pdfs.return_value = [{"doc_id": "4"}]

        main()

        mock_urls.assert_called_once()
        mock_rss.assert_called_once()
        mock_gdelt.assert_called_once()
        mock_pdfs.assert_called_once()
        mock_save.assert_called_once()
        mock_build.assert_called_once()
        mock_summary.assert_called_once()


class TestConstants:
    """Test module constants."""

    def test_starter_urls_is_list(self):
        assert isinstance(STARTER_URLS, list)
        assert len(STARTER_URLS) > 0

    def test_starter_urls_have_required_fields(self):
        for url in STARTER_URLS:
            assert "source_name" in url
            assert "url" in url
            assert "sector" in url

    def test_starter_rss_is_list(self):
        assert isinstance(STARTER_RSS, list)
        assert len(STARTER_RSS) > 0

    def test_gdelt_queries_is_list(self):
        assert isinstance(GDELT_QUERIES, list)
        assert len(GDELT_QUERIES) > 0

    def test_gdelt_queries_have_required_fields(self):
        for query in GDELT_QUERIES:
            assert "query" in query
            assert "sector" in query
            assert "theme" in query
