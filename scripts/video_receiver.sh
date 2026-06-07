#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-5000}"
DECODER="${DECODER:-avdec_h264 ! videoconvert ! autovideosink sync=false}"

gst-launch-1.0 -v udpsrc port="${PORT}" caps="application/x-rtp, media=(string)video, encoding-name=(string)H264, payload=(int)96" \
  ! rtph264depay \
  ! h264parse \
  ! ${DECODER}
