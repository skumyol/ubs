"""Text cleaning and paragraph splitting for AI classification pipeline."""

import re
from typing import List


def clean_text(text: str) -> str:
    """Remove boilerplate, normalize whitespace, strip encoding artifacts.

    Args:
        text: Raw text from scraped web pages, PDFs, or transcripts.

    Returns:
        Cleaned text with normalized whitespace and removed artifacts.
    """
    # Remove null bytes and other encoding artifacts
    text = text.replace("\x00", "")

    # Normalize whitespace: tabs and multiple spaces -> single space
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize line breaks: 3+ newlines -> 2 newlines (paragraph separator)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove common boilerplate patterns
    boilerplate_patterns = [
        r"Forward-looking statements.*?\n",
        r"This document contains forward-looking.*?\n",
        r"Safe Harbor Statement.*?\n",
        r"Copyright ©.*?\n",
        r"All rights reserved.*?\n",
        r"Privacy Policy.*?\n",
        r"Terms of Use.*?\n",
        r"Cookie Policy.*?\n",
    ]

    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Remove website navigation headers (common in RSS scrapes)
    nav_patterns = [
        r"Direct naar inhoud.*?\n",
        r"Skip to content.*?\n",
        r"Go to home.*?\n",
        r"Home\s*\n",
        r"Menu\s*\n",
        r"Search\s*\n",
        r"Login\s*\n",
        r"Subscribe\s*\n",
        r"Advertisement\s*\n",
        r"Sponsored\s*\n",
        r"Offshore-Energy\.biz.*?\n",
        r"offshoreWIND\.biz.*?\n",
        r"DredgingToday\.com.*?\n",
        r"NavalToday\.com.*?\n",
        r"Green Marine.*?\n",
        r"Exhibition and Conference.*?\n",
        r"Advertising.*?\n",
    ]

    for pattern in nav_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    return text.strip()


def split_into_paragraphs(
    text: str,
    min_chars: int = 120,
    max_chars: int = 1800,
) -> List[str]:
    """Split text into coherent paragraph chunks for AI classification.

    Splits on double newlines first, then sentence boundaries for oversized
    chunks. Filters out fragments below min_chars.

    Args:
        text: Cleaned text to split.
        min_chars: Minimum paragraph length to keep (filters headers/fragments).
        max_chars: Maximum paragraph length before sentence-level splitting.

    Returns:
        List of paragraph strings meeting length criteria.
    """
    raw_chunks = re.split(r"\n{2,}", text)
    paragraphs = []

    for chunk in raw_chunks:
        chunk = chunk.strip()

        if len(chunk) < min_chars:
            continue

        if len(chunk) <= max_chars:
            paragraphs.append(chunk)
            continue

        # Oversized chunk: split at sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", chunk)
        buffer = ""

        for sentence in sentences:
            if len(buffer) + len(sentence) <= max_chars:
                buffer += " " + sentence if buffer else sentence
            else:
                if len(buffer.strip()) >= min_chars:
                    paragraphs.append(buffer.strip())
                buffer = sentence

        # Don't lose the last buffer
        if len(buffer.strip()) >= min_chars:
            paragraphs.append(buffer.strip())

    return paragraphs
