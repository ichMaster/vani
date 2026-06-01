"""The state repository: the single access point to persisted documents.

Every layer reads and writes state through this interface; no layer knows
whether JSON or Mongo sits beneath it (architecture §4, §10). `json_store`
backs it through v2 P1; `mongo_store` takes over at v2 P2.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# A persisted document is a plain JSON-serializable mapping.
Document = dict[str, Any]


class Repository(ABC):
    """Single-point access to persisted documents, keyed by (doc_type, doc_id)."""

    @abstractmethod
    def save(self, doc_type: str, doc_id: str, data: Document) -> None:
        """Persist `data` under (doc_type, doc_id), overwriting any existing document."""

    @abstractmethod
    def load(self, doc_type: str, doc_id: str) -> Document | None:
        """Return the document at (doc_type, doc_id), or None if it does not exist."""

    @abstractmethod
    def list_ids(self, doc_type: str) -> list[str]:
        """Return the ids of all documents of `doc_type` (sorted)."""

    @abstractmethod
    def delete(self, doc_type: str, doc_id: str) -> bool:
        """Delete the document; return True if it existed, False otherwise."""
