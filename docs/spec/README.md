# Spec 索引

V0.1 spec 文档都派生自 `docs/SDK/bible/SDK_DESIGN_OVERVIEW.md`。

建议阅读顺序：

1. [`runtime-planes.md`](runtime-planes.md) — Control、Presentation、Data 三条运行平面的 ownership。
2. [`sdk-surface.md`](sdk-surface.md) — 稳定 Host-facing SDK surface。
3. [`render-profile.md`](render-profile.md) — Meiso Profile 0 渲染 contract。
4. [`object-protocol.md`](object-protocol.md) — object/interface/opcode dispatch。
5. [`runtime-protocol.md`](runtime-protocol.md) — canonical runtime encoding。
6. [`wire-protocol.md`](wire-protocol.md) — 可选 Core Wire record wrapper。
7. [`transport-profile.md`](transport-profile.md) — link-specific reliability、security 和 limit。
8. [`wire-test-vectors.md`](wire-test-vectors.md) — binary compatibility vectors。

维护规则：

- 产品概念放在 runtime planes 和 SDK surface。
- object/runtime/wire/transport 文档只定义承载方式。
- future profile 和 manager 名称不能在没有明确 spec 变更的情况下进入 public SDK surface。
