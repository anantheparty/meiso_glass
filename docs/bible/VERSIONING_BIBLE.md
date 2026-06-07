# Versioning Bible

本文件定义 package、protocol、schema、profile 的版本规则。

## Package Version

Python package 使用 SemVer：

- MAJOR：public API 或已发布协议发生不兼容变化。
- MINOR：向后兼容新增功能。
- PATCH：向后兼容修复。

在 `0.x` 阶段仍要写清 breaking change，不能把 `0.x` 当作随意破坏契约的理由。

## Protocol Version

`Message.version` 表示 wire protocol major version。相同 major version 内：

- old client 必须能和 new server 做基本交互。
- new optional field 不得破坏 old client。
- 默认值语义不得静默改变。

## Schema Version

JSON message、config profile、binary telemetry 都应有自己的 schema 或 format version。它们可以和 package version 不同步，但每次变更必须记录兼容性。

## Deprecation

废弃流程：

1. 在 docs 和 changelog 标记 deprecated。
2. 保留兼容解析。
3. 加入 runtime warning 或 log event。
4. 至少跨一个 minor release 后才能移除。
5. 移除必须提升 major version 或 format version。

## Compatibility Matrix

协议变更必须维护矩阵：

```text
old endpoint <-> new sdc
new endpoint <-> old sdc
old host     <-> new endpoint
new host     <-> old endpoint
```
