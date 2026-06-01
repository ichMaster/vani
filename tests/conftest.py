"""Shared test fixtures and the stub LLM for the headless harness (VANI-010).

These let any test drive a full turn through the brain with a temp repository
and a scripted, network-free LLM — the basis for per-phase tests and later
ablation/replay runs (refinement #3).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from src.contracts.documents import Session, Turn
from src.engine import Engine
from src.llm.client import Completion, Message, Usage
from src.planner.perception import PERCEPTION_SYSTEM
from src.state.json_store import JsonStore

# Canned perception reply (intent chitchat -> simple route) for the stub LLM.
_PERCEPTION_JSON = (
    '{"topic": {"value": "t", "confidence": 0.9}, '
    '"intent": {"value": "chitchat", "confidence": 0.9}}'
)


class StubLLM:
    """A scripted, network-free LLMClient: returns canned replies in order."""

    def __init__(self, replies: list[str] | None = None) -> None:
        self._replies = list(replies) if replies else ["ok"]
        self._index = 0
        self.calls: list[dict] = []

    async def complete(
        self, *, system: str, messages: list[Message], tier: str = "opus", on_delta=None
    ) -> Completion:
        self.calls.append({"system": system, "messages": messages, "tier": tier})
        # Perception calls classify; they must not consume the scripted assistant replies.
        if system == PERCEPTION_SYSTEM:
            return Completion(text=_PERCEPTION_JSON, tier=tier, usage=Usage(input_tokens=1))
        reply = self._replies[min(self._index, len(self._replies) - 1)]
        self._index += 1
        if on_delta is not None:
            on_delta(reply)
        return Completion(text=reply, tier=tier, usage=Usage(input_tokens=1, output_tokens=1))


@pytest.fixture
def tmp_store(tmp_path) -> JsonStore:
    """A repository backed by a throwaway temp directory."""
    return JsonStore(tmp_path)


@pytest.fixture
def make_engine(tmp_store: JsonStore) -> Callable[..., Engine]:
    """Factory: build an Engine over the temp store with a scripted stub LLM."""

    def _make(replies: list[str] | None = None, **kwargs) -> Engine:
        return Engine(tmp_store, StubLLM(replies), **kwargs)

    return _make


@pytest.fixture
def sample_session() -> Session:
    """A small two-turn session for tests that need existing history."""
    return Session(
        session_id="sample",
        user_id="u",
        turns=[Turn("t0", "user", "hi"), Turn("t1", "assistant", "hello")],
    )
