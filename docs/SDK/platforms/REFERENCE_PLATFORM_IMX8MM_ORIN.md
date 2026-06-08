# 参考平台：i.MX8MM Endpoint + Orin SDC

这是第一个参考平台，不是 SDK 约束。

## Endpoint

- NXP i.MX8M Mini 开发板
- A53 上运行嵌入式 Linux
- 后续可能加入 M4 固件
- 未来模块可能包括 HM0360、HM01B0、LR2021、GW1NZ、IMU、麦克风唤醒、电源 monitor

profile：

```text
configs/platforms/endpoint.imx8mm.yaml
```

## SDC

- NVIDIA Jetson Orin Nano SBC
- Jetson Linux / Ubuntu
- 接收 H.264/RTP/UDP 视频
- 接收 heartbeat、health 和 telemetry
- 向 endpoint 发送命令

profile：

```text
configs/platforms/sdc.orin.yaml
```

## 第一条链路

- 先用 Ethernet
- 后续切 Wi-Fi
- UDP JSON 控制面
- H.264/RTP/UDP 视频冒烟测试
- 先用 JSON telemetry，后续再做 binary telemetry

## 调试启动边界

这个参考平台可能需要板卡专用 adapter、BSP 设置、设备树修改或 GStreamer 编码器元素名。这些细节不能进入 SDK 核心协议或默认通用示例。
