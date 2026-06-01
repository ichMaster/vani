"""Tests for dispatch + routing wired into the engine (VANI-014)."""

import asyncio
import json

from src.contracts.documents import Session
from src.engine import Engine
from src.guardian.guardrail import SAFE_REDIRECT, MinimalGuardian
from src.llm.client import Completion, Usage
from src.planner.perception import PERCEPTION_SYSTEM
from src.state.json_store import JsonStore


class RouteStub:
    """Perception returns a chosen intent; generation returns a reply. Records tiers."""

    def __init__(self, intent: str, reply: str = "ok") -> None:
        self._intent = intent
        self._reply = reply
        self.tiers: list[str] = []

    async def complete(self, *, system, messages, tier="opus", on_delta=None) -> Completion:
        self.tiers.append(tier)
        if system == PERCEPTION_SYSTEM:
            payload = {
                "topic": {"value": "t", "confidence": 0.9},
                "intent": {"value": self._intent, "confidence": 0.9},
            }
            return Completion(text=json.dumps(payload), tier=tier, usage=Usage())
        if on_delta is not None:
            on_delta(self._reply)
        return Completion(text=self._reply, tier=tier, usage=Usage())


def test_simple_route_generates_on_haiku(tmp_path):
    stub = RouteStub("chitchat")  # simple intent
    asyncio.run(Engine(JsonStore(tmp_path), stub).handle_turn("s1", "hi"))
    assert stub.tiers == ["haiku", "haiku"]  # perception + Haiku generation


def test_deep_route_makes_one_haiku_and_one_opus_call(tmp_path):
    stub = RouteStub("weighing_decision")  # deep intent
    asyncio.run(Engine(JsonStore(tmp_path), stub).handle_turn("s1", "hi"))
    assert stub.tiers == ["haiku", "opus"]  # one Haiku (perception) + one Opus (generation)


def test_route_recorded_on_assistant_turn(tmp_path):
    store = JsonStore(tmp_path)
    asyncio.run(Engine(store, RouteStub("weighing_decision")).handle_turn("s1", "hi"))
    assistant = Session.from_dict(store.load("sessions", "s1")).turns[-1]
    assert assistant.role == "assistant"
    assert assistant.route == "deep"


def test_guardrail_still_gates_after_routing(tmp_path):
    stub = RouteStub("chitchat", reply="this is forbidden content")
    engine = Engine(JsonStore(tmp_path), stub, guardian=MinimalGuardian(["forbidden"]))
    reply = asyncio.run(engine.handle_turn("s1", "hi"))
    assert reply == SAFE_REDIRECT
