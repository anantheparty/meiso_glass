# Wire Protocol Spec

本页定义 Meiso Core Wire V0.1。Core wire 不是 JSON API，也不是同步 RPC。它是 Host 和 Edge runtime 之间的低层二进制 framing、校验、分片和异步 delivery contract。

Runtime payload 可以是 JSON、CBOR、Protobuf、FlatBuffers 或 raw bytes。Core 层只把 payload 当成 opaque bytes。

## Unit Convention

- 表格里的 `Offset` 和 `Size` 默认单位是 byte。
- 本 spec 中 1 byte 固定等于 8 bit，也可称为 1 octet。
- `flags` 里的位编号使用 bit。
- `payload_len`、`total_len`、`header_ext_len` 都是 byte count。
- 带宽可以用 bit/s 或 byte/s 表达，但 frame layout 不用 bit 作为长度单位。

## Layering

```text
Application / Host SDK
  -> Runtime Protocol
      JSON / CBOR / Protobuf / FlatBuffers / raw telemetry
  -> Meiso Core Wire
      binary frame, delivery class, sequence, ack, fragment, CRC
  -> Link
      UDP / Wi-Fi buffer / BLE / low-power radio / lab serial bridge
```

Core wire 的目标是：即使发送端没有完整 OS 或复杂 CPU，只要能把 bytes 写入 Wi-Fi/radio buffer，对端也能按固定头接收、校验、丢弃或交给 runtime。

## Core Frame

每个 core frame：

```text
fixed_header[28] | header_extension[header_ext_len] | payload[payload_len]
```

`payload` 是 runtime bytes。Core 层不解析 JSON field，不知道 `requestId`、`feature`、`entityId` 或 `assetId`。

## Fixed Header

所有多 byte 整数使用 network byte order，也就是 big-endian。固定头长度 V0.1 为 28 bytes，4-byte aligned。

| Offset | Size | Field | Type | Rule |
|---:|---:|---|---|---|
| 0 | 4 | `magic` | bytes | ASCII `MEIS` |
| 4 | 1 | `version` | uint8 | Core wire version，V0.1 为 `1` |
| 5 | 1 | `fixed_header_len` | uint8 | V0.1 固定为 `28` |
| 6 | 2 | `flags` | uint16 | core transport flags |
| 8 | 2 | `frame_type` | uint16 | numeric frame type |
| 10 | 2 | `header_ext_len` | uint16 | byte count，必须 4-byte aligned |
| 12 | 4 | `total_len` | uint32 | fixed header + extension + payload |
| 16 | 4 | `payload_len` | uint32 | payload byte count |
| 20 | 4 | `header_crc32c` | uint32 | fixed header CRC，本字段计算时置 0 |
| 24 | 4 | `body_crc32c` | uint32 | extension + payload CRC |

校验顺序：

1. 读取前 28 bytes。
2. 检查 `magic`、`version`、`fixed_header_len`。
3. 检查 reserved flag 是否为 0。
4. 检查 `total_len == fixed_header_len + header_ext_len + payload_len`。
5. 检查 `header_ext_len` 是否 4-byte aligned。
6. 检查 `header_crc32c`。
7. 按 `total_len` 读取剩余 bytes。
8. 检查 `body_crc32c`。
9. 解析 header extension。
10. 按 delivery class 进入 core transport 队列或交给 runtime。

CRC-32C 只用于传输错误检测，不提供认证、加密或防篡改。安全性必须由 session handshake、AEAD/MAC 或外层安全 transport 提供。

## Flags

| Bit | Name | Meaning |
|---:|---|---|
| 0 | `FLAG_FRAGMENT` | frame 是一个 fragment，必须带 `fragment` TLV |
| 1 | `FLAG_ACK_ECHO` | frame 携带 transport ack 信息 |
| 2 | `FLAG_RETRANSMIT` | frame 是重传 |
| 3 | `FLAG_COMPRESSED` | extension + payload 已压缩 |
| 4 | `FLAG_ENCRYPTED` | extension + payload 已加密 |
| 5-15 | reserved | V0.1 必须为 0 |

未知 reserved bit 必须拒绝，不能忽略。

## Frame Types

`frame_type` 是 core/runtime 边界的数字类型，不是 JSON string。

Core control range：

| Value | Name | Meaning |
|---:|---|---|
| `0x0001` | `transport_ping` | link RTT / liveness probe |
| `0x0002` | `transport_close` | close or drain connection |
| `0x0003` | `transport_error` | core wire parse or transport error |
| `0x0004` | `transport_probe` | link capability / MTU probe |

Runtime payload range：

| Value | Runtime Message |
|---:|---|
| `0x0100` | `runtime_heartbeat` |
| `0x0101` | `runtime_error` |
| `0x0102` | `runtime_time_sync` |
| `0x0110` | `feature_request` |
| `0x0111` | `feature_response` |
| `0x0112` | `feature_release` |
| `0x0120` | `scene_snapshot` |
| `0x0121` | `scene_delta` |
| `0x0130` | `hud_update` |
| `0x0140` | `sensor_subscribe` |
| `0x0141` | `sensor_unsubscribe` |
| `0x0142` | `sensor_sample` |
| `0x0150` | `telemetry_report` |
| `0x0160` | `asset_request` |
| `0x0161` | `asset_chunk` |
| `0x0170` | `host_status` |
| `0x0171` | `edge_status` |

Private range：

| Range | Use |
|---|---|
| `0x8000..0xFFFF` | experimental / private，不能进入 public contract |

Transport ack 不是 `frame_type`，也不是 runtime message。Ack 信息通过 TLV piggyback；必要时可发送空 payload frame 携带 ack TLV。

## Header Extension TLV

`header_extension` 使用 TLV：

```text
tag u8 | len u8 | value[len] | zero padding to 4-byte boundary
```

规则：

- `header_ext_len` 必须 4-byte aligned。
- padding byte 必须为 `0x00`，并计入 `body_crc32c`。
- `tag` 的最高位是 `critical` bit；registry 里的 tag 是不带 critical bit 的 base tag。
- 未知 critical TLV 必须拒绝。
- 未知 non-critical TLV 可以跳过。
- TLV 按 tag 升序排列。
- 重复 TLV 默认拒绝，除非该 tag 明确允许重复。
- Edge / low-power profile 建议 `header_ext_len <= 64` bytes。

### TLV Registry

| Tag | Name | Value | Required For |
|---:|---|---|---|
| `0x01` | `delivery_class` | uint8 | most runtime frames |
| `0x02` | `connection_id` | uint64 | connected transports |
| `0x03` | `flow_id` | uint16 | ordered/reliable flows |
| `0x04` | `packet_seq` | uint32 or uint64 | ack / retry / loss accounting |
| `0x05` | `message_seq` | uint32 or uint64 | `reliable_ordered` delivery |
| `0x06` | `object_seq` | uint32 or uint64 | `unreliable_latest` object version |
| `0x07` | `source_time_ns` | uint64 | timing / telemetry |
| `0x08` | `payload_codec` | uint8 | runtime payload decode |
| `0x09` | `runtime_version` | uint16 | runtime protocol version |
| `0x0A` | `priority` | uint8 | scheduler |
| `0x0B` | `valid_until_ns` | uint64 | stale data cutoff |
| `0x10` | `ack_range` | struct | transport ack |
| `0x11` | `fragment` | struct | core fragmentation |
| `0x12` | `link_mtu_hint` | uint16 | probe / negotiation |

Core TLV 不承载业务对象 ID。`requestId`、`leaseId`、`entityId`、`assetId` 等属于 runtime payload。

## Payload Codec

`payload_codec`：

| Value | Codec | Use |
|---:|---|---|
| `0` | `raw` | binary telemetry、already-framed media side data |
| `1` | `json_utf8` | lab/debug/runtime bootstrap |
| `2` | `cbor` | compact diagnostic / management payload |
| `3` | `protobuf` | schema-based runtime payload |
| `4` | `flatbuffers` | zero-copy oriented runtime payload |

V0.1 可以用 `json_utf8` 做 Host-facing debug payload，但 core wire 不因此变成 JSON protocol。

## Delivery Classes

`delivery_class` 是 core transport 的异步 delivery class，不是业务 API 分类。

| Value | Name | Core Semantics | Typical Runtime Use |
|---:|---|---|---|
| `0` | `reliable_ordered` | ack、retry、按 `flow_id + message_seq` 有序交付 | feature、policy、critical state |
| `1` | `unreliable_latest` | 不重传，按 object version 丢旧数据 | transform、pose、input、telemetry |
| `2` | `bulk_resumable` | chunk/range、可暂停、可恢复，不阻塞 control | asset、log、config、replay |
| `3` | `tiny_control` | 小包、低频、可用于 low-power link bootstrap | wake、status、content ID |

不要再使用 `high_reliable`、`latest_wins`、`low_reliable`、`low_power` 作为 core wire 名称。它们可以作为历史概念映射，但 public spec 使用上表。

## Transport Ack

Ack 是 core transport 机制，不能等同业务成功。

建议 `ack_range` TLV：

```text
ack_base       uint64   highest contiguous packet_seq received
ack_bitmap     uint64   recent packet_seq receive bitmap
ack_delay_us   uint32   receiver-side ack delay
```

规则：

- Ack 可以 piggyback 在任意 outgoing frame。
- 也可以发送 empty payload frame 专门携带 ack。
- `reliable_ordered` sender 保留 unacked frame 到 retry timeout 或 max retry。
- Receiver 必须去重，但业务 side effect 的 exactly-once 仍由 runtime idempotency key 保证。
- Transport ack 只说明 core frame 被接收并通过校验，不说明 `feature_request` 成功。

## Fragmentation

建议 `fragment` TLV：

```text
message_id            uint64
fragment_index        uint16
fragment_count        uint16
original_payload_len  uint32
fragment_crc32c       uint32
```

规则：

- 默认避免 IP fragmentation。
- Sender 应让单个 `total_len <= link_mtu`。
- Core fragmentation 是最后手段，不是 asset transfer 的默认策略。
- 每个 fragment 都是完整 core frame，有独立 fixed header 和 CRC。
- Fragment 是对 runtime payload bytes 分片，不对 JSON object 或业务字段分片。
- `asset_chunk` 应优先在 runtime 层按 chunk 切分，再进入 core。
- `unreliable_latest` 可以丢弃旧 fragment set，不等待重传。
- `tiny_control` 不允许多 fragment。

## MTU Policy

不要定义全局 MTU。Core 使用 per-link `link_mtu`。

建议默认值：

| Link | Default `total_len` Limit |
|---|---:|
| Wi-Fi / UDP | 1200 bytes |
| Lab Ethernet / controlled LAN | 1400 bytes |
| BLE / low-power radio | negotiated，保守目标 64-220 bytes |
| Serial bridge | negotiated by framing profile |

这些是默认值，不是硬件事实。硬件验证后写入 capability profile。

## Runtime Object IDs

Runtime payload 中继续使用 ASCII string ID：

| ID | Scope |
|---|---|
| `sessionId` | runtime session |
| `requestId` | feature request idempotency |
| `leaseId` | feature lease |
| `entityId` | scene entity |
| `snapshotId` | scene snapshot |
| `assetId` | content-addressed asset |
| `subscriptionId` | sensor subscription |
| `traceId` | diagnostics |

这些 ID 不进入 core fixed header。只有 runtime 需要解析它们。

## Error Codes

Core transport error codes：

| Code | Meaning |
|---|---|
| `bad_magic` | `magic` 不是 `MEIS` |
| `unsupported_core_version` | core version 不支持 |
| `bad_header_length` | fixed header 或 extension length 不合法 |
| `bad_total_length` | `total_len` 不匹配 |
| `bad_header_crc` | fixed header CRC 失败 |
| `bad_body_crc` | extension/payload CRC 失败 |
| `unknown_frame_type` | unknown public `frame_type` |
| `unknown_critical_tlv` | unknown critical TLV |
| `reserved_flag_set` | reserved flag bit 非 0 |
| `mtu_exceeded` | frame 超过 link MTU |
| `fragment_timeout` | fragment reassembly 超时 |
| `retry_exhausted` | reliable retry window exhausted |

Runtime error codes 由 runtime spec 定义，例如 `permission_denied`、`capability_unsupported`、`asset_missing`。

## Compatibility

- Fixed header 只通过 `version` 升级。
- Optional 扩展只能放 TLV。
- 未知 critical TLV 必须拒绝。
- 未知 non-critical TLV 可以跳过。
- Reserved flag 必须为 0。
- 兼容性必须由 binary golden vectors 保护。

## Explicit Non-Goals

Core wire 不做：

- JSON object envelope。
- 同步 RPC。
- User-facing API。
- 权限判断。
- 业务状态机。
- Auth token 或 user identity。
- Unity/Godot/OpenGL object 传输。
- 大资产或视频流的业务级分块策略。
