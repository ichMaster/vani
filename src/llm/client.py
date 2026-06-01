"""LLM clients: the single place the model is called (architecture §11).

Two Claude tiers behind one interface — Haiku (perception, simple turns) and
Opus (deep turns). Streaming is surfaced through an `on_delta` callback; token
usage is returned on completion. The Anthropic SDK is imported lazily so the
package imports without it and so tests can inject a stub.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from src.config.config import Config
from src.llm.prompt import build_system

# Anthropic-native chat message: {"role": "user"|"assistant", "content": "..."}.
Message = dict[str, str]


@dataclass
class Usage:
    """Token usage for one completion."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0


@dataclass
class Completion:
    """The result of one LLM call."""

    text: str
    tier: str
    usage: Usage = field(default_factory=Usage)


@runtime_checkable
class LLMClient(Protocol):
    """The interface every layer uses; lets the model be mocked in tests."""

    async def complete(
        self,
        *,
        system: str,
        messages: list[Message],
        tier: str = "opus",
        on_delta: Callable[[str], None] | None = None,
    ) -> Completion: ...


class AnthropicClient:
    """An `LLMClient` over the Anthropic SDK, with streaming."""

    def __init__(self, config: Config, *, max_tokens: int = 1024) -> None:
        self._config = config
        self._max_tokens = max_tokens
        self._client = None  # lazily constructed on first call

    def _model_for(self, tier: str) -> str:
        return self._config.haiku_model if tier == "haiku" else self._config.opus_model

    def _ensure_client(self):
        if self._client is None:
            if not self._config.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY is not set; cannot call the LLM")
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self._config.anthropic_api_key)
        return self._client

    async def complete(
        self,
        *,
        system: str,
        messages: list[Message],
        tier: str = "opus",
        on_delta: Callable[[str], None] | None = None,
    ) -> Completion:
        client = self._ensure_client()
        parts: list[str] = []
        async with client.messages.stream(
            model=self._model_for(tier),
            max_tokens=self._max_tokens,
            system=build_system(system),  # cached prefix; messages are the fresh suffix
            messages=messages,
        ) as stream:
            async for delta in stream.text_stream:
                parts.append(delta)
                if on_delta is not None:
                    on_delta(delta)
            final = await stream.get_final_message()
        usage = final.usage
        return Completion(
            text="".join(parts),
            tier=tier,
            usage=Usage(
                input_tokens=getattr(usage, "input_tokens", 0) or 0,
                output_tokens=getattr(usage, "output_tokens", 0) or 0,
                cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            ),
        )
