# 0002 Remove AI Native Interface

## Status

Accepted for V0.1 spec drafting.

## Context

早期 spec 增加了 `AI Native Interface`，包括 tools、context、state、ToolSpec、ToolCall、ToolResult 等对象。

这层抽象会把 SDK 已有的 Device、Scene、HUD、Sensor、Telemetry 再封装一遍，容易限制 agent 开发者，也会把 agent runtime 的偏好写进底层 SDK contract。

## Decision

V0.1 删除 AI Native Interface 作为 SDK contract。

SDK 只提供稳定 Host/Edge contract：

- Device
- Scene
- HUD
- Sensor
- Telemetry
- Wire / Transport
- Capability / Policy / Fault / Time model

Agent 开发者可以在 SDK 之上自行封装 tools、context、state，但这些不是 Meiso core spec 的一部分。

## Consequences

- `docs/spec/ai-native.md` 删除。
- Spec index 不再列出 AI Native Interface。
- State machine、fault model、security policy 和 time model 不再包含 AI Tool 语义。
- 代码中如果仍保留 AI helper，也只能视为实验实现，不能作为 public contract。

## Open Questions

- 后续是否提供 examples 给 agent 开发者参考。
- 如果提供 examples，应放在 examples 或 integration layer，不能进入 core spec。
