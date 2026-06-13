# Meiso Glass

Meiso Glass 是一个面向 AR 眼镜端侧设备和 SDC 设备的平台中立 SDK 骨架。

这个仓库刻意把开放 SDK 契约和任何单一原型平台分开。i.MX 8M Mini、Jetson Orin Nano、LR2021、HM0360 等器件可以作为平台配置 profile 或 adapter 出现，但 SDK 核心应当能被其它 Linux SBC、自定义端侧板、模拟设备以及未来的视频/无线传输方案复用。

## 当前范围

- 控制面：基于 UDP JSON 的 `heartbeat`、`health`、命令、ACK、错误和事件消息。
- 视频冒烟测试：基于 GStreamer 的 H.264/RTP/UDP，默认使用 `videotestsrc`。
- 健康探针：采集 OS、网络、存储、视频设备以及可选平台提示信息。
- 配置 profile：优先提供通用 Linux 示例；板卡专用配置放在 `configs/platforms/`。
- 运行时角色：`endpoint` 表示眼镜侧设备，`sdc` 表示口袋/主机侧空间数据计算设备，`host` 表示开发工具。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 本地冒烟测试

终端 A：

```bash
meiso-sdc --config configs/examples/sdc.generic.yaml
```

终端 B：

```bash
meiso-endpoint --config configs/examples/endpoint.generic.yaml
```

终端 C：

```bash
meiso-send --host 127.0.0.1 --port 42001 ping
meiso-send --host 127.0.0.1 --port 42001 health
```

## 本地 Wiki

本仓库使用 VitePress 维护 `docs/` 下的 Web wiki。它只用于本地预览和静态构建验证，不包含部署配置。

```bash
npm install
npm run docs:dev
npm run docs:build
```

## 项目结构

```text
src/meiso_glass/        SDK 包
configs/examples/       平台中立示例配置
configs/platforms/      板卡专用上电调试 profile
scripts/                可移植的开发/探针/视频冒烟脚本
docs/                   Web wiki、origin 原始文档、SDK 三份核心设计文档与真机验证计划
systemd/                通用 service 模板
tests/                  聚焦 SDK 契约的测试
```

应用层代码可以先使用 `meiso_glass.api.EndpointClient` 和 `meiso_glass.api.SDCRegistry`，不必直接手写 UDP 消息。

## 文档

- [文档索引](docs/README.md)
- [SDK 文档索引](docs/SDK/README.md)
- [SDK 设计概览与核心设计图](docs/SDK/bible/SDK_DESIGN_OVERVIEW.md)
- [SDK 子系统详细设计案](docs/SDK/bible/SDK_SUBSYSTEM_DESIGN.md)
- [SDK 开发计划与当前进度](docs/SDK/bible/SDK_DEVELOPMENT_PLAN.md)
- [真机验证计划](docs/validation/README.md)

## 硬件上下文

当前实验室候选硬件是 bring-up 目标，不是 SDK 约束：

- endpoint 上电调试：i.MX 8M Mini 开发板
- 低功耗端侧外设：HM0360、GW1NZ-2、LR2021、nRF54L15、ICM-45686、T5838
- SDC 上电调试：Jetson Orin Nano / Orin NX 类计算设备

SDK 核心应当保持在协议、传输、视频、遥测和能力抽象之后，让这些硬件后续可以被开放生态里的替代方案替换。
