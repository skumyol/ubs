"""AI text classification utilities for energy-security signal tracking."""

import json
import time
from typing import Dict, List, Optional


# Category definitions used across the pipeline
CATEGORIES = [
    "Oil Supply Disruption",
    "Oilfield Cost Pressure",
    "Grid Resilience",
    "Electricity Demand",
    "Policy-Backed Capex",
    "Margin / Earnings Risk",
]


def build_classification_prompt(paragraph: str, template: str) -> str:
    """Insert paragraph into classification prompt template.

    Args:
        paragraph: Text excerpt to classify.
        template: Prompt template with [INSERT TEXT] placeholder.

    Returns:
        Ready-to-send prompt string.
    """
    return template.replace("[INSERT TEXT]", paragraph.strip())


def parse_ai_response(response_text: str) -> Dict:
    """Parse AI JSON response safely. Returns fallback on failure.

    Args:
        response_text: Raw text from AI model (expected JSON).

    Returns:
        Dict with keys: category, sentiment, confidence, reason.
    """
    try:
        data = json.loads(response_text)
        return {
            "category": data.get("category", "Unclassified"),
            "sentiment": data.get("sentiment", "neutral").lower(),
            "confidence": int(data.get("confidence", 0)),
            "reason": data.get("reason", ""),
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "category": "Parse Error",
            "sentiment": "neutral",
            "confidence": 0,
            "reason": "AI response could not be parsed.",
        }


def classify_batch(
    paragraphs: List[str],
    prompt_template: str,
    call_llm_fn,
    delay_seconds: float = 1.0,
) -> List[Dict]:
    """Classify a batch of paragraphs with rate-limiting.

    Args:
        paragraphs: List of text excerpts.
        prompt_template: Template with [INSERT TEXT] placeholder.
        call_llm_fn: Callable that takes a prompt string and returns response text.
        delay_seconds: Sleep between calls to respect rate limits.

    Returns:
        List of classification dicts (one per paragraph).
    """
    results = []

    for paragraph in paragraphs:
        prompt = build_classification_prompt(paragraph, prompt_template)

        try:
            response = call_llm_fn(prompt)
            parsed = parse_ai_response(response)
        except Exception as e:
            parsed = {
                "category": "Error",
                "sentiment": "neutral",
                "confidence": 0,
                "reason": f"Exception: {e}",
            }

        results.append(parsed)
        time.sleep(delay_seconds)

    return results
