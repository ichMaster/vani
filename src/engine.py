"""Transport-agnostic brain entry point (architecture §10).

Every surface (TUI now; voice and server later) drives the brain through
`Engine.handle_turn`; the engine imports no transport code. All per-session
state lives in the repository keyed by `session_id` — the engine holds only its
injected dependencies, never session state — so one engine serves many sessions
and the v3 server/API is a thin adapter rather than a rewrite.
"""

from __future__ import annotations

from collections.abc import Callable

from src.contracts.documents import Session, Turn
from src.llm.client import LLMClient
from src.state.repository import Repository

# Minimal placeholder identity; replaced by the compiled canon at VANI-008 / v2 P1.
DEFAULT_SYSTEM = "You are Vani, a warm and concise companion. Reply briefly and kindly."


class Engine:
    """The brain. Runs one conversational turn for a session."""

    def __init__(
        self,
        repository: Repository,
        llm: LLMClient,
        *,
        system_prompt: str = DEFAULT_SYSTEM,
        user_id: str = "local",
    ) -> None:
        self._repo = repository
        self._llm = llm
        self._system = system_prompt
        self._user_id = user_id

    def _load_session(self, session_id: str) -> Session:
        raw = self._repo.load("sessions", session_id)
        if raw is None:
            return Session(session_id=session_id, user_id=self._user_id)
        return Session.from_dict(raw)

    def _save_session(self, session: Session) -> None:
        self._repo.save("sessions", session.session_id, session.to_dict())

    async def handle_turn(
        self,
        session_id: str,
        user_input: str,
        *,
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        """Run one turn: append the user message, generate a reply, persist, return it.

        `on_delta` (optional) receives streamed reply chunks for live rendering.
        """
        session = self._load_session(session_id)
        session.turns.append(Turn(turn_id=f"t{len(session.turns)}", role="user", text=user_input))

        messages = [{"role": t.role, "content": t.text} for t in session.turns]
        completion = await self._llm.complete(
            system=self._system, messages=messages, tier="opus", on_delta=on_delta
        )

        session.turns.append(
            Turn(turn_id=f"t{len(session.turns)}", role="assistant", text=completion.text)
        )
        self._save_session(session)
        return completion.text
