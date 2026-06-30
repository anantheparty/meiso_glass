# Runtime Protocol Spec

本页定义 Core Wire payload 的 runtime contract。Core Wire 不选择 JSON、CBOR、Protobuf 或 FlatBuffers。V0.1 只定义一个 canonical runtime encoding。

## Canonical Encoding

V0.1 canonical runtime codec is:

```text
meiso_object_binary_v1
```

Rules:

- Core Wire `frame_kind=data` payload MUST be `meiso_object_binary_v1` unless a link/session profile explicitly negotiates a future codec.
- Debug JSON MAY exist as Host-side tooling adapter, log export or test fixture format.
- Debug JSON MUST NOT be treated as peer interoperability format.
- Runtime encoding version is negotiated during runtime bootstrap. It is not carried in every Core Wire frame.

## Payload Container

`meiso_object_binary_v1` payload is a sequence of object messages:

```text
object_message | object_message | ...
```

Each object message uses the header defined in [Object Protocol](./object-protocol.md). Receiver MUST stop at exact payload end. Trailing bytes are a parse error.

## Compact Runtime IDs

V0.1 uses compact numeric IDs on wire:

| ID | Width | Owner / Scope |
|---|---:|---|
| `object_id` | uint32 | Object Protocol dispatch id |
| `session_id` | uint64 | runtime session instance |
| `lease_id` | uint32 | Edge-created feature lease id |
| `subscription_id` | uint32 | sensor subscription id |
| `entity_id` | uint32 | scene entity id within a scene object |
| `asset_alias` | uint64 | session-local alias for asset content hash |
| `trace_id` | uint64 | diagnostics only |

String IDs can exist in authoring tools, logs and docs. They do not cross the runtime wire except as explicit debug payload.

## Asset Identity

Assets need both compact wire identity and collision-safe content identity:

- Host catalog assigns `asset_alias uint64` for efficient runtime references.
- Catalog entry maps alias to content hash, size, media type and render profile requirements.
- Edge MUST validate alias against catalog before accepting asset-dependent commit.
- If alias maps to missing or mismatched content hash, Edge emits `asset_missing` or `asset_mismatch`.
- Content hash is the long-term identity; alias is session-local acceleration.

## Runtime Bootstrap

Bootstrap establishes:

- runtime encoding name and version.
- object ID ranges.
- schema hash.
- supported interface versions.
- session id.
- link profile currently in use.
- capability profile snapshot id.

Bootstrap MAY use normal Core Wire `data` with `meiso_registry` messages, or a profile-specific prelude. Once bootstrap completes, normal runtime messages MUST use object protocol dispatch.

## Versioning

- Runtime encoding version is session scoped.
- Interface version is object scoped.
- Opcode compatibility is interface scoped.
- Capability profile revision is Edge scoped.
- Link profile revision is transport scoped.

These versions MUST NOT be collapsed into one `protocolVersion` string.

## Runtime Errors

Runtime parse errors are object/runtime errors, not Core Wire errors, once Core Wire validation succeeds.

| Error | Meaning |
|---|---|
| `bad_object_message_len` | payload ended inside an object message |
| `reserved_object_flag` | reserved object message flag set |
| `reserved_object_field` | reserved field non-zero |
| `unknown_object` | object id not live |
| `unknown_interface` | interface id not known in negotiated schema |
| `unsupported_interface_version` | object version not supported |
| `unknown_opcode` | opcode not valid for interface version |
| `invalid_direction` | sender role cannot send this opcode |
| `invalid_args` | typed args fail schema validation |

## Debug Representations

Tooling MAY expose a JSON view such as:

```json
{
  "object": "meiso_scene#42",
  "opcode": "commit",
  "desiredVersion": 7
}
```

This view is for humans and tests. It is not the canonical transport payload.
