# Wire 协议 Golden Vectors

本页定义 Core Wire V0.1 必需的兼容性测试向量。它是 spec artifact，不是测试运行器实现。

所有 hex bytes 忽略空格。多字节整数使用 network byte order。

## 1. Positive Vectors

### `normal_runtime_data_control_ok`

目的：最小 normal record，在 control channel 上承载 runtime bytes。

字段：

| Field | Value |
|---|---|
| magic | `0x4D57` |
| version | `1` |
| kind | `runtime_data` = `0` |
| channel | `control` = `0` |
| payload_len | `5` |
| seq | `1` |
| payload | ASCII `MEISO` |

Hex：

```text
4D 57 01 00 00 05 00 01 4D 45 49 53 4F
```

期望：接受，并将 runtime payload bytes `4D 45 49 53 4F` 分发给 Runtime Protocol。

### `normal_profile_control_ok`

目的：normal record 承载 profile-control bytes。Payload 语义由当前 Link Profile 拥有，不属于 Core Wire。

字段：

| Field | Value |
|---|---|
| magic | `0x4D57` |
| version | `1` |
| kind | `profile_control` = `1` |
| channel | `control` = `0` |
| payload_len | `6` |
| seq | `101` |
| payload | `00 64 00 00 00 0F` |

Hex：

```text
4D 57 01 10 00 06 00 65 00 64 00 00 00 0F
```

期望：接受，并将 payload 分发给当前 Link Profile 的 control handler。不得将它当作业务成功。

### `tiny_wake_ok`

目的：最小 low-power wake record。

字段：

| Field | Value |
|---|---|
| magic | `0xA7` |
| version | `1` |
| tiny kind | `wake` = `0` |
| seq | `1` |
| payload_len | `0` |

Hex：

```text
A7 10 01 00
```

期望：接受为 tiny wake record。

### `tiny_status_ok`

目的：带两个 payload bytes 的 tiny status record。

字段：

| Field | Value |
|---|---|
| magic | `0xA7` |
| version | `1` |
| tiny kind | `status` = `1` |
| seq | `2` |
| payload_len | `2` |
| payload | `01 02` |

Hex：

```text
A7 11 02 02 01 02
```

期望：接受，并分发 compact status payload `01 02`。

## 2. Negative Vectors

公开声明 V0.1 兼容前，以下向量必须存在于可执行测试中。

| Vector | Mutation | Expected |
|---|---|---|
| `normal_bad_magic_reject` | 修改有效 normal record 的第一个 byte | reject/drop |
| `normal_unsupported_version_reject` | version 从 `1` 改为 `2` | reject |
| `normal_reserved_kind_reject` | `kind_channel` high nibble 设置为 reserved `4` | reject |
| `normal_reserved_channel_reject` | `kind_channel` low nibble 设置为 reserved `4` | reject |
| `payload_len_profile_cap_reject` | payload_len 超过 active link profile cap | 分配 payload 前 reject |
| `tiny_bad_magic_reject` | 修改 tiny magic | reject/drop |
| `tiny_unknown_kind_reject` | low nibble kind 设置为 reserved `6` | reject |
| `tiny_oversize_reject` | tiny payload_len 超过 link cap | 分配 payload 前 reject |
| `profile_integrity_fail_reject` | profile-level CRC/MIC/auth 检查失败 | runtime dispatch 前 reject |

## 3. Profile Compliance Vectors

| Vector | Profile | Expected |
|---|---|---|
| `quic_stream_no_core_wrapper_required` | `quic_wifi.v0` reliable stream | profile 可以直接承载 runtime record，不强制 Core Wire |
| `udp_profile_control_allowed` | `udp_wifi.v0` | profile-control payload 可以释放 retry slot |
| `lora_no_normal_record_default` | `lora_lr2021.v0` | 除非 profile 明确启用，否则 normal record 被拒绝 |
| `asset_no_core_fragmentation` | all V0.1 profiles | asset transfer 使用 runtime chunks；无 Core fragmentation |

## 4. Implementation Notes

- Golden vectors 必须由 Device 侧 C/C++ decoder 和 Host 侧 Rust codec 同时检查。
- Test fixture 可以暴露 JSON metadata，但兼容性 artifact 是 binary bytes。
- Positive vector 的任何变化都是 wire compatibility break，除非 spec version 同步变化。
