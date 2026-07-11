#include "meiso_slice.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

static int failures;

#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "%s:%d check failed: %s\n", __FILE__, __LINE__, #condition); \
        failures += 1; \
    } \
} while (0)

typedef struct {
    uint8_t source_pixel;
    uint8_t target_pixel;
    MeisoEdgeState state;
    MeisoOverlayState overlay;
    MeisoCameraFrame source;
    MeisoCameraFrame target;
    MeisoOrientation source_pose;
    MeisoOrientation target_pose;
    MeisoCalibration calibration;
    MeisoSliceLimits limits;
    MeisoComposeResult result;
} Fixture;

static bool near(double actual, double expected, double tolerance)
{
    return fabs(actual - expected) <= tolerance;
}

static void init_fixture(Fixture *fixture)
{
    MeisoFrameKey source_key = {7U, 3U, 100U};
    MeisoFrameKey target_key = {7U, 3U, 105U};
    MeisoDisplayAction action;

    memset(fixture, 0, sizeof(*fixture));
    fixture->source_pixel = 10U;
    fixture->target_pixel = 20U;
    fixture->overlay = (MeisoOverlayState){
        9U, 11U, source_key, {300.0, 230.0, 340.0, 250.0}, false
    };
    fixture->source = (MeisoCameraFrame){
        source_key, 1000000000U, 1U, 1U, &fixture->source_pixel, 1U, 1U, true
    };
    fixture->target = (MeisoCameraFrame){
        target_key, 1020000000U, 1U, 1U, &fixture->target_pixel, 1U, 1U, true
    };
    fixture->source_pose = (MeisoOrientation){
        7U,
        1000000000U,
        1000000000U,
        1000000000U,
        {1.0, 0.0, 0.0, 0.0},
        0.001,
        true
    };
    fixture->target_pose = (MeisoOrientation){
        7U,
        1020000000U,
        1020000000U,
        1020000000U,
        {1.0, 0.0, 0.0, 0.0},
        0.001,
        true
    };
    fixture->calibration = (MeisoCalibration){
        true, 3U, 1U, 1U, 100.0, 100.0, 320.0, 240.0, 0.0,
        {1.0, 0.0, 0.0, 0.0}
    };
    fixture->limits = (MeisoSliceLimits){50000000U, 1000000U, 1000000U, 0.01};
    CHECK(meiso_edge_begin_session(&fixture->state, 9U, &action) == MEISO_SESSION_STARTED);
    CHECK(action == MEISO_DISPLAY_HIDE);
}

static MeisoDropReason compose(Fixture *fixture)
{
    MeisoDisplayAction action;
    MeisoDropReason reason = meiso_edge_ingest_overlay(
        &fixture->state, &fixture->overlay, &action
    );
    if (reason != MEISO_DROP_NONE) {
        return reason;
    }
    CHECK(action == MEISO_DISPLAY_HIDE);
    return meiso_edge_render_overlay(
        &fixture->state,
        &fixture->source,
        &fixture->target,
        &fixture->source_pose,
        &fixture->target_pose,
        &fixture->calibration,
        &fixture->limits,
        &fixture->result
    );
}

static void check_quad(const MeisoComposeResult *result, const double expected[4][2])
{
    size_t index;
    for (index = 0U; index < 4U; ++index) {
        CHECK(near(result->quad[index].x, expected[index][0], 1e-6));
        CHECK(near(result->quad[index].y, expected[index][1], 1e-6));
    }
}

static void test_loopback_semantics(void)
{
    uint8_t storage[64];
    uint8_t receiver_storage[64];
    uint8_t receiver_storage_next[64];
    uint8_t pixels[81];
    MeisoLoopback link;
    MeisoCaptureIntent intent = {4U, 1U, true, 100U};
    MeisoCaptureIntent received_intent;
    MeisoImuObservation imu = {7U, 2U, 1U, 10U, {1.0, 2.0, 3.0}, true};
    MeisoImuObservation received_imu;
    MeisoCameraFrame frame = {
        {7U, 3U, 1U}, 10U, 4U, 4U, pixels, 16U, 16U, true
    };
    MeisoCameraFrame received_frame;
    MeisoOverlayState overlay = {
        4U, 1U, {7U, 3U, 1U}, {1.0, 2.0, 3.0, 4.0}, false
    };
    MeisoOverlayState received_overlay;

    memset(pixels, 42, sizeof(pixels));
    meiso_loopback_init(&link, storage, sizeof(storage));
    CHECK(meiso_loopback_begin_session(&link, 4U) == MEISO_SESSION_STARTED);

    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_QUEUED);
    intent.version = 2U;
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_REPLACED);
    intent.version = 1U;
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_STALE_VERSION);
    CHECK(meiso_loopback_receive_capture_intent(&link, &received_intent));
    CHECK(received_intent.version == 2U);
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_STALE_VERSION);

    CHECK(meiso_loopback_send_imu(&link, &imu) == MEISO_SEND_QUEUED);
    imu.timestamp_ns = 11U;
    imu.sample_sequence = 2U;
    CHECK(meiso_loopback_send_imu(&link, &imu) == MEISO_SEND_OBSERVATION_OVERWROTE);
    CHECK(link.observation_drop_count == 1U);
    CHECK(meiso_loopback_receive_imu(&link, &received_imu));
    CHECK(received_imu.timestamp_ns == 11U);
    CHECK(received_imu.sample_sequence == 2U);

    frame.complete = false;
    frame.received_size = 8U;
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_INCOMPLETE_BULK);
    frame.complete = true;
    frame.received_size = 16U;
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_BUSY);
    CHECK(!meiso_loopback_receive_camera(&link, receiver_storage, 15U, &received_frame));
    CHECK(meiso_loopback_receive_camera(
        &link, receiver_storage, sizeof(receiver_storage), &received_frame));
    CHECK(received_frame.gray8 == receiver_storage);
    CHECK(received_frame.gray8 != storage);
    CHECK(memcmp(received_frame.gray8, pixels, 16U) == 0);
    pixels[0] = 99U;
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_QUEUED);
    CHECK(receiver_storage[0] == 42U);
    CHECK(meiso_loopback_receive_camera(
        &link, receiver_storage_next, sizeof(receiver_storage_next), &received_frame));
    CHECK(receiver_storage_next[0] == 99U);
    frame.width = 9U;
    frame.height = 9U;
    frame.payload_size = sizeof(pixels);
    frame.received_size = sizeof(pixels);
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_CAPACITY);

    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_QUEUED);
    overlay.version = 2U;
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_REPLACED);
    overlay.version = 1U;
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_STALE_VERSION);
    CHECK(meiso_loopback_receive_overlay(&link, &received_overlay));
    CHECK(received_overlay.version == 2U);
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_STALE_VERSION);
}

static void test_loopback_session_isolation(void)
{
    uint8_t storage[16];
    uint8_t receiver_storage[16];
    uint8_t pixels[4] = {1U, 2U, 3U, 4U};
    MeisoLoopback link;
    MeisoCaptureIntent intent = {4U, 1U, true, 100U};
    MeisoCaptureIntent received_intent;
    MeisoOverlayState overlay = {
        4U, 1U, {7U, 3U, 1U}, {0.0, 0.0, 1.0, 1.0}, false
    };
    MeisoOverlayState received_overlay;
    MeisoCameraFrame frame = {
        {7U, 3U, 1U}, 10U, 2U, 2U, pixels, sizeof(pixels), sizeof(pixels), true
    };
    MeisoCameraFrame received_frame;
    MeisoImuObservation imu = {7U, 2U, 1U, 10U, {0.0, 0.0, 0.0}, true};
    MeisoImuObservation received_imu;
    MeisoCaptureState capture_state = {0};
    MeisoEdgeState edge_state = {0};
    MeisoDisplayAction action;

    meiso_loopback_init(&link, storage, sizeof(storage));
    CHECK(!meiso_loopback_session_active(&link));
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_SESSION_INACTIVE);
    CHECK(meiso_loopback_begin_session(&link, 4U) == MEISO_SESSION_STARTED);
    CHECK(meiso_loopback_session_active(&link));
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_imu(&link, &imu) == MEISO_SEND_QUEUED);

    CHECK(meiso_loopback_begin_session(&link, 5U) == MEISO_SESSION_STARTED);
    CHECK(!meiso_loopback_receive_capture_intent(&link, &received_intent));
    CHECK(!meiso_loopback_receive_overlay(&link, &received_overlay));
    CHECK(!meiso_loopback_receive_camera(
        &link, receiver_storage, sizeof(receiver_storage), &received_frame));
    CHECK(!meiso_loopback_receive_imu(&link, &received_imu));
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) ==
          MEISO_SEND_SESSION_MISMATCH);
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_SESSION_MISMATCH);

    intent.session_id = 5U;
    intent.version = UINT64_MAX;
    overlay.session_id = 5U;
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_imu(&link, &imu) == MEISO_SEND_QUEUED);
    intent.version = 0U;
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_VERSION_WRAP);
    CHECK(!meiso_loopback_session_active(&link));
    CHECK(!meiso_loopback_receive_capture_intent(&link, &received_intent));
    CHECK(!meiso_loopback_receive_overlay(&link, &received_overlay));
    CHECK(!meiso_loopback_receive_camera(
        &link, receiver_storage, sizeof(receiver_storage), &received_frame));
    CHECK(!meiso_loopback_receive_imu(&link, &received_imu));
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_SESSION_INACTIVE);
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_SESSION_INACTIVE);
    CHECK(meiso_loopback_begin_session(&link, 5U) == MEISO_SESSION_NOT_NEWER);

    CHECK(meiso_loopback_begin_session(&link, 6U) == MEISO_SESSION_STARTED);
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_SESSION_MISMATCH);
    intent.session_id = 6U;
    intent.version = 1U;
    overlay.session_id = 6U;
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_receive_capture_intent(&link, &received_intent));
    CHECK(meiso_loopback_receive_overlay(&link, &received_overlay));

    intent.version = 2U;
    overlay.version = UINT64_MAX;
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_imu(&link, &imu) == MEISO_SEND_QUEUED);
    overlay.version = 0U;
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_VERSION_WRAP);
    CHECK(!meiso_loopback_session_active(&link));
    CHECK(!meiso_loopback_receive_capture_intent(&link, &received_intent));
    CHECK(!meiso_loopback_receive_overlay(&link, &received_overlay));
    CHECK(!meiso_loopback_receive_camera(
        &link, receiver_storage, sizeof(receiver_storage), &received_frame));
    CHECK(!meiso_loopback_receive_imu(&link, &received_imu));

    CHECK(meiso_loopback_begin_session(&link, 7U) == MEISO_SESSION_STARTED);
    intent.session_id = 7U;
    intent.version = 0U;
    overlay.session_id = 7U;
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_receive_capture_intent(&link, &received_intent));
    CHECK(meiso_loopback_receive_overlay(&link, &received_overlay));

    CHECK(meiso_capture_begin_session(&capture_state, 7U) == MEISO_SESSION_STARTED);
    CHECK(meiso_capture_ingest_intent(&capture_state, &received_intent, 1000U) ==
          MEISO_CAPTURE_ACCEPTED);
    CHECK(meiso_capture_is_active(&capture_state, 1099U));
    CHECK(meiso_edge_begin_session(&edge_state, 7U, &action) == MEISO_SESSION_STARTED);
    CHECK(action == MEISO_DISPLAY_HIDE);
    CHECK(meiso_edge_ingest_overlay(&edge_state, &received_overlay, &action) ==
          MEISO_DROP_NONE);

    intent.version = 1U;
    overlay.version = 1U;
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_camera(&link, &frame) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_imu(&link, &imu) == MEISO_SEND_QUEUED);
    meiso_loopback_end_session(&link);
    meiso_capture_end_session(&capture_state);
    CHECK(meiso_edge_end_session(&edge_state) == MEISO_DISPLAY_HIDE);
    CHECK(!meiso_loopback_session_active(&link));
    CHECK(!meiso_capture_is_active(&capture_state, 1000U));
    CHECK(!meiso_loopback_receive_capture_intent(&link, &received_intent));
    CHECK(!meiso_loopback_receive_overlay(&link, &received_overlay));
    CHECK(!meiso_loopback_receive_camera(
        &link, receiver_storage, sizeof(receiver_storage), &received_frame));
    CHECK(!meiso_loopback_receive_imu(&link, &received_imu));
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_SESSION_INACTIVE);
    CHECK(meiso_loopback_begin_session(&link, 7U) == MEISO_SESSION_NOT_NEWER);
    CHECK(meiso_capture_begin_session(&capture_state, 7U) == MEISO_SESSION_NOT_NEWER);
    CHECK(meiso_edge_begin_session(&edge_state, 7U, &action) ==
          MEISO_SESSION_NOT_NEWER);
    CHECK(action == MEISO_DISPLAY_KEEP);

    CHECK(meiso_loopback_begin_session(&link, 8U) == MEISO_SESSION_STARTED);
    CHECK(meiso_capture_begin_session(&capture_state, 8U) == MEISO_SESSION_STARTED);
    CHECK(meiso_edge_begin_session(&edge_state, 8U, &action) == MEISO_SESSION_STARTED);
    CHECK(action == MEISO_DISPLAY_HIDE);
    intent.session_id = 8U;
    intent.version = 0U;
    overlay.session_id = 8U;
    overlay.version = 0U;
    CHECK(meiso_loopback_send_capture_intent(&link, &intent) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_send_overlay(&link, &overlay) == MEISO_SEND_QUEUED);
    CHECK(meiso_loopback_receive_capture_intent(&link, &received_intent));
    CHECK(meiso_loopback_receive_overlay(&link, &received_overlay));
}

static void test_host_detector(void)
{
    uint8_t pixels[64];
    MeisoCameraFrame frame = {
        {1U, 2U, 3U}, 100U, 8U, 8U, pixels, sizeof(pixels), sizeof(pixels), true
    };
    MeisoOverlayState overlay;
    size_t x;
    size_t y;

    memset(pixels, 0, sizeof(pixels));
    for (y = 3U; y <= 6U; ++y) {
        for (x = 2U; x <= 5U; ++x) {
            pixels[y * 8U + x] = 220U;
        }
    }
    CHECK(meiso_host_detect_bright_box(&frame, 5U, 8U, 200U, &overlay) == MEISO_HOST_BOX);
    CHECK(!overlay.hide);
    CHECK(overlay.source_key.frame_sequence == 3U);
    CHECK(overlay.box.left == 2.0 && overlay.box.top == 3.0);
    CHECK(overlay.box.right == 5.0 && overlay.box.bottom == 6.0);

    memset(pixels, 0, sizeof(pixels));
    CHECK(meiso_host_detect_bright_box(&frame, 5U, 9U, 200U, &overlay) == MEISO_HOST_HIDE);
    CHECK(overlay.hide);
    frame.complete = false;
    frame.received_size -= 1U;
    CHECK(meiso_host_detect_bright_box(&frame, 5U, 10U, 200U, &overlay) ==
          MEISO_HOST_INCOMPLETE_BULK);
}

static void test_capture_lease(void)
{
    MeisoCaptureState state = {0};
    MeisoCaptureIntent intent = {5U, 1U, true, 100U};

    CHECK(meiso_capture_begin_session(&state, 5U) == MEISO_SESSION_STARTED);
    CHECK(meiso_capture_ingest_intent(&state, &intent, 1000U) == MEISO_CAPTURE_ACCEPTED);
    CHECK(meiso_capture_is_active(&state, 1099U));
    CHECK(meiso_capture_begin_session(&state, 5U) == MEISO_SESSION_NOT_NEWER);
    CHECK(meiso_capture_is_active(&state, 1099U));
    CHECK(!meiso_capture_is_active(&state, 1100U));
    CHECK(meiso_capture_ingest_intent(&state, &intent, 1000U) ==
          MEISO_CAPTURE_DUPLICATE_VERSION);
    intent.version = 0U;
    CHECK(meiso_capture_ingest_intent(&state, &intent, 1000U) ==
          MEISO_CAPTURE_STALE_VERSION);
    intent.version = 2U;
    intent.enabled = false;
    CHECK(meiso_capture_ingest_intent(&state, &intent, 1000U) == MEISO_CAPTURE_DISABLED);
    CHECK(!meiso_capture_is_active(&state, 1000U));
    intent.session_id = 6U;
    intent.version = 3U;
    CHECK(meiso_capture_ingest_intent(&state, &intent, 1000U) ==
          MEISO_CAPTURE_SESSION_MISMATCH);
    CHECK(meiso_capture_begin_session(&state, 6U) == MEISO_SESSION_STARTED);
    CHECK(!meiso_capture_is_active(&state, 1000U));

    intent.version = UINT64_MAX;
    intent.enabled = true;
    CHECK(meiso_capture_ingest_intent(&state, &intent, 1000U) == MEISO_CAPTURE_ACCEPTED);
    CHECK(meiso_capture_is_active(&state, 1099U));
    intent.version = 0U;
    CHECK(meiso_capture_ingest_intent(&state, &intent, 1000U) ==
          MEISO_CAPTURE_VERSION_WRAP);
    CHECK(!meiso_capture_is_active(&state, 1000U));
    CHECK(meiso_capture_begin_session(&state, 6U) == MEISO_SESSION_NOT_NEWER);
    CHECK(meiso_capture_begin_session(&state, 7U) == MEISO_SESSION_STARTED);
    CHECK(meiso_capture_ingest_intent(&state, &intent, 1000U) ==
          MEISO_CAPTURE_SESSION_MISMATCH);
    intent.session_id = 7U;
    CHECK(meiso_capture_ingest_intent(&state, &intent, 1000U) == MEISO_CAPTURE_ACCEPTED);
    meiso_capture_end_session(&state);
    CHECK(!meiso_capture_is_active(&state, 1000U));
    CHECK(meiso_capture_begin_session(&state, 7U) == MEISO_SESSION_NOT_NEWER);
    CHECK(meiso_capture_begin_session(&state, 8U) == MEISO_SESSION_STARTED);
}

static void test_rotation_vectors(void)
{
    Fixture fixture;
    const double identity[4][2] = {
        {300.0, 230.0}, {340.0, 230.0}, {340.0, 250.0}, {300.0, 250.0}
    };
    const double yaw[4][2] = {
        {0.0, 64.644660940673},
        {66.666666666667, 76.429773960448},
        {66.666666666667, 123.570226039552},
        {0.0, 135.355339059327}
    };
    const double extrinsic[4][2] = {
        {330.0, 220.0}, {330.0, 260.0}, {310.0, 260.0}, {310.0, 220.0}
    };
    MeisoComposeResult positive;

    init_fixture(&fixture);
    CHECK(compose(&fixture) == MEISO_DROP_NONE);
    check_quad(&fixture.result, identity);

    init_fixture(&fixture);
    fixture.calibration.cx = 100.0;
    fixture.calibration.cy = 100.0;
    fixture.overlay.box = (MeisoBox){100.0, 75.0, 150.0, 125.0};
    fixture.target_pose.q_w_from_i = (MeisoQuaternion){
        0.9238795325112867, 0.0, 0.3826834323650898, 0.0
    };
    CHECK(compose(&fixture) == MEISO_DROP_NONE);
    check_quad(&fixture.result, yaw);
    positive = fixture.result;

    init_fixture(&fixture);
    fixture.calibration.cx = 100.0;
    fixture.calibration.cy = 100.0;
    fixture.overlay.box = (MeisoBox){100.0, 75.0, 150.0, 125.0};
    fixture.target_pose.q_w_from_i = (MeisoQuaternion){
        -0.9238795325112867, 0.0, -0.3826834323650898, 0.0
    };
    CHECK(compose(&fixture) == MEISO_DROP_NONE);
    {
        size_t index;
        for (index = 0U; index < 4U; ++index) {
            CHECK(near(fixture.result.quad[index].x, positive.quad[index].x, 1e-6));
            CHECK(near(fixture.result.quad[index].y, positive.quad[index].y, 1e-6));
        }
    }

    init_fixture(&fixture);
    fixture.target_pose.q_w_from_i = (MeisoQuaternion){
        0.7071067811865476, 0.0, 0.7071067811865476, 0.0
    };
    fixture.calibration.q_i_from_c = (MeisoQuaternion){
        0.7071067811865476, 0.7071067811865476, 0.0, 0.0
    };
    CHECK(compose(&fixture) == MEISO_DROP_NONE);
    check_quad(&fixture.result, extrinsic);

    init_fixture(&fixture);
    fixture.overlay.box = (MeisoBox){320.0, 240.0, 320.0, 240.0};
    fixture.target_pose.q_w_from_i = (MeisoQuaternion){
        0.7071067811865476, 0.0, 0.7071067811865476, 0.0
    };
    CHECK(compose(&fixture) == MEISO_DROP_PROJECTION_INVALID);

    init_fixture(&fixture);
    fixture.calibration.fx = 80.0;
    fixture.calibration.fy = 120.0;
    fixture.calibration.skew = 7.0;
    CHECK(compose(&fixture) == MEISO_DROP_NONE);
    check_quad(&fixture.result, identity);

    init_fixture(&fixture);
    fixture.target_pose.q_w_from_i.w = 2.0;
    CHECK(compose(&fixture) == MEISO_DROP_POSE_MISSING);
}

static void test_overlay_reuse_across_targets(void)
{
    Fixture fixture;
    MeisoDisplayAction action;
    double first_x;

    init_fixture(&fixture);
    CHECK(meiso_edge_ingest_overlay(&fixture.state, &fixture.overlay, &action) ==
          MEISO_DROP_NONE);
    CHECK(action == MEISO_DISPLAY_HIDE);
    CHECK(meiso_edge_render_overlay(
        &fixture.state,
        &fixture.source,
        &fixture.target,
        &fixture.source_pose,
        &fixture.target_pose,
        &fixture.calibration,
        &fixture.limits,
        &fixture.result
    ) == MEISO_DROP_NONE);
    CHECK(fixture.result.action == MEISO_DISPLAY_SHOW);
    first_x = fixture.result.quad[0].x;

    fixture.target.key.frame_sequence += 1U;
    fixture.target.timestamp_ns += 10000000U;
    fixture.target_pose.timestamp_ns = fixture.target.timestamp_ns;
    fixture.target_pose.support_start_ns = fixture.target.timestamp_ns;
    fixture.target_pose.support_end_ns = fixture.target.timestamp_ns;
    fixture.target_pose.q_w_from_i = (MeisoQuaternion){
        0.9848077530122080, 0.0, 0.1736481776669303, 0.0
    };
    CHECK(meiso_edge_render_overlay(
        &fixture.state,
        &fixture.source,
        &fixture.target,
        &fixture.source_pose,
        &fixture.target_pose,
        &fixture.calibration,
        &fixture.limits,
        &fixture.result
    ) == MEISO_DROP_NONE);
    CHECK(fixture.result.action == MEISO_DISPLAY_SHOW);
    CHECK(!near(fixture.result.quad[0].x, first_x, 1e-6));
}

static void test_edge_gates(void)
{
    Fixture fixture;
    MeisoDisplayAction action;

    init_fixture(&fixture);
    CHECK(meiso_edge_render_overlay(
        &fixture.state,
        &fixture.source,
        &fixture.target,
        &fixture.source_pose,
        &fixture.target_pose,
        &fixture.calibration,
        &fixture.limits,
        &fixture.result
    ) == MEISO_DROP_NO_OVERLAY);
    CHECK(fixture.result.action == MEISO_DISPLAY_HIDE);

    init_fixture(&fixture);
    fixture.overlay.session_id += 1U;
    CHECK(compose(&fixture) == MEISO_DROP_SESSION_MISMATCH);

    init_fixture(&fixture);
    CHECK(compose(&fixture) == MEISO_DROP_NONE);
    CHECK(compose(&fixture) == MEISO_DROP_DUPLICATE_VERSION);
    fixture.overlay.version -= 1U;
    CHECK(compose(&fixture) == MEISO_DROP_STALE_VERSION);

    init_fixture(&fixture);
    fixture.overlay.source_key.clock_epoch += 1U;
    CHECK(compose(&fixture) == MEISO_DROP_WRONG_CLOCK_EPOCH);

    init_fixture(&fixture);
    fixture.overlay.source_key.stream_instance += 1U;
    CHECK(compose(&fixture) == MEISO_DROP_STREAM_INSTANCE_MISMATCH);

    init_fixture(&fixture);
    fixture.overlay.source_key.frame_sequence += 1U;
    CHECK(compose(&fixture) == MEISO_DROP_SOURCE_FRAME_NOT_RETAINED);

    init_fixture(&fixture);
    fixture.target.key.frame_sequence = 99U;
    CHECK(compose(&fixture) == MEISO_DROP_TARGET_PRECEDES_SOURCE);

    init_fixture(&fixture);
    fixture.target.timestamp_ns = 1060000000U;
    fixture.target_pose.timestamp_ns = fixture.target.timestamp_ns;
    CHECK(compose(&fixture) == MEISO_DROP_SOURCE_FRAME_TOO_OLD);

    init_fixture(&fixture);
    fixture.source.complete = false;
    CHECK(compose(&fixture) == MEISO_DROP_INCOMPLETE_BULK);

    init_fixture(&fixture);
    fixture.calibration.valid = false;
    CHECK(compose(&fixture) == MEISO_DROP_CALIBRATION_MISSING);

    init_fixture(&fixture);
    fixture.calibration.stream_instance += 1U;
    CHECK(compose(&fixture) == MEISO_DROP_CALIBRATION_MISMATCH);

    init_fixture(&fixture);
    fixture.source_pose.valid = false;
    CHECK(compose(&fixture) == MEISO_DROP_POSE_MISSING);

    init_fixture(&fixture);
    fixture.source_pose.clock_epoch += 1U;
    CHECK(compose(&fixture) == MEISO_DROP_POSE_EPOCH);

    init_fixture(&fixture);
    fixture.source_pose.timestamp_ns += 2000000U;
    CHECK(compose(&fixture) == MEISO_DROP_POSE_GAP);

    init_fixture(&fixture);
    fixture.source_pose.support_start_ns -= 2000000U;
    fixture.source_pose.support_end_ns += 2000000U;
    CHECK(compose(&fixture) == MEISO_DROP_POSE_SUPPORT_GAP);

    init_fixture(&fixture);
    fixture.target_pose.uncertainty_rad = 0.02;
    CHECK(compose(&fixture) == MEISO_DROP_POSE_UNCERTAIN);

    init_fixture(&fixture);
    fixture.overlay.hide = true;
    CHECK(compose(&fixture) == MEISO_DROP_HIDDEN);
    CHECK(fixture.result.hidden);
    CHECK(fixture.result.action == MEISO_DISPLAY_HIDE);

    init_fixture(&fixture);
    fixture.overlay.version = 10U;
    CHECK(compose(&fixture) == MEISO_DROP_NONE);
    CHECK(fixture.result.action == MEISO_DISPLAY_SHOW);
    fixture.overlay.version = 11U;
    fixture.overlay.source_key.clock_epoch += 1U;
    CHECK(meiso_edge_ingest_overlay(&fixture.state, &fixture.overlay, &action) ==
          MEISO_DROP_NONE);
    CHECK(action == MEISO_DISPLAY_HIDE);
    CHECK(meiso_edge_render_overlay(
        &fixture.state,
        &fixture.source,
        &fixture.target,
        &fixture.source_pose,
        &fixture.target_pose,
        &fixture.calibration,
        &fixture.limits,
        &fixture.result
    ) == MEISO_DROP_WRONG_CLOCK_EPOCH);
    CHECK(fixture.result.action == MEISO_DISPLAY_HIDE);
    fixture.overlay.version = 10U;
    CHECK(meiso_edge_ingest_overlay(&fixture.state, &fixture.overlay, &action) ==
          MEISO_DROP_STALE_VERSION);
    CHECK(action == MEISO_DISPLAY_KEEP);

    init_fixture(&fixture);
    fixture.overlay.version = UINT64_MAX;
    CHECK(meiso_edge_ingest_overlay(&fixture.state, &fixture.overlay, &action) ==
          MEISO_DROP_NONE);
    CHECK(action == MEISO_DISPLAY_HIDE);
    fixture.overlay.version = 0U;
    CHECK(meiso_edge_ingest_overlay(&fixture.state, &fixture.overlay, &action) ==
          MEISO_DROP_VERSION_WRAP);
    CHECK(action == MEISO_DISPLAY_HIDE);
    CHECK(meiso_edge_render_overlay(
        &fixture.state,
        &fixture.source,
        &fixture.target,
        &fixture.source_pose,
        &fixture.target_pose,
        &fixture.calibration,
        &fixture.limits,
        &fixture.result
    ) == MEISO_DROP_INVALID_INPUT);
    CHECK(fixture.result.action == MEISO_DISPLAY_HIDE);
    CHECK(meiso_edge_begin_session(&fixture.state, 9U, &action) ==
          MEISO_SESSION_NOT_NEWER);
    CHECK(action == MEISO_DISPLAY_KEEP);
    CHECK(meiso_edge_begin_session(&fixture.state, 10U, &action) ==
          MEISO_SESSION_STARTED);
    CHECK(action == MEISO_DISPLAY_HIDE);
    CHECK(meiso_edge_ingest_overlay(&fixture.state, &fixture.overlay, &action) ==
          MEISO_DROP_SESSION_MISMATCH);
    CHECK(action == MEISO_DISPLAY_KEEP);
    fixture.overlay.session_id = 10U;
    fixture.overlay.version = 1U;
    CHECK(meiso_edge_ingest_overlay(&fixture.state, &fixture.overlay, &action) ==
          MEISO_DROP_NONE);
    CHECK(action == MEISO_DISPLAY_HIDE);
    CHECK(meiso_edge_render_overlay(
        &fixture.state,
        &fixture.source,
        &fixture.target,
        &fixture.source_pose,
        &fixture.target_pose,
        &fixture.calibration,
        &fixture.limits,
        &fixture.result
    ) == MEISO_DROP_NONE);
    CHECK(fixture.result.action == MEISO_DISPLAY_SHOW);
    CHECK(meiso_edge_begin_session(&fixture.state, 10U, &action) ==
          MEISO_SESSION_NOT_NEWER);
    CHECK(action == MEISO_DISPLAY_KEEP);
    fixture.overlay.version = 0U;
    CHECK(meiso_edge_ingest_overlay(&fixture.state, &fixture.overlay, &action) ==
          MEISO_DROP_STALE_VERSION);
    CHECK(action == MEISO_DISPLAY_KEEP);
    CHECK(meiso_edge_render_overlay(
        &fixture.state,
        &fixture.source,
        &fixture.target,
        &fixture.source_pose,
        &fixture.target_pose,
        &fixture.calibration,
        &fixture.limits,
        &fixture.result
    ) == MEISO_DROP_NONE);
    CHECK(fixture.result.action == MEISO_DISPLAY_SHOW);
    CHECK(meiso_edge_end_session(&fixture.state) == MEISO_DISPLAY_HIDE);
    CHECK(meiso_edge_render_overlay(
        &fixture.state,
        &fixture.source,
        &fixture.target,
        &fixture.source_pose,
        &fixture.target_pose,
        &fixture.calibration,
        &fixture.limits,
        &fixture.result
    ) == MEISO_DROP_INVALID_INPUT);
    CHECK(fixture.result.action == MEISO_DISPLAY_HIDE);
    CHECK(meiso_edge_begin_session(&fixture.state, 10U, &action) ==
          MEISO_SESSION_NOT_NEWER);
    CHECK(meiso_edge_begin_session(&fixture.state, 11U, &action) ==
          MEISO_SESSION_STARTED);
    CHECK(action == MEISO_DISPLAY_HIDE);
}

int main(void)
{
    test_loopback_semantics();
    test_loopback_session_isolation();
    test_host_detector();
    test_capture_lease();
    test_rotation_vectors();
    test_overlay_reuse_across_targets();
    test_edge_gates();
    if (failures != 0) {
        fprintf(stderr, "%d test checks failed\n", failures);
        return 1;
    }
    printf("meiso_slice_test: passed\n");
    return 0;
}
