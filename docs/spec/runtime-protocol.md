# Runtime 协议规范

本页定义 Runtime Encoding。Core Wire 不选择 JSON、CBOR、Protobuf 或 FlatBuffers。V0.1 只有一个 canonical runtime encoding。

## 1. Canonical Encoding

V0.1 canonical runtime codec 是：

```text
meiso_object_binary_v1
```

规则：

- Bootstrap 完成后，runtime record 必须使用 `meiso_object_binary_v1`，除非后续 session profile 明确协商了其它 codec。
- Debug JSON 可以作为 Host-side 工具 adapter、日志导出或测试 fixture 格式存在。
- Debug JSON 不得被当作 peer interoperability 格式。
- Runtime encoding version 是 session scoped，不在每条 record 或 Core Wire frame 中携带。

## 2. Payload Container

`meiso_object_binary_v1` 是一串 object message：

```text
object_message | object_message | ...
```

每个 object message 使用 [对象协议](./object-protocol.md) 中定义的 8-byte header：

```text
object_id uint32
opcode    uint16
args_len  uint16
args      bytes[args_len]
```

Receiver 必须刚好在 payload 末尾停止。任何 trailing bytes 都是 parse error。

## 3. 紧凑 Runtime ID

V0.1 在 wire 上使用紧凑 numeric ID：

| ID | Width | Owner / Scope |
|---|---:|---|
| `object_id` | uint32 | Object Protocol dispatch id |
| `session_id` | uint64 | runtime session instance |
| `lease_id` | uint32 | Device-created feature lease id |
| `subscription_id` | uint32 | sensor subscription id |
| `entity_id` | uint32 | scene entity id within a scene object |
| `asset_alias` | uint64 | session-local alias for asset content hash |
| `trace_id` | uint64 | diagnostics only |

String ID 可以存在于 authoring tools、logs 和 docs 中。除显式 debug payload 外，它们不跨 runtime wire。

## 4. Asset Identity

资产需要紧凑 wire identity 和 collision-safe content identity：

- Host catalog 分配 `asset_alias uint64`，用于高效 runtime 引用。
- Catalog entry 将 alias 映射到 content hash、size、media type 和 render profile requirements。
- Device 接受依赖资产的 commit 前，必须根据 catalog 验证 alias。
- 如果 alias 映射到缺失或 hash 不匹配的内容，Device 发出 `asset_missing` 或 `asset_mismatch`。
- Content hash 是长期身份；alias 是 session-local 加速身份。

## 5. Runtime Bootstrap

Bootstrap 建立：

- runtime encoding name 和 version。
- object ID ranges。
- schema hash。
- supported interface versions。
- session id。
- 当前 link profile。
- capability profile snapshot id。

Bootstrap 可以使用 profile-specific prelude 或 `meiso_registry` 消息。Bootstrap 完成后，普通 runtime message 必须使用 object protocol dispatch。

## 6. Versioning

- Runtime encoding version 是 session scoped。
- Interface version 是 object scoped，保存在 live object binding table 中。
- Opcode compatibility 是 interface scoped。
- Capability profile revision 是 Device scoped。
- Link profile revision 是 transport scoped。

这些 version 不得合并成一个 `protocolVersion` string。

## 7. Runtime Parse Errors

一旦 Core Wire 或 profile-level record validation 已经通过，runtime parse error 就是 runtime/object error，不是 Core Wire error。

| Error | Meaning |
|---|---|
| `bad_object_message_len` | payload 在 object message 中途结束 |
| `reserved_object_id` | object id 是 null 或 reserved invalid |
| `unknown_object` | object id 不是 live |
| `unsupported_interface_version` | bound object version 不被 receiver implementation 支持 |
| `unknown_opcode` | opcode 对该 object 的 bound interface version 无效 |
| `invalid_direction` | sender role 不能发送该 opcode |
| `invalid_args` | typed args 未通过 schema validation |

## 8. Debug 表示

Tooling 可以暴露 JSON view，例如：

```json
{
  "object": "meiso_scene#42",
  "opcode": "commit",
  "desiredVersion": 7
}
```

该 view 只用于人类阅读和测试，不是 canonical transport payload。
