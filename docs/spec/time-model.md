# 时间模型规范

Meiso SDK 不用 wall clock 决定消息顺序或显示时机。所有实时控制使用 monotonic nanoseconds。

## 1. Clock 类型

| 字段 | Clock | 含义 |
|---|---|---|
| `source_time_ns` | sender monotonic ns | frame 或 runtime message 生成时间 |
| `received_time_ns` | receiver monotonic ns | frame 到达时间，本地记录 |
| `captureTime` | Device monotonic ns | sensor sample 捕获时间 |
| `displayTime` | Device monotonic ns | 目标显示时刻 |
| `validUntil` | receiver domain or declared domain | 数据有效期 |
| `leaseExpiresAt` | Device monotonic ns | feature lease 到期 |
| `expiresAt` | owner monotonic ns | HUD、asset request 等过期 |
| `unixTime` | wall clock ns | 只用于日志关联，不用于排序 |

字段必须声明时间域。没有声明时，`source_time_ns` 属于发送端 monotonic domain。

## 2. Time Sync

`time_sync` 用于估计 Host 和 Device monotonic clock 的 offset。

```json
{
  "syncId": "sync-001",
  "hostSendTime": 1000000000,
  "deviceReceiveTime": 1200000000,
  "deviceSendTime": 1201000000,
  "hostReceiveTime": 1003000000
}
```

Host 可以估算：

- `roundTripNs = hostReceiveTime - hostSendTime - (deviceSendTime - deviceReceiveTime)`
- `offsetNs = deviceReceiveTime - (hostSendTime + roundTripNs / 2)`
- `uncertaintyNs = max(roundTripNs / 2, transportJitterEstimate)`

V0.1 不要求高精度同步，但必须记录 `uncertaintyNs`。未知同步精度不能被当成精确时间。

## 3. Ordering

- Link Profile 的 sequence 决定低层包序或重复包统计。
- Object version 决定 latest-state 对象新旧。
- State version 决定 desired-state patch 或 commit 的基线。
- `source_time_ns` 不用于替代 sequence 或 version。
- 如果 timestamp 倒退，receiver 必须记录 telemetry，并按 sequence、object version 或 state version 处理。

## 4. validUntil

`validUntil` 表示数据过期后不能继续作为实时事实使用。

规则：

- Sensor sample 过期后不能用于新的 runtime decision。
- Transform 过期后 Device 可以短时预测，然后 freeze 或 hide。
- HUD 过期后必须移除或进入 stale 表示。
- Policy decision 过期后必须重新评估。

## 5. displayTime

`displayTime` 只由 Device Frame Loop 最终解释。

规则：

- Host 可以提交期望显示时刻，但 Device 可以因 VSync、tracking、thermal 或 safety 调整。
- Device 永远不等待 Host 的下一帧。
- Frame Loop 使用最近完整 immutable scene snapshot。
- 最终 pose prediction 使用 Device 本地 tracking 数据。

## 6. Lease Time

Feature lease 使用 Device monotonic time 计算到期。

- Host 请求使用 duration：`leaseTime`。
- Device response 返回 absolute：`leaseExpiresAt`。
- Host disconnect 后，Device 不依赖 Host 时间关闭高功耗 feature。

## 7. Timeout Defaults

V0.1 推荐默认值：

| 项目 | 默认值 |
|---|---:|
| heartbeat interval | 1000 ms |
| heartbeat timeout | 3000 ms |
| feature request timeout | 2000 ms |
| control retry window | 5000 ms |
| stale transform window | 100 ms |

这些是默认建议，不是硬件实测值。具体 profile 可以收紧，但不能放松 safety lease。
