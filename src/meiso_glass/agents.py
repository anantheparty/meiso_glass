from __future__ import annotations

import json
import signal
import time
from typing import Any

from .config import SDKConfig
from .features import FeatureRequest
from .health import collect_health
from .logging_utils import setup_logging
from .protocol import MeisoChannel, MeisoMessage, MeisoMessageType
from .runtime.edge import MeisoEdgeRuntime
from .transport.udp import UDPTransport


class EdgeAgent:
    def __init__(self, cfg: SDKConfig) -> None:
        self.cfg = cfg
        self.logger = setup_logging(cfg.log_dir, "edge_agent")
        self.device_id = cfg.device_id
        self.seq = 0
        self.control = UDPTransport(cfg.bind_host, cfg.control_port)
        self.heartbeat_tx = UDPTransport("0.0.0.0", 0)
        self.runtime = MeisoEdgeRuntime()
        self.running = True

    def stop(self) -> None:
        self.running = False
        self.control.close()
        self.heartbeat_tx.close()

    def send_heartbeat(self) -> None:
        self.seq += 1
        msg = MeisoMessage.make(
            message_type=MeisoMessageType.HEARTBEAT,
            channel=MeisoChannel.HIGH_RELIABLE,
            session_id=self.device_id,
            sequence=self.seq,
            payload={
                "role": "edge",
                "platform": self.cfg.platform,
                "control_port": self.cfg.control_port,
                "active_features": sorted(
                    lease.request.feature.value for lease in self.runtime.feature_leases.active.values()
                ),
            },
        )
        self.heartbeat_tx.send(msg, self.cfg.peer_host, self.cfg.peer_heartbeat_port)

    def handle_message(self, msg: MeisoMessage, addr: tuple[str, int]) -> None:
        self.logger.info("command from %s: %s", addr, json.dumps(msg.payload, ensure_ascii=False))
        payload: dict[str, Any]
        message_type = MeisoMessageType.ACK
        try:
            if msg.header.message_type == MeisoMessageType.FEATURE_REQUEST:
                request = FeatureRequest.from_payload(msg.payload)
                response = self.runtime.request_feature(request)
                message_type = MeisoMessageType.FEATURE_RESPONSE
                payload = response.to_payload()
            elif msg.header.message_type == MeisoMessageType.EDGE_STATUS:
                payload = {"health": collect_health()}
            else:
                payload = {"ackMessageType": msg.header.message_type.value, "ok": True}
        except Exception as exc:
            message_type = MeisoMessageType.ERROR
            payload = {"error": str(exc), "ackMessageType": msg.header.message_type.value}
        reply = MeisoMessage.make(
            message_type=message_type,
            channel=MeisoChannel.HIGH_RELIABLE,
            session_id=msg.header.session_id,
            sequence=msg.header.sequence,
            payload=payload,
        )
        self.control.send(reply, addr[0], addr[1])

    def run(self) -> None:
        self.logger.info(
            "edge agent starting: id=%s platform=%s peer=%s:%s control=%s",
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
                self.handle_message(msg, addr)


class HostAgent:
    def __init__(self, cfg: SDKConfig) -> None:
        self.cfg = cfg
        self.logger = setup_logging(cfg.log_dir, "host_agent")
        self.device_id = cfg.device_id
        self.rx = UDPTransport(cfg.bind_host, cfg.heartbeat_port)
        self.running = True
        self.last_edge: dict[str, dict[str, Any]] = {}

    def stop(self) -> None:
        self.running = False
        self.rx.close()

    def run(self) -> None:
        self.logger.info(
            "host agent starting: id=%s platform=%s listen=%s:%s",
            self.device_id,
            self.cfg.platform,
            self.cfg.bind_host,
            self.cfg.heartbeat_port,
        )
        while self.running:
            msg, addr = self.rx.recv()
            if msg is None:
                continue
            if msg.header.message_type == MeisoMessageType.HEARTBEAT:
                edge_id = str(msg.payload.get("edgeId", msg.header.session_id))
                self.last_edge[edge_id] = {"addr": addr, "msg": msg.to_dict(), "time": time.time()}
                self.logger.info(
                    "heartbeat from %s at %s payload=%s",
                    edge_id,
                    addr,
                    json.dumps(msg.payload, ensure_ascii=False),
                )
            elif msg.header.message_type in (MeisoMessageType.ACK, MeisoMessageType.ERROR):
                self.logger.info(
                    "reply from %s at %s payload=%s",
                    msg.header.session_id,
                    addr,
                    json.dumps(msg.payload, ensure_ascii=False),
                )
            else:
                self.logger.info("message from %s at %s: %s", msg.header.session_id, addr, msg.to_dict())


def install_signal_handlers(agent: Any) -> None:
    def _handler(signum: int, frame: object) -> None:
        agent.stop()

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)
