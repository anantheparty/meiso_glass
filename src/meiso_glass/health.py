from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _run(cmd: list[str], timeout: float = 2.0) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=timeout)
        return out.decode("utf-8", errors="replace").strip()
    except Exception as exc:
        return f"ERROR: {exc}"


def read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def collect_health() -> dict[str, Any]:
    disk = shutil.disk_usage("/")
    return {
        "hostname": platform.node(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "kernel": platform.release(),
        "python": platform.python_version(),
        "os_release": read_text("/etc/os-release"),
        "uptime": read_text("/proc/uptime"),
        "loadavg": read_text("/proc/loadavg"),
        "meminfo_head": "\n".join(read_text("/proc/meminfo").splitlines()[:8]),
        "disk_root": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
        },
        "ip_addr": _run(["ip", "addr"], timeout=2.0),
        "video_devices": _run(["bash", "-lc", "ls -l /dev/video* 2>/dev/null || true"], timeout=2.0),
        "gst_version": _run(["bash", "-lc", "gst-launch-1.0 --version 2>/dev/null | head -3 || true"], timeout=2.0),
        "platform_hints": {
            "nvidia_l4t": read_text("/etc/nv_tegra_release"),
        },
        "env": {"USER": os.environ.get("USER", "")},
    }
