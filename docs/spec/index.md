# Spec

本页定义 Meiso SDK V0.1 的初版 contract 形状。`SDK_DESIGN_OVERVIEW.md` 仍是唯一 bible；本页只把 bible 落成可开发、可测试的 spec。

## Spec Index

这些页面是当前 V0.1 contract 的专项 spec：

- [Wire Protocol](./wire-protocol.md)：消息头、对象 ID、通道语义、版本兼容、错误码。
- [Capability Profile](./capability-profile.md)：设备能力、渲染等级、传感器能力、功耗档位。
- [State Machines](./state-machines.md)：连接、Feature Lease、传感器、资产同步。
- [Time Model](./time-model.md)：时钟同步、timestamp、`validUntil`、`displayTime`。
- [Render Profile](./render-profile.md)：Meiso Profile 0/1/2 支持和禁止的能力。
- [Security Policy](./security-policy.md)：相机、麦克风、眼动、用户确认、离线策略。
- [Fault Model](./fault-model.md)：延迟、丢包、乱序、断连、资产缺失、Host 消失。

## 命名

- `Host` 是业务和计算侧角色名。
- `Edge` 是设备和显示侧 runtime 角色名。
- 公开 CLI 使用 `meiso`，子命令使用 `host`、`edge`、`send`、`probe`。
- 公开类名前缀使用 `Meiso`，例如 `MeisoHost`、`MeisoEdgeRuntime`、`MeisoMessage`。

## Language Neutrality

本 spec 是语言中立 contract。示例使用 payload shape 或伪代码表达，不代表 SDK 必须用 Python 实现。

实现分层原则：

| Layer | Preferred Implementation |
|---|---|
| Edge embedded runtime core | C |
| Edge HAL / MCU firmware | C |
| Edge renderer boundary | C ABI |
| Host core runtime / transport / daemon | Rust |
| Shared public ABI | C |
| Python | 上层 binding、prototype、mock、CLI、测试 harness |

## Host Contract

Host 侧 contract 暂定五组接口：

| API | 责任 |
|---|---|
| `device` | 连接 Edge、查询能力、申请 feature、释放 feature |
| `scene` | 提交 `SceneSnapshot` 或后续增量更新 |
| `hud` | 提交 App HUD 的 text、image、panel、progress、anchor、layout |
| `sensor` | 订阅 camera、audio、eye、IMU 或 Edge 本地处理结果 |
| `telemetry` | 读取温度、电量、FPS、丢帧、网络、缓存和错误 |

伪代码：

```text
host = open_host_session("session-dev")

request = FeatureRequest {
  feature: "camera",
  mode: "stream",
  leaseTime: 5000,
  requestId: "req-camera-001"
}

host.device.request_feature(request)
```

## Meiso Core Wire

Core wire 使用二进制 frame，不使用 JSON envelope。固定头只承载接收、长度、校验和低层传输需要的信息：

| Field | 说明 |
|---|---|
| `magic` | ASCII `MEIS` |
| `version` | core wire version |
| `flags` | fragment、ack echo、retransmit、compressed、encrypted |
| `frame_type` | numeric core/runtime frame type |
| `header_ext_len` | TLV extension byte count |
| `total_len` | whole frame byte count |
| `payload_len` | payload byte count |
| `header_crc32c` | fixed header CRC |
| `body_crc32c` | extension + payload CRC |

Runtime payload 可以是 JSON、CBOR、Protobuf、FlatBuffers 或 raw bytes。Core 层只按 bytes 传输和校验。

## Delivery Classes

Logical channel 在 V0.1 改名为 delivery class。它是 core transport 的异步投递语义，不是业务 API 分类：

| Delivery Class | 用途 |
|---|---|
| `reliable_ordered` | 控制、权限、FeatureRequest、关键状态 |
| `unreliable_latest` | Transform、连续输入、实时遥测、最新状态 |
| `bulk_resumable` | 资产、日志、配置、replay |
| `tiny_control` | 唤醒、状态查询、缓存内容 ID、建立高速链路 |

Transport ack 不代表业务成功。业务成功或失败必须由 runtime response 表达。

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
