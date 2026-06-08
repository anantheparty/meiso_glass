# Core Boundary Rules

本文件是 core boundary 的审查规则。

## Core 包含什么

`src/meiso_glass` 可以包含：

- protocol types
- telemetry packet format
- adapter interfaces
- runtime interfaces
- platform-neutral helpers
- mock and simulation utilities

## Core 不包含什么

`src/meiso_glass` 不应包含：

- reference board name
- vendor BSP branch
- fixed lab device path as contract
- hard-coded platform capability
- platform-specific decoder alias
- hardware-only startup requirement

## 允许例外

允许例外必须满足：

- 放在 reference implementation 子模块。
- 文档说明为什么暂时不能抽象。
- 有 issue 或 TODO 指向迁移计划。
- architecture fitness test 有显式白名单。

默认不允许隐式例外。

## 审查问题

每次改 core 时必须问：

- 这段代码能在普通 PC mock 环境运行吗？
- 这段代码是否知道某个 board/vendor？
- 这段代码是否能被 fake transport/video/power 替换？
- 这段代码是否改变了 public contract？
- 这段代码是否需要新增 protocol fixture 或 adapter contract test？
