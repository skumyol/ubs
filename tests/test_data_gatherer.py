"""Tests for src/data_gatherer module."""

import pytest
import re
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.data_gatherer import (
    safe_filename,
    hash_text,
    clean_text,
    split_into_paragraphs,
    fetch_html,
    extract_readable_text,
)


class TestSafeFilename:
    """Test safe_filename function."""

    def test_removes_special_chars(self):
        # Trailing underscore is stripped by implementation
        assert safe_filename("Hello World!@#") == "Hello_World"

    def test_limits_length(self):
        long_name = "a" * 150
        result = safe_filename(long_name)
        assert len(result) <= 90

    def test_handles_empty(self):
        assert safe_filename("") == "untitled"

    def test_strips_underscores(self):
        assert safe_filename("_hello_") == "hello"

    def test_converts_to_string(self):
        assert safe_filename(123) == "123"


class TestHashText:
    """Test hash_text function."""

    def test_returns_12_chars(self):
        result = hash_text("test")
        assert len(result) == 12

    def test_consistent_hashing(self):
        result1 = hash_text("same input")
        result2 = hash_text("same input")
        assert result1 == result2

    def test_different_inputs_different_hashes(self):
        result1 = hash_text("input1")
        result2 = hash_text("input2")
        assert result1 != result2

    def test_is_hexadecimal(self):
        result = hash_text("test")
        assert all(c in '0123456789abcdef' for c in result)


class TestFetchHtml:
    """Test fetch_html function."""

    @patch('src.data_gatherer.requests.get')
    def test_successful_fetch(self, mock_get):
        mock_response = Mock()
        mock_response.text = '<html>content</html>'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_html("http://example.com")
        assert result == '<html>content</html>'

    @patch('src.data_gatherer.requests.get')
    def test_failed_fetch_returns_none(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        result = fetch_html("http://example.com")
        assert result is None

    @patch('src.data_gatherer.requests.get')
    def test_uses_user_agent(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetch_html("http://example.com")
        call_kwargs = mock_get.call_args[1]
        assert 'headers' in call_kwargs
        assert 'User-Agent' in call_kwargs['headers']


class TestExtractReadableText:
    """Test extract_readable_text function."""

    def test_uses_trafilatura_first(self):
        # Test that trafilatura extraction works
        # Need >300 chars to trigger early return path
        long_content = "A" * 301
        with patch('src.data_gatherer.trafilatura.extract') as mock_extract:
            mock_extract.return_value = long_content
            result = extract_readable_text("<html></html>", "http://example.com")
            assert long_content in result

    @patch('src.data_gatherer.trafilatura.extract')
    def test_falls_back_to_beautifulsoup(self, mock_extract):
        mock_extract.return_value = None
        html = "<html><body>Content here</body></html>"
        result = extract_readable_text(html, "http://example.com")
        assert "Content" in result

    def test_handles_empty_html(self):
        result = extract_readable_text("", "http://example.com")
        assert result == ""


class TestIntegration:
    """Integration tests for data gatherer utilities."""

    def test_clean_then_hash_workflow(self):
        text = "Hello\x00 World  \t\t  "
        cleaned = clean_text(text)
        hashed = hash_text(cleaned)
        assert len(hashed) == 12
        assert "\x00" not in cleaned

    def test_filename_from_hash(self):
        url = "http://example.com/article"
        hashed = hash_text(url)
        filename = f"DOC_{hashed}_article.txt"
        assert re.match(r"DOC_[a-f0-9]{12}_article\.txt", filename)

    def test_split_paragraphs_after_clean(self):
        dirty = "Para1\n\n\n\nPara2\x00\n\nThis is long enough"
        cleaned = clean_text(dirty)
        paragraphs = split_into_paragraphs(cleaned, min_chars=5)
        # Short paragraphs filtered - expect 2 valid ones
        assert len(paragraphs) >= 2
        assert any("Para1" in p for p in paragraphs)
