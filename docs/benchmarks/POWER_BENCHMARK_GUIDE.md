# 功耗基准指南

功耗是 SDK 的一等约束。每个 session 都应记录足够的元数据，用来解释能耗、延迟和唤醒行为。

## 功耗模式

1. 关机 / 运输模式（Off / Ship）
2. 常开哨兵模式（Always-on Sentinel）
3. 低保真视觉遥测（Lowfi Vision Telemetry）
4. 命令唤醒（Command Wake）
5. 富视频会话（Rich Video Session）
6. 显示 / AR 会话（Display / AR Session）
7. 调试 / OTA（Debug / OTA）

## 必需 Session 元数据

- mode
- 唤醒源
- start/stop 单调时间戳
- A53/Linux 唤醒时间
- 可用时记录 MCU/M4 唤醒时间
- Wi-Fi 活跃时间
- 低功耗无线电 airtime
- 显示开启时间
- 摄像头活跃时间
- 发送/接收包数
- 生成的遥测帧数
- 可用时记录电源轨能量样本

## 派生指标

- 每个遥测帧的能耗
- 每个无线包的能耗
- 命令 ACK 延迟
- heartbeat 抖动
- 视频启动延迟
- 帧丢失或包丢失

## Adapter 边界

电源轨 monitor、fuel gauge、PMIC 状态和热传感器应通过 `PowerAdapter` 或 `SensorAdapter` 暴露，不应在核心 agent loop 里直接读取。
