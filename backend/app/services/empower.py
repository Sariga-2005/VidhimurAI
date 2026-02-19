"""
Empowerment analysis service — production-grade pipeline.

Pipeline:
    0. Query Normalization  (stopwords, synonyms, domain detection)
    1. Issue Classification (deterministic keyword matching)
    2. Retrieval + Authority Filter + Dual Scoring (empower mode)
    3. Relevant Sections    (statutes from top cases)
    4. Legal Strength       (heuristic from court levels)
    5. Action Roadmap       (deterministic template)
    6. Cache                (store results)
"""

from __future__ import annotations

from app.config import ACTION_ROADMAPS, DEFAULT_ROADMAP, get_authority_tier, AUTHORITY_MIN_HIGH_TIER
from app.models.schemas import CaseRecord, CaseResult, EmpowerResponse
from app.services.ranking import compute_score, tokenize_query
from app.services.query_normalizer import normalize_query
from app.services.kanoon_adapter import get_all_cases
from app.services.cache import cache


# ---------------------------------------------------------------------------
# Issue classification (deterministic keyword matching)
# ---------------------------------------------------------------------------

def _classify_issue(query: str, detected_domain: str) -> str:
    """
    Map a citizen query to the best-matching legal area.

    Uses the domain already detected by the normalizer as the primary signal.
    """
    if detected_domain != "General Legal Issue":
        return detected_domain
    return "General Legal Issue"


# ---------------------------------------------------------------------------
# Authority filter
# ---------------------------------------------------------------------------

def _authority_filter(cases: list[CaseRecord]) -> list[CaseRecord]:
    """Prioritize higher courts."""
    higher = [c for c in cases if get_authority_tier(c.court) <= 2]
    if len(higher) >= AUTHORITY_MIN_HIGH_TIER:
        return higher
    return cases


# ---------------------------------------------------------------------------
# Relevant statutes / sections
# ---------------------------------------------------------------------------

def _collect_relevant_sections(cases: list[CaseRecord]) -> list[str]:
    """De-duplicate statutes from the matched cases."""
    seen: set[str] = set()
    sections: list[str] = []
    for case in cases:
        for s in case.statutes_referenced:
            if s not in seen:
                seen.add(s)
                sections.append(s)
    return sections


# ---------------------------------------------------------------------------
# Legal strength determination
# ---------------------------------------------------------------------------

def _compute_legal_strength(precedents: list[CaseResult]) -> str:
    """Heuristic based on quantity and court levels of precedents."""
    if not precedents:
        return "Weak"

    supreme_count = sum(
        1 for p in precedents
        if get_authority_tier(p.court) == 1
    )
    high_count = sum(
        1 for p in precedents
        if get_authority_tier(p.court) == 2
    )
    total = len(precedents)

    if supreme_count >= 2 or (supreme_count >= 1 and high_count >= 2):
        return "Strong"
    if total >= 3 or supreme_count >= 1 or high_count >= 2:
        return "Moderate"
    return "Weak"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_empowerment(query: str, context: str | None = None) -> EmpowerResponse:
    """
    Full empowerment pipeline:
        normalize → classify → retrieve → filter → rank → assess → roadmap
    """

    # Layer 0: Normalize query
    normalized = normalize_query(query)

    # Check cache
    cache_key = f"empower:{normalized.search_string}"
    cached = cache.get_query(cache_key)
    if cached:
        return cached

    # Layer 1: Classify issue (using normalizer's domain detection)
    issue_type = _classify_issue(query, normalized.detected_domain)

    # Layer 2: Combine query + optional context for relevance matching
    full_query = f"{query} {context}" if context else query
    full_normalized = normalize_query(full_query) if context else normalized
    tokens = full_normalized.expanded_terms or tokenize_query(full_query)

    # Layer 3: Retrieve + authority filter + dual scoring (empower mode)
    all_cases = _authority_filter(get_all_cases())
    scored: list[tuple[CaseRecord, float, dict]] = []
    for case in all_cases:
        score, breakdown = compute_score(case, tokens, mode="empower")
        scored.append((case, score, breakdown))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Keep top-5 as precedents
    top_precedents: list[CaseResult] = []
    top_records: list[CaseRecord] = []
    for case, score, bd in scored[:5]:
        top_precedents.append(CaseResult(
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
        top_records.append(case)

    # Layer 4: Relevant sections
    relevant_sections = _collect_relevant_sections(top_records)

    # Layer 5: Legal strength
    legal_strength = _compute_legal_strength(top_precedents)

    # Layer 6: Action roadmap (deterministic template)
    roadmap_entries = ACTION_ROADMAPS.get(issue_type, DEFAULT_ROADMAP)
    action_steps = [
        f"Step {e['step']}: {e['title']} \u2014 {e['description']}"
        for e in roadmap_entries
    ]

    response = EmpowerResponse(
        issue_type=issue_type,
        relevant_sections=relevant_sections,
        precedents=top_precedents,
        legal_strength=legal_strength,
        action_steps=action_steps,
    )

    # Cache the result
    cache.set_query(cache_key, response)

    return response
