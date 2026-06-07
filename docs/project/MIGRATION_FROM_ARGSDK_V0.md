# 从 arglasses_dual_device_sdk_v0 迁移

已审阅 `arglasses_dual_device_sdk_v0` 骨架，并把有用内容部分迁移到本仓库。

## 已迁移

- message dataclass 和 ACK/error helper
- UDP JSON transport
- endpoint 和 SDC agent loop
- health probe
- GStreamer 测试源发送器和 H.264/RTP 接收 helper
- 首次运行、架构、协议、日志说明
- 通用 probe 脚本和视频冒烟脚本

## 已调整

- 包名：`arglass_sdk` 改为 `meiso_glass`
- 协议 magic：`ARGSDK` 改为 `MEISOGLASS`
- 角色命名：保留开放 `sdc` 角色；Orin 只是其中一个 SDC profile
- 命令：`arglass-*` 改为 `meiso-*`
- 默认配置：平台中立示例放在 `configs/examples/`
- 板卡 profile：i.MX8MM endpoint 和 Orin SDC 移到 `configs/platforms/`
- service 模板：重命名并指向 `/opt/meiso_glass`

## 未作为默认迁移

- i.MX8MM 专用 setup 脚本
- Orin 专用 setup 脚本
- 指向 `/opt/arglasses_dual_device_sdk_v0` 的 systemd 文件
- Python 字节码缓存

板卡专用知识后续应通过 adapter 或 platform profile 回到项目里，而不是进入 SDK 核心 import 或默认示例。
