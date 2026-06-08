# Supply Chain Bible

本文件定义从私有研发期到开源生态期的最小供应链治理。

## 私有期最低要求

- `main` 分支保持可测试。
- 每次结构性改动都运行 `pytest`。
- GitHub Actions 使用最小权限 token。
- actions 版本固定到明确版本，后续再升级到 SHA pin。
- 依赖更新记录在 PR 中。
- 不提交密钥、私钥、实验室凭据。

## 开源前要求

- LICENSE
- CODEOWNERS
- SECURITY.md
- CONTRIBUTING.md
- CI required checks
- dependency update policy
- SBOM roadmap
- provenance roadmap
- release checklist

## 发布原则

SDK release 必须包含：

- package version
- protocol version
- compatibility notes
- migration notes
- test result
- known hardware-gated validation status

## 安全基线

后续接入 OpenSSF Scorecard、SLSA provenance、Sigstore signing、SBOM 工具时，不应改变 SDK runtime contract。供应链工具属于 release pipeline，不属于 endpoint/sdc runtime。
