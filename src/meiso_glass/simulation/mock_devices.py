from __future__ import annotations

from dataclasses import dataclass, field

from meiso_glass.adapters.mock import (
    FakeIMU,
    FakeLocalResultGenerator,
    FakePowerMonitor,
    FakeRadioLink,
    MockCameraAdapter,
)
from meiso_glass.protocol import MeisoChannel, MeisoMessage, MeisoMessageType
from meiso_glass.telemetry.packet import TelemetryPacket, TelemetryPacketType
from meiso_glass.timebase import monotonic_ns


@dataclass
class MockEdge:
    device_id: str = "mock-edge-001"
    camera: MockCameraAdapter = field(default_factory=MockCameraAdapter)
    imu: FakeIMU = field(default_factory=FakeIMU)
    power: FakePowerMonitor = field(default_factory=FakePowerMonitor)
    local_result: FakeLocalResultGenerator = field(default_factory=FakeLocalResultGenerator)
    radio: FakeRadioLink = field(default_factory=FakeRadioLink)
    seq: int = 0

    def heartbeat(self) -> MeisoMessage:
        self.seq += 1
        return MeisoMessage.make(
            message_type=MeisoMessageType.HEARTBEAT,
            channel=MeisoChannel.HIGH_RELIABLE,
            session_id=self.device_id,
            sequence=self.seq,
            payload={"power": self.power.get_state(), "camera": self.camera.get_status().details},
        )

    def local_result_packet(self) -> TelemetryPacket:
        event = self.local_result.next_event()
        return TelemetryPacket(
            packet_type=TelemetryPacketType.LOCAL_RESULT,
            seq=event["seq"],
            timestamp_us=monotonic_ns() // 1000,
            source_id=int(event["source_id"]),
            payload=str(event).encode("utf-8"),
        )


@dataclass
class MockHost:
    device_id: str = "mock-host-001"
    received: list[MeisoMessage] = field(default_factory=list)

    def receive(self, msg: MeisoMessage) -> None:
        self.received.append(msg)

    def status_request(self, edge_id: str) -> MeisoMessage:
        return MeisoMessage.make(
            message_type=MeisoMessageType.EDGE_STATUS,
            channel=MeisoChannel.HIGH_RELIABLE,
            session_id=self.device_id,
            sequence=1,
            payload={"target": edge_id},
        )
