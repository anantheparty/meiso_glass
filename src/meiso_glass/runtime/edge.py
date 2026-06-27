from __future__ import annotations

from dataclasses import dataclass, field

from ..features import FeatureLeaseTable, FeatureName, FeatureRequest, FeatureResponse
from ..hud import HUD_COMPOSITION_ORDER
from ..scene import SceneReplica, SceneSnapshot
from ..timebase import monotonic_ns

FRAME_LOOP_ORDER = (
    "wait_local_vsync",
    "read_latest_complete_snapshot",
    "predict_local_pose",
    "choose_redraw_hud_or_cached_frame",
    "draw_scene_3d",
    "draw_app_hud",
    "draw_system_hud",
    "present",
    "record_metrics",
)


@dataclass
class MeisoEdgeRuntime:
    feature_leases: FeatureLeaseTable = field(default_factory=FeatureLeaseTable)
    scene_replica: SceneReplica = field(default_factory=SceneReplica)

    def request_feature(self, request: FeatureRequest, now_ns: int | None = None) -> FeatureResponse:
        return self.feature_leases.request(request, now_ns=now_ns)

    def expire_feature_leases(self, now_ns: int | None = None) -> None:
        self.feature_leases.expire(now_ns=now_ns)

    def handle_host_disconnect(self) -> None:
        self.feature_leases.clear_for_host_disconnect()

    def is_feature_active(self, feature: FeatureName, now_ns: int | None = None) -> bool:
        return self.feature_leases.is_active(feature, now_ns=now_ns)

    def publish_scene_snapshot(self, snapshot: SceneSnapshot) -> None:
        self.scene_replica.publish_complete_snapshot(snapshot)

    def current_scene_snapshot(self) -> SceneSnapshot | None:
        return self.scene_replica.latest_snapshot()

    def frame_loop_order(self) -> tuple[str, ...]:
        return FRAME_LOOP_ORDER

    def hud_composition_order(self) -> tuple[str, ...]:
        return HUD_COMPOSITION_ORDER

    def host_wait_deadline_ns(self) -> None:
        return None

    def local_pose_timestamp_ns(self) -> int:
        return monotonic_ns()
