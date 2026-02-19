"""
LLM-powered query understanding — fallback for when deterministic
keyword matching can't classify the legal domain.

When the normalizer detects "General Legal Issue" (i.e., keywords didn't match),
this module uses the Groq LLM to:
    1. Classify the legal domain
    2. Extract key legal concepts
    3. Expand the query with relevant legal terms

This allows natural citizen language ("my city is very polluted") to be
correctly mapped to "Environmental Law" without hardcoding every word variant.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from app.config import ISSUE_KEYWORDS

logger = logging.getLogger(__name__)

# Lazy singleton — avoid import-time API calls
_llm_service = None


def _get_llm():
    """Lazy-load the LLM service to avoid import-time side effects."""
    global _llm_service
    if _llm_service is None:
        try:
            import sys
            from pathlib import Path
            backend_root = Path(__file__).resolve().parent.parent.parent
            if str(backend_root) not in sys.path:
                sys.path.insert(0, str(backend_root))
            from services.llm_service import LLMService
            _llm_service = LLMService()
        except Exception as e:
            logger.warning(f"Could not initialize LLM service: {e}")
    return _llm_service


# The valid domains the LLM can classify into
VALID_DOMAINS = list(ISSUE_KEYWORDS.keys())

SYSTEM_PROMPT = """You are a legal domain classifier for Indian law. 
Given a user's query (which may be in everyday language), you must:
1. Identify the legal domain it falls under
2. Extract the core legal concepts
3. Suggest relevant legal search terms

You must respond ONLY with valid JSON. No text before or after the JSON.

STRICT RULES:
- The domain MUST be one of: {domains}
- If the query genuinely doesn't fit any domain, use "General Legal Issue"
- search_terms should be legal terminology that would match Indian court cases
- Keep search_terms to 5-8 terms maximum
- Do NOT hallucinate or invent legal terms
"""

USER_PROMPT = """Classify this legal query and extract search terms:

Query: "{query}"

Respond with this exact JSON format:
{{
    "domain": "<one of the valid domains>",
    "search_terms": ["term1", "term2", "term3"],
    "reasoning": "<one line explaining why this domain>"
}}"""


def llm_classify_query(query: str) -> Optional[dict]:
    """
    Use LLM to classify a query into a legal domain and extract search terms.

    Returns:
        dict with keys: domain, search_terms, reasoning
        None if LLM is unavailable or fails
    """
    llm = _get_llm()
    if llm is None or llm.client is None:
        logger.info("LLM not available, falling back to deterministic classification.")
        return None

    try:
        system = SYSTEM_PROMPT.format(domains=", ".join(VALID_DOMAINS))
        prompt = USER_PROMPT.format(query=query)

        raw = llm.generate_json_response(prompt, system_role=system)
        if not raw:
            return None

        result = json.loads(raw)

        # Validate the domain is one we recognize
        if result.get("domain") not in VALID_DOMAINS:
            result["domain"] = "General Legal Issue"

        # Ensure search_terms is a list of strings
        terms = result.get("search_terms", [])
        result["search_terms"] = [str(t).lower() for t in terms if t]

        logger.info(f"LLM classified '{query}' → {result['domain']} "
                     f"(terms: {result['search_terms']})")
        return result

    except Exception as e:
        logger.error(f"LLM query classification failed: {e}")
        return None
