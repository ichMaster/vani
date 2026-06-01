"""Transport-agnostic brain entry point (architecture §10).

Every surface (TUI now; voice and server later) drives the brain through
`Engine.handle_turn`; the engine imports no transport code. All per-session
state lives in the repository keyed by `session_id` — the engine holds only its
injected dependencies, never session state — so one engine serves many sessions
and the v2 server/API is a thin adapter rather than a rewrite.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from src.config.config import Config
from src.contracts.confidence import Confident
from src.contracts.documents import Session, Turn
from src.contracts.pipeline import PerceptionResult
from src.guardian.guardrail import Guardian, MinimalGuardian
from src.llm.client import LLMClient
from src.planner.perception import perceive
from src.planner.router import make_plan
from src.state.repository import Repository

# Minimal placeholder identity; replaced by the compiled canon at VANI-008 / v1 P1.
DEFAULT_SYSTEM = "You are Vani, a warm and concise companion. Reply briefly and kindly."

# Generation tier per route: simple turns answer on Haiku, deep turns on Opus.
_TIER_FOR_ROUTE = {"simple": "haiku", "deep": "opus"}

# Degradation messages (spec §15). The local-LLM offline fallback comes later.
RETRY_FILLER = "(one moment…)"
GENERATION_FALLBACK = (
    "I'm having trouble reaching my brain right now — give me a moment and try again."
)


class Engine:
    """The brain. Runs one conversational turn for a session."""

    def __init__(
        self,
        repository: Repository,
        llm: LLMClient,
        *,
        system_prompt: str = DEFAULT_SYSTEM,
        user_id: str = "local",
        guardian: Guardian | None = None,
        config: Config | None = None,
    ) -> None:
        self._repo = repository
        self._llm = llm
        self._system = system_prompt
        self._user_id = user_id
        self._guardian = guardian or MinimalGuardian()
        self._config = config or Config()

    def _load_session(self, session_id: str) -> Session:
        raw = self._repo.load("sessions", session_id)
        if raw is None:
            return Session(session_id=session_id, user_id=self._user_id)
        return Session.from_dict(raw)

    def _save_session(self, session: Session) -> None:
        self._repo.save("sessions", session.session_id, session.to_dict())

    def transcript(self, session_id: str) -> list[tuple[str, str]]:
        """Return the (role, text) history for a session, for an adapter to render."""
        return [(t.role, t.text) for t in self._load_session(session_id).turns]

    async def handle_turn(
        self,
        session_id: str,
        user_input: str,
        *,
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        """Run one turn: perceive, route, generate, gate, persist, return.

        Pipeline (spec §9.2): one Haiku perception call classifies the message;
        deterministic routing picks the generation tier (simple -> Haiku, deep ->
        Opus); the model output is buffered and passed through the synchronous
        Guardian *before* anything reaches the caller — safety is never checked
        after the fact. `on_delta` (optional) receives the guarded reply.
        """
        session = self._load_session(session_id)
        session.turns.append(Turn(turn_id=f"t{len(session.turns)}", role="user", text=user_input))
        messages = [{"role": t.role, "content": t.text} for t in session.turns]

        # 1. Perception (Haiku) -> 2. Decision (deterministic route). A failed
        # perception degrades to a low-confidence read (which routes to deep).
        try:
            perception = await perceive(self._llm, messages)
        except Exception:
            perception = PerceptionResult(
                topic=Confident("unknown", 0.0), intent=Confident("unknown", 0.0)
            )
        plan = make_plan(perception, self._config)

        # 3. Dispatch on the route (with retry/backoff), then 4. the Guardian gate.
        text = await self._generate(messages, _TIER_FOR_ROUTE[plan.route], on_delta)
        verdict = self._guardian.check(text)
        reply = verdict.output
        if on_delta is not None:
            on_delta(reply)

        # 5. Post-update: persist the turn, recording the route taken.
        session.turns.append(
            Turn(turn_id=f"t{len(session.turns)}", role="assistant", text=reply, route=plan.route)
        )
        self._save_session(session)
        return reply

    async def _generate(
        self,
        messages: list[dict[str, str]],
        tier: str,
        on_delta: Callable[[str], None] | None,
    ) -> str:
        """Generate the reply, retrying transient LLM failures with backoff.

        On a transient error it emits a short filler and retries; once retries
        are exhausted it returns an honest fallback message rather than crash.
        """
        delay = self._config.llm_retry_base_delay
        for attempt in range(self._config.llm_max_retries + 1):
            try:
                completion = await self._llm.complete(
                    system=self._system, messages=messages, tier=tier
                )
                return completion.text
            except Exception:
                if attempt < self._config.llm_max_retries:
                    if on_delta is not None:
                        on_delta(RETRY_FILLER)
                    await asyncio.sleep(delay)
                    delay *= 2
        return GENERATION_FALLBACK
