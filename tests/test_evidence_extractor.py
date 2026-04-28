"""Tests for evidence extractor."""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
from src.evidence_extractor import (
    score_quote,
    clean_quote,
    extract_evidence,
    build_evidence_pack,
    is_boilerplate,
    SLIDE_EVIDENCE_MAP,
    SLIDE_DISPLAY_LIMIT,
)


class TestIsBoilerplate:
    def test_detects_call_participant_boilerplate(self):
        text = "Date Jan. 21, 2026 at 9 a.m. ET Call participants Chairman, President, and CEO Jeffrey Miller"
        assert is_boilerplate(text) is True

    def test_detects_motley_fool_transcribing(self):
        text = "Apr 21, 2026 By Motley Fool Transcribing Halliburton Q1 2026 Earnings Transcript"
        assert is_boilerplate(text) is True

    def test_detects_short_text(self):
        text = "Very short text."
        assert is_boilerplate(text) is True

    def test_detects_no_verbs(self):
        text = "Halliburton Schlumberger Baker Hughes International America Asia Europe Middle East"
        assert is_boilerplate(text) is True

    def test_accepts_substantive_content(self):
        text = "Sieyuan Electric reported that overseas revenue grew 35% driven by strong demand in Middle East grid upgrade projects."
        assert is_boilerplate(text) is False

    def test_accepts_earnings_quote(self):
        text = "Sequential revenue is expected to decrease by 12-13% in Q4 2025 with greater than typical white space cited."
        assert is_boilerplate(text) is False

    def test_detects_page_markers(self):
        text = "Electricity 2026 Demand PAGE | 24 IEA CC BY 4.0 Overview of renewable energy adoption rates in the electricity sector"
        assert is_boilerplate(text) is True


class TestDedupeAcrossSlides:
    def test_same_quote_not_used_twice(self):
        # Create fake classified data with duplicate content
        duplicate_quote = (
            "Electricity demand in the United States is expected to rise 2% per year "
            "driven by data centre expansion across multiple regions."
        )
        df = pd.DataFrame({
            "paragraph_id": [f"p_{i:04d}" for i in range(6)],
            "text": [duplicate_quote] * 6,
            "category": ["Electricity Demand"] * 6,
            "confidence": [0.95] * 6,
            "sentiment": ["positive"] * 6,
            "sector": ["Grid Infrastructure"] * 6,
            "source_name": ["IEA"] * 6,
            "title": ["IEA Report"] * 6,
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "evidence_pack"
            evidence = build_evidence_pack(df, output)

            # Count how many slides reference this same quote
            total_uses = sum(
                len([q for q in slide["quotes"] if duplicate_quote[:50] in q["quote"]])
                for slide in evidence.values()
            )
            # Dedupe should ensure max 1 use across all slides
            assert total_uses <= 1


class TestSlideDisplayLimit:
    def test_display_limit_defined_for_all_slides(self):
        for slide_id in SLIDE_EVIDENCE_MAP.keys():
            assert slide_id in SLIDE_DISPLAY_LIMIT
            assert SLIDE_DISPLAY_LIMIT[slide_id] > 0


class TestScoreQuote:
    def test_quantification_boosts_score(self):
        with_pct = score_quote(
            "Sieyuan reported that revenue grew 15% year over year driven by strong overseas orders.",
            0.8,
        )
        without_pct = score_quote(
            "Sieyuan reported that revenue grew significantly this year driven by strong overseas orders.",
            0.8,
        )
        assert with_pct > without_pct

    def test_dollar_amounts_boost_score(self):
        with_dollar = score_quote(
            "Halliburton announced capex of $500M planned for international drilling operations next year.",
            0.8,
        )
        without_dollar = score_quote(
            "Halliburton announced capex is planned for international drilling operations next year.",
            0.8,
        )
        assert with_dollar > without_dollar

    def test_navigation_text_penalized(self):
        nav = score_quote(
            "Subscribe to our cookie policy newsletter and accept privacy policy terms here.",
            0.9,
        )
        normal = score_quote(
            "Grid investment is accelerating globally with transmission upgrade projects announced across multiple regions.",
            0.9,
        )
        assert nav < normal

    def test_too_short_penalized(self):
        short = score_quote("Yes.", 0.9)
        normal = score_quote(
            "Sieyuan reported 20% revenue growth driven by overseas markets and expanding grid orders.",
            0.9,
        )
        assert short < normal


class TestCleanQuote:
    def test_removes_extra_whitespace(self):
        result = clean_quote("Hello    world\n\n\ntest")
        assert "    " not in result
        assert "\n\n\n" not in result

    def test_truncates_long_text(self):
        long_text = "Sentence one. " * 50
        result = clean_quote(long_text, max_length=100)
        assert len(result) <= 105  # Allow small overshoot for "..."

    def test_truncates_at_sentence_boundary(self):
        text = "First sentence. Second sentence. Third sentence."
        result = clean_quote(text, max_length=20)
        # Should stop at sentence boundary or truncate cleanly
        assert len(result) <= 25


class TestExtractEvidence:
    def make_classified_df(self):
        return pd.DataFrame([
            {
                "text": "Sieyuan reports 25% growth in Q3 with $500M new orders from Middle East.",
                "category": "Grid Resilience",
                "sentiment": "positive",
                "confidence": 0.9,
                "title": "Q3 Earnings",
                "source_name": "Reuters",
            },
            {
                "text": "Subscribe to newsletter cookie policy.",
                "category": "Grid Resilience",
                "sentiment": "neutral",
                "confidence": 0.95,
                "title": "Newsletter",
                "source_name": "Site",
            },
            {
                "text": "Halliburton margin compressed 200bps on logistics costs in Q2 2026.",
                "category": "Margin/Earnings Risk",
                "sentiment": "negative",
                "confidence": 0.88,
                "title": "HAL Earnings",
                "source_name": "Bloomberg",
            },
        ])

    def test_filters_by_category(self):
        df = self.make_classified_df()
        config = {
            "title": "Test",
            "categories": ["Grid Resilience"],
            "min_confidence": 0.5,
            "max_quotes": 5,
        }
        quotes = extract_evidence(df, config)
        for q in quotes:
            assert q["category"] == "Grid Resilience"

    def test_navigation_text_excluded(self):
        """Even though the nav text has high confidence, it should rank below the real quote."""
        df = self.make_classified_df()
        config = {
            "title": "Test",
            "categories": ["Grid Resilience"],
            "min_confidence": 0.5,
            "max_quotes": 1,
        }
        quotes = extract_evidence(df, config)
        assert len(quotes) == 1
        # Real quote with $500M and 25% should beat the cookie policy text
        assert "Sieyuan" in quotes[0]["quote"]

    def test_respects_max_quotes(self):
        df = self.make_classified_df()
        config = {
            "title": "Test",
            "categories": ["Grid Resilience", "Margin/Earnings Risk"],
            "min_confidence": 0.5,
            "max_quotes": 1,
        }
        quotes = extract_evidence(df, config)
        assert len(quotes) <= 1

    def test_min_confidence_filter(self):
        df = self.make_classified_df()
        config = {
            "title": "Test",
            "categories": ["Grid Resilience"],
            "min_confidence": 0.99,  # Higher than any sample
            "max_quotes": 5,
        }
        quotes = extract_evidence(df, config)
        assert len(quotes) == 0

    def test_ai_module_one_per_category(self):
        df = self.make_classified_df()
        config = {
            "title": "AI Signal Tracker test",
            "categories": ["Grid Resilience", "Margin/Earnings Risk"],
            "min_confidence": 0.5,
            "max_quotes": 6,
        }
        quotes = extract_evidence(df, config)
        # AI module returns one per category
        categories = [q["category"] for q in quotes]
        assert len(set(categories)) == len(categories)


class TestBuildEvidencePack:
    def test_creates_json_and_markdown(self):
        df = pd.DataFrame([
            {
                "text": "Grid investment growing 20%.",
                "category": "Grid Resilience",
                "sentiment": "positive",
                "confidence": 0.85,
                "title": "Test",
                "source_name": "X",
            }
        ])

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "evidence_pack"
            evidence = build_evidence_pack(df, output)

            assert output.with_suffix(".json").exists()
            assert output.with_suffix(".md").exists()
            assert isinstance(evidence, dict)

    def test_pack_covers_all_slides(self):
        df = pd.DataFrame([{
            "text": "Test text.",
            "category": "Grid Resilience",
            "sentiment": "positive",
            "confidence": 0.85,
            "title": "Test",
            "source_name": "X",
        }])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "evidence_pack"
            evidence = build_evidence_pack(df, output)
            # All slides in map should appear
            assert set(evidence.keys()) == set(SLIDE_EVIDENCE_MAP.keys())
