"""Configuration loader.

Precedence: explicit overrides > environment variables > `.env` file > defaults.
A local `.env` (gitignored) supplies secrets like ANTHROPIC_API_KEY for local
runs; real environment variables always win over it. Config is instantiated per
run (no global mutable cache), and reading `.env` never mutates `os.environ`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


@dataclass(frozen=True)
class Config:
    """Runtime configuration for a Vani session."""

    anthropic_api_key: str | None = None
    log_level: str = "INFO"
    state_dir: str = ".vani_state"
    opus_model: str = "claude-opus-4-8"
    haiku_model: str = "claude-haiku-4-5-20251001"

    # Routing knobs (VANI-013): which intents stay on the fast tier, and the
    # thresholds that escalate to the deep tier (ambiguity / emotional weight).
    simple_intents: tuple[str, ...] = ("chitchat", "question", "command")
    route_confidence_floor: float = 0.4
    route_arousal_ceiling: float = 0.66

    # LLM failure handling (VANI-015): retries on transient errors + backoff base (seconds).
    llm_max_retries: int = 2
    llm_retry_base_delay: float = 0.5

    @classmethod
    def load(cls, *, env_file: str | Path | None = None, **overrides: object) -> Config:
        """Build a Config from env vars and a `.env` file, applying explicit overrides.

        `env_file` selects the dotenv file; None searches for a local `.env`.
        """
        file_values = dotenv_values(env_file) if env_file else dotenv_values()

        def get(key: str, default: str | None = None) -> str | None:
            return os.environ.get(key, file_values.get(key, default))

        values: dict[str, object] = {
            "anthropic_api_key": get("ANTHROPIC_API_KEY"),
            "log_level": get("VANI_LOG_LEVEL", "INFO"),
            "state_dir": get("VANI_STATE_DIR", ".vani_state"),
        }
        values.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**values)  # type: ignore[arg-type]
