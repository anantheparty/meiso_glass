from meiso_glass.features import FeatureLeaseTable, FeatureName, FeatureRequest, FeatureResponseStatus, PermissionState


def test_feature_request_schema_is_exact():
    request = FeatureRequest(
        feature=FeatureName.CAMERA,
        mode="stream",
        params={"sensorLevel": 1},
        lease_time_ms=5000,
        request_id="req-001",
    )

    assert request.to_payload() == {
        "feature": "camera",
        "mode": "stream",
        "params": {"sensorLevel": 1},
        "priority": "normal",
        "leaseTime": 5000,
        "requestId": "req-001",
    }


def test_high_power_sensors_default_off():
    table = FeatureLeaseTable()

    assert table.is_active(FeatureName.CAMERA) is False
    assert table.is_active(FeatureName.MICROPHONE) is False
    assert table.is_active(FeatureName.EYE) is False


def test_accepted_feature_request_expires_by_lease_time():
    table = FeatureLeaseTable()
    request = FeatureRequest(
        feature=FeatureName.CAMERA,
        mode="stream",
        lease_time_ms=10,
        request_id="req-camera",
    )

    response = table.request(request, now_ns=1_000)

    assert response.status == FeatureResponseStatus.ACCEPTED
    assert table.is_active(FeatureName.CAMERA, now_ns=1_000)
    assert table.is_active(FeatureName.CAMERA, now_ns=9_000_000)
    assert not table.is_active(FeatureName.CAMERA, now_ns=10_001_000)


def test_host_disconnect_expires_active_leases():
    table = FeatureLeaseTable()
    table.request(
        FeatureRequest(feature=FeatureName.MICROPHONE, mode="capture", lease_time_ms=10_000, request_id="req-mic"),
        now_ns=1,
    )

    table.clear_for_host_disconnect()

    assert table.is_active(FeatureName.MICROPHONE, now_ns=2) is False


def test_degraded_and_rejected_do_not_hide_reason():
    table = FeatureLeaseTable(max_sensor_level=1)
    degraded = table.request(
        FeatureRequest(
            feature=FeatureName.CAMERA,
            mode="stream",
            params={"sensorLevel": 2},
            lease_time_ms=1000,
            request_id="req-degraded",
        ),
        now_ns=1,
    )

    table.permissions[FeatureName.EYE] = PermissionState.DENIED
    rejected = table.request(
        FeatureRequest(feature=FeatureName.EYE, mode="track", lease_time_ms=1000, request_id="req-rejected"),
        now_ns=1,
    )

    assert degraded.status == FeatureResponseStatus.DEGRADED
    assert degraded.reason == "sensor_level_capped"
    assert degraded.granted_params["sensorLevel"] == 1
    assert rejected.status == FeatureResponseStatus.REJECTED
    assert rejected.reason == "permission_denied"


def test_duplicate_request_id_is_idempotent():
    table = FeatureLeaseTable()
    request = FeatureRequest(feature=FeatureName.CAMERA, mode="stream", lease_time_ms=1000, request_id="req-once")

    first = table.request(request, now_ns=1)
    second = table.request(request, now_ns=999)

    assert first == second
    assert len(table.active) == 1
