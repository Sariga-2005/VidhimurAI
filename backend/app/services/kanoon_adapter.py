"""
Adapter layer for Indian Kanoon Data.

responsibilities:
1. Define the internal schema for Indian Kanoon API responses (KanoonDoc).
2. Load data from the mock JSON (or live API in future).
3. Map KanoonDoc objects to our internal CaseRecord domain model.
"""

from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from app.config import KANOON_CASES_FILE
from app.models.schemas import CaseRecord


# ---------------------------------------------------------------------------
# Indian Kanoon API Schemas
# ---------------------------------------------------------------------------

class VidhimurEnrichment(BaseModel):
    """Our internal enrichment data (keywords, issues, etc.) not provided by Kanoon."""
    keywords: list[str] = Field(default_factory=list)
    outcome: str = ""
    legal_issues: list[str] = Field(default_factory=list)
    statutes_referenced: list[str] = Field(default_factory=list)
    precedents_cited: list[str] = Field(default_factory=list)


class KanoonDocRef(BaseModel):
    """Reference to another doc (citeList item)."""
    tid: int
    title: str


class KanoonDoc(BaseModel):
    """Matches the shape of a single document from Indian Kanoon's API."""
    tid: int
    title: str
    headline: str | None = None
    docsource: str
    docsize: int
    publishdate: str  # Format: DD-MM-YYYY
    numcites: int
    numcitedby: int
    catname: str
    citeList: list[KanoonDocRef] = Field(default_factory=list)
    citedbyList: list[KanoonDocRef] = Field(default_factory=list)

    # Enrichment block (Vidhimur specific)
    vidhimur: VidhimurEnrichment = Field(default_factory=VidhimurEnrichment, alias="_vidhimur")


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_kanoon_docs(path: str | None = None) -> list[KanoonDoc]:
    """Load raw Kanoon docs from local JSON simulation."""
    file_path = Path(path) if path else KANOON_CASES_FILE
    
    if not file_path.exists():
        # Fallback for now if config isn't updated or file missing
        raise FileNotFoundError(f"Kanoon dataset not found at {file_path}")

    with open(file_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    return [KanoonDoc(**doc) for doc in raw_data]


# ---------------------------------------------------------------------------
# Mapper (Adapter Logic)
# ---------------------------------------------------------------------------

def kanoon_to_case_record(doc: KanoonDoc) -> CaseRecord:
    """
    Convert a KanoonDoc (external API shape) to CaseRecord (internal domain model).
    
    Mapping Strategy:
    - ID: Generated from TID (e.g. "CASE-{tid}")
    - Court: docsource
    - Year: Extracted from publishdate
    - Summary: headline + outcome (since headline is just a snippet)
    - Citations: numcitedby
    - Enrichment: direct copy from _vidhimur
    """
    
    # Parse year from DD-MM-YYYY
    try:
        year = int(doc.publishdate.split("-")[-1])
    except (IndexError, ValueError):
        year = 0  # Fallback
        
    case_summary = doc.headline or ""
    if doc.vidhimur.outcome:
        case_summary += f" Outcome: {doc.vidhimur.outcome}"

    return CaseRecord(
        id=f"CASE-{doc.tid}",
        kanoon_tid=doc.tid,
        case_name=doc.title,
        court=doc.docsource,
        year=year,
        citation_count=doc.numcitedby,
        summary=case_summary,
        keywords=doc.vidhimur.keywords,
        outcome=doc.vidhimur.outcome,
        legal_issues=doc.vidhimur.legal_issues,
        statutes_referenced=doc.vidhimur.statutes_referenced,
        precedents_cited=doc.vidhimur.precedents_cited or [c.title for c in doc.citeList]
    )


def get_all_cases() -> list[CaseRecord]:
    """
    Public accessor used by Search/Empower services.
    Fetches raw Kanoon docs and adapts them to CaseRecords.
    """
    raw_docs = load_kanoon_docs()
    return [kanoon_to_case_record(doc) for doc in raw_docs]
