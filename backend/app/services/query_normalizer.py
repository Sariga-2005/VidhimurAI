"""
Layer 0 — Query Normalizer

Transforms citizen-language queries into effective search terms.

Pipeline:
    Raw query → Lowercase → Remove stopwords → Expand synonyms → Detect domain → Output

If deterministic keyword matching fails (returns "General Legal Issue"),
the LLM is used as a fallback to classify the legal domain and expand terms.

Example:
    "My landlord refuses to return my deposit"
    → tokens: ["landlord", "refuses", "return", "deposit"]
    → expanded: ["landlord", "tenant", "refuses", "return", "deposit", "security deposit"]
    → domain: "Property Law"

    "my city is very polluted"
    → keywords fail → LLM classifies as "Environmental Law"
    → expanded terms include: ["pollution", "environment", "ngt", ...]
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.config import STOPWORDS, LEGAL_SYNONYMS, ISSUE_KEYWORDS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Normalized Query Output
# ---------------------------------------------------------------------------

@dataclass
class NormalizedQuery:
    """Result of the normalization pipeline."""
    raw_query: str
    tokens: list[str]                          # Cleaned tokens (stopwords removed)
    expanded_terms: list[str]                  # Tokens + synonym expansions
    detected_domain: str                       # Best-match legal area
    search_string: str = ""                    # Final string for IK API

    def __post_init__(self):
        if not self.search_string:
            self.search_string = " ".join(self.expanded_terms)


# ---------------------------------------------------------------------------
# Normalizer Pipeline
# ---------------------------------------------------------------------------

def normalize_query(query: str) -> NormalizedQuery:
    """
    Full normalization pipeline.

    1. Lowercase + tokenize
    2. Remove stopwords
    3. Expand synonyms
    4. Detect legal domain (deterministic → LLM fallback)
    5. Build search string
    """

    # Step 1: Tokenize
    raw_tokens = re.split(r"\W+", query.lower())
    raw_tokens = [t for t in raw_tokens if t]   # Remove empty strings

    # Step 2: Remove stopwords
    tokens = [t for t in raw_tokens if t not in STOPWORDS and len(t) > 1]

    # Step 3: Expand synonyms
    expanded = list(tokens)  # Start with cleaned tokens
    seen = set(tokens)
    for token in tokens:
        synonyms = LEGAL_SYNONYMS.get(token, [])
        for syn in synonyms:
            if syn not in seen:
                expanded.append(syn)
                seen.add(syn)

    # Step 4: Detect legal domain (deterministic first)
    domain = _detect_domain(query)

    # Step 4b: LLM fallback — if keywords couldn't classify, ask the LLM
    if domain == "General Legal Issue":
        try:
            from app.services.llm_query_enhancer import llm_classify_query
            llm_result = llm_classify_query(query)
            if llm_result and llm_result.get("domain") != "General Legal Issue":
                domain = llm_result["domain"]
                # Merge LLM-suggested search terms into expanded terms
                for term in llm_result.get("search_terms", []):
                    if term not in seen:
                        expanded.append(term)
                        seen.add(term)
                logger.info(f"LLM enhanced query: domain={domain}, "
                            f"new terms={llm_result.get('search_terms', [])}")
        except Exception as e:
            logger.warning(f"LLM fallback failed, using deterministic: {e}")

    return NormalizedQuery(
        raw_query=query,
        tokens=tokens,
        expanded_terms=expanded,
        detected_domain=domain,
    )


# ---------------------------------------------------------------------------
# Domain Detection (deterministic)
# ---------------------------------------------------------------------------

def _detect_domain(query: str) -> str:
    """Match query against ISSUE_KEYWORDS to detect the legal domain."""
    query_lower = query.lower()
    scores: dict[str, int] = {}

    for area, keywords in ISSUE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[area] = score

    if not scores:
        return "General Legal Issue"

    return max(scores, key=scores.get)  # type: ignore[arg-type]
