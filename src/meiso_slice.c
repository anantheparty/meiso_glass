#include "meiso_slice.h"

#include <math.h>
#include <string.h>

typedef struct {
    double x;
    double y;
    double z;
} MeisoVec3;

static bool is_finite_box(MeisoBox box)
{
    return isfinite(box.left) && isfinite(box.top) && isfinite(box.right) &&
           isfinite(box.bottom) && box.left <= box.right && box.top <= box.bottom;
}

static bool frame_shape_valid(const MeisoCameraFrame *frame, size_t *expected_size)
{
    size_t expected;

    if (frame == NULL || frame->gray8 == NULL || frame->width == 0U || frame->height == 0U) {
        return false;
    }
    if ((size_t)frame->width > SIZE_MAX / (size_t)frame->height) {
        return false;
    }
    expected = (size_t)frame->width * (size_t)frame->height;
    if (frame->payload_size != expected) {
        return false;
    }
    if (expected_size != NULL) {
        *expected_size = expected;
    }
    return true;
}

static bool frame_complete(const MeisoCameraFrame *frame)
{
    return frame_shape_valid(frame, NULL) && frame->complete &&
           frame->received_size == frame->payload_size;
}

static uint64_t abs_diff_u64(uint64_t lhs, uint64_t rhs)
{
    return lhs >= rhs ? lhs - rhs : rhs - lhs;
}

static bool normalize_quaternion(MeisoQuaternion input, MeisoQuaternion *output)
{
    double norm_squared;
    double inverse_norm;

    if (output == NULL || !isfinite(input.w) || !isfinite(input.x) ||
        !isfinite(input.y) || !isfinite(input.z)) {
        return false;
    }
    norm_squared = input.w * input.w + input.x * input.x +
                   input.y * input.y + input.z * input.z;
    if (!isfinite(norm_squared) || norm_squared <= 0.0 || fabs(norm_squared - 1.0) > 1e-3) {
        return false;
    }
    inverse_norm = 1.0 / sqrt(norm_squared);
    output->w = input.w * inverse_norm;
    output->x = input.x * inverse_norm;
    output->y = input.y * inverse_norm;
    output->z = input.z * inverse_norm;
    return true;
}

static MeisoQuaternion conjugate_quaternion(MeisoQuaternion value)
{
    MeisoQuaternion result = {value.w, -value.x, -value.y, -value.z};
    return result;
}

static MeisoVec3 cross_product(MeisoVec3 lhs, MeisoVec3 rhs)
{
    MeisoVec3 result = {
        lhs.y * rhs.z - lhs.z * rhs.y,
        lhs.z * rhs.x - lhs.x * rhs.z,
        lhs.x * rhs.y - lhs.y * rhs.x
    };
    return result;
}

static MeisoVec3 add_vector(MeisoVec3 lhs, MeisoVec3 rhs)
{
    MeisoVec3 result = {lhs.x + rhs.x, lhs.y + rhs.y, lhs.z + rhs.z};
    return result;
}

static MeisoVec3 scale_vector(MeisoVec3 value, double scale)
{
    MeisoVec3 result = {value.x * scale, value.y * scale, value.z * scale};
    return result;
}

static MeisoVec3 rotate_vector(MeisoQuaternion rotation, MeisoVec3 value)
{
    MeisoVec3 axis = {rotation.x, rotation.y, rotation.z};
    MeisoVec3 twice_cross = scale_vector(cross_product(axis, value), 2.0);
    return add_vector(value, add_vector(
        scale_vector(twice_cross, rotation.w),
        cross_product(axis, twice_cross)
    ));
}

static bool calibration_valid(const MeisoCalibration *calibration, MeisoQuaternion *q_i_from_c)
{
    return calibration != NULL && isfinite(calibration->fx) &&
           isfinite(calibration->fy) && isfinite(calibration->cx) &&
           isfinite(calibration->cy) && isfinite(calibration->skew) &&
           calibration->fx > 0.0 && calibration->fy > 0.0 &&
           normalize_quaternion(calibration->q_i_from_c, q_i_from_c);
}

static bool project_corner(
    MeisoPoint2 source,
    const MeisoCalibration *calibration,
    MeisoQuaternion q_i_from_c,
    MeisoQuaternion q_w_from_i_source,
    MeisoQuaternion q_w_from_i_target,
    MeisoPoint2 *target
)
{
    double normalized_y;
    double normalized_x;
    double ray_norm;
    MeisoVec3 ray_camera_source;
    MeisoVec3 ray_imu_source;
    MeisoVec3 ray_world;
    MeisoVec3 ray_imu_target;
    MeisoVec3 ray_camera_target;

    normalized_y = (source.y - calibration->cy) / calibration->fy;
    normalized_x = (source.x - calibration->cx - calibration->skew * normalized_y) /
                   calibration->fx;
    ray_camera_source.x = normalized_x;
    ray_camera_source.y = normalized_y;
    ray_camera_source.z = 1.0;

    ray_imu_source = rotate_vector(q_i_from_c, ray_camera_source);
    ray_world = rotate_vector(q_w_from_i_source, ray_imu_source);
    ray_imu_target = rotate_vector(conjugate_quaternion(q_w_from_i_target), ray_world);
    ray_camera_target = rotate_vector(conjugate_quaternion(q_i_from_c), ray_imu_target);

    ray_norm = sqrt(ray_camera_target.x * ray_camera_target.x +
                    ray_camera_target.y * ray_camera_target.y +
                    ray_camera_target.z * ray_camera_target.z);
    if (!isfinite(ray_norm) || ray_norm <= 0.0 ||
        ray_camera_target.z <= 1e-6 * ray_norm) {
        return false;
    }

    target->x = calibration->fx * ray_camera_target.x / ray_camera_target.z +
                calibration->skew * ray_camera_target.y / ray_camera_target.z +
                calibration->cx;
    target->y = calibration->fy * ray_camera_target.y / ray_camera_target.z +
                calibration->cy;
    return isfinite(target->x) && isfinite(target->y);
}

bool meiso_frame_key_equal(MeisoFrameKey lhs, MeisoFrameKey rhs)
{
    return lhs.clock_epoch == rhs.clock_epoch &&
           lhs.stream_instance == rhs.stream_instance &&
           lhs.frame_sequence == rhs.frame_sequence;
}

static void loopback_clear_session_data(MeisoLoopback *link)
{
    memset(&link->intent_slot, 0, sizeof(link->intent_slot));
    memset(&link->camera_slot, 0, sizeof(link->camera_slot));
    memset(&link->imu_slot, 0, sizeof(link->imu_slot));
    memset(&link->overlay_slot, 0, sizeof(link->overlay_slot));
    link->intent_latest_version = 0U;
    link->overlay_latest_version = 0U;
    link->observation_drop_count = 0U;
    link->intent_ready = false;
    link->camera_ready = false;
    link->imu_ready = false;
    link->overlay_ready = false;
    link->intent_has_version = false;
    link->overlay_has_version = false;
}

void meiso_loopback_end_session(MeisoLoopback *link)
{
    if (link == NULL) {
        return;
    }
    loopback_clear_session_data(link);
    link->session_id = 0U;
}

void meiso_loopback_init(MeisoLoopback *link, uint8_t *bulk_storage, size_t bulk_capacity)
{
    if (link == NULL) {
        return;
    }
    memset(link, 0, sizeof(*link));
    link->bulk_storage = bulk_storage;
    link->bulk_capacity = bulk_capacity;
}

MeisoSessionStatus meiso_loopback_begin_session(MeisoLoopback *link, uint64_t session_id)
{
    if (link == NULL || session_id == 0U) {
        return MEISO_SESSION_INVALID;
    }
    if (link->has_session_history && session_id <= link->highest_session_id) {
        return MEISO_SESSION_NOT_NEWER;
    }
    loopback_clear_session_data(link);
    link->session_id = session_id;
    link->highest_session_id = session_id;
    link->has_session_history = true;
    return MEISO_SESSION_STARTED;
}

bool meiso_loopback_session_active(const MeisoLoopback *link)
{
    return link != NULL && link->session_id != 0U;
}

MeisoSendStatus meiso_loopback_send_capture_intent(
    MeisoLoopback *link,
    const MeisoCaptureIntent *intent
)
{
    MeisoSendStatus status = MEISO_SEND_QUEUED;

    if (link == NULL || intent == NULL || intent->session_id == 0U) {
        return MEISO_SEND_INVALID;
    }
    if (!meiso_loopback_session_active(link)) {
        return MEISO_SEND_SESSION_INACTIVE;
    }
    if (intent->session_id != link->session_id) {
        return MEISO_SEND_SESSION_MISMATCH;
    }
    if (link->intent_has_version) {
        if (link->intent_latest_version == UINT64_MAX &&
            intent->version < link->intent_latest_version) {
            meiso_loopback_end_session(link);
            return MEISO_SEND_VERSION_WRAP;
        }
        if (intent->version <= link->intent_latest_version) {
            return MEISO_SEND_STALE_VERSION;
        }
    }
    if (link->intent_ready) {
        status = MEISO_SEND_REPLACED;
    }
    link->intent_slot = *intent;
    link->intent_latest_version = intent->version;
    link->intent_has_version = true;
    link->intent_ready = true;
    return status;
}

bool meiso_loopback_receive_capture_intent(MeisoLoopback *link, MeisoCaptureIntent *intent)
{
    if (!meiso_loopback_session_active(link) || intent == NULL || !link->intent_ready) {
        return false;
    }
    *intent = link->intent_slot;
    link->intent_ready = false;
    return true;
}

MeisoSendStatus meiso_loopback_send_camera(MeisoLoopback *link, const MeisoCameraFrame *frame)
{
    size_t expected_size;

    if (link == NULL || !frame_shape_valid(frame, &expected_size)) {
        return MEISO_SEND_INVALID;
    }
    if (!meiso_loopback_session_active(link)) {
        return MEISO_SEND_SESSION_INACTIVE;
    }
    if (!frame->complete || frame->received_size != frame->payload_size) {
        return MEISO_SEND_INCOMPLETE_BULK;
    }
    if (link->bulk_storage == NULL || expected_size > link->bulk_capacity) {
        return MEISO_SEND_CAPACITY;
    }
    if (link->camera_ready) {
        return MEISO_SEND_BUSY;
    }
    memcpy(link->bulk_storage, frame->gray8, expected_size);
    link->camera_slot = *frame;
    link->camera_slot.gray8 = link->bulk_storage;
    link->camera_ready = true;
    return MEISO_SEND_QUEUED;
}

bool meiso_loopback_receive_camera(
    MeisoLoopback *link,
    uint8_t *receiver_storage,
    size_t receiver_capacity,
    MeisoCameraFrame *frame
)
{
    if (!meiso_loopback_session_active(link) || receiver_storage == NULL || frame == NULL ||
        !link->camera_ready ||
        link->camera_slot.payload_size > receiver_capacity) {
        return false;
    }
    memcpy(receiver_storage, link->bulk_storage, link->camera_slot.payload_size);
    *frame = link->camera_slot;
    frame->gray8 = receiver_storage;
    link->camera_ready = false;
    return true;
}

MeisoSendStatus meiso_loopback_send_imu(
    MeisoLoopback *link,
    const MeisoImuObservation *observation
)
{
    MeisoSendStatus status = MEISO_SEND_QUEUED;

    if (link == NULL || observation == NULL || !observation->valid ||
        !isfinite(observation->angular_velocity_rad_s[0]) ||
        !isfinite(observation->angular_velocity_rad_s[1]) ||
        !isfinite(observation->angular_velocity_rad_s[2])) {
        return MEISO_SEND_INVALID;
    }
    if (!meiso_loopback_session_active(link)) {
        return MEISO_SEND_SESSION_INACTIVE;
    }
    if (link->imu_ready) {
        link->observation_drop_count += 1U;
        status = MEISO_SEND_OBSERVATION_OVERWROTE;
    }
    link->imu_slot = *observation;
    link->imu_ready = true;
    return status;
}

bool meiso_loopback_receive_imu(MeisoLoopback *link, MeisoImuObservation *observation)
{
    if (!meiso_loopback_session_active(link) || observation == NULL || !link->imu_ready) {
        return false;
    }
    *observation = link->imu_slot;
    link->imu_ready = false;
    return true;
}

MeisoSendStatus meiso_loopback_send_overlay(MeisoLoopback *link, const MeisoOverlayState *overlay)
{
    MeisoSendStatus status = MEISO_SEND_QUEUED;

    if (link == NULL || overlay == NULL || overlay->session_id == 0U ||
        (!overlay->hide && !is_finite_box(overlay->box))) {
        return MEISO_SEND_INVALID;
    }
    if (!meiso_loopback_session_active(link)) {
        return MEISO_SEND_SESSION_INACTIVE;
    }
    if (overlay->session_id != link->session_id) {
        return MEISO_SEND_SESSION_MISMATCH;
    }
    if (link->overlay_has_version) {
        if (link->overlay_latest_version == UINT64_MAX &&
            overlay->version < link->overlay_latest_version) {
            meiso_loopback_end_session(link);
            return MEISO_SEND_VERSION_WRAP;
        }
        if (overlay->version <= link->overlay_latest_version) {
            return MEISO_SEND_STALE_VERSION;
        }
    }
    if (link->overlay_ready) {
        status = MEISO_SEND_REPLACED;
    }
    link->overlay_slot = *overlay;
    link->overlay_latest_version = overlay->version;
    link->overlay_has_version = true;
    link->overlay_ready = true;
    return status;
}

bool meiso_loopback_receive_overlay(MeisoLoopback *link, MeisoOverlayState *overlay)
{
    if (!meiso_loopback_session_active(link) || overlay == NULL || !link->overlay_ready) {
        return false;
    }
    *overlay = link->overlay_slot;
    link->overlay_ready = false;
    return true;
}

MeisoHostStatus meiso_host_detect_bright_box(
    const MeisoCameraFrame *frame,
    uint64_t session_id,
    uint64_t overlay_version,
    uint8_t threshold,
    MeisoOverlayState *overlay
)
{
    uint32_t x;
    uint32_t y;
    uint32_t min_x = UINT32_MAX;
    uint32_t min_y = UINT32_MAX;
    uint32_t max_x = 0U;
    uint32_t max_y = 0U;
    bool found = false;

    if (overlay == NULL || session_id == 0U || !frame_shape_valid(frame, NULL)) {
        return MEISO_HOST_INVALID_FRAME;
    }
    if (!frame_complete(frame)) {
        return MEISO_HOST_INCOMPLETE_BULK;
    }
    for (y = 0U; y < frame->height; ++y) {
        for (x = 0U; x < frame->width; ++x) {
            size_t index = (size_t)y * (size_t)frame->width + (size_t)x;
            if (frame->gray8[index] >= threshold) {
                if (x < min_x) {
                    min_x = x;
                }
                if (x > max_x) {
                    max_x = x;
                }
                if (y < min_y) {
                    min_y = y;
                }
                if (y > max_y) {
                    max_y = y;
                }
                found = true;
            }
        }
    }

    memset(overlay, 0, sizeof(*overlay));
    overlay->session_id = session_id;
    overlay->version = overlay_version;
    overlay->source_key = frame->key;
    overlay->hide = !found;
    if (!found) {
        return MEISO_HOST_HIDE;
    }
    overlay->box.left = (double)min_x;
    overlay->box.top = (double)min_y;
    overlay->box.right = (double)max_x;
    overlay->box.bottom = (double)max_y;
    return MEISO_HOST_BOX;
}

MeisoSessionStatus meiso_capture_begin_session(MeisoCaptureState *state, uint64_t session_id)
{
    if (state == NULL || session_id == 0U) {
        return MEISO_SESSION_INVALID;
    }
    if (state->has_session_history && session_id <= state->highest_session_id) {
        return MEISO_SESSION_NOT_NEWER;
    }
    state->session_id = session_id;
    state->highest_session_id = session_id;
    state->last_intent_version = 0U;
    state->local_lease_deadline_ns = 0U;
    state->has_session_history = true;
    state->has_intent_version = false;
    state->requested_enabled = false;
    return MEISO_SESSION_STARTED;
}

void meiso_capture_end_session(MeisoCaptureState *state)
{
    if (state == NULL) {
        return;
    }
    state->session_id = 0U;
    state->last_intent_version = 0U;
    state->local_lease_deadline_ns = 0U;
    state->has_intent_version = false;
    state->requested_enabled = false;
}

MeisoCaptureStatus meiso_capture_ingest_intent(
    MeisoCaptureState *state,
    const MeisoCaptureIntent *intent,
    uint64_t edge_now_ns
)
{
    if (state == NULL || intent == NULL || state->session_id == 0U ||
        intent->session_id == 0U) {
        return MEISO_CAPTURE_INVALID;
    }
    if (intent->session_id != state->session_id) {
        return MEISO_CAPTURE_SESSION_MISMATCH;
    }
    if (state->has_intent_version) {
        if (intent->version == state->last_intent_version) {
            return MEISO_CAPTURE_DUPLICATE_VERSION;
        }
        if (state->last_intent_version == UINT64_MAX &&
            intent->version < state->last_intent_version) {
            meiso_capture_end_session(state);
            return MEISO_CAPTURE_VERSION_WRAP;
        }
        if (intent->version < state->last_intent_version) {
            return MEISO_CAPTURE_STALE_VERSION;
        }
    }
    if (intent->enabled &&
        (intent->lease_duration_ns == 0U || edge_now_ns > UINT64_MAX - intent->lease_duration_ns)) {
        return MEISO_CAPTURE_INVALID;
    }
    state->last_intent_version = intent->version;
    state->has_intent_version = true;
    state->requested_enabled = intent->enabled;
    state->local_lease_deadline_ns = intent->enabled
        ? edge_now_ns + intent->lease_duration_ns
        : edge_now_ns;
    return intent->enabled ? MEISO_CAPTURE_ACCEPTED : MEISO_CAPTURE_DISABLED;
}

bool meiso_capture_is_active(const MeisoCaptureState *state, uint64_t edge_now_ns)
{
    return state != NULL && state->session_id != 0U && state->requested_enabled &&
           edge_now_ns < state->local_lease_deadline_ns;
}

MeisoDisplayAction meiso_edge_end_session(MeisoEdgeState *state)
{
    if (state != NULL) {
        state->session_id = 0U;
        state->last_overlay_version = 0U;
        memset(&state->current_overlay, 0, sizeof(state->current_overlay));
        state->has_overlay_version = false;
        state->has_overlay = false;
    }
    return MEISO_DISPLAY_HIDE;
}

MeisoSessionStatus meiso_edge_begin_session(
    MeisoEdgeState *state,
    uint64_t session_id,
    MeisoDisplayAction *action
)
{
    if (action == NULL) {
        return MEISO_SESSION_INVALID;
    }
    *action = MEISO_DISPLAY_KEEP;
    if (state == NULL || session_id == 0U) {
        return MEISO_SESSION_INVALID;
    }
    if (state->has_session_history && session_id <= state->highest_session_id) {
        return MEISO_SESSION_NOT_NEWER;
    }
    (void)meiso_edge_end_session(state);
    state->session_id = session_id;
    state->highest_session_id = session_id;
    state->has_session_history = true;
    *action = MEISO_DISPLAY_HIDE;
    return MEISO_SESSION_STARTED;
}

MeisoDropReason meiso_edge_ingest_overlay(
    MeisoEdgeState *state,
    const MeisoOverlayState *overlay,
    MeisoDisplayAction *action
)
{
    if (action == NULL) {
        return MEISO_DROP_INVALID_INPUT;
    }
    *action = MEISO_DISPLAY_KEEP;
    if (state == NULL || overlay == NULL || state->session_id == 0U ||
        overlay->session_id == 0U || (!overlay->hide && !is_finite_box(overlay->box))) {
        return MEISO_DROP_INVALID_INPUT;
    }
    if (overlay->session_id != state->session_id) {
        return MEISO_DROP_SESSION_MISMATCH;
    }
    if (state->has_overlay_version) {
        if (overlay->version == state->last_overlay_version) {
            return MEISO_DROP_DUPLICATE_VERSION;
        }
        if (state->last_overlay_version == UINT64_MAX &&
            overlay->version < state->last_overlay_version) {
            *action = meiso_edge_end_session(state);
            return MEISO_DROP_VERSION_WRAP;
        }
        if (overlay->version < state->last_overlay_version) {
            return MEISO_DROP_STALE_VERSION;
        }
    }
    state->current_overlay = *overlay;
    state->last_overlay_version = overlay->version;
    state->has_overlay_version = true;
    state->has_overlay = true;
    *action = MEISO_DISPLAY_HIDE;
    return MEISO_DROP_NONE;
}

MeisoDropReason meiso_edge_render_overlay(
    const MeisoEdgeState *state,
    const MeisoCameraFrame *source_frame,
    const MeisoCameraFrame *target_frame,
    const MeisoOrientation *source_orientation,
    const MeisoOrientation *target_orientation,
    const MeisoCalibration *calibration,
    const MeisoSliceLimits *limits,
    MeisoComposeResult *result
)
{
    MeisoQuaternion q_i_from_c;
    MeisoQuaternion q_w_from_i_source;
    MeisoQuaternion q_w_from_i_target;
    MeisoPoint2 source_corners[4];
    const MeisoOverlayState *overlay;
    size_t index;

#define RETURN_REASON(value) do { \
    result->reason = (value); \
    result->action = (value) == MEISO_DROP_NONE ? MEISO_DISPLAY_SHOW : MEISO_DISPLAY_HIDE; \
    return (value); \
} while (0)

    if (result == NULL) {
        return MEISO_DROP_INVALID_INPUT;
    }
    memset(result, 0, sizeof(*result));
    result->reason = MEISO_DROP_INVALID_INPUT;
    result->action = MEISO_DISPLAY_HIDE;
    if (state == NULL || source_frame == NULL || target_frame == NULL ||
        source_orientation == NULL || target_orientation == NULL || limits == NULL ||
        state->session_id == 0U) {
        return MEISO_DROP_INVALID_INPUT;
    }
    if (!state->has_overlay) {
        RETURN_REASON(MEISO_DROP_NO_OVERLAY);
    }
    overlay = &state->current_overlay;
    if (overlay->session_id != state->session_id) {
        RETURN_REASON(MEISO_DROP_SESSION_MISMATCH);
    }

    result->source_key = overlay->source_key;
    result->target_key = target_frame->key;
    result->overlay_version = overlay->version;

    if (overlay->hide) {
        result->hidden = true;
        RETURN_REASON(MEISO_DROP_HIDDEN);
    }
    if (overlay->source_key.clock_epoch != source_frame->key.clock_epoch ||
        target_frame->key.clock_epoch != source_frame->key.clock_epoch) {
        RETURN_REASON(MEISO_DROP_WRONG_CLOCK_EPOCH);
    }
    if (overlay->source_key.stream_instance != source_frame->key.stream_instance ||
        target_frame->key.stream_instance != source_frame->key.stream_instance) {
        RETURN_REASON(MEISO_DROP_STREAM_INSTANCE_MISMATCH);
    }
    if (overlay->source_key.frame_sequence != source_frame->key.frame_sequence) {
        RETURN_REASON(MEISO_DROP_SOURCE_FRAME_NOT_RETAINED);
    }
    if (target_frame->key.frame_sequence < source_frame->key.frame_sequence ||
        target_frame->timestamp_ns < source_frame->timestamp_ns) {
        RETURN_REASON(MEISO_DROP_TARGET_PRECEDES_SOURCE);
    }
    if (target_frame->timestamp_ns - source_frame->timestamp_ns > limits->max_source_age_ns) {
        RETURN_REASON(MEISO_DROP_SOURCE_FRAME_TOO_OLD);
    }
    if (!frame_complete(source_frame) || !frame_complete(target_frame)) {
        RETURN_REASON(MEISO_DROP_INCOMPLETE_BULK);
    }
    if (calibration == NULL || !calibration->valid) {
        RETURN_REASON(MEISO_DROP_CALIBRATION_MISSING);
    }
    if (calibration->stream_instance != source_frame->key.stream_instance ||
        calibration->image_width != source_frame->width ||
        calibration->image_height != source_frame->height ||
        calibration->image_width != target_frame->width ||
        calibration->image_height != target_frame->height) {
        RETURN_REASON(MEISO_DROP_CALIBRATION_MISMATCH);
    }
    if (!calibration_valid(calibration, &q_i_from_c)) {
        RETURN_REASON(MEISO_DROP_CALIBRATION_MISMATCH);
    }
    if (!source_orientation->valid || !target_orientation->valid ||
        !normalize_quaternion(source_orientation->q_w_from_i, &q_w_from_i_source) ||
        !normalize_quaternion(target_orientation->q_w_from_i, &q_w_from_i_target)) {
        RETURN_REASON(MEISO_DROP_POSE_MISSING);
    }
    if (source_orientation->clock_epoch != source_frame->key.clock_epoch ||
        target_orientation->clock_epoch != target_frame->key.clock_epoch) {
        RETURN_REASON(MEISO_DROP_POSE_EPOCH);
    }
    if (abs_diff_u64(source_orientation->timestamp_ns, source_frame->timestamp_ns) >
            limits->max_pose_gap_ns ||
        abs_diff_u64(target_orientation->timestamp_ns, target_frame->timestamp_ns) >
            limits->max_pose_gap_ns) {
        RETURN_REASON(MEISO_DROP_POSE_GAP);
    }
    if (source_orientation->support_start_ns > source_frame->timestamp_ns ||
        source_orientation->support_end_ns < source_frame->timestamp_ns ||
        source_orientation->support_end_ns < source_orientation->support_start_ns ||
        target_orientation->support_start_ns > target_frame->timestamp_ns ||
        target_orientation->support_end_ns < target_frame->timestamp_ns ||
        target_orientation->support_end_ns < target_orientation->support_start_ns ||
        source_orientation->support_end_ns - source_orientation->support_start_ns >
            limits->max_pose_support_gap_ns ||
        target_orientation->support_end_ns - target_orientation->support_start_ns >
            limits->max_pose_support_gap_ns) {
        RETURN_REASON(MEISO_DROP_POSE_SUPPORT_GAP);
    }
    if (!isfinite(source_orientation->uncertainty_rad) ||
        !isfinite(target_orientation->uncertainty_rad) ||
        !isfinite(limits->max_orientation_uncertainty_rad) ||
        source_orientation->uncertainty_rad < 0.0 ||
        target_orientation->uncertainty_rad < 0.0 ||
        limits->max_orientation_uncertainty_rad < 0.0 ||
        source_orientation->uncertainty_rad > limits->max_orientation_uncertainty_rad ||
        target_orientation->uncertainty_rad > limits->max_orientation_uncertainty_rad) {
        RETURN_REASON(MEISO_DROP_POSE_UNCERTAIN);
    }

    source_corners[0].x = overlay->box.left;
    source_corners[0].y = overlay->box.top;
    source_corners[1].x = overlay->box.right;
    source_corners[1].y = overlay->box.top;
    source_corners[2].x = overlay->box.right;
    source_corners[2].y = overlay->box.bottom;
    source_corners[3].x = overlay->box.left;
    source_corners[3].y = overlay->box.bottom;
    for (index = 0U; index < 4U; ++index) {
        if (!project_corner(
                source_corners[index],
                calibration,
                q_i_from_c,
                q_w_from_i_source,
                q_w_from_i_target,
                &result->quad[index])) {
            RETURN_REASON(MEISO_DROP_PROJECTION_INVALID);
        }
    }
    RETURN_REASON(MEISO_DROP_NONE);

#undef RETURN_REASON
}

const char *meiso_send_status_name(MeisoSendStatus status)
{
    static const char *const names[] = {
        "queued",
        "replaced",
        "observation-overwrote",
        "busy",
        "incomplete-bulk",
        "capacity",
        "stale-version",
        "version-wrap",
        "session-mismatch",
        "session-inactive",
        "invalid"
    };
    size_t index = (size_t)status;
    return index < sizeof(names) / sizeof(names[0]) ? names[index] : "unknown";
}

const char *meiso_drop_reason_name(MeisoDropReason reason)
{
    static const char *const names[] = {
        "none",
        "hidden",
        "invalid-input",
        "no-overlay",
        "session-mismatch",
        "duplicate-version",
        "stale-version",
        "version-wrap",
        "wrong-clock-epoch",
        "stream-instance-mismatch",
        "source-frame-not-retained",
        "target-precedes-source",
        "source-frame-too-old",
        "incomplete-bulk",
        "calibration-missing",
        "calibration-mismatch",
        "pose-missing",
        "pose-epoch",
        "pose-gap",
        "pose-support-gap",
        "pose-uncertain",
        "projection-invalid"
    };
    size_t index = (size_t)reason;
    return index < sizeof(names) / sizeof(names[0]) ? names[index] : "unknown";
}
