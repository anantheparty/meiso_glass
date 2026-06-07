#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-127.0.0.1}"
PORT="${2:-5000}"
WIDTH="${WIDTH:-1280}"
HEIGHT="${HEIGHT:-720}"
FPS="${FPS:-30}"
ENCODER="${ENCODER:-x264enc tune=zerolatency speed-preset=ultrafast bitrate=4000 key-int-max=30}"

gst-launch-1.0 -v videotestsrc is-live=true pattern=ball \
  ! video/x-raw,width="${WIDTH}",height="${HEIGHT}",framerate="${FPS}"/1 \
  ! videoconvert \
  ! ${ENCODER} \
  ! h264parse config-interval=1 \
  ! rtph264pay pt=96 \
  ! udpsink host="${HOST}" port="${PORT}" sync=false
