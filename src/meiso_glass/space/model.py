from __future__ import annotations

from dataclasses import dataclass, field

from ..core.model import Availability, ValidationState
from ..core.types import Metadata, clamp_u8, require_semantic_path


@dataclass(frozen=True)
class SpaceRef:
    space_id: str
    kind: str
    owner_role: str
    persistence: str = "session"

    def __post_init__(self) -> None:
        require_semantic_path(self.space_id)


@dataclass(frozen=True)
class Pose:
    position_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    orientation_xyzw: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)


@dataclass(frozen=True)
class SpaceRelation:
    from_space: str
    to_space: str
    timestamp_ns: int
    pose: Pose = field(default_factory=Pose)
    timebase: str = "monotonic"
    linear_velocity_mps: tuple[float, float, float] | None = None
    angular_velocity_radps: tuple[float, float, float] | None = None
    validity: str = "estimated"
    confidence_level_u8: int = 0
    source: str = "declared_only"

    def __post_init__(self) -> None:
        require_semantic_path(self.from_space)
        require_semantic_path(self.to_space)
        clamp_u8(self.confidence_level_u8)


@dataclass(frozen=True)
class SensorSlot:
    slot_id: str
    sensor_role: str
    capture_modality: str
    mounted_space: str
    owner_role: str
    validation_state: ValidationState = ValidationState.DECLARED

    def __post_init__(self) -> None:
        require_semantic_path(self.slot_id)
        require_semantic_path(self.mounted_space)


@dataclass(frozen=True)
class SpatialCapabilitySpec:
    spatial_role: str
    source_slots: list[str]
    output_forms: list[str]
    coordinate_space: str
    update_rate_hz: float | None = None
    privacy_class: str = "none"


@dataclass(frozen=True)
class SpatialCapability:
    metadata: Metadata
    spec: SpatialCapabilitySpec
    validation_state: ValidationState = ValidationState.DECLARED
    availability: Availability = Availability.UNAVAILABLE
    confidence_level_u8: int = 0
    unknowns: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        clamp_u8(self.confidence_level_u8)
