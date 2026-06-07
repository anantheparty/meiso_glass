from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Any

from .messages import Message, MessageType, Role
from .transport.udp import UDPTransport


@dataclass(frozen=True)
class EndpointClient:
    host: str
    port: int = 42001
    src_id: str = socket.gethostname()
    timeout_s: float = 2.0

    def send_command(self, msg_type: MessageType, payload: dict[str, Any] | None = None) -> Message | None:
        tx = UDPTransport("0.0.0.0", 0, timeout_s=self.timeout_s)
        try:
            msg = Message(
                msg_type=msg_type,
                src_role=Role.HOST,
                src_id=self.src_id,
                dst_role=Role.ENDPOINT,
                payload=payload or {"command": msg_type.value},
            )
            tx.send(msg, self.host, self.port)
            reply, _addr = tx.recv()
            return reply
        finally:
            tx.close()

    def ping(self) -> Message | None:
        return self.send_command(MessageType.PING)

    def health(self) -> Message | None:
        return self.send_command(MessageType.HEALTH)

    def start_video(self, video_host: str, video_port: int = 5000, encoder: str | None = None) -> Message | None:
        payload: dict[str, Any] = {
            "command": MessageType.START_VIDEO.value,
            "video_host": video_host,
            "video_port": video_port,
        }
        if encoder:
            payload["encoder"] = encoder
        return self.send_command(MessageType.START_VIDEO, payload)

    def stop_video(self) -> Message | None:
        return self.send_command(MessageType.STOP_VIDEO)

    def start_lowfi(self) -> Message | None:
        return self.send_command(MessageType.START_LOWFI)

    def stop_lowfi(self) -> Message | None:
        return self.send_command(MessageType.STOP_LOWFI)

    def power_state(self) -> Message | None:
        return self.send_command(MessageType.POWER_STATE)


@dataclass
class SDCRegistry:
    endpoints: dict[str, Message]

    def register_endpoint(self, heartbeat: Message) -> None:
        if heartbeat.msg_type != MessageType.HEARTBEAT or heartbeat.src_role != Role.ENDPOINT:
            raise ValueError("expected endpoint heartbeat")
        self.endpoints[heartbeat.src_id] = heartbeat
