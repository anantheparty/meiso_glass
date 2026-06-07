# 兼容性检查清单

在标记一个新平台 profile 或 adapter 可用之前，先按这份清单检查。

## 协议

- 能发出带版本号的消息。
- 收到未知消息类型时不会崩溃。
- 延迟测量使用单调时间戳。
- 命令会产生 ACK 或 error。

## 控制面

- endpoint 的 heartbeat 能到达 SDC。
- `ping` 返回 ACK。
- `health` 返回结构化健康数据。
- `start_video` 和 `stop_video` 返回确定性的状态。

## 视频面

- 视频源可以替换，不需要修改 agent 逻辑。
- 编码器可以通过配置或 adapter 替换。
- 接收端可以显示或录制视频流。

## 遥测面

- JSON 开发事件可以被直接检查。
- 二进制包实现会校验长度、版本和 CRC。
- 包序号和时间戳来源已经文档化。

## Adapter

- 依赖硬件的行为都在 adapter 后面。
- 每个真实 adapter 都有对应 mock。
- adapter 状态会报告可用性和运行状态。

## 功耗

- 平台能报告 power mode。
- session 日志包含开始和结束时间戳。
- 硬件支持时，日志包含电源轨或电池指标。

## 文档

- 平台 profile 位于 `configs/platforms/`。
- 安装和 bring-up 特殊点写在文档里，不写进 SDK 核心代码。
- 不支持的功能要明确返回状态或错误，不能静默 fallback。
