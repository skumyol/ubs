#!/usr/bin/env python3
"""Multi-provider LLM client for the UBS pipeline.

Supports:
- OpenRouter (primary - best for general models)
- DeepSeek (cheap reasoning models)
- DashScope (Alibaba/Qwen - great for Chinese content)
- OpenAI-compatible fallback
"""

import os
import json
import time
from typing import Optional, Dict, List, Any, Literal
from pathlib import Path
import requests

# Load .env if present
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

Provider = Literal["openrouter", "deepseek", "dashscope", "openai"]


class LLMClient:
    """Universal LLM client with automatic failover across providers."""

    PROVIDER_CONFIG = {
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "env_key": "OPENROUTER_API_KEY",
            # Reasoning models: qwen/qwen3.5-122b-a10b (when available)
            # Fallback: qwen/qwen-2.5-72b-instruct, anthropic/claude-3.5-sonnet
            "default_model": "qwen/qwen-2.5-72b-instruct",
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "env_key": "DEEPSEEK_API_KEY",
            "default_model": "deepseek-chat",
        },
        "dashscope": {
            "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            "env_key": "DASHSCOPE_API_KEY",
            "default_model": "qwen3.6-plus",
        },
    }

    def __init__(self, provider: Optional[Provider] = None, api_key: Optional[str] = None):
        """Initialize LLM client.

        Args:
            provider: Explicit provider choice. If None, tries all in order.
            api_key: Explicit API key. If None, reads from env.
        """
        self.provider = provider
        self.explicit_key = api_key
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ubs-challenge",
            "X-Title": "UBS Energy Transition Research",
        })

    def _get_key(self, provider: str) -> Optional[str]:
        if self.explicit_key:
            return self.explicit_key
        return os.getenv(self.PROVIDER_CONFIG[provider]["env_key"])

    def _build_headers(self, provider: str) -> Dict[str, str]:
        key = self._get_key(provider)
        if not key:
            raise ValueError(f"No API key for {provider}")
        headers = {"Authorization": f"Bearer {key}"}
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://localhost"
            headers["X-Title"] = "UBS Research Pipeline"
        return headers

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        timeout: int = 120,
        reasoning: bool = False,
    ) -> str:
        """Send chat completion request with automatic failover.

        Args:
            messages: List of {"role": "user"|"system"|"assistant", "content": str}
            model: Override default model for provider
            temperature: 0-1, lower = more deterministic
            max_tokens: Max response length
            timeout: Request timeout seconds (increased for reasoning models)
            reasoning: Enable reasoning for supported models (Qwen 3.5, etc.)

        Returns:
            Response text content
        """
        providers_to_try = []
        if self.provider:
            providers_to_try = [self.provider]
        else:
            # Priority: DashScope (Qwen) -> OpenRouter -> DeepSeek
            providers_to_try = ["dashscope", "openrouter", "deepseek"]

        last_error = None
        for prov in providers_to_try:
            try:
                key = self._get_key(prov)
                if not key:
                    continue

                cfg = self.PROVIDER_CONFIG[prov]
                url = f"{cfg['base_url']}/chat/completions"
                headers = self._build_headers(prov)
                payload = {
                    "model": model or cfg["default_model"],
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                # Enable reasoning for models that support it
                if reasoning and prov == "openrouter":
                    payload["reasoning"] = {"enabled": True}

                response = self._session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                data = response.json()

                # Extract content
                if "choices" in data and data["choices"]:
                    msg = data["choices"][0]["message"]
                    # Return content, but preserve reasoning_details if present
                    return msg.get("content", "")
                elif "output" in data:  # DashScope format
                    return data["output"]["text"]
                else:
                    return json.dumps(data, indent=2)

            except Exception as e:
                last_error = e
                print(f"  [WARN] {prov} failed: {e}")
                time.sleep(1)
                continue

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    def chat_with_reasoning(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """Send chat completion with reasoning support for multi-turn.

        Args:
            messages: List of message dicts. Can include reasoning_details from prior turns.
            model: Override default model
            temperature: 0-1
            max_tokens: Max response length
            timeout: Request timeout seconds

        Returns:
            Dict with 'content' (str) and 'reasoning_details' (list) if present
        """
        providers_to_try = ["openrouter"]  # Only OpenRouter supports reasoning_details

        if self.provider:
            providers_to_try = [self.provider]

        last_error = None
        for prov in providers_to_try:
            try:
                key = self._get_key(prov)
                if not key:
                    continue

                cfg = self.PROVIDER_CONFIG[prov]
                url = f"{cfg['base_url']}/chat/completions"
                headers = self._build_headers(prov)
                payload = {
                    "model": model or cfg["default_model"],
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "reasoning": {"enabled": True},
                }

                response = self._session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                data = response.json()

                if "choices" in data and data["choices"]:
                    msg = data["choices"][0]["message"]
                    return {
                        "content": msg.get("content", ""),
                        "reasoning_details": msg.get("reasoning_details", []),
                        "raw_message": msg,
                    }

            except Exception as e:
                last_error = e
                print(f"  [WARN] {prov} failed: {e}")
                time.sleep(1)
                continue

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000,
    ) -> Dict[str, Any]:
        """Generate structured JSON output from LLM.

        Args:
            prompt: User prompt requesting JSON output
            system_prompt: Optional system prompt
            temperature: Lower for more deterministic JSON
            max_tokens: Max response length

        Returns:
            Parsed JSON dict
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.chat(messages, temperature=temperature, max_tokens=max_tokens)

        # Try to extract JSON from response
        text = response.strip()

        # Handle markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON-like content
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            raise ValueError(f"Could not parse JSON from LLM response: {text[:500]}")


def quick_generate(prompt: str, provider: Optional[str] = None, **kwargs) -> str:
    """Quick one-off generation without instantiating client."""
    client = LLMClient(provider=provider)
    return client.chat([{"role": "user", "content": prompt}], **kwargs)


# Convenience aliases for specific use cases
def generate_investment_thesis(
    company: str,
    context: str,
    bull_bear: bool = True,
) -> Dict[str, Any]:
    """Generate investment thesis using LLM."""
    system = (
        "You are a senior equity research analyst at a top investment bank. "
        "Generate structured, evidence-based investment theses. "
        "Always return valid JSON with keys: thesis_summary, key_bull_points, key_bear_points, "
        "catalysts, risks, confidence_score (1-10)."
    )
    prompt = f"""Analyze {company} based on the following context:

{context}

Generate a structured investment thesis. Return ONLY valid JSON."""

    client = LLMClient()
    return client.generate_structured(prompt, system_prompt=system, temperature=0.3)


def generate_evidence_quotes(
    text: str,
    topic: str,
    max_quotes: int = 5,
) -> List[Dict[str, str]]:
    """Extract killer evidence quotes from text using LLM."""
    system = (
        "You extract powerful, quotable evidence from research text. "
        "Return JSON array of objects with: quote (exact text), relevance_score (1-10), "
        "key_theme, source_reference."
    )
    prompt = f"""Extract {max_quotes} most compelling evidence quotes about '{topic}' from this text:

{text[:8000]}

Return ONLY valid JSON array."""

    client = LLMClient()
    result = client.generate_structured(prompt, system_prompt=system, temperature=0.2)
    if isinstance(result, list):
        return result
    elif isinstance(result, dict) and "quotes" in result:
        return result["quotes"]
    else:
        return []


def generate_deck_slide_content(
    slide_title: str,
    context: str,
    bullet_count: int = 5,
) -> List[str]:
    """Generate slide bullet points using LLM."""
    prompt = f"""Generate {bullet_count} concise, investment-grade bullet points for a pitch deck slide titled:

"{slide_title}"

Context:
{context}

Requirements:
- Each bullet should be 10-25 words
- Use data where possible
- Lead with the insight, not the process
- One bullet per key point
- No fluff, no hedging language

Return as a simple numbered list, one bullet per line."""

    client = LLMClient()
    response = client.chat([{"role": "user", "content": prompt}], temperature=0.3)

    # Parse bullet points
    bullets = []
    for line in response.strip().split("\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
            # Remove numbering/bullet markers
            cleaned = line.lstrip("0123456789.-* ").strip()
            if cleaned:
                bullets.append(cleaned)
    return bullets[:bullet_count]


if __name__ == "__main__":
    # Quick test
    print("="*60)
    print("Testing LLM Client")
    print("="*60)

    # Test with different models
    test_prompt = "Calculate the expected return for a pair trade: Long Dongfang (expected +97%) / Short Jereh (expected -5%). What's the spread?"

    # Test 1: OpenRouter with Qwen (no reasoning - qwen-2.5 doesn't support it)
    print("\n[1] Testing OpenRouter with Qwen 2.5 72B...")
    client = LLMClient(provider="openrouter")
    try:
        result = client.chat(
            messages=[{"role": "user", "content": test_prompt}],
            model="qwen/qwen-2.5-72b-instruct",
            temperature=0.1,
            max_tokens=500,
        )
        print(f"✓ Response: {result[:200]}...")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 2: DeepSeek (has built-in reasoning)
    print("\n[2] Testing DeepSeek...")
    client_ds = LLMClient(provider="deepseek")
    try:
        result = client_ds.chat(
            messages=[{"role": "user", "content": test_prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        print(f"✓ Response: {result[:200]}...")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 3: Auto-failover
    print("\n[3] Testing auto-failover (no provider specified)...")
    client_auto = LLMClient()
    try:
        result = client_auto.chat(
            messages=[{"role": "user", "content": "Say 'UBS Energy Transition pipeline ready' in one sentence."}],
            temperature=0.1,
            max_tokens=100,
        )
        print(f"✓ Response: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)
