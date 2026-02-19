"""Pydantic models for the case data and API request / response contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
#  Internal case representation (matches cases.json)
# ═══════════════════════════════════════════════════════════════════════════

class CaseRecord(BaseModel):
    """Raw case as stored in the local JSON dataset."""

    id: str
    kanoon_tid: int | None = None
    case_name: str
    court: str
    year: int
    citation_count: int
    summary: str
    keywords: list[str] = Field(default_factory=list)
    outcome: str = ""
    legal_issues: list[str] = Field(default_factory=list)
    statutes_referenced: list[str] = Field(default_factory=list)
    precedents_cited: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
#  Request schemas
# ═══════════════════════════════════════════════════════════════════════════

class SearchFilters(BaseModel):
    court: str | None = None
    year_start: int | None = None
    year_end: int | None = None


class SearchRequest(BaseModel):
    """POST /research/search"""

    query: str = Field(..., min_length=1, description="Legal search query")
    filters: SearchFilters | None = None
    lang: str = Field(default="en", description="UI language code for translation")


class EmpowerRequest(BaseModel):
    """POST /empower/analyze"""

    query: str = Field(..., min_length=1, description="Citizen's legal issue description")
    context: str | None = None
    lang: str = Field(default="en", description="UI language code for translation")


# ═══════════════════════════════════════════════════════════════════════════
#  Response schemas  — STRICT CONTRACT (provided by team lead)
# ═══════════════════════════════════════════════════════════════════════════

# ---------- Research Mode ----------

class CaseResult(BaseModel):
    """Single case in the research results."""

    kanoon_tid: int | None = None
    case_name: str
    court: str
    year: int
    citation_count: int
    strength_score: float
    authority_score: float = 0.0
    relevance_score: float = 0.0
    summary: str


class SearchResponse(BaseModel):
    """POST /research/search  → response body"""

    total_cases: int
    top_cases: list[CaseResult]
    most_influential_case: CaseResult | None = None


# ---------- Empower Mode ----------

class EmpowerResponse(BaseModel):
    """POST /empower/analyze  → response body"""

    issue_type: str
    relevant_sections: list[str]
    precedents: list[CaseResult]
    legal_strength: str            # "Strong" | "Moderate" | "Weak"
    action_steps: list[str]
