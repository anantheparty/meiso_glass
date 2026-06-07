#!/usr/bin/env bash
set -euo pipefail

echo "== uname =="
uname -a || true

echo "== os-release =="
cat /etc/os-release || true

echo "== cpuinfo head =="
head -80 /proc/cpuinfo || true

echo "== memory =="
free -h || true

echo "== block devices =="
lsblk || true

echo "== disk =="
df -h || true

echo "== network =="
ip addr || true
ip route || true

echo "== video devices =="
ls -l /dev/video* 2>/dev/null || true
v4l2-ctl --list-devices 2>/dev/null || true

echo "== gstreamer =="
gst-launch-1.0 --version 2>/dev/null || true
gst-inspect-1.0 2>/dev/null | grep -Ei "h264|vpu|v4l2|nv|rtp|udp" | head -120 || true

echo "== optional platform probes =="
cat /etc/nv_tegra_release 2>/dev/null || true
command -v tegrastats >/dev/null 2>&1 && timeout 3 tegrastats --interval 1000 || true
