# Wire Protocol Spec

本页定义 Meiso Core Wire V0.1。Core Wire 是低层 framing 规范，只解决 byte record 的边界、版本、低层投递语义和完整性校验。它不是 JSON API，不是同步 RPC，不是业务对象协议，也不是通用可靠传输协议。

设计原则：**Core Wire 的字段必须能直接服务嵌入式接收端的定界、限长、校验、丢弃或队列投递；否则不进入 V0.1。**

## 1. Design Stance

Core Wire MUST 做：

- 提供固定、可流式读取的 frame 边界。
- 在分配或读取 payload 前检查版本、kind、delivery、长度和 profile cap。
- 为 raw datagram、serial、low-power radio 这类链路提供最小完整性校验。
- 为 UDP/raw profile 提供一个最小 sequence 字段，用于 ack、loss、duplicate 和 retry accounting。
- 把已校验 payload 作为 opaque bytes 交给 Runtime Protocol。

Core Wire MUST NOT 做：

- 传输 OpenGL、Unity、Godot 或应用对象。
- 表达 feature、scene、HUD、sensor、asset、permission、AI tool 等业务语义。
- 把 transport ack 当作业务成功。
- 在每帧携带 runtime codec、runtime version、object id、timestamp、policy 或 schema hash。
- 在 QUIC stream / IPC / loopback 等已经提供可靠记录语义的 profile 上重复实现 ack、重传、加密、有序交付。
- 提供通用 fragmentation。大 payload MUST 在 Runtime 层 chunk。

## 2. Layering

```text
Host SDK / Device Runtime
  -> Object Protocol
       object_id, opcode, typed args, request/event
  -> Runtime Encoding
       meiso_object_binary_v1
  -> Core Wire
       normal raw frame or tiny low-power frame when the link profile needs it
  -> Link Profile
       loopback / IPC / QUIC / UDP / BLE / LoRa / serial
  -> Physical or Simulated Transport
```

Core Wire 不是所有 profile 都必须强制使用的 envelope。`loopback`、`IPC`、`QUIC stream` MAY carry Runtime Encoding records directly if their Link Profile already supplies record boundaries, reliability and authentication. `UDP`、`serial`、`BLE`、`LoRa`、raw radio profiles SHOULD use the frame layouts below unless their profile defines a smaller proven framing.

## 3. Frame Families

| Family | Header Size | Use |
|---|---:|---|
| `normal` | 12 bytes | Raw datagram、UDP Wi-Fi、serial、debug bridge、QUIC datagram payload、profile needing explicit frame boundary。 |
| `tiny` | 6 bytes | LoRa/BLE/low-power wake、status、probe、小控制包。 |

`tiny` is a separate layout. It is not a compressed normal frame and has no extension/options area.

All multi-byte integers use network byte order.

## 4. Normal Frame V0.1

```text
normal_header[12] | payload[payload_len]
```

| Offset | Size | Field | Type | Rule |
|---:|---:|---|---|---|
| 0 | 2 | `magic` | uint16 | fixed `0x4D57` (`MW`) |
| 2 | 1 | `version` | uint8 | V0.1 fixed `1` |
| 3 | 1 | `kind_delivery` | uint8 | high nibble = `frame_kind`, low nibble = `delivery_class` |
| 4 | 2 | `payload_len` | uint16 | payload byte count; MUST be `<= link_profile.max_payload` |
| 6 | 2 | `seq` | uint16 | sender-local link sequence; wraps modulo 65536 |
| 8 | 4 | `frame_crc32c` | uint32 | CRC-32C over bytes `0..7` plus payload |

`frame_len = 12 + payload_len`.

Why this is smaller than the previous 20/28-byte design:

- There is no `fixed_header_len`: V0.1 has exactly one normal header layout.
- There is no `total_len`: `12 + payload_len` is sufficient.
- There is no `option_len`: V0.1 has no Core Wire options.
- There is no split header/body CRC: one bounded frame CRC is enough for raw profiles; reliable/authenticated profiles should not use Core Wire for reliability.
- There is no `frame_type` enum for business messages: Object Protocol handles those.

## 5. Normal Frame Kind

`frame_kind = kind_delivery >> 4`.

| Value | Name | Payload Rule |
|---:|---|---|
| `0` | `data` | payload is Runtime Encoding bytes |
| `1` | `ack` | payload is Core ack payload for profiles that use Core minimal reliability |
| `2` | `ping` | payload MAY contain opaque probe bytes |
| `3` | `close` | payload MAY contain compact close reason |
| `4` | `error` | payload MAY contain compact core error |
| `5` | `probe` | payload MAY contain link profile probe data |
| `6..15` | reserved | MUST reject in V0.1 |

Runtime names such as `feature_request`、`scene_commit`、`hud_update`、`sensor_sample`、`asset_chunk` MUST NOT appear in Core Wire. They are Object Protocol interface/opcode messages inside `frame_kind=data` payload.

## 6. Delivery Class

`delivery_class = kind_delivery & 0x0F`.

| Value | Name | Meaning |
|---:|---|---|
| `0` | `reliable_ordered` | link/profile should deliver once and in order within a bounded flow |
| `1` | `unreliable_latest` | no retransmit; receiver/runtime may drop older state |
| `2` | `bulk_resumable` | low priority bulk queue; chunk/hash/resume live in runtime layer |
| `3` | `tiny_control` | high priority control path, usually tiny family or bootstrap |
| `4..15` | reserved | MUST reject in V0.1 |

Delivery class is queue intent. It is not business API type and not business success.

## 7. Core Ack Payload

Core ack exists only for Link Profiles whose `reliability_source=core_minimal_shim`.

`frame_kind=ack` payload:

```text
ack_base   uint16   highest contiguous seq received and Core-validated
ack_bits   uint32   bit 0 acknowledges ack_base - 1; bit 31 acknowledges ack_base - 32
```

Rules:

- Ack payload length MUST be exactly 6 bytes.
- A frame MUST NOT be acked until magic、version、kind、delivery、length、CRC all pass.
- Ack retires transport retry slots only. It never means `feature_request`、`scene_commit` or any business request succeeded.
- QUIC stream, IPC and loopback profiles MUST NOT use Core ack for their native reliability.

## 8. Tiny Frame V0.1

Tiny frame is for low-power wake/status/probe paths.

```text
tiny_header[6] | payload[payload_len]
```

| Offset | Size | Field | Type | Rule |
|---:|---:|---|---|---|
| 0 | 1 | `magic` | uint8 | fixed `0xA7` |
| 1 | 1 | `version_kind` | uint8 | high nibble = version, low nibble = tiny kind |
| 2 | 1 | `seq` | uint8 | sender-local tiny sequence |
| 3 | 1 | `payload_len` | uint8 | payload byte count; profile cap still applies |
| 4 | 2 | `crc16` | uint16 | CRC-16/CCITT over bytes `0..3` plus payload |

Tiny kind:

| Value | Name | Rule |
|---:|---|---|
| `0` | `wake` | wake or keepalive hint |
| `1` | `status` | compact status payload |
| `2` | `ack` | low-power ack for duplex tiny profiles |
| `3` | `probe` | low-power link probe |
| `4` | `data` | compact runtime payload allowed by profile |
| `5` | `error` | compact core error |
| `6..15` | reserved | MUST reject in V0.1 |

Tiny restrictions:

- delivery class is implicit `tiny_control`.
- no Core options.
- no fragmentation.
- no JSON envelope.
- no bulk transfer.
- no high-rate sensor stream.
- no generic scene or asset payload in V0.1.

## 9. Decoder State Machine

Normal stream/serial decoder:

```text
SEEK_MAGIC
  -> READ_FIXED_HEADER
  -> CHECK_VERSION_KIND_DELIVERY_LENGTH
  -> READ_PAYLOAD_WITH_PROFILE_CAP
  -> CHECK_FRAME_CRC
  -> DISPATCH_BY_KIND_AND_DELIVERY
```

Datagram decoder starts at `READ_FIXED_HEADER`; bad magic drops the datagram.

Drop policy:

- Bad `magic` on datagram profile drops the datagram.
- Bad `magic` on stream/serial profile enters bounded resync scan.
- Bad `version`、reserved kind、reserved delivery、oversize payload、CRC failure all reject the frame.
- Rejected frames are not acked.

Embedded decoder constraints:

- decode hot path MUST NOT allocate heap memory.
- receiver MUST validate `payload_len <= link_profile.max_payload` before reading payload.
- payload dispatch SHOULD pass pointer + length view instead of copying payload.
- no JSON parser, compression, crypto, dynamic schema lookup, object dispatch or policy evaluation in Core Wire decode path.
- caller owns rx ring, tx retry slots and payload buffer policy.

## 10. Field Proof

| Field | Producer | Consumer | Without It | Tiny Profile | Golden Test |
|---|---|---|---|---|---|
| normal `magic` | sender codec | stream/datagram receiver | cannot resync or reject noise cheaply | replaced by 1-byte tiny magic | `normal_bad_magic_reject` |
| normal `version` | sender codec | receiver codec | incompatible layouts can be misparsed | high nibble of `version_kind` | `normal_unsupported_version_reject` |
| normal `kind_delivery` | core sender | core dispatcher / queue | ack/ping/error/data require runtime parsing | low nibble kind only | `normal_reserved_kind_reject` |
| normal `payload_len` | sender codec | receiver length parser | stream profiles cannot bound reads | tiny `payload_len` | `payload_len_profile_cap_reject` |
| normal `seq` | sender link state | ack/loss/duplicate detector | UDP/raw reliability has no common key | tiny 8-bit seq | `ack_payload_valid` |
| normal `frame_crc32c` | sender codec | receiver before dispatch | corrupted runtime bytes can reach object decoder on weak links | tiny CRC16 | `bad_frame_crc_reject` |
| tiny `magic` | tiny sender | tiny receiver | cannot reject idle-line noise cheaply | native | `tiny_bad_magic_reject` |
| tiny `version_kind` | tiny sender | tiny receiver | layout and kind cannot be separated in 6 bytes | native | `tiny_unknown_kind_reject` |
| tiny `seq` | tiny sender | tiny duplicate/loss accounting | stop-and-wait and duplicate drop degrade | native | `tiny_seq_wrap_ok` |
| tiny `payload_len` | tiny sender | tiny receiver | low-power receiver cannot bound read | native | `tiny_oversize_reject` |
| tiny `crc16` | tiny sender | tiny receiver | corrupted low-power frames reach runtime | native | `tiny_bad_crc_reject` |

## 11. Compatibility

- Normal fixed header changes require a new `version`.
- Tiny fixed header changes require a new high-nibble version.
- V0.1 has no Core options or TLV. New optional metadata belongs in Runtime Protocol or Link Profile unless it is proven to be a Core decoder requirement.
- Reserved values MUST reject until assigned by a later spec.
- Binary golden vectors are the compatibility source of truth.

## 12. Explicit Non-Goals

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
