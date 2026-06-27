from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..power import PowerBudget
from .types import Condition, Metadata, StringEnum, StructuredError


class ValidationState(StringEnum):
    DECLARED = "declared"
    MOCKED = "mocked"
    DETECTED = "detected"
    SMOKE_TESTED = "smoke_tested"
    MEASURED = "measured"
    BLOCKED = "blocked"


class Availability(StringEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


class SessionState(StringEnum):
    PROPOSED = "proposed"
    ADMITTED = "admitted"
    REJECTED = "rejected"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True)
class ResourceTier:
    compute: str = "none"
    vision: str = "none"
    audio: str = "none"
    display: str = "none"
    link: str = "none"
    payload: str = "none"


@dataclass(frozen=True)
class CapabilitySpec:
    family: str
    role_owner: str
    resource_tier: ResourceTier = field(default_factory=ResourceTier)
    output_forms: list[str] = field(default_factory=list)
    required_spaces: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    limits: dict[str, Any] = field(default_factory=dict)
    power_profile_ref: str | None = None
    quality_profile: dict[str, Any] = field(default_factory=dict)
    latency_profile: dict[str, Any] = field(default_factory=dict)
    privacy_class: str = "none"


@dataclass(frozen=True)
class CapabilityStatus:
    availability: Availability = Availability.UNAVAILABLE
    validation_state: ValidationState = ValidationState.DECLARED
    current_level_u8: int | None = None
    conditions: list[Condition] = field(default_factory=list)


@dataclass(frozen=True)
class CapabilityEvidence:
    measurement_source: str = "declared_only"
    confidence_level_u8: int = 0
    last_validated_at_ns: int | None = None
    unknowns: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Capability:
    metadata: Metadata
    spec: CapabilitySpec
    status: CapabilityStatus = field(default_factory=CapabilityStatus)
    evidence: CapabilityEvidence = field(default_factory=CapabilityEvidence)

    @property
    def capability_id(self) -> str:
        return self.metadata.id

    def usable_for_admission(self) -> bool:
        if self.status.availability in {Availability.UNAVAILABLE, Availability.BLOCKED}:
            return False
        return self.status.validation_state in {
            ValidationState.MOCKED,
            ValidationState.DETECTED,
            ValidationState.SMOKE_TESTED,
            ValidationState.MEASURED,
        }


@dataclass(frozen=True)
class SessionRequest:
    idempotency_key: str
    requester_role: str
    intent: str
    priority: str = "normal"


@dataclass(frozen=True)
class SessionSpec:
    session_type: str
    requested_capabilities: list[str]
    power_budget: PowerBudget = field(default_factory=PowerBudget)
    required_spaces: list[str] = field(default_factory=list)
    quality_budget: dict[str, Any] = field(default_factory=dict)
    information_budget: dict[str, Any] = field(default_factory=dict)
    allowed_degradation: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SessionStatus:
    state: SessionState = SessionState.PROPOSED
    selected_capabilities: list[str] = field(default_factory=list)
    selected_power_levels: dict[str, int] = field(default_factory=dict)
    selected_plan: dict[str, Any] = field(default_factory=dict)
    degradation_reason: str | None = None
    conditions: list[Condition] = field(default_factory=list)


@dataclass(frozen=True)
class SessionEvidence:
    admission_trace: list[dict[str, Any]] = field(default_factory=list)
    state_transitions: list[dict[str, Any]] = field(default_factory=list)
    metrics_summary: dict[str, Any] = field(default_factory=dict)
    power_summary: dict[str, Any] | None = None
    errors: list[StructuredError] = field(default_factory=list)


@dataclass(frozen=True)
class Session:
    metadata: Metadata
    request: SessionRequest
    spec: SessionSpec
    status: SessionStatus = field(default_factory=SessionStatus)
    evidence: SessionEvidence = field(default_factory=SessionEvidence)

    @property
    def session_id(self) -> str:
        return self.metadata.id


@dataclass(frozen=True)
class SystemProfile:
    metadata: Metadata
    role: str
    platform_family: str
    capabilities: list[Capability] = field(default_factory=list)
    adapter_bindings: list[dict[str, Any]] = field(default_factory=list)
    default_policy_ref: str | None = None
    network_paths: list[dict[str, Any]] = field(default_factory=list)
    measurement_sources: list[str] = field(default_factory=list)
    extension_slots: list[dict[str, Any]] = field(default_factory=list)
    validation_state: ValidationState = ValidationState.DECLARED
    conditions: list[Condition] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)

    def capability_map(self) -> dict[str, Capability]:
        return {cap.capability_id: cap for cap in self.capabilities}
