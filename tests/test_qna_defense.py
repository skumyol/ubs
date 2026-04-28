"""Tests for Q&A defense generator."""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from src.qna_defense import (
    extract_top_quote,
    build_qna_doc,
    QNA_QUESTIONS,
)


class TestExtractTopQuote:
    def test_returns_highest_confidence(self):
        df = pd.DataFrame([
            {"category": "X", "text": "low conf", "confidence": 0.5,
             "title": "A", "source_name": "src"},
            {"category": "X", "text": "high conf", "confidence": 0.95,
             "title": "B", "source_name": "src"},
        ])
        quote = extract_top_quote(df, ["X"], {})
        assert quote is not None
        assert "high conf" in quote["text"]

    def test_returns_none_for_empty(self):
        df = pd.DataFrame(columns=["category", "text", "confidence"])
        quote = extract_top_quote(df, ["X"], {})
        assert quote is None

    def test_returns_none_when_no_categories(self):
        df = pd.DataFrame([
            {"category": "X", "text": "something", "confidence": 0.9,
             "title": "T", "source_name": "S"},
        ])
        quote = extract_top_quote(df, [], {})
        assert quote is None

    def test_filters_by_category(self):
        df = pd.DataFrame([
            {"category": "Wrong", "text": "wrong cat", "confidence": 0.99,
             "title": "T", "source_name": "S"},
            {"category": "Right", "text": "right cat", "confidence": 0.6,
             "title": "T", "source_name": "S"},
        ])
        quote = extract_top_quote(df, ["Right"], {})
        assert "right cat" in quote["text"]


class TestQnaQuestions:
    def test_all_have_required_fields(self):
        for q in QNA_QUESTIONS:
            assert "id" in q
            assert "question" in q
            assert "base_answer" in q
            assert "evidence_categories" in q

    def test_unique_ids(self):
        ids = [q["id"] for q in QNA_QUESTIONS]
        assert len(ids) == len(set(ids))


class TestBuildQnaDoc:
    def test_creates_markdown(self):
        df = pd.DataFrame([
            {"category": "Grid Resilience", "text": "Grid grows 20%",
             "confidence": 0.9, "title": "Source", "source_name": "X"},
        ])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "qna.md"
            result = build_qna_doc(df, None, None, output)
            assert result.exists()
            content = result.read_text()
            assert "Q&A Defense" in content

    def test_includes_valuation_summary(self):
        valuation = {
            "long_expected_return": 19.0,
            "short_expected_return": -30.0,
            "pair_spread_return": 49.0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "qna.md"
            build_qna_doc(None, valuation, None, output)
            content = output.read_text()
            assert "19.0" in content
            assert "49.0" in content

    def test_includes_narrative_shift(self):
        narrative = {
            "total_signals": 100,
            "grid_signal_share": 0.45,
            "oil_signal_share": 0.10,
            "grid_positive_rate": 0.9,
            "oil_negative_rate": 0.8,
            "thesis_support_score": 0.35,
            "interpretation": "Strong support",
        }
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "qna.md"
            build_qna_doc(None, None, narrative, output)
            content = output.read_text()
            assert "Strong support" in content
            assert "100" in content

    def test_handles_no_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "qna.md"
            build_qna_doc(None, None, None, output)
            assert output.exists()
            content = output.read_text()
            # Still has questions
            assert "Q1" in content
