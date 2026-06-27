# Language Policy

本文件是语言选型 policy，不是第二个 bible。唯一 bible 仍然是 `docs/SDK/bible/SDK_DESIGN_OVERVIEW.md`。

## Default Rule

默认选择能保护当前 contract 的最简单语言，不因为未来可能需要而提前拆出多语言系统。

## Current V0

- SDK contract、mock、simulator、CLI：Python。
- Wiki、spec、开发文档：Markdown。
- Wire protocol 的真源头是 schema、fixture 和 contract test，不是某个语言实现。

## Production Targets

| Area | Language |
|---|---|
| Edge runtime | C++17 |
| Edge HAL | C |
| M4 firmware | C |
| Renderer / EGL / GLES2 | C++17 |
| Protocol reference implementation | Rust |
| Host daemon | Rust |
| Asset cooker / validator / simulator / replay | Rust |
| Unity wrapper | C# over C ABI |
| Godot wrapper | C++ GDExtension over C ABI |
| Public ABI | C |

## ABI Rules

- Public ABI 只使用 C。
- C++ exception 不得跨 ABI。
- Rust panic 不得跨 ABI。
- Memory ownership 必须显式：谁创建、谁释放、buffer 生命周期多久。
- Callback 必须声明 thread ownership 和 reentrancy。
- Error model 必须是稳定 status code，加可选 message 和 details。
- Unity、Godot 和其它 engine wrapper 只能绑定 C ABI，不直接绑定内部 Rust/C++ 对象。

## Complexity Rule

新增语言前必须满足至少一个条件：

- 当前语言无法表达稳定 ABI 或实时约束。
- 已有实现出现不可接受的性能、内存或平台限制。
- 目标平台明确要求该语言或 ABI。
- 新语言边界已经有 contract test、fixture 或 smoke test 保护。
