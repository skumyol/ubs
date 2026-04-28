"""Tests for transcript downloader."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.transcript_downloader import (
    COMPANIES,
    fetch_page,
    extract_pdf_links,
    download_pdf,
    verify_downloads,
)


class TestCompaniesConfig:
    def test_halliburton_config(self):
        assert "halliburton" in COMPANIES
        config = COMPANIES["halliburton"]
        assert config["ticker"] == "HAL"
        assert "ir.halliburton.com" in config["ir_url"]
        assert "file_pattern" in config

    def test_slb_config(self):
        assert "slb" in COMPANIES
        config = COMPANIES["slb"]
        assert config["ticker"] == "SLB"
        assert "slb.com" in config["ir_url"]

    def test_file_pattern_is_valid_regex(self):
        import re
        for key, config in COMPANIES.items():
            # Should not raise
            pattern = re.compile(config["file_pattern"], re.IGNORECASE)
            # Test it matches expected strings
            assert pattern.search("Q1_2025_transcript.pdf")
            assert pattern.search("earnings_call_2024.pdf")


class TestFetchPage:
    @patch("src.transcript_downloader.requests.get")
    def test_successful_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_page("https://example.com")
        assert result == "<html><body>Test</body></html>"
        mock_get.assert_called_once()

    @patch("src.transcript_downloader.requests.get")
    def test_fetch_failure(self, mock_get):
        from requests import RequestException
        mock_get.side_effect = RequestException("Connection error")

        result = fetch_page("https://example.com")
        assert result is None

    def test_no_requests_installed(self):
        with patch("src.transcript_downloader.HAS_DEPS", False):
            result = fetch_page("https://example.com")
            assert result is None


class TestExtractPdfLinks:
    def test_extracts_pdf_links(self):
        html = """
        <html>
        <body>
            <a href="/files/transcript_q1_2025.pdf">Q1 2025 Transcript</a>
            <a href="/files/earnings_call.pdf">Earnings Call</a>
            <a href="/files/report.docx">Not PDF</a>
            <a href="https://other.com/presentation.pdf">External PDF</a>
        </body>
        </html>
        """
        pattern = r"transcript|earnings.*call|presentation"
        links = extract_pdf_links(html, "https://example.com/", pattern)

        assert len(links) == 3  # 3 PDFs
        urls = [l["url"] for l in links]
        assert any("transcript_q1_2025.pdf" in u for u in urls)
        assert any("earnings_call.pdf" in u for u in urls)
        assert any("presentation.pdf" in u for u in urls)

    def test_resolves_relative_urls(self):
        html = '<a href="/path/to/file.pdf">Link</a>'
        links = extract_pdf_links(html, "https://example.com/base/", r".*")

        assert len(links) == 1
        assert links[0]["url"] == "https://example.com/path/to/file.pdf"

    def test_pattern_filters_correctly(self):
        html = """
        <a href="/transcript.pdf">Transcript</a>
        <a href="/annual_report.pdf">Report</a>
        <a href="/earnings_call.pdf">Earnings</a>
        """
        pattern = r"transcript|earnings"
        links = extract_pdf_links(html, "https://example.com/", pattern)

        assert len(links) == 2
        filenames = [l["filename"] for l in links]
        assert "transcript.pdf" in filenames
        assert "earnings_call.pdf" in filenames
        assert "annual_report.pdf" not in filenames

    def test_empty_html(self):
        links = extract_pdf_links("", "https://example.com/", ".*")
        assert links == []

    def test_no_beautifulsoup(self):
        with patch("src.transcript_downloader.HAS_DEPS", False):
            links = extract_pdf_links("<html></html>", "https://example.com/", ".*")
            assert links == []


class TestDownloadPdf:
    @patch("src.transcript_downloader.requests.get")
    def test_successful_download(self, mock_get, tmp_path):
        mock_response = MagicMock()
        mock_response.content = b"%PDF-1.4 test content"
        mock_response.headers = {"Content-Type": "application/pdf", "Content-Length": "15000"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        output_path = tmp_path / "test.pdf"
        result = download_pdf("https://example.com/file.pdf", output_path)

        assert result is True
        assert output_path.exists()
        assert output_path.read_bytes() == b"%PDF-1.4 test content"

    @patch("src.transcript_downloader.requests.get")
    def test_skips_non_pdf(self, mock_get, tmp_path):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/html", "Content-Length": "100"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        output_path = tmp_path / "test.pdf"
        result = download_pdf("https://example.com/file.pdf", output_path)

        assert result is False
        assert not output_path.exists()

    @patch("src.transcript_downloader.requests.get")
    def test_skips_too_small(self, mock_get, tmp_path):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/pdf", "Content-Length": "5000"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        output_path = tmp_path / "test.pdf"
        result = download_pdf("https://example.com/file.pdf", output_path)

        assert result is False

    @patch("src.transcript_downloader.requests.get")
    def test_download_failure(self, mock_get, tmp_path):
        from requests import RequestException
        mock_get.side_effect = RequestException("Network error")

        output_path = tmp_path / "test.pdf"
        result = download_pdf("https://example.com/file.pdf", output_path)

        assert result is False

    def test_no_requests_installed(self, tmp_path):
        with patch("src.transcript_downloader.HAS_DEPS", False):
            output_path = tmp_path / "test.pdf"
            result = download_pdf("https://example.com/file.pdf", output_path)
            assert result is False


class TestVerifyDownloads:
    def test_identifies_valid_pdfs(self, tmp_path):
        # Create a valid PDF
        valid_pdf = tmp_path / "valid.pdf"
        valid_pdf.write_bytes(b"%PDF-1.4 test content")

        # Create an invalid file
        invalid_pdf = tmp_path / "invalid.pdf"
        invalid_pdf.write_bytes(b"Not a PDF file")

        with patch("src.transcript_downloader.RAW_PDF_DIR", tmp_path):
            valid = verify_downloads()

        assert len(valid) == 1
        assert valid[0].name == "valid.pdf"

    def test_empty_directory(self, tmp_path):
        with patch("src.transcript_downloader.RAW_PDF_DIR", tmp_path):
            valid = verify_downloads()
        assert valid == []

    def test_nonexistent_directory(self):
        with patch("src.transcript_downloader.RAW_PDF_DIR", Path("/nonexistent/path")):
            valid = verify_downloads()
        assert valid == []


class TestIntegration:
    """Integration-style tests that check the full flow."""

    @patch("src.transcript_downloader.HAS_DEPS", True)
    @patch("src.transcript_downloader.requests.get")
    def test_end_to_end_flow(self, mock_get, tmp_path):
        """Simulate downloading a transcript from a mock IR page."""
        # Mock HTML response
        html_response = MagicMock()
        html_response.text = """
        <html>
        <body>
            <a href="/files/HAL_Q1_2025_Transcript.pdf">Q1 2025 Earnings Call Transcript</a>
        </body>
        </html>
        """
        html_response.raise_for_status.return_value = None

        # Mock PDF response
        pdf_response = MagicMock()
        pdf_response.content = b"%PDF-1.4 HAL Q1 2025 transcript content"
        pdf_response.headers = {
            "Content-Type": "application/pdf",
            "Content-Length": "50000"
        }
        pdf_response.raise_for_status.return_value = None

        # Return different responses for different URLs
        def side_effect(url, **kwargs):
            if url.endswith(".pdf"):
                return pdf_response
            return html_response

        mock_get.side_effect = side_effect

        # Run extraction
        from src.transcript_downloader import extract_pdf_links, download_pdf

        html = html_response.text
        links = extract_pdf_links(html, "https://ir.halliburton.com/", r"transcript|earnings")

        assert len(links) == 1
        assert "HAL_Q1_2025" in links[0]["filename"]

        # Download
        output_path = tmp_path / "HAL_Q1_2025_Transcript.pdf"
        result = download_pdf(links[0]["url"], output_path)

        assert result is True
        assert output_path.exists()
