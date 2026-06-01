"""Tests for the TUI adapter (VANI-006)."""

import ast
import asyncio
from pathlib import Path

from src.tui.app import VaniApp

TUI_SRC = Path(__file__).parents[2] / "src" / "tui" / "app.py"


class StubEngine:
    """Stands in for the brain; records turns and streams a canned reply."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def transcript(self, session_id: str) -> list[tuple[str, str]]:
        return [("user", "earlier"), ("assistant", "hello again")]

    async def handle_turn(self, session_id, user_input, *, on_delta=None) -> str:
        self.calls.append(user_input)
        if on_delta is not None:
            on_delta("reply")
        return "reply"


def test_tui_imports_no_state_or_llm():
    # The TUI is an adapter: it must not reach the repository or llm directly.
    tree = ast.parse(TUI_SRC.read_text(encoding="utf-8"))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(a.name for a in node.names)
    assert not [m for m in modules if ".state" in m or ".llm" in m]


def test_initial_transcript_renders_on_mount():
    async def run() -> int:
        app = VaniApp(StubEngine(), session_id="s1")
        async with app.run_test():
            return len(app.query(".msg"))

    assert asyncio.run(run()) == 2


def test_submitting_input_drives_the_engine():
    engine = StubEngine()

    async def run() -> tuple[list[str], int]:
        app = VaniApp(engine, session_id="s1")
        async with app.run_test() as pilot:
            app.query_one("#prompt").value = "hi vani"
            await pilot.press("enter")
            await pilot.pause()
            return engine.calls, len(app.query(".msg"))

    calls, msg_count = asyncio.run(run())
    assert calls == ["hi vani"]
    # 2 initial + user + assistant
    assert msg_count == 4
