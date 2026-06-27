import json

import pytest

from meiso_glass.protocol import HEADER_WIRE_KEYS, MeisoChannel, MeisoMessage, MeisoMessageType


def test_message_header_matches_bible_fields():
    msg = MeisoMessage.make(
        message_type=MeisoMessageType.FEATURE_REQUEST,
        channel=MeisoChannel.HIGH_RELIABLE,
        session_id="session-001",
        sequence=7,
        payload={"requestId": "req-001"},
        source_timestamp_ns=123,
    )

    wire = msg.to_dict()

    assert tuple(wire["header"].keys()) == HEADER_WIRE_KEYS
    assert wire["header"] == {
        "protocolVersion": 1,
        "sessionId": "session-001",
        "messageType": "feature_request",
        "channel": "high_reliable",
        "sequence": 7,
        "sourceTimestamp": 123,
        "payloadLength": len(json.dumps({"requestId": "req-001"}, separators=(",", ":"), sort_keys=True)),
        "flags": 0,
    }


def test_payload_length_is_computed_and_verified():
    msg = MeisoMessage.make(
        message_type=MeisoMessageType.HUD_UPDATE,
        channel=MeisoChannel.HIGH_RELIABLE,
        session_id="session-001",
        sequence=1,
        payload={"items": ["a", "b"]},
    )
    decoded = MeisoMessage.from_bytes(msg.to_bytes())
    assert decoded.payload == {"items": ["a", "b"]}

    wire = msg.to_dict()
    wire["header"]["payloadLength"] += 1
    with pytest.raises(ValueError, match="payload length"):
        MeisoMessage.from_bytes(json.dumps(wire).encode("utf-8"))


def test_old_header_shape_is_rejected():
    old_wire = {
        "protocol_magic": "MEISOGLASS",
        "protocol_version": 1,
        "msg_type": "command",
        "src_role": "host",
        "dst_role": "edge",
        "seq": 1,
        "payload": {},
    }

    with pytest.raises(ValueError):
        MeisoMessage.from_bytes(json.dumps(old_wire).encode("utf-8"))


def test_channel_enum_is_exact_bible_set():
    assert {item.value for item in MeisoChannel} == {
        "high_reliable",
        "latest_wins",
        "low_reliable",
        "low_power",
    }
