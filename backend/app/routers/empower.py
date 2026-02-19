"""Router for POST /empower/analyze."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import EmpowerRequest, EmpowerResponse
from app.services.empower import analyze_empowerment
from app.services.translator import translate_text, translate_batch

router = APIRouter(prefix="/empower", tags=["Empower"])


@router.post("/analyze", response_model=EmpowerResponse)
async def empower_analyze(body: EmpowerRequest) -> EmpowerResponse:
    """Analyze a citizen's legal issue: classify, find precedents, assess strength.

    Returns structured data consumable by both the frontend and the AI layer.
    Supports optional lang parameter for multilingual results.
    """
    try:
        response = analyze_empowerment(query=body.query, context=body.context)

        # Translate results if non-English language requested
        if body.lang and body.lang != "en":
            # Translate issue type
            response.issue_type = translate_text(response.issue_type, body.lang)

            # Translate action steps in batch
            if response.action_steps:
                response.action_steps = translate_batch(response.action_steps, body.lang)

            # Translate relevant sections (statute badges) in batch
            if response.relevant_sections:
                response.relevant_sections = translate_batch(response.relevant_sections, body.lang)

            # Translate precedent case names, courts, and summaries
            if response.precedents:
                summaries = [p.summary for p in response.precedents]
                translated_summaries = translate_batch(summaries, body.lang)

                case_names = [p.case_name for p in response.precedents]
                translated_names = translate_batch(case_names, body.lang)

                courts = [p.court for p in response.precedents]
                translated_courts = translate_batch(courts, body.lang)

                for prec, t_summary, t_name, t_court in zip(
                    response.precedents, translated_summaries, translated_names, translated_courts
                ):
                    prec.summary = t_summary
                    prec.case_name = t_name
                    prec.court = t_court

        return response
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during analysis: {exc}",
        ) from exc
