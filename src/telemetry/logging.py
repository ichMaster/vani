"""Structured logging and a telemetry sink (scaffolding for v1 P1).

Provides a configurable logger and a repository-backed telemetry sink that
later phases append per-turn records to (telemetry.schema.json). Sensitive
fields are redacted before anything is written (refinement #1). No metrics are
computed here — that begins at v1 P1.
"""

from __future__ import annotations

import logging
from typing import Any

from src.contracts.documents import Document
from src.state.repository import Repository

# Keys whose values must never reach telemetry (message text, birth data, secrets).
SENSITIVE_KEYS = frozenset({"text", "message", "content", "birth_data", "anthropic_api_key"})

REDACTED = "[redacted]"


def get_logger(name: str = "vani", level: str = "INFO") -> logging.Logger:
    """Return a configured structured logger at the given level."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(level.upper())
    return logger


def redact(value: Any, sensitive_keys: frozenset[str] = SENSITIVE_KEYS) -> Any:
    """Recursively replace sensitive values with a redaction marker."""
    if isinstance(value, dict):
        return {
            key: (REDACTED if key in sensitive_keys else redact(val, sensitive_keys))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [redact(item, sensitive_keys) for item in value]
    return value


class TelemetrySink:
    """Append-only per-turn telemetry, stored via the repository (telemetry.schema.json)."""

    DOC_TYPE = "telemetry"
    DOC_ID = "events"

    def __init__(
        self, repository: Repository, *, sensitive_keys: frozenset[str] = SENSITIVE_KEYS
    ) -> None:
        self._repo = repository
        self._sensitive = sensitive_keys

    def record(self, event: Document) -> None:
        """Append one telemetry event, redacting sensitive fields first."""
        doc = self._repo.load(self.DOC_TYPE, self.DOC_ID) or {"schema_version": 1, "events": []}
        doc["events"].append(redact(event, self._sensitive))
        self._repo.save(self.DOC_TYPE, self.DOC_ID, doc)

    def events(self) -> list[Document]:
        """Return the recorded events (empty if none yet)."""
        doc = self._repo.load(self.DOC_TYPE, self.DOC_ID)
        return doc["events"] if doc else []
