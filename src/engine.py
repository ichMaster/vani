"""Transport-agnostic brain entry point (architecture §10).

Every surface (TUI now; voice and server later) drives the brain through
`Engine.handle_turn`; the engine imports no transport code. All per-session
state lives in the repository keyed by `session_id` — the engine holds only its
injected dependencies, never session state — so one engine serves many sessions
and the v2 server/API is a thin adapter rather than a rewrite.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from datetime import UTC, datetime

from src.config.config import Config
from src.contracts.confidence import Confident
from src.contracts.documents import Session, Turn
from src.contracts.pipeline import PerceptionResult
from src.guardian.guardrail import Guardian, MinimalGuardian
from src.llm.client import LLMClient, Usage
from src.planner.perception import PERCEPTION_SYSTEM, parse_perception
from src.planner.router import make_plan
from src.state.repository import Repository
from src.telemetry.cost import estimate_cost
from src.telemetry.logging import TelemetrySink

_USAGE_KEYS = ("haiku_input", "haiku_output", "opus_input", "opus_output", "cache_read")

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
        telemetry: TelemetrySink | None = None,
    ) -> None:
        self._repo = repository
        self._llm = llm
        self._system = system_prompt
        self._user_id = user_id
        self._guardian = guardian or MinimalGuardian()
        self._config = config or Config()
        self._telemetry = telemetry

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

    def usage_summary(self) -> dict:
        """Token/cost summary from telemetry — the last turn and the running totals.

        For an adapter (the TUI token meter) to render; sourced from recorded
        telemetry, never from a fresh llm call.
        """
        events = self._telemetry.events() if self._telemetry is not None else []
        total = dict.fromkeys(_USAGE_KEYS, 0)
        for event in events:
            tu = event.get("token_usage", {})
            for key in _USAGE_KEYS:
                total[key] += tu.get(key, 0)
        last = events[-1].get("token_usage", {}) if events else {}
        return {
            "turn_tokens": sum(last.get(k, 0) for k in _USAGE_KEYS),
            "turn_cost": estimate_cost(last, self._config),
            "total_tokens": sum(total.values()),
            "total_cost": estimate_cost(total, self._config),
            "haiku_tokens": total["haiku_input"] + total["haiku_output"],
            "opus_tokens": total["opus_input"] + total["opus_output"],
            "cache_read_tokens": total["cache_read"],
        }

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
        p_start = time.perf_counter()
        try:
            pc = await self._llm.complete(system=PERCEPTION_SYSTEM, messages=messages, tier="haiku")
            perception = parse_perception(pc.text)
            perception_usage = pc.usage
        except Exception:
            perception = PerceptionResult(
                topic=Confident("unknown", 0.0), intent=Confident("unknown", 0.0)
            )
            perception_usage = Usage()
        perception_ms = (time.perf_counter() - p_start) * 1000
        plan = make_plan(perception, self._config)

        # 3. Dispatch on the route (with retry/backoff), then 4. the Guardian gate.
        g_start = time.perf_counter()
        text, generation_usage = await self._generate(
            messages, _TIER_FOR_ROUTE[plan.route], on_delta
        )
        generation_ms = (time.perf_counter() - g_start) * 1000
        verdict = self._guardian.check(text)
        reply = verdict.output
        if on_delta is not None:
            on_delta(reply)

        # 5. Post-update: persist the turn (with route), then record telemetry.
        turn_id = f"t{len(session.turns)}"
        session.turns.append(Turn(turn_id=turn_id, role="assistant", text=reply, route=plan.route))
        self._save_session(session)
        if self._telemetry is not None:
            self._telemetry.record(
                _turn_event(
                    turn_id,
                    plan.route,
                    perception_ms,
                    generation_ms,
                    perception_usage,
                    generation_usage,
                    verdict.outcome,
                )
            )
        return reply

    async def _generate(
        self,
        messages: list[dict[str, str]],
        tier: str,
        on_delta: Callable[[str], None] | None,
    ) -> tuple[str, Usage]:
        """Generate the reply, retrying transient LLM failures with backoff.

        On a transient error it emits a short filler and retries; once retries
        are exhausted it returns an honest fallback message rather than crash.
        Returns the reply text and the generation token usage.
        """
        delay = self._config.llm_retry_base_delay
        for attempt in range(self._config.llm_max_retries + 1):
            try:
                completion = await self._llm.complete(
                    system=self._system, messages=messages, tier=tier
                )
                return completion.text, completion.usage
            except Exception:
                if attempt < self._config.llm_max_retries:
                    if on_delta is not None:
                        on_delta(RETRY_FILLER)
                    await asyncio.sleep(delay)
                    delay *= 2
        return GENERATION_FALLBACK, Usage()


def _turn_event(
    turn_id: str,
    route: str,
    perception_ms: float,
    generation_ms: float,
    perception_usage: Usage,
    generation_usage: Usage,
    guardian_outcome: str,
) -> dict:
    """Build a per-turn telemetry event (telemetry.schema.json). No message text."""
    usage = {
        "haiku_input": 0,
        "haiku_output": 0,
        "opus_input": 0,
        "opus_output": 0,
        "cache_read": 0,
    }
    # Perception is always a Haiku call.
    usage["haiku_input"] += perception_usage.input_tokens
    usage["haiku_output"] += perception_usage.output_tokens
    usage["cache_read"] += perception_usage.cache_read_tokens
    # Generation is on the route's tier.
    gen_tier = "haiku" if route == "simple" else "opus"
    usage[f"{gen_tier}_input"] += generation_usage.input_tokens
    usage[f"{gen_tier}_output"] += generation_usage.output_tokens
    usage["cache_read"] += generation_usage.cache_read_tokens
    return {
        "turn_id": turn_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "route": route,
        "latency_ms": {
            "perception": round(perception_ms, 1),
            "generation": round(generation_ms, 1),
        },
        "token_usage": usage,
        "metrics": {"guardian_outcome": guardian_outcome},
    }
