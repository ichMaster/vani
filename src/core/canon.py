"""Layer 1 character core — the placeholder canon for P0 (architecture §3.1).

A minimal identity so the assistant is *someone*; the full hand-authored
character bible arrives at v1 P1 (canon.schema.json). The canon carries NO
confidence — it is a stable foundation, not a hypothesis.
"""

from __future__ import annotations

from src.contracts.documents import Document
from src.state.repository import Repository

CANON_DOC_TYPE = "canon"
CANON_ID = "default"

# Minimal placeholder canon. Expanded into the full bible at v1 P1.
PLACEHOLDER_CANON: Document = {
    "schema_version": 1,
    "name": "Vani",
    "birth_myth": "A companion born to fit the person it speaks with.",
    "aesthetic_and_voice": "warm, concise, and curious",
    "hard_invariants": [
        "correctness",
        "honesty_without_fabrication",
        "safety",
        "wellbeing",
        "child_safety",
    ],
}


def default_canon() -> Document:
    """Return a fresh copy of the placeholder canon."""
    return dict(PLACEHOLDER_CANON)


def load_canon(repository: Repository) -> Document:
    """Load the canon via the repository, seeding the placeholder on first run."""
    raw = repository.load(CANON_DOC_TYPE, CANON_ID)
    if raw is None:
        raw = default_canon()
        repository.save(CANON_DOC_TYPE, CANON_ID, raw)
    return raw


def compile_identity_prompt(canon: Document) -> str:
    """Compile the canon into the cached system-prompt identity block."""
    name = canon.get("name", "Vani")
    voice = canon.get("aesthetic_and_voice", "warm and concise")
    invariants = ", ".join(canon.get("hard_invariants", []))
    return (
        f"You are {name}, a single, coherent companion. "
        f"Your voice is {voice}. Speak as one personality. "
        f"Above all and above identity, always uphold: {invariants}."
    )
