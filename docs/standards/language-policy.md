# Language Policy

本文件是语言选型 policy，不是第二个 bible。唯一 bible 仍然是 `docs/SDK/bible/SDK_DESIGN_OVERVIEW.md`。

## Default Rule

默认选择能保护当前 contract 的最简单语言，不因为未来可能需要而提前拆出多语言系统。

## Current V0

- Spec 是语言中立 contract，不是 Python API 文档。
- 当前仓库里的 Python 代码只作为 prototype、mock、CLI 和本机验证 harness。
- Wiki、spec、开发文档使用 Markdown。
- Wire protocol 的真源头是 binary layout、schema、fixture 和 contract test，不是某个语言实现。

## Production Targets

| Area | Language |
|---|---|
| Edge embedded runtime core | C |
| Edge HAL / driver boundary | C |
| M4 / MCU firmware | C |
| Edge renderer / EGL / GLES2 boundary | C public ABI, C implementation preferred |
| Host core runtime | Rust |
| Host protocol / transport implementation | Rust, with C ABI boundary where shared |
| Host daemon / service | Rust |
| Asset cooker / validator / simulator / replay | Rust |
| Python package | Upper-layer binding over Host C ABI or Rust binding |
| Unity wrapper | C# over C ABI |
| Godot wrapper | C++ GDExtension + C ABI |
| Public ABI | C |

## Layering Rule

- Edge 侧默认按 embedded C 设计，避免把 Python、Rust runtime、C++ exception 或 heap-heavy assumptions 带入 Edge core。
- Host 侧可以使用 Rust 实现 transport、state machine、asset tooling 和 daemon。
- C 是跨语言和跨平台的 stable ABI 边界。
- Python 是上层开发体验、prototype 和测试入口，不是 core SDK contract。
- Spec 示例优先使用 schema、伪代码或 payload shape；只有明确写为 prototype/example 时才使用 Python。

## ABI Rules

- Public ABI 只使用 C。
- C++ exception 不得跨 ABI。
- Rust panic 不得跨 ABI。
- Memory ownership 必须显式：谁创建、谁释放、buffer 生命周期多久。
- Callback 必须声明 thread ownership 和 reentrancy。
- Error model 必须是稳定 status code，加可选 message 和 details。
- Unity、Godot 和其它 engine wrapper 只能绑定 C ABI，不直接绑定内部 Rust/C++ 对象。

## External References

- [Zephyr C Language Support](https://docs.zephyrproject.org/latest/develop/languages/c/index.html)：Zephyr 主要以 C 实现并原生支持 C app，embedded runtime 以 C 为基线更稳。
- [FreeRTOS C Development Tools](https://www.freertos.org/Documentation/02-Kernel/05-RTOS-implementation-tutorial/02-Building-blocks/02-C-development-tools)：FreeRTOS tooling 和 RTOS 边界以 C 开发模型为主。
- [Rustonomicon FFI](https://doc.rust-lang.org/nomicon/ffi.html)：Rust 与 C/外部语言交互需要明确 FFI 边界。
- [Rust `repr(C)`](https://doc.rust-lang.org/nomicon/other-reprs.html)：跨 FFI 的数据结构需要 C-compatible layout。
- [Python Extending and Embedding](https://docs.python.org/3/extending/index.html)：Python 支持 C/C++ extension 和 embedding，更适合作为上层扩展入口。
- [PyO3 User Guide](https://pyo3.rs/)：Rust 可以暴露 Python module 或嵌入 Python，适合 Host 上层 binding。

## Complexity Rule

新增语言前必须满足至少一个条件：

- 当前语言无法表达稳定 ABI 或实时约束。
- 已有实现出现不可接受的性能、内存或平台限制。
- 目标平台明确要求该语言或 ABI。
- 新语言边界已经有 contract test、fixture 或 smoke test 保护。
