from __future__ import annotations

from dataclasses import dataclass, field

from meiso_glass.adapters.mock import FakeIMU, FakeLowfiTelemetryGenerator, FakePowerMonitor, FakeRadioLink, MockCameraAdapter
from meiso_glass.messages import Message, MessageType, Role
from meiso_glass.telemetry.packet import TelemetryPacket, TelemetryPacketType
from meiso_glass.timebase import monotonic_ns


@dataclass
class MockEndpoint:
    device_id: str = "mock-endpoint-001"
    camera: MockCameraAdapter = field(default_factory=MockCameraAdapter)
    imu: FakeIMU = field(default_factory=FakeIMU)
    power: FakePowerMonitor = field(default_factory=FakePowerMonitor)
    lowfi: FakeLowfiTelemetryGenerator = field(default_factory=FakeLowfiTelemetryGenerator)
    radio: FakeRadioLink = field(default_factory=FakeRadioLink)
    seq: int = 0

    def heartbeat(self) -> Message:
        self.seq += 1
        return Message(
            msg_type=MessageType.HEARTBEAT,
            src_role=Role.ENDPOINT,
            dst_role=Role.SDC,
            src_id=self.device_id,
            seq=self.seq,
            payload={"power": self.power.get_state(), "camera": self.camera.get_status().details},
        )

    def lowfi_packet(self) -> TelemetryPacket:
        event = self.lowfi.next_event()
        return TelemetryPacket(
            packet_type=TelemetryPacketType.LOWFI_VISION,
            seq=event["seq"],
            timestamp_us=monotonic_ns() // 1000,
            source_id=int(event["source_id"]),
            payload=str(event).encode("utf-8"),
        )


@dataclass
class MockSDC:
    device_id: str = "mock-sdc-001"
    received: list[Message] = field(default_factory=list)

    def receive(self, msg: Message) -> None:
        self.received.append(msg)

    def ping(self, endpoint_id: str) -> Message:
        return Message(
            msg_type=MessageType.PING,
            src_role=Role.SDC,
            dst_role=Role.ENDPOINT,
            src_id=self.device_id,
            payload={"target": endpoint_id, "command": "ping"},
        )
