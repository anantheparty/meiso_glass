from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SensorType(str, Enum):
    CAMERA = "camera"
    AUDIO = "audio"
    EYE = "eye"
    IMU = "imu"
    LOCAL_RESULT = "local_result"


@dataclass(frozen=True)
class SensorSubscription:
    subscription_id: str
    sensor: SensorType
    rate_hz: float | None = None
    resolution: tuple[int, int] | None = None
    encoding: str = "none"
    data_type: str = "raw"
    max_duration_ms: int | None = None
    params: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "subscriptionId": self.subscription_id,
            "sensor": self.sensor.value,
            "rateHz": self.rate_hz,
            "resolution": self.resolution,
            "encoding": self.encoding,
            "dataType": self.data_type,
            "maxDuration": self.max_duration_ms,
            "params": self.params,
        }


@dataclass(frozen=True)
class SensorSample:
    subscription_id: str
    sensor: SensorType
    sequence: int
    timestamp_ns: int
    payload: dict[str, Any]
