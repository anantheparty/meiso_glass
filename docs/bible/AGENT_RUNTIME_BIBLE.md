# Agent Runtime Bible

本文件定义 EndpointAgent、SDCAgent、HostTool 的生命周期。

## Lifecycle

每个 agent 必须支持以下阶段：

```text
initialize
negotiate_capabilities
run
drain
shutdown
```

`initialize` 建立 dependency graph，但不应立即要求真实硬件存在。

`negotiate_capabilities` 交换 role、protocol version、transport、video、telemetry、power、debug 能力。

`run` 处理 heartbeat、command、telemetry、session event。

`drain` 停止接收新 session，等待已有 session 收尾。

`shutdown` 释放 transport、process、device handle、log sink。

## Runtime 依赖

runtime 应依赖 port/interface：

- `ControlTransport`
- `HeartbeatTransport`
- `VideoSessionRunner`
- `HealthProvider`
- `PowerProvider`
- `Clock`
- `Logger`

runtime 不应直接创建 UDP socket、GStreamer process、platform probe。V0 可以暂时保留 legacy constructor，但必须向依赖注入迁移。

## Command 语义

每个 command 必须定义：

- idempotency
- timeout
- cancel
- retry
- ACK fields
- error code
- state transition
- observability event

## Fake Runtime Tests

核心状态机测试必须能在没有 socket、没有 subprocess、没有硬件的情况下运行。fake transport 和 fake clock 是 runtime 正确性的第一测试入口。
