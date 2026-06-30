# Wire Protocol Spec

本页定义 Meiso Core Wire V0.1。它不是 JSON API，不是同步 RPC，也不是业务对象协议。Core Wire 只负责让 Host 和 Edge 在不同链路上交换可校验、可丢弃、可投递的 byte frame。

设计原则：如果一个字段不能证明它对嵌入式接收端的解码、长度判断、完整性校验、投递分类或链路恢复有直接价值，它不属于 Core Wire。

## Design Stance

Core Wire MUST 做：

- 提供固定、可流式读取的 frame 边界。
- 在读取 payload 前校验 header 里的长度和版本字段。
- 标明 frame 属于哪种低层投递语义。
- 提供最小 sequence 和 ack 承载点，支持 UDP/raw radio 的轻量可靠性。
- 把已校验 payload 作为 opaque bytes 交给 runtime。

Core Wire MUST NOT 做：

- 传输 JSON object envelope。
- 传输 OpenGL、Unity、Godot 或应用对象。
- 表达权限、feature lease、scene、HUD、sensor、asset 等业务语义。
- 把 transport ack 伪装成业务成功。
- 在每帧携带 runtime codec、runtime version、object id、timestamp 或 policy 信息。
- 在 QUIC stream 上重复实现 QUIC 已经提供的 ack、重传、加密和有序交付。

## Unit Convention

- frame layout 表里的 `Offset` 和 `Size` 默认单位是 byte。
- 1 byte 固定等于 8 bit，也可称为 1 octet。
- bit 只用于 bitmap 或 bit field 说明。
- `payload_len` 和 `option_len` 都是 byte count，不是 bit count。
- 带宽可以写 bit/s 或 byte/s；协议 offset/size 只用 byte。

## Layering

```text
Host SDK / Edge Runtime
  -> Object Protocol
      object_id, interface_id, opcode, typed args
  -> Runtime Encoding
      canonical meiso_object_binary_v1
  -> Core Frame
      normal frame or tiny frame
  -> Link Profile
      UDP / QUIC / BLE / low-power radio / serial / loopback
  -> Physical or Simulated Transport
```

Core Wire 的目标是：即使发送端没有完整 OS，甚至只有一个能把 bytes 写入 Wi-Fi/radio buffer 的 MCU/FPGA helper，对端也能按固定规则接收、校验、丢弃或投递。

## Frame Families

V0.1 定义两种 frame family：

| Family | Header Size | Use |
|---|---:|---|
| `normal` | 20 bytes | Wi-Fi、QUIC DATAGRAM payload、USB/serial debug、loopback、IPC。承载 Object Protocol payload。 |
| `tiny` | 6 bytes | 低功耗 wake/status/probe 小包。不能承载大 scene、asset、high-rate sensor stream。 |

`normal` 和 `tiny` 是不同 binary layout。Tiny 不是 normal frame 的压缩版，也不支持 normal options。

## Normal Frame V0.1

所有多 byte 整数使用 network byte order，也就是 big-endian。

```text
normal_header[20] | options[option_len] | payload[payload_len]
```

| Offset | Size | Field | Type | Rule |
|---:|---:|---|---|---|
| 0 | 2 | `magic` | uint16 | 固定为 `0x4D57`，ASCII hint 为 `MW` |
| 2 | 1 | `version` | uint8 | V0.1 固定为 `1` |
| 3 | 1 | `frame_kind` | uint8 | core frame kind |
| 4 | 1 | `delivery_class` | uint8 | low-level delivery semantics |
| 5 | 1 | `option_len` | uint8 | option byte count，V0.1 profile cap 为 32 |
| 6 | 2 | `payload_len` | uint16 | payload byte count，实际上限由 link profile 决定 |
| 8 | 4 | `seq` | uint32 | sender-local link sequence |
| 12 | 4 | `header_crc32c` | uint32 | CRC-32C over bytes 0..11，本字段计算前置 0 |
| 16 | 4 | `body_crc32c` | uint32 | CRC-32C over options + payload |

`frame_len = 20 + option_len + payload_len`。

为什么 normal header 不是更小：

- `magic + version` 让 stream/serial profile 能 resync，也让未来版本能拒绝旧 frame。
- `frame_kind + delivery_class` 把低层控制包、数据包和队列语义分开，避免 runtime payload 才能决定如何排队。
- `option_len + payload_len` 让接收端无需扫描 payload 就能决定读取多少 byte。
- `seq` 是 UDP/raw radio 上 ack、loss、duplicate、replay accounting 的最小公共字段。
- `header_crc32c` 必须在读取 body 前保护长度字段，否则 stream receiver 会被坏长度拖入错误读取。
- `body_crc32c` 在没有外层 AEAD/FCS 的 profile 上提供 payload 完整性；有强外层认证的 profile 仍保留该字段，值为规范化校验结果，避免 layout 分叉。

## Normal Frame Kind

| Value | Name | Payload Rule |
|---:|---|---|
| `0` | `data` | payload 是 Runtime Encoding bytes |
| `1` | `ack` | payload MUST be empty，MUST carry `ack_range` option |
| `2` | `ping` | payload MAY carry opaque ping bytes |
| `3` | `close` | payload MAY carry core close reason |
| `4` | `error` | payload MAY carry core error detail |
| `5` | `probe` | payload MAY carry link profile probe data |
| `6..127` | reserved public | MUST reject in V0.1 |
| `128..255` | private experiment | MUST NOT enter public compatibility tests |

Runtime message type 不在 `frame_kind` 中。`feature_request`、`scene_commit`、`hud_update`、`sensor_sample`、`asset_chunk` 等都属于 Object Protocol。

## Delivery Class

| Value | Name | Core Meaning |
|---:|---|---|
| `0` | `reliable_ordered` | 对同一 link sender 的 `seq` 做 ack、bounded retry、duplicate drop、ordered delivery。 |
| `1` | `unreliable_latest` | 不重传。Core 只做完整性校验和队列投递，runtime 按 object version 丢旧值。 |
| `2` | `bulk_resumable` | 低优先级 bulk queue。恢复、chunk、hash 校验由 runtime asset/log layer 做。 |
| `3` | `tiny_control` | 小控制包优先级。normal frame 中只用于 bootstrap/probe/debug 兼容路径。 |
| `4..255` | reserved | MUST reject in V0.1。 |

`delivery_class` 是异步队列语义，不是业务 API 分类。Transport ack 只说明 frame 通过 Core Wire 校验，不说明 runtime 已接受业务请求。

## Options

Normal frame options 使用紧凑 option list：

```text
tag u8 | len u8 | value[len]
```

规则：

- `option_len` MUST be `<= 32` in V0.1。
- option count MUST be `<= 4`。
- option 不做 padding；receiver 按 `tag,len` 顺序走完 `option_len`。
- `tag & 0x80` 表示 critical option。
- 未知 critical option MUST reject frame。
- 未知 non-critical option MUST skip and count telemetry。
- duplicate option MUST reject frame，除非该 option 明确允许重复。
- option MUST sort by base tag ascending。base tag 是 `tag & 0x7F`。

V0.1 option registry：

| Base Tag | Name | Value Layout | Used By |
|---:|---|---|---|
| `0x01` | `ack_range` | `ack_base uint32`, `ack_bitmap uint32` | UDP/raw bidirectional reliability |
| `0x02` | `core_error_code` | `code uint16` | `frame_kind=error` fast path |

不进入 Core Wire option 的字段：

| Removed Field | New Home |
|---|---|
| `payload_codec` | [Runtime Protocol](./runtime-protocol.md) session negotiation |
| `runtime_version` | Runtime bootstrap / object registry |
| `object_seq` | Object Protocol payload |
| `source_time_ns` / `valid_until_ns` | [Time Model](./time-model.md) and runtime payload |
| `connection_id` | link/session state |
| `priority` | scheduler metadata, not wire decoder |
| `link_mtu_hint` | `probe` payload or capability exchange |
| `fragment` | runtime chunking; no Core Wire fragmentation in V0.1 |

## Ack Rules

`ack_range` value:

```text
ack_base    uint32
ack_bitmap  uint32
```

Rules:

- `ack_base` is the highest contiguous `seq` received and accepted by Core Wire validation.
- Bit 0 of `ack_bitmap` refers to `ack_base - 1`; bit 31 refers to `ack_base - 32`.
- A frame MUST NOT be acked until `magic`、`version`、length、`header_crc32c`、`body_crc32c` and options all pass.
- `reliable_ordered` retry is bounded by link profile. Exactly-once business side effect is runtime responsibility.
- QUIC stream profile MUST NOT use `ack_range` for QUIC-provided reliability.

## Tiny Frame V0.1

Tiny frame is for low-power wake/status/probe paths.

```text
tiny_header[6] | payload[payload_len]
```

| Offset | Size | Field | Type | Rule |
|---:|---:|---|---|---|
| 0 | 1 | `magic` | uint8 | fixed `0xA7` |
| 1 | 1 | `version_kind` | uint8 | high nibble version, low nibble kind |
| 2 | 1 | `seq` | uint8 | sender-local tiny sequence |
| 3 | 1 | `payload_len` | uint8 | profile capped; hard limit 220 total bytes |
| 4 | 2 | `crc16` | uint16 | CRC-16/CCITT over bytes 0..3 with crc zeroed + payload |

Tiny kind:

| Value | Name | Rule |
|---:|---|---|
| `0` | `wake` | wake or keepalive hint |
| `1` | `status` | compact status payload |
| `2` | `ack` | stop-and-wait or sparse tiny ack |
| `3` | `probe` | low-power link probe |
| `4` | `data` | compact runtime payload allowed by profile |
| `5` | `error` | compact core error |
| `6..15` | reserved | MUST reject in V0.1 |

Tiny frame restrictions:

- delivery class is implicit `tiny_control`。
- no options。
- no fragmentation。
- no runtime JSON envelope。
- no bulk transfer。
- no high-rate sensor stream。
- no scene or asset payload unless a later tiny profile explicitly defines a compact format。

## Decoder State Machine

Normal stream/serial decoder:

```text
SEEK_MAGIC
  -> READ_FIXED_HEADER
  -> VALIDATE_FIXED_HEADER
  -> READ_BODY
  -> VALIDATE_BODY_CRC
  -> PARSE_OPTIONS
  -> DISPATCH
```

Drop policy:

- Bad `magic` on datagram profile drops the datagram.
- Bad `magic` on stream/serial profile enters bounded resync scan.
- Bad `version`、length、CRC、unknown critical option、duplicate option、reserved value all reject the frame.
- Rejected frames are not acked.
- Non-critical unknown options are skipped after CRC passes.

Embedded decoder constraints:

- decode/feed hot path MUST NOT allocate heap memory.
- payload dispatch SHOULD pass `ptr + len` view instead of copying payload.
- no JSON parser, compression, crypto, dynamic schema lookup or runtime object dispatch in Core Wire decode path.
- caller owns static context, rx ring, tx retry slots and payload buffer policy.

## Field Proof

| Field | Producer | Consumer | Without It | Tiny Profile | Golden Test |
|---|---|---|---|---|---|
| normal `magic` | any sender | stream/datagram receiver | cannot resync or quickly reject noise | replaced by 1-byte tiny magic | `normal_bad_magic_reject` |
| normal `version` | sender codec | receiver codec | incompatible layouts may be misparsed | high nibble of `version_kind` | `normal_unsupported_version_reject` |
| normal `frame_kind` | core sender | core dispatcher | ack/ping/error/data require runtime parsing | low nibble kind | `normal_unknown_kind_reject` |
| normal `delivery_class` | scheduler | rx queue / retry policy | every payload must be decoded before queueing | implicit `tiny_control` | `delivery_reserved_reject` |
| normal `option_len` | sender codec | receiver length parser | cannot skip options or locate payload | not supported | `option_len_over_cap_reject` |
| normal `payload_len` | sender codec | receiver length parser | must trust transport datagram only; stream impossible | tiny `payload_len` | `payload_len_profile_cap_reject` |
| normal `seq` | sender link state | ack/loss/duplicate detector | UDP/raw reliability has no common key | tiny 8-bit seq | `ack_range_accepts_valid_seq` |
| normal `header_crc32c` | sender codec | receiver before body read | corrupted length can poison stream parsing | tiny uses whole-frame CRC16 | `bad_header_crc_reject` |
| normal `body_crc32c` | sender codec | receiver before dispatch | corrupted runtime bytes reach object decoder on weak links | tiny uses whole-frame CRC16 | `bad_body_crc_reject` |
| option `ack_range` | receiver with outgoing path | retry sender | UDP/raw sender cannot retire tx slots | optional tiny ack kind | `ack_only_frame_ok` |
| option `core_error_code` | core error sender | peer diagnostics | only opaque error payload remains | tiny error kind | `core_error_code_ok` |
| tiny `magic` | tiny sender | tiny receiver | cannot reject idle-line noise cheaply | native | `tiny_bad_magic_reject` |
| tiny `version_kind` | tiny sender | tiny receiver | layout and kind cannot be separated in 6 bytes | native | `tiny_unknown_kind_reject` |
| tiny `seq` | tiny sender | tiny ack/loss accounting | stop-and-wait and duplicate drop degrade | native | `tiny_seq_wrap_ok` |
| tiny `payload_len` | tiny sender | tiny receiver | low-power receiver cannot bound read | native | `tiny_oversize_reject` |
| tiny `crc16` | tiny sender | tiny receiver | corrupted low-power frames reach runtime | native | `tiny_bad_crc_reject` |

## Compatibility

- `version` changes fixed header layout. V0.1 receiver MUST reject unknown normal version.
- Optional extension uses options only; no variable fixed header length.
- Unknown critical options reject; unknown non-critical options skip.
- Reserved values MUST remain invalid until a new spec assigns them.
- Binary golden vectors are the compatibility source of truth.

## Explicit Non-Goals

Core Wire does not define:

- Object ID allocation.
- Runtime method names or opcodes.
- Permissions or user confirmation.
- Time synchronization semantics.
- Render profile.
- Asset chunk hash semantics.
- Video stream payload format.
- AI/tool/context/state APIs.

Those are specified in Object Protocol, Runtime Protocol, Transport Profile, Time Model, Security Policy, Render Profile and Capability Profile.
