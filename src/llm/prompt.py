"""Prompt assembly: a cached prefix + a fresh suffix (architecture §11).

The prefix is the stable system/identity block (the compiled canon, plus the
daily temperament from v1 P2) — it carries Anthropic `cache_control` so it is
served from the prompt cache across turns. The fresh suffix is the per-turn
message list, which is not cached. Caching the prefix is what keeps cost ~1x.
"""

from __future__ import annotations

from typing import Any

CACHE_CONTROL = {"type": "ephemeral"}


def build_system(identity: str, temperament: str | None = None) -> list[dict[str, Any]]:
    """Build the cached system prefix as Anthropic text blocks.

    `identity` is the compiled canon (stable). `temperament` is the optional
    daily block (wired at v1 P2); when present it is appended as a second cached
    block. Both stable blocks carry `cache_control`.
    """
    blocks: list[dict[str, Any]] = [
        {"type": "text", "text": identity, "cache_control": CACHE_CONTROL}
    ]
    if temperament:
        blocks.append({"type": "text", "text": temperament, "cache_control": CACHE_CONTROL})
    return blocks
