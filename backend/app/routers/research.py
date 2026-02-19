"""Router for POST /research/search."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import SearchRequest, SearchResponse
from app.services.search import search_cases
from app.services.translator import translate_batch

router = APIRouter(prefix="/research", tags=["Research"])


@router.post("/search", response_model=SearchResponse)
async def research_search(body: SearchRequest) -> SearchResponse:
    """Search legal cases with deterministic ranking.

    Supports optional filters for court and year range.
    Supports optional lang parameter for multilingual results.
    """
    try:
        response = search_cases(query=body.query, filters=body.filters)

        # Translate results if non-English language requested
        if body.lang and body.lang != "en" and response.top_cases:
            # Batch translate summaries
            summaries = [c.summary for c in response.top_cases]
            translated_summaries = translate_batch(summaries, body.lang)

            # Batch translate case names
            case_names = [c.case_name for c in response.top_cases]
            translated_names = translate_batch(case_names, body.lang)

            # Batch translate court names
            courts = [c.court for c in response.top_cases]
            translated_courts = translate_batch(courts, body.lang)

            for case, t_summary, t_name, t_court in zip(
                response.top_cases, translated_summaries, translated_names, translated_courts
            ):
                case.summary = t_summary
                case.case_name = t_name
                case.court = t_court

            # Also translate the most influential case if present
            if response.most_influential_case and response.top_cases:
                response.most_influential_case = response.top_cases[0]

        return response
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during search: {exc}",
        ) from exc

