"""Deterministic ranking engine for legal case scoring.

Formula:
    Score = (CourtWeight × 3) + (CitationCount × 0.5) + RecencyBoost + RelevanceScore
"""

from __future__ import annotations

import re

from app.config import COURT_WEIGHTS, CURRENT_YEAR, RECENCY_DECAY_RATE, RECENCY_MAX_BOOST
from app.models.schemas import CaseRecord


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_score(case: CaseRecord, query_tokens: list[str]) -> tuple[float, dict]:
    """Return (total_score, breakdown_dict) for a given case against the query."""

    court_weight = _court_weight(case.court)
    citation_score = _citation_score(case.citation_count)
    recency_boost = _recency_boost(case.year)
    relevance_score = _relevance_score(case, query_tokens)

    total = (court_weight * 3) + (citation_score) + recency_boost + relevance_score

    breakdown = {
        "court_weight": round(court_weight * 3, 2),
        "citation_score": round(citation_score, 2),
        "recency_boost": round(recency_boost, 2),
        "relevance_score": round(relevance_score, 2),
    }

    return round(total, 2), breakdown


def tokenize_query(query: str) -> list[str]:
    """Lowercase split + basic normalisation."""
    return [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]


# ---------------------------------------------------------------------------
# Component functions
# ---------------------------------------------------------------------------

def _court_weight(court: str) -> int:
    """Map court name → integer weight."""
    return COURT_WEIGHTS.get(court, 4)


def _citation_score(citation_count: int) -> float:
    """Citation contribution = count × 0.5"""
    return citation_count * 0.5


def _recency_boost(year: int) -> float:
    """Newer cases get up to RECENCY_MAX_BOOST points.

    Decays by RECENCY_DECAY_RATE per year of age.
    """
    age = CURRENT_YEAR - year
    boost = RECENCY_MAX_BOOST - (age * RECENCY_DECAY_RATE)
    return max(0.0, round(boost, 2))


def _relevance_score(case: CaseRecord, query_tokens: list[str]) -> float:
    """Keyword overlap ratio × 10.

    Checks keywords, legal_issues, case_name, and summary for matches.
    """
    if not query_tokens:
        return 0.0

    # Build a bag of words from the case's searchable fields
    case_text = " ".join([
        case.case_name.lower(),
        case.summary.lower(),
        " ".join(k.lower() for k in case.keywords),
        " ".join(i.lower() for i in case.legal_issues),
    ])

    matches = sum(1 for token in query_tokens if token in case_text)
    ratio = matches / len(query_tokens)
    return round(ratio * 10, 2)
