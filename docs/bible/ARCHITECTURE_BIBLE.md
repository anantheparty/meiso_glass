# Architecture Bible

本文件定义 SDK 的长期结构。它比某个模块的当前实现更重要。

## 依赖方向

允许的方向：

```text
protocol / telemetry / timebase
  <- ports and interfaces
  <- runtime
  <- api / cli / apps

adapter interfaces
  <- runtime

concrete adapters
  <- composition root / platform profile / demo
```

禁止的方向：

- `protocol` 依赖 runtime、config、transport、adapter。
- `telemetry` 依赖 platform profile。
- `runtime` 依赖具体 board、BSP、radio、camera、decoder。
- `api` 依赖某个 concrete transport。
- generic config 依赖参考平台命名。

## 层定义

`protocol` 层定义 message envelope、message type、error model、compatibility rule。

`telemetry` 层定义 low-power binary packet 和 development telemetry event。

`ports` 层定义 transport、video、camera、power、sensor、storage、audio、bridge 的抽象接口。

`runtime` 层实现 EndpointAgent、SDCAgent、HostTool 的 lifecycle 和 state machine。

`adapter` 层实现具体硬件、mock、simulator、reference implementation。

`platform` 层用 profile 组合 adapter，不向核心注入 board-specific branch。

## Role 和 Platform

`endpoint`、`sdc`、`host` 是协议 role，不是设备型号。

`platform` 是 profile 的属性，用于加载 adapter 组合和调试说明。`platform` 不得改变 core protocol 的语义。

## Composition Root

所有 concrete transport、video process、probe、hardware adapter 都应该在 composition root 装配。当前 V0 的 CLI 可以暂时承担 composition root 角色，但 runtime 构造函数应逐步支持依赖注入，方便 fake tests 和非 UDP/非 GStreamer 实现。
