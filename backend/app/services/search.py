"""
Search service — TF-IDF + Semantic Re-ranking pipeline.

Pipeline:
    0. Query Normalization  (stopwords, synonyms, domain detection)
    1. TF-IDF Retrieval     (cosine similarity over enriched case corpus)
    2. Authority Filter     (research mode: prefer SC > HC)
    3. User Filters         (court, year range)
    4. Semantic Re-rank     (sentence-transformer re-orders top candidates)
    5. Cache                (store results for repeat queries)
    6. Output Builder       (structured response)
"""

from __future__ import annotations

import hashlib
import logging

from app.config import get_authority_tier, AUTHORITY_MIN_HIGH_TIER
from app.models.schemas import CaseRecord, CaseResult, SearchFilters, SearchResponse
from app.services.tfidf_index import build_index, get_index
from app.services.semantic_reranker import build_reranker, get_reranker
from app.services.query_normalizer import normalize_query
from app.services.kanoon_adapter import get_all_cases
from app.services.cache import cache

logger = logging.getLogger(__name__)

_index_built = False


def _ensure_index() -> None:
    global _index_built
    if not _index_built:
        cases = get_all_cases()
        build_index(cases)
        build_reranker(cases)
        _index_built = True
        logger.info(f"Search TF-IDF index + semantic re-ranker ready ({len(cases)} cases).")


# ---------------------------------------------------------------------------
# Authority filter (research mode: SC/HC preferred)
# ---------------------------------------------------------------------------

def _authority_filter(
    scored: list[tuple[CaseRecord, float, dict]],
) -> list[tuple[CaseRecord, float, dict]]:
    """
    In research mode, if enough SC+HC results exist, deprioritize lower courts.
    Cases are not dropped — lower courts are moved to the end.
    """
    higher  = [(c, s, b) for c, s, b in scored if get_authority_tier(c.court) <= 2]
    lower   = [(c, s, b) for c, s, b in scored if get_authority_tier(c.court) >  2]

    if len(higher) >= AUTHORITY_MIN_HIGH_TIER:
        return higher + lower   # Higher courts first

    return scored   # Not enough authoritative results; keep original order


# ---------------------------------------------------------------------------
# User filters
# ---------------------------------------------------------------------------

def _apply_filters(
    scored: list[tuple[CaseRecord, float, dict]],
    filters: SearchFilters | None,
) -> list[tuple[CaseRecord, float, dict]]:
    if filters is None:
        return scored

    result = scored

    if filters.court:
        result = [(c, s, b) for c, s, b in result
                  if c.court.lower() == filters.court.lower()]

    if filters.year_start is not None:
        result = [(c, s, b) for c, s, b in result if c.year >= filters.year_start]

    if filters.year_end is not None:
        result = [(c, s, b) for c, s, b in result if c.year <= filters.year_end]

    return result


# ---------------------------------------------------------------------------
# Search Pipeline
# ---------------------------------------------------------------------------

def search_cases(query: str, filters: SearchFilters | None = None) -> SearchResponse:
    """
    Full search pipeline:
        normalize → TF-IDF retrieve → authority filter → user filter
        → semantic re-rank → cache → output
    """

    # Layer 0: Normalize
    normalized = normalize_query(query)

    # Build search string: original query + expanded synonyms
    search_parts = [query] + (normalized.expanded_terms or [])
    search_string = " ".join(search_parts)

    # Cache key (skip cache when filters are active)
    filters_hash = (
        hashlib.md5(str(filters).encode()).hexdigest()[:6] if filters else "nofilter"
    )
    cache_key = f"search_tfidf:{normalized.search_string}:{filters_hash}"
    cached = cache.get_query(cache_key)
    if cached and filters is None:
        return cached

    # Layer 1: TF-IDF retrieval
    _ensure_index()
    index   = get_index()
    scored  = index.search(search_string, top_n=100, min_score=0.005)

    # Layer 2: Authority filter (research cares about court tier)
    scored = _authority_filter(scored)

    # Layer 3: User filters
    scored = _apply_filters(scored, filters)

    # Layer 4: Semantic re-ranking
    # Re-ranker refines ordering using sentence embeddings.
    # Falls back to TF-IDF order if model unavailable.
    reranker = get_reranker()
    scored   = reranker.rerank(query, scored, top_n=None)

    # Keep only cases with a meaningful score
    MIN_SCORE = 0.005
    scored = [(c, s, b) for c, s, b in scored if b.get("tfidf_score", 0.0) >= MIN_SCORE]

    # Layer 5: Build output
    top_cases: list[CaseResult] = []
    for case, score, bd in scored:
        top_cases.append(CaseResult(
            kanoon_tid=case.kanoon_tid,
            case_name=case.case_name,
            court=case.court,
            year=case.year,
            citation_count=case.citation_count,
            strength_score=round(score, 4),
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

    if filters is None:
        cache.set_query(cache_key, response)

    return response
