"""
LLM Client — OpenRouter API wrapper for InsightAI.

All LLM calls go through this module.
Model: meta-llama/llama-3.1-8b-instruct:free  (fast, free tier on OpenRouter)
Fallback: mistralai/mistral-7b-instruct:free

API key is read from:
  1. OPENROUTER_API_KEY environment variable
  2. insight-ai/.env file
"""

import os
import json
import logging
from typing import Optional

import requests
from dotenv import load_dotenv

# Load .env from insight-ai/ directory
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

OPENROUTER_BASE   = "https://openrouter.ai/api/v1/chat/completions"
PRIMARY_MODEL     = "meta-llama/llama-3.3-70b-instruct:free"
FALLBACK_MODEL    = "google/gemma-3-12b-it:free"
DEFAULT_MAX_TOKENS = 1800
DEFAULT_TEMPERATURE = 0.3   # low = more focused, structured output


def get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. "
            "Add it to insight-ai/.env or set the environment variable."
        )
    return key


def chat(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    model: str = PRIMARY_MODEL,
) -> str:
    """
    Send a chat completion request to OpenRouter.

    Returns the assistant message text.
    Raises RuntimeError on API errors.
    """
    api_key = get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://insightai.local",
        "X-Title": "InsightAI",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "max_tokens":  max_tokens,
        "temperature": temperature,
    }

    try:
        resp = requests.post(OPENROUTER_BASE, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    except requests.HTTPError as e:
        # Try fallback model once
        if model != FALLBACK_MODEL:
            logger.warning("Primary model failed (%s), trying fallback…", e)
            return chat(system_prompt, user_prompt, max_tokens, temperature, FALLBACK_MODEL)
        raise RuntimeError(f"OpenRouter API error: {e} — {resp.text[:300]}")

    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}")


def is_available() -> bool:
    """Return True if the API key is configured and OpenRouter is reachable."""
    try:
        get_api_key()
        return True
    except RuntimeError:
        return False
