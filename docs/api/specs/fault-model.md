# Fault Model Spec

Meiso SDK 默认网络和设备都不可靠。V0.1 不承诺 exactly-once transport，只通过 idempotency、sequence、state version 和 lease 实现可恢复行为。

## Fault Table

| Fault | Detection | Required Behavior | Telemetry |
|---|---|---|---|
| latency spike | RTT、heartbeat、channel queue age | high_reliable 保持，latest_wins 丢旧包 | `network_latency` |
| packet loss | missing sequence、timeout | high_reliable retry，latest_wins skip | `packet_loss` |
| reorder | sequence regression | high_reliable reorder/drop，latest_wins compare object version | `reordered_packets` |
| duplicate | repeated idempotency key | 返回原结果，不重复 side effect | `duplicate_messages` |
| disconnect | heartbeat timeout | stop new high-power requests，进入 reconnecting | `disconnect_count` |
| Host disappears | lease/watchdog timeout | release transient lease，保留 System HUD | `host_timeout` |
| Edge restarts | session lost / boot counter changed | Host 重新 sync capability 和 scene snapshot | `edge_restart` |
| asset missing | cache miss | placeholder + asset_request，不阻塞 whole scene | `asset_missing` |
| asset corrupt | hash mismatch | reject asset，request retry or mark failed | `asset_corrupt` |
| stale state | state version mismatch | reject patch with `conflict` | `state_conflict` |
| time drift | sync uncertainty too high | widen valid window or degrade real-time feature | `time_uncertainty` |
| thermal high | thermal telemetry / policy | degrade render/sensor/network or revoke lease | `thermal_throttle` |
| low battery | battery telemetry / policy | shorten lease、disable rich session | `battery_guard` |

## Channel Behavior Under Fault

### high_reliable

- Retry until ack or timeout.
- Consumer must dedupe by idempotency key.
- Side effect happens after validation and policy check.
- Ack does not equal business success.
- If retry window expires, sender reports `timeout`.

### latest_wins

- Old packets can be dropped.
- Receiver keeps newest value per object key.
- Missing old packet must not block new value.
- Stale data past `validUntil` must freeze, hide, or degrade.

### low_reliable

- Used for asset/log/config/replay.
- Transfer must be chunked and resumable.
- Asset hash validates final content.
- Low reliable must not block high reliable.

### low_power

- Used only for wake/status/bootstrap.
- Payload must stay small.
- If low_power fails, system can remain offline without pretending active.

## Idempotency

Required idempotency keys:

| Operation | Key |
|---|---|
| feature request | `requestId` |
| feature release | `leaseId` or `requestId` |
| scene snapshot | `snapshotId` |
| HUD update | `updateId` |
| sensor subscribe | `subscriptionId` |
| AI tool call | `toolCallId` plus optional `idempotencyKey` |
| asset chunk | `assetId + chunkIndex + chunkHash` |
| state patch | `stateId + baseVersion + patchId` |

Duplicate side effects are bugs even if duplicate messages are expected.

## Host Missing

If Host disappears:

- Edge stops accepting new Host-originated high-power actions.
- Transient camera/microphone/eye lease expires or is revoked.
- Latest safe scene snapshot may remain until `validUntil`.
- System HUD must remain available.
- Edge attempts reconnect according to transport policy.

## Asset Missing

If a scene references missing asset:

- Edge renders placeholder for that entity.
- Edge sends `asset_request`.
- Scene snapshot remains valid if other entities are renderable.
- If required safety asset is missing, Edge may reject the scene or show System HUD only.

## Partial Success

If side effect succeeds but ack fails:

- Sender may retry.
- Receiver must recognize idempotency key and return the original result.

If ack succeeds but side effect later fails:

- Receiver must send business response or telemetry error.
- Sender must not infer success from ack alone.

## Open Questions

- Exact retry backoff values need transport implementation data.
- Reconnect session resume rules need persistent session token design.
- Hardware validation should decide thermal and low battery thresholds.
