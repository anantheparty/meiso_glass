# Transport Profile Spec

本页定义 Meiso V0.1 的 Link Profile 和 Channel 边界。Core Wire record 只是某些链路需要的显式 record wrapper；可靠性、有序性、完整性、安全和重传属于 Link Profile。

## 1. Core Rule

`Channel` describes queue intent. `LinkProfile` describes which layer supplies reliability, ordering, integrity, authentication and record boundaries.

Rules:

- UDP/raw radio MAY use a Meiso minimal shim: Core Wire `seq`, profile-control payload, bounded retry, pacing and duplicate drop.
- QUIC stream MUST use QUIC reliability, ordering, congestion control and TLS. Meiso MUST NOT duplicate those mechanisms.
- QUIC DATAGRAM MAY carry normal Core Wire records for latest-state data.
- BLE/ATT/L2CAP MUST account for BLE-provided reliability before adding Meiso retries.
- Low-power one-way or sparse-duplex radio MUST default to best-effort tiny control unless hardware validation proves reliable duplex.
- Core Wire V0.1 has no generic fragmentation. Bulk transfer uses runtime chunks.

## 2. Channels

| Channel | Reliability | Ordering | Drop Old | Retransmit | Fragmentation | Render Thread Rule |
|---|---|---|---|---|---|---|
| `control` | profile-dependent reliable path preferred | profile-dependent | no, except expired duplicate | only when profile defines it | no Core fragmentation | render thread never waits on network |
| `latest` | best effort | runtime object version decides freshness | yes | no | forbidden | render reads latest valid snapshot |
| `bulk` | chunk/range/hash at runtime | per asset/log/config object | superseded versions can drop | runtime chunk retry | no Core fragmentation | missing assets use placeholder/degrade path |
| `low_power` | profile dependent | tiny `seq` for duplicate/loss accounting | yes | bounded only on duplex tiny links | forbidden | wake/status/safety only |

Channel does not define business success. Runtime still needs commit results, lease results, asset errors and object errors.

## 3. Link Profiles

| Profile ID | Record Boundary | Max Runtime Payload | Reliability Source | Ordering Source | Integrity/Auth Source | Allowed Channels | Tiny Required |
|---|---|---:|---|---|---|---|---|
| `loopback.dev.v0` | native runtime record | 65535 | in-memory queue | FIFO | process trust | all | no |
| `ipc.local.v0` | OS message/stream record | 65535 | OS stream or local queue | OS FIFO | OS permissions/peer credentials | all | no |
| `udp_wifi.v0` | normal Core Wire | 1192 for 1200-byte datagram cap | profile minimal shim | Core Wire `seq`; runtime object version for latest | UDP checksum plus optional session AEAD/MAC | all | yes |
| `quic_wifi.v0` | QUIC stream record or normal Core Wire in DATAGRAM | 1192 datagram, 16384 stream cap | QUIC streams or best-effort DATAGRAM | QUIC stream order; object version for datagram latest | QUIC TLS 1.3 | all, with latest over datagram | yes |
| `ble.control.v0` | tiny Core Wire by default | negotiated | BLE LL/ATT/L2CAP plus profile policy | BLE/L2CAP order; object version for latest | BLE security plus optional session auth | low_power, small control, small latest | yes |
| `lora_lr2021.v0` | tiny Core Wire | 60 for 64-byte total cap | best effort unless approved duplex profile | tiny `seq` only | radio CRC is not auth; session MIC needed for trusted control | low_power, small latest | yes |
| `serial_debug.v0` | normal or tiny Core Wire | 504 UART, 4088 USB CDC | framed byte stream plus optional profile CRC | stream FIFO after record validation | lab only unless session auth added | all for lab/testing | yes |

Limits above are Meiso caps, not physical truths. Capability profile records hardware-validated limits.

## 4. UDP Minimal Shim

`udp_wifi.v0` MAY define profile-control payloads for:

- ack range.
- retry request or close reason.
- path MTU probe.
- pacing feedback.

It MAY use normal Core Wire with `kind=profile_control` and `channel=control`.

It MUST NOT implement:

- unbounded retransmit.
- generic Core fragmentation.
- global ordered queue for all channels.
- business-level exactly-once semantics.

Ack payload shape is profile-owned. It is not part of Core Wire.

## 5. QUIC Profile

`quic_wifi.v0` rules:

- `control` SHOULD use QUIC stream carrying Runtime Encoding records directly.
- `bulk` SHOULD use QUIC stream plus runtime chunk/hash semantics.
- `latest` SHOULD use QUIC DATAGRAM when available; DATAGRAM MAY wrap normal Core Wire for seq/tooling symmetry with UDP.
- `low_power` MAY use a small QUIC stream, DATAGRAM, or tiny Core Wire according to latency/power policy.
- Core/profile ack MUST NOT be used as the reliability mechanism for QUIC streams.
- Meiso session encryption MUST NOT duplicate QUIC TLS. End-to-end payload encryption MAY be defined later as a separate security layer.

## 6. BLE And Low-Power Profiles

`ble.control.v0`:

- payload size is negotiated and hardware validated.
- tiny Core Wire is required for wake/status paths.
- no high-rate scene/sensor stream by default.
- bulk is limited to small config/log trickle unless a later profile proves throughput and power.

`lora_lr2021.v0`:

- default total frame cap is 64 bytes, so tiny payload cap is 60 bytes.
- tiny control and compact latest telemetry are the default use cases.
- reliable command mode requires bidirectional link budget, latency budget and retry policy validation.
- no bulk transfer.
- no Core fragmentation.
- no normal Core Wire by default.

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
| header bytes | 8 | 4 |
| options bytes | 0 | 0 |
| max payload bytes | profile cap | profile cap |
| max inflight reliable tx | 8 for UDP Wi-Fi profile shim | 1 if duplex tiny profile enables retry |
| max rx reorder slots | 8 for UDP Wi-Fi profile shim | 1 |
| max allocation in decode path | 0 heap allocations | 0 heap allocations |
| generic reassembly sets | 0 | 0 |

Normal `payload_len` is uint16, but profiles SHOULD cap far below 65535 when the link cannot safely carry that size.

## 9. Queue Semantics

| Queue | Admission Rule | Drop Rule |
|---|---|---|
| control | bounded by profile control budget | reject new or close link when full |
| latest | keyed by runtime object/version | replace older pending value |
| bulk | low priority budget | pause, resume, or drop superseded version |
| low_power | highest wake/status priority | drop expired duplicate |

The render thread consumes committed runtime snapshots. It MUST NOT block on Core Wire parsing, profile retry, profile ack or asset transfer.
