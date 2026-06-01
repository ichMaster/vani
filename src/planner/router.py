"""Deterministic router (spec §9.5): simple -> Haiku, deep -> Opus. No LLM call.

Scored code, not a model call: it reads the `PerceptionResult` and decides the
route, recording it on the `TurnPlan`. Thresholds are config knobs so routing is
tunable without code changes.
"""

from __future__ import annotations

from src.config.config import Config
from src.contracts.pipeline import PerceptionResult, TurnPlan


def decide_route(perception: PerceptionResult, config: Config) -> str:
    """Return "simple" or "deep" for this turn."""
    intent = perception.intent

    # Ambiguity: a low-confidence classification is reasoned out on the deep tier.
    if intent.confidence < config.route_confidence_floor:
        return "deep"

    # Emotional weight escalates (emotion is a placeholder until v0 P3).
    if perception.emotion.arousal >= config.route_arousal_ceiling:
        return "deep"

    # Simple, low-stakes intents stay on the fast tier.
    if intent.value in config.simple_intents:
        return "simple"

    return "deep"


def make_plan(perception: PerceptionResult, config: Config) -> TurnPlan:
    """Build the minimal v0 P1 turn plan: the route plus the perceived intent."""
    return TurnPlan(route=decide_route(perception, config), intent=perception.intent.value)
