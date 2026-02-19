"""Search service — loads dataset, applies filters, ranks results."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.models.schemas import CaseRecord, CaseResult, SearchFilters, SearchResponse
from app.services.ranking import compute_score, tokenize_query
from app.services.kanoon_adapter import get_all_cases


# ---------------------------------------------------------------------------
# Filtering
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
# Search pipeline
# ---------------------------------------------------------------------------

def search_cases(query: str, filters: SearchFilters | None = None) -> SearchResponse:
    """Full search pipeline: load → filter → rank → format."""

    cases = get_all_cases()
    filtered = _apply_filters(cases, filters)
    tokens = tokenize_query(query)

    # Score every case
    scored: list[tuple[CaseRecord, float, dict]] = []
    for case in filtered:
        score, _breakdown = compute_score(case, tokens)
        scored.append((case, score, _breakdown))

    # Sort descending by score
    scored.sort(key=lambda x: x[1], reverse=True)

    # Build response
    top_cases: list[CaseResult] = []
    for case, score, _bd in scored:
        top_cases.append(CaseResult(
            kanoon_tid=case.kanoon_tid,
            case_name=case.case_name,
            court=case.court,
            year=case.year,
            citation_count=case.citation_count,
            strength_score=score,
            summary=case.summary,
        ))

    most_influential = top_cases[0] if top_cases else None

    return SearchResponse(
        total_cases=len(top_cases),
        top_cases=top_cases,
        most_influential_case=most_influential,
    )
