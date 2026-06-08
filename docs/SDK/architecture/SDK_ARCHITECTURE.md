# SDK 架构

## 原则

Meiso Glass 不能锁死在某一个 endpoint SoC、某一个 SDC 模块、某一个摄像头或某一种无线电上。SDK 核心负责协议、时间、日志、命令和传输边界；硬件选择放在平台 profile 和 adapter 里。

## 运行时角色

```text
endpoint
  - heartbeat
  - 健康探针
  - 命令接收器
  - 可选视频 pipeline 启动器
  - 未来的 sensor、power、display、radio、FPGA adapter

sdc
  - heartbeat 接收器
  - 命令发送器
  - 视频接收/录制
  - 未来的融合、AI、world cache、dashboard、replay runtime

host
  - 开发 CLI 工具
  - record/replay/inspect 工具
  - 模拟器和测试 fixture
```

## SDK API 层

API 层应向 app 和 dashboard 暴露稳定方法。当前 V0 骨架先提供：

- `EndpointClient.ping()`
- `EndpointClient.health()`
- `EndpointClient.start_video()`
- `EndpointClient.stop_video()`
- `EndpointClient.start_lowfi()`
- `EndpointClient.stop_lowfi()`
- `EndpointClient.power_state()`
- `SDCRegistry.register_endpoint()`

未来 API 组应保持同样的 adapter-backed 形态：

- `camera.start()`
- `video.start_stream()`
- `telemetry.subscribe()`
- `power.get_state()`
- `endpoint.send_command()`
- `sdc.register_endpoint()`

项目可以使用 i.MX 8M Mini endpoint 和 Jetson Orin SDC profile 做上电调试，但这些名字不应出现在核心协议类型或默认配置里。

## 平面划分

控制面：

- V0 使用 `42000` 和 `42001` 端口上的 UDP JSON 消息
- 人类可读，bring-up 时方便检查
- 不是最终低功耗无线电遥测格式

视频面：

- V0 使用 `5000` 端口上的 RTP/H.264 over UDP
- 起步使用 `videotestsrc`
- 平台 profile 可以替换为 V4L2、CSI、硬件编码器或显示 sink

遥测面：

- V0 可以用 UDP JSON event 做开发
- 低功耗无线电遥测后续应变成紧凑二进制包，显式包含序号、时间戳、payload length 和 CRC

回放面：

- 记录 raw message、decoded event、health snapshot 和人工备注
- replay 应能在没有 live hardware 时驱动 SDC 侧算法

## 适配器规则

核心代码可以依赖：

- Python 标准库
- 协议 dataclass
- 通用 transport interface
- config 值

核心代码不应依赖：

- 某个具体板卡镜像
- 硬编码 Linux device node
- Jetson-only library
- 某个具体 i.MX encoder element
- 最终无线电包布局
