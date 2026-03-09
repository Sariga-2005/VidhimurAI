"""
TF-IDF vector index for case retrieval.

Replaces manual token-overlap scoring with proper TF-IDF cosine similarity.
Key design decisions:
  - ngram_range=(1, 2): bigrams captured natively ("sexual harassment",
    "security deposit", "wrongful termination" all become single features).
  - sublinear_tf=True: log-dampens term frequency automatically — no need
    for hand-tuned weights like the old system's weight=0.1 for "job".
  - Field boosting via repetition: keywords and legal_issues are repeated
    in the corpus document so they outweigh noisy summary text.
  - The fitted vectorizer is reused at query time — terms unseen during
    fitting get zero weight, which is correct behaviour.
"""

from __future__ import annotations

import logging
import math

import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _cosine_similarity
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

from app.models.schemas import CaseRecord
from app.config import get_court_weight, CURRENT_YEAR, RECENCY_DECAY_RATE, RECENCY_MAX_BOOST

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Authority scoring helpers (kept here so empower.py has one import)
# ---------------------------------------------------------------------------

def compute_authority_score(case: CaseRecord) -> float:
    """Court-weight + log-citation score (same formula as old ranking.py)."""
    court_w = get_court_weight(case.court)
    citation_s = math.log1p(case.citation_count) * 2
    return round((court_w * 3) + citation_s, 2)


def compute_recency_boost(case: CaseRecord) -> float:
    age = CURRENT_YEAR - case.year
    boost = RECENCY_MAX_BOOST - (age * RECENCY_DECAY_RATE)
    return round(max(0.0, boost), 2)


# approx upper bound for authority: Supreme Court (10*3=30) + log(10000)*2 ≈ 43
_MAX_AUTHORITY = 45.0


def _authority_bonus(authority_score: float) -> float:
    """Normalize authority to a [0, 0.25] bonus.

    This keeps TF-IDF as the PRIMARY ranking signal.  A Supreme Court
    landmark case gets at most a 0.25 bonus on top of its TF-IDF score —
    enough to break ties between equally relevant cases, not enough to
    override irrelevant high-citation cases.
    """
    normalised = min(authority_score / _MAX_AUTHORITY, 1.0)
    return round(normalised * 0.25, 4)


# ---------------------------------------------------------------------------
# TF-IDF Index
# ---------------------------------------------------------------------------

class TFIDFIndex:
    """
    Builds a TF-IDF matrix at startup and answers cosine-similarity queries.

    Usage
    -----
        index = TFIDFIndex()
        index.build(all_cases)
        results = index.search("sexual harassment at workplace", top_n=20)
        # → [(CaseRecord, tfidf_score), ...] sorted descending
    """

    def __init__(self) -> None:
        self._cases: list[CaseRecord] = []
        self._matrix = None       # sparse (n_cases × n_features)
        self._vectorizer: TfidfVectorizer | None = None
        self._built = False

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, cases: list[CaseRecord]) -> None:
        """Fit the vectorizer on the case corpus and store the TF-IDF matrix."""
        if not _SKLEARN_AVAILABLE:
            logger.error(
                "scikit-learn is not installed. Install it with: pip install scikit-learn"
            )
            return

        self._cases = cases
        corpus = [self._to_document(c) for c in cases]

        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),   # unigrams + bigrams
            min_df=1,             # keep even rare legal terms
            max_df=0.90,          # drop tokens present in >90% of cases (stop-like)
            sublinear_tf=True,    # log(1 + tf) — automatic frequency dampening
            strip_accents="unicode",
            lowercase=True,
        )
        self._matrix = self._vectorizer.fit_transform(corpus)
        self._built = True
        logger.info(
            f"TF-IDF index built: {len(cases)} cases, "
            f"{self._matrix.shape[1]} features"
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_n: int = 50,
        min_score: float = 0.01,
    ) -> list[tuple[CaseRecord, float, dict]]:
        """
        Return top-n cases scored by TF-IDF cosine similarity.

        Returns
        -------
        list of (CaseRecord, tfidf_score, breakdown_dict)
        """
        if not self._built or self._vectorizer is None:
            logger.warning("TF-IDF index not built — returning empty results.")
            return []

        qvec = self._vectorizer.transform([query])
        raw_scores: np.ndarray = _cosine_similarity(qvec, self._matrix)[0]

        top_indices = np.argsort(raw_scores)[::-1][:top_n]

        results = []
        for idx in top_indices:
            tfidf_score = float(raw_scores[idx])
            if tfidf_score < min_score:
                break   # sorted descending — everything after is also below threshold

            case = self._cases[idx]
            authority = compute_authority_score(case)
            recency   = compute_recency_boost(case)

            # Final score = TF-IDF (primary) + small normalised authority bonus.
            # Authority is capped at 0.25 so a hacking case with 1000 citations
            # cannot outrank a relevant property case just because it's famous.
            bonus = _authority_bonus(authority)
            final = tfidf_score + (tfidf_score * bonus)

            breakdown = {
                "tfidf_score":     round(tfidf_score, 4),
                "authority_score": round(authority, 2),
                "authority_bonus": round(bonus, 4),
                "relevance_score": round(tfidf_score * 100, 2),  # ×100 for UI compat
                "recency_boost":   round(recency, 2),
                "final_score":     round(final, 4),
            }
            results.append((case, final, breakdown))

        # Sort by TF-IDF score (primary) so relevance always dominates.
        # The small authority bonus only breaks exact ties.
        results.sort(key=lambda x: x[2]["tfidf_score"], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Internal: document builder
    # ------------------------------------------------------------------

    def _to_document(self, case: CaseRecord) -> str:
        """
        Build a single searchable text document per case.

        Field boosting via repetition:
          - keywords and legal_issues appear twice → higher TF contribution
          - case_name appears once (already specific)
          - summary once (may contain noise)
        """
        parts = [
            case.case_name or "",
            # boost structured fields
            " ".join(case.keywords),
            " ".join(case.keywords),           # ×2
            " ".join(case.legal_issues),
            " ".join(case.legal_issues),       # ×2
            " ".join(case.statutes_referenced),
            case.summary or "",
        ]
        return " ".join(p for p in parts if p).strip()

    # ------------------------------------------------------------------
    # Rebuild (call when cases change at runtime)
    # ------------------------------------------------------------------

    def rebuild(self, cases: list[CaseRecord]) -> None:
        """Teardown existing index and build a fresh one."""
        self._built = False
        self._cases = []
        self._matrix = None
        self._vectorizer = None
        self.build(cases)


# ---------------------------------------------------------------------------
# Module-level singleton — imported by empower.py
# ---------------------------------------------------------------------------

_index: TFIDFIndex | None = None


def get_index() -> TFIDFIndex:
    """Return the module-level singleton (creates it if it doesn't exist yet)."""
    global _index
    if _index is None:
        _index = TFIDFIndex()
    return _index


def build_index(cases: list[CaseRecord]) -> TFIDFIndex:
    """Build (or rebuild) the singleton index from the given case list."""
    idx = get_index()
    idx.build(cases)
    return idx
