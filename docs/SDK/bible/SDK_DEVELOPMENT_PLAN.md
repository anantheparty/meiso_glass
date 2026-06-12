# SDK 开发计划与当前进度

## 当前阶段

当前阶段是 SDK 结构设计阶段，不是使用指南阶段，也不是完整真机 bring-up 阶段。

本阶段目标：

1. 把 SDK 的模块边界、大小资源模型、角色边界和 session 模型梳理清楚。
2. 把功耗模型提前放进 capability、session、adapter 和 telemetry。
3. 删除会导致漂移的过早文档。
4. 保留最少的核心设计文档。
5. 后续再按结构逐步改代码，而不是先堆 guide。

## 已完成

- 仓库已有最小 Python package。
- 已有 endpoint、SDC、host 三类角色雏形。
- 已有 UDP JSON message skeleton。
- 已有二进制 telemetry packet header 雏形。
- 已有 mock camera、fake IMU、fake power、fake radio 等模拟对象。
- 已有本机 smoke test 级别测试。
- 原始文档已放入 `docs/origin/`，并规定 agent 不得私自修改。
- SDK 文档已收敛到 `docs/SDK/bible/` 下三个核心文档。
- 本轮已把 Mermaid 图改成短图，把详细设计迁移到表格和字段定义。
- 本轮已把 adapter 功耗等级、多维功耗、采集/处理/传输信息量拆分写入设计。

## 本次文档收敛结果

保留：

```text
docs/SDK/bible/SDK_DESIGN_OVERVIEW.md
docs/SDK/bible/SDK_SUBSYSTEM_DESIGN.md
docs/SDK/bible/SDK_DEVELOPMENT_PLAN.md
```

不单独维护：

- 独立 guide。
- 独立 ADR。
- 独立 checklist。
- 独立 protocol 细则。
- 独立 platform 文档。
- 独立 project review。
- 独立 research/source 文档。

需要保留的信息必须先合并进三个核心文档。

## 当前设计变化

这次更新后的关键变化：

- Mermaid 只保留短图，不再用长图表达全部系统。
- `power_mode` 不再是唯一功耗抽象。
- 每个 adapter 都需要 `power_profile`。
- `power_level_u8` 使用 `0..255`，但只作为策略等级，不直接等于 mW。
- 多维功耗字段进入模型：state、duty、throughput、quality、latency、thermal、confidence。
- 摄像头设计明确拆分 `capture_cost`、`process_cost`、`egress_cost`、`information_level`。
- telemetry 增加 `adapter_power_state` 方向。
- profile 需要记录 measurement source 和 unknowns。

## 近期开发路线

### P0：结构冻结

目标：确认 SDK 一等概念。

任务：

- 确认 `role` 模型。
- 确认 resource tier 模型。
- 确认 capability 模型。
- 确认 session 模型。
- 确认 power profile 模型。
- 确认 control/telemetry/media/power 四个平面。
- 确认 adapter 和 runtime 的边界。

验收：

- 三份核心文档能够解释 SDK 为什么这样分层。
- 新增功能能明确落入某个模块，不需要新增散乱文档。
- Mermaid 图不再承载详细清单。

### P1：Power model 代码化

目标：先把功耗模型写成 SDK 数据结构，而不是先接硬件。

任务：

- 定义 `PowerLevel`、`PowerDimensions`、`PowerProfile`、`MeasuredPowerPoint`。
- 定义 `power_level_u8` 的分段常量。
- 定义 `confidence_level_u8` 和 `measurement_source`。
- 在 capability 中加入 `power_profile`。
- 在 session 中加入 `power_budget` 和 `information_budget`。
- 在 mock adapter 中实现可配置 power profile。

验收：

- mock camera 可以声明不同 level 的 resolution/fps/output。
- mock radio 可以声明 airtime/payload budget。
- mock display 可以声明 brightness/refresh 等级。
- session 可以因为 power budget 不足被拒绝或降级。

### P2：领域模型代码化

目标：把结构写进代码，而不是先接硬件。

任务：

- 新增或整理 `core` 模块。
- 定义 `Capability`、`ResourceTier`、`Session`、`SessionState`。
- 定义结构化错误。
- 定义 config schema 的最小形状。
- 保留现有 UDP 和 mock，但不要让它们定义 SDK 边界。

验收：

- mock endpoint 和 mock SDC 可以基于 session/capability/power 模型运行。
- 测试覆盖错误和状态迁移，不只覆盖 happy path。

### P3：Adapter contract

目标：使 adapter 不再是自由字典。

任务：

- 为 camera、audio、display、radio、power、M4、FPGA、storage 定义最小 contract。
- 每类 adapter 都必须暴露 `power_profile`。
- 每类 adapter 都必须返回 structured status 和 structured error。
- 为每类 adapter 加 mock contract test。
- 明确 `available`、`running`、`blocked`、`degraded` 的语义。

验收：

- 新 adapter 必须声明 capability。
- 新 adapter 必须声明 supported power levels。
- 新 adapter 必须能报告 current level 和 measurement confidence。
- mock 与 real adapter 使用同一套测试。

### P4：Control plane 状态机

目标：把命令从“字符串触发函数”升级为“状态机驱动 session”。

任务：

- 固定 envelope 和 command payload 边界。
- 增加 `start_session`、`stop_session`、`query_capability`、`set_policy`。
- 加入 `session_id`、幂等键和结构化 ACK。
- 错误返回稳定 `code`。
- ACK 中返回 selected capability、selected power level、degradation reason。

验收：

- 重复 `start_session` 不会重复启动同一资源。
- malformed message 不会打死 agent。
- unknown command 返回稳定错误。
- power budget 不足时返回可解释的拒绝或降级。

### P5：大小资源策略

目标：让大小核、大小链路、大小摄像头、大小麦克风进入 SDK 模型。

任务：

- 在 capability 中加入 `resource_tier`。
- 在 session 中声明需要的 resource tier。
- 在 power policy 中定义 mode 到 tier/level 的映射。
- 在 mock 中模拟从小资源唤醒大资源。
- 定义 `information_level_u8` 和 `egress_level_u8` 的关系。

验收：

- 可以表达“低功耗视觉事件触发 rich video session”。
- 可以表达“唤醒麦触发命令唤醒，但不启动全阵列麦”。
- 可以表达“LR/BLE 控制链路与高速 Wi-Fi 媒体链路不同”。
- 可以表达“摄像头高采集但只传 ROI tuple”。

### P6：Measurement path

目标：让功耗等级从纯设计变成可验证数据。

任务：

- 定义 `MeasuredPowerPoint` fixture。
- 定义 rail measurement schema。
- 支持 OS source：Linux `hwmon`、Linux `powercap`、Android PowerStats 类数据。
- 支持 external fixture source。
- session 结束时记录 power summary。

验收：

- 每个 mock session 能输出 fake measurement。
- 真机没有 rail 数据时，可以记录 `declared_only` 或 `datasheet_estimate`。
- 有 rail 数据时，可以记录 `mw_avg`、`mw_peak`、`uj_per_event`、`uj_per_frame`。
- confidence 低的数据不会被 policy 当成精确预算。

### P7：Reference path

目标：在 SDK 结构清楚后，再考虑真实硬件落地。

任务：

- Orin 作为 SDC reference path。
- MX8MM 作为 endpoint reference path。
- 决定 MX8MM endpoint 是 Android proxy、Android native，还是 embedded Linux。
- 建立 direct Ethernet 的最小测试路径。
- 再接视频、功耗、M4、低功耗传感器。

验收：

- reference path 只使用 public SDK contract。
- 真机发现的问题能反向修正 SDK 模型。
- 本地敏感配置不进入 remote 仓库。

## 当前明确不做

- 不维护独立使用指南。
- 不维护后期移植文档。
- 不维护大量 checklist。
- 不为还没稳定的设计单独写 ADR。
- 不把真机 bring-up 脚本放进 core。
- 不把本地实验室敏感信息放进 remote 仓库。
- 不把任何一个 OS 的 power API 当作 SDK 唯一模型。
- 不把 `power_level_u8` 伪装成真实 mW。

## 主要风险

### 风险 1：平台中立变成空泛抽象

应对：

- 所有抽象都必须能解释 i.MX8MM + Orin reference path。
- 但 reference path 不得反向硬编码进 core。

### 风险 2：大小系统继续缺席

应对：

- resource tier 必须进入 capability、session 和 power policy。
- 任何涉及 camera、audio、radio、compute 的设计都必须说明自己属于大资源、小资源，还是跨层升级路径。

### 风险 3：功耗模型太粗

应对：

- 每个 adapter 都要有 `power_profile`。
- 每个 profile 都区分 level、dimension、measurement source 和 confidence。
- 摄像头、radio、display 等不能只用一个字符串 mode 表达。

### 风险 4：功耗模型太细导致实现拖慢

应对：

- V0 只要求少量 supported levels。
- 没测量数据可以先用 `declared_only`。
- 8-bit 分段先作为策略骨架，不要求所有 adapter 支持所有档位。

### 风险 5：文档再次膨胀

应对：

- 新 SDK 文档默认不允许创建。
- 先改三份核心文档。
- 只有当内容稳定、重复引用、且确实无法继续放在三份文档中时，才拆分。

### 风险 6：实现绕过设计

应对：

- 先把 session/capability/resource tier/power profile 写进代码。
- 再迁移当前 UDP/GStreamer/mock。
- 测试必须覆盖状态机、错误、降级和 power budget，而不仅是对象 roundtrip。

## 未决问题清单

这些问题暂时不强行定稿：

1. `power_level_u8` 是否应该跨 adapter family 可比。
2. 是否保留 256 档，还是 V0 先公开 128 档、保留高 bit。
3. `information_level_u8` 是否应当进入所有 media session，还是先只在 camera/radio 上定义。
4. Camera 的 `capture_level`、`process_level`、`egress_level` 是否需要分别进入 wire telemetry。
5. 没有 rail 级测量时，如何从整机功耗差分估算 adapter 功耗。
6. M4、FPGA、A53 三者之间的低功耗视觉边界需要真实测量，不应靠直觉决定。
7. Display 的功耗模型是否需要按显示技术拆分。
8. Radio 的低功耗模型是否能抽象到 BLE/LR/Wi-Fi 共用字段，同时保留各协议特性。
9. PowerAdapter 的采样开销如何计入 session budget。
10. confidence 低的数据是否允许进入自动 policy，还是只允许人工分析。

## 下一步建议

1. 先确认三份文档中的 power model 方向是否符合项目判断。
2. 如果方向确认，下一步先改代码结构：建立 `core/power` 的最小模型。
3. 再把 `Capability`、`Session`、`AdapterStatus` 串起来。
4. 然后补 mock camera/radio/display/power 的 power profile contract tests。
5. 最后再把 Orin/MX8MM reference path 接进 adapter 和 runtime。

## 当前状态快照

```text
文档结构：已收敛
Mermaid：已改为短图
SDK 总体结构：草案
大小资源模型：已进入设计文档，未进入代码
power profile：已进入设计文档，未进入代码
8-bit power level：已进入设计文档，未进入代码
session 模型：已进入设计文档，未进入代码
adapter contract：已有旧雏形，需要重做
control plane：已有旧雏形，需要状态机化
telemetry：已有 header 雏形，需要 payload family 和 power state payload
media：已有 smoke test 雏形，需要 session 化
measurement：只有设计，需要 schema 和 fake fixture
reference hardware：准备阶段，不作为当前文档重点
```
