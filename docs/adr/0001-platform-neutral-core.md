# ADR 0001: Platform Neutral Core

## Status

Accepted

## Context

项目当前有 endpoint 和 SDC 参考硬件，但长期目标是开放生态。若核心 SDK 直接写入 board/vendor 分支，后续新增平台会不断修改核心。

## Decision

core 只定义 role、protocol、telemetry、runtime contract、adapter interface。board/vendor 细节只允许出现在 platform profile、adapter、reference implementation 和 reference docs。

## Consequences

新增硬件的主要工作是实现 adapter 和 profile。短期会多一些 mock 和 contract test，但长期能降低平台迁移成本。
