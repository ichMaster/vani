"""In-memory pipeline contracts (architecture §9).

`PerceptionResult` is produced by the perception step (Haiku); `TurnPlan` is
produced by the decision step (deterministic code). Both are transient per-turn
objects (not persisted documents), serializable so they can be logged and
validated against `architecture/schemas/{perception_result,turn_plan}.schema.json`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.contracts.confidence import Confident, clamp

Document = dict[str, Any]

# Allowed values, mirrored from the JSON Schemas.
MODALITIES = ("joke", "serious", "hypothetical", "sarcasm", "quotation", "exaggeration")
ROUTES = ("simple", "deep")
STRATEGIES = (
    "active_listening",
    "empathy",
    "fun_facts",
    "execution",
    "informational",
    "coaching",
    "companionable",
    "recap",
    "encouragement",
    "proactive_prompt",
)
LINE_ACTIONS = ("none", "pick_up_loop", "follow_up", "ask_curiosity_question", "converge")


@dataclass
class Emotion:
    """Non-diagnostic affect read (perception_result.schema.json -> emotion)."""

    valence: float = 0.0  # -1..1
    arousal: float = 0.0  # 0..1
    confidence: float = 0.0

    def to_dict(self) -> Document:
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "confidence": clamp(self.confidence),
        }


@dataclass
class PerceptionResult:
    """Output of the perception step (Haiku) — reads the message, does not reply.

    For v0 P1 only `topic` and `intent` are populated by the model; `emotion`
    and `modality` are present but low-confidence placeholders until v0 P3.
    """

    topic: Confident[str]
    intent: Confident[str]
    emotion: Emotion = field(default_factory=Emotion)
    modality: Confident[str] = field(default_factory=lambda: Confident("serious", 0.0))
    style_signals: Document = field(default_factory=dict)
    open_loop_matches: list[Document] = field(default_factory=list)

    def to_dict(self) -> Document:
        data: Document = {
            "topic": {"value": self.topic.value, "confidence": self.topic.confidence},
            "intent": {"value": self.intent.value, "confidence": self.intent.confidence},
            "emotion": self.emotion.to_dict(),
            "modality": {"value": self.modality.value, "confidence": self.modality.confidence},
        }
        if self.style_signals:
            data["style_signals"] = self.style_signals
        if self.open_loop_matches:
            data["open_loop_matches"] = self.open_loop_matches
        return data

    @classmethod
    def from_dict(cls, data: Document) -> PerceptionResult:
        emotion_raw = data.get("emotion", {})
        modality_raw = data.get("modality", {"value": "serious", "confidence": 0.0})
        return cls(
            topic=Confident(data["topic"]["value"], data["topic"].get("confidence", 0.0)),
            intent=Confident(data["intent"]["value"], data["intent"].get("confidence", 0.0)),
            emotion=Emotion(
                valence=emotion_raw.get("valence", 0.0),
                arousal=emotion_raw.get("arousal", 0.0),
                confidence=emotion_raw.get("confidence", 0.0),
            ),
            modality=Confident(modality_raw["value"], modality_raw.get("confidence", 0.0)),
            style_signals=data.get("style_signals", {}),
            open_loop_matches=data.get("open_loop_matches", []),
        )


@dataclass
class TurnPlan:
    """Output of the decision step (deterministic) — who/how/where for this turn.

    For v0 P1 the planner populates `route` and a minimal plan; richer fields
    (facet weights, strategy modifiers, line actions) fill in at later phases.
    """

    route: str  # "simple" | "deep"
    strategy: str = "companionable"
    facet_weights: dict[str, float] = field(default_factory=dict)
    modifier: str | None = None
    intent: str | None = None
    target_length: str | None = None
    tone: str | None = None
    filler: str | None = None
    confirmation: bool = False
    conversation_line_action: str = "none"
    self_check: bool = False

    def to_dict(self) -> Document:
        data: Document = {
            "facet_weights": self.facet_weights,
            "strategy": self.strategy,
            "route": self.route,
            "confirmation": self.confirmation,
            "conversation_line_action": self.conversation_line_action,
            "self_check": self.self_check,
        }
        for key in ("modifier", "intent", "target_length", "tone", "filler"):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data

    @classmethod
    def from_dict(cls, data: Document) -> TurnPlan:
        return cls(
            route=data["route"],
            strategy=data.get("strategy", "companionable"),
            facet_weights=data.get("facet_weights", {}),
            modifier=data.get("modifier"),
            intent=data.get("intent"),
            target_length=data.get("target_length"),
            tone=data.get("tone"),
            filler=data.get("filler"),
            confirmation=data.get("confirmation", False),
            conversation_line_action=data.get("conversation_line_action", "none"),
            self_check=data.get("self_check", False),
        )
