from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .protocol import MeisoRole


@dataclass(frozen=True)
class SDKConfig:
    raw: dict[str, Any]

    @property
    def device_id(self) -> str:
        return str(self.raw.get("device", {}).get("id", "unknown-device"))

    @property
    def role(self) -> str:
        return str(self.raw.get("device", {}).get("role", "unknown"))

    @property
    def meiso_role(self) -> MeisoRole:
        return MeisoRole(self.role)

    @property
    def platform(self) -> str:
        return str(self.raw.get("device", {}).get("platform", "generic-linux"))

    @property
    def bind_host(self) -> str:
        return str(self.raw.get("network", {}).get("bind_host", "0.0.0.0"))

    @property
    def heartbeat_port(self) -> int:
        return int(self.raw.get("network", {}).get("heartbeat_port", 42000))

    @property
    def control_port(self) -> int:
        return int(self.raw.get("network", {}).get("control_port", 42001))

    @property
    def peer_host(self) -> str:
        return str(self.raw.get("network", {}).get("peer_host", "127.0.0.1"))

    @property
    def peer_heartbeat_port(self) -> int:
        return int(self.raw.get("network", {}).get("peer_heartbeat_port", 42000))

    @property
    def video_host(self) -> str:
        return str(self.raw.get("video", {}).get("host", self.peer_host))

    @property
    def video_port(self) -> int:
        return int(self.raw.get("video", {}).get("port", 5000))

    @property
    def video_width(self) -> int:
        return int(self.raw.get("video", {}).get("width", 1280))

    @property
    def video_height(self) -> int:
        return int(self.raw.get("video", {}).get("height", 720))

    @property
    def video_fps(self) -> int:
        return int(self.raw.get("video", {}).get("fps", 30))

    @property
    def video_encoder(self) -> str:
        return str(self.raw.get("video", {}).get("encoder", "x264enc"))

    @property
    def video_decoder(self) -> str:
        return str(
            self.raw.get("video", {}).get(
                "decoder",
                "avdec_h264 ! videoconvert ! autovideosink sync=false",
            )
        )

    @property
    def log_dir(self) -> Path:
        return Path(str(self.raw.get("logging", {}).get("dir", "./logs")))

    @property
    def high_reliable_port(self) -> int:
        return int(self.raw.get("channels", {}).get("high_reliable_port", self.control_port))

    @property
    def latest_wins_port(self) -> int:
        return int(self.raw.get("channels", {}).get("latest_wins_port", 42003))

    @property
    def low_reliable_port(self) -> int:
        return int(self.raw.get("channels", {}).get("low_reliable_port", 42004))

    @property
    def low_power_port(self) -> int:
        return int(self.raw.get("channels", {}).get("low_power_port", 42005))


def load_config(path: str | Path) -> SDKConfig:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"config root must be a mapping: {path}")
    cfg = SDKConfig(raw=raw)
    if cfg.role not in {role.value for role in MeisoRole}:
        raise ValueError(f"unsupported Meiso role: {cfg.role}")
    return cfg
