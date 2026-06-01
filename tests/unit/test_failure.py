"""Tests for LLM failure handling in dispatch (VANI-015)."""

import asyncio
import json

from src.config.config import Config
from src.contracts.documents import Session
from src.engine import GENERATION_FALLBACK, RETRY_FILLER, Engine
from src.llm.client import Completion, Usage
from src.planner.perception import PERCEPTION_SYSTEM
from src.state.json_store import JsonStore

# No real backoff sleeps in tests.
FAST = Config(llm_retry_base_delay=0.0, llm_max_retries=2)

_PERCEPTION = json.dumps(
    {"topic": {"value": "t", "confidence": 0.9}, "intent": {"value": "chitchat", "confidence": 0.9}}
)


class FailingStub:
    """Perception succeeds; generation raises for the first `fail_generation` attempts."""

    def __init__(
        self, *, fail_generation: int = 0, reply: str = "ok", fail_perception: bool = False
    ):
        self._fail_generation = fail_generation
        self._reply = reply
        self._fail_perception = fail_perception
        self.gen_attempts = 0

    async def complete(self, *, system, messages, tier="opus", on_delta=None) -> Completion:
        if system == PERCEPTION_SYSTEM:
            if self._fail_perception:
                raise ConnectionError("perception down")
            return Completion(text=_PERCEPTION, tier=tier, usage=Usage())
        self.gen_attempts += 1
        if self.gen_attempts <= self._fail_generation:
            raise ConnectionError("generation down")
        return Completion(text=self._reply, tier=tier, usage=Usage())


def test_retries_then_succeeds(tmp_path):
    stub = FailingStub(fail_generation=1, reply="recovered")
    deltas: list[str] = []
    reply = asyncio.run(
        Engine(JsonStore(tmp_path), stub, config=FAST).handle_turn(
            "s1", "hi", on_delta=deltas.append
        )
    )
    assert reply == "recovered"
    assert stub.gen_attempts == 2  # one failure + one success
    assert RETRY_FILLER in deltas  # a filler was shown before retrying


def test_persistent_failure_returns_honest_fallback(tmp_path):
    store = JsonStore(tmp_path)
    stub = FailingStub(fail_generation=99)
    reply = asyncio.run(Engine(store, stub, config=FAST).handle_turn("s1", "hi"))
    assert reply == GENERATION_FALLBACK
    assert stub.gen_attempts == 3  # initial + 2 retries
    # State stays consistent: a complete user+assistant pair, assistant = fallback.
    session = Session.from_dict(store.load("sessions", "s1"))
    assert [(t.role, t.text) for t in session.turns] == [
        ("user", "hi"),
        ("assistant", GENERATION_FALLBACK),
    ]


def test_perception_failure_degrades_without_crashing(tmp_path):
    stub = FailingStub(fail_perception=True, reply="still works")
    reply = asyncio.run(Engine(JsonStore(tmp_path), stub, config=FAST).handle_turn("s1", "hi"))
    assert reply == "still works"  # perception fell back; generation proceeded
