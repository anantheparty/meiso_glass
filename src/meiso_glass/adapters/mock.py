from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from ..power import MeasurementSource, PowerCostPoint, PowerProfile
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

    def get_power_profile(self) -> PowerProfile:
        return PowerProfile(
            profile_id=f"/power/{self.name}",
            adapter_id=self.name,
            family="camera",
            supported_levels=[0, 32, 64, 128],
            default_level=0,
            cost_points=[
                PowerCostPoint(level=0, adapter_state="off", confidence_level_u8=255),
                PowerCostPoint(
                    level=32,
                    adapter_state="active",
                    settings={"output_form": "event"},
                    expected_mw=2.0,
                    measurement_source=MeasurementSource.DECLARED_ONLY,
                    confidence_level_u8=32,
                ),
                PowerCostPoint(
                    level=64,
                    adapter_state="active",
                    settings={"output_form": "tile"},
                    expected_mw=8.0,
                    measurement_source=MeasurementSource.DECLARED_ONLY,
                    confidence_level_u8=32,
                ),
                PowerCostPoint(
                    level=128,
                    adapter_state="active",
                    settings={"output_form": "compressed_stream"},
                    expected_mw=80.0,
                    measurement_source=MeasurementSource.DECLARED_ONLY,
                    confidence_level_u8=32,
                ),
            ],
            unknowns=["mock values are not physical measurements"],
        )

    def start_stream(self, config: StreamConfig) -> AdapterStatus:
        self.running = True
        self.last_config = config
        return self.get_status()

    def stop_stream(self) -> AdapterStatus:
        self.running = False
        return self.get_status()

    def get_status(self) -> AdapterStatus:
        level = 128 if self.running else 0
        profile = self.get_power_profile()
        return AdapterStatus(
            self.name,
            available=True,
            running=self.running,
            current_level_u8=level,
            power_profile_ref=profile.profile_id,
            details={"config": self.last_config},
        )


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

    def get_power_profile(self) -> PowerProfile:
        return PowerProfile(
            profile_id=f"/power/{self.name}",
            adapter_id=self.name,
            family="sensor",
            supported_levels=[0, 32, 64],
            default_level=32,
            cost_points=[
                PowerCostPoint(level=0, adapter_state="off", confidence_level_u8=255),
                PowerCostPoint(level=32, adapter_state="active", expected_mw=1.0, confidence_level_u8=32),
                PowerCostPoint(level=64, adapter_state="active", expected_mw=4.0, confidence_level_u8=32),
            ],
            unknowns=["mock values are not physical measurements"],
        )

    def get_status(self) -> AdapterStatus:
        profile = self.get_power_profile()
        return AdapterStatus(
            self.name,
            available=True,
            current_level_u8=32,
            power_profile_ref=profile.profile_id,
            details={"seq": self.seq},
        )


@dataclass
class FakePowerMonitor:
    name: str = "fake_power"
    mode: str = "debug"

    def get_state(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "battery_percent": 100.0,
            "rails_mw": {"edge": 250.0, "sensors": 12.0, "radio": 0.5},
        }

    def get_power_profile(self) -> PowerProfile:
        return PowerProfile(
            profile_id=f"/power/{self.name}",
            adapter_id=self.name,
            family="power",
            supported_levels=[0, 16, 64],
            default_level=16,
            cost_points=[
                PowerCostPoint(level=0, adapter_state="off", confidence_level_u8=255),
                PowerCostPoint(level=16, adapter_state="active", settings={"sampling": "coarse"}, expected_mw=0.1),
                PowerCostPoint(level=64, adapter_state="active", settings={"sampling": "session"}, expected_mw=1.0),
            ],
            unknowns=["monitor sampling cost is estimated"],
        )

    def set_mode(self, mode: str) -> AdapterStatus:
        self.mode = mode
        return self.get_status()

    def get_status(self) -> AdapterStatus:
        profile = self.get_power_profile()
        return AdapterStatus(
            self.name,
            available=True,
            running=True,
            current_level_u8=16,
            power_profile_ref=profile.profile_id,
            details={"mode": self.mode},
        )


@dataclass
class FakeLocalResultGenerator:
    source_id: int = 1
    seq: int = 0

    def next_event(self) -> dict[str, Any]:
        self.seq += 1
        return {
            "type": "local_result",
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

    def get_power_profile(self) -> PowerProfile:
        return PowerProfile(
            profile_id=f"/power/{self.name}",
            adapter_id=self.name,
            family="radio",
            supported_levels=[0, 32, 64, 96],
            default_level=32,
            cost_points=[
                PowerCostPoint(level=0, adapter_state="off", confidence_level_u8=255),
                PowerCostPoint(
                    level=32,
                    adapter_state="active",
                    settings={"link_role": "wake_listen"},
                    expected_mw=0.2,
                ),
                PowerCostPoint(level=64, adapter_state="active", settings={"link_role": "control"}, expected_mw=1.5),
                PowerCostPoint(
                    level=96,
                    adapter_state="active",
                    settings={"link_role": "telemetry_burst"},
                    expected_mw=8.0,
                ),
            ],
            unknowns=["airtime model is not calibrated"],
        )

    def get_status(self) -> AdapterStatus:
        profile = self.get_power_profile()
        return AdapterStatus(
            self.name,
            available=True,
            running=True,
            current_level_u8=64 if self.tx_queue else 32,
            power_profile_ref=profile.profile_id,
            details={"queued": len(self.tx_queue)},
        )
