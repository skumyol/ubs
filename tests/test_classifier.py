"""Tests for src/classifier module."""

import pytest
import json
from src.classifier import (
    build_classification_prompt,
    parse_ai_response,
    classify_batch,
    CATEGORIES,
)


class TestBuildClassificationPrompt:
    """Test prompt building."""

    def test_inserts_text_at_placeholder(self):
        template = "Analyze: [INSERT TEXT]"
        paragraph = "This is the content."
        result = build_classification_prompt(paragraph, template)
        assert "This is the content." in result
        assert "[INSERT TEXT]" not in result

    def test_handles_empty_paragraph(self):
        template = "Analyze: [INSERT TEXT]"
        result = build_classification_prompt("", template)
        assert result == "Analyze: "

    def test_strips_whitespace_from_paragraph(self):
        template = "Analyze: [INSERT TEXT]"
        paragraph = "  content  "
        result = build_classification_prompt(paragraph, template)
        assert result == "Analyze: content"

    def test_preserves_template_structure(self):
        template = "Start [INSERT TEXT] End"
        paragraph = "middle"
        result = build_classification_prompt(paragraph, template)
        assert result == "Start middle End"


class TestParseAIResponse:
    """Test response parsing."""

    def test_parses_valid_json(self):
        response = '{"category": "Grid Resilience", "sentiment": "positive", "confidence": 5, "reason": "Mentions grid."}'
        result = parse_ai_response(response)
        assert result["category"] == "Grid Resilience"
        assert result["sentiment"] == "positive"
        assert result["confidence"] == 5
        assert result["reason"] == "Mentions grid."

    def test_sentiment_lowercase_conversion(self):
        response = '{"category": "Test", "sentiment": "POSITIVE", "confidence": 3, "reason": "Test."}'
        result = parse_ai_response(response)
        assert result["sentiment"] == "positive"

    def test_handles_parse_error_gracefully(self):
        response = "Not valid JSON"
        result = parse_ai_response(response)
        assert result["category"] == "Parse Error"
        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 0

    def test_handles_empty_string(self):
        result = parse_ai_response("")
        assert result["category"] == "Parse Error"

    def test_handles_missing_keys(self):
        response = '{"category": "Only Category"}'
        result = parse_ai_response(response)
        assert result["category"] == "Only Category"
        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 0
        assert result["reason"] == ""

    def test_handles_malformed_json(self):
        response = '{"category": "Test", "sentiment": }'
        result = parse_ai_response(response)
        assert result["category"] == "Parse Error"

    def test_handles_none_input(self):
        result = parse_ai_response(None)
        assert result["category"] == "Parse Error"


class TestClassifyBatch:
    """Test batch classification."""

    def test_classifies_all_paragraphs(self):
        mock_llm = lambda prompt: '{"category": "Test", "sentiment": "neutral", "confidence": 3, "reason": "Test."}'
        paragraphs = ["Para 1", "Para 2", "Para 3"]
        template = "Classify: [INSERT TEXT]"

        results = classify_batch(paragraphs, template, mock_llm, delay_seconds=0)

        assert len(results) == 3
        for result in results:
            assert result["category"] == "Test"
            assert result["sentiment"] == "neutral"

    def test_handles_llm_exception(self):
        def failing_llm(prompt):
            raise Exception("API Error")

        paragraphs = ["Para 1"]
        template = "Classify: [INSERT TEXT]"

        results = classify_batch(paragraphs, template, failing_llm, delay_seconds=0)

        assert len(results) == 1
        assert results[0]["category"] == "Error"
        assert "API Error" in results[0]["reason"]

    def test_empty_batch_returns_empty_list(self):
        mock_llm = lambda prompt: '{}'
        results = classify_batch([], "template", mock_llm, delay_seconds=0)
        assert results == []

    def test_respects_delay(self):
        import time
        mock_llm = lambda prompt: '{"category": "Test"}'
        start = time.time()
        classify_batch(["Para"], "template", mock_llm, delay_seconds=0.1)
        elapsed = time.time() - start
        assert elapsed >= 0.1


class TestCategories:
    """Test category definitions."""

    def test_categories_list_exists(self):
        assert len(CATEGORIES) == 6
        assert "Grid Resilience" in CATEGORIES
        assert "Oilfield Cost Pressure" in CATEGORIES

    def test_all_categories_are_strings(self):
        for cat in CATEGORIES:
            assert isinstance(cat, str)
            assert len(cat) > 0

    def test_no_duplicate_categories(self):
        assert len(CATEGORIES) == len(set(CATEGORIES))
