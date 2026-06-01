"""Tests for the LLM client (VANI-004)."""

import asyncio

import pytest

from src.config.config import Config
from src.llm.client import AnthropicClient, Completion, LLMClient, Message, Usage


class StubLLM:
    """A mock LLMClient that streams a canned reply (used to inject in tests)."""

    def __init__(self, text: str = "hi there") -> None:
        self._text = text

    async def complete(
        self, *, system: str, messages: list[Message], tier: str = "opus", on_delta=None
    ) -> Completion:
        for word in self._text.split():
            if on_delta is not None:
                on_delta(word + " ")
        return Completion(text=self._text, tier=tier, usage=Usage(input_tokens=5, output_tokens=3))


def test_stub_satisfies_llmclient_protocol():
    assert isinstance(StubLLM(), LLMClient)


def test_stub_streams_deltas_and_returns_usage():
    deltas: list[str] = []
    stub = StubLLM("alpha beta gamma")
    result = asyncio.run(
        stub.complete(
            system="s", messages=[{"role": "user", "content": "x"}], on_delta=deltas.append
        )
    )
    assert result.text == "alpha beta gamma"
    assert "".join(deltas).strip() == "alpha beta gamma"
    assert result.usage.input_tokens == 5


def test_anthropic_client_requires_api_key():
    client = AnthropicClient(Config(anthropic_api_key=None))
    with pytest.raises(RuntimeError):
        asyncio.run(client.complete(system="s", messages=[{"role": "user", "content": "hi"}]))


def test_anthropic_client_selects_model_by_tier():
    client = AnthropicClient(Config(anthropic_api_key="k", opus_model="OPUS", haiku_model="HAIKU"))
    assert client._model_for("opus") == "OPUS"
    assert client._model_for("haiku") == "HAIKU"
