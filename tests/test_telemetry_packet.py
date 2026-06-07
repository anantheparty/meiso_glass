import pytest

from meiso_glass.telemetry.packet import TelemetryPacket, TelemetryPacketType


def test_telemetry_packet_roundtrip_with_crc():
    packet = TelemetryPacket(
        packet_type=TelemetryPacketType.IMU,
        seq=123,
        timestamp_us=456789,
        source_id=7,
        payload=b"imu-sample",
    )

    decoded = TelemetryPacket.decode(packet.encode())

    assert decoded == packet


def test_telemetry_packet_rejects_crc_mismatch():
    encoded = bytearray(
        TelemetryPacket(
            packet_type=TelemetryPacketType.POWER_STATE,
            seq=1,
            timestamp_us=2,
            source_id=3,
            payload=b"power",
        ).encode()
    )
    encoded[-1] ^= 0x01

    with pytest.raises(ValueError, match="crc"):
        TelemetryPacket.decode(bytes(encoded))
