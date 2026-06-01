"""Perception step (spec §9.2 step 1): one Haiku call that classifies the input.

Reads the user's latest message (with recent context) and returns a structured
`PerceptionResult` — it does not reply to the user. The only LLM call at the
input of a turn. For v0 P1 it populates topic + intent; emotion/modality arrive
at v0 P3 (the fields are present but low-confidence).
"""

from __future__ import annotations

import json

from src.contracts.confidence import Confident, clamp
from src.contracts.pipeline import PerceptionResult
from src.llm.client import LLMClient, Message

INTENTS = ("question", "command", "sharing", "chitchat", "weighing_decision")

PERCEPTION_SYSTEM = (
    "You classify a user's latest message for a conversational assistant. "
    "Reply with ONLY a JSON object (no prose, no code fences) of the form: "
    '{"topic": {"value": "<short topic>", "confidence": <0..1>}, '
    '"intent": {"value": "<one of: ' + ", ".join(INTENTS) + '>", "confidence": <0..1>}}. '
    "Do not answer the user; only classify."
)


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of the model's reply (tolerates fences/prose)."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object in perception output")
    return json.loads(text[start : end + 1])


def _as_confident(raw: object, default_conf: float = 0.5) -> Confident[str]:
    """Accept either {"value", "confidence"} or a bare string."""
    if isinstance(raw, dict):
        return Confident(
            str(raw.get("value", "")), clamp(float(raw.get("confidence", default_conf)))
        )
    return Confident(str(raw), default_conf)


async def perceive(llm: LLMClient, messages: list[Message]) -> PerceptionResult:
    """Classify the latest message via one Haiku call; fall back safely on bad output."""
    completion = await llm.complete(system=PERCEPTION_SYSTEM, messages=messages, tier="haiku")
    try:
        data = _extract_json(completion.text)
        return PerceptionResult(
            topic=_as_confident(data["topic"]),
            intent=_as_confident(data["intent"]),
        )
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        # Low-confidence fallback — the planner treats this as "ask again / be cautious".
        return PerceptionResult(topic=Confident("unknown", 0.0), intent=Confident("unknown", 0.0))
