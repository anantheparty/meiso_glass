# Transport Profile Spec

本页定义 Meiso V0.1 的 Link Profile 和 Delivery Class 边界。Core Wire frame 不等于所有链路都要自己实现可靠性；Link Profile 决定责任归属。

## 1. Core Rule

`DeliveryClass` describes what runtime traffic needs. `LinkProfile` describes which layer supplies reliability, ordering, integrity, security and record boundaries.

Rules:

- UDP/raw radio MAY use Meiso minimal shim: normal frame `seq`, ack payload, bounded retry, pacing and duplicate drop.
- QUIC stream MUST use QUIC reliability, ordering, congestion control and TLS. Meiso MUST NOT duplicate those mechanisms.
- QUIC DATAGRAM MAY carry normal frames for latest-state data when datagram record boundary is useful.
- BLE/ATT/L2CAP MUST account for BLE-provided reliability before adding Meiso retries.
- Low-power one-way or sparse-duplex radio MUST default to best-effort tiny control unless hardware validation proves reliable duplex.
- Core Wire V0.1 has no generic fragmentation. Bulk transfer uses runtime chunks.

## 2. Delivery Classes

| Delivery Class | Reliability | Ordering | Drop Old | Runtime Version Needed | Retransmit | Fragmentation | Render Thread Rule |
|---|---|---|---|---|---|---|---|
| `reliable_ordered` | reliable if profile supports it | by transport stream order or core `seq` | no, except expired duplicate | optional | only when `reliability_source=core_minimal_shim` | no Core fragmentation | render thread never waits on network |
| `unreliable_latest` | best effort | runtime object version decides freshness | yes | required | no | forbidden | render reads latest valid snapshot |
| `bulk_resumable` | chunk/range/hash at runtime | per asset/log/config object | superseded versions can drop | required | runtime chunk retry | no Core fragmentation | missing assets use placeholder/degrade path |
| `tiny_control` | profile dependent | tiny `seq` for duplicate/loss accounting | yes | optional | bounded only on duplex tiny links | forbidden | wake/status/safety only |

Delivery class does not define business success. Runtime still needs `commit_result`, `lease_result`, `asset_missing` and object errors.

## 3. Link Profiles

| Profile ID | Record Boundary | Max Normal Payload | Reliability Source | Ordering Source | Security Source | Allowed Delivery Classes | Tiny Required |
|---|---|---:|---|---|---|---|---|
| `loopback.dev.v0` | native runtime record | 65535 | in-memory queue | FIFO | process trust | all | no |
| `ipc.local.v0` | OS message/stream record | 65535 | OS stream or local queue | OS FIFO | OS permissions/peer credentials | all | no |
| `udp_wifi.v0` | normal frame | 1188 | Meiso core minimal shim | normal `seq`; runtime object version for latest | Meiso session AEAD/MAC if needed | all | yes |
| `quic_wifi.v0` | QUIC stream record or normal frame in DATAGRAM | 1188 datagram, 16384 stream app cap | QUIC streams or QUIC DATAGRAM | QUIC stream order; object version for datagram latest | QUIC TLS 1.3 | all, with latest over datagram | yes |
| `ble.control.v0` | tiny frame by default | negotiated if normal is allowed | BLE LL/ATT/L2CAP plus profile policy | BLE/L2CAP order; object version for latest | BLE security plus optional session auth | tiny, small reliable, small latest | yes |
| `lora_lr2021.v0` | tiny frame | not allowed by default | best effort unless approved duplex profile | tiny `seq` only | radio CRC is not auth; session MIC needed for trusted control | tiny, small latest | yes |
| `serial_debug.v0` | normal or tiny frame | 500 UART, 4084 USB CDC | framed byte stream plus CRC | stream FIFO after frame validation | lab only unless session auth added | all for lab/testing | yes |

Payload limits above exclude Core Wire header bytes. They are Meiso caps, not physical truths. Capability profile records hardware-validated limits.

## 4. UDP Minimal Shim

`udp_wifi.v0` may implement:

- tx retry slots for `reliable_ordered`.
- normal `frame_kind=ack` payload.
- duplicate drop by `seq`.
- bounded retry count and retry timeout.
- pacing to avoid queue collapse.
- drop-old queues for `unreliable_latest`.

It MUST NOT implement:

- unbounded retransmit.
- generic Core fragmentation.
- global ordered queue for all delivery classes.
- business-level exactly-once semantics.

Ack payload is defined in [Wire Protocol](./wire-protocol.md). It is a payload, not an option/TLV.

## 5. QUIC Profile

`quic_wifi.v0` rules:

- `reliable_ordered` SHOULD use QUIC stream carrying runtime records directly.
- `bulk_resumable` SHOULD use QUIC stream plus runtime chunk/hash semantics.
- `unreliable_latest` SHOULD use QUIC DATAGRAM when available; DATAGRAM MAY wrap a normal Core Wire frame for seq/checksum symmetry with UDP tooling.
- `tiny_control` MAY use a small QUIC stream, DATAGRAM, or tiny frame according to latency/power policy.
- Core ack MUST NOT be used as the reliability mechanism for QUIC streams.
- Meiso session encryption MUST NOT duplicate QUIC TLS. End-to-end payload encryption MAY be defined later as a separate security layer.

## 6. BLE And Low-Power Profiles

`ble.control.v0`:

- payload size is negotiated and hardware validated.
- tiny frame is required for wake/status paths.
- no high-rate scene/sensor stream by default.
- bulk is limited to small config/log trickle unless a later profile proves throughput and power.

`lora_lr2021.v0`:

- default max tiny payload is 58 bytes when total frame cap is 64 bytes.
- tiny control and compact latest telemetry are the default use cases.
- reliable command mode requires bidirectional link budget, latency budget and retry policy validation.
- no bulk transfer.
- no Core fragmentation.
- no normal frame by default.

## 7. Core Fragmentation Policy

V0.1 has no generic Core Wire fragmentation.

Reasons:

- It adds reassembly buffers to Device and MCU receivers.
- It creates timeout and partial-state failure modes before runtime can apply object semantics.
- Asset/log/config already need runtime hash, range and resume semantics.
- Latest-state payloads should be reduced or dropped, not fragmented.

If a later profile adds Core fragmentation, it must define profile caps, buffer ownership, timeout, reassembly hash, fragment loss behavior and golden vectors before use.

## 8. Embedded Limits

Minimum embedded receiver profile:

| Limit | Normal | Tiny |
|---|---:|---:|
| header bytes | 12 | 6 |
| options bytes | 0 | 0 |
| max payload bytes | profile cap | profile cap minus 6 if total cap is used |
| max inflight reliable tx | 8 for UDP Wi-Fi | 1 stop-and-wait |
| max rx reorder slots | 8 for UDP Wi-Fi reliable | 1 |
| max frame allocation in decode path | 0 heap allocations | 0 heap allocations |
| generic reassembly sets | 0 | 0 |

Normal `payload_len` is uint16, but profiles SHOULD cap far below 65535 when the link cannot safely carry that size.

## 9. Queue Semantics

| Queue | Admission Rule | Drop Rule |
|---|---|---|
| reliable control | bounded by retry slots | reject new or close link when full |
| latest state | keyed by runtime object/version | replace older pending value |
| bulk | low priority budget | pause, resume, or drop superseded version |
| tiny | highest wake/status priority | drop expired duplicate |

The render thread consumes committed runtime snapshots. It MUST NOT block on Core Wire retry, ack, parsing or asset transfer.
