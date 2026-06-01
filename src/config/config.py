"""Configuration loader.

Precedence: explicit overrides > environment variables > defaults. Config is
instantiated per run (no global mutable cache).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Runtime configuration for a Vani session."""

    anthropic_api_key: str | None = None
    log_level: str = "INFO"
    state_dir: str = ".vani_state"
    opus_model: str = "claude-opus-4-8"
    haiku_model: str = "claude-haiku-4-5-20251001"

    @classmethod
    def load(cls, **overrides: object) -> Config:
        """Build a Config from env vars, applying any explicit overrides."""
        values: dict[str, object] = {
            "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY"),
            "log_level": os.environ.get("VANI_LOG_LEVEL", "INFO"),
            "state_dir": os.environ.get("VANI_STATE_DIR", ".vani_state"),
        }
        values.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**values)  # type: ignore[arg-type]
