# SDK 公开面规范

本页定义 Meiso SDK V0.1 的稳定 Host-facing surface。它刻意排除 wire、transport、runtime manager 和 AI registry 这类内部实现面。

## 1. 公开 Surface

| Surface | 方向 | 用途 |
|---|---|---|
| `Session` | Host ↔ Device | 连接、关闭、查询能力、接收事件 |
| `FeatureLease` | Host → Device → Host | 请求、释放、撤销高功耗或特权能力 |
| `Scene` | Host → Device | 通过紧凑实体和资产引用提交 3D 期望状态 |
| `Hud` | Host → Device | 提交 App HUD 期望状态 |
| `SensorStream` | Device → Host | 在 lease 通过后传递样本或处理结果 |
| `AssetCatalog` | Host → Device | 发布资产元数据和分块，分配 runtime asset alias |
| `Telemetry` | Device → Host | 上报健康、帧、链路、资产、传感器和策略事件 |

## 2. V0.1 不公开的内容

以下内容是内部实现或生成物，不是稳定 SDK contract：

- Core Wire record
- Object Protocol dispatch table
- Runtime Encoding record
- Transport Manager
- Device Manager
- Policy Manager
- Power Manager
- Frame Scheduler
- Render backend
- AI tool registry
- Python debug message envelope

它们可以出现在测试、prototype 或调试工具中，但不能被当作稳定 SDK contract。

## 3. Session

Session 管理连接生命周期和能力发现。

必需操作：

```text
connect
close
query_capabilities
subscribe_events
```

Session 事件包括：

- connected
- disconnected
- capability_changed
- link_changed
- fatal_error

## 4. FeatureLease

FeatureLease 是公开 SDK 请求特权能力或高功耗能力的唯一方式。

必需操作：

```text
request_feature(feature, mode, params, lease_time)
release_feature(lease_id)
```

必需结果：

```text
accepted
degraded
rejected
expired
revoked
```

高分辨率相机、麦克风、眼动追踪等传感器访问，必须先通过 FeatureLease，再允许进入数据流。

## 5. Scene

Scene 提交视觉期望状态。Device 拥有最终 Runtime 状态。

必需操作：

```text
commit_scene(scene_state)
clear_scene
```

Scene state 只能包含：

- entity id
- parent id
- transform
- visibility
- asset reference
- material reference
- simple animation state token
- lifetime
- replication mode

Scene state 不得包含 asset bytes、script、engine object、shader graph 或 physics object。

## 6. Hud

Hud 只提交 App HUD 期望状态。

必需操作：

```text
commit_app_hud(hud_state)
clear_app_hud
```

V0.1 允许的 App HUD 元素：

- text
- image
- panel
- progress

System HUD 由 Device 拥有，不暴露为 Host 可创建元素。

## 7. SensorStream

SensorStream 在 FeatureLease 激活后传递数据。

必需操作：

```text
subscribe_sensor_stream(lease_id, stream_spec)
unsubscribe_sensor_stream(subscription_id)
```

SensorStream 不能创建或延长 lease。它只能绑定到已经 accepted 的 lease。

## 8. AssetCatalog

AssetCatalog 将长期资产身份映射为 session-local alias。

必需操作：

```text
publish_asset_metadata
send_asset_chunk
remove_asset_alias
```

规则：

- content hash 是长期身份。
- alias 是 session-local。
- Device 根据 Render Profile 和 Device budget 验证资产。
- Scene commit 只有在 catalog 注册后才能引用 alias。

## 9. Telemetry

Telemetry 是读取和事件 surface，不是控制 API。

必需事件类别：

- frame metrics
- feature lease events
- transport metrics
- asset cache events
- sensor stream health
- thermal/power events
- policy degrade/reject reasons

Host 可以订阅 telemetry。Telemetry 的产生者是 Device。

## 10. AI Adapter 边界

V0.1 中 AI 是可选能力。

AI adapter 可以：

- 读取由 Session、Telemetry、Scene 和 Sensor result 派生的 context。
- 通过公开 SDK surface 请求动作。
- 接收 ToolResult 事件。

AI adapter 不得：

- 绕过 FeatureLease。
- 直接写 System HUD。
- 访问 Core Wire 内部。
- 成为 Session、Scene、HUD、Sensor 或 Telemetry 的必需依赖。

## 11. Prototype 边界

当前 Python 包可以提供 debug factory、mock 和 CLI helper。这些可以不同于最终 C ABI / Rust / C++ 实现。

只有当本文明确列为 public surface，或由批准后的 IDL 生成时，某个 Python type 才能成为 contract。
