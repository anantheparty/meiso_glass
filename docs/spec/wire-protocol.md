# Wire 协议规范

本页定义 Meiso Core Wire V0.1。Core Wire 只在链路需要显式 byte record 时使用。它不是业务对象协议，不是可靠传输协议，也不是所有 profile 都必须套的一层 envelope。

设计原则：**Core Wire 只保留嵌入式接收端立刻需要的字段：边界、版本、队列 hint、长度和可选 link sequence。其他内容进入 Runtime Protocol、Object Protocol 或 Link Profile。**

## 1. 边界

Core Wire 必须做：

- 在 raw datagram、serial、BLE、LoRa、debug bridge 等 profile 上提供最小 record 边界。
- 在读取 payload 前检查 version、kind、channel 和 length。
- 给 profile 一个 sender-local `seq`，用于 duplicate/loss/accounting；是否 ack/retry 由 Link Profile 决定。
- 把 payload 作为 opaque bytes 交给 Runtime Protocol。

Core Wire 不得做：

- 传输 OpenGL、Unity、Godot 或应用对象。
- 表达 feature、scene、HUD、sensor、asset、permission、AI tool 等业务语义。
- 定义通用 ack、retry、fragmentation、compression、encryption 或 codec negotiation。
- 在 QUIC stream、IPC、loopback 等已有 record/reliability/authentication 的 profile 上强制包一层。

## 2. 分层

```text
Host SDK / Device Runtime
  -> Object Protocol          object_id, opcode, args
  -> Runtime Encoding         meiso_object_binary_v1
  -> Core Wire                仅当 Link Profile 需要显式 record 时使用
  -> Link Profile             loopback / IPC / QUIC / UDP / BLE / LoRa / serial
  -> Physical or Simulated Transport
```

## 3. Frame Families

| Family | Header Size | Use |
|---|---:|---|
| `normal` | 8 bytes | UDP、serial、debug bridge、QUIC datagram payload、需要 record boundary 的 raw links |
| `tiny` | 4 bytes | LoRa/BLE wake、status、probe、小控制包 |

所有多字节整数使用 network byte order。

Core Wire V0.1 没有 options/TLV，也没有 Core fragmentation。

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

`frame_len = 8 + payload_len`。

没有 checksum 字段的原因：

- UDP、BLE、LoRa、serial 和 QUIC profile 拥有不同的 integrity/authentication 机制。
- 通用 Core checksum 会在 authenticated link 上重复工作，也不能提供安全性。
- 需要额外 CRC 或 MIC 的 profile 必须在 Link Profile 中定义 trailer 或 lower-layer guard。

## 5. Normal Kind

`kind = kind_channel >> 4`。

| Value | Name | Payload Rule |
|---:|---|---|
| `0` | `runtime_data` | payload 是 Runtime Encoding bytes |
| `1` | `profile_control` | payload 是 Link Profile control bytes |
| `2` | `probe` | payload 是 link probe data |
| `3` | `close` | payload 是 compact close reason |
| `4..15` | reserved | V0.1 必须拒绝 |

`feature_request`、`scene_commit`、`hud_update`、`sensor_sample`、`asset_chunk` 等 runtime name 不得出现在 Core Wire 中。它们是 `runtime_data` 里的 Object Protocol interface/opcode message。

## 6. Channel

`channel = kind_channel & 0x0F`。

| Value | Name | Meaning |
|---:|---|---|
| `0` | `control` | feature lease、policy、session、registry 和小型关键请求 |
| `1` | `latest` | 可替换的 latest-state update |
| `2` | `bulk` | asset/log/config chunk traffic |
| `3` | `low_power` | wake/status/sparse low-power traffic |
| `4..15` | reserved | V0.1 必须拒绝 |

Channel 是 admission 和 queue hint。它本身不定义 business success、ordering 或 retry。

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

Tiny kind：

| Value | Name | Rule |
|---:|---|---|
| `0` | `wake` | wake or keepalive hint |
| `1` | `status` | compact status payload |
| `2` | `profile_control` | tiny profile control bytes |
| `3` | `probe` | low-power link probe |
| `4` | `data` | 只有 profile 明确允许时，才承载 compact runtime payload |
| `5` | `close` | compact close reason |
| `6..15` | reserved | V0.1 必须拒绝 |

Tiny 限制：

- 无 options/TLV。
- 无 fragmentation。
- 无 JSON envelope。
- 无 bulk transfer。
- 无 high-rate sensor stream。
- V0.1 中无 generic scene 或 asset payload。
- integrity/authentication 属于 profile，不属于 Core。

## 8. Decoder 状态机

Normal stream/serial decoder：

```text
SEEK_MAGIC
  -> READ_HEADER
  -> CHECK_VERSION_KIND_CHANNEL_LENGTH
  -> READ_PAYLOAD_WITH_PROFILE_CAP
  -> PROFILE_INTEGRITY_CHECK_IF_ANY
  -> DISPATCH_BY_KIND_AND_CHANNEL
```

Datagram decoder 从 `READ_HEADER` 开始；bad magic 直接丢弃 datagram。

Drop policy：

- Datagram profile 上 bad `magic` 直接丢弃 datagram。
- Stream/serial profile 上 bad `magic` 进入 bounded resync scan。
- Bad `version`、reserved kind、reserved channel、oversize payload 都拒绝 record。
- Integrity/authentication failure 由 Link Profile 处理，并且必须在 runtime dispatch 前拒绝。

嵌入式 decoder 约束：

- decode hot path 不得分配 heap memory。
- receiver 必须在读取 payload 前检查 `payload_len <= link_profile.max_payload`。
- payload dispatch 应传递 pointer + length view，而不是复制 payload。
- Core Wire decode path 中不得出现 JSON parser、compression、crypto、dynamic schema lookup、object dispatch 或 policy evaluation。

## 9. 字段证明

| Field | Producer | Consumer | Without It | Tiny Profile | Golden Test |
|---|---|---|---|---|---|
| normal `magic` | sender codec | stream/datagram receiver | 无法便宜地 resync 或拒绝噪声 | 1-byte tiny magic | `normal_bad_magic_reject` |
| normal `version` | sender codec | receiver codec | 不兼容 layout 可能被误解析 | `version_kind` high nibble | `normal_unsupported_version_reject` |
| normal `kind_channel` | core sender | dispatcher / queue | profile-control 和 runtime-data 需要先解析 payload 才能排队 | low nibble kind only | `normal_reserved_kind_reject` |
| normal `payload_len` | sender codec | receiver length parser | stream profile 无法限制读取长度 | tiny `payload_len` | `payload_len_profile_cap_reject` |
| normal `seq` | sender link state | profile duplicate/loss accounting | UDP/raw profile 没有通用 packet key | tiny 8-bit seq | `seq_wrap_ok` |
| tiny `magic` | tiny sender | tiny receiver | 无法便宜地拒绝 idle-line noise | native | `tiny_bad_magic_reject` |
| tiny `version_kind` | tiny sender | tiny receiver | 4 bytes 中无法分离 layout 和 kind | native | `tiny_unknown_kind_reject` |
| tiny `seq` | tiny sender | tiny duplicate/loss accounting | sparse duplicate drop 退化 | native | `tiny_seq_wrap_ok` |
| tiny `payload_len` | tiny sender | tiny receiver | low-power receiver 无法限制读取长度 | native | `tiny_oversize_reject` |

## 10. 兼容性

- Normal fixed header 变化必须提升 `version`。
- Tiny fixed header 变化必须提升 high-nibble version。
- V0.1 没有 Core options 或 TLV。新 metadata 应进入 Runtime Protocol 或 Link Profile，除非它被证明是 Core decoder requirement。
- Reserved values 在后续 spec 分配前必须拒绝。
- Binary golden vector 是 compatibility source of truth。

## 11. 明确非目标

Core Wire 不定义：

- Object ID allocation。
- Runtime method name 或 opcode。
- Permission 或 user confirmation。
- Time synchronization semantics。
- Render profile。
- Asset chunk hash semantics。
- Video stream payload format。
- AI/tool/context/state API。

这些内容由 Object Protocol、Runtime Protocol、Transport Profile、Time Model、Security Policy、Render Profile 和 Capability Profile 定义。
