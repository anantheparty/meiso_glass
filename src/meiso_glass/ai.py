from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any

from .protocol import MeisoChannel
from .timebase import monotonic_ns


class AiToolKind(str, Enum):
    DEVICE_FEATURE = "device_feature"
    SCENE = "scene"
    HUD = "hud"
    SENSOR = "sensor"
    TELEMETRY = "telemetry"
    CONTEXT_QUERY = "context_query"
    STATE_QUERY = "state_query"


class AiToolResultStatus(str, Enum):
    OK = "ok"
    REJECTED = "rejected"
    ERROR = "error"


class ContextKind(str, Enum):
    SESSION = "session"
    EDGE = "edge"
    SCENE = "scene"
    HUD = "hud"
    SENSOR = "sensor"
    TELEMETRY = "telemetry"
    POLICY = "policy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    kind: AiToolKind
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    channel: MeisoChannel = MeisoChannel.HIGH_RELIABLE
    idempotent: bool = True
    requires_confirmation: bool = False
    lease_required: bool = False
    timeout_ms: int | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.startswith("meiso."):
            raise ValueError("AI tool names must use the meiso. prefix")
        if self.timeout_ms is not None and self.timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str | None = None
    context_refs: tuple[str, ...] = ()
    state_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.call_id:
            raise ValueError("call_id is required")
        if not self.tool_name.startswith("meiso."):
            raise ValueError("tool_name must use the meiso. prefix")


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    status: AiToolResultStatus
    payload: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def __post_init__(self) -> None:
        if self.status != AiToolResultStatus.OK and not self.error:
            raise ValueError("non-ok tool results must include error")


@dataclass(frozen=True)
class ContextItem:
    context_id: str
    kind: ContextKind
    content: dict[str, Any]
    priority: int = 0
    expires_at_ns: int | None = None
    source: str = "sdk"

    def expired(self, now_ns: int | None = None) -> bool:
        if self.expires_at_ns is None:
            return False
        return (now_ns if now_ns is not None else monotonic_ns()) >= self.expires_at_ns


@dataclass(frozen=True)
class ContextPacket:
    session_id: str
    items: tuple[ContextItem, ...]
    state_refs: tuple[str, ...] = ()
    tool_names: tuple[str, ...] = ()

    def compact(self, max_items: int) -> ContextPacket:
        if max_items <= 0:
            raise ValueError("max_items must be positive")
        ordered = sorted(self.items, key=lambda item: item.priority, reverse=True)
        return ContextPacket(
            session_id=self.session_id,
            items=tuple(ordered[:max_items]),
            state_refs=self.state_refs,
            tool_names=self.tool_names,
        )


@dataclass(frozen=True)
class StateSnapshot:
    state_id: str
    version: int
    values: Mapping[str, Any]
    timestamp_ns: int = field(default_factory=monotonic_ns)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


@dataclass(frozen=True)
class StatePatch:
    state_id: str
    base_version: int
    set_values: dict[str, Any] = field(default_factory=dict)
    delete_keys: tuple[str, ...] = ()
    patch_id: str = ""

    def __post_init__(self) -> None:
        if self.base_version < 0:
            raise ValueError("base_version must be non-negative")


@dataclass
class ToolRegistry:
    _tools: dict[str, ToolSpec] = field(default_factory=dict)

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"duplicate AI tool: {spec.name}")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        return self._tools[name]

    def list_tools(self) -> tuple[ToolSpec, ...]:
        return tuple(self._tools[name] for name in sorted(self._tools))


@dataclass
class ContextStore:
    _items: dict[str, ContextItem] = field(default_factory=dict)

    def put(self, item: ContextItem) -> None:
        self._items[item.context_id] = item

    def packet(
        self,
        session_id: str,
        tool_names: tuple[str, ...] = (),
        state_refs: tuple[str, ...] = (),
        now_ns: int | None = None,
    ) -> ContextPacket:
        active = tuple(item for item in self._items.values() if not item.expired(now_ns))
        return ContextPacket(session_id=session_id, items=active, state_refs=state_refs, tool_names=tool_names)


@dataclass
class StateStore:
    _snapshots: dict[str, StateSnapshot] = field(default_factory=dict)

    def snapshot(self, state_id: str) -> StateSnapshot:
        return self._snapshots.get(state_id, StateSnapshot(state_id=state_id, version=0, values={}))

    def apply(self, patch: StatePatch) -> StateSnapshot:
        current = self.snapshot(patch.state_id)
        if current.version != patch.base_version:
            raise ValueError("state patch base_version mismatch")
        next_values = dict(current.values)
        for key in patch.delete_keys:
            next_values.pop(key, None)
        next_values.update(patch.set_values)
        updated = StateSnapshot(state_id=patch.state_id, version=current.version + 1, values=next_values)
        self._snapshots[patch.state_id] = updated
        return updated


@dataclass
class MeisoAiApi:
    session_id: str
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    context: ContextStore = field(default_factory=ContextStore)
    state: StateStore = field(default_factory=StateStore)

    def register_default_tools(self) -> None:
        defaults = [
            ToolSpec(
                name="meiso.device.request_feature",
                kind=AiToolKind.DEVICE_FEATURE,
                description="Request an Edge feature with lease and policy handling.",
                lease_required=True,
            ),
            ToolSpec(
                name="meiso.scene.submit_snapshot",
                kind=AiToolKind.SCENE,
                description="Submit an immutable scene snapshot by asset references.",
                channel=MeisoChannel.LATEST_WINS,
            ),
            ToolSpec(
                name="meiso.hud.update",
                kind=AiToolKind.HUD,
                description="Update App HUD without writing System HUD.",
            ),
            ToolSpec(
                name="meiso.sensor.subscribe",
                kind=AiToolKind.SENSOR,
                description="Subscribe to Edge sensor data or local processed results.",
            ),
            ToolSpec(
                name="meiso.telemetry.report",
                kind=AiToolKind.TELEMETRY,
                description="Read or emit telemetry metrics.",
                channel=MeisoChannel.LATEST_WINS,
            ),
        ]
        for spec in defaults:
            if spec.name not in self.tools._tools:
                self.tools.register(spec)

    def build_context_packet(self, max_items: int | None = None) -> ContextPacket:
        packet = self.context.packet(
            session_id=self.session_id,
            tool_names=tuple(tool.name for tool in self.tools.list_tools()),
            state_refs=tuple(sorted(self.state._snapshots)),
        )
        return packet.compact(max_items) if max_items is not None else packet
