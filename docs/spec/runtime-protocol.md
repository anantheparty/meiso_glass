# Runtime Protocol Spec

本页定义 Runtime Encoding。Core Wire 不选择 JSON、CBOR、Protobuf 或 FlatBuffers。V0.1 只有一个 canonical runtime encoding。

## 1. Canonical Encoding

V0.1 canonical runtime codec is:

```text
meiso_object_binary_v1
```

Rules:

- Runtime records MUST use `meiso_object_binary_v1` after bootstrap unless a later session profile explicitly negotiates another codec.
- Debug JSON MAY exist as Host-side tooling adapter, log export or test fixture format.
- Debug JSON MUST NOT be treated as peer interoperability format.
- Runtime encoding version is session scoped. It is not carried in every record or Core Wire frame.

## 2. Payload Container

`meiso_object_binary_v1` is a sequence of object messages:

```text
object_message | object_message | ...
```

Each object message uses the 8-byte header defined in [Object Protocol](./object-protocol.md):

```text
object_id uint32
opcode    uint16
args_len  uint16
args      bytes[args_len]
```

Receiver MUST stop at exact payload end. Trailing bytes are a parse error.

## 3. Compact Runtime IDs

V0.1 uses compact numeric IDs on wire:

| ID | Width | Owner / Scope |
|---|---:|---|
| `object_id` | uint32 | Object Protocol dispatch id |
| `session_id` | uint64 | runtime session instance |
| `lease_id` | uint32 | Device-created feature lease id |
| `subscription_id` | uint32 | sensor subscription id |
| `entity_id` | uint32 | scene entity id within a scene object |
| `asset_alias` | uint64 | session-local alias for asset content hash |
| `trace_id` | uint64 | diagnostics only |

String IDs can exist in authoring tools, logs and docs. They do not cross the runtime wire except as explicit debug payload.

## 4. Asset Identity

Assets need both compact wire identity and collision-safe content identity:

- Host catalog assigns `asset_alias uint64` for efficient runtime references.
- Catalog entry maps alias to content hash, size, media type and render profile requirements.
- Device MUST validate alias against catalog before accepting asset-dependent commit.
- If alias maps to missing or mismatched content hash, Device emits `asset_missing` or `asset_mismatch`.
- Content hash is the long-term identity; alias is session-local acceleration.

## 5. Runtime Bootstrap

Bootstrap establishes:

- runtime encoding name and version.
- object ID ranges.
- schema hash.
- supported interface versions.
- session id.
- link profile currently in use.
- capability profile snapshot id.

Bootstrap MAY use a profile-specific prelude or `meiso_registry` messages. Once bootstrap completes, normal runtime messages MUST use object protocol dispatch.

## 6. Versioning

- Runtime encoding version is session scoped.
- Interface version is object scoped and stored in the live object binding table.
- Opcode compatibility is interface scoped.
- Capability profile revision is Device scoped.
- Link profile revision is transport scoped.

These versions MUST NOT be collapsed into one `protocolVersion` string.

## 7. Runtime Parse Errors

Runtime parse errors are runtime/object errors, not Core Wire errors, once Core Wire or profile-level record validation succeeds.

| Error | Meaning |
|---|---|
| `bad_object_message_len` | payload ended inside an object message |
| `reserved_object_id` | object id is null or reserved invalid |
| `unknown_object` | object id not live |
| `unsupported_interface_version` | bound object version not supported by receiver implementation |
| `unknown_opcode` | opcode not valid for the object's bound interface version |
| `invalid_direction` | sender role cannot send this opcode |
| `invalid_args` | typed args fail schema validation |

## 8. Debug Representations

Tooling MAY expose a JSON view such as:

```json
{
  "object": "meiso_scene#42",
  "opcode": "commit",
  "desiredVersion": 7
}
```

This view is for humans and tests. It is not the canonical transport payload.
