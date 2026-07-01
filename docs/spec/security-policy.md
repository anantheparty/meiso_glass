# 安全策略规范

Security / Policy 的核心原则：Host 可以请求，Device 最终裁决。任何 engine wrapper 或 app API 都不能绕过 Device policy。

## 1. 参与方

| Actor | Responsibility |
|---|---|
| `host_app` | 发起业务请求 |
| `host_daemon` | 维护 session、state、asset 和 transport |
| `device_runtime` | 执行 device、render、sensor 和 display |
| `policy_engine` | 最终决定权限、lease、确认和降级 |
| `user` | 对 camera、microphone、eye 等敏感能力确认 |

## 2. 敏感 Feature

V0.1 敏感 feature：

- `camera`
- `microphone`
- `eye`
- `display`
- `network`

`imu` 默认不是高隐私 feature，但仍然可能暴露运动模式；profile 可以要求权限。

## 3. Feature Request Policy

每个敏感 request 必须包含：

```json
{
  "requestId": "req-camera-001",
  "feature": "camera",
  "mode": "stream",
  "leaseTime": 5000,
  "params": {},
  "purpose": "scene_understanding"
}
```

Policy engine 必须检查：

- feature 是否存在于 capability profile。
- app/session 是否已授权。
- 是否需要用户确认。
- requested lease 是否超过 `maxLeaseMs`。
- requested params 是否超过功耗、隐私或 thermal 限制。
- offline 状态是否允许继续。

## 4. 用户确认

默认需要用户确认：

| Feature | Confirmation |
|---|---|
| `camera` | required |
| `microphone` | required |
| `eye` | required |
| `display` | profile-defined |
| `network` | profile-defined |

确认结果可以缓存，但必须有 TTL。缓存命中不能超过 feature 的 `maxLeaseMs` 和 policy 的 confirmation TTL。

## 5. Offline Behavior

Host 消失或连接断开时：

- 新的高功耗 feature request 必须拒绝。
- 现有 transient lease 必须到期或立即撤销。
- Device 可以继续显示 System HUD。
- Device 可以继续使用本地 safety、thermal、battery policy。
- App HUD 和 scene 可以保留最近安全 snapshot，但必须受 `validUntil` 限制。

## 6. Data Minimization

Sensor 输出按 privacy class 分类：

| Class | Examples | Rule |
|---|---|---|
| `public` | battery、thermal、network status | 可用于 telemetry |
| `motion` | IMU、pose hint | 限制采样和 retention |
| `scene` | camera feature、local vision result | 需要 camera policy |
| `biometric` | eye tracking | 需要独立 eye policy |
| `audio` | mic stream、wake audio | 需要 microphone policy |

V0.1 默认不持久化 raw camera、raw audio、eye raw stream，除非 profile 显式开启 debug/validation mode。

## 7. Policy Decision Payload

```json
{
  "decisionId": "policy-001",
  "requestId": "req-camera-001",
  "status": "accepted",
  "reason": "",
  "leaseExpiresAt": 123456789,
  "grantedParams": {},
  "requiresUserConfirmation": false
}
```

`status` 只能是：

- `accepted`
- `degraded`
- `rejected`
- `revoked`

`degraded`、`rejected`、`revoked` 必须带 `reason`。
