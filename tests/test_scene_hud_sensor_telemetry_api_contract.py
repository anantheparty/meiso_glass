import pytest

from meiso_glass.api import MeisoHost
from meiso_glass.features import FeatureName, FeatureRequest
from meiso_glass.hud import HUD_COMPOSITION_ORDER, HudElement, HudElementType, HudUpdate
from meiso_glass.protocol import MeisoChannel, MeisoMessageType
from meiso_glass.scene import SceneEntity, SceneSnapshot, Transform, assert_scene_payload_uses_asset_ids_only
from meiso_glass.sensors import SensorSubscription, SensorType
from meiso_glass.telemetry import REQUIRED_TELEMETRY_METRICS, TelemetryReport


def test_public_api_exports_device_scene_hud_sensor_telemetry():
    host = MeisoHost(session_id="session-001")

    assert host.device
    assert host.scene
    assert host.hud
    assert host.sensor
    assert host.telemetry


def test_host_device_api_generates_feature_request_message():
    host = MeisoHost(session_id="session-001")
    msg = host.device.request_feature(
        FeatureRequest(feature=FeatureName.CAMERA, mode="stream", lease_time_ms=1000, request_id="req-camera")
    )

    assert msg.header.message_type == MeisoMessageType.FEATURE_REQUEST
    assert msg.header.channel == MeisoChannel.HIGH_RELIABLE
    assert msg.payload["feature"] == "camera"
    assert msg.payload["requestId"] == "req-camera"


def test_scene_entity_minimum_model_fields_and_asset_ids_only():
    entity = SceneEntity(
        entity_id="entity-1",
        parent_id=None,
        transform=Transform(position_m=(1.0, 2.0, 3.0)),
        mesh_id="mesh:hash-1",
        material_id="material:hash-1",
        visibility=True,
        animation_state="idle",
        lifetime_ms=1000,
        replication_mode="latest_wins",
    )
    snapshot = SceneSnapshot.from_entities("snapshot-1", "session-001", 1, [entity])

    assert snapshot.asset_refs == ("mesh:hash-1", "material:hash-1")
    assert_scene_payload_uses_asset_ids_only(snapshot.to_payload())
    with pytest.raises(ValueError):
        assert_scene_payload_uses_asset_ids_only({"meshBytes": b"no"})


def test_hud_composition_order_is_fixed_and_system_hud_is_not_host_writable():
    update = HudUpdate(
        update_id="hud-1",
        session_id="session-001",
        elements=(HudElement("text-1", HudElementType.TEXT, content={"text": "ready"}),),
    )

    assert HUD_COMPOSITION_ORDER == ("scene_3d", "app_hud", "system_hud")
    assert update.to_payload()["compositionOrder"] == ["scene_3d", "app_hud", "system_hud"]
    with pytest.raises(ValueError):
        HudElement("bad", HudElementType.TEXT, layer="system_hud")


def test_sensor_and_telemetry_api_messages_have_expected_channels():
    host = MeisoHost(session_id="session-001")
    sub = SensorSubscription(subscription_id="sub-imu", sensor=SensorType.IMU, rate_hz=120.0)
    sensor_msg = host.sensor.subscribe(sub)
    report = TelemetryReport(
        report_id="report-1",
        timestamp_ns=1,
        metrics={metric: 0 for metric in REQUIRED_TELEMETRY_METRICS},
    )
    telemetry_msg = host.telemetry.report(report)

    assert sensor_msg.header.message_type == MeisoMessageType.SENSOR_SUBSCRIBE
    assert sensor_msg.header.channel == MeisoChannel.HIGH_RELIABLE
    assert telemetry_msg.header.message_type == MeisoMessageType.TELEMETRY_REPORT
    assert telemetry_msg.header.channel == MeisoChannel.LATEST_WINS
    assert report.missing_required_metrics() == ()
