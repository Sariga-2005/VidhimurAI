"""Router for POST /empower/analyze."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import EmpowerRequest, EmpowerResponse
from app.services.empower import analyze_empowerment

router = APIRouter(prefix="/empower", tags=["Empowerment"])


@router.post("/analyze", response_model=EmpowerResponse)
async def empower_analyze(body: EmpowerRequest) -> EmpowerResponse:
    """Analyze a citizen's legal issue: classify, find precedents, assess strength.

    Returns structured data consumable by both the frontend and the AI layer.
    """
    try:
        return analyze_empowerment(query=body.query, context=body.context)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during analysis: {exc}",
        ) from exc
