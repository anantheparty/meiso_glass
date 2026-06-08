# 平台移植指南

移植一个平台，指的是在保持协议契约不变的前提下，实现 adapter 和配置 profile。

## 1. 给设备分类

- Endpoint：低功耗眼镜侧设备
- SDC：口袋/主机侧空间数据计算设备
- Host：开发工作站或测试工具

## 2. 创建平台 Profile

profile 配置放在 `configs/platforms/`。

最小字段：

```yaml
device:
  id: my-endpoint-001
  role: endpoint
  platform: my-platform
network:
  bind_host: 0.0.0.0
logging:
  dir: ./logs
```

## 3. 实现 Adapter

先从 mock 开始，再一次替换一个真实 adapter：

- camera
- 视频编码器
- radio
- power
- sensor
- audio
- display
- M4 或 MCU bridge
- FPGA bridge

## 4. 跑兼容性检查

在宣称一个平台已支持之前，先使用 `docs/SDK/guides/COMPATIBILITY_CHECKLIST.md`。

## 5. 不要把参考平台代码写进核心

参考平台说明放在 `docs/SDK/platforms/REFERENCE_PLATFORM_IMX8MM_ORIN.md` 或 adapter 模块里。核心协议、消息、遥测包和运行时 loop 必须保持平台中立。
