# SDK Bible

本文件是 Meiso Glass SDK 的最高层工程契约。后续具体 API、adapter、平台 profile、demo、脚本都必须服从这里的边界。

## 核心目标

Meiso Glass SDK 要成为开放的 dual-device AR 生态框架，而不是某一对开发板的演示工程。当前 endpoint 参考板和 SDC 参考板只用于 bring-up、验证和示例，不得把 SDK 核心锁死到这些硬件。

SDK 核心只定义：

- `role`
- message protocol
- telemetry format
- runtime lifecycle
- adapter contracts
- platform profile contract
- mock and simulation behavior
- tests and release gates

SDK 核心不定义：

- board-specific branch
- vendor-specific decoder alias
- fixed device path
- hardware-only startup assumption
- transport-only API

## 不可漂移规则

- `src/meiso_glass` 不得出现参考平台 token，例如 `imx8mm`、`orin`、`jetson`、`tegra`、`nvv4l2`。
- 具体硬件实现必须位于 adapter、reference implementation、platform profile 或 docs/SDK/reference 中。
- 每个硬件能力都必须有 mock 或 fake 实现，真实硬件不是开发和 CI 的前置条件。
- public API 不得等同于 UDP client、GStreamer pipeline 或某个板卡 BSP。
- 所有 wire payload、config key、CLI command、log field、metric name 必须使用英文 ASCII 标识。
- 解释性文档正文使用中文，文件名和目录名使用英文。
- 协议变更先改 schema、fixture、兼容矩阵，再改实现。
- SDK 的正确性以测试门禁为准，不以手工跑通某块板为准。

## 合并门槛

任何 PR 至少说明它影响了下列哪类契约：

- architecture boundary
- public API
- protocol
- telemetry binary format
- runtime lifecycle
- adapter contract
- platform profile
- observability
- tests
- docs

如果影响 public API、protocol、telemetry、runtime lifecycle、adapter contract，必须同时更新对应 bible、checklist 和测试。

## 本文件的来源

本 bible 综合了本仓库审计、subagent 审计和官方资料调研。核心参考包括 Ports and Adapters、Google AIP-180、SemVer、JSON Schema、Protocol Buffers best practices、OpenTelemetry、W3C Trace Context、MCP lifecycle、pytest、SLSA 和 OpenSSF Scorecard。完整来源见 [REFERENCE_SOURCES.md](../research/REFERENCE_SOURCES.md)。
