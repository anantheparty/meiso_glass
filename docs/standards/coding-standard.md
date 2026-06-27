# Coding Standard

本规范用于保护 Meiso SDK V0.1 的起点，重点是命名、API 稳定性和测试约束。

## 命名

- public role 只使用 `host` 和 `edge`。
- public class 前缀使用 `Meiso`。
- public CLI 只使用 `meiso`。
- 不新增历史角色名作为 SDK public role。
- 文件名、目录名、协议字段、配置键、CLI 参数使用英文。
- 解释性文档正文使用中文。

## Python

- 支持 Python 3.10+。
- public contract 优先使用 `dataclass`、`Enum` 和明确的 `to_payload()` / `from_payload()`。
- wire protocol 字段由 dedicated model 生成，不允许在业务代码里手写散装 dict。
- 硬件相关代码必须放在 adapter、profile 或 development validation 中。
- 核心 SDK 不 import 平台专用 BSP、GPU、VPU、camera driver 名称。

## API

- Host API 只能通过 `FeatureRequest` 打开 Edge 高功耗功能。
- Edge 返回 `accepted`、`degraded`、`rejected`，不能用布尔值隐藏原因。
- Scene 只引用 asset ID。
- HUD 永远不能绕过 System HUD。
- Frame scheduler 由 Edge 本地 VSync 驱动，不等待 Host 下一帧。

## 文档

- `docs/SDK/bible/SDK_DESIGN_OVERVIEW.md` 是唯一 bible。
- 其它文档只能解释当前实现、API、开发环境、CI/CD 或验证方法。
- Mermaid 图只画局部关系，节点用短英文，长解释写正文。

## 复杂度控制

- 默认实现当前真实需要的最小 contract，不主动建设未来系统。
- 新增 layer、adapter、workflow 或 gate 前，必须有明确的 contract 风险、重复实现、发布需求或硬件事实。
- 未来想法可以记录为后续方向，但不能写成当前必须执行的制度。
- CI/CD 当前只分 CI Gate、Release Gate 和 Hardware Validation；本地命令只是便利，不算治理层。

## 测试

每次改变 public contract 至少更新一类测试：

- protocol contract
- feature lease contract
- scene / HUD / sensor / telemetry contract
- render profile contract
- frame scheduler contract
- forbidden old naming fitness
