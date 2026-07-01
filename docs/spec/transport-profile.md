# 传输 Profile 规范

本页定义 Meiso V0.1 的 Link Profile 和 Channel 边界。Core Wire record 只是某些链路需要的显式 record wrapper；可靠性、有序性、完整性、安全和重传属于 Link Profile。

## 1. 核心规则

`Channel` 描述队列意图。`LinkProfile` 描述由哪一层提供可靠性、有序性、完整性、认证和 record boundary。

规则：

- UDP/raw radio 可以使用 Meiso minimal shim：Core Wire `seq`、profile-control payload、bounded retry、pacing 和 duplicate drop。
- QUIC stream 必须使用 QUIC 的可靠性、有序性、拥塞控制和 TLS。Meiso 不得重复实现这些机制。
- QUIC DATAGRAM 可以承载 normal Core Wire record，用于 latest-state data。
- BLE/ATT/L2CAP 在增加 Meiso retry 前，必须先计算 BLE 已提供的可靠性。
- Low-power one-way 或 sparse-duplex radio 默认使用 best-effort tiny control，除非硬件验证证明 reliable duplex 可用。
- Core Wire V0.1 没有 generic fragmentation。Bulk transfer 使用 runtime chunks。

## 2. Channel

| Channel | 可靠性 | 有序性 | 是否丢旧 | 重传 | 分片 | Render Thread 规则 |
|---|---|---|---|---|---|---|
| `control` | 优先使用 profile 提供的可靠路径 | profile-dependent | 不丢，除非是过期重复包 | 仅当 profile 定义时允许 | 无 Core fragmentation | render thread 不等待网络 |
| `latest` | best effort | runtime object version 判断新旧 | 是 | 不重传 | 禁止 | render 读取最新有效快照 |
| `bulk` | runtime 层 chunk/range/hash | 按 asset/log/config object | superseded version 可丢弃 | runtime chunk retry | 无 Core fragmentation | 缺失资产走 placeholder/degrade path |
| `low_power` | profile dependent | tiny `seq` 用于 duplicate/loss accounting | 是 | 仅 duplex tiny link 可 bounded retry | 禁止 | 只用于 wake/status/safety |

Channel 不定义业务成功。Runtime 仍然需要 commit result、lease result、asset error 和 object error。

## 3. Link Profiles

| Profile ID | Record Boundary | Max Runtime Payload | Reliability Source | Ordering Source | Integrity/Auth Source | Allowed Channels | Tiny Required |
|---|---|---:|---|---|---|---|---|
| `loopback.dev.v0` | native runtime record | 65535 | in-memory queue | FIFO | process trust | all | no |
| `ipc.local.v0` | OS message/stream record | 65535 | OS stream or local queue | OS FIFO | OS permissions/peer credentials | all | no |
| `udp_wifi.v0` | normal Core Wire | 1192 for 1200-byte datagram cap | profile minimal shim | Core Wire `seq`; latest 使用 runtime object version | UDP checksum plus optional session AEAD/MAC | all | yes |
| `quic_wifi.v0` | QUIC stream record 或 DATAGRAM 中的 normal Core Wire | 1192 datagram, 16384 stream cap | QUIC streams or best-effort DATAGRAM | QUIC stream order; datagram latest 使用 object version | QUIC TLS 1.3 | all, with latest over datagram | yes |
| `ble.control.v0` | 默认 tiny Core Wire | negotiated | BLE LL/ATT/L2CAP plus profile policy | BLE/L2CAP order; latest 使用 object version | BLE security plus optional session auth | low_power, small control, small latest | yes |
| `lora_lr2021.v0` | tiny Core Wire | 60 for 64-byte total cap | best effort unless approved duplex profile | tiny `seq` only | radio CRC is not auth; trusted control 需要 session MIC | low_power, small latest | yes |
| `serial_debug.v0` | normal or tiny Core Wire | 504 UART, 4088 USB CDC | framed byte stream plus optional profile CRC | stream FIFO after record validation | lab only unless session auth added | all for lab/testing | yes |

上述限制是 Meiso cap，不是物理事实。硬件验证后的真实限制写入 Capability Profile。

## 4. UDP Minimal Shim

`udp_wifi.v0` 可以定义 profile-control payload，用于：

- ack range。
- retry request 或 close reason。
- path MTU probe。
- pacing feedback。

它可以使用 `kind=profile_control`、`channel=control` 的 normal Core Wire record。

它不得实现：

- unbounded retransmit。
- generic Core fragmentation。
- 所有 channel 共用的 global ordered queue。
- business-level exactly-once semantics。

Ack payload shape 由 profile 拥有，不属于 Core Wire。

## 5. QUIC Profile

`quic_wifi.v0` 规则：

- `control` 应使用 QUIC stream 直接承载 Runtime Encoding records。
- `bulk` 应使用 QUIC stream 加 runtime chunk/hash semantics。
- `latest` 应在可用时使用 QUIC DATAGRAM；为了与 UDP tooling 保持 seq 对齐，DATAGRAM 可以包 normal Core Wire。
- `low_power` 可以根据 latency/power policy 使用小 QUIC stream、DATAGRAM 或 tiny Core Wire。
- Core/profile ack 不得作为 QUIC stream 的可靠性机制。
- Meiso session encryption 不得重复 QUIC TLS。端到端 payload encryption 可以作为后续独立安全层定义。

## 6. BLE 与低功耗 Profile

`ble.control.v0`：

- payload size 由协商和硬件验证决定。
- wake/status 路径必须支持 tiny Core Wire。
- 默认不支持 high-rate scene/sensor stream。
- bulk 仅限小 config/log trickle，除非后续 profile 证明 throughput 和 power 可接受。

`lora_lr2021.v0`：

- 默认 total frame cap 是 64 bytes，因此 tiny payload cap 是 60 bytes。
- 默认用途是 tiny control 和 compact latest telemetry。
- reliable command mode 需要验证 bidirectional link budget、latency budget 和 retry policy。
- 不支持 bulk transfer。
- 不支持 Core fragmentation。
- 默认不支持 normal Core Wire。

## 7. Core Fragmentation Policy

V0.1 没有 generic Core Wire fragmentation。

原因：

- 它会给 Device 和 MCU receiver 增加 reassembly buffer。
- 它会在 runtime 能应用 object semantics 前制造 timeout 和 partial-state failure mode。
- Asset/log/config 本来就需要 runtime hash、range 和 resume semantics。
- Latest-state payload 应该被缩小或丢弃，而不是被分片。

如果后续 profile 添加 Core fragmentation，必须先定义 profile cap、buffer ownership、timeout、reassembly hash、fragment loss behavior 和 golden vector。

## 8. 嵌入式限制

最小嵌入式 receiver profile：

| Limit | Normal | Tiny |
|---|---:|---:|
| header bytes | 8 | 4 |
| options bytes | 0 | 0 |
| max payload bytes | profile cap | profile cap |
| max inflight reliable tx | UDP Wi-Fi profile shim 为 8 | duplex tiny profile 启用 retry 时为 1 |
| max rx reorder slots | UDP Wi-Fi profile shim 为 8 | 1 |
| max allocation in decode path | 0 heap allocations | 0 heap allocations |
| generic reassembly sets | 0 | 0 |

Normal `payload_len` 是 uint16，但当链路无法安全承载大 payload 时，profile 应将上限设得远低于 65535。

## 9. 队列语义

| Queue | Admission Rule | Drop Rule |
|---|---|---|
| control | 受 profile control budget 限制 | 满时拒绝新请求或关闭链路 |
| latest | 按 runtime object/version 建 key | 替换更旧的 pending value |
| bulk | 低优先级预算 | pause、resume 或丢弃 superseded version |
| low_power | 最高 wake/status 优先级 | 丢弃过期重复包 |

Render thread 消费已提交的 runtime snapshot，不得等待 Core Wire parsing、profile retry、profile ack 或 asset transfer。
