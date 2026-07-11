#include "meiso_slice.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
    DEMO_WIDTH = 160,
    DEMO_HEIGHT = 120,
    DEMO_PIXELS = DEMO_WIDTH * DEMO_HEIGHT
};

static uint8_t source_pixels[DEMO_PIXELS];
static uint8_t target_pixels[DEMO_PIXELS];
static uint8_t loopback_bulk[DEMO_PIXELS];
static uint8_t host_frame_storage[DEMO_PIXELS];
static uint8_t preview_rgb[DEMO_PIXELS * 3];

static void put_red_pixel(int x, int y)
{
    size_t index;

    if (x < 0 || y < 0 || x >= DEMO_WIDTH || y >= DEMO_HEIGHT) {
        return;
    }
    index = ((size_t)y * DEMO_WIDTH + (size_t)x) * 3U;
    preview_rgb[index] = 255U;
    preview_rgb[index + 1U] = 32U;
    preview_rgb[index + 2U] = 32U;
}

static unsigned int viewport_code(double x, double y)
{
    unsigned int code = 0U;
    if (x < 0.0) {
        code |= 1U;
    } else if (x > (double)(DEMO_WIDTH - 1)) {
        code |= 2U;
    }
    if (y < 0.0) {
        code |= 4U;
    } else if (y > (double)(DEMO_HEIGHT - 1)) {
        code |= 8U;
    }
    return code;
}

static bool clip_line_to_viewport(double *x0, double *y0, double *x1, double *y1)
{
    unsigned int iteration;

    if (!isfinite(*x0) || !isfinite(*y0) || !isfinite(*x1) || !isfinite(*y1)) {
        return false;
    }
    for (iteration = 0U; iteration < 8U; ++iteration) {
        unsigned int code0 = viewport_code(*x0, *y0);
        unsigned int code1 = viewport_code(*x1, *y1);
        unsigned int outside;
        double x;
        double y;

        if ((code0 | code1) == 0U) {
            return true;
        }
        if ((code0 & code1) != 0U) {
            return false;
        }
        outside = code0 != 0U ? code0 : code1;
        if ((outside & 8U) != 0U) {
            if (*y1 == *y0) {
                return false;
            }
            y = (double)(DEMO_HEIGHT - 1);
            x = *x0 + (*x1 - *x0) * (y - *y0) / (*y1 - *y0);
        } else if ((outside & 4U) != 0U) {
            if (*y1 == *y0) {
                return false;
            }
            y = 0.0;
            x = *x0 + (*x1 - *x0) * (y - *y0) / (*y1 - *y0);
        } else if ((outside & 2U) != 0U) {
            if (*x1 == *x0) {
                return false;
            }
            x = (double)(DEMO_WIDTH - 1);
            y = *y0 + (*y1 - *y0) * (x - *x0) / (*x1 - *x0);
        } else {
            if (*x1 == *x0) {
                return false;
            }
            x = 0.0;
            y = *y0 + (*y1 - *y0) * (x - *x0) / (*x1 - *x0);
        }
        if (outside == code0) {
            *x0 = x;
            *y0 = y;
        } else {
            *x1 = x;
            *y1 = y;
        }
    }
    return false;
}

static void draw_line(MeisoPoint2 start, MeisoPoint2 end)
{
    double clipped_x0 = start.x;
    double clipped_y0 = start.y;
    double clipped_x1 = end.x;
    double clipped_y1 = end.y;
    int x0;
    int y0;
    int x1;
    int y1;
    int dx;
    int sx;
    int dy;
    int sy;
    int error;

    if (!clip_line_to_viewport(&clipped_x0, &clipped_y0, &clipped_x1, &clipped_y1)) {
        return;
    }
    x0 = (int)lround(clipped_x0);
    y0 = (int)lround(clipped_y0);
    x1 = (int)lround(clipped_x1);
    y1 = (int)lround(clipped_y1);
    dx = abs(x1 - x0);
    sx = x0 < x1 ? 1 : -1;
    dy = -abs(y1 - y0);
    sy = y0 < y1 ? 1 : -1;
    error = dx + dy;

    for (;;) {
        int twice_error;
        put_red_pixel(x0, y0);
        if (x0 == x1 && y0 == y1) {
            break;
        }
        twice_error = 2 * error;
        if (twice_error >= dy) {
            error += dy;
            x0 += sx;
        }
        if (twice_error <= dx) {
            error += dx;
            y0 += sy;
        }
    }
}

static bool write_preview(const char *path, const MeisoComposeResult *result)
{
    FILE *file;
    size_t index;

    for (index = 0U; index < DEMO_PIXELS; ++index) {
        uint8_t gray = target_pixels[index];
        preview_rgb[index * 3U] = gray;
        preview_rgb[index * 3U + 1U] = gray;
        preview_rgb[index * 3U + 2U] = gray;
    }
    for (index = 0U; index < 4U; ++index) {
        draw_line(result->quad[index], result->quad[(index + 1U) % 4U]);
    }

    file = fopen(path, "wb");
    if (file == NULL) {
        return false;
    }
    if (fprintf(file, "P6\n%d %d\n255\n", DEMO_WIDTH, DEMO_HEIGHT) < 0 ||
        fwrite(preview_rgb, 1U, sizeof(preview_rgb), file) != sizeof(preview_rgb)) {
        fclose(file);
        return false;
    }
    return fclose(file) == 0;
}

int main(int argc, char **argv)
{
    const char *output_path = argc > 1 ? argv[1] : "slice_preview.ppm";
    const uint64_t session_id = 1U;
    const double target_angle_rad = 0.13962634015954636;
    MeisoLoopback link;
    MeisoCaptureIntent intent = {session_id, 1U, true, 1000000000U};
    MeisoCaptureIntent received_intent;
    MeisoCaptureState capture_state = {0};
    MeisoFrameKey source_key = {7U, 3U, 100U};
    MeisoFrameKey target_key = {7U, 3U, 101U};
    MeisoCameraFrame source_frame;
    MeisoCameraFrame received_frame;
    MeisoCameraFrame target_frame;
    MeisoImuObservation imu = {
        7U, 1U, 1U, 1000000000U, {0.0, 6.981317007977318, 0.0}, true
    };
    MeisoImuObservation received_imu;
    MeisoOverlayState overlay;
    MeisoOverlayState received_overlay;
    MeisoOrientation source_orientation = {
        7U,
        1000000000U,
        1000000000U,
        1000000000U,
        {1.0, 0.0, 0.0, 0.0},
        0.001,
        true
    };
    MeisoOrientation target_orientation = {
        7U,
        1020000000U,
        1000000000U,
        1020000000U,
        {1.0, 0.0, 0.0, 0.0},
        0.001,
        true
    };
    MeisoCalibration calibration = {
        true,
        3U,
        DEMO_WIDTH,
        DEMO_HEIGHT,
        140.0,
        140.0,
        80.0,
        60.0,
        0.0,
        {1.0, 0.0, 0.0, 0.0}
    };
    MeisoSliceLimits limits = {50000000U, 1000000U, 20000000U, 0.01};
    MeisoEdgeState edge_state = {0};
    MeisoComposeResult composition;
    MeisoHostStatus host_status;
    MeisoDropReason compose_status;
    MeisoDisplayAction ingest_action;
    double integrated_angle;
    size_t x;
    size_t y;

    memset(source_pixels, 24, sizeof(source_pixels));
    memset(target_pixels, 48, sizeof(target_pixels));
    for (y = 45U; y <= 75U; ++y) {
        for (x = 65U; x <= 95U; ++x) {
            source_pixels[y * DEMO_WIDTH + x] = 240U;
        }
    }
    for (y = 44U; y <= 76U; ++y) {
        for (x = 44U; x <= 75U; ++x) {
            target_pixels[y * DEMO_WIDTH + x] = 120U;
        }
    }

    source_frame = (MeisoCameraFrame){
        source_key,
        1000000000U,
        DEMO_WIDTH,
        DEMO_HEIGHT,
        source_pixels,
        sizeof(source_pixels),
        sizeof(source_pixels),
        true
    };
    target_frame = (MeisoCameraFrame){
        target_key,
        1020000000U,
        DEMO_WIDTH,
        DEMO_HEIGHT,
        target_pixels,
        sizeof(target_pixels),
        sizeof(target_pixels),
        true
    };

    integrated_angle = imu.angular_velocity_rad_s[1] *
        (double)(target_frame.timestamp_ns - source_frame.timestamp_ns) * 1e-9;
    if (fabs(integrated_angle - target_angle_rad) > 1e-12) {
        fprintf(stderr, "synthetic IMU integration mismatch\n");
        return 1;
    }
    target_orientation.q_w_from_i.w = cos(0.5 * integrated_angle);
    target_orientation.q_w_from_i.y = sin(0.5 * integrated_angle);

    meiso_loopback_init(&link, loopback_bulk, sizeof(loopback_bulk));
    if (meiso_loopback_begin_session(&link, session_id) != MEISO_SESSION_STARTED ||
        meiso_loopback_send_capture_intent(&link, &intent) != MEISO_SEND_QUEUED ||
        !meiso_loopback_receive_capture_intent(&link, &received_intent) ||
        !received_intent.enabled) {
        fprintf(stderr, "capture intent failed\n");
        return 1;
    }
    if (meiso_capture_begin_session(&capture_state, session_id) != MEISO_SESSION_STARTED ||
        meiso_capture_ingest_intent(&capture_state, &received_intent, 900000000U) !=
            MEISO_CAPTURE_ACCEPTED ||
        !meiso_capture_is_active(&capture_state, source_frame.timestamp_ns) ||
        meiso_capture_is_active(&capture_state, 1900000000U)) {
        fprintf(stderr, "capture lease failed\n");
        return 1;
    }
    if (meiso_loopback_send_camera(&link, &source_frame) != MEISO_SEND_QUEUED ||
        meiso_loopback_send_imu(&link, &imu) != MEISO_SEND_QUEUED ||
        !meiso_loopback_receive_camera(
            &link, host_frame_storage, sizeof(host_frame_storage), &received_frame) ||
        !meiso_loopback_receive_imu(&link, &received_imu)) {
        fprintf(stderr, "Edge to Host transfer failed\n");
        return 1;
    }
    if (received_imu.clock_epoch != source_key.clock_epoch ||
        received_imu.stream_instance != 1U || received_imu.sample_sequence != 1U ||
        received_imu.timestamp_ns != source_frame.timestamp_ns ||
        fabs(received_imu.angular_velocity_rad_s[1] -
             imu.angular_velocity_rad_s[1]) > 1e-12) {
        fprintf(stderr, "IMU association failed\n");
        return 1;
    }

    host_status = meiso_host_detect_bright_box(
        &received_frame, session_id, 1U, 200U, &overlay
    );
    if (host_status != MEISO_HOST_BOX ||
        meiso_loopback_send_overlay(&link, &overlay) != MEISO_SEND_QUEUED ||
        !meiso_loopback_receive_overlay(&link, &received_overlay)) {
        fprintf(stderr, "Host overlay failed\n");
        return 1;
    }

    if (meiso_edge_begin_session(&edge_state, session_id, &ingest_action) !=
            MEISO_SESSION_STARTED || ingest_action != MEISO_DISPLAY_HIDE ||
        meiso_edge_ingest_overlay(&edge_state, &received_overlay, &ingest_action) !=
            MEISO_DROP_NONE || ingest_action != MEISO_DISPLAY_HIDE) {
        fprintf(stderr, "Edge overlay ingest failed\n");
        return 1;
    }
    compose_status = meiso_edge_render_overlay(
        &edge_state,
        &source_frame,
        &target_frame,
        &source_orientation,
        &target_orientation,
        &calibration,
        &limits,
        &composition
    );
    if (compose_status != MEISO_DROP_NONE || composition.action != MEISO_DISPLAY_SHOW) {
        fprintf(stderr, "Edge composition dropped: %s\n", meiso_drop_reason_name(compose_status));
        return 1;
    }
    if (!write_preview(output_path, &composition)) {
        fprintf(stderr, "preview write failed\n");
        return 1;
    }

    printf(
        "source=%llu target=%llu overlay=%llu result=%s preview=%s\n",
        (unsigned long long)composition.source_key.frame_sequence,
        (unsigned long long)composition.target_key.frame_sequence,
        (unsigned long long)composition.overlay_version,
        meiso_drop_reason_name(composition.reason),
        output_path
    );
    return 0;
}
