from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .interfaces import AdapterStatus, StreamConfig


@dataclass
class MockCameraAdapter:
    name: str = "fake_camera"
    running: bool = False
    last_config: StreamConfig | None = None

    def list_devices(self) -> list[dict[str, Any]]:
        return [{"id": self.name, "kind": "mock", "label": "Fake Camera"}]

    def list_formats(self, device_id: str | None = None) -> list[dict[str, Any]]:
        return [{"format": "RGB", "width": 1280, "height": 720, "fps": 30}]

    def start_stream(self, config: StreamConfig) -> AdapterStatus:
        self.running = True
        self.last_config = config
        return self.get_status()

    def stop_stream(self) -> AdapterStatus:
        self.running = False
        return self.get_status()

    def get_status(self) -> AdapterStatus:
        return AdapterStatus(self.name, available=True, running=self.running, details={"config": self.last_config})


@dataclass
class FakeIMU:
    name: str = "fake_imu"
    seq: int = 0

    def list_sensors(self) -> list[dict[str, Any]]:
        return [{"id": self.name, "kind": "imu", "axes": 6}]

    def read_sample(self, sensor_id: str) -> dict[str, Any] | None:
        if sensor_id != self.name:
            return None
        self.seq += 1
        return {
            "sensor_id": self.name,
            "seq": self.seq,
            "accel_mps2": [0.0, 0.0, 9.80665],
            "gyro_rps": [0.0, 0.0, 0.0],
        }

    def get_status(self) -> AdapterStatus:
        return AdapterStatus(self.name, available=True, details={"seq": self.seq})


@dataclass
class FakePowerMonitor:
    name: str = "fake_power"
    mode: str = "debug"

    def get_state(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "battery_percent": 100.0,
            "rails_mw": {"endpoint": 250.0, "sensors": 12.0, "radio": 0.5},
        }

    def set_mode(self, mode: str) -> AdapterStatus:
        self.mode = mode
        return self.get_status()

    def get_status(self) -> AdapterStatus:
        return AdapterStatus(self.name, available=True, running=True, details={"mode": self.mode})


@dataclass
class FakeLowfiTelemetryGenerator:
    source_id: int = 1
    seq: int = 0

    def next_event(self) -> dict[str, Any]:
        self.seq += 1
        return {
            "type": "lowfi_vision",
            "source_id": self.source_id,
            "seq": self.seq,
            "roi": {"x": 0, "y": 0, "w": 64, "h": 64},
            "tile_stats": [{"tile": 0, "mean": 12, "motion": 0}],
        }


@dataclass
class FakeFpgaPacketGenerator:
    seq: int = 0

    def next_packet(self) -> bytes:
        self.seq += 1
        return f"fpga:{self.seq}".encode("ascii")


@dataclass
class FakeRadioLink:
    name: str = "fake_radio"
    tx_queue: deque[bytes] = field(default_factory=deque)

    def send_packet(self, payload: bytes) -> AdapterStatus:
        self.tx_queue.append(payload)
        return self.get_status()

    def receive_packet(self, timeout_s: float = 0.0) -> bytes | None:
        if not self.tx_queue:
            return None
        return self.tx_queue.popleft()

    def get_status(self) -> AdapterStatus:
        return AdapterStatus(self.name, available=True, running=True, details={"queued": len(self.tx_queue)})
