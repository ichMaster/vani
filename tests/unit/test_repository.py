"""Tests for the JSON-backed Repository (VANI-002)."""

from src.state.json_store import JsonStore
from src.state.repository import Repository


def test_jsonstore_is_a_repository(tmp_path):
    store = JsonStore(tmp_path)
    assert isinstance(store, Repository)


def test_save_load_roundtrip_utf8(tmp_path):
    store = JsonStore(tmp_path)
    doc = {"name": "Вані", "note": "café — naïve", "n": 3}
    store.save("sessions", "s1", doc)
    assert store.load("sessions", "s1") == doc


def test_load_missing_returns_none(tmp_path):
    store = JsonStore(tmp_path)
    assert store.load("sessions", "nope") is None


def test_list_ids(tmp_path):
    store = JsonStore(tmp_path)
    store.save("sessions", "b", {"x": 1})
    store.save("sessions", "a", {"x": 2})
    assert store.list_ids("sessions") == ["a", "b"]
    assert store.list_ids("missing") == []


def test_delete(tmp_path):
    store = JsonStore(tmp_path)
    store.save("sessions", "s1", {"x": 1})
    assert store.delete("sessions", "s1") is True
    assert store.delete("sessions", "s1") is False
    assert store.load("sessions", "s1") is None
