"""Lightweight translation service using Groq LLM.

Translates case-related text (case names, summaries, court names, action steps)
from English to the requested language. Returns original text for English.
"""

from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Any

# Load .ENV file from backend root
_env_path = Path(__file__).resolve().parent.parent.parent / ".ENV"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

logger = logging.getLogger(__name__)

# Language code → full name mapping
LANG_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
}


def _get_groq_client() -> Any:
    """Lazily create a Groq client."""
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key or api_key.startswith("gsk_74j2y4"):
            logger.warning("GROQ_API_KEY not set or is placeholder — translation disabled")
            return None
        return Groq(api_key=api_key)
    except ImportError:
        logger.warning("groq package not installed — translation disabled")
        return None


def translate_text(text: str, lang: str) -> str:
    """Translate a single text string to the target language using Groq."""
    if lang == "en" or not text or not text.strip():
        return text

    lang_name = LANG_NAMES.get(lang, lang)
    client = _get_groq_client()
    if client is None:
        return text  # Fallback: return original

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a translator. Translate the following text to {lang_name}. "
                        "Return ONLY the translated text, nothing else. "
                        "Translate everything including legal case names, court names, and statute references. "
                        "Do not add any explanation."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        translated = response.choices[0].message.content
        return translated.strip() if translated else text
    except Exception as exc:
        logger.error("Translation failed: %s", exc)
        return text  # Fallback: return original


def translate_batch(texts: list[str], lang: str) -> list[str]:
    """Translate multiple texts in a single LLM call for efficiency."""
    if lang == "en" or not texts:
        return texts

    lang_name = LANG_NAMES.get(lang, lang)
    client = _get_groq_client()
    if client is None:
        return texts

    # Pack texts as numbered list for batch translation
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a translator. Translate each numbered item below to {lang_name}. "
                        "Return ONLY the translated numbered list in the same format (e.g. '1. translated text'). "
                        "Translate everything including legal case names, court names, and statute references. "
                        "Do not add any explanation."
                    ),
                },
                {"role": "user", "content": numbered},
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        raw = response.choices[0].message.content or ""
        lines = raw.strip().split("\n")

        result: list[str] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove numbering prefix like "1. " or "1) "
            for sep in [". ", ") ", ": "]:
                idx = line.find(sep)
                if idx != -1 and line[:idx].isdigit():
                    line = line[idx + len(sep):]
                    break
            result.append(line)

        # If parsing failed, return originals
        if len(result) != len(texts):
            logger.warning("Batch translation count mismatch: expected %d, got %d", len(texts), len(result))
            return texts

        return result
    except Exception as exc:
        logger.error("Batch translation failed: %s", exc)
        return texts
