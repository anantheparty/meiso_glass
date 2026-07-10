# Meiso Glass

Meiso Glass 是一个由 `Edge` 与 `Host` 组成的双端嵌入式系统。

- `Edge` 负责设备驱动、传感器采集、本地低延迟行为和最终显示。
- `Host` 负责较重的数据处理，并决定应用希望 `Edge` 显示的内容。

当前只验证一条最小闭环：

```text
Edge camera + timestamped IMU
  -> Host overlay decision
  -> Edge pose correction
  -> Edge display
```

开发板上会把修正后的 overlay 叠加到 camera 画面，以便直接观察结果。camera 背景合成只是验证工具，不属于正式穿戴设备。

项目仍处于早期验证阶段。当前开发板、操作系统和 Wi-Fi 都只是验证条件，不构成产品接口；仓库暂时没有需要兼容的稳定实现。

## 文档

- [系统形式](docs/system.md)
- [链路契约](docs/link.md)
- [开发板验证](docs/validation.md)
- [文档入口](docs/index.md)
