from __future__ import annotations

from dataclasses import dataclass, field

from ..space import Pose


@dataclass(frozen=True)
class ViewSlot:
    view_id: str
    eye: str = "none"
    display_space: str = "/space/display/primary"
    viewport: tuple[int, int, int, int] | None = None
    recommended_resolution: tuple[int, int] | None = None
    supported_refresh_hz: list[float] = field(default_factory=list)
    projection_kind: str = "profile_declared"
    fov_hint: dict[str, float] | None = None


@dataclass(frozen=True)
class ViewSet:
    viewset_id: str
    topology: str
    views: list[ViewSlot]
    stereo_mode: str = "none"
    depth_composition: str = "unsupported"

    def primary_view(self) -> ViewSlot | None:
        return self.views[0] if self.views else None


@dataclass(frozen=True)
class PresentationSurface:
    surface_id: str
    producer_role: str
    kind: str
    format_hint: str = "unknown"
    size_px: tuple[int, int] | None = None
    max_update_hz: float | None = None
    transport_ref: str | None = None


@dataclass(frozen=True)
class PresentationLayer:
    layer_id: str
    layer_type: str
    target_views: list[str]
    surface_ref: str
    order: int = 0
    alpha_mode: str = "opaque"
    space: str = "/space/display/primary"
    pose_in_space: Pose | None = None
    max_latency_ms: float | None = None
    min_refresh_hz: float | None = None
    allow_drop: bool = True
    allow_refresh_degrade: bool = True
    allow_brightness_cap: bool = True
    allow_viewport_scale: bool = True
    allow_layer_disable: bool = False


@dataclass(frozen=True)
class PresentationSessionSpec:
    viewset_ref: str
    layers: list[PresentationLayer]
    target_refresh_hz: float
    max_frame_latency_ms: float
    allow_frame_skip: bool = True
    brightness_mode: str = "auto"
    max_brightness_pct: int | None = None
    content_update_region: str = "full"
    degradation_order: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FrameTiming:
    frame_index: int
    predicted_display_time_ns: int
    deadline_ns: int
    submitted_time_ns: int | None = None
    displayed_time_ns: int | None = None
    missed_deadline: bool = False
    drop_reason: str = "none"


@dataclass(frozen=True)
class PresentationFrameStats:
    session_id: str
    frames_submitted: int = 0
    frames_displayed: int = 0
    frames_dropped: int = 0
    avg_latency_ms: float | None = None
    p95_latency_ms: float | None = None
    refresh_hz_observed: float | None = None
    selected_brightness_pct: int | None = None
    selected_viewport_scale: float | None = None
