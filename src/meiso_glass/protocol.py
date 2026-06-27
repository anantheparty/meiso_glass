from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .timebase import monotonic_ns

PROTOCOL_VERSION = 1
PROTOCOL_MAGIC = "MEISO"


class StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class MeisoRole(StringEnum):
    HOST = "host"
    EDGE = "edge"


class MeisoChannel(StringEnum):
    HIGH_RELIABLE = "high_reliable"
    LATEST_WINS = "latest_wins"
    LOW_RELIABLE = "low_reliable"
    LOW_POWER = "low_power"


class MeisoMessageType(StringEnum):
    HEARTBEAT = "heartbeat"
    ACK = "ack"
    ERROR = "error"
    TIME_SYNC = "time_sync"
    FEATURE_REQUEST = "feature_request"
    FEATURE_RESPONSE = "feature_response"
    FEATURE_RELEASE = "feature_release"
    SCENE_SNAPSHOT = "scene_snapshot"
    SCENE_DELTA = "scene_delta"
    HUD_UPDATE = "hud_update"
    SENSOR_SUBSCRIBE = "sensor_subscribe"
    SENSOR_UNSUBSCRIBE = "sensor_unsubscribe"
    SENSOR_SAMPLE = "sensor_sample"
    TELEMETRY_REPORT = "telemetry_report"
    ASSET_REQUEST = "asset_request"
    ASSET_CHUNK = "asset_chunk"
    HOST_STATUS = "host_status"
    EDGE_STATUS = "edge_status"


HEADER_WIRE_KEYS = (
    "protocolVersion",
    "sessionId",
    "messageType",
    "channel",
    "sequence",
    "sourceTimestamp",
    "payloadLength",
    "flags",
)


def canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


@dataclass(frozen=True)
class MeisoMessageHeader:
    protocol_version: int
    session_id: str
    message_type: MeisoMessageType
    channel: MeisoChannel
    sequence: int
    source_timestamp_ns: int
    payload_length: int
    flags: int = 0

    def to_wire(self) -> dict[str, Any]:
        return {
            "protocolVersion": self.protocol_version,
            "sessionId": self.session_id,
            "messageType": self.message_type.value,
            "channel": self.channel.value,
            "sequence": self.sequence,
            "sourceTimestamp": self.source_timestamp_ns,
            "payloadLength": self.payload_length,
            "flags": self.flags,
        }

    @classmethod
    def from_wire(cls, data: dict[str, Any]) -> MeisoMessageHeader:
        missing = [key for key in HEADER_WIRE_KEYS if key not in data]
        if missing:
            raise ValueError(f"missing Meiso header fields: {missing}")
        version = int(data["protocolVersion"])
        if version != PROTOCOL_VERSION:
            raise ValueError(f"unsupported Meiso protocol version: {version}")
        return cls(
            protocol_version=version,
            session_id=str(data["sessionId"]),
            message_type=MeisoMessageType(str(data["messageType"])),
            channel=MeisoChannel(str(data["channel"])),
            sequence=int(data["sequence"]),
            source_timestamp_ns=int(data["sourceTimestamp"]),
            payload_length=int(data["payloadLength"]),
            flags=int(data["flags"]),
        )


@dataclass(frozen=True)
class MeisoMessage:
    header: MeisoMessageHeader
    payload: dict[str, Any] = field(default_factory=dict)
    magic: str = PROTOCOL_MAGIC

    @classmethod
    def make(
        cls,
        message_type: MeisoMessageType,
        channel: MeisoChannel,
        session_id: str,
        sequence: int,
        payload: dict[str, Any] | None = None,
        flags: int = 0,
        source_timestamp_ns: int | None = None,
    ) -> MeisoMessage:
        body = payload or {}
        header = MeisoMessageHeader(
            protocol_version=PROTOCOL_VERSION,
            session_id=session_id,
            message_type=message_type,
            channel=channel,
            sequence=sequence,
            source_timestamp_ns=source_timestamp_ns if source_timestamp_ns is not None else monotonic_ns(),
            payload_length=len(canonical_payload_bytes(body)),
            flags=flags,
        )
        return cls(header=header, payload=body)

    def to_dict(self) -> dict[str, Any]:
        return {
            "magic": self.magic,
            "header": self.header.to_wire(),
            "payload": self.payload,
        }

    def to_bytes(self) -> bytes:
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> MeisoMessage:
        obj = json.loads(data.decode("utf-8"))
        if obj.get("magic") != PROTOCOL_MAGIC:
            raise ValueError("invalid Meiso protocol magic")
        if "header" not in obj or not isinstance(obj["header"], dict):
            raise ValueError("missing Meiso message header")
        payload = obj.get("payload", {})
        if not isinstance(payload, dict):
            raise ValueError("Meiso message payload must be an object")
        header = MeisoMessageHeader.from_wire(obj["header"])
        actual_length = len(canonical_payload_bytes(payload))
        if actual_length != header.payload_length:
            raise ValueError("Meiso payload length mismatch")
        return cls(header=header, payload=payload)


def ack_for(src: MeisoMessage, payload: dict[str, Any] | None = None) -> MeisoMessage:
    return MeisoMessage.make(
        message_type=MeisoMessageType.ACK,
        channel=MeisoChannel.HIGH_RELIABLE,
        session_id=src.header.session_id,
        sequence=src.header.sequence,
        payload={
            "ackMessageType": src.header.message_type.value,
            "ok": True,
            **(payload or {}),
        },
    )


Message = MeisoMessage
MessageType = MeisoMessageType
Role = MeisoRole
