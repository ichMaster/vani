"""Tests for the transport-agnostic engine (VANI-005)."""

import asyncio

from src.contracts.documents import Session
from src.engine import Engine
from src.llm.client import Completion, Message, Usage
from src.state.json_store import JsonStore


class StubLLM:
    """Echoes a canned reply and records the messages it was given."""

    def __init__(self, text: str = "hello") -> None:
        self.text = text
        self.last_messages: list[Message] | None = None

    async def complete(self, *, system, messages, tier="opus", on_delta=None) -> Completion:
        self.last_messages = messages
        if on_delta is not None:
            on_delta(self.text)
        return Completion(text=self.text, tier=tier, usage=Usage())


def _engine(tmp_path, text="hello") -> tuple[Engine, JsonStore, StubLLM]:
    store = JsonStore(tmp_path)
    llm = StubLLM(text)
    return Engine(store, llm), store, llm


def test_handle_turn_returns_reply(tmp_path):
    engine, _, _ = _engine(tmp_path, "hi there")
    reply = asyncio.run(engine.handle_turn("s1", "hello"))
    assert reply == "hi there"


def test_turn_is_persisted(tmp_path):
    engine, store, _ = _engine(tmp_path)
    asyncio.run(engine.handle_turn("s1", "hello"))
    session = Session.from_dict(store.load("sessions", "s1"))
    assert [(t.role, t.text) for t in session.turns] == [("user", "hello"), ("assistant", "hello")]


def test_on_delta_receives_stream(tmp_path):
    engine, _, _ = _engine(tmp_path, "streamed")
    deltas: list[str] = []
    asyncio.run(engine.handle_turn("s1", "hi", on_delta=deltas.append))
    assert "".join(deltas) == "streamed"


def test_history_carried_into_next_turn(tmp_path):
    engine, _, llm = _engine(tmp_path)
    asyncio.run(engine.handle_turn("s1", "first"))
    asyncio.run(engine.handle_turn("s1", "second"))
    # second call sees the full prior history plus the new user turn
    assert [m["content"] for m in llm.last_messages] == ["first", "hello", "second"]


def test_sessions_are_independent(tmp_path):
    engine, store, _ = _engine(tmp_path)
    asyncio.run(engine.handle_turn("s1", "alpha"))
    asyncio.run(engine.handle_turn("s2", "beta"))
    assert len(Session.from_dict(store.load("sessions", "s1")).turns) == 2
    assert Session.from_dict(store.load("sessions", "s2")).turns[0].text == "beta"
