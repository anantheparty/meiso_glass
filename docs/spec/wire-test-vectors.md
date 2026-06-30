# Wire Protocol Golden Vectors

This file defines required Core Wire V0.1 compatibility vectors. It is a spec artifact, not an implementation test runner.

All hex bytes are space-insensitive. Multi-byte integers are network byte order.

## 1. CRC Algorithms

- Normal frame `frame_crc32c` uses CRC-32C / Castagnoli.
- Tiny frame `crc16` uses CRC-16/CCITT-FALSE with initial value `0xFFFF`.

## 2. Positive Vectors

### `normal_data_reliable_ok`

Purpose: minimal normal data frame carrying runtime bytes.

Fields:

| Field | Value |
|---|---|
| magic | `0x4D57` |
| version | `1` |
| frame_kind | `data` = `0` |
| delivery_class | `reliable_ordered` = `0` |
| payload_len | `5` |
| seq | `1` |
| payload | ASCII `MEISO` |
| frame_crc32c | `0xADD0ADF4` |

Hex:

```text
4D 57 01 00 00 05 00 01 AD D0 AD F4 4D 45 49 53 4F
```

Expected: accept and dispatch runtime payload bytes `4D 45 49 53 4F`.

### `normal_ack_ok`

Purpose: ack frame for profiles using Core minimal reliability.

Fields:

| Field | Value |
|---|---|
| magic | `0x4D57` |
| version | `1` |
| frame_kind | `ack` = `1` |
| delivery_class | `reliable_ordered` = `0` |
| payload_len | `6` |
| seq | `101` |
| payload | `ack_base=100`, `ack_bits=0x0000000F` |
| frame_crc32c | `0x4B5A15E5` |

Hex:

```text
4D 57 01 10 00 06 00 65 4B 5A 15 E5 00 64 00 00 00 0F
```

Expected: accept as Core ack. MUST NOT be surfaced as business success.

### `tiny_wake_ok`

Purpose: minimal low-power wake frame.

Fields:

| Field | Value |
|---|---|
| magic | `0xA7` |
| version | `1` |
| tiny kind | `wake` = `0` |
| seq | `1` |
| payload_len | `0` |
| crc16 | `0x4FC9` |

Hex:

```text
A7 10 01 00 4F C9
```

Expected: accept as tiny wake frame.

### `tiny_status_ok`

Purpose: tiny status frame with two payload bytes.

Fields:

| Field | Value |
|---|---|
| magic | `0xA7` |
| version | `1` |
| tiny kind | `status` = `1` |
| seq | `2` |
| payload_len | `2` |
| payload | `01 02` |
| crc16 | `0x1909` |

Hex:

```text
A7 11 02 02 19 09 01 02
```

Expected: accept and dispatch compact status payload `01 02`.

## 3. Negative Vectors

These vectors MUST exist in executable tests before public V0.1 compatibility is claimed.

| Vector | Mutation | Expected |
|---|---|---|
| `normal_bad_magic_reject` | first byte of valid normal frame changed | reject/drop |
| `normal_unsupported_version_reject` | version changed from `1` to `2` | reject |
| `normal_reserved_kind_reject` | high nibble of `kind_delivery` set to reserved `6` | reject |
| `delivery_reserved_reject` | low nibble of `kind_delivery` set to reserved `4` | reject |
| `payload_len_profile_cap_reject` | payload_len exceeds active link profile cap | reject before payload allocation |
| `bad_frame_crc_reject` | frame CRC flipped | reject; do not ack |
| `ack_bad_payload_len_reject` | `frame_kind=ack` with payload_len not equal `6` | reject |
| `tiny_bad_magic_reject` | tiny magic changed | reject/drop |
| `tiny_unknown_kind_reject` | low nibble kind set to reserved `6` | reject |
| `tiny_oversize_reject` | tiny payload_len exceeds link cap | reject before allocation |
| `tiny_bad_crc_reject` | tiny CRC flipped | reject |

## 4. Profile Compliance Vectors

| Vector | Profile | Expected |
|---|---|---|
| `quic_stream_no_core_ack` | `quic_wifi.v0` reliable stream | Core ack payload MUST NOT be used as reliability mechanism |
| `udp_ack_allowed` | `udp_wifi.v0` | Core ack payload MAY retire retry slots |
| `lora_no_normal_frame_default` | `lora_lr2021.v0` | normal frame rejected unless profile explicitly enables it |
| `asset_no_core_fragmentation` | all V0.1 profiles | asset transfer uses runtime chunks; no Core fragmentation |

## 5. Implementation Notes

- Golden vectors must be checked by C/C++ Device decoder and Rust Host codec.
- Test fixtures may expose JSON metadata, but the compatibility artifact is the binary bytes.
- Any change to a positive vector is a wire compatibility break unless the spec version changes.
