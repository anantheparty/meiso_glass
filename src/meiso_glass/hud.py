from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HudElementType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    PANEL = "panel"
    PROGRESS = "progress"
    ANCHOR = "anchor"
    LAYOUT = "layout"


HUD_COMPOSITION_ORDER = ("scene_3d", "app_hud", "system_hud")
SYSTEM_HUD_TOPICS = ("battery", "network", "permission", "thermal", "error", "safety")


@dataclass(frozen=True)
class HudElement:
    element_id: str
    element_type: HudElementType
    layer: str = "app_hud"
    order: int = 0
    anchor: str = "center"
    lifetime_ms: int | None = None
    content: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.layer == "system_hud":
            raise ValueError("Host API cannot create system_hud elements")


@dataclass(frozen=True)
class HudUpdate:
    update_id: str
    session_id: str
    elements: tuple[HudElement, ...]
    strategy: str = "replace"

    def to_payload(self) -> dict[str, Any]:
        return {
            "updateId": self.update_id,
            "sessionId": self.session_id,
            "strategy": self.strategy,
            "compositionOrder": list(HUD_COMPOSITION_ORDER),
            "elements": [
                {
                    "elementId": item.element_id,
                    "type": item.element_type.value,
                    "layer": item.layer,
                    "order": item.order,
                    "anchor": item.anchor,
                    "lifetime": item.lifetime_ms,
                    "content": item.content,
                }
                for item in self.elements
            ],
        }
