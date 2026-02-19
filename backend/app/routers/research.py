"""Router for POST /research/search."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import SearchRequest, SearchResponse
from app.services.search import search_cases

router = APIRouter(prefix="/research", tags=["Research"])


@router.post("/search", response_model=SearchResponse)
async def research_search(body: SearchRequest) -> SearchResponse:
    """Search legal cases with deterministic ranking.

    Supports optional filters for court and year range.
    """
    try:
        return search_cases(query=body.query, filters=body.filters)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during search: {exc}",
        ) from exc
