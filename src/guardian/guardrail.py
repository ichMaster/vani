"""Minimal synchronous safety gate — a placeholder Guardian (architecture §12, §13).

Safety is checked synchronously before anything is shown; it is never deferred
(no rollback once spoken). This is a placeholder: a denylist-based pass/redirect
with a clear extension point. The full Guardian — rubric, wellbeing, child
safety, no-manipulation rule — arrives at v1 P4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

SAFE_REDIRECT = "I'm sorry, I can't help with that."


@dataclass
class GuardResult:
    """The verdict for one candidate reply."""

    outcome: str  # "pass" | "redirect" | "block"
    output: str  # the text to actually deliver (possibly redirected)
    reason: str = ""


@runtime_checkable
class Guardian(Protocol):
    """The synchronous gate every candidate reply passes before display."""

    def check(self, text: str) -> GuardResult: ...


class MinimalGuardian:
    """Placeholder gate: redirects replies containing a denylisted term, else passes.

    The denylist is the extension point; the full rubric replaces it at v1 P4.
    Defaults to empty (pure pass-through) for V1.
    """

    def __init__(self, denylist: list[str] | None = None, *, redirect: str = SAFE_REDIRECT) -> None:
        self._denylist = [term.lower() for term in (denylist or [])]
        self._redirect = redirect

    def check(self, text: str) -> GuardResult:
        lowered = text.lower()
        for term in self._denylist:
            if term in lowered:
                return GuardResult("redirect", self._redirect, f"matched denylist term: {term!r}")
        return GuardResult("pass", text)
