# Transport Payload Rules

本文件定义传输内容规则。

## 字符集

transport payload 使用英文 ASCII field name、type name、role name、error code、capability name。文本字段默认也使用英文，避免调试工具、低功耗链路和跨语言 SDK 因编码产生歧义。

## Envelope 先于 Payload

所有 message 都先解析 envelope，再进入 command handler。handler 不应从 payload 中猜测 role、version、seq。

## Error Code

错误码使用稳定英文 snake_case：

- `unknown_command`
- `unsupported_version`
- `invalid_payload`
- `adapter_unavailable`
- `timeout`
- `busy`

## Extensions

实验性扩展必须放入 `extensions` 或 adapter-specific namespace，不得直接污染 top-level envelope。

## Payload 示例

```json
{
  "command": "start_video",
  "video_host": "192.0.2.10",
  "video_port": 5000,
  "session_id": "session-001"
}
```
