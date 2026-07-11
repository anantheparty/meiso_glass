#ifndef MEISO_SLICE_H
#define MEISO_SLICE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint64_t clock_epoch;
    uint64_t stream_instance;
    uint64_t frame_sequence;
} MeisoFrameKey;

typedef struct {
    double w;
    double x;
    double y;
    double z;
} MeisoQuaternion;

typedef struct {
    uint64_t clock_epoch;
    uint64_t timestamp_ns;
    uint64_t support_start_ns;
    uint64_t support_end_ns;
    MeisoQuaternion q_w_from_i;
    double uncertainty_rad;
    bool valid;
} MeisoOrientation;

typedef struct {
    uint64_t clock_epoch;
    uint64_t stream_instance;
    uint64_t sample_sequence;
    uint64_t timestamp_ns;
    double angular_velocity_rad_s[3];
    bool valid;
} MeisoImuObservation;

typedef struct {
    bool valid;
    uint64_t stream_instance;
    uint32_t image_width;
    uint32_t image_height;
    double fx;
    double fy;
    double cx;
    double cy;
    double skew;
    MeisoQuaternion q_i_from_c;
} MeisoCalibration;

typedef struct {
    double left;
    double top;
    double right;
    double bottom;
} MeisoBox;

typedef struct {
    double x;
    double y;
} MeisoPoint2;

typedef struct {
    uint64_t session_id;
    uint64_t version;
    bool enabled;
    uint64_t lease_duration_ns;
} MeisoCaptureIntent;

typedef struct {
    MeisoFrameKey key;
    uint64_t timestamp_ns;
    uint32_t width;
    uint32_t height;
    const uint8_t *gray8;
    size_t payload_size;
    size_t received_size;
    bool complete;
} MeisoCameraFrame;

typedef struct {
    uint64_t session_id;
    uint64_t version;
    MeisoFrameKey source_key;
    MeisoBox box;
    bool hide;
} MeisoOverlayState;

typedef enum {
    MEISO_SEND_QUEUED = 0,
    MEISO_SEND_REPLACED,
    MEISO_SEND_OBSERVATION_OVERWROTE,
    MEISO_SEND_BUSY,
    MEISO_SEND_INCOMPLETE_BULK,
    MEISO_SEND_CAPACITY,
    MEISO_SEND_STALE_VERSION,
    MEISO_SEND_VERSION_WRAP,
    MEISO_SEND_SESSION_MISMATCH,
    MEISO_SEND_SESSION_INACTIVE,
    MEISO_SEND_INVALID
} MeisoSendStatus;

typedef enum {
    MEISO_HOST_BOX = 0,
    MEISO_HOST_HIDE,
    MEISO_HOST_INCOMPLETE_BULK,
    MEISO_HOST_INVALID_FRAME
} MeisoHostStatus;

typedef enum {
    MEISO_SESSION_STARTED = 0,
    MEISO_SESSION_NOT_NEWER,
    MEISO_SESSION_INVALID
} MeisoSessionStatus;

typedef enum {
    MEISO_CAPTURE_ACCEPTED = 0,
    MEISO_CAPTURE_DISABLED,
    MEISO_CAPTURE_SESSION_MISMATCH,
    MEISO_CAPTURE_DUPLICATE_VERSION,
    MEISO_CAPTURE_STALE_VERSION,
    MEISO_CAPTURE_VERSION_WRAP,
    MEISO_CAPTURE_INVALID
} MeisoCaptureStatus;

typedef enum {
    MEISO_DISPLAY_KEEP = 0,
    MEISO_DISPLAY_HIDE,
    MEISO_DISPLAY_SHOW
} MeisoDisplayAction;

typedef enum {
    MEISO_DROP_NONE = 0,
    MEISO_DROP_HIDDEN,
    MEISO_DROP_INVALID_INPUT,
    MEISO_DROP_NO_OVERLAY,
    MEISO_DROP_SESSION_MISMATCH,
    MEISO_DROP_DUPLICATE_VERSION,
    MEISO_DROP_STALE_VERSION,
    MEISO_DROP_VERSION_WRAP,
    MEISO_DROP_WRONG_CLOCK_EPOCH,
    MEISO_DROP_STREAM_INSTANCE_MISMATCH,
    MEISO_DROP_SOURCE_FRAME_NOT_RETAINED,
    MEISO_DROP_TARGET_PRECEDES_SOURCE,
    MEISO_DROP_SOURCE_FRAME_TOO_OLD,
    MEISO_DROP_INCOMPLETE_BULK,
    MEISO_DROP_CALIBRATION_MISSING,
    MEISO_DROP_CALIBRATION_MISMATCH,
    MEISO_DROP_POSE_MISSING,
    MEISO_DROP_POSE_EPOCH,
    MEISO_DROP_POSE_GAP,
    MEISO_DROP_POSE_SUPPORT_GAP,
    MEISO_DROP_POSE_UNCERTAIN,
    MEISO_DROP_PROJECTION_INVALID
} MeisoDropReason;

typedef struct {
    uint64_t max_source_age_ns;
    uint64_t max_pose_gap_ns;
    uint64_t max_pose_support_gap_ns;
    double max_orientation_uncertainty_rad;
} MeisoSliceLimits;

typedef struct {
    uint64_t session_id;
    uint64_t highest_session_id;
    uint64_t last_intent_version;
    uint64_t local_lease_deadline_ns;
    bool has_session_history;
    bool has_intent_version;
    bool requested_enabled;
} MeisoCaptureState;

typedef struct {
    uint64_t session_id;
    uint64_t highest_session_id;
    uint64_t last_overlay_version;
    MeisoOverlayState current_overlay;
    bool has_session_history;
    bool has_overlay_version;
    bool has_overlay;
} MeisoEdgeState;

typedef struct {
    MeisoDropReason reason;
    MeisoDisplayAction action;
    bool hidden;
    MeisoFrameKey source_key;
    MeisoFrameKey target_key;
    uint64_t overlay_version;
    MeisoPoint2 quad[4];
} MeisoComposeResult;

typedef struct {
    uint8_t *bulk_storage;
    size_t bulk_capacity;
    MeisoCaptureIntent intent_slot;
    MeisoCameraFrame camera_slot;
    MeisoImuObservation imu_slot;
    MeisoOverlayState overlay_slot;
    uint64_t observation_drop_count;
    uint64_t session_id;
    uint64_t highest_session_id;
    uint64_t intent_latest_version;
    uint64_t overlay_latest_version;
    bool has_session_history;
    bool intent_ready;
    bool camera_ready;
    bool imu_ready;
    bool overlay_ready;
    bool intent_has_version;
    bool overlay_has_version;
} MeisoLoopback;

bool meiso_frame_key_equal(MeisoFrameKey lhs, MeisoFrameKey rhs);

void meiso_loopback_init(MeisoLoopback *link, uint8_t *bulk_storage, size_t bulk_capacity);
MeisoSessionStatus meiso_loopback_begin_session(MeisoLoopback *link, uint64_t session_id);
void meiso_loopback_end_session(MeisoLoopback *link);
bool meiso_loopback_session_active(const MeisoLoopback *link);
MeisoSendStatus meiso_loopback_send_capture_intent(MeisoLoopback *link, const MeisoCaptureIntent *intent);
bool meiso_loopback_receive_capture_intent(MeisoLoopback *link, MeisoCaptureIntent *intent);
MeisoSendStatus meiso_loopback_send_camera(MeisoLoopback *link, const MeisoCameraFrame *frame);
bool meiso_loopback_receive_camera(
    MeisoLoopback *link,
    uint8_t *receiver_storage,
    size_t receiver_capacity,
    MeisoCameraFrame *frame
);
MeisoSendStatus meiso_loopback_send_imu(MeisoLoopback *link, const MeisoImuObservation *observation);
bool meiso_loopback_receive_imu(MeisoLoopback *link, MeisoImuObservation *observation);
MeisoSendStatus meiso_loopback_send_overlay(MeisoLoopback *link, const MeisoOverlayState *overlay);
bool meiso_loopback_receive_overlay(MeisoLoopback *link, MeisoOverlayState *overlay);

MeisoHostStatus meiso_host_detect_bright_box(
    const MeisoCameraFrame *frame,
    uint64_t session_id,
    uint64_t overlay_version,
    uint8_t threshold,
    MeisoOverlayState *overlay
);

MeisoSessionStatus meiso_capture_begin_session(MeisoCaptureState *state, uint64_t session_id);
void meiso_capture_end_session(MeisoCaptureState *state);
MeisoCaptureStatus meiso_capture_ingest_intent(
    MeisoCaptureState *state,
    const MeisoCaptureIntent *intent,
    uint64_t edge_now_ns
);
bool meiso_capture_is_active(const MeisoCaptureState *state, uint64_t edge_now_ns);

MeisoSessionStatus meiso_edge_begin_session(
    MeisoEdgeState *state,
    uint64_t session_id,
    MeisoDisplayAction *action
);
MeisoDisplayAction meiso_edge_end_session(MeisoEdgeState *state);
MeisoDropReason meiso_edge_ingest_overlay(
    MeisoEdgeState *state,
    const MeisoOverlayState *overlay,
    MeisoDisplayAction *action
);
MeisoDropReason meiso_edge_render_overlay(
    const MeisoEdgeState *state,
    const MeisoCameraFrame *source_frame,
    const MeisoCameraFrame *target_frame,
    const MeisoOrientation *source_orientation,
    const MeisoOrientation *target_orientation,
    const MeisoCalibration *calibration,
    const MeisoSliceLimits *limits,
    MeisoComposeResult *result
);

const char *meiso_send_status_name(MeisoSendStatus status);
const char *meiso_drop_reason_name(MeisoDropReason reason);

#ifdef __cplusplus
}
#endif

#endif
