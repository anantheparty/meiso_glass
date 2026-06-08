# SDK 开发计划与当前进度

## 当前阶段

当前阶段是 SDK 结构设计阶段，不是使用指南阶段，也不是完整真机 bring-up 阶段。

本阶段目标：

1. 把 SDK 的模块边界、大小资源模型、角色边界和 session 模型梳理清楚。
2. 删除会导致漂移的过早文档。
3. 保留最少的核心设计文档。
4. 后续再按结构逐步改代码，而不是先堆 guide。

## 已完成

- 仓库已有最小 Python package。
- 已有 endpoint、SDC、host 三类角色雏形。
- 已有 UDP JSON message skeleton。
- 已有二进制 telemetry packet header 雏形。
- 已有 mock camera、fake IMU、fake power、fake radio 等模拟对象。
- 已有本机 smoke test 级别测试。
- 原始文档已放入 `docs/origin/`，并规定 agent 不得私自修改。
- SDK 文档已收敛到 `docs/SDK/bible/` 下三个核心文档。

## 本次文档收敛结果

保留：

```text
docs/SDK/bible/SDK_DESIGN_OVERVIEW.md
docs/SDK/bible/SDK_SUBSYSTEM_DESIGN.md
docs/SDK/bible/SDK_DEVELOPMENT_PLAN.md
```

删除或合并：

- 独立 guide。
- 独立 ADR。
- 独立 checklist。
- 独立 protocol 细则。
- 独立 platform 文档。
- 独立 project review。
- 独立 research/source 文档。

这些内容目前不应单独维护。确实需要保留的设计信息已经合并到三个核心文档。

## 近期开发路线

### P0：结构冻结

目标：确认 SDK 一等概念。

任务：

- 确认 `role` 模型。
- 确认 resource tier 模型。
- 确认 capability 模型。
- 确认 session 模型。
- 确认 control/telemetry/media/power 四个平面。
- 确认 adapter 和 runtime 的边界。

验收：

- 三份核心文档能够解释 SDK 为什么这样分层。
- 新增功能能明确落入某个模块，不需要新增散乱文档。

### P1：领域模型代码化

目标：先把结构写进代码，而不是先接硬件。

任务：

- 新增或整理 `core` 模块。
- 定义 `Capability`、`ResourceTier`、`Session`、`SessionState`。
- 定义结构化错误。
- 定义 config schema 的最小形状。
- 保留现有 UDP 和 mock，但不要让它们定义 SDK 边界。

验收：

- mock endpoint 和 mock SDC 可以基于 session/capability 模型运行。
- 测试覆盖错误和状态迁移，不只覆盖 happy path。

### P2：Control plane 状态机

目标：把命令从“字符串触发函数”升级为“状态机驱动 session”。

任务：

- 固定 envelope 和 command payload 边界。
- 增加 `start_session`、`stop_session`、`query_capability`。
- 加入 `session_id`、幂等键和结构化 ACK。
- 错误返回稳定 `code`。

验收：

- 重复 `start_session` 不会重复启动同一资源。
- malformed message 不会打死 agent。
- unknown command 返回稳定错误。

### P3：大小资源策略

目标：让大小核、大小链路、大小摄像头、大小麦克风进入 SDK 模型。

任务：

- 在 capability 中加入 `tier`。
- 在 session 中声明需要的 resource tier。
- 在 power policy 中定义 mode 到 tier 的映射。
- 在 mock 中模拟从小资源唤醒大资源。

验收：

- 可以表达“低功耗视觉事件触发 rich video session”。
- 可以表达“唤醒麦触发命令唤醒，但不启动全阵列麦”。
- 可以表达“LR/BLE 控制链路与高速 Wi-Fi 媒体链路不同”。

### P4：Adapter contract

目标：使 adapter 不再是自由字典。

任务：

- 为 camera、audio、display、radio、power、M4、FPGA 定义最小 contract。
- 为每类 adapter 加 mock contract test。
- 明确 `available`、`running`、`blocked`、`degraded` 的语义。

验收：

- 新 adapter 必须声明 capability。
- 新 adapter 必须能返回结构化 status 和 error。
- mock 与 real adapter 使用同一套测试。

### P5：Reference path

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

## 主要风险

### 风险 1：平台中立变成空泛抽象

应对：

- 所有抽象都必须能解释 i.MX8MM + Orin reference path。
- 但 reference path 不得反向硬编码进 core。

### 风险 2：大小系统继续缺席

应对：

- resource tier 必须进入 capability、session 和 power policy。
- 任何涉及 camera、audio、radio、compute 的设计都必须说明自己属于大资源、小资源，还是跨层升级路径。

### 风险 3：文档再次膨胀

应对：

- 新 SDK 文档默认不允许创建。
- 先改三份核心文档。
- 只有当内容稳定、重复引用、且确实无法继续放在三份文档中时，才拆分。

### 风险 4：实现绕过设计

应对：

- 先把 session/capability/resource tier 写进代码。
- 再迁移当前 UDP/GStreamer/mock。
- 测试必须覆盖状态机和错误，而不仅是对象 roundtrip。

## 下一步建议

1. 先确认这三份文档定义的 SDK 结构是否符合项目方向。
2. 如果方向确认，下一步改代码结构：建立 `core`、`control`、`media`、`power` 的最小模型。
3. 再把现有 `messages.py`、`agents.py`、`adapters/` 迁到新结构。
4. 最后再把 Orin/MX8MM reference path 接进 adapter 和 runtime。

## 当前状态快照

```text
文档结构：已收敛
SDK 总体结构：草案
大小资源模型：已进入设计文档，未进入代码
session 模型：已进入设计文档，未进入代码
adapter contract：已有旧雏形，需要重做
control plane：已有旧雏形，需要状态机化
telemetry：已有 header 雏形，需要 payload family
media：已有 smoke test 雏形，需要 session 化
power：只有概念，需要模型化
reference hardware：准备阶段，不作为当前文档重点
```
