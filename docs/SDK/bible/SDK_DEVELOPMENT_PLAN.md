# Meiso Glass SDK Bible：开发计划与冻结路线

> 状态：Bible v0.4 XR-core 草案
> 修订日期：2026-06-13
> 当前阶段：SDK bible 结构冻结 -> core schema / presentation / power 代码化

## 0. 当前判断

当前不是写使用指南的阶段，也不是完整真机 bring-up 阶段。当前最重要的是冻结一条足够小、足够硬、能解释 AR 眼镜特点的 SDK 主线：

```text
SystemProfile -> Capability -> Session -> Space/ViewSet/Layer -> PowerBudget -> Adapter -> Evidence
```

本版比 v0.3 更简化：

- 保留 OpenXR/WebXR 类 XR SDK 的核心对象：system、session、space、view、layer、frame timing、action slot、extension slot。
- 删除不适合当前阶段的完整 loader、graphics binding、render engine、full action map、anchors/hit-test/mesh public API。
- 把功耗从七维大表压成 `PowerBudget + PowerLevel + PowerCostPoint + MeasuredPowerPoint`。
- 把单眼/双眼/3D 的问题统一放进 `ViewSet`。
- 把未来 depth/stereo/IR/event camera 放进 `SensorSlot` / `SpatialCapability`，不提前写 adapter。

## 1. 已完成状态

已存在：

- 最小 Python package。
- endpoint、SDC、host 三类角色雏形。
- UDP JSON message skeleton。
- 二进制 telemetry packet header 雏形。
- mock camera、fake IMU、fake power、fake radio 等模拟对象。
- 本机 smoke test 级别测试。
- 原始文档放入 `docs/origin/`，不应被 agent 私自修改。
- SDK bible 收敛到三份核心文档。

已进入 bible：

- role / core / runtime / adapters / profile 分层。
- capability/session/power/evidence 主线。
- ResourceTier 大小系统。
- PowerLevel 和 measurement source。
- Camera capture/process/egress/information 分离。
- Presentation/ViewSet/Layer/FrameTiming 初版 contract。
- Future depth/spatial sensor slot。
- Telemetry 和 adapter status 方向。

尚未进入代码：

- SystemProfile / Capability / Session schema。
- Space / ViewSet / PresentationLayer schema。
- PowerBudget / PowerProfile / PowerCostPoint schema。
- Adapter base contract。
- Runtime admission。
- Evidence recorder。
- Contract test suite。

## 2. Phase gates

### P0：Bible v0.4 冻结

目标：三份文档能稳定指导代码，不再继续发散。

任务：

- 冻结 10 个核心对象：`SystemProfile`、`Capability`、`ResourceTier`、`Session`、`Space`、`ViewSet`、`PresentationLayer`、`PowerBudget`、`PowerProfile`、`Evidence`。
- 明确 Meiso 不是完整 OpenXR runtime。
- 明确 SDK 管 presentation contract，不管 render engine。
- 明确 future depth/stereo/anchor/hit-test 只作为 declared slot。
- 明确 power 是 admission 约束，不是 telemetry 附属字段。
- 删除文档中对未落地 adapter 的过细展开。

验收：

- 新功能能落入 core/space/presentation/power/adapters/runtime/control/telemetry/evidence/profile 之一。
- 文档能解释初版单眼和未来双眼/3D 不冲突。
- 文档能解释 future depth 为什么不写 DepthCameraAdapter。
- 文档能解释 power level 为什么不等于 mW。
- 三份文档职责互不重叠。

产物：

```text
docs/SDK/bible/SDK_DESIGN_OVERVIEW.md
docs/SDK/bible/SDK_SUBSYSTEM_DESIGN.md
docs/SDK/bible/SDK_DEVELOPMENT_PLAN.md
```

### P1：Core schema 代码化

目标：先把 public contract 写成数据结构和 schema。

任务：

- 建立 `core/`。
- 定义 `Metadata`、`SemanticPath`、`Condition`、`StructuredError`。
- 定义 `SystemProfile`、`Capability`、`ResourceTier`、`Session`。
- 所有长生命周期对象拆 `spec/status/evidence`。
- 增加 schema validation。
- 增加 serialization roundtrip tests。
- 增加 API surface snapshot 或等价测试。

验收：

- 能表达 endpoint/sdc/host 三类 role。
- 能表达 lowfi camera、rich camera、eye hint、display mono、radio telemetry、power probe capability。
- `declared` capability 不能被当成可运行能力。
- 缺失关键字段会失败。
- session 非法状态迁移会失败。

产物：

```text
core/path.py
core/metadata.py
core/condition.py
core/error.py
core/profile.py
core/capability.py
core/resource_tier.py
core/session.py
tests/core/test_schema_roundtrip.py
tests/core/test_session_state.py
tests/core/test_declared_capability.py
```

### P2：Space / Presentation schema 代码化

目标：把 AR 眼镜最关键的显示和坐标 contract 放进代码。

任务：

- 建立 `space/` 和 `presentation/`。
- 定义 `SpaceRef`、`Pose`、`SpaceRelation`。
- 定义 `SensorSlot`、`SpatialCapability`。
- 定义 `ViewSet`、`ViewSlot`。
- 定义 `PresentationSurface`、`PresentationLayer`、`PresentationSessionSpec`。
- 定义 `FrameTiming`、`PresentationFrameStats`。
- 写 mono profile fixture。
- 写 future stereo/depth declared slot fixture。

验收：

- 初版单眼 display 表达为 `ViewSet.topology=mono`。
- 未来双眼/3D 可表达为 `ViewSet.topology=stereo|multiview|three_d`，不改 Session 模型。
- Future depth slot 可以 declared，但 admission 不可使用。
- PresentationLayer 不包含 shader/material/scene graph。
- FrameStats 可以表达 drop、late、refresh degrade。

产物：

```text
space/space.py
space/pose.py
space/relation.py
space/sensor_slot.py
space/spatial_capability.py
presentation/view.py
presentation/surface.py
presentation/layer.py
presentation/session_spec.py
presentation/frame_timing.py
tests/presentation/test_viewset.py
tests/presentation/test_declared_future_slots.py
```

### P3：Power model 代码化

目标：把功耗变成 admission 可用的数据结构。

任务：

- 建立 `power/`。
- 定义 `PowerBudget`、`PowerLevel`、`PowerProfile`、`PowerCostPoint`、`PowerTransition`、`MeasuredPowerPoint`。
- 定义 measurement source 和 confidence。
- 写 level band 常量。
- 在 Capability 中接入 `power_profile_ref`。
- 在 Session 中接入 `PowerBudget`。
- 写 budget check helper。

验收：

- `power_level_u8` 不等于 mW。
- supported levels 不要求 256 档。
- 没测量数据可用 `declared_only`，但 confidence 低。
- budget 不足会 reject 或 degrade。
- PowerAdapter 自身采样成本可表达。
- Presentation session 可以因为 brightness/refresh/layer/view 触发 power degradation。

产物：

```text
power/level.py
power/budget.py
power/profile.py
power/cost_point.py
power/transition.py
power/measurement.py
power/check.py
tests/power/test_level_band.py
tests/power/test_budget_check.py
tests/power/test_measurement_confidence.py
```

### P4：Adapter base contract

目标：让 adapter 不再是自由字典。

任务：

- 建立 `adapters/base.py`。
- 定义 `AdapterStatus`、`AdapterProbeResult`、`ValidationResult`。
- 定义 family contracts：camera、display、presentation_port、radio、sensor、compute_bridge、power、storage。
- 迁移现有 mock camera/fake IMU/fake power/fake radio。
- 写 shared adapter contract tests。
- 明确 V0 不写 `RenderAdapter`、不写 `DepthCameraAdapter`。

验收：

- 每个 adapter 必须声明 capability。
- 每个 adapter 必须声明 power profile。
- 每个 adapter 必须返回 structured status/error。
- mock 和 real adapter 使用同一套测试。
- DisplayAdapter 不暴露 layer/scene graph。
- PresentationPort 只消费 PresentationSessionSpec。

产物：

```text
adapters/base.py
adapters/status.py
adapters/camera.py
adapters/display.py
adapters/presentation_port.py
adapters/radio.py
adapters/sensor.py
adapters/compute_bridge.py
adapters/power.py
adapters/storage.py
tests/adapters/test_contract.py
```

### P5：Runtime admission 和 session manager

目标：把命令从“字符串触发函数”升级为 admission + 状态机。

任务：

- 建立 `runtime/admission.py`。
- 实现 capability filtering。
- 实现 validation_state gate。
- 实现 dependency/conflict 检查。
- 实现 power/link/thermal/display/presentation budget 检查。
- 实现 degradation selection。
- 实现 session state machine。
- 支持 idempotency key。
- 输出 admission trace。

验收：

- 重复 start 不重复启动资源。
- unknown capability 返回稳定错误。
- `declared` future slot 不会被选中。
- power budget 不足返回 reject/degrade。
- presentation budget 不足能降刷新、降 viewport、关 layer 或拒绝。
- session stop 后有 evidence。

产物：

```text
runtime/admission.py
runtime/session_manager.py
runtime/degradation.py
runtime/policy.py
tests/runtime/test_admission.py
tests/runtime/test_idempotency.py
tests/runtime/test_presentation_degradation.py
```

### P6：Control plane 固化

目标：让 endpoint/SDC/host 通过稳定 envelope 协作。

任务：

- 固定 `ControlEnvelope`。
- 固定 command payload。
- 固定 ACK/error 格式。
- 接入 session manager。
- 保留现有 UDP JSON，但不让 UDP 定义 public contract。
- 增加 malformed message tests。

验收：

- `query_system_profile`、`query_capabilities`、`propose_session`、`start_session`、`stop_session` 可跑通 mock。
- malformed message 不打死 runtime。
- 错误码稳定。
- ACK 包含 selected plan / idempotency hit / warning。

产物：

```text
control/envelope.py
control/commands.py
control/ack.py
control/errors.py
tests/control/test_envelope.py
tests/control/test_malformed.py
```

### P7：Telemetry / Evidence path

目标：让 session 决策可回放。

任务：

- 定义 telemetry payload family。
- 定义 binary header 与 JSON debug event 对照。
- 定义 `SessionEvidence`。
- 定义 evidence recorder。
- 增加 replay reader。
- 接入 power summary、presentation frame stats、adapter status。

验收：

- 每个 session stop 后有 evidence。
- 可以看到 admission trace。
- 可以看到 frame stats。
- 可以看到 power confidence/source。
- 可以从 evidence 解释 reject/degrade。

产物：

```text
telemetry/payloads.py
telemetry/header.py
telemetry/replay.py
evidence/session_evidence.py
evidence/recorder.py
tests/evidence/test_session_evidence.py
```

### P8：Simulation / conformance

目标：在真机前让 contract 先稳定。

任务：

- Fake endpoint 支持 lowfi/rich/display/power/radio capability。
- Fake SDC 支持 proposal/admission/start/stop。
- Fake presentation clock 支持 frame drop/late/degrade。
- Fake power measurement 支持 confidence/source。
- 增加 conformance fixtures。

验收：

- 本机能跑完整 session flow。
- Mock display presentation 可模拟 mono HUD。
- Mock future depth slot 会被拒绝 admission。
- Mock power budget 不足会降级。
- 测试覆盖失败路径。

产物：

```text
simulation/fake_endpoint.py
simulation/fake_sdc.py
simulation/fake_presentation.py
simulation/fake_power.py
tests/conformance/test_v0_flow.py
```

### P9：Reference path 再接真机

目标：在 contract 稳定后接 i.MX8MM / Orin reference path。

任务：

- MX8MM endpoint profile fixture。
- Orin SDC profile fixture。
- direct Ethernet / Wi-Fi path 最小连接。
- rich video path 作为 media session，不污染 core。
- display DSI path 作为 DisplayAdapter/PresentationPort，不污染 render engine。
- lowfi HM0360/GW1NZ/LR2021 path 作为 camera/radio/compute bridge adapters。
- power rail data 进入 MeasuredPowerPoint。

验收：

- 真机路径只使用 public SDK contract。
- 真机发现的问题反向修正 schema，而不是写旁路脚本。
- 本地敏感配置不进 remote。
- 所有硬件路径都有 validation_state。

## 3. 当前明确不做

- 不做使用指南。
- 不做完整 OpenXR runtime。
- 不做 OpenXR bridge。
- 不做 RenderAdapter。
- 不做 DepthCameraAdapter。
- 不做 anchors/hit-test/mesh public API。
- 不做 shader/material/scene graph。
- 不做完整 controller action map。
- 不为每种未来传感器新建 adapter。
- 不把 hardware bring-up 脚本放进 core。
- 不把 `power_level_u8` 当成 mW。

## 4. 风险和应对

### 风险 1：借鉴 OpenXR 后变成过大 runtime

应对：只借对象边界，不借 loader/graphics binding/full action map。P0 明确 Meiso SDK 是 device/session/power contract layer。

### 风险 2：presentation 继续被 DisplayAdapter 吃掉

应对：DisplayAdapter 只管 panel/link/power；ViewSet/Layer/FrameTiming 进入 presentation 模块。

### 风险 3：未来 depth/stereo 提前污染 V0

应对：future capability 只能 declared，不可 admission；不得写 DepthCameraAdapter。

### 风险 4：power model 太细拖慢代码

应对：V0 只要求 `PowerBudget + PowerLevel + PowerCostPoint`，family detail 放 settings。

### 风险 5：power model 太粗不能指导 AR 眼镜

应对：admission 必须看 power/link/thermal/display/presentation；session evidence 必须记录 source/confidence。

### 风险 6：Profile 变成 IP 配置文件

应对：Profile 必须声明 capability、adapter binding、validation_state、measurement_sources、unknowns。

### 风险 7：实现绕过设计

应对：contract tests 先于真机 adapter；mock 和 real 共用测试。

## 5. 未决问题

这些问题暂不阻塞 v0.4：

1. `PowerLevel` 跨 adapter family 是否需要更强可比性。
2. PresentationSurface 是否需要真正 swapchain 语义，还是 V0 用 stream/surface 足够。
3. `SpaceRelation` 是否需要 covariance；V0 可以先只用 confidence。
4. Eye hint 输出是否统一成 `SpatialCapability(gaze)`，还是保留 camera tuple 到 SDC 融合。
5. Mono display 的 `eye` 字段初版写 `none` 还是由 product profile 指定 left/right。
6. Future depth 的 output form 是否先只定义 depth_map/confidence_map，还是预留 mesh/plane。
7. PowerAdapter 的采样功耗如何计入长期 sentinel mode。
8. Display/presentation 的真实功耗是否需要按 panel 技术拆 profile。
9. LR2021/BLE/Wi-Fi 的 link profile 是否需要统一 retry/airtime schema。
10. OpenXR bridge 如果未来需要，是由 SDC 侧实现，还是作为 host/debug 工具实现。

## 6. 最近下一步

最推荐的代码顺序：

1. 写 `core/metadata.py`、`core/path.py`、`core/error.py`、`core/condition.py`。
2. 写 `core/capability.py`、`core/session.py`、`core/profile.py`。
3. 写 `space/` 和 `presentation/` 的 schema，不接真显示。
4. 写 `power/` 的 schema 和 budget check。
5. 迁移 mock adapter 到 base contract。
6. 写 runtime admission。
7. 再接现有 UDP JSON。
8. 最后接真机 reference path。

判断标准：**每一步都必须增加 contract test，而不是只增加一个能跑的 demo。**
