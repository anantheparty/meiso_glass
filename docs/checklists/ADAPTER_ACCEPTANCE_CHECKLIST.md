# Adapter Acceptance Checklist

新增 adapter 前检查：

- [ ] 对应 interface 已存在或已评审。
- [ ] mock/fake adapter 已存在。
- [ ] contract test 已覆盖 start/stop/status/error。
- [ ] unsupported capability 返回结构化错误。
- [ ] 不把 board-specific 逻辑写入 runtime。
- [ ] 文档写明依赖、权限、格式、失败模式。
- [ ] logs/metrics 字段为英文。
- [ ] 硬件测试步骤可复现。
- [ ] 没有把真实设备作为 unit test 前置条件。
