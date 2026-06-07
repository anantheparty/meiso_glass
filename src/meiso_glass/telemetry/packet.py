from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum

TELEMETRY_MAGIC = 0x4D47
TELEMETRY_VERSION = 1
_HEADER = struct.Struct("!HBBIQHH")
_CRC = struct.Struct("!H")


class TelemetryPacketType(IntEnum):
    IMU = 1
    MOTION = 2
    LOWFI_VISION = 3
    EYE_HINT = 4
    POWER_STATE = 5
    THERMAL_STATE = 6
    WAKE_EVENT = 7
    LINK_STATS = 8


def crc16_ccitt(data: bytes, initial: int = 0xFFFF) -> int:
    crc = initial
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


@dataclass(frozen=True)
class TelemetryPacket:
    packet_type: TelemetryPacketType
    seq: int
    timestamp_us: int
    source_id: int
    payload: bytes
    version: int = TELEMETRY_VERSION
    magic: int = TELEMETRY_MAGIC

    def encode(self) -> bytes:
        header = _HEADER.pack(
            self.magic,
            self.version,
            int(self.packet_type),
            self.seq,
            self.timestamp_us,
            self.source_id,
            len(self.payload),
        )
        body = header + self.payload
        return body + _CRC.pack(crc16_ccitt(body))

    @staticmethod
    def decode(data: bytes) -> "TelemetryPacket":
        min_len = _HEADER.size + _CRC.size
        if len(data) < min_len:
            raise ValueError("telemetry packet too short")
        header = data[: _HEADER.size]
        magic, version, packet_type, seq, timestamp_us, source_id, payload_len = _HEADER.unpack(header)
        expected_len = _HEADER.size + payload_len + _CRC.size
        if len(data) != expected_len:
            raise ValueError("telemetry payload length mismatch")
        if magic != TELEMETRY_MAGIC:
            raise ValueError("invalid telemetry magic")
        if version != TELEMETRY_VERSION:
            raise ValueError("unsupported telemetry version")
        payload = data[_HEADER.size : _HEADER.size + payload_len]
        expected_crc = _CRC.unpack(data[-_CRC.size :])[0]
        actual_crc = crc16_ccitt(data[:-_CRC.size])
        if expected_crc != actual_crc:
            raise ValueError("invalid telemetry crc")
        return TelemetryPacket(
            packet_type=TelemetryPacketType(packet_type),
            seq=seq,
            timestamp_us=timestamp_us,
            source_id=source_id,
            payload=payload,
            version=version,
            magic=magic,
        )
