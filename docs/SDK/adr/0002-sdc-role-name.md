# ADR 0002: SDC Role Name

## Status

Accepted

## Context

系统需要一个表示 pocket compute / spatial data compute / host companion 的协议 role。当前使用 `sdc`。

## Decision

保留 `sdc` 作为 V0 协议 role。`sdc` 表示计算角色，不表示某个具体 SBC 或 SoC。

## Consequences

文档必须反复说明 `sdc` 是 role，不是 platform。未来如果需要面向 phone、PC、cloud companion，可在 API 层增加 alias，但 wire role 需要按 protocol version 迁移。
