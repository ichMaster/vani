"""Tests for prompt-prefix assembly (VANI-016)."""

from src.llm.prompt import CACHE_CONTROL, build_system


def test_identity_only_is_one_cached_block():
    blocks = build_system("You are Vani.")
    assert len(blocks) == 1
    assert blocks[0]["text"] == "You are Vani."
    assert blocks[0]["cache_control"] == CACHE_CONTROL


def test_temperament_appends_a_second_cached_block():
    blocks = build_system("identity", "today you are warm")
    assert len(blocks) == 2
    assert blocks[1]["text"] == "today you are warm"
    assert all(b["cache_control"] == CACHE_CONTROL for b in blocks)


def test_no_temperament_block_when_absent():
    assert len(build_system("identity")) == 1
    assert len(build_system("identity", None)) == 1
    assert len(build_system("identity", "")) == 1  # empty temperament is skipped
