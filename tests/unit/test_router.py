"""Tests for the deterministic router (VANI-013)."""

from src.config.config import Config
from src.contracts.confidence import Confident
from src.contracts.pipeline import Emotion, PerceptionResult
from src.planner.router import decide_route, make_plan

CONFIG = Config()


def _perception(intent: str, conf: float = 0.9, arousal: float = 0.0) -> PerceptionResult:
    return PerceptionResult(
        topic=Confident("t", 0.9),
        intent=Confident(intent, conf),
        emotion=Emotion(arousal=arousal),
    )


def test_simple_intents_stay_simple():
    assert decide_route(_perception("chitchat"), CONFIG) == "simple"
    assert decide_route(_perception("question"), CONFIG) == "simple"


def test_reasoning_and_sharing_go_deep():
    assert decide_route(_perception("weighing_decision"), CONFIG) == "deep"
    assert decide_route(_perception("sharing"), CONFIG) == "deep"


def test_low_confidence_escalates_to_deep():
    # chitchat would be simple, but ambiguity (low confidence) forces deep.
    assert decide_route(_perception("chitchat", conf=0.1), CONFIG) == "deep"


def test_high_arousal_escalates_to_deep():
    assert decide_route(_perception("question", arousal=0.9), CONFIG) == "deep"


def test_thresholds_are_config_driven():
    # Move "sharing" into the simple set via config -> routing changes, no code edit.
    cfg = Config(simple_intents=("sharing",))
    assert decide_route(_perception("sharing"), cfg) == "simple"
    assert decide_route(_perception("chitchat"), cfg) == "deep"


def test_make_plan_writes_route_and_intent():
    plan = make_plan(_perception("question"), CONFIG)
    assert plan.route == "simple"
    assert plan.intent == "question"
