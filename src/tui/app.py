"""The text UI — a thin adapter over the brain engine (architecture §10).

The TUI holds no brain logic and never touches the llm or the repository
directly: it renders `engine.transcript(...)` and sends input through
`engine.handle_turn(...)`, streaming the reply via the `on_delta` callback.
"""

from __future__ import annotations

from typing import Protocol

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Input, Static


class TurnHandler(Protocol):
    """The slice of the engine the TUI depends on."""

    def transcript(self, session_id: str) -> list[tuple[str, str]]: ...
    async def handle_turn(self, session_id: str, user_input: str, *, on_delta=None) -> str: ...


class VaniApp(App):
    """A minimal chat TUI: scrollable transcript, input field, status line."""

    CSS = """
    #transcript { height: 1fr; padding: 0 1; }
    .msg { margin-bottom: 1; }
    .user { color: $accent; }
    .assistant { color: $text; }
    #status { height: 1; color: $text-muted; padding: 0 1; }
    """

    def __init__(self, engine: TurnHandler, *, session_id: str = "local") -> None:
        super().__init__()
        self._engine = engine
        self._session_id = session_id

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="transcript")
        yield Input(placeholder="Talk to Vani…", id="prompt")
        yield Static("Vani — type a message and press Enter", id="status")

    def on_mount(self) -> None:
        for role, text in self._engine.transcript(self._session_id):
            self._append(role, text)
        self.query_one("#prompt", Input).focus()

    def _append(self, role: str, text: str) -> Static:
        line = Static(text, classes=f"msg {role}")
        self.query_one("#transcript", VerticalScroll).mount(line)
        return line

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        prompt = self.query_one("#prompt", Input)
        prompt.value = ""
        prompt.disabled = True
        self._append("user", text)
        reply_line = self._append("assistant", "")
        buffer = ""

        def on_delta(chunk: str) -> None:
            nonlocal buffer
            buffer += chunk
            reply_line.update(buffer)

        try:
            reply = await self._engine.handle_turn(self._session_id, text, on_delta=on_delta)
            reply_line.update(reply)
        finally:
            prompt.disabled = False
            prompt.focus()


def run_tui(engine: TurnHandler, *, session_id: str = "local") -> None:
    """Launch the Vani TUI over the given engine."""
    VaniApp(engine, session_id=session_id).run()
