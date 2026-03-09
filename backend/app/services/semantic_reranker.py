"""
Semantic re-ranker using sentence-transformers.

Role in the pipeline:
    TF-IDF retrieves a candidate set (fast, lexical).
    This re-ranker refines that set by cosine similarity of sentence embeddings
    (slow per query, but only runs on ~50 candidates, not 500 cases).

Design decisions:
  - Model: all-MiniLM-L6-v2 (80MB, MIT, CPU-friendly, ~50ms for 50 candidates)
  - Embeddings for all cases are computed once at startup and persisted to disk
    so cold-start after the first run is instant.
  - Graceful degradation: if the model is unavailable (download failed, no
    internet on first run), returns the TF-IDF ranking unchanged.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"
_DATA_DIR   = Path(__file__).resolve().parent.parent / "data"
_EMBED_FILE = _DATA_DIR / "embeddings.npy"
_INDEX_FILE = _DATA_DIR / "embeddings_index.json"   # maps position → kanoon_tid

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False
    logger.warning("sentence-transformers not installed — semantic re-ranking disabled.")


# ---------------------------------------------------------------------------
# Cosine similarity helper (pure numpy, no sklearn dep for this module)
# ---------------------------------------------------------------------------

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Row-wise cosine similarity between a (1, d) query and b (n, d) matrix."""
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return (a_norm @ b_norm.T).squeeze(0)


# ---------------------------------------------------------------------------
# SemanticReranker
# ---------------------------------------------------------------------------

class SemanticReranker:
    """
    Encodes legal case documents into dense vectors at startup.
    At query time, re-orders a TF-IDF candidate list by semantic similarity.

    Usage
    -----
        reranker = SemanticReranker()
        reranker.build(all_cases)                        # once at startup
        ranked = reranker.rerank(query, tfidf_results)   # per request
    """

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None
        self._embeddings: np.ndarray | None = None   # shape (n_cases, 384)
        self._tid_to_idx: dict[int, int] = {}
        self._built = False

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, cases) -> None:  # cases: list[CaseRecord]
        """Encode all cases. Load from disk if already cached, else compute."""
        if not _ST_AVAILABLE:
            return

        # Load model
        try:
            self._model = SentenceTransformer(_MODEL_NAME)
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}")
            return

        # Try loading existing embeddings from disk
        if _EMBED_FILE.exists() and _INDEX_FILE.exists():
            try:
                saved_index: list[int] = json.loads(_INDEX_FILE.read_text())
                saved_tids  = set(saved_index)
                case_tids   = {c.kanoon_tid for c in cases}

                if saved_tids == case_tids:
                    self._embeddings = np.load(str(_EMBED_FILE))
                    self._tid_to_idx = {tid: i for i, tid in enumerate(saved_index)}
                    self._built = True
                    logger.info(
                        f"Semantic re-ranker loaded from disk "
                        f"({len(cases)} cases, dim={self._embeddings.shape[1]})"
                    )
                    return
                else:
                    logger.info("Case set changed — recomputing embeddings.")
            except Exception as e:
                logger.warning(f"Failed to load cached embeddings: {e} — recomputing.")

        # Compute embeddings
        logger.info(f"Computing sentence embeddings for {len(cases)} cases...")
        docs = [self._to_document(c) for c in cases]
        self._embeddings = self._model.encode(
            docs,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2-normalised → dot product = cosine sim
        )

        # Save to disk
        try:
            np.save(str(_EMBED_FILE), self._embeddings)
            ordered_tids = [c.kanoon_tid for c in cases]
            _INDEX_FILE.write_text(json.dumps(ordered_tids))
            logger.info(f"Embeddings saved to {_EMBED_FILE}")
        except Exception as e:
            logger.warning(f"Could not save embeddings to disk: {e}")

        self._tid_to_idx = {c.kanoon_tid: i for i, c in enumerate(cases)}
        self._built = True
        logger.info(
            f"Semantic re-ranker ready "
            f"({len(cases)} cases, dim={self._embeddings.shape[1]})"
        )

    # ------------------------------------------------------------------
    # Re-rank
    # ------------------------------------------------------------------

    def rerank(
        self,
        query: str,
        candidates: list[tuple],   # list of (CaseRecord, score, breakdown)
        top_n: int | None = None,
    ) -> list[tuple]:
        """
        Re-order candidates by semantic similarity to query.

        If the model is unavailable or a candidate has no embedding,
        those candidates are left in TF-IDF order (graceful degradation).

        Parameters
        ----------
        query      : raw user query string
        candidates : output of TFIDFIndex.search()
        top_n      : if set, return only the top-n after re-ranking

        Returns
        -------
        list of (CaseRecord, combined_score, breakdown) — sorted by semantic sim
        """
        if not self._built or self._model is None or self._embeddings is None:
            return candidates[:top_n] if top_n else candidates

        if not candidates:
            return candidates

        # Encode query (normalized)
        q_vec = self._model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )  # shape (1, 384)

        # Gather embeddings for candidates (skip any without an embedding)
        valid, missing = [], []
        for item in candidates:
            case = item[0]
            idx  = self._tid_to_idx.get(case.kanoon_tid)
            if idx is not None:
                valid.append((item, idx))
            else:
                missing.append(item)

        if not valid:
            return candidates[:top_n] if top_n else candidates

        indices  = [idx for _, idx in valid]
        c_matrix = self._embeddings[indices]          # (n_valid, 384)
        sem_scores = (q_vec @ c_matrix.T).squeeze(0)  # dot = cosine (L2-normed)

        # Combine: 70% semantic + 30% TF-IDF (research values authority, empower values relevance)
        ranked = []
        for i, (item, _) in enumerate(valid):
            case, tfidf_final, bd = item
            tfidf_raw = bd.get("tfidf_score", 0.0)
            sem        = float(sem_scores[i])
            combined   = 0.70 * sem + 0.30 * tfidf_raw
            new_bd = {**bd, "semantic_score": round(sem, 4), "combined_score": round(combined, 4)}
            ranked.append((case, combined, new_bd))

        ranked.sort(key=lambda x: x[1], reverse=True)
        result = ranked + missing   # append any un-embeddable cases at the end

        return result[:top_n] if top_n else result

    # ------------------------------------------------------------------
    # Document builder (same field-boosting as TF-IDF)
    # ------------------------------------------------------------------

    def _to_document(self, case) -> str:  # case: CaseRecord
        parts = [
            case.case_name or "",
            " ".join(case.keywords) * 2,
            " ".join(case.legal_issues) * 2,
            " ".join(case.statutes_referenced),
            case.summary or "",
        ]
        return " ".join(p for p in parts if p).strip() or "unknown legal case"

    def rebuild(self, cases) -> None:
        """Force recompute (e.g. after dataset update)."""
        self._built = False
        self._embeddings = None
        self._tid_to_idx = {}
        self._model = None
        self.build(cases)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_reranker: SemanticReranker | None = None


def get_reranker() -> SemanticReranker:
    global _reranker
    if _reranker is None:
        _reranker = SemanticReranker()
    return _reranker


def build_reranker(cases) -> SemanticReranker:
    r = get_reranker()
    r.build(cases)
    return r
