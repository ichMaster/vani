"""Confidence — the cross-cutting attribute on inferred state (spec §9.7).

Almost everything the assistant infers about the user or the situation carries a
confidence in [0, 1] that rises with confirmation and decays over time without
it. The canon and the hard invariants carry NO confidence — they are a stable
foundation, not hypotheses. The rise/decay equations are formalized at v1 P3 /
refinement #5; P0 only scaffolds the field and a clamped wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


def clamp(value: float) -> float:
    """Clamp a confidence into the [0, 1] range."""
    return max(0.0, min(1.0, value))


@dataclass
class Confident(Generic[T]):
    """A value paired with a confidence in [0, 1]."""

    value: T
    confidence: float = 0.0

    def __post_init__(self) -> None:
        self.confidence = clamp(self.confidence)
