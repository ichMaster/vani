"""Tests for token cost estimation and the TUI meter formatting (VANI-018)."""

from src.config.config import Config
from src.telemetry.cost import estimate_cost
from src.tui.app import format_meter

CONFIG = Config()


def test_estimate_cost_uses_per_tier_prices():
    usage = {"haiku_input": 1_000_000, "opus_output": 1_000_000}
    cost = estimate_cost(usage, CONFIG)
    assert cost == CONFIG.price_haiku_input + CONFIG.price_opus_output


def test_estimate_cost_is_config_driven():
    usage = {"opus_input": 1_000_000}
    assert estimate_cost(usage, Config(price_opus_input=30.0)) == 30.0


def test_empty_usage_is_zero_cost():
    assert estimate_cost({}, CONFIG) == 0.0


def test_format_meter_shows_tokens_and_cost():
    summary = {
        "turn_tokens": 1200,
        "turn_cost": 0.012,
        "total_tokens": 5000,
        "total_cost": 0.05,
        "haiku_tokens": 2100,
        "opus_tokens": 2900,
        "cache_read_tokens": 0,
    }
    line = format_meter(summary)
    assert "1.2k tok" in line
    assert "$0.0120" in line
    assert "session 5.0k tok" in line
    assert "H 2.1k / O 2.9k" in line
