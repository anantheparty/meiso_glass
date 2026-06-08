# Mock / 模拟器指南

开发者应当能在没有实体硬件的普通 PC 上运行 SDK。

## 当前模拟组件

- `MockEndpoint`
- `MockSDC`
- `MockCameraAdapter`
- `FakeIMU`
- `FakePowerMonitor`
- `FakeLowfiTelemetryGenerator`
- `FakeFpgaPacketGenerator`
- `FakeRadioLink`

代码位置：

```text
src/meiso_glass/adapters/mock.py
src/meiso_glass/simulation/mock_devices.py
```

## 使用场景

- 测试协议消息
- 生成 fake 低保真遥测
- 测试功耗模式处理
- 在没有 endpoint 硬件时运行 SDC 侧融合开发
- record/replay 工具可用后，用于回放基准测试

## 规则

任何被 example app 使用的硬件 adapter，都必须有 mock 实现，并且必须有能在普通开发 PC 上运行的测试。
