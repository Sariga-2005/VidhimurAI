"""
Empowerment analysis service — TF-IDF + Semantic Re-ranking pipeline.

Pipeline:
    0. Query Normalization  (stopwords, synonyms, domain detection)
    1. Issue Classification (deterministic keyword matching + sub-classification)
    2. TF-IDF Retrieval     (cosine similarity over enriched case corpus)
    3. Case Exclusion       (remove irrelevant cases by summary keywords)
    4. Semantic Re-rank     (sentence-transformer re-orders top candidates)
    5. Relevant Sections    (statutes from top cases, blacklist-filtered)
    6. Legal Strength       (heuristic from TF-IDF score + court levels)
    7. Action Roadmap       (deterministic template)
    8. Cache                (store results)
"""

from __future__ import annotations

import hashlib
import logging

from app.config import (
    ACTION_ROADMAPS,
    DEFAULT_ROADMAP,
    get_authority_tier,
    PROPERTY_SUBCATEGORIES,
    STATUTE_BLACKLIST_PATTERNS,
    CASE_EXCLUSION_KEYWORDS,
)
from app.models.schemas import CaseRecord, CaseResult, EmpowerResponse
from app.services.tfidf_index import build_index, get_index
from app.services.semantic_reranker import build_reranker, get_reranker
from app.services.query_normalizer import normalize_query
from app.services.kanoon_adapter import get_all_cases
from app.services.cache import cache

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Index lifecycle — built once at first use, rebuilt if new cases are loaded
# ---------------------------------------------------------------------------

_index_built = False


def _ensure_index() -> None:
    """Build TF-IDF index + semantic re-ranker if not yet done."""
    global _index_built
    if not _index_built:
        all_cases = get_all_cases()
        build_index(all_cases)
        build_reranker(all_cases)   # loads from disk if already computed
        _index_built = True
        logger.info(f"Empower index + re-ranker ready for {len(all_cases)} cases.")


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
    """Refine a Property Law classification to a precise sub-category."""
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
    """Remove cases whose summary contains exclusion keywords."""
    filtered = []
    for case, score, bd in scored:
        blob = case.summary.lower() + " " + case.case_name.lower()
        excluded = any(kw in blob for kw in CASE_EXCLUSION_KEYWORDS)
        if not excluded:
            filtered.append((case, score, bd))
    return filtered


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
# Legal strength determination (TF-IDF scale: scores in [0, 1])
# ---------------------------------------------------------------------------

def _compute_legal_strength(precedents: list[CaseResult]) -> str:
    """
    Heuristic based on TF-IDF relevance (0–1 scale) and court authority.

    Thresholds are tuned for cosine similarity output:
      Strong   : avg_tfidf > 0.15 AND ≥1 Supreme Court OR ≥2 High Court cases
      Moderate : avg_tfidf > 0.04
      Weak     : everything else
    """
    if not precedents:
        return "Weak"

    # relevance_score is stored ×100 for UI compat, so divide back
    avg_tfidf = sum(p.relevance_score / 100.0 for p in precedents) / len(precedents)

    supreme_count = sum(1 for p in precedents if get_authority_tier(p.court) == 1)
    high_count    = sum(1 for p in precedents if get_authority_tier(p.court) == 2)

    if avg_tfidf > 0.15 and (supreme_count >= 1 or high_count >= 2):
        return "Strong"
    if avg_tfidf > 0.04:
        return "Moderate"
    return "Weak"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_empowerment(query: str, context: str | None = None) -> EmpowerResponse:
    """
    Full empowerment pipeline:
        normalize → classify → TF-IDF retrieve → exclude → authority re-rank → assess → roadmap
    """

    # Layer 0: Normalize query
    normalized = normalize_query(query)

    # Check cache
    context_hash = hashlib.md5(context.encode("utf-8")).hexdigest()[:8] if context else "no_ctx"
    cache_key = f"empower_tfidf:{normalized.search_string}:{context_hash}"
    cached = cache.get_query(cache_key)
    if cached:
        return cached

    # Layer 1: Classify issue
    issue_type = _classify_issue(query, normalized.detected_domain)

    # Layer 2: Build full search string (query + context + expanded terms)
    full_query_parts = [query]
    if context:
        full_query_parts.append(context)
    # Append expanded terms from the normalizer (synonyms etc.) to the search string
    full_query_parts.extend(normalized.expanded_terms)
    search_string = " ".join(full_query_parts)

    # Layer 3: TF-IDF retrieval
    _ensure_index()
    index = get_index()
    scored = index.search(search_string, top_n=50, min_score=0.01)

    # Layer 4: Case exclusion (terrorism, habeas corpus, etc.)
    scored = _exclude_irrelevant_cases(scored)

    # Layer 4a: Semantic re-rank — refine ordering with sentence embeddings.
    # Re-ranker uses 70% semantic similarity + 30% TF-IDF on top 20 candidates.
    # Falls back to TF-IDF order gracefully if model unavailable.
    reranker = get_reranker()
    scored = reranker.rerank(query, scored, top_n=20)

    # Keep top-5 as precedents — only cases with a real TF-IDF match
    top_precedents: list[CaseResult] = []
    top_records: list[CaseRecord] = []
    for case, score, bd in scored[:5]:
        # Skip zero-score cases — they dilute strength calculation
        if bd.get("tfidf_score", 0.0) < 0.01:
            continue
        top_precedents.append(CaseResult(
            kanoon_tid=case.kanoon_tid,
            case_name=case.case_name,
            court=case.court,
            year=case.year,
            citation_count=case.citation_count,
            strength_score=round(score, 4),
            authority_score=bd.get("authority_score", 0.0),
            relevance_score=bd.get("relevance_score", 0.0),
            summary=case.summary,
        ))
        top_records.append(case)
        if len(top_precedents) == 5:
            break

    # Layer 5: Relevant sections
    relevant_sections = _collect_relevant_sections(top_records)

    # Layer 6: Legal strength
    legal_strength = _compute_legal_strength(top_precedents)

    # Layer 7: Confidence gating
    # (a) If TF-IDF found nothing meaningful, revert to General inquiry
    avg_tfidf = (
        sum(p.relevance_score / 100.0 for p in top_precedents) / len(top_precedents)
        if top_precedents else 0.0
    )
    if avg_tfidf < 0.02:
        legal_strength = "Weak"

    # (b) General Legal Issue should never be Moderate/Strong —
    #     if we classified as General (vague query, no legal vocabulary),
    #     cap strength at Weak regardless of incidental TF-IDF matches.
    if issue_type == "General Legal Issue":
        legal_strength = "Weak"

    # Layer 8: Action roadmap
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

    cache.set_query(cache_key, response)
    return response
