"""Cost estimation from token usage (VANI-018).

Per-million-token prices come from `Config` so they are tunable without code
changes. Used by the TUI token/cost meter; not a billing source of truth.
"""

from __future__ import annotations

from src.config.config import Config

_PER_MILLION = 1_000_000


def estimate_cost(token_usage: dict[str, int], config: Config) -> float:
    """Estimated USD cost for a token_usage dict."""
    total = (
        token_usage.get("haiku_input", 0) * config.price_haiku_input
        + token_usage.get("haiku_output", 0) * config.price_haiku_output
        + token_usage.get("opus_input", 0) * config.price_opus_input
        + token_usage.get("opus_output", 0) * config.price_opus_output
        + token_usage.get("cache_read", 0) * config.price_cache_read
    )
    return total / _PER_MILLION
