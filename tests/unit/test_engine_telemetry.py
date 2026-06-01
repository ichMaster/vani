"""Tests for per-turn telemetry wired into the engine (VANI-017)."""

import asyncio
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from src.engine import Engine
from src.llm.client import Completion, Usage
from src.planner.perception import PERCEPTION_SYSTEM
from src.state.json_store import JsonStore
from src.telemetry.logging import TelemetrySink

SCHEMA = json.loads(
    (
        Path(__file__).parents[2]
        / "specification"
        / "architecture"
        / "schemas"
        / "telemetry.schema.json"
    ).read_text(encoding="utf-8")
)


class UsageStub:
    """Perception (Haiku) and generation report token usage; intent picks the route."""

    def __init__(self, intent: str) -> None:
        self._intent = intent

    async def complete(self, *, system, messages, tier="opus", on_delta=None) -> Completion:
        if system == PERCEPTION_SYSTEM:
            payload = {
                "topic": {"value": "t", "confidence": 0.9},
                "intent": {"value": self._intent, "confidence": 0.9},
            }
            return Completion(json.dumps(payload), tier, Usage(input_tokens=10, output_tokens=2))
        return Completion(
            "a reply", tier, Usage(input_tokens=40, output_tokens=12, cache_read_tokens=5)
        )


def _run(intent: str, tmp_path) -> dict:
    store = JsonStore(tmp_path)
    sink = TelemetrySink(store)
    asyncio.run(Engine(store, UsageStub(intent), telemetry=sink).handle_turn("s1", "hi"))
    events = sink.events()
    assert len(events) == 1
    return events[0]


def test_deep_turn_records_haiku_and_opus_usage(tmp_path):
    ev = _run("weighing_decision", tmp_path)  # deep
    assert ev["route"] == "deep"
    assert ev["token_usage"]["haiku_input"] == 10  # perception
    assert ev["token_usage"]["opus_input"] == 40  # deep generation
    assert ev["token_usage"]["cache_read"] == 5
    assert ev["metrics"]["guardian_outcome"] == "pass"
    assert "perception" in ev["latency_ms"] and "generation" in ev["latency_ms"]


def test_simple_turn_records_haiku_generation(tmp_path):
    ev = _run("chitchat", tmp_path)  # simple
    assert ev["route"] == "simple"
    # perception (10) + simple generation (40) both Haiku
    assert ev["token_usage"]["haiku_input"] == 50
    assert ev["token_usage"]["opus_input"] == 0


def test_event_conforms_to_schema_and_has_no_message_text(tmp_path):
    ev = _run("chitchat", tmp_path)
    Draft202012Validator(SCHEMA).validate({"schema_version": 1, "events": [ev]})
    assert "text" not in ev and "message" not in ev


def test_no_telemetry_without_a_sink(tmp_path):
    # Engine without a telemetry sink must still run (no crash, nothing recorded).
    store = JsonStore(tmp_path)
    reply = asyncio.run(Engine(store, UsageStub("chitchat")).handle_turn("s1", "hi"))
    assert reply == "a reply"
    assert store.load("telemetry", "events") is None
