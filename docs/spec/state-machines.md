# State Machines Spec

本页定义 V0.1 必须遵守的状态机。状态机的目标不是画复杂图，而是明确 owner、side effect、过期和恢复行为。

## Common Rules

- 状态变更必须有明确 owner：Host、Edge、Transport、Policy 或 Adapter。
- 会产生 side effect 的 transition 必须有 idempotency key。
- Unknown 不是安全状态。遇到 unknown 必须 defer、reject 或进入 degraded。
- Durable state 和 in-memory state 必须分开记录。

## Connection

Owner：Transport Manager。

| State | Meaning |
|---|---|
| `disconnected` | 无可用链路 |
| `discovering` | 正在发现 Edge 或 Host |
| `authenticating` | 正在认证 session |
| `syncing` | 交换 capability、time sync 和 cached state |
| `active` | 可以发送普通消息 |
| `degraded` | 有链路但能力不足或延迟过高 |
| `reconnecting` | 连接丢失后尝试恢复 |
| `suspended` | 主动低功耗挂起 |
| `closed` | session 结束，不再恢复 |

关键 transition：

| From | To | Trigger | Required Action |
|---|---|---|---|
| `disconnected` | `discovering` | start | 清空非 durable transport cache |
| `discovering` | `authenticating` | peer found | 建立 transport candidate |
| `authenticating` | `syncing` | auth ok | 创建 `sessionId` 或恢复 session |
| `syncing` | `active` | capability/time sync ok | 发布 connection ready |
| `active` | `degraded` | high latency / loss / thermal | 降低 channel 或 capability |
| `active` | `reconnecting` | heartbeat timeout | 停止新 high-power request |
| `reconnecting` | `active` | session restored | 重发未确认 `reliable_ordered` frame |
| any | `closed` | explicit close | 释放 transient lease |

## Feature Lease

Owner：Edge Policy Manager。

| State | Meaning |
|---|---|
| `idle` | feature 未开启 |
| `requested` | Host 发出请求 |
| `pending_confirmation` | 等待用户或系统确认 |
| `active` | feature 已按 granted params 开启 |
| `degraded` | feature 已开启但参数被降低 |
| `release_pending` | Host 请求释放或 Edge 正在关闭 |
| `released` | 已释放 |
| `rejected` | policy、permission 或 capability 拒绝 |
| `expired` | lease 到期 |
| `revoked` | thermal、battery、privacy 或 safety 撤销 |

规则：

- `requestId` 是幂等 key。同一个 `requestId` 重发必须得到同一个 response。
- Camera、microphone、eye 必须有独立 permission state。
- Lease 到期后 Edge 必须关闭高功耗 adapter，不等待 Host。
- Host disconnect 后 transient lease 必须释放，除非 profile 明确允许 offline continuation。
- `degraded` 必须带 `grantedParams` 和 `reason`。

## Sensor Subscription

Owner：Edge Sensor Manager。

| State | Meaning |
|---|---|
| `unsubscribed` | 无订阅 |
| `requested` | 收到 subscribe |
| `starting` | Adapter 正在启动 |
| `streaming` | 正在发送 sample |
| `paused` | policy 或 transport 暂停 |
| `degraded` | rate、resolution 或 encoding 降级 |
| `draining` | unsubscribe 后清理队列 |
| `stopped` | 订阅结束 |
| `error` | adapter 或 policy 错误 |

规则：

- `subscriptionId` 是订阅主 ID。
- 每个 sample 必须带 `subscriptionId`、`sequence`、`timestamp`。
- `unreliable_latest` sensor 可以丢旧 sample；`reliable_ordered` sensor 不能用于高频流。
- 订阅必须绑定 feature lease 或明确标记为不需要 lease。

## Asset Sync

Owner：Asset Cache。

| State | Meaning |
|---|---|
| `unknown` | Edge 不知道该 asset |
| `announced` | Host 在 scene 中引用该 asset |
| `requested` | Edge 已请求 asset |
| `transferring` | 正在收 chunk |
| `validating` | hash、size、profile 校验中 |
| `ready` | 可被 scene 使用 |
| `missing` | 当前不可用但可重试 |
| `failed` | 校验失败或不支持 |
| `evicted` | 因容量被移除 |

规则：

- Scene message 只引用 `assetId`，不内嵌 asset bytes。
- 缺失 asset 不阻塞整个 scene；Edge 显示 placeholder 并异步请求。
- `assetId` 建议是 content hash，chunk retry 必须可恢复。
- Asset 校验失败必须返回 `asset_missing` 或 `profile_unsupported`。
