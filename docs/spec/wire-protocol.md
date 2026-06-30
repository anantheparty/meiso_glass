# Wire Protocol Spec

本页定义 Meiso Core Wire V0.1。Core Wire 只在链路需要显式 byte record 时使用。它不是业务对象协议，不是可靠传输协议，也不是所有 profile 都必须套的一层 envelope。

设计原则：**Core Wire 只保留嵌入式接收端立刻需要的字段：边界、版本、队列 hint、长度和可选 link sequence。其他内容进入 Runtime Protocol、Object Protocol 或 Link Profile。**

## 1. Boundary

Core Wire MUST 做：

- 在 raw datagram、serial、BLE、LoRa、debug bridge 等 profile 上提供最小 record 边界。
- 在读取 payload 前检查 version、kind、channel 和 length。
- 给 profile 一个 sender-local `seq`，用于 duplicate/loss/accounting；是否 ack/retry 由 Link Profile 决定。
- 把 payload 作为 opaque bytes 交给 Runtime Protocol。

Core Wire MUST NOT 做：

- 传输 OpenGL、Unity、Godot 或应用对象。
- 表达 feature、scene、HUD、sensor、asset、permission、AI tool 等业务语义。
- 定义通用 ack、retry、fragmentation、compression、encryption 或 codec negotiation。
- 在 QUIC stream、IPC、loopback 等已有 record/reliability/authentication 的 profile 上强制包一层。

## 2. Layering

```text
Host SDK / Device Runtime
  -> Object Protocol          object_id, opcode, args
  -> Runtime Encoding         meiso_object_binary_v1
  -> Core Wire                only when the Link Profile needs explicit records
  -> Link Profile             loopback / IPC / QUIC / UDP / BLE / LoRa / serial
  -> Physical or Simulated Transport
```

## 3. Frame Families

| Family | Header Size | Use |
|---|---:|---|
| `normal` | 8 bytes | UDP、serial、debug bridge、QUIC datagram payload、raw links needing record boundary |
| `tiny` | 4 bytes | LoRa/BLE wake、status、probe、小控制包 |

All multi-byte integers use network byte order.

Core Wire V0.1 has no options/TLV and no Core fragmentation.

## 4. Normal Record

```text
normal_header[8] | payload[payload_len]
```

| Offset | Size | Field | Type | Rule |
|---:|---:|---|---|---|
| 0 | 2 | `magic` | uint16 | fixed `0x4D57` (`MW`) |
| 2 | 1 | `version` | uint8 | V0.1 fixed `1` |
| 3 | 1 | `kind_channel` | uint8 | high nibble = kind, low nibble = channel |
| 4 | 2 | `payload_len` | uint16 | payload byte count; MUST be `<= link_profile.max_payload` |
| 6 | 2 | `seq` | uint16 | sender-local link sequence; wraps modulo 65536 |

`frame_len = 8 + payload_len`.

Why there is no checksum field here:

- UDP, BLE, LoRa, serial and QUIC profiles already have different integrity/authentication mechanisms.
- A universal Core checksum creates duplicate work on authenticated links and still does not provide security.
- Profiles that need an additional CRC or MIC MUST define it in the Link Profile as a trailer or lower-layer guard.

## 5. Normal Kind

`kind = kind_channel >> 4`.

| Value | Name | Payload Rule |
|---:|---|---|
| `0` | `runtime_data` | payload is Runtime Encoding bytes |
| `1` | `profile_control` | payload is Link Profile control bytes, such as UDP ack shim |
| `2` | `probe` | payload is link probe data |
| `3` | `close` | payload is compact close reason |
| `4..15` | reserved | MUST reject in V0.1 |

Runtime names such as `feature_request`、`scene_commit`、`hud_update`、`sensor_sample`、`asset_chunk` MUST NOT appear in Core Wire. They are Object Protocol interface/opcode messages inside `runtime_data`.

## 6. Channel

`channel = kind_channel & 0x0F`.

| Value | Name | Meaning |
|---:|---|---|
| `0` | `control` | feature lease, policy, session, registry and small critical requests |
| `1` | `latest` | replaceable latest-state updates |
| `2` | `bulk` | asset/log/config chunk traffic |
| `3` | `low_power` | wake/status/sparse low-power traffic |
| `4..15` | reserved | MUST reject in V0.1 |

Channel is an admission and queue hint. It does not define business success, ordering or retry by itself.

## 7. Tiny Record

```text
tiny_header[4] | payload[payload_len]
```

| Offset | Size | Field | Type | Rule |
|---:|---:|---|---|---|
| 0 | 1 | `magic` | uint8 | fixed `0xA7` |
| 1 | 1 | `version_kind` | uint8 | high nibble = version, low nibble = tiny kind |
| 2 | 1 | `seq` | uint8 | sender-local tiny sequence |
| 3 | 1 | `payload_len` | uint8 | payload byte count; profile cap applies |

Tiny kind:

| Value | Name | Rule |
|---:|---|---|
| `0` | `wake` | wake or keepalive hint |
| `1` | `status` | compact status payload |
| `2` | `profile_control` | tiny profile control bytes |
| `3` | `probe` | low-power link probe |
| `4` | `data` | compact runtime payload only if profile explicitly allows it |
| `5` | `close` | compact close reason |
| `6..15` | reserved | MUST reject in V0.1 |

Tiny restrictions:

- no options/TLV.
- no fragmentation.
- no JSON envelope.
- no bulk transfer.
- no high-rate sensor stream.
- no generic scene or asset payload in V0.1.
- integrity/authentication is profile-owned, not Core-owned.

## 8. Decoder State Machine

Normal stream/serial decoder:

```text
SEEK_MAGIC
  -> READ_HEADER
  -> CHECK_VERSION_KIND_CHANNEL_LENGTH
  -> READ_PAYLOAD_WITH_PROFILE_CAP
  -> PROFILE_INTEGRITY_CHECK_IF_ANY
  -> DISPATCH_BY_KIND_AND_CHANNEL
```

Datagram decoder starts at `READ_HEADER`; bad magic drops the datagram.

Drop policy:

- Bad `magic` on datagram profile drops the datagram.
- Bad `magic` on stream/serial profile enters bounded resync scan.
- Bad `version`、reserved kind、reserved channel、oversize payload all reject the record.
- Integrity/authentication failure is handled by Link Profile and rejects before runtime dispatch.

Embedded decoder constraints:

- decode hot path MUST NOT allocate heap memory.
- receiver MUST validate `payload_len <= link_profile.max_payload` before reading payload.
- payload dispatch SHOULD pass pointer + length view instead of copying payload.
- no JSON parser, compression, crypto, dynamic schema lookup, object dispatch or policy evaluation in Core Wire decode path.

## 9. Field Proof

| Field | Producer | Consumer | Without It | Tiny Profile | Golden Test |
|---|---|---|---|---|---|
| normal `magic` | sender codec | stream/datagram receiver | cannot resync or reject noise cheaply | 1-byte tiny magic | `normal_bad_magic_reject` |
| normal `version` | sender codec | receiver codec | incompatible layouts can be misparsed | high nibble of `version_kind` | `normal_unsupported_version_reject` |
| normal `kind_channel` | core sender | dispatcher / queue | profile-control and runtime-data require payload parsing before queueing | low nibble kind only | `normal_reserved_kind_reject` |
| normal `payload_len` | sender codec | receiver length parser | stream profiles cannot bound reads | tiny `payload_len` | `payload_len_profile_cap_reject` |
| normal `seq` | sender link state | profile duplicate/loss accounting | UDP/raw profile has no common packet key | tiny 8-bit seq | `seq_wrap_ok` |
| tiny `magic` | tiny sender | tiny receiver | cannot reject idle-line noise cheaply | native | `tiny_bad_magic_reject` |
| tiny `version_kind` | tiny sender | tiny receiver | layout and kind cannot be separated in 4 bytes | native | `tiny_unknown_kind_reject` |
| tiny `seq` | tiny sender | tiny duplicate/loss accounting | sparse duplicate drop degrades | native | `tiny_seq_wrap_ok` |
| tiny `payload_len` | tiny sender | tiny receiver | low-power receiver cannot bound read | native | `tiny_oversize_reject` |

## 10. Compatibility

- Normal fixed header changes require a new `version`.
- Tiny fixed header changes require a new high-nibble version.
- V0.1 has no Core options or TLV. New metadata belongs in Runtime Protocol or Link Profile unless it is proven to be a Core decoder requirement.
- Reserved values MUST reject until assigned by a later spec.
- Binary golden vectors are the compatibility source of truth.

## 11. Explicit Non-Goals

Core Wire does not define:

- Object ID allocation.
- Runtime method names or opcodes.
- Permissions or user confirmation.
- Time synchronization semantics.
- Render profile.
- Asset chunk hash semantics.
- Video stream payload format.
- AI/tool/context/state APIs.

Those are specified by Object Protocol, Runtime Protocol, Transport Profile, Time Model, Security Policy, Render Profile and Capability Profile.
