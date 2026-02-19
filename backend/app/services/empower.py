"""Empowerment analysis service — deterministic issue classification and precedent matching."""

from __future__ import annotations

from app.config import ACTION_ROADMAPS, DEFAULT_ROADMAP, ISSUE_KEYWORDS
from app.models.schemas import CaseRecord, CaseResult, EmpowerResponse
from app.services.ranking import compute_score, tokenize_query
from app.services.kanoon_adapter import get_all_cases


# ---------------------------------------------------------------------------
# Issue classification (deterministic keyword matching)
# ---------------------------------------------------------------------------

def _classify_issue(query: str) -> str:
    """Map a citizen query to the best-matching legal area."""
    query_lower = query.lower()
    scores: dict[str, int] = {}

    for area, keywords in ISSUE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[area] = score

    if not scores:
        return "General Legal Issue"

    return max(scores, key=scores.get)  # type: ignore[arg-type]


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

    supreme_count = sum(1 for p in precedents if p.court == "Supreme Court")
    high_count = sum(1 for p in precedents if p.court == "High Court")
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
    """Full empowerment pipeline: classify → find precedents → assess strength → roadmap."""

    # 1. Classify issue
    issue_type = _classify_issue(query)

    # 2. Combine query + optional context for relevance matching
    full_query = f"{query} {context}" if context else query
    tokens = tokenize_query(full_query)

    # 3. Score all cases and pick relevant ones
    all_cases = get_all_cases()
    scored: list[tuple[CaseRecord, float]] = []
    for case in all_cases:
        score, _ = compute_score(case, tokens)
        scored.append((case, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Keep top-5 as precedents
    top_precedents: list[CaseResult] = []
    top_records: list[CaseRecord] = []
    for case, score in scored[:5]:
        top_precedents.append(CaseResult(
            kanoon_tid=case.kanoon_tid,
            case_name=case.case_name,
            court=case.court,
            year=case.year,
            citation_count=case.citation_count,
            strength_score=score,
            summary=case.summary,
        ))
        top_records.append(case)

    # 4. Relevant sections
    relevant_sections = _collect_relevant_sections(top_records)

    # 5. Legal strength
    legal_strength = _compute_legal_strength(top_precedents)

    # 6. Action roadmap (flattened to list of strings for the contract)
    roadmap_entries = ACTION_ROADMAPS.get(issue_type, DEFAULT_ROADMAP)
    action_steps = [f"Step {e['step']}: {e['title']} — {e['description']}" for e in roadmap_entries]

    return EmpowerResponse(
        issue_type=issue_type,
        relevant_sections=relevant_sections,
        precedents=top_precedents,
        legal_strength=legal_strength,
        action_steps=action_steps,
    )
