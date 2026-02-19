"""
Layer 6 — Two-Level Cache.

Level A: Document Cache (keyed by tid)
    Stores enriched case metadata so we don't re-enrich the same doc.

Level B: Query Cache (keyed by normalized query hash)
    Stores ranked search results so repeat queries are instant.

Both levels use TTL-based expiration.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any

from app.config import CACHE_TTL_SECONDS


# ---------------------------------------------------------------------------
# Cache Entry
# ---------------------------------------------------------------------------

@dataclass
class CacheEntry:
    """Single cached value with timestamp."""
    data: Any
    created_at: float = field(default_factory=time.time)

    def is_expired(self, ttl: int = CACHE_TTL_SECONDS) -> bool:
        return (time.time() - self.created_at) > ttl


# ---------------------------------------------------------------------------
# Two-Level Cache
# ---------------------------------------------------------------------------

class LegalCache:
    """In-memory cache with document-level and query-level stores."""

    def __init__(self):
        self._doc_cache: dict[str, CacheEntry] = {}     # key = tid
        self._query_cache: dict[str, CacheEntry] = {}   # key = query hash

    # ---- Document Cache (Level A) ----

    def get_doc(self, tid: str | int) -> Any | None:
        """Retrieve cached document metadata by tid."""
        key = str(tid)
        entry = self._doc_cache.get(key)
        if entry is None or entry.is_expired():
            if entry and entry.is_expired():
                del self._doc_cache[key]
            return None
        return entry.data

    def set_doc(self, tid: str | int, data: Any) -> None:
        """Cache document metadata."""
        self._doc_cache[str(tid)] = CacheEntry(data=data)

    # ---- Query Cache (Level B) ----

    def get_query(self, query: str) -> Any | None:
        """Retrieve cached query results."""
        key = self._hash_query(query)
        entry = self._query_cache.get(key)
        if entry is None or entry.is_expired():
            if entry and entry.is_expired():
                del self._query_cache[key]
            return None
        return entry.data

    def set_query(self, query: str, data: Any) -> None:
        """Cache query results."""
        self._query_cache[self._hash_query(query)] = CacheEntry(data=data)

    # ---- Utilities ----

    def clear(self) -> None:
        """Flush both caches."""
        self._doc_cache.clear()
        self._query_cache.clear()

    @property
    def stats(self) -> dict:
        """Current cache statistics."""
        return {
            "doc_entries": len(self._doc_cache),
            "query_entries": len(self._query_cache),
        }

    @staticmethod
    def _hash_query(query: str) -> str:
        """Deterministic hash for a normalized query string."""
        return hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------

cache = LegalCache()
