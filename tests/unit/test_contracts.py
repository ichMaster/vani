"""Tests for data contracts, schema validation, and migrate-on-read (VANI-003)."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from src.contracts.documents import SCHEMA_VERSION, Session, Turn, migrate
from src.state.json_store import JsonStore

SCHEMA_DIR = Path(__file__).parents[2] / "specification" / "architecture" / "schemas"


def _registry() -> Registry:
    """Register every schema by its $id so sibling $refs resolve."""
    resources = []
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def _validator(schema_file: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / schema_file).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=_registry())


def test_session_roundtrip():
    session = Session(
        session_id="s1",
        user_id="u1",
        turns=[Turn("t1", "user", "hi"), Turn("t2", "assistant", "hello")],
    )
    assert Session.from_dict(session.to_dict()) == session


def test_session_validates_against_schema():
    session = Session(session_id="s1", user_id="u1", turns=[Turn("t1", "user", "hi")])
    _validator("sessions.schema.json").validate(session.to_dict())


def test_all_schemas_are_valid_jsonschema():
    # Drift/sanity guard: every exported schema is a well-formed 2020-12 schema with an $id.
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert "$id" in schema
        Draft202012Validator.check_schema(schema)


def test_migrate_on_read_bumps_version(tmp_path):
    store = JsonStore(tmp_path, migrator=migrate)
    store.save(
        "sessions", "s1", {"schema_version": 0, "session_id": "s1", "user_id": "u1", "turns": []}
    )
    loaded = store.load("sessions", "s1")
    assert loaded["schema_version"] == SCHEMA_VERSION


def test_migrate_is_idempotent():
    current = {"schema_version": SCHEMA_VERSION, "session_id": "s", "user_id": "u", "turns": []}
    assert migrate("sessions", current) == current


@pytest.mark.parametrize("name", ["sessions.schema.json", "turn_plan.schema.json"])
def test_schema_files_exist(name):
    assert (SCHEMA_DIR / name).exists()
