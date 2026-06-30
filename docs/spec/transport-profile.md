# Transport Profile Spec

本页定义 Meiso V0.1 的 link profile 和 delivery class 边界。Core Wire 的字段不等于所有链路都要自己实现可靠性；链路 profile 决定责任归属。

## Core Rule

`DeliveryClass` describes what the runtime needs. `LinkProfile` describes which layer provides reliability, ordering, integrity and security.

Rules:

- UDP/raw radio MAY use Meiso minimal shim: `seq`, `ack_range`, bounded retry, pacing and duplicate drop.
- QUIC stream MUST use QUIC reliability, ordering, congestion control and TLS. Meiso MUST NOT duplicate those mechanisms.
- BLE/ATT/L2CAP MUST account for BLE-provided reliability before adding Meiso retries.
- Low-power one-way or sparse-duplex radio MUST default to best-effort tiny control unless hardware validation proves reliable duplex.
- Core Wire V0.1 has no generic fragmentation. Bulk transfer uses runtime chunks.

## Delivery Classes

| Delivery Class | Reliability | Ordering | Drop Old | Runtime Version Needed | Retransmit | Fragmentation | Render Thread Rule |
|---|---|---|---|---|---|---|---|
| `reliable_ordered` | reliable if profile supports it | by link `seq` or transport stream order | no, except expired duplicate | optional | only when `reliability_source=core_minimal_shim` | no Core fragmentation | render thread never waits on network |
| `unreliable_latest` | best effort | runtime object version decides freshness | yes | required | no | forbidden | render reads latest valid snapshot |
| `bulk_resumable` | chunk/range/hash at runtime | per asset/log/config object | superseded versions can drop | required | runtime chunk retry | no Core fragmentation | missing assets use placeholder/degrade path |
| `tiny_control` | profile dependent | tiny `seq` for duplicate/loss accounting | yes | optional | bounded only on duplex tiny links | forbidden | wake/status/safety only |

Delivery class does not define business success. Runtime still needs `commit_result`, `lease_result`, `asset_missing` and object errors.

## Link Profiles

| Profile ID | Max Normal Frame | Reliability Source | Ordering Source | Security Source | Allowed Delivery Classes | Tiny Required |
|---|---:|---|---|---|---|---|
| `loopback.dev.v0` | 65535 | in-memory queue | FIFO | process trust | all | no |
| `ipc.local.v0` | 65535 | OS stream or local queue | OS FIFO | OS permissions/peer credentials | all | no |
| `udp_wifi.v0` | 1200 | Meiso core minimal shim | `seq`; runtime object version for latest | Meiso session AEAD/MAC if needed | all | yes |
| `quic_wifi.v0` | 1200 datagram, 16384 stream app cap | QUIC streams or QUIC DATAGRAM | QUIC stream order; object version for datagram latest | QUIC TLS 1.3 | all, with latest over datagram | yes |
| `ble.control.v0` | negotiated 64..220 | BLE LL/ATT/L2CAP plus profile policy | BLE/L2CAP order; object version for latest | BLE security plus optional session auth | tiny, small reliable, small latest | yes |
| `lora_lr2021.v0` | 64 default, <=220 after RF validation | best effort unless approved duplex profile | tiny `seq` only | radio CRC is not auth; session MIC needed for trusted control | tiny, small latest | yes |
| `serial_debug.v0` | 512 UART, 4096 USB CDC | framed byte stream plus CRC | stream FIFO after frame validation | lab only unless session auth added | all for lab/testing | yes |

`Max Normal Frame` is a Meiso cap, not a physical truth. Capability profile records hardware-validated limits.

## UDP Minimal Shim

`udp_wifi.v0` may implement:

- tx retry slots for `reliable_ordered`.
- `ack_range` option.
- duplicate drop by `seq`.
- bounded retry count and retry timeout.
- pacing to avoid queue collapse.
- drop-old queues for `unreliable_latest`.

It MUST NOT implement:

- unbounded retransmit.
- generic Core fragmentation.
- global ordered queue for all delivery classes.
- business-level exactly-once semantics.

## QUIC Profile

`quic_wifi.v0` rules:

- `reliable_ordered` SHOULD use QUIC stream.
- `bulk_resumable` SHOULD use QUIC stream plus runtime chunk/hash semantics.
- `unreliable_latest` SHOULD use QUIC DATAGRAM when available.
- `tiny_control` MAY use a small QUIC stream or datagram according to latency/power policy.
- Core `ack_range` MUST NOT be used as the reliability mechanism for QUIC streams.
- Meiso session encryption MUST NOT be added only to duplicate QUIC TLS. End-to-end payload encryption MAY be defined later as a separate security layer.

## BLE And Low-Power Profiles

`ble.control.v0`:

- payload size is negotiated and hardware validated.
- tiny frame is required for wake/status paths.
- no high-rate scene/sensor stream by default.
- bulk is limited to small config/log trickle unless a later profile proves throughput and power.

`lora_lr2021.v0`:

- default max frame is 64 bytes.
- tiny control and compact latest telemetry are the default use cases.
- reliable command mode requires bidirectional link budget, latency budget and retry policy validation.
- no bulk transfer.
- no Core fragmentation.

## Core Fragmentation Policy

V0.1 has no generic Core Wire fragmentation.

Reasons:

- It adds reassembly buffers to Edge and MCU receivers.
- It creates timeout and partial-state failure modes before runtime can apply object semantics.
- Asset/log/config already need runtime hash, range and resume semantics.
- Latest-state payloads should be reduced or dropped, not fragmented.

If a later profile adds Core fragmentation, it must define profile caps, buffer ownership, timeout, reassembly hash, fragment loss behavior and golden vectors before use.

## Embedded Limits

Minimum embedded receiver profile:

| Limit | Normal | Tiny |
|---|---:|---:|
| header bytes | 20 | 6 |
| max options bytes | 32 | 0 |
| max option count | 4 | 0 |
| max payload bytes | profile cap minus header/options | profile cap minus 6 |
| max inflight reliable tx | 8 for UDP Wi-Fi | 1 stop-and-wait |
| max rx reorder slots | 8 for UDP Wi-Fi reliable | 1 |
| max frame allocation in decode path | 0 heap allocations | 0 heap allocations |
| generic reassembly sets | 0 | 0 |

Normal `payload_len` is uint16, but profiles SHOULD cap far below 65535 when the link cannot safely carry that size.

## Queue Semantics

| Queue | Admission Rule | Drop Rule |
|---|---|---|
| reliable control | bounded by retry slots | reject new or close link when full |
| latest state | keyed by runtime object/version | replace older pending value |
| bulk | low priority budget | pause, resume, or drop superseded version |
| tiny | highest wake/status priority | drop expired duplicate |

The render thread consumes committed runtime snapshots. It MUST NOT block on Core Wire retry, ack, parsing or asset transfer.
