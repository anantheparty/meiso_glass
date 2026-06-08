# Decoupling Bible

本文件定义解耦要求。目标不是抽象越多越好，而是让 SDK 核心长期不被参考硬件污染。

## Core 禁区

`src/meiso_glass` core 不得包含：

- reference board name
- vendor-specific device path
- vendor-specific decoder alias
- platform-only capability assumption
- direct subprocess requirement for core state machine
- direct socket requirement for core state machine
- environment-only health logic that cannot be mocked

允许出现在 core 的内容：

- generic role name
- protocol enum
- adapter protocol interface
- generic GStreamer reference helper，前提是不包含 vendor branch
- portable Linux development helper，前提是不成为 SDK 契约

## Adapter 边界

adapter 的职责是把外部技术转换成 SDK port。adapter 可以知道硬件、BSP、driver、radio、camera、display、sensor、process、socket。

runtime 的职责是 state machine、command dispatch、session metadata、error handling。runtime 不应该知道 adapter 背后的硬件。

## Reference Implementation 边界

reference implementation 用来证明 contract 可运行，不是 contract 本身。

例如 H.264/RTP/GStreamer 可以是 V0 reference video implementation，但 SDK API 只能承诺 video session capability，不承诺所有平台都有同样的 GStreamer element。

## 可执行约束

CI 必须包含 architecture fitness tests：

- core source denylist
- generic config denylist
- docs governance existence
- machine-readable content ASCII check

denylist 不是架构的全部，但能阻止最常见的早期漂移。
