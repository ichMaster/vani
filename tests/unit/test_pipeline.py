"""Tests for the pipeline contracts (VANI-011)."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from src.contracts.confidence import Confident
from src.contracts.pipeline import Emotion, PerceptionResult, TurnPlan

SCHEMA_DIR = Path(__file__).parents[2] / "specification" / "architecture" / "schemas"


def _validator(schema_file: str) -> Draft202012Validator:
    resources = [
        (
            json.loads(p.read_text(encoding="utf-8"))["$id"],
            Resource.from_contents(json.loads(p.read_text(encoding="utf-8"))),
        )
        for p in SCHEMA_DIR.glob("*.schema.json")
    ]
    registry = Registry().with_resources(resources)
    schema = json.loads((SCHEMA_DIR / schema_file).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=registry)


def test_perception_result_roundtrip():
    pr = PerceptionResult(topic=Confident("work", 0.8), intent=Confident("sharing", 0.7))
    assert PerceptionResult.from_dict(pr.to_dict()) == pr


def test_perception_result_validates_against_schema():
    pr = PerceptionResult(
        topic=Confident("work", 0.8),
        intent=Confident("question", 0.6),
        emotion=Emotion(valence=-0.2, arousal=0.4, confidence=0.5),
        modality=Confident("serious", 0.9),
    )
    _validator("perception_result.schema.json").validate(pr.to_dict())


def test_perception_result_has_required_fields_even_when_minimal():
    pr = PerceptionResult(topic=Confident("x", 0.1), intent=Confident("chitchat", 0.1))
    data = pr.to_dict()
    assert {"topic", "intent", "emotion", "modality"} <= data.keys()


def test_turn_plan_roundtrip_and_schema():
    plan = TurnPlan(route="deep", strategy="empathy", facet_weights={"psychologist": 0.7})
    assert TurnPlan.from_dict(plan.to_dict()) == plan
    _validator("turn_plan.schema.json").validate(plan.to_dict())


def test_turn_plan_minimal_is_valid():
    plan = TurnPlan(route="simple")
    data = plan.to_dict()
    assert {"facet_weights", "strategy", "route"} <= data.keys()
    _validator("turn_plan.schema.json").validate(data)
