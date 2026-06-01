"""Tests for logging and the telemetry sink (VANI-009)."""

import json
import logging
from pathlib import Path

from jsonschema import Draft202012Validator

from src.state.json_store import JsonStore
from src.telemetry.logging import REDACTED, TelemetrySink, get_logger, redact

SCHEMA_DIR = Path(__file__).parents[2] / "specification" / "architecture" / "schemas"


def test_logger_level_is_configurable():
    logger = get_logger("vani.test", "DEBUG")
    assert logger.level == logging.DEBUG
    assert logger.handlers  # has a structured handler


def test_redact_masks_sensitive_keys_recursively():
    data = {
        "turn_id": "t1",
        "text": "secret message",
        "user": {"birth_data": {"date": "1990-01-01"}},
    }
    out = redact(data)
    assert out["turn_id"] == "t1"
    assert out["text"] == REDACTED
    assert out["user"]["birth_data"] == REDACTED


def test_sink_records_and_reads_back(tmp_path):
    sink = TelemetrySink(JsonStore(tmp_path))
    sink.record({"turn_id": "t1", "timestamp": "2026-06-01T00:00:00Z", "route": "deep"})
    events = sink.events()
    assert len(events) == 1
    assert events[0]["route"] == "deep"


def test_sink_redacts_before_storing(tmp_path):
    sink = TelemetrySink(JsonStore(tmp_path))
    sink.record({"turn_id": "t1", "timestamp": "2026-06-01T00:00:00Z", "text": "private"})
    assert sink.events()[0]["text"] == REDACTED


def test_telemetry_doc_conforms_to_schema(tmp_path):
    sink = TelemetrySink(JsonStore(tmp_path))
    sink.record({"turn_id": "t1", "timestamp": "2026-06-01T00:00:00Z", "route": "simple"})
    doc = JsonStore(tmp_path).load("telemetry", "events")
    schema = json.loads((SCHEMA_DIR / "telemetry.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(doc)
