"""
Deterministic ranking engine — Dual Scoring Model.

Produces three scores per case:
    authority_score  = (CourtWeight x 3) + (CitationCount x 0.5)
    relevance_score  = RecencyBoost + QueryOverlapScore
    final_score      = weighted combination based on mode

Mode weights (from config.SCORE_WEIGHTS):
    research → 0.7 authority + 0.3 relevance
    empower  → 0.5 authority + 0.5 relevance
"""

from __future__ import annotations

import math
import re

from app.config import (
    get_court_weight,
    CURRENT_YEAR,
    RECENCY_DECAY_RATE,
    RECENCY_MAX_BOOST,
    SCORE_WEIGHTS,
)
from app.models.schemas import CaseRecord


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_score(
    case: CaseRecord,
    query_tokens: list[str],
    mode: str = "research",
) -> tuple[float, dict]:
    """
    Return (final_score, breakdown_dict) for a case against the query.

    Parameters
    ----------
    case : CaseRecord
    query_tokens : list of normalized search tokens
    mode : "research" or "empower" — determines weighting
    """

    court_w = _court_weight(case.court)
    citation_s = _citation_score(case.citation_count)
    recency_b = _recency_boost(case.year)
    relevance_s = _relevance_score(case, query_tokens)

    # ---- Dual scores ----
    authority_score = (court_w * 3) + citation_s
    relevance_score = recency_b + relevance_s

    # ---- Mode-weighted final score ----
    # Relevance-Gated Authority: Authority only boosts proportionally to relevance.
    # This prevents irrelevant landmark cases (high authority, 0 relevance)
    # from dominating results in ANY mode.
    final_score = relevance_score + (authority_score * (relevance_score / 100.0))

    breakdown = {
        "authority_score": round(authority_score, 2),
        "relevance_score": round(relevance_score, 2),
        "final_score": round(final_score, 2),
        "mode": mode,
        # Component detail
        "court_weight": round(court_w * 3, 2),
        "citation_score": round(citation_s, 2),
        "recency_boost": round(recency_b, 2),
        "query_overlap": round(relevance_s, 2),
    }

    return round(final_score, 2), breakdown


def tokenize_query(query: str) -> list[str]:
    """Lowercase split + basic normalisation."""
    return [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]


# ---------------------------------------------------------------------------
# Component functions
# ---------------------------------------------------------------------------

def _court_weight(court: str) -> int:
    """Map court name → integer weight using pattern matching."""
    return get_court_weight(court)


def _citation_score(citation_count: int) -> float:
    """Citation contribution = log(count + 1).

    This drastically reduces the dominance of landmark cases with 100+ citations
    while still rewarding authority.
    """
    return math.log1p(citation_count) * 2


def _recency_boost(year: int) -> float:
    """Newer cases get up to RECENCY_MAX_BOOST points.

    Decays by RECENCY_DECAY_RATE per year of age.
    """
    age = CURRENT_YEAR - year
    boost = RECENCY_MAX_BOOST - (age * RECENCY_DECAY_RATE)
    return max(0.0, round(boost, 2))


def _relevance_score(case: CaseRecord, query_tokens: list[str]) -> float:
    """Keyword overlap score.

    Checks keywords, legal_issues, case_name, and summary for matches.
    Handles both single tokens and multi-word phrases (e.g. "sexual harassment").
    """
    if not query_tokens:
        return 0.0

    # Build a searchable text blob from the case
    case_text = " ".join([
        case.case_name.lower(),
        case.summary.lower(),
        " ".join(k.lower() for k in case.keywords),
        " ".join(i.lower() for i in case.legal_issues),
        " ".join(s.lower() for s in case.statutes_referenced),
    ])

    # Count matches — both single tokens and multi-word phrases
    matches = 0
    for token in query_tokens:
        if token in case_text:
            matches += 1

    ratio = matches / len(query_tokens)

    # Boost: Scale 0-1 ratio to 0-100 score
    return round(ratio * 100, 2)
