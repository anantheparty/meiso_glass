from __future__ import annotations

import argparse
import json
import socket
import sys

from .agents import EndpointAgent, SDCAgent, install_signal_handlers
from .config import load_config
from .health import collect_health
from .messages import Message, MessageType, Role
from .transport.udp import UDPTransport


def main_endpoint() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = load_config(args.config)
    agent = EndpointAgent(cfg)
    install_signal_handlers(agent)
    agent.run()
    return 0


def main_sdc() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = load_config(args.config)
    agent = SDCAgent(cfg)
    install_signal_handlers(agent)
    agent.run()
    return 0


def main_probe() -> int:
    print(json.dumps(collect_health(), ensure_ascii=False, indent=2))
    return 0


def main_send() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, default=42001)
    ap.add_argument("--src-id", default=socket.gethostname())
    ap.add_argument("--video-host", default=None)
    ap.add_argument("--video-port", type=int, default=None)
    ap.add_argument("--encoder", default=None)
    ap.add_argument(
        "command",
        choices=["ping", "health", "start_video", "stop_video", "start_lowfi", "stop_lowfi", "power_state"],
    )
    args = ap.parse_args()

    payload: dict[str, object] = {"command": args.command}
    if args.video_host:
        payload["video_host"] = args.video_host
    if args.video_port:
        payload["video_port"] = args.video_port
    if args.encoder:
        payload["encoder"] = args.encoder

    msg_type_by_command = {
        "ping": MessageType.PING,
        "health": MessageType.HEALTH,
        "start_video": MessageType.START_VIDEO,
        "stop_video": MessageType.STOP_VIDEO,
        "start_lowfi": MessageType.START_LOWFI,
        "stop_lowfi": MessageType.STOP_LOWFI,
        "power_state": MessageType.POWER_STATE,
    }
    msg = Message(
        msg_type=msg_type_by_command[args.command],
        src_role=Role.HOST,
        src_id=args.src_id,
        dst_role=Role.ENDPOINT,
        payload=payload,
    )
    tx = UDPTransport("0.0.0.0", 0, timeout_s=2.0)
    tx.send(msg, args.host, args.port)
    reply, addr = tx.recv()
    tx.close()
    if reply:
        print(json.dumps(reply.to_dict(), ensure_ascii=False, indent=2))
        return 0 if reply.msg_type == MessageType.ACK else 2
    print("No reply", file=sys.stderr)
    return 1
