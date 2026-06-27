# Wire Protocol Spec

本页定义 Meiso Protocol V0.1 的 wire contract。V0.1 可以用 JSON 编码，但字段、通道语义、错误码和兼容规则必须稳定。

## Envelope

每个 wire message 必须是一个 object：

```json
{
  "magic": "MEISO",
  "header": {},
  "payload": {}
}
```

`magic` 固定为 `MEISO`。`payload` 必须是 object，不能是 array、string 或二进制裸值。

## Header

| Field | Type | Required | Rule |
|---|---:|---:|---|
| `protocolVersion` | uint16 | yes | V0.1 固定为 `1` |
| `sessionId` | string | yes | Host/Edge 逻辑会话 ID |
| `messageType` | string | yes | 必须是已知 message type |
| `channel` | string | yes | 必须是已知 logical channel |
| `sequence` | uint64 | yes | 当前 `sessionId + channel` 内递增 |
| `sourceTimestamp` | int64 | yes | 发送端 monotonic nanoseconds |
| `payloadLength` | uint32 | yes | canonical JSON payload byte length |
| `flags` | uint32 | yes | V0.1 必须为 `0` |

Header 不包含 `src_role`、`dst_role`、`direction`。角色由 session 建立和认证阶段确定，不放进每条消息里。

## Message Types

V0.1 message types：

- `heartbeat`
- `ack`
- `error`
- `time_sync`
- `feature_request`
- `feature_response`
- `feature_release`
- `scene_snapshot`
- `scene_delta`
- `hud_update`
- `sensor_subscribe`
- `sensor_unsubscribe`
- `sensor_sample`
- `telemetry_report`
- `ai_context_update`
- `ai_state_patch`
- `ai_tool_call`
- `ai_tool_result`
- `asset_request`
- `asset_chunk`
- `host_status`
- `edge_status`

未知 `messageType` 必须返回 `error.unknown_message_type`，不能静默忽略。

## Object IDs

所有 public object ID 使用 ASCII string。ID 不携带中文，不依赖本机路径，不依赖数据库自增 ID。

| ID | Scope | Rule |
|---|---|---|
| `sessionId` | connection | Host 创建或协商，断连恢复时可复用 |
| `requestId` | feature request | 幂等 key，同一个 request 重发必须得到同一个结果 |
| `leaseId` | feature lease | Edge 创建，用于释放或续租 |
| `entityId` | scene | Host 权威 ID，同一 snapshot 内唯一 |
| `snapshotId` | scene | 完整 scene snapshot ID |
| `assetId` | asset | 建议使用 `asset:<algo>:<digest>` |
| `subscriptionId` | sensor | Host 创建，用于 unsubscribe 和 sample 关联 |
| `toolCallId` | AI tool | 每次 tool call 唯一，可携带 idempotency key |
| `stateId` | AI state | 状态对象 ID |
| `contextId` | AI context | context item ID |
| `traceId` | diagnostics | 跨消息追踪 ID，可选 |

如果一个 message 会产生 side effect，payload 必须包含稳定 idempotency key，例如 `requestId`、`updateId`、`snapshotId` 或 `toolCallId`。

## Logical Channels

| Channel | Delivery | Ordering | Use |
|---|---|---|---|
| `high_reliable` | retry until ack or timeout | ordered per session | control、permission、feature lease、critical state |
| `latest_wins` | best effort | per object latest only | transform、input、telemetry、local pose hint |
| `low_reliable` | resumable/bounded retry | chunk order by object | asset、log、config、replay |
| `low_power` | small best effort or tiny ack | no bulk ordering | wake、status、content ID、link bootstrap |

`high_reliable` 不得被 asset transfer 阻塞。`latest_wins` 不得因为旧包丢失等待重传。`low_power` 不允许发送 scene stream、asset bytes 或视频帧。

## Ack

`ack` payload：

```json
{
  "ackMessageType": "feature_request",
  "ackSequence": 7,
  "ok": true,
  "requestId": "req-camera-001"
}
```

Ack 只表示消息被接收并通过基础校验，不等于业务动作已经成功。业务结果必须用对应 response message 表达。

## Error

`error` payload：

```json
{
  "code": "permission_denied",
  "message": "camera permission denied",
  "retryable": false,
  "refMessageType": "feature_request",
  "refSequence": 7,
  "details": {}
}
```

## Error Codes

| Code | Retryable | Meaning |
|---|---:|---|
| `invalid_message` | no | message 不是合法 envelope 或 payload 不是 object |
| `unsupported_version` | no | `protocolVersion` 不支持 |
| `unknown_message_type` | no | 未知 `messageType` |
| `unknown_channel` | no | 未知 `channel` |
| `payload_length_mismatch` | no | `payloadLength` 与 canonical payload 不一致 |
| `unauthorized` | no | session 或主体未授权 |
| `permission_denied` | no | 用户或系统权限拒绝 |
| `policy_denied` | no | policy 不允许该动作 |
| `lease_expired` | yes | lease 已过期，需要重新申请 |
| `capability_unsupported` | no | 设备不支持该能力 |
| `profile_unsupported` | no | render/capability profile 不支持 |
| `asset_missing` | yes | asset cache 缺失 |
| `timeout` | yes | 等待 ack、asset、sensor 或 tool 超时 |
| `stale_message` | no | message 早于当前 state version 或 valid window |
| `conflict` | yes | state version 或 lease 状态冲突 |
| `rate_limited` | yes | 触发速率限制 |
| `transport_unavailable` | yes | 当前 transport 不可用 |
| `internal_error` | yes | 未分类内部错误 |

## Compatibility

- `protocolVersion = 1` 内，receiver 必须忽略未知 optional payload fields。
- 必填字段缺失必须返回 `invalid_message`。
- unknown enum value 必须返回明确 error，不能自动降级。
- `flags != 0` 在 V0.1 必须拒绝，避免误解未来语义。
- 兼容性由 fixture test 保护，不由人工阅读保证。
