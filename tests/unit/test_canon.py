"""Tests for the placeholder canon and confidence scaffolding (VANI-008)."""

import asyncio

from src.contracts.confidence import Confident, clamp
from src.core.canon import CANON_ID, compile_identity_prompt, default_canon, load_canon
from src.engine import Engine
from src.llm.client import Completion, Usage
from src.state.json_store import JsonStore


class _RecordingLLM:
    def __init__(self) -> None:
        self.system: str | None = None

    async def complete(self, *, system, messages, tier="opus", on_delta=None) -> Completion:
        self.system = system
        return Completion(text="hi", tier=tier, usage=Usage())


def test_canon_carries_no_confidence():
    canon = default_canon()
    assert "confidence" not in canon


def test_load_canon_seeds_then_persists(tmp_path):
    store = JsonStore(tmp_path)
    canon = load_canon(store)
    assert canon["name"] == "Vani"
    # second load returns the persisted document
    assert store.load("canon", CANON_ID) == canon


def test_identity_prompt_reflects_canon():
    prompt = compile_identity_prompt(default_canon())
    assert "Vani" in prompt
    assert "child_safety" in prompt


def test_engine_uses_canon_identity(tmp_path):
    store = JsonStore(tmp_path)
    llm = _RecordingLLM()
    identity = compile_identity_prompt(load_canon(store))
    engine = Engine(store, llm, system_prompt=identity)
    asyncio.run(engine.handle_turn("s1", "hello"))
    assert llm.system is not None and "Vani" in llm.system


def test_confident_clamps():
    assert clamp(1.5) == 1.0
    assert clamp(-0.2) == 0.0
    assert Confident("emotion", 2.0).confidence == 1.0
