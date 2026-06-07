# Protocol Bible

本文件定义控制面和 telemetry 事件的协议规则。

## Envelope

所有 control message 必须有 envelope。V0 JSON envelope 至少包含：

```json
{
  "magic": "MEISOGLASS",
  "version": 1,
  "type": "heartbeat",
  "src_role": "endpoint",
  "src_id": "endpoint-001",
  "dst_role": "sdc",
  "dst_id": null,
  "seq": 1,
  "timestamp_ns": 123456789,
  "payload": {}
}
```

后续应补充但不能破坏旧 client 的字段：

- `trace_id`
- `session_id`
- `capabilities`
- `extensions`
- `schema`

## 兼容策略

- 新增 optional field 通常兼容。
- 删除 field、改名、改类型、改默认语义通常不兼容。
- unknown field 必须被保留或忽略，不得导致旧 client 崩溃。
- unknown message type 必须返回 `error`，不得静默执行。
- enum value 不得复用。
- binary telemetry 的 header 字节序、magic、version、CRC 必须有 golden vector。

## Error Model

错误 payload 必须使用英文机器字段：

```json
{
  "code": "unknown_command",
  "message": "unknown command",
  "retryable": false,
  "details": {}
}
```

`message` 可以给开发者阅读，但仍必须是英文 wire content。中文解释写在 docs，不写进传输 payload。

## State Machine

控制面命令必须定义：

- accepted state
- idempotency
- timeout
- cancel behavior
- ACK payload
- error payload
- observability fields

`start_video`、`stop_video`、`start_lowfi`、`stop_lowfi` 等 session command 必须记录 `session_id`、`seq`、`timestamp_ns` 和 power/latency metadata。
