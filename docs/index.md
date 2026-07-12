# Meiso Glass 文档

## 设计

- [系统设计](system.md)：解释产品目标、长期边界与核心取舍。

## 技术契约

- [Composition 契约](composition.md)：定义 layer 来源、最终合成和代际切换。
- [链路契约](link.md)：定义 Object、MediaStream、LinkSession 与 carrier 边界。

## 当前验证

- [开发板验证](validation.md)：记录当前开发板形式、C11 slice、验证顺序和完成条件。

## 历史来源

[手写方向来源](manual-origin.md) 保护提交 `70c3643` 中的原始输入，不是另一份规范。

设计文档说明为什么和边界；技术契约定义双方必须遵守的语义；验证文档只陈述当前证据。尚未进入实现的字节布局、资源参数和平台细节不提前固化。
