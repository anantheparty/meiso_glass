# 遥测包格式

开发期 telemetry 可以在 Ethernet 或 Wi-Fi 上使用 JSON event。LR2021、BLE 或自定义低功耗无线电链路应使用紧凑二进制包。

## V0 二进制消息头

网络字节序：

```text
magic u16
version u8
packet_type u8
seq u32
timestamp_us u64
source_id u16
payload_len u16
payload bytes
crc16 u16
```

当前常量：

- magic：`0x4D47`
- version：`1`
- CRC：对 header 和 payload 计算 CRC-16/CCITT

Python 参考实现是 `meiso_glass.telemetry.packet.TelemetryPacket`。

## 包类型

- `IMU`
- `MOTION`
- `LOWFI_VISION`
- `EYE_HINT`
- `POWER_STATE`
- `THERMAL_STATE`
- `WAKE_EVENT`
- `LINK_STATS`

Payload 编码目前刻意不锁死。早期 payload 可以是紧凑的 CBOR-like 格式，也可以是项目自定义 binary struct。每个 payload 家族在接入硬件前，必须记录单位、坐标系、时间戳来源和丢包行为。

## 时间

测量延迟时，`timestamp_us` 应来自设备的单调时钟。wall-clock 只用于人类可读的日志关联。
