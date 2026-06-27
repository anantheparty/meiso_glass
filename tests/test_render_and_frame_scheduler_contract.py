import pytest

from meiso_glass.render import RENDER_PROFILE_0_ALLOWED, RENDER_PROFILE_0_FORBIDDEN, MeisoRenderProfile
from meiso_glass.runtime.edge import FRAME_LOOP_ORDER, MeisoEdgeRuntime
from meiso_glass.scene import SceneEntity, SceneSnapshot


def test_render_profile_0_allows_only_bible_features():
    profile = MeisoRenderProfile()

    profile.validate_features(set(RENDER_PROFILE_0_ALLOWED))
    assert profile.graphics_api == "opengl_es_2_0"


def test_render_profile_0_rejects_forbidden_features():
    profile = MeisoRenderProfile()

    for feature in RENDER_PROFILE_0_FORBIDDEN:
        with pytest.raises(ValueError):
            profile.validate_features({feature})


def test_frame_scheduler_is_local_vsync_driven_and_never_waits_for_host_frame():
    runtime = MeisoEdgeRuntime()

    assert runtime.frame_loop_order() == FRAME_LOOP_ORDER
    assert FRAME_LOOP_ORDER[0] == "wait_local_vsync"
    assert "read_latest_complete_snapshot" in FRAME_LOOP_ORDER
    assert "present" in FRAME_LOOP_ORDER
    assert runtime.host_wait_deadline_ns() is None


def test_scene_replica_publishes_complete_immutable_snapshot():
    runtime = MeisoEdgeRuntime()
    snapshot = SceneSnapshot.from_entities("snap-1", "session-001", 1, [SceneEntity(entity_id="entity-1")])

    runtime.publish_scene_snapshot(snapshot)

    latest = runtime.current_scene_snapshot()
    assert latest == snapshot
    assert isinstance(latest.entities, tuple)
