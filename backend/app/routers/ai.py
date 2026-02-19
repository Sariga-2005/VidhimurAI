"""Router for AI / LLM-powered legal services.

Endpoints:
    POST /ai/simplify   — Simplify legal text to layman terms
    POST /ai/translate  — Translate legal text to another language
    POST /ai/draft      — Generate a legal complaint draft
    POST /ai/roadmap    — Generate a detailed action roadmap
    POST /ai/enhance    — AI-enhanced case summaries and analysis
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    SimplifyRequest, SimplifyResponse,
    TranslateRequest, TranslateResponse,
    DraftRequest, DraftResponse,
    RoadmapRequest,
    EnhanceRequest,
)

# Import LLM services from backend/services/
import sys
from pathlib import Path
# Add the backend root to sys.path so we can import from 'services'
_backend_root = Path(__file__).resolve().parent.parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from services.simplifier import Simplifier
from services.translator import Translator
from services.draft_generator import DraftGenerator
from services.roadmap_generator import RoadmapGenerator
from services.research_ai_enhancer import ResearchAIEnhancer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Services"])

# Lazy-init singletons (created on first request, not at import time)
_simplifier: Simplifier | None = None
_translator: Translator | None = None
_draft_gen: DraftGenerator | None = None
_roadmap_gen: RoadmapGenerator | None = None
_enhancer: ResearchAIEnhancer | None = None


def _get_simplifier() -> Simplifier:
    global _simplifier
    if _simplifier is None:
        _simplifier = Simplifier()
    return _simplifier


def _get_translator() -> Translator:
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def _get_draft_gen() -> DraftGenerator:
    global _draft_gen
    if _draft_gen is None:
        _draft_gen = DraftGenerator()
    return _draft_gen


def _get_roadmap_gen() -> RoadmapGenerator:
    global _roadmap_gen
    if _roadmap_gen is None:
        _roadmap_gen = RoadmapGenerator()
    return _roadmap_gen


def _get_enhancer() -> ResearchAIEnhancer:
    global _enhancer
    if _enhancer is None:
        _enhancer = ResearchAIEnhancer()
    return _enhancer


# ---------------------------------------------------------------------------
# POST /ai/simplify
# ---------------------------------------------------------------------------

@router.post("/simplify", response_model=SimplifyResponse)
async def simplify_text(body: SimplifyRequest) -> SimplifyResponse:
    """Simplify complex legal text into layman-friendly language."""
    try:
        result = _get_simplifier().simplify(body.legal_summary)
        return SimplifyResponse(simplified_summary=result.get("simplified_summary", ""))
    except Exception as exc:
        logger.error(f"Simplify error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# POST /ai/translate
# ---------------------------------------------------------------------------

@router.post("/translate", response_model=TranslateResponse)
async def translate_text(body: TranslateRequest) -> TranslateResponse:
    """Translate legal text into the target language."""
    try:
        result = _get_translator().translate(body.legal_draft, body.target_language)
        return TranslateResponse(translated_text=result.get("translated_text", ""))
    except Exception as exc:
        logger.error(f"Translate error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# POST /ai/draft
# ---------------------------------------------------------------------------

@router.post("/draft", response_model=DraftResponse)
async def generate_draft(body: DraftRequest) -> DraftResponse:
    """Generate a legal complaint draft from structured case data."""
    try:
        case_data = {
            "issue_type": body.issue_type,
            "relevant_sections": body.relevant_sections,
            "precedents": body.precedents,
            "legal_strength": body.legal_strength,
            "action_steps": body.action_steps,
        }
        result = _get_draft_gen().generate_draft(case_data)
        return DraftResponse(
            complaint_title=result.get("complaint_title", ""),
            draft_text=result.get("draft_text", ""),
            recommended_authority=result.get("recommended_authority", ""),
        )
    except Exception as exc:
        logger.error(f"Draft error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# POST /ai/roadmap
# ---------------------------------------------------------------------------

@router.post("/roadmap")
async def generate_roadmap(body: RoadmapRequest) -> dict:
    """Generate a detailed legal action roadmap."""
    try:
        analysis = {
            "issue_type": body.issue_type,
            "relevant_sections": body.relevant_sections,
            "legal_strength": body.legal_strength,
            "action_steps": body.action_steps,
        }
        return _get_roadmap_gen().generate_roadmap(analysis)
    except Exception as exc:
        logger.error(f"Roadmap error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# POST /ai/enhance
# ---------------------------------------------------------------------------

@router.post("/enhance")
async def enhance_research(body: EnhanceRequest) -> dict:
    """Enhance research results with AI-generated case summaries and analysis."""
    try:
        research_data = {
            "query": body.query,
            "top_cases": body.top_cases,
            "most_influential_case": body.most_influential_case,
        }
        return _get_enhancer().enhance_research(research_data)
    except Exception as exc:
        logger.error(f"Enhance error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
