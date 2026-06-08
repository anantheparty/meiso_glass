# Observability Bible

本文件定义日志、trace、metrics、replay 的最低要求。

## Structured Logs

日志字段必须使用英文 machine key：

```json
{
  "event": "command_received",
  "role": "endpoint",
  "device_id": "endpoint-001",
  "session_id": "session-001",
  "trace_id": "trace-001",
  "seq": 42,
  "timestamp_ns": 123456789
}
```

中文解释只出现在文档，不进入 log field 或 payload field。

## Trace

每个跨设备 session 都应有 `trace_id`。如果经过 HTTP 或兼容网关，应能映射到 W3C Trace Context 的 `traceparent` 概念。

## Metrics

metrics name 使用英文 snake_case：

- `heartbeat_latency_ms`
- `control_packet_loss_ratio`
- `video_start_latency_ms`
- `endpoint_awake_time_ms`
- `radio_airtime_ms`
- `energy_per_telemetry_frame_uj`

## Replay

SDK 应能记录：

- control message stream
- telemetry event stream
- session lifecycle
- error events
- power and latency metadata

replay 文件必须脱离真实硬件可运行，用于 regression test 和 bug report。
