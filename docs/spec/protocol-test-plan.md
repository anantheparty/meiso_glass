# Protocol Test Plan

本页定义 Meiso Core Wire、Runtime Encoding 和 Object Protocol 的 V0.1 测试矩阵。目标不是证明 demo 能跑，而是防止跨语言实现和嵌入式解码器漂移。

## Test Artifacts

V0.1 需要这些测试资产：

| Artifact | Purpose |
|---|---|
| `golden/core-wire/*.bin` | normal/tiny frame canonical bytes |
| `golden/core-wire/*.json` | golden vector metadata for test harness only |
| `golden/object/*.bin` | canonical object message payload |
| `schemas/meiso-object-v1.*` | Object Protocol IDL/schema source |
| `tests/core-wire/*` | C/Rust/Python cross-check tests |
| `tests/runtime/*` | object message decode/dispatch tests |

Metadata JSON 只描述 fixture，不是 runtime wire format。

## Core Wire Golden Vectors

| Name | Input | Expected |
|---|---|---|
| `normal_data_empty_ok` | valid normal data frame, empty payload | decode and dispatch empty runtime payload |
| `normal_object_payload_ok` | valid normal data frame with object payload | payload view delivered unchanged |
| `normal_ack_only_ok` | `frame_kind=ack`, zero payload, valid `ack_range` | ack accepted; no runtime dispatch |
| `normal_ping_payload_ok` | ping with opaque bytes | core ping handler receives bytes |
| `normal_bad_magic_reject` | bad normal magic | reject, no ack |
| `normal_unsupported_version_reject` | version not 1 | reject, no ack |
| `normal_bad_header_crc_reject` | corrupted header CRC | reject before body dispatch |
| `normal_bad_body_crc_reject` | corrupted payload CRC | reject after body read |
| `normal_option_len_over_cap_reject` | option_len > 32 | reject |
| `normal_unknown_critical_option_reject` | unknown tag with high bit set | reject |
| `normal_unknown_noncritical_option_skip` | unknown tag without high bit | skip and dispatch |
| `normal_duplicate_option_reject` | duplicate `ack_range` | reject |
| `normal_payload_profile_cap_reject` | frame exceeds link profile cap | reject |
| `normal_reserved_kind_reject` | public reserved `frame_kind` | reject |
| `normal_reserved_delivery_reject` | delivery class > 3 | reject |
| `normal_runtime_type_not_in_wire_ok` | object payload contains runtime opcode | Core Wire does not inspect it |

## Tiny Golden Vectors

| Name | Input | Expected |
|---|---|---|
| `tiny_wake_ok` | valid wake frame | tiny control dispatch |
| `tiny_status_ok` | valid status payload | tiny status dispatch |
| `tiny_ack_ok` | valid tiny ack | tx slot update if profile supports it |
| `tiny_bad_magic_reject` | bad magic | drop |
| `tiny_unknown_kind_reject` | reserved kind | reject |
| `tiny_bad_crc_reject` | crc mismatch | drop |
| `tiny_oversize_reject` | payload exceeds profile cap | reject |
| `tiny_no_options_enforced` | bytes shaped as option list | treated as payload only or rejected by tiny profile |

## Decoder State Tests

| Group | Required Cases |
|---|---|
| stream split | header split at every byte, body split at every byte |
| back-to-back | two normal frames in one feed, tiny then normal, normal then tiny if profile allows mixed framing |
| resync | noise before magic, partial magic, bad CRC then valid next frame |
| bounded scan | stream noise > scan cap forces degraded/down state |
| zero allocation | allocator poison around decode/feed |
| payload view | payload pointer/length valid until caller-owned buffer release |

## Object Protocol Tests

| Name | Expected |
|---|---|
| `object_registry_bind_ok` | Host bind creates live object from valid Edge global |
| `object_wrong_direction_reject` | sender role cannot use opcode |
| `object_unknown_id_reject` | no dispatch to handler |
| `object_wrong_interface_reject` | object live but interface mismatch |
| `object_unsupported_version_reject` | version higher than negotiated |
| `object_reserved_flag_reject` | reserved flag set |
| `object_new_id_wrong_range_reject` | Host/Edge allocation range enforced |
| `object_destructor_lifecycle_ok` | live -> destroying -> dead |
| `object_commit_stale_reject` | stale base version produces object error |
| `object_batch_exact_end_ok` | batch parser stops exactly at payload end |

## Transport Profile Tests

| Profile | Required Assertions |
|---|---|
| `udp_wifi.v0` | uses `ack_range` for minimal shim; retry bounded; no Core fragmentation |
| `quic_wifi.v0` | no Meiso ack/retry for QUIC stream reliability; datagram latest uses object version |
| `ble.control.v0` | profile cap enforced; tiny required; no bulk scene stream by default |
| `lora_lr2021.v0` | max 64 default; no bulk; no Core fragmentation |
| `serial_debug.v0` | bounded resync; CRC failure does not dispatch |

## Cross-Language Compatibility

Every public golden vector MUST pass in:

- C Edge decoder.
- Rust Host decoder.
- Python test harness.

The tests MUST compare:

- decoded field values.
- CRC values.
- accepted/rejected result.
- dispatched payload bytes.
- error code for rejected frames.

## Non-Goals For V0.1 Tests

Do not add V0.1 compatibility tests for:

- JSON runtime payload as wire format.
- generic Core fragmentation.
- runtime payload compression.
- OpenGL/Unity/Godot object transport.
- AI native tool/context/state APIs.
