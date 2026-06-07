from __future__ import annotations

import json
import signal
import time
from typing import Any

from .config import SDKConfig
from .health import collect_health
from .logging_utils import setup_logging
from .messages import Message, MessageType, Role, ack_for
from .transport.udp import UDPTransport
from .video.gstreamer import GStreamerProcess, testsrc_h264_rtp_sender_command


class EndpointAgent:
    def __init__(self, cfg: SDKConfig) -> None:
        self.cfg = cfg
        self.logger = setup_logging(cfg.log_dir, "endpoint_agent")
        self.device_id = cfg.device_id
        self.seq = 0
        self.control = UDPTransport(cfg.bind_host, cfg.control_port)
        self.heartbeat_tx = UDPTransport("0.0.0.0", 0)
        self.video = GStreamerProcess()
        self.running = True

    def stop(self) -> None:
        self.running = False
        self.video.stop()
        self.control.close()
        self.heartbeat_tx.close()

    def send_heartbeat(self) -> None:
        self.seq += 1
        msg = Message(
            msg_type=MessageType.HEARTBEAT,
            src_role=Role.ENDPOINT,
            src_id=self.device_id,
            seq=self.seq,
            dst_role=Role.SDC,
            payload={
                "video_running": self.video.running(),
                "role": "endpoint",
                "platform": self.cfg.platform,
                "control_port": self.cfg.control_port,
            },
        )
        self.heartbeat_tx.send(msg, self.cfg.peer_host, self.cfg.peer_heartbeat_port)

    def handle_command(self, msg: Message, addr: tuple[str, int]) -> None:
        command = str(msg.payload.get("command", msg.msg_type.value))
        self.logger.info("command from %s: %s", addr, json.dumps(msg.payload, ensure_ascii=False))
        ok = True
        extra: dict[str, Any] = {}
        try:
            if command == "ping":
                extra = {"pong": True}
            elif command == "health":
                extra = {"health": collect_health()}
            elif command == "start_video":
                cmd = testsrc_h264_rtp_sender_command(
                    host=str(msg.payload.get("video_host", self.cfg.video_host)),
                    port=int(msg.payload.get("video_port", self.cfg.video_port)),
                    width=int(msg.payload.get("width", self.cfg.video_width)),
                    height=int(msg.payload.get("height", self.cfg.video_height)),
                    fps=int(msg.payload.get("fps", self.cfg.video_fps)),
                    encoder=str(msg.payload.get("encoder", self.cfg.video_encoder)),
                )
                self.logger.info("starting video pipeline: %s", cmd)
                self.video.start(cmd)
                extra = {"video_running": self.video.running(), "pipeline": cmd}
            elif command == "stop_video":
                self.video.stop()
                extra = {"video_running": self.video.running()}
            elif command == "start_lowfi":
                extra = {"lowfi_running": False, "adapter": "not_configured"}
            elif command == "stop_lowfi":
                extra = {"lowfi_running": False, "adapter": "not_configured"}
            elif command == "power_state":
                extra = {"power": {"adapter": "not_configured"}}
            else:
                ok = False
                extra = {"error": f"unknown command {command!r}"}
        except Exception as exc:
            ok = False
            extra = {"error": str(exc)}
        reply = ack_for(msg, src_role=Role.ENDPOINT, src_id=self.device_id, ok=ok, extra=extra)
        self.control.send(reply, addr[0], addr[1])

    def run(self) -> None:
        self.logger.info(
            "endpoint agent starting: id=%s platform=%s peer=%s:%s control=%s",
            self.device_id,
            self.cfg.platform,
            self.cfg.peer_host,
            self.cfg.peer_heartbeat_port,
            self.cfg.control_port,
        )
        last_hb = 0.0
        while self.running:
            now = time.time()
            if now - last_hb >= 1.0:
                self.send_heartbeat()
                last_hb = now
            msg, addr = self.control.recv()
            if msg is not None and addr is not None:
                if msg.msg_type in {
                    MessageType.COMMAND,
                    MessageType.PING,
                    MessageType.HEALTH,
                    MessageType.START_VIDEO,
                    MessageType.STOP_VIDEO,
                    MessageType.START_LOWFI,
                    MessageType.STOP_LOWFI,
                    MessageType.POWER_STATE,
                }:
                    self.handle_command(msg, addr)
                else:
                    self.logger.info("ignored message: %s", msg.to_dict())


class SDCAgent:
    def __init__(self, cfg: SDKConfig) -> None:
        self.cfg = cfg
        self.logger = setup_logging(cfg.log_dir, "sdc_agent")
        self.device_id = cfg.device_id
        self.rx = UDPTransport(cfg.bind_host, cfg.heartbeat_port)
        self.running = True
        self.last_endpoint: dict[str, dict[str, Any]] = {}

    def stop(self) -> None:
        self.running = False
        self.rx.close()

    def run(self) -> None:
        self.logger.info(
            "sdc agent starting: id=%s platform=%s listen=%s:%s",
            self.device_id,
            self.cfg.platform,
            self.cfg.bind_host,
            self.cfg.heartbeat_port,
        )
        while self.running:
            msg, addr = self.rx.recv()
            if msg is None:
                continue
            if msg.msg_type == MessageType.HEARTBEAT:
                self.last_endpoint[msg.src_id] = {"addr": addr, "msg": msg.to_dict(), "time": time.time()}
                self.logger.info(
                    "heartbeat from %s at %s payload=%s",
                    msg.src_id,
                    addr,
                    json.dumps(msg.payload, ensure_ascii=False),
                )
            elif msg.msg_type in (MessageType.ACK, MessageType.ERROR):
                self.logger.info(
                    "reply from %s at %s payload=%s",
                    msg.src_id,
                    addr,
                    json.dumps(msg.payload, ensure_ascii=False),
                )
            else:
                self.logger.info("message from %s at %s: %s", msg.src_id, addr, msg.to_dict())


def install_signal_handlers(agent: Any) -> None:
    def _handler(signum: int, frame: object) -> None:
        agent.stop()

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)
