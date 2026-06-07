from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .timebase import monotonic_ns, realtime_ns

PROTOCOL_MAGIC = "MEISOGLASS"
PROTOCOL_VERSION = 1


class Role(str, Enum):
    ENDPOINT = "endpoint"
    SDC = "sdc"
    HOST = "host"


class MessageType(str, Enum):
    HEARTBEAT = "heartbeat"
    PING = "ping"
    HEALTH = "health"
    START_VIDEO = "start_video"
    STOP_VIDEO = "stop_video"
    START_LOWFI = "start_lowfi"
    STOP_LOWFI = "stop_lowfi"
    POWER_STATE = "power_state"
    SENSOR_EVENT = "sensor_event"
    TELEMETRY_PACKET = "telemetry_packet"
    DISPLAY_SESSION = "display_session"
    FIRMWARE_STATUS = "firmware_status"
    LOG_EVENT = "log_event"
    CRASH_REPORT = "crash_report"
    COMMAND = "command"
    ACK = "ack"
    ERROR = "error"
    EVENT = "event"
    TIME_SYNC = "time_sync"


@dataclass
class Message:
    msg_type: MessageType
    src_role: Role
    src_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    seq: int = 0
    dst_role: Role | None = None
    realtime_ns: int = field(default_factory=realtime_ns)
    monotonic_ns: int = field(default_factory=monotonic_ns)
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_magic: str = PROTOCOL_MAGIC
    protocol_version: int = PROTOCOL_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_magic": self.protocol_magic,
            "protocol_version": self.protocol_version,
            "msg_id": self.msg_id,
            "msg_type": self.msg_type.value,
            "src_role": self.src_role.value,
            "dst_role": self.dst_role.value if self.dst_role else None,
            "src_id": self.src_id,
            "seq": self.seq,
            "realtime_ns": self.realtime_ns,
            "monotonic_ns": self.monotonic_ns,
            "payload": self.payload,
        }

    def to_bytes(self) -> bytes:
        return json.dumps(self.to_dict(), separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @staticmethod
    def from_bytes(data: bytes) -> "Message":
        obj = json.loads(data.decode("utf-8"))
        if obj.get("protocol_magic") != PROTOCOL_MAGIC:
            raise ValueError("invalid protocol magic")
        if int(obj.get("protocol_version", -1)) != PROTOCOL_VERSION:
            raise ValueError("unsupported protocol version")
        return Message(
            msg_type=MessageType(obj["msg_type"]),
            src_role=Role(obj["src_role"]),
            dst_role=Role(obj["dst_role"]) if obj.get("dst_role") else None,
            src_id=obj["src_id"],
            seq=int(obj.get("seq", 0)),
            realtime_ns=int(obj.get("realtime_ns", 0)),
            monotonic_ns=int(obj.get("monotonic_ns", 0)),
            msg_id=obj.get("msg_id", ""),
            payload=obj.get("payload", {}),
        )


def ack_for(
    src: Message,
    src_role: Role,
    src_id: str,
    ok: bool = True,
    extra: dict[str, Any] | None = None,
) -> Message:
    payload = {
        "ok": ok,
        "ack_msg_id": src.msg_id,
        "ack_msg_type": src.msg_type.value,
    }
    if extra:
        payload.update(extra)
    return Message(
        msg_type=MessageType.ACK if ok else MessageType.ERROR,
        src_role=src_role,
        src_id=src_id,
        dst_role=src.src_role,
        seq=src.seq,
        payload=payload,
    )
