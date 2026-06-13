from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


def clamp_u8(value: int) -> int:
    if not 0 <= value <= 255:
        raise ValueError(f"u8 value out of range: {value}")
    return value


def require_semantic_path(value: str) -> str:
    if not value.startswith("/"):
        raise ValueError(f"semantic path must start with '/': {value}")
    if "//" in value or value.endswith("/"):
        raise ValueError(f"invalid semantic path: {value}")
    return value


@dataclass(frozen=True)
class Metadata:
    id: str
    revision: str = "v0"
    owner_role: str = "host"
    device_id: str | None = None
    instance_id: str | None = None
    profile_id: str | None = None
    created_at_realtime_ns: int | None = None
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Condition:
    type: str
    status: bool | None
    reason: str = ""
    message: str = ""
    observed_generation: int = 0
    last_transition_time_ns: int | None = None


@dataclass(frozen=True)
class StructuredError:
    code: str
    message: str
    retryable: bool = False
    severity: str = "error"
    related_session_id: str | None = None
    related_capability_id: str | None = None
    failed_state: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
