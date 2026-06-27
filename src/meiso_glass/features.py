from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .timebase import monotonic_ns


class StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class FeatureName(StringEnum):
    CAMERA = "camera"
    MICROPHONE = "microphone"
    EYE = "eye"
    IMU = "imu"
    DISPLAY = "display"
    NETWORK = "network"
    RENDER = "render"


class FeaturePriority(StringEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    SAFETY = "safety"


class FeatureResponseStatus(StringEnum):
    ACCEPTED = "accepted"
    DEGRADED = "degraded"
    REJECTED = "rejected"


class PermissionState(StringEnum):
    UNKNOWN = "unknown"
    GRANTED = "granted"
    DENIED = "denied"


HIGH_POWER_FEATURES = frozenset({FeatureName.CAMERA, FeatureName.MICROPHONE, FeatureName.EYE})


@dataclass(frozen=True)
class FeatureRequest:
    feature: FeatureName
    mode: str
    params: dict[str, Any] = field(default_factory=dict)
    priority: FeaturePriority = FeaturePriority.NORMAL
    lease_time_ms: int = 0
    request_id: str = ""

    def __post_init__(self) -> None:
        if self.lease_time_ms < 0:
            raise ValueError("lease_time_ms must be non-negative")
        if not self.request_id:
            raise ValueError("request_id is required")

    def to_payload(self) -> dict[str, Any]:
        return {
            "feature": self.feature.value,
            "mode": self.mode,
            "params": self.params,
            "priority": self.priority.value,
            "leaseTime": self.lease_time_ms,
            "requestId": self.request_id,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> FeatureRequest:
        return cls(
            feature=FeatureName(str(payload["feature"])),
            mode=str(payload["mode"]),
            params=dict(payload.get("params", {})),
            priority=FeaturePriority(str(payload.get("priority", FeaturePriority.NORMAL.value))),
            lease_time_ms=int(payload.get("leaseTime", 0)),
            request_id=str(payload["requestId"]),
        )


@dataclass(frozen=True)
class FeatureResponse:
    request_id: str
    feature: FeatureName
    status: FeatureResponseStatus
    granted_mode: str | None = None
    granted_params: dict[str, Any] = field(default_factory=dict)
    lease_expires_at_ns: int | None = None
    reason: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "requestId": self.request_id,
            "feature": self.feature.value,
            "status": self.status.value,
            "grantedMode": self.granted_mode,
            "grantedParams": self.granted_params,
            "leaseExpiresAt": self.lease_expires_at_ns,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FeatureLease:
    request: FeatureRequest
    response: FeatureResponse

    def expired(self, now_ns: int | None = None) -> bool:
        expires_at = self.response.lease_expires_at_ns
        return expires_at is not None and (now_ns if now_ns is not None else monotonic_ns()) >= expires_at


@dataclass
class FeatureLeaseTable:
    permissions: dict[FeatureName, PermissionState] = field(
        default_factory=lambda: {
            FeatureName.CAMERA: PermissionState.UNKNOWN,
            FeatureName.MICROPHONE: PermissionState.UNKNOWN,
            FeatureName.EYE: PermissionState.UNKNOWN,
        }
    )
    active: dict[str, FeatureLease] = field(default_factory=dict)
    seen_requests: dict[str, FeatureResponse] = field(default_factory=dict)
    max_sensor_level: int = 2

    def request(self, request: FeatureRequest, now_ns: int | None = None) -> FeatureResponse:
        if request.request_id in self.seen_requests:
            return self.seen_requests[request.request_id]

        now = now_ns if now_ns is not None else monotonic_ns()
        permission = self.permissions.get(request.feature, PermissionState.GRANTED)
        if request.feature in HIGH_POWER_FEATURES and permission == PermissionState.DENIED:
            response = FeatureResponse(
                request_id=request.request_id,
                feature=request.feature,
                status=FeatureResponseStatus.REJECTED,
                reason="permission_denied",
            )
            self.seen_requests[request.request_id] = response
            return response

        requested_level = int(request.params.get("sensorLevel", self.max_sensor_level))
        if requested_level > self.max_sensor_level:
            granted_params = {**request.params, "sensorLevel": self.max_sensor_level}
            response = FeatureResponse(
                request_id=request.request_id,
                feature=request.feature,
                status=FeatureResponseStatus.DEGRADED,
                granted_mode=request.mode,
                granted_params=granted_params,
                lease_expires_at_ns=now + request.lease_time_ms * 1_000_000 if request.lease_time_ms else None,
                reason="sensor_level_capped",
            )
        else:
            response = FeatureResponse(
                request_id=request.request_id,
                feature=request.feature,
                status=FeatureResponseStatus.ACCEPTED,
                granted_mode=request.mode,
                granted_params=request.params,
                lease_expires_at_ns=now + request.lease_time_ms * 1_000_000 if request.lease_time_ms else None,
            )

        self.seen_requests[request.request_id] = response
        if response.status != FeatureResponseStatus.REJECTED:
            self.active[request.request_id] = FeatureLease(request=request, response=response)
        return response

    def expire(self, now_ns: int | None = None) -> list[FeatureLease]:
        now = now_ns if now_ns is not None else monotonic_ns()
        expired = [lease for lease in self.active.values() if lease.expired(now)]
        for lease in expired:
            self.active.pop(lease.request.request_id, None)
        return expired

    def clear_for_host_disconnect(self) -> None:
        self.active.clear()

    def is_active(self, feature: FeatureName, now_ns: int | None = None) -> bool:
        self.expire(now_ns)
        return any(lease.request.feature == feature for lease in self.active.values())
