from meiso_glass.messages import Message, MessageType, PROTOCOL_MAGIC, Role, ack_for


def test_message_roundtrip_preserves_header_and_payload():
    msg = Message(
        msg_type=MessageType.COMMAND,
        src_role=Role.HOST,
        dst_role=Role.ENDPOINT,
        src_id="host-1",
        seq=42,
        payload={"command": "ping"},
    )

    decoded = Message.from_bytes(msg.to_bytes())

    assert decoded.protocol_magic == PROTOCOL_MAGIC
    assert decoded.msg_type == MessageType.COMMAND
    assert decoded.src_role == Role.HOST
    assert decoded.dst_role == Role.ENDPOINT
    assert decoded.src_id == "host-1"
    assert decoded.seq == 42
    assert decoded.payload == {"command": "ping"}


def test_ack_for_targets_source_role_and_message_id():
    src = Message(
        msg_type=MessageType.COMMAND,
        src_role=Role.HOST,
        dst_role=Role.ENDPOINT,
        src_id="host-1",
        seq=7,
        payload={"command": "health"},
    )

    ack = ack_for(src, src_role=Role.ENDPOINT, src_id="endpoint-1")

    assert ack.msg_type == MessageType.ACK
    assert ack.dst_role == Role.HOST
    assert ack.seq == 7
    assert ack.payload["ok"] is True
    assert ack.payload["ack_msg_id"] == src.msg_id
    assert ack.payload["ack_msg_type"] == "command"


def test_required_v0_message_types_are_declared():
    required = {
        "heartbeat",
        "ping",
        "ack",
        "error",
        "health",
        "start_video",
        "stop_video",
        "start_lowfi",
        "stop_lowfi",
        "power_state",
        "sensor_event",
        "telemetry_packet",
        "display_session",
        "firmware_status",
        "log_event",
        "crash_report",
    }

    assert required.issubset({item.value for item in MessageType})
