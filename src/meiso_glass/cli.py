from __future__ import annotations

import argparse
import json
import sys

from .agents import EdgeAgent, HostAgent, install_signal_handlers
from .config import load_config
from .features import FeatureName, FeaturePriority, FeatureRequest
from .health import collect_health
from .protocol import MeisoChannel, MeisoMessage, MeisoMessageType
from .transport.udp import UDPTransport


def main_edge(args: argparse.Namespace | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    parsed = args or ap.parse_args()
    cfg = load_config(parsed.config)
    agent = EdgeAgent(cfg)
    install_signal_handlers(agent)
    agent.run()
    return 0


def main_host(args: argparse.Namespace | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    parsed = args or ap.parse_args()
    cfg = load_config(parsed.config)
    agent = HostAgent(cfg)
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
    ap.add_argument("--session-id", required=True)
    ap.add_argument("--feature", choices=[item.value for item in FeatureName], required=True)
    ap.add_argument("--mode", required=True)
    ap.add_argument("--request-id", required=True)
    ap.add_argument("--lease-ms", type=int, default=0)
    ap.add_argument(
        "--priority",
        choices=[item.value for item in FeaturePriority],
        default=FeaturePriority.NORMAL.value,
    )
    args = ap.parse_args()

    request = FeatureRequest(
        feature=FeatureName(args.feature),
        mode=args.mode,
        priority=FeaturePriority(args.priority),
        lease_time_ms=args.lease_ms,
        request_id=args.request_id,
    )
    msg = MeisoMessage.make(
        message_type=MeisoMessageType.FEATURE_REQUEST,
        channel=MeisoChannel.HIGH_RELIABLE,
        session_id=args.session_id,
        sequence=1,
        payload=request.to_payload(),
    )
    tx = UDPTransport("0.0.0.0", 0, timeout_s=2.0)
    tx.send(msg, args.host, args.port)
    reply, addr = tx.recv()
    tx.close()
    if reply:
        print(json.dumps(reply.to_dict(), ensure_ascii=False, indent=2))
        return 0 if reply.header.message_type != MeisoMessageType.ERROR else 2
    print("No reply", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="meiso")
    sub = parser.add_subparsers(dest="command", required=True)

    edge = sub.add_parser("edge")
    edge.add_argument("--config", required=True)

    host = sub.add_parser("host")
    host.add_argument("--config", required=True)

    sub.add_parser("probe")

    send = sub.add_parser("send")
    send.add_argument("--host", required=True)
    send.add_argument("--port", type=int, default=42001)
    send.add_argument("--session-id", required=True)
    send.add_argument("--feature", choices=[item.value for item in FeatureName], required=True)
    send.add_argument("--mode", required=True)
    send.add_argument("--request-id", required=True)
    send.add_argument("--lease-ms", type=int, default=0)
    send.add_argument(
        "--priority",
        choices=[item.value for item in FeaturePriority],
        default=FeaturePriority.NORMAL.value,
    )

    args = parser.parse_args()
    if args.command == "edge":
        return main_edge(args)
    if args.command == "host":
        return main_host(args)
    if args.command == "probe":
        return main_probe()
    if args.command == "send":
        request = FeatureRequest(
            feature=FeatureName(args.feature),
            mode=args.mode,
            priority=FeaturePriority(args.priority),
            lease_time_ms=args.lease_ms,
            request_id=args.request_id,
        )
        msg = MeisoMessage.make(
            message_type=MeisoMessageType.FEATURE_REQUEST,
            channel=MeisoChannel.HIGH_RELIABLE,
            session_id=args.session_id,
            sequence=1,
            payload=request.to_payload(),
        )
        tx = UDPTransport("0.0.0.0", 0, timeout_s=2.0)
        try:
            tx.send(msg, args.host, args.port)
            reply, _addr = tx.recv()
        finally:
            tx.close()
        if reply:
            print(json.dumps(reply.to_dict(), ensure_ascii=False, indent=2))
            return 0 if reply.header.message_type != MeisoMessageType.ERROR else 2
        print("No reply", file=sys.stderr)
        return 1
    raise AssertionError(args.command)
