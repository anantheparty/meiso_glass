# Reference Sources

本文件记录本轮结构调研使用的官方或一手资料。这里不是照搬外部规范，而是把适合 Meiso Glass SDK 的原则转化为本仓库的 bible、规则和测试。

## Architecture And Decoupling

- [Alistair Cockburn: Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture)：Ports and Adapters 的原始文章，支撑 core 只依赖 port、外部技术通过 adapter 接入的方向。
- [Google AIP-180: Backwards Compatibility](https://google.aip.dev/180)：用于区分 source、wire、semantic compatibility，并指导协议演进。
- [OpenAPI Specification](https://spec.openapis.org/oas/)：参考“API 契约先于实现”的机器可读文档方向。
- [CloudEvents Specification](https://github.com/cloudevents/spec)：参考 event envelope、interoperability 和 extension 思路。

## Protocol And Versioning

- [Semantic Versioning 2.0.0](https://semver.org/)：用于 package version 和 public API 变更语义。
- [JSON Schema Specification](https://json-schema.org/specification)：用于后续 JSON payload 和 config schema。
- [Protocol Buffers Best Practices](https://protobuf.dev/best-practices/dos-donts/)：参考字段不复用、删除字段保留、兼容演进原则。
- [RFC 8949: CBOR](https://datatracker.ietf.org/doc/html/rfc8949)：为低功耗 binary telemetry 的未来编码选型提供参考。
- [Kubernetes Deprecation Policy](https://kubernetes.io/docs/reference/using-api/deprecation-policy)：参考 API removal 和 deprecation window 的治理方式。

## Agent Runtime And Observability

- [Model Context Protocol Lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)：参考 initialize、capability negotiation、operation、shutdown 的 lifecycle 划分。
- [OpenAI Agents SDK Tracing](https://openai.github.io/openai-agents-python/tracing/)：参考 agent run 中 trace/span 的记录方式。
- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/)：参考 logs、metrics、traces 的统一 observability 模型。
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)：参考跨组件 `trace_id` 和 propagation 语义。

## Testing Packaging And Supply Chain

- [pytest Good Integration Practices](https://pytest.org/en/7.4.x/explanation/goodpractices.html)：参考 Python SDK 的测试布局和运行方式。
- [Python Packaging pyproject.toml Specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)：参考 package metadata 和 build-system 配置。
- [SLSA Specification](https://slsa.dev/spec/latest/)：参考 provenance 和 release pipeline 的长期治理。
- [OpenSSF Scorecard](https://openssf.org/scorecard/)：参考开源安全健康检查方向。
