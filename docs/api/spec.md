# API Spec

本页定义 Meiso SDK V0.1 的初版 API 形状。`SDK_DESIGN_OVERVIEW.md` 仍是唯一 bible；本页只把 bible 落成可开发、可测试的 contract。

## Spec Index

这些页面是当前 V0.1 contract 的专项 spec：

- [Wire Protocol](./specs/wire-protocol.md)：消息头、对象 ID、通道语义、版本兼容、错误码。
- [Capability Profile](./specs/capability-profile.md)：设备能力、渲染等级、传感器能力、功耗档位。
- [State Machines](./specs/state-machines.md)：连接、Feature Lease、传感器、资产同步、AI Tool。
- [Time Model](./specs/time-model.md)：时钟同步、timestamp、`validUntil`、`displayTime`。
- [Render Profile](./specs/render-profile.md)：Meiso Profile 0/1/2 支持和禁止的能力。
- [Security Policy](./specs/security-policy.md)：相机、麦克风、眼动、用户确认、离线策略。
- [Fault Model](./specs/fault-model.md)：延迟、丢包、乱序、断连、资产缺失、Host 消失。

## 命名

- `Host` 是业务和计算侧角色名。
- `Edge` 是设备和显示侧 runtime 角色名。
- 公开 CLI 使用 `meiso`，子命令使用 `host`、`edge`、`send`、`probe`。
- 公开类名前缀使用 `Meiso`，例如 `MeisoHost`、`MeisoEdgeRuntime`、`MeisoMessage`。

## Host SDK

Host SDK 暴露六组 API：

| API | 责任 |
|---|---|
| `device` | 连接 Edge、查询能力、申请 feature、释放 feature |
| `scene` | 提交 `SceneSnapshot` 或后续增量更新 |
| `hud` | 提交 App HUD 的 text、image、panel、progress、anchor、layout |
| `sensor` | 订阅 camera、audio、eye、IMU 或 Edge 本地处理结果 |
| `telemetry` | 读取温度、电量、FPS、丢帧、网络、缓存和错误 |
| `ai` | 面向 agent 的 tools、context、state API |

Python 入口：

```python
from meiso_glass.api import FeatureName, FeatureRequest, MeisoHost

host = MeisoHost(session_id="session-dev")
msg = host.device.request_feature(
    FeatureRequest(
        feature=FeatureName.CAMERA,
        mode="stream",
        lease_time_ms=5000,
        request_id="req-camera-001",
    )
)
```

## AI Native API

Host SDK 暴露 `host.ai`，用于 agent-friendly 的工具、上下文和状态管理。

核心对象：

- `ToolSpec`
- `ToolCall`
- `ToolResult`
- `ContextItem`
- `ContextPacket`
- `StateSnapshot`
- `StatePatch`

规则：

- tool 名字必须使用 `meiso.` 前缀。
- tool 必须声明 logical channel。
- 会打开 Edge 高功耗功能的 tool 必须通过 lease。
- state patch 必须带 `base_version`。
- context packet 必须可压缩，不能无限增长。

详细设计见 [AI Native API](./ai-native.md)。

## Meiso Protocol Header

所有 Meiso message 的 wire header 使用这些字段：

| Field | 说明 |
|---|---|
| `protocolVersion` | 当前为 `1` |
| `sessionId` | Host/Edge 会话或逻辑连接 ID |
| `messageType` | `feature_request`、`scene_snapshot` 等 |
| `channel` | `high_reliable`、`latest_wins`、`low_reliable`、`low_power` |
| `sequence` | 当前 channel 内的序号 |
| `sourceTimestamp` | 单调时间戳 |
| `payloadLength` | canonical JSON payload 长度 |
| `flags` | bit flags，V0.1 默认为 `0` |

legacy role/direction/timestamp 字段不再是 public protocol。

## Logical Channels

| Channel | 用途 |
|---|---|
| `high_reliable` | 控制、权限、FeatureRequest、实体创建/销毁、关键状态 |
| `latest_wins` | Transform、连续输入、实时遥测、最新状态 |
| `low_reliable` | 资产、日志、配置、非紧急同步 |
| `low_power` | 唤醒、通知、状态查询、缓存内容 ID、建立高速链路 |

`low_power` 不允许实时 3D scene stream 或大资产。

## FeatureRequest

Host 只能通过 `FeatureRequest` 显式开启 Edge 上的高功耗功能。

Wire payload：

```json
{
  "feature": "camera",
  "mode": "stream",
  "params": {},
  "priority": "normal",
  "leaseTime": 5000,
  "requestId": "req-camera-001"
}
```

Edge 只返回三类结果：

- `accepted`
- `degraded`
- `rejected`

`degraded` 和 `rejected` 必须带 `reason`。`accepted` 和 `degraded` 可以带 `leaseExpiresAt`。

## Scene API

最小实体模型：

- `EntityId`
- `ParentId`
- `Transform`
- `MeshId`
- `MaterialId`
- `Visibility`
- `AnimationState`
- `Lifetime`
- `ReplicationMode`

Scene message 只引用 asset ID，不内嵌 mesh、texture、font bytes。

## HUD API

Host 只能创建 App HUD。System HUD 属于 Edge runtime，应用不能遮挡。

固定合成顺序：

```text
3D Scene -> App HUD -> System HUD
```

## Sensor API

订阅字段包括：

- sensor 类型
- 分辨率
- 频率
- encoding
- data type
- max duration
- params

Camera、microphone、eye 使用独立权限和独立状态。

## Telemetry API

V0.1 必须覆盖：

- temperature
- battery
- fps
- dropped_frames
- network_latency
- packet_loss
- cache
- error

## Render Profile 0

允许：

- static low-poly mesh
- transform
- unlit color
- unlit texture
- vertex color
- alpha blend
- simple depth test
- fixed texture/material count

拒绝：

- dynamic shadow
- arbitrary shader
- particle
- post-processing
- script
- complex local physics

超出 profile 的资产构建必须报错，不允许静默降级。
