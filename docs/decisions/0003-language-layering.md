# 0003 Language Layering

## Status

Accepted for V0.1 spec drafting.

## Context

早期文档容易让人误解为 Meiso SDK 默认由 Python 实现。当前仓库确实有 Python prototype，但 spec 应该是语言中立 contract。

Edge 侧是 embedded runtime，需要面向 MCU、RTOS、driver、radio buffer 和低功耗约束。Host 侧有更强算力，适合使用 Rust 实现 transport、state machine、asset tooling 和 daemon，同时通过 C ABI 提供稳定边界。Python 更适合上层 binding、prototype、mock、CLI 和测试。

## Decision

V0.1 采用语言分层：

| Layer | Decision |
|---|---|
| Edge embedded runtime core | C |
| Edge HAL / driver boundary | C |
| M4 / MCU firmware | C |
| Edge renderer public boundary | C ABI |
| Host core runtime / transport / daemon | Rust |
| Shared public ABI | C |
| Python | Upper-layer binding, prototype, mock, CLI, test harness |

Spec 示例默认使用 schema、payload shape 或伪代码。Python example 只能作为 prototype example，不能定义 core contract。

## External References

- [Zephyr C Language Support](https://docs.zephyrproject.org/latest/develop/languages/c/index.html)：Zephyr 主要以 C 实现并原生支持 C app，embedded runtime 以 C 为基线更稳。
- [FreeRTOS C Development Tools](https://www.freertos.org/Documentation/02-Kernel/05-RTOS-implementation-tutorial/02-Building-blocks/02-C-development-tools)：FreeRTOS tooling 和 RTOS 边界以 C 开发模型为主。
- [Rustonomicon FFI](https://doc.rust-lang.org/nomicon/ffi.html)：Rust 与 C/外部语言交互需要明确 FFI 边界。
- [Rust `repr(C)`](https://doc.rust-lang.org/nomicon/other-reprs.html)：跨 FFI 的数据结构需要 C-compatible layout。
- [Python Extending and Embedding](https://docs.python.org/3/extending/index.html)：Python 支持 C/C++ extension 和 embedding，更适合作为上层扩展入口。
- [PyO3 User Guide](https://pyo3.rs/)：Rust 可以暴露 Python module 或嵌入 Python，适合 Host 上层 binding。

## Consequences

- `docs/spec/` 不应把 Python API 写成 normative API。
- `src/meiso_glass/` 当前只是 prototype，不代表最终 SDK 语言。
- Edge core 不引入 Python runtime。
- Public ABI 仍然只用 C。
- Host Rust 内部类型不能直接跨语言暴露，必须经过 C ABI 或语言 binding。

## Open Questions

- Edge renderer 内部是否允许受限 C++，需要等具体 GPU/EGL/GLES driver 和工具链验证。
- Host core 是否直接使用 Rust + C ABI，还是先保留 Python prototype 到 core wire 稳定后再迁移。
- Python binding 最终采用 PyO3、CFFI、ctypes 还是生成式 binding，需要等 C ABI 固化后决定。
