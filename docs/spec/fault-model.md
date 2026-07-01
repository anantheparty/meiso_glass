# 故障模型规范

Meiso SDK 默认网络和设备都不可靠。V0.1 不承诺 exactly-once transport，只通过 idempotency、sequence、state version 和 lease 实现可恢复行为。

## 1. 故障表

| Fault | Detection | Required Behavior | Telemetry |
|---|---|---|---|
| latency spike | RTT、heartbeat、queue age | control 保持；latest 丢旧包 | `network_latency` |
| packet loss | missing sequence、timeout | control 按 profile retry；latest skip | `packet_loss` |
| reorder | sequence regression | control reorder/drop；latest compare object version | `reordered_packets` |
| duplicate | repeated idempotency key | 返回原结果，不重复 side effect | `duplicate_messages` |
| disconnect | heartbeat timeout | Host enters `lost`; Device enters `standalone` or keeps `limited` until timeout | `disconnect_count` |
| Host disappears | lease/watchdog timeout | release transient lease，保留 System HUD | `host_timeout` |
| Device restarts | session lost / boot counter changed | Host 重新 sync capability 和 scene snapshot | `device_restart` |
| asset missing | cache miss | placeholder + asset request，不阻塞 whole scene | `asset_missing` |
| asset corrupt | hash mismatch | reject asset，request retry or mark failed | `asset_corrupt` |
| stale state | state version mismatch | reject patch with `conflict` | `state_conflict` |
| time drift | sync uncertainty too high | widen valid window or degrade real-time feature | `time_uncertainty` |
| thermal high | thermal telemetry / policy | degrade render/sensor/network or revoke lease | `thermal_throttle` |
| low battery | battery telemetry / policy | shorten lease、disable rich session | `battery_guard` |

## 2. 故障下的 Channel 行为

### control

- 按 profile retry，直到 ack 或 timeout。
- Consumer 必须按 idempotency key 去重。
- Side effect 发生在 validation 和 policy check 之后。
- Transport/profile ack 不等于 business success。
- Retry window 过期后，sender 报告 `timeout`。

### latest

- 旧包可以丢弃。
- Receiver 每个 object key 保留 newest value。
- 缺失旧包不得阻塞新值。
- 超过 `validUntil` 的 stale data 必须 freeze、hide 或 degrade。

### bulk

- 用于 asset/log/config/replay。
- Transfer 必须 chunked and resumable。
- Asset hash 验证最终内容。
- Bulk transfer 不得阻塞 control。

### low_power

- 只用于 wake/status/bootstrap。
- Payload 必须保持小。
- 如果 tiny control 失败，系统可以保持 offline，但不能假装 active。

## 3. Idempotency

必需 idempotency key：

| Operation | Key |
|---|---|
| feature request | `requestId` |
| feature release | `leaseId` or `requestId` |
| scene snapshot | `snapshotId` |
| HUD update | `updateId` |
| sensor subscribe | `subscriptionId` |
| asset chunk | `assetId + chunkIndex + chunkHash` |
| state patch | `stateId + baseVersion + patchId` |

即使 duplicate message 是预期情况，duplicate side effect 仍然是 bug。

## 4. Host Missing

如果 Host 消失：

- Device 停止接受新的 Host-originated high-power action。
- Transient camera/microphone/eye lease 到期或被撤销。
- 最近安全 scene snapshot 可以保留到 `validUntil`。
- System HUD 必须保持可用。
- Device 按 transport policy 尝试重连。

## 5. Asset Missing

如果 scene 引用了缺失 asset：

- Device 为该 entity 渲染 placeholder。
- Device 发送 `asset_request`。
- 如果其它 entities 可渲染，scene snapshot 仍然有效。
- 如果缺失的是 safety asset，Device 可以拒绝 scene 或只显示 System HUD。

## 6. Partial Success

如果 side effect 成功但 ack 失败：

- Sender 可以重试。
- Receiver 必须识别 idempotency key 并返回原结果。

如果 ack 成功但 side effect 后续失败：

- Receiver 必须发送 business response 或 telemetry error。
- Sender 不得从 ack 推断业务成功。

## 7. Open Questions

- 精确 retry backoff 需要 transport implementation 数据。
- Reconnect session resume 规则需要 persistent session token 设计。
- Thermal 和 low battery thresholds 应由硬件验证决定。
