"""
Layer 0 — Query Normalizer

Transforms citizen-language queries into effective search terms.

Pipeline:
    Raw query → Lowercase → Remove stopwords → Expand synonyms → Detect domain → Output

Example:
    "My landlord refuses to return my deposit"
    → tokens: ["landlord", "refuses", "return", "deposit"]
    → expanded: ["landlord", "tenant", "refuses", "return", "deposit", "security deposit"]
    → domain: "Property Law"
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.config import STOPWORDS, LEGAL_SYNONYMS, ISSUE_KEYWORDS


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
    4. Detect legal domain
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

    # Step 4: Detect legal domain
    domain = _detect_domain(query)

    return NormalizedQuery(
        raw_query=query,
        tokens=tokens,
        expanded_terms=expanded,
        detected_domain=domain,
    )


# ---------------------------------------------------------------------------
# Domain Detection
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
