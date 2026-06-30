# 0004 State Machine Boundaries

## Status

Accepted for V0.1 spec drafting.

## Context

早期 state machine 把 `discovering`、`authenticating`、`syncing`、`requested`、`validating` 等过程都写成状态。这会让 core 状态变成流程描述，而不是系统行为承接点。

Host 和 Edge 也不能共用一套状态。Host 是 app/session/request owner；Edge 是 hardware/policy/lease/runtime owner。

## Decision

V0.1 state machine 只保留能改变行为的状态：

- Core Link：`down`、`up`、`limited`
- Host Session：`idle`、`linked`、`limited`、`lost`
- Edge Runtime：`booting`、`standalone`、`linked`、`limited`、`safe_mode`
- Feature Lease：`off`、`running`、`stopping`
- Sensor Subscription：`off`、`streaming`、`paused`、`stopping`
- Asset Cache：`missing`、`fetching`、`ready`、`bad`

这些过程不是状态：

- discovery
- authentication
- capability sync
- time sync
- request received
- validation

它们是 task、event、transition guard 或 transition action。

## Consequences

- 每个状态必须说明 allowed behavior、self behavior 和 exit。
- Host state 不得暗示 Host 拥有 hardware。
- Edge state 必须保留 System HUD、thermal、battery 和 safety path。
- Sync 不阻塞 core 行为；它在 `linked/up` 内后台运行。
- Mermaid 图只画最小转移，不画长解释。

## Open Questions

- `safe_mode` 的退出条件需要真实 hardware fault 和 thermal policy 校准。
- 是否需要把 media/video path 单独定义状态机，等视频 spec 出来再决定。
