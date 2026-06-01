"""Tests for the TUI token/cost meter wiring (VANI-018)."""

import asyncio
import json

from textual.widgets import Static

from src.engine import Engine
from src.llm.client import Completion, Usage
from src.planner.perception import PERCEPTION_SYSTEM
from src.state.json_store import JsonStore
from src.telemetry.logging import TelemetrySink
from src.tui.app import VaniApp


class _UsageStub:
    async def complete(self, *, system, messages, tier="opus", on_delta=None) -> Completion:
        if system == PERCEPTION_SYSTEM:
            payload = {
                "topic": {"value": "t", "confidence": 0.9},
                "intent": {"value": "chitchat", "confidence": 0.9},  # simple route
            }
            return Completion(json.dumps(payload), tier, Usage(input_tokens=100, output_tokens=20))
        return Completion("hi", tier, Usage(input_tokens=300, output_tokens=80))


def test_engine_usage_summary_accumulates(tmp_path):
    store = JsonStore(tmp_path)
    engine = Engine(store, _UsageStub(), telemetry=TelemetrySink(store))

    async def run() -> dict:
        await engine.handle_turn("s1", "hi")
        await engine.handle_turn("s1", "again")
        return engine.usage_summary()

    summary = asyncio.run(run())
    # two simple turns, each 100+20 (perception) + 300+80 (gen) = 500 Haiku tokens
    assert summary["total_tokens"] == 1000
    assert summary["turn_tokens"] == 500
    assert summary["opus_tokens"] == 0


def test_status_line_renders_the_meter(tmp_path):
    store = JsonStore(tmp_path)
    engine = Engine(store, _UsageStub(), telemetry=TelemetrySink(store))

    async def run() -> str:
        app = VaniApp(engine, session_id="s1")
        async with app.run_test() as pilot:
            app.query_one("#prompt").value = "hi"
            await pilot.press("enter")
            await pilot.pause()
            return str(app.query_one("#status", Static).render())

    status = asyncio.run(run())
    assert "tok" in status and "$" in status and "session" in status
