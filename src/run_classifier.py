"""Run AI classification on paragraph dataset.

Requires an LLM API key set in environment or .env file.
Supports OpenAI, Anthropic, or any compatible API.
"""

import os
import time
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

from src.config import (
    PARAGRAPH_DATASET_PATH,
    CLASSIFIED_PARAGRAPHS_PATH,
    CLASSIFICATION_PROMPT_PATH,
    LLM_DELAY_SECONDS,
)
from src.classifier import classify_batch, parse_ai_response

load_dotenv()


def get_llm_caller():
    """Return a function that calls the configured LLM."""

    # Try DeepSeek API directly first
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com/v1",
            )

            def call_deepseek(prompt: str) -> str:
                resp = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are an equity research assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=200,
                )
                return resp.choices[0].message.content

            print("Using DeepSeek API")
            return call_deepseek

        except ImportError:
            pass

    # Try OpenRouter (can route to DeepSeek, OpenAI, etc.)
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
            )

            def call_openrouter(prompt: str) -> str:
                resp = client.chat.completions.create(
                    model="deepseek/deepseek-chat",  # or "openai/gpt-4o-mini", "anthropic/claude-3-haiku", etc.
                    messages=[
                        {"role": "system", "content": "You are an equity research assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=200,
                    extra_headers={
                        "HTTP-Referer": "https://ubs-research.local",
                        "X-Title": "UBS Energy Security Research",
                    },
                )
                return resp.choices[0].message.content

            print("Using OpenRouter API (DeepSeek)")
            return call_openrouter

        except ImportError:
            pass

    # Try OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=openai_key)

            def call_openai(prompt: str) -> str:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an equity research assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=200,
                )
                return resp.choices[0].message.content

            print("Using OpenAI API")
            return call_openai

        except ImportError:
            pass

    # Try Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=anthropic_key)

            def call_anthropic(prompt: str) -> str:
                resp = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=200,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.content[0].text

            print("Using Anthropic API")
            return call_anthropic

        except ImportError:
            pass

    raise RuntimeError(
        "No LLM API key found. Set DEEPSEEK_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in .env"
    )


def main():
    if not PARAGRAPH_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Paragraph dataset not found: {PARAGRAPH_DATASET_PATH}\n"
            "Run run_text_cleaner.py first."
        )

    if not CLASSIFICATION_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Prompt template not found: {CLASSIFICATION_PROMPT_PATH}"
        )

    prompt_template = CLASSIFICATION_PROMPT_PATH.read_text(encoding="utf-8")
    call_llm = get_llm_caller()

    df = pd.read_csv(PARAGRAPH_DATASET_PATH)

    # Resume support: check for existing classifications
    if CLASSIFIED_PARAGRAPHS_PATH.exists():
        existing = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
        done_ids = set(existing["paragraph_id"].tolist())
        print(f"Resuming: {len(done_ids)} already classified, {len(df) - len(done_ids)} remaining")
        df = df[~df["paragraph_id"].isin(done_ids)].copy()

    if len(df) == 0:
        print("All paragraphs already classified.")
        return

    results = []
    errors = 0

    print(f"Classifying {len(df)} paragraphs...")

    for _, row in tqdm(df.iterrows(), total=len(df)):
        paragraph = row["text"]
        prompt = prompt_template.replace("[INSERT TEXT]", paragraph.strip())

        try:
            response = call_llm(prompt)
            parsed = parse_ai_response(response)
        except Exception as e:
            parsed = {
                "category": "Error",
                "sentiment": "neutral",
                "confidence": 0,
                "reason": f"Exception: {e}",
            }
            errors += 1

        results.append({
            "paragraph_id": row["paragraph_id"],
            "doc_id": row["doc_id"],
            "source_name": row["source_name"],
            "company": row["company"],
            "sector": row["sector"],
            "document_type": row["document_type"],
            "theme": row["theme"],
            "text": paragraph,
            "category": parsed["category"],
            "sentiment": parsed["sentiment"],
            "confidence": parsed["confidence"],
            "reason": parsed["reason"],
            "human_review_status": "pending",
        })

        time.sleep(LLM_DELAY_SECONDS)

    # Save
    new_df = pd.DataFrame(results)

    if CLASSIFIED_PARAGRAPHS_PATH.exists():
        old_df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    final_df.to_csv(CLASSIFIED_PARAGRAPHS_PATH, index=False)

    print(f"\nSaved: {CLASSIFIED_PARAGRAPHS_PATH}")
    print(f"Classified: {len(final_df)} paragraphs")
    print(f"Errors: {errors}")
    print(f"\nCategories:")
    print(final_df["category"].value_counts(dropna=False))


if __name__ == "__main__":
    main()
