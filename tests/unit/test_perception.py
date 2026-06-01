"""Tests for the perception step (VANI-012)."""

import asyncio

from src.contracts.pipeline import PerceptionResult
from src.llm.client import Completion, Usage
from src.planner.perception import perceive


class _StubLLM:
    """Returns canned text and records the tier it was called with."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.tier: str | None = None

    async def complete(self, *, system, messages, tier="opus", on_delta=None) -> Completion:
        self.tier = tier
        return Completion(text=self.text, tier=tier, usage=Usage())


MESSAGES = [{"role": "user", "content": "did the report ship?"}]


def test_perceive_parses_json_into_perception_result():
    llm = _StubLLM(
        '{"topic": {"value": "work report", "confidence": 0.8}, '
        '"intent": {"value": "question", "confidence": 0.9}}'
    )
    result = asyncio.run(perceive(llm, MESSAGES))
    assert isinstance(result, PerceptionResult)
    assert result.topic.value == "work report"
    assert result.intent.value == "question"
    assert result.intent.confidence == 0.9


def test_perceive_uses_the_haiku_tier():
    llm = _StubLLM(
        '{"topic": {"value": "x", "confidence": 0.5}, '
        '"intent": {"value": "chitchat", "confidence": 0.5}}'
    )
    asyncio.run(perceive(llm, MESSAGES))
    assert llm.tier == "haiku"


def test_perceive_tolerates_fences_and_prose():
    llm = _StubLLM(
        'Here you go:\n```json\n{"topic": {"value": "coffee", "confidence": 0.6}, '
        '"intent": {"value": "sharing", "confidence": 0.6}}\n```'
    )
    result = asyncio.run(perceive(llm, MESSAGES))
    assert result.topic.value == "coffee"


def test_perceive_falls_back_on_malformed_output():
    result = asyncio.run(perceive(_StubLLM("totally not json"), MESSAGES))
    assert result.topic.value == "unknown"
    assert result.topic.confidence == 0.0
    assert result.intent.confidence == 0.0
