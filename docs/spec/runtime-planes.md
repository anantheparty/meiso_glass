# 运行平面规范

本页定义 Meiso SDK V0.1 的三条运行平面。它用于避免 SDK 继续按照 manager、API 或物理模块名称膨胀。

## 1. 平面模型

```text
Control Plane
  决定哪些能力可以被启用

Presentation Plane
  决定用户最终看到什么

Data Plane
  将设备侧观测结果送出
```

Object Protocol、Runtime Encoding、Core Wire 和 Transport Profile 只负责承载这些平面的消息。它们不是第四条业务平面。

## 2. 控制平面

职责：判断 Host 请求的能力是否可以在 Device 上启用。

控制平面拥有：

- 能力快照
- Feature Lease 表
- 权限状态
- Session 状态
- 电量与温度保护输入
- 策略拒绝原因

输入：

- Host 的 Feature 请求
- Device 能力
- 用户或系统权限
- 电量与温度状态
- 链路与 Session 状态
- 安全状态

输出：

- Lease accepted
- Lease degraded
- Lease rejected
- Lease expired
- Lease revoked
- Capability update
- Session status

V0.1 的公开概念只有：

```text
FeatureLease
```

以下名称可以出现在实现内部，但不是 SDK 概念：

- Device Manager
- Policy Manager
- Power Manager
- Sensor Manager

## 3. 呈现平面

职责：维护最新的安全可见状态，并按照 Device 本地帧时钟进行显示。

呈现平面拥有：

- Scene desired-state replica
- Asset cache view
- App HUD desired state
- System HUD state
- Render Profile enforcement
- Frame Loop
- Placeholder/degraded presentation state

输入：

- 已接受的 Scene commit
- Asset catalog/cache 事件
- 已接受的 App HUD commit
- 本地姿态与 tracking
- 系统状态
- 控制平面的 lease/capability 状态

输出：

- 已呈现帧
- 帧指标
- stale/freeze/hide 决策
- asset missing / asset invalid 事件

规则：

- Frame Loop 是 Device Runtime 主干。
- Frame Loop 读取快照，不等待 Host。
- App HUD 是 Host 提交的期望状态。
- System HUD 是 Device Runtime 状态，并拥有最高显示优先级。
- Asset bytes 不得进入 Scene commit。

## 4. 数据平面

职责：将观测、测量和处理结果从 Device 送往 Host。

数据平面拥有：

- Sensor stream 对象
- 处理结果流
- 输入事件
- Telemetry 事件
- 可选 AI context 快照

输入：

- 激活中的 Feature Lease
- 传感器硬件数据
- 本地处理结果
- 帧、链路、资产等指标
- Runtime 错误

输出：

- 传感器样本
- 处理结果
- Telemetry 快照或事件
- 可选 AI context packet

规则：

- 高功耗传感器流必须有激活中的控制平面 lease。
- Sensor subscription 不能授予硬件访问权。
- Telemetry 由 Device 拥有，主要方向是 Device 到 Host。
- AI 是覆盖在数据平面和控制平面上的 adapter，不是 Runtime 必需依赖。

## 5. 跨平面规则

- 数据平面不得在没有控制平面 lease 的情况下启用传感器。
- 呈现平面可以读取控制平面状态，用于显示权限、温度、网络等 System HUD。
- 呈现平面不得等待数据平面上传完成。
- 控制平面可以根据 telemetry、温度或安全状态撤销 lease。
- Host 的期望状态永远不能覆盖 Device 的 System HUD。
- 传输失败不得阻塞 Frame Loop。

## 6. 反模式

V0.1 拒绝以下设计：

- 将独立 `PolicyManager` 暴露为公开 SDK 模块。
- Host API 以返回 transport message 作为主要抽象。
- AI tool registry 成为 core SDK 必需 surface。
- Sensor subscription 绕过 Feature Lease。
- Render thread 读取可变网络状态。
- Scene commit 携带 asset bytes。
- Core Wire 携带业务消息名。
