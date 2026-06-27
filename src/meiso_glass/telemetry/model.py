from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TelemetryMetric(str, Enum):
    TEMPERATURE = "temperature"
    BATTERY = "battery"
    FPS = "fps"
    DROPPED_FRAMES = "dropped_frames"
    NETWORK_LATENCY = "network_latency"
    PACKET_LOSS = "packet_loss"
    CACHE = "cache"
    ERROR = "error"


REQUIRED_TELEMETRY_METRICS = tuple(metric.value for metric in TelemetryMetric)


@dataclass(frozen=True)
class TelemetryReport:
    report_id: str
    timestamp_ns: int
    metrics: dict[str, Any] = field(default_factory=dict)

    def missing_required_metrics(self) -> tuple[str, ...]:
        return tuple(metric for metric in REQUIRED_TELEMETRY_METRICS if metric not in self.metrics)

    def to_payload(self) -> dict[str, Any]:
        return {
            "reportId": self.report_id,
            "timestamp": self.timestamp_ns,
            "metrics": self.metrics,
        }
