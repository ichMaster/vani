"""Shared, serializable data contracts and document schema versioning.

Single source of truth for the in-memory shapes (architecture §9). The JSON
Schema exports under `specification/architecture/schemas/` mirror these, and the
tests assert the two agree. Every persisted document carries `schema_version`;
the repository migrates older documents forward on read.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Document = dict[str, Any]

# Current version of the persisted-document schemas. Bump when a document shape
# changes, and add the corresponding upgrade step to `migrate`.
SCHEMA_VERSION = 1


@dataclass
class Turn:
    """One turn in a session (sessions.schema.json -> turns[])."""

    turn_id: str
    role: str  # "user" | "assistant"
    text: str = ""
    route: str | None = None  # "simple" | "deep" — set on assistant turns (v0 P1)

    def to_dict(self) -> Document:
        data: Document = {"turn_id": self.turn_id, "role": self.role, "text": self.text}
        if self.route is not None:
            data["route"] = self.route
        return data

    @classmethod
    def from_dict(cls, data: Document) -> Turn:
        return cls(
            turn_id=data["turn_id"],
            role=data["role"],
            text=data.get("text", ""),
            route=data.get("route"),
        )


@dataclass
class Session:
    """Per-session turn history (sessions.schema.json)."""

    session_id: str
    user_id: str
    turns: list[Turn] = field(default_factory=list)
    started_at: str | None = None
    ended_at: str | None = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> Document:
        data: Document = {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "turns": [t.to_dict() for t in self.turns],
        }
        if self.started_at is not None:
            data["started_at"] = self.started_at
        if self.ended_at is not None:
            data["ended_at"] = self.ended_at
        return data

    @classmethod
    def from_dict(cls, data: Document) -> Session:
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            turns=[Turn.from_dict(t) for t in data.get("turns", [])],
            started_at=data.get("started_at"),
            ended_at=data.get("ended_at"),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


def migrate(doc_type: str, raw: Document) -> Document:
    """Upgrade a raw document to the current `schema_version` (migrate-on-read).

    The seam for forward-compatible schema evolution: each future version adds
    an upgrade step keyed on the stored version. Version 0 introduces no
    upgrades yet, so it only stamps the current version onto older or
    unversioned documents.
    """
    version = raw.get("schema_version", 0)
    if version < SCHEMA_VERSION:
        raw = {**raw, "schema_version": SCHEMA_VERSION}
    return raw
