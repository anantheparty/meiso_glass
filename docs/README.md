# 文档索引

`docs/` 按主题整理，目录名和文件名保持英文，正文说明使用中文。

## SDK 治理入口

- [SDK 总纲](bible/SDK_BIBLE.md)
- [架构总纲](bible/ARCHITECTURE_BIBLE.md)
- [解耦总纲](bible/DECOUPLING_BIBLE.md)
- [测试总纲](bible/TESTING_BIBLE.md)
- [协议总纲](bible/PROTOCOL_BIBLE.md)
- [版本治理](bible/VERSIONING_BIBLE.md)
- [Agent Runtime 总纲](bible/AGENT_RUNTIME_BIBLE.md)
- [Adapter Contract 总纲](bible/ADAPTER_CONTRACT_BIBLE.md)
- [Config Profile 总纲](bible/CONFIG_PROFILE_BIBLE.md)
- [Control Plane 总纲](bible/CONTROL_PLANE_BIBLE.md)
- [Observability 总纲](bible/OBSERVABILITY_BIBLE.md)
- [Supply Chain 总纲](bible/SUPPLY_CHAIN_BIBLE.md)
- [Reference Implementation 边界](bible/REFERENCE_IMPLEMENTATION_BOUNDARY.md)

## 规则和检查清单

- [语言和命名规则](rules/LANGUAGE_AND_NAMING_RULES.md)
- [核心边界规则](rules/CORE_BOUNDARY_RULES.md)
- [传输内容规则](rules/TRANSPORT_PAYLOAD_RULES.md)
- [解耦审查清单](checklists/DECOUPLING_REVIEW_CHECKLIST.md)
- [协议变更清单](checklists/PROTOCOL_CHANGE_CHECKLIST.md)
- [Adapter 验收清单](checklists/ADAPTER_ACCEPTANCE_CHECKLIST.md)
- [Platform 验收清单](checklists/PLATFORM_ACCEPTANCE_CHECKLIST.md)
- [Release 清单](checklists/RELEASE_READINESS_CHECKLIST.md)

## 架构

- [SDK 架构](architecture/SDK_ARCHITECTURE.md)

## 协议与遥测

- [消息协议](protocol/MESSAGE_PROTOCOL.md)
- [遥测包格式](protocol/TELEMETRY_PACKET_FORMAT.md)

## 硬件适配与模拟

- [硬件 Adapter API](adapters/HARDWARE_ADAPTER_API.md)
- [Mock/模拟器指南](adapters/MOCK_SIMULATOR_GUIDE.md)

## 使用和移植指南

- [首次运行](guides/FIRST_RUN.md)
- [平台移植指南](guides/PLATFORM_PORTING_GUIDE.md)
- [兼容性检查清单](guides/COMPATIBILITY_CHECKLIST.md)

## 功耗与基准

- [功耗基准指南](benchmarks/POWER_BENCHMARK_GUIDE.md)
- [功耗和延迟日志](benchmarks/POWER_AND_LATENCY_LOGGING.md)

## 平台与项目记录

- [参考平台：i.MX8MM + Orin](platforms/REFERENCE_PLATFORM_IMX8MM_ORIN.md)
- [从 arglasses_dual_device_sdk_v0 迁移](project/MIGRATION_FROM_ARGSDK_V0.md)
- [SDK 文档设计与维护评审](project/SDK_DOCUMENTATION_AND_MAINTENANCE_REVIEW.md)

## ADR 和调研来源

- [ADR 0001: Platform Neutral Core](adr/0001-platform-neutral-core.md)
- [ADR 0002: SDC Role Name](adr/0002-sdc-role-name.md)
- [ADR 0003: UDP JSON Control Plane V0](adr/0003-udp-json-control-plane-v0.md)
- [ADR 0004: Adapter Backed Hardware](adr/0004-adapter-backed-hardware.md)
- [ADR 0005: Chinese Docs English Contracts](adr/0005-chinese-docs-english-contracts.md)
- [调研来源](research/REFERENCE_SOURCES.md)
