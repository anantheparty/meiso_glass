# 消息协议 V0

V0 传输使用 UDP JSON。它刻意保持简单、可读、方便检查；它不是最终低功耗无线电包格式。

## 消息头

```json
{
  "protocol_magic": "MEISOGLASS",
  "protocol_version": 1,
  "msg_id": "uuid",
  "msg_type": "heartbeat|health|command|ack|error|event|time_sync",
  "src_role": "endpoint|sdc|host",
  "dst_role": "endpoint|sdc|host|null",
  "src_id": "device-id",
  "seq": 1,
  "realtime_ns": 123,
  "monotonic_ns": 456,
  "payload": {}
}
```

`realtime_ns` 用于跨日志的人类时间关联。`monotonic_ns` 用于延迟区间测量。

## 命令

V0 命令工具会发送直接带类型消息。早期开发阶段，endpoint 也接受 payload 里的兼容旧版 `command` 字段。

```json
{"command": "ping"}
{"command": "health"}
{"command": "start_video", "video_host": "127.0.0.1", "video_port": 5000}
{"command": "stop_video"}
{"command": "start_lowfi"}
{"command": "stop_lowfi"}
```

## 必需消息类型

- `heartbeat`
- `ping`
- `ack`
- `error`
- `health`
- `start_video`
- `stop_video`
- `start_lowfi`
- `stop_lowfi`
- `power_state`
- `sensor_event`
- `telemetry_packet`
- `display_session`
- `firmware_status`
- `log_event`
- `crash_report`

命令返回 `ack` 或 `error`：

```json
{
  "ok": true,
  "ack_msg_id": "uuid",
  "ack_msg_type": "command"
}
```

## 未来二进制遥测

低功耗无线电遥测不应使用 JSON。建议从固定包形状开始：

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

候选 payload 家族：

- IMU 样本
- 低功耗视觉 tile/ROI
- 眼动稀疏 tuple
- 音频唤醒事件
- 热状态样本
- 电池样本
- 电源轨功耗样本
- 无线链路统计
