# AI Native API

Meiso SDK 的 AI-native API 不是把 LLM 塞进 runtime，而是把 SDK 变成 agent 容易安全使用的工具系统。

核心对象：

| Object | 作用 |
|---|---|
| `ToolSpec` | 描述可调用能力、输入输出 schema、channel、lease、确认需求 |
| `ToolCall` | 一次可追踪、可幂等的工具调用 |
| `ToolResult` | 工具调用结果，必须显式 `ok`、`rejected` 或 `error` |
| `ContextItem` | 给 agent 使用的局部上下文 |
| `ContextPacket` | 按优先级压缩后的上下文包 |
| `StateSnapshot` | 只读状态快照 |
| `StatePatch` | 带 version precondition 的状态变更 |
| `MeisoAiApi` | Host 上的 tools/context/state 聚合入口 |

## Design Rules

- tool 名字必须使用 `meiso.` 前缀。
- tool 必须声明 `kind` 和 logical channel。
- 会打开 Edge 高功耗功能的 tool 必须通过 lease。
- state patch 必须带 `base_version`，避免 agent 用旧状态覆盖新状态。
- context 可过期、可按 priority 压缩，不能无限堆进 prompt。
- Tool result 不能只返回布尔值；失败必须有错误或拒绝原因。

## Python Example

```python
from meiso_glass.api import ContextItem, ContextKind, MeisoHost, StatePatch

host = MeisoHost(session_id="session-ai")

host.ai.context.put(
    ContextItem(
        context_id="ctx-scene",
        kind=ContextKind.SCENE,
        content={"activeEntityCount": 3},
        priority=10,
    )
)

state = host.ai.state.apply(
    StatePatch(
        state_id="state-session",
        base_version=0,
        set_values={"mode": "idle"},
    )
)

packet = host.ai.build_context_packet(max_items=8)
tools = host.ai.tools.list_tools()
```

## Default Tools

`MeisoHost` 默认注册：

- `meiso.device.request_feature`
- `meiso.scene.submit_snapshot`
- `meiso.hud.update`
- `meiso.sensor.subscribe`
- `meiso.telemetry.report`

这些 tool 只是 SDK contract。真正执行时仍然要经过 Host/Edge runtime、FeatureRequest lease、policy 和 Meiso Protocol。
