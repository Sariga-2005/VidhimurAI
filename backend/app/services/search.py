"""
Search service — production-grade pipeline.

Pipeline:
    0. Query Normalization  (stopwords, synonyms, domain detection)
    1. Retrieval            (load all cases from adapter)
    2. Authority Filter     (prioritize SC > HC > DC)
    3. User Filters         (court, year range)
    4. Deterministic Ranking (dual scoring: authority + relevance)
    5. Cache                (store results for repeat queries)
    6. Output Builder       (structured response)
"""

from __future__ import annotations

from app.config import get_authority_tier, AUTHORITY_MIN_HIGH_TIER, RELEVANCE_THRESHOLD
from app.models.schemas import CaseRecord, CaseResult, SearchFilters, SearchResponse
from app.services.ranking import compute_score, tokenize_query
from app.services.query_normalizer import normalize_query
from app.services.kanoon_adapter import get_all_cases
from app.services.cache import cache


# ---------------------------------------------------------------------------
# Layer 2 — Authority Filter
# ---------------------------------------------------------------------------

def _authority_filter(cases: list[CaseRecord]) -> list[CaseRecord]:
    """
    Prioritize higher courts. If enough SC + HC results exist,
    exclude district court cases to reduce noise.
    """
    higher = [c for c in cases if get_authority_tier(c.court) <= 2]

    if len(higher) >= AUTHORITY_MIN_HIGH_TIER:
        return higher  # Enough authoritative results; skip lower courts

    return cases  # Not enough high-tier; keep everything


# ---------------------------------------------------------------------------
# User Filters (court, year range)
# ---------------------------------------------------------------------------

def _apply_filters(cases: list[CaseRecord], filters: SearchFilters | None) -> list[CaseRecord]:
    if filters is None:
        return cases

    result = cases

    if filters.court:
        result = [c for c in result if c.court.lower() == filters.court.lower()]

    if filters.year_start is not None:
        result = [c for c in result if c.year >= filters.year_start]

    if filters.year_end is not None:
        result = [c for c in result if c.year <= filters.year_end]

    return result


# ---------------------------------------------------------------------------
# Search Pipeline
# ---------------------------------------------------------------------------

def search_cases(query: str, filters: SearchFilters | None = None) -> SearchResponse:
    """
    Full search pipeline:
        normalize → retrieve → authority filter → user filter → rank → cache → output
    """

    # Layer 0: Normalize query
    normalized = normalize_query(query)

    # Layer 6: Check query cache first
    cache_key = normalized.search_string
    cached = cache.get_query(cache_key)
    if cached and filters is None:
        return cached

    # Layer 1: Retrieve all cases
    cases = get_all_cases()

    # Layer 2: Authority filter (reduce noise)
    authoritative = _authority_filter(cases)

    # Layer 3: Apply user filters
    filtered = _apply_filters(authoritative, filters)

    # Layer 4: Dual scoring (mode = "research")
    tokens = normalized.expanded_terms or tokenize_query(query)
    scored: list[tuple[CaseRecord, float, dict]] = []
    for case in filtered:
        score, breakdown = compute_score(case, tokens, mode="research")
        scored.append((case, score, breakdown))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Layer 4b: Relevance-aware reranking
    # Separate cases with meaningful relevance from authority-only cases.
    # This prevents irrelevant landmark cases (high authority, 0 relevance)
    # from pushing genuinely relevant cases out of the top results.
    RESEARCH_RELEVANCE_MIN = 5.0
    relevant = [(c, s, b) for c, s, b in scored if b.get("relevance_score", 0) >= RESEARCH_RELEVANCE_MIN]
    authority_only = [(c, s, b) for c, s, b in scored if b.get("relevance_score", 0) < RESEARCH_RELEVANCE_MIN]

    # Show relevant cases first, then backfill with authority-only cases
    scored = relevant + authority_only

    # Layer 4c: Relevance threshold — hide cases with near-zero relevance
    scored = [(c, s, b) for c, s, b in scored if b.get("relevance_score", 0) >= RELEVANCE_THRESHOLD]

    # Layer 7: Build structured output
    top_cases: list[CaseResult] = []
    for case, score, bd in scored:
        top_cases.append(CaseResult(
            kanoon_tid=case.kanoon_tid,
            case_name=case.case_name,
            court=case.court,
            year=case.year,
            citation_count=case.citation_count,
            strength_score=score,
            authority_score=bd.get("authority_score", 0.0),
            relevance_score=bd.get("relevance_score", 0.0),
            summary=case.summary,
        ))

    most_influential = top_cases[0] if top_cases else None

    response = SearchResponse(
        total_cases=len(top_cases),
        top_cases=top_cases,
        most_influential_case=most_influential,
    )

    # Layer 6: Cache the result
    if filters is None:
        cache.set_query(cache_key, response)

    return response
