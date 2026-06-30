# Host Edge Contract Spec

本页区分 Host-side SDK、Edge-side runtime contract 和 shared core。不是所有能力两侧都有；Host 和 Edge 的职责不能对称化。

## Shared Core

Shared core 是两侧都必须实现或遵守的部分：

| Area | Contract |
|---|---|
| Core wire | binary frame、TLV、delivery class、CRC、fragment、ack |
| Runtime payload | message schema、payload codec、idempotency key |
| Time model | monotonic time、`displayTime`、`validUntil`、lease expiry |
| Error model | transport error 和 runtime error 分层 |
| Capability profile | Edge 声明能力，Host 按能力请求 |
| Render profile | Host 产物和 Edge renderer 的共同约束 |

Shared core 不能假设某一侧使用 Python。正式实现应以 spec、schema 和 binary fixtures 为准。

## Host-Side SDK

Host-side SDK 是应用、agent、engine wrapper 或 daemon 使用的接口层。

Host 负责：

- 建立或恢复 Host/Edge session。
- 读取 Edge capability profile。
- 发送 `FeatureRequest`，并处理 accepted / degraded / rejected。
- 生产 scene snapshot / scene delta。
- 生产 App HUD update。
- 订阅 sensor stream 或 Edge local result。
- 接收 telemetry、health、fault 和 runtime error。
- 发布或提供 asset catalog / asset chunk。
- 管理 app-level idempotency key、correlation ID 和 retry policy。

Host 不负责：

- 直接驱动 camera、display、radio、power rail、MIPI、GPU 或 MCU。
- 直接写 Edge HAL。
- 决定最终权限、热保护、电池保护或 System HUD。
- 把 Unity/Godot/OpenGL object 传给 Edge。
- 把 Python API 当作 wire contract。

## Edge-Side Runtime Contract

Edge-side runtime 不是给普通应用开发者扩展业务逻辑的 SDK。它是设备侧 core runtime 和 adapter boundary。

Edge 负责：

- 接收 core wire frame，执行 delivery class、ack、fragment、CRC 和去重。
- 发布 capability profile。
- 执行 policy decision。
- 管理 feature lease 和高功耗 adapter 生命周期。
- 控制 camera、audio、eye、IMU、display、radio、power、thermal adapter。
- 维护 Scene Replica 和 Asset Cache。
- 执行 local tracking、frame scheduler、renderer、HUD composer。
- 始终保留 System HUD 和 safety path。
- 在 Host 消失、链路变差、热/电异常时自发降级或撤销 lease。

Edge 不负责：

- 运行业务 app。
- 运行完整 Unity/Godot。
- 运行任意 shader、script 或 OpenXR native app。
- 接受 Host 绕过 policy 的直接硬件命令。
- 把 Host 的下一帧作为显示阻塞条件。

## Edge Extension Boundary

Edge 可扩展边界应该是 C ABI / C adapter，而不是 Python plugin。

| Extension | Boundary |
|---|---|
| HAL / driver | C |
| Camera adapter | C |
| Audio adapter | C |
| IMU / eye adapter | C |
| Power / thermal adapter | C |
| Radio adapter | C |
| Renderer backend | C ABI |
| MCU bridge | C protocol / binary packet |

## Host Extension Boundary

Host 可扩展边界更宽，但仍不直接暴露内部 Rust object。

| Extension | Boundary |
|---|---|
| Python package | Python binding over Host ABI |
| Unity wrapper | C# over C ABI |
| Godot wrapper | C++ GDExtension over C ABI |
| Asset tool | Rust CLI / library |
| Simulator | Rust or Python prototype |

## Contract Rule

当一个概念只属于一侧时，spec 必须写清 owner：

- Feature lease：Edge owns final state。
- Scene authority：Host owns desired scene state；Edge owns renderable replica。
- Sensor adapter：Edge owns hardware; Host owns subscription request。
- Asset bytes：Host owns source; Edge owns cache state。
- System HUD：Edge owns.
- App HUD：Host requests; Edge composes.
