# Hardware Validation

硬件验证不是 SDK contract。硬件事实只有在影响 Host/Edge API、Meiso Protocol、feature lease、logical channel、render profile 或 power policy 时才进入 bible。

V0.1 允许保留 reference platform profile，但核心 SDK 不绑定具体板卡。

## 记录原则

- 板卡、驱动、链路、传感器和功耗数据写成 validation evidence。
- 通过 adapter 或 profile 暴露硬件差异。
- 不把 BSP 命令、串口路径、平台专用 pipeline 写进 public API。
- 如果某个硬件能力不可验证，状态必须是 unknown 或 rejected，不能伪装成 supported。

## 当前优先级

1. Edge runtime 能在通用 Linux 上跑 mock。
2. Host SDK 能生成 FeatureRequest、SceneSnapshot、HudUpdate、SensorSubscription。
3. UDP reference path 只作为开发路径。
4. 真实硬件接入时先补 profile 和 adapter，再补测量证据。
