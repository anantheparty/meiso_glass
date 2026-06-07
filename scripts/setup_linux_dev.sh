#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
  python3 python3-venv python3-pip python3-yaml \
  gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
  v4l-utils iperf3 net-tools

echo "Probe hardware codecs with: gst-inspect-1.0 | grep -Ei 'vpu|h264|v4l2|nv'"
