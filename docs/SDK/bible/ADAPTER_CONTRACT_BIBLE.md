# Adapter Contract Bible

本文件定义 adapter 的通用契约。

## Adapter 原则

adapter 是 SDK core 和外部技术之间的唯一边界。外部技术包括 camera、display、encoder、radio、power monitor、M4 bridge、FPGA bridge、sensor、storage、audio、transport、health probe。

每个 adapter 必须：

- 实现明确 interface。
- 提供 `get_status()` 或等价状态输出。
- 支持可重复 `start` 和 `stop`，重复调用不得破坏状态。
- 对 unsupported capability 返回结构化错误，不得静默成功。
- 不把中文写入 machine payload。
- 提供 mock 或 fake 实现。
- 跑过共享 contract tests。

## 状态字段

状态字段使用英文 machine key：

```json
{
  "name": "mock_camera",
  "state": "running",
  "capabilities": ["video_source"],
  "errors": []
}
```

## 真实硬件 Adapter

真实 adapter 可以依赖平台库、device path、BSP 工具和 vendor binary，但这些依赖必须被限制在 adapter 包或 reference implementation 中。

真实 adapter 文档必须说明：

- required kernel/module/driver
- required permissions
- supported formats
- expected power state
- failure modes
- hardware test procedure

## Mock Parity

mock adapter 不需要模拟所有性能特征，但必须模拟 contract 语义、状态迁移、错误路径和 observability fields。
