"""Tests for the minimal guardrail and its synchronous integration (VANI-007)."""

import asyncio

from src.contracts.documents import Session
from src.engine import Engine
from src.guardian.guardrail import SAFE_REDIRECT, Guardian, GuardResult, MinimalGuardian
from src.llm.client import Completion, Usage
from src.state.json_store import JsonStore


class _Stub:
    def __init__(self, text: str) -> None:
        self.text = text

    async def complete(self, *, system, messages, tier="opus", on_delta=None) -> Completion:
        return Completion(text=self.text, tier=tier, usage=Usage())


def test_minimal_guardian_is_a_guardian():
    assert isinstance(MinimalGuardian(), Guardian)


def test_passes_clean_text():
    result = MinimalGuardian().check("a kind, helpful reply")
    assert result == GuardResult("pass", "a kind, helpful reply")


def test_redirects_denylisted_text():
    result = MinimalGuardian(["forbidden"]).check("here is FORBIDDEN content")
    assert result.outcome == "redirect"
    assert result.output == SAFE_REDIRECT


def test_engine_gates_before_speaking(tmp_path):
    # A redirecting guardian must replace the raw model text everywhere it surfaces.
    engine = Engine(
        JsonStore(tmp_path),
        _Stub("this is forbidden content"),
        guardian=MinimalGuardian(["forbidden"]),
    )
    deltas: list[str] = []
    reply = asyncio.run(engine.handle_turn("s1", "hi", on_delta=deltas.append))

    assert reply == SAFE_REDIRECT
    assert "".join(deltas) == SAFE_REDIRECT  # the UI never saw the raw unsafe text
    persisted = Session.from_dict(JsonStore(tmp_path).load("sessions", "s1"))
    assert persisted.turns[-1].text == SAFE_REDIRECT


def test_engine_passes_clean_replies(tmp_path):
    engine = Engine(JsonStore(tmp_path), _Stub("hello there"))
    reply = asyncio.run(engine.handle_turn("s1", "hi"))
    assert reply == "hello there"
