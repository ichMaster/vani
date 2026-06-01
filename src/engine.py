"""Transport-agnostic brain entry point (architecture §10).

Every surface (TUI, voice, server) drives the brain through this module; the
engine never imports transport code. Implemented in VANI-005.
"""

from __future__ import annotations


async def handle_turn(session_id: str, user_input: str) -> str:
    """Run one conversational turn for a session and return the reply.

    Placeholder stub — wired to the repository and llm in VANI-005.
    """
    raise NotImplementedError("engine.handle_turn is implemented in VANI-005")
