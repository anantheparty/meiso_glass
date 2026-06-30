# Wire Protocol Golden Vectors

This file defines required Core Wire V0.1 compatibility vectors. It is a spec artifact, not an implementation test runner.

All hex bytes are space-insensitive. Multi-byte integers are network byte order.

## 1. Positive Vectors

### `normal_runtime_data_control_ok`

Purpose: minimal normal record carrying runtime bytes on the control channel.

Fields:

| Field | Value |
|---|---|
| magic | `0x4D57` |
| version | `1` |
| kind | `runtime_data` = `0` |
| channel | `control` = `0` |
| payload_len | `5` |
| seq | `1` |
| payload | ASCII `MEISO` |

Hex:

```text
4D 57 01 00 00 05 00 01 4D 45 49 53 4F
```

Expected: accept and dispatch runtime payload bytes `4D 45 49 53 4F`.

### `normal_profile_control_ok`

Purpose: normal record carrying profile-control bytes. Payload semantics are owned by the active Link Profile, not Core Wire.

Fields:

| Field | Value |
|---|---|
| magic | `0x4D57` |
| version | `1` |
| kind | `profile_control` = `1` |
| channel | `control` = `0` |
| payload_len | `6` |
| seq | `101` |
| payload | `00 64 00 00 00 0F` |

Hex:

```text
4D 57 01 10 00 06 00 65 00 64 00 00 00 0F
```

Expected: accept and dispatch payload to active Link Profile control handler. MUST NOT be surfaced as business success.

### `tiny_wake_ok`

Purpose: minimal low-power wake record.

Fields:

| Field | Value |
|---|---|
| magic | `0xA7` |
| version | `1` |
| tiny kind | `wake` = `0` |
| seq | `1` |
| payload_len | `0` |

Hex:

```text
A7 10 01 00
```

Expected: accept as tiny wake record.

### `tiny_status_ok`

Purpose: tiny status record with two payload bytes.

Fields:

| Field | Value |
|---|---|
| magic | `0xA7` |
| version | `1` |
| tiny kind | `status` = `1` |
| seq | `2` |
| payload_len | `2` |
| payload | `01 02` |

Hex:

```text
A7 11 02 02 01 02
```

Expected: accept and dispatch compact status payload `01 02`.

## 2. Negative Vectors

These vectors MUST exist in executable tests before public V0.1 compatibility is claimed.

| Vector | Mutation | Expected |
|---|---|---|
| `normal_bad_magic_reject` | first byte of valid normal record changed | reject/drop |
| `normal_unsupported_version_reject` | version changed from `1` to `2` | reject |
| `normal_reserved_kind_reject` | high nibble of `kind_channel` set to reserved `4` | reject |
| `normal_reserved_channel_reject` | low nibble of `kind_channel` set to reserved `4` | reject |
| `payload_len_profile_cap_reject` | payload_len exceeds active link profile cap | reject before payload allocation |
| `tiny_bad_magic_reject` | tiny magic changed | reject/drop |
| `tiny_unknown_kind_reject` | low nibble kind set to reserved `6` | reject |
| `tiny_oversize_reject` | tiny payload_len exceeds link cap | reject before allocation |
| `profile_integrity_fail_reject` | profile-level CRC/MIC/auth check fails | reject before runtime dispatch |

## 3. Profile Compliance Vectors

| Vector | Profile | Expected |
|---|---|---|
| `quic_stream_no_core_wrapper_required` | `quic_wifi.v0` reliable stream | profile MAY carry runtime records directly without Core Wire |
| `udp_profile_control_allowed` | `udp_wifi.v0` | profile-control payload MAY retire retry slots |
| `lora_no_normal_record_default` | `lora_lr2021.v0` | normal record rejected unless profile explicitly enables it |
| `asset_no_core_fragmentation` | all V0.1 profiles | asset transfer uses runtime chunks; no Core fragmentation |

## 4. Implementation Notes

- Golden vectors must be checked by C/C++ Device decoder and Rust Host codec.
- Test fixtures may expose JSON metadata, but the compatibility artifact is the binary bytes.
- Any change to a positive vector is a wire compatibility break unless the spec version changes.
