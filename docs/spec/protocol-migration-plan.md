# Protocol Migration Plan

本页记录从旧 `wire-protocol.md` 到分层协议 spec 的迁移计划。它是执行计划，不是第二份 bible。

## Problem

旧版 `wire-protocol.md` 把过多语义塞进 Core Wire：

- fixed header 有 `flags`、`fixed_header_len`、`total_len`、`payload_codec` 间接依赖。
- runtime message names 出现在 Core Wire `frame_type`。
- timestamp、object sequence、priority、connection id、link MTU hint 等字段混入 header/TLV。
- JSON/CBOR/Protobuf/FlatBuffers 被写成每帧 payload codec 候选。
- fragmentation、compression、encryption、ack echo、retransmit flag 同时存在，产生重复状态。

这些字段会让 Edge C decoder、MCU helper 和低功耗 radio profile 被业务层复杂度拖住。

## New Spec Structure

| File | Responsibility |
|---|---|
| [wire-protocol.md](./wire-protocol.md) | normal/tiny frame, length, CRC, sequence, core options |
| [object-protocol.md](./object-protocol.md) | object id, interface id, opcode, lifecycle, async request/event |
| [runtime-protocol.md](./runtime-protocol.md) | canonical runtime encoding, compact IDs, bootstrap |
| [transport-profile.md](./transport-profile.md) | link profile, delivery class, reliability ownership |
| [protocol-test-plan.md](./protocol-test-plan.md) | golden vectors, decoder matrix, cross-language tests |
| [time-model.md](./time-model.md) | timestamp, display time, valid until |
| [security-policy.md](./security-policy.md) | camera/mic/eye policy and user confirmation |
| [capability-profile.md](./capability-profile.md) | device capability and power/render/sensor profile |

## Field Migration

| Old Field | Action |
|---|---|
| `magic=MEIS` | replaced by normal `uint16 0x4D57` and tiny `uint8 0xA7` |
| `fixed_header_len` | deleted; fixed layout selected by `version` |
| `flags` | deleted; each behavior needs option, runtime field or profile rule |
| `frame_type` runtime range | moved to Object Protocol interface/opcode |
| `header_ext_len` | replaced by `option_len uint8` |
| `total_len` | deleted; derived as `20 + option_len + payload_len` |
| `payload_len uint32` | reduced to `uint16`; profile caps actual size |
| `delivery_class` TLV | promoted to fixed normal header |
| `connection_id` | moved to session/link state |
| `flow_id` | not in V0.1 core; add only if multiple reliable flows are proven |
| `packet_seq` / `message_seq` | collapsed to normal `seq uint32` |
| `object_seq` | moved to Object Protocol/runtime payload |
| `source_time_ns` / `valid_until_ns` | moved to Time Model/runtime payload |
| `payload_codec` | moved to Runtime Protocol bootstrap |
| `runtime_version` | moved to Runtime Protocol bootstrap |
| `priority` | moved to scheduler policy |
| `ack_range` TLV | retained as compact option for UDP/raw bidirectional profile |
| `fragment` TLV | removed from V0.1 core; runtime chunks own bulk transfer |
| `link_mtu_hint` | moved to `probe` payload/capability exchange |

## Implementation Phases

1. Freeze docs around the new split.
2. Add binary golden vectors for normal/tiny frames.
3. Implement smallest C decoder for Core Wire without runtime dispatch.
4. Implement Rust/Python decoders against the same vectors.
5. Add Object Protocol IDL and generated tables.
6. Add runtime bootstrap and registry bind path.
7. Add UDP minimal shim only after normal frame decode passes.
8. Add QUIC profile without Meiso duplicate ack/retry.
9. Add capability/profile negotiation.
10. Build Host/Edge feature lease and scene commit on top of Object Protocol.

## Acceptance Criteria

- Core Wire decoder can reject malformed frame without parsing runtime payload.
- Core Wire tests include no JSON payload dependency.
- QUIC profile does not use Meiso `ack_range` for stream reliability.
- No generic Core fragmentation is present in V0.1.
- Object Protocol owns runtime message names.
- Every field in normal/tiny header has a golden test.
- C, Rust and Python agree on public golden vectors.

## Open Questions

- Normal header uses `0x4D57` two-byte magic; stream resync quality must be tested with serial noise fixtures.
- Body CRC policy on authenticated QUIC payloads may later allow a fixed zero/skip convention, but V0.1 keeps layout constant.
- Whether V0.1 needs multiple reliable flows is not proven. Do not add `flow_id` until test cases require it.
- Low-power radio profile limits must be validated on hardware before they become product claims.
- IDL format is not selected yet; candidates include custom XML, small YAML, or a Rust/C schema source that generates docs.
