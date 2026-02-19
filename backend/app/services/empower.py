"""
Empowerment analysis service — production-grade pipeline.

Pipeline:
    0. Query Normalization  (stopwords, synonyms, domain detection)
    1. Issue Classification (deterministic keyword matching + sub-classification)
    2. Retrieval + Dual Scoring (empower mode)
    3. Case Exclusion       (remove irrelevant cases by summary keywords)
    4. Relevance Threshold  (discard cases below RELEVANCE_THRESHOLD)
    5. Relevant Sections    (statutes from top cases, blacklist-filtered)
    6. Legal Strength       (heuristic from court levels)
    7. Action Roadmap       (deterministic template)
    8. Cache                (store results)
"""

from __future__ import annotations

from app.config import (
    ACTION_ROADMAPS,
    DEFAULT_ROADMAP,
    get_authority_tier,
    PROPERTY_SUBCATEGORIES,
    RELEVANCE_THRESHOLD,
    STATUTE_BLACKLIST_PATTERNS,
    CASE_EXCLUSION_KEYWORDS,
)
from app.models.schemas import CaseRecord, CaseResult, EmpowerResponse
from app.services.ranking import compute_score, tokenize_query
from app.services.query_normalizer import normalize_query
from app.services.kanoon_adapter import get_all_cases
from app.services.cache import cache


# ---------------------------------------------------------------------------
# Issue classification (deterministic keyword matching + sub-classification)
# ---------------------------------------------------------------------------

def _classify_issue(query: str, detected_domain: str) -> str:
    """
    Map a citizen query to the best-matching legal area.

    If the broad domain is Property Law, refine to a precise sub-category
    (e.g., "Security Deposit Recovery", "Tenancy Dispute").
    """
    if detected_domain == "Property Law":
        return _refine_property_issue(query)
    if detected_domain != "General Legal Issue":
        return detected_domain
    return "General Legal Issue"


def _refine_property_issue(query: str) -> str:
    """Refine a Property Law classification to a precise sub-category.

    Uses weighted scoring: multi-word phrase matches score 3 points,
    single-word matches score 1. This ensures 'Security Deposit Recovery'
    beats 'Tenancy Dispute' when the user mentions 'deposit'.
    """
    q = query.lower()
    best_match = "Property Law"
    best_score = 0
    for subcategory, keywords in PROPERTY_SUBCATEGORIES.items():
        score = 0
        for kw in keywords:
            if kw in q:
                score += 3 if " " in kw else 1
        if score > best_score:
            best_score = score
            best_match = subcategory
    return best_match


# ---------------------------------------------------------------------------
# Case exclusion filter
# ---------------------------------------------------------------------------

def _exclude_irrelevant_cases(
    scored: list[tuple[CaseRecord, float, dict]],
) -> list[tuple[CaseRecord, float, dict]]:
    """Remove cases whose summary contains exclusion keywords (terrorism, habeas corpus, etc.)."""
    filtered = []
    for case, score, bd in scored:
        summary_lower = case.summary.lower()
        case_name_lower = case.case_name.lower()
        blob = summary_lower + " " + case_name_lower
        excluded = any(kw in blob for kw in CASE_EXCLUSION_KEYWORDS)
        if not excluded:
            filtered.append((case, score, bd))
    return filtered


# ---------------------------------------------------------------------------
# Relevance threshold filter
# ---------------------------------------------------------------------------

def _apply_relevance_threshold(
    scored: list[tuple[CaseRecord, float, dict]],
) -> list[tuple[CaseRecord, float, dict]]:
    """Discard cases with relevance_score below RELEVANCE_THRESHOLD."""
    return [
        (case, score, bd)
        for case, score, bd in scored
        if bd.get("relevance_score", 0.0) >= RELEVANCE_THRESHOLD
    ]


# ---------------------------------------------------------------------------
# Relevant statutes / sections (blacklist-filtered)
# ---------------------------------------------------------------------------

def _collect_relevant_sections(cases: list[CaseRecord]) -> list[str]:
    """De-duplicate statutes from the matched cases, excluding blacklisted patterns."""
    seen: set[str] = set()
    sections: list[str] = []
    for case in cases:
        for s in case.statutes_referenced:
            s_lower = s.lower()
            if any(bl in s_lower for bl in STATUTE_BLACKLIST_PATTERNS):
                continue
            if s not in seen:
                seen.add(s)
                sections.append(s)
    return sections


# ---------------------------------------------------------------------------
# Legal strength determination
# ---------------------------------------------------------------------------

def _compute_legal_strength(precedents: list[CaseResult]) -> str:
    """Heuristic based on quantity and court levels of precedents.

    Conservative — only returns 'Strong' if facts clearly support it.
    """
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

    # Layer 1: Classify issue (using normalizer's domain detection + sub-classification)
    issue_type = _classify_issue(query, normalized.detected_domain)

    # Layer 2: Combine query + optional context for relevance matching
    full_query = f"{query} {context}" if context else query
    full_normalized = normalize_query(full_query) if context else normalized
    tokens = full_normalized.expanded_terms or tokenize_query(full_query)

    # Layer 3: Retrieve + dual scoring (empower mode, no authority pre-filter)
    all_cases = get_all_cases()
    scored: list[tuple[CaseRecord, float, dict]] = []
    for case in all_cases:
        score, breakdown = compute_score(case, tokens, mode="empower")
        scored.append((case, score, breakdown))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Layer 4: Case Exclusion — remove terrorism, habeas corpus, PIL, etc.
    scored = _exclude_irrelevant_cases(scored)

    # Layer 5: Relevance Threshold — discard low-relevance cases
    scored = _apply_relevance_threshold(scored)

    # Keep top-5 as precedents (may be fewer if filtering removed cases)
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

    # Layer 6: Relevant sections (blacklist-filtered)
    relevant_sections = _collect_relevant_sections(top_records)

    # Layer 7: Legal strength
    legal_strength = _compute_legal_strength(top_precedents)

    # Layer 8: Action roadmap (deterministic template)
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
