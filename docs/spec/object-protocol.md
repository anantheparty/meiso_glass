# Object Protocol Spec

本页定义 Meiso Object Protocol V0.1。它位于 Runtime Encoding 内，负责 Host 和 Device Runtime 的对象、接口、opcode、参数和异步事件。

Core Wire 只看到 `frame_kind=data` 和 payload bytes。Object Protocol 才知道 feature、scene、HUD、sensor、asset、telemetry。

## 1. Design Stance

Object Protocol 借鉴 Wayland 的 object/interface/opcode 模型，但不复制 Wayland 的显示语义。

V0.1 边界：

- Host owns desired state.
- Device owns runtime state.
- Request/event 都是异步消息。
- Transport ack 不等于 request accepted。
- Object ID 是紧凑整数，不是 string。
- Interface/version 是 object binding 属性，MUST NOT be repeated in every message。
- Opcode、direction、new_id、destructor、idempotency、args schema MUST come from IDL/codegen。

## 2. Runtime Payload Shape

Core Wire `data` payload uses [Runtime Protocol](./runtime-protocol.md) `meiso_object_binary_v1`.

```text
object_message | object_message | ...
```

Each object message:

```text
object_header[12] | args[args_len]
```

| Offset | Size | Field | Type | Rule |
|---:|---:|---|---|---|
| 0 | 4 | `object_id` | uint32 | dispatch target |
| 4 | 2 | `opcode` | uint16 | request/event opcode within bound interface |
| 6 | 2 | `args_len` | uint16 | byte count of args |
| 8 | 4 | `serial` | uint32 | sender-local object-message serial |

`message_len = 12 + args_len`.

Why the header does not carry `interface_id` or `interface_version`:

- `object_id` maps to a live object record.
- The live object record already stores interface id and negotiated version.
- Repeating interface/version costs 4 bytes per message and creates mismatch states.
- Direction and opcode validity are generated from the bound interface table.

No per-message object flags exist in V0.1. Destructor、new_id、snapshot、idempotent are opcode schema properties, not wire flags.

## 3. Object ID Allocation

| Range | Owner |
|---:|---|
| `0x00000000` | reserved null |
| `0x00000001` | `meiso_registry` |
| `0x00000002..0x7FFFFFFF` | Host-created objects |
| `0x80000000..0xFFFFFFFE` | Device-created objects |
| `0xFFFFFFFF` | reserved invalid |

Rules:

- Sender MUST only allocate IDs from its owned range.
- `object_id=1` is live after runtime bootstrap.
- A new object can only be created by an opcode whose IDL declares `new_id`.
- Receiver MUST reject unknown object, wrong opcode, unsupported version, wrong direction, duplicate live ID or reserved ID.
- Session reset destroys transient objects and proxies.

## 4. Registry

`object_id=1` is `meiso_registry`.

| Opcode | Direction | Name | Args |
|---:|---|---|---|
| `0` | Device to Host | `global` | `name_id`, `interface_id`, `version_min`, `version_max`, `capability_bits` |
| `1` | Device to Host | `global_remove` | `name_id` |
| `2` | Host to Device | `bind` | `name_id`, `interface_id`, `interface_version`, `new_object_id` |
| `3` | Host to Device | `sync` | `sync_id` |
| `4` | Device to Host | `done` | `sync_id`, `registry_revision` |

Interface names exist in IDL/docs/debug metadata. They MUST NOT be carried in every runtime message.

## 5. Initial Interfaces

| Interface ID | Interface | Owner Boundary |
|---:|---|---|
| `0x0001` | `meiso_registry` | Device advertises globals; Host binds objects |
| `0x0002` | `meiso_object` | common object error/lifecycle events |
| `0x0010` | `meiso_session` | runtime session status and close |
| `0x0020` | `meiso_capability` | Device capability profile snapshots |
| `0x0100` | `meiso_feature_manager` | Host requests feature leases |
| `0x0110` | `meiso_feature_lease` | Device owns accepted/degraded/revoked lease state |
| `0x0200` | `meiso_scene` | Host owns desired scene state |
| `0x0210` | `meiso_app_hud` | Host owns desired app HUD state |
| `0x0300` | `meiso_sensor_manager` | Host requests sensor subscriptions |
| `0x0310` | `meiso_sensor_stream` | Device owns sensor sample stream |
| `0x0400` | `meiso_asset_catalog` | Host owns asset catalog/source |
| `0x0410` | `meiso_asset_cache` | Device owns cache state and misses |
| `0x0500` | `meiso_telemetry` | Device reports runtime/health/fault state |

Business messages live here, not in Core Wire:

| Old Concept | Object Protocol Home |
|---|---|
| `feature_request` | `meiso_feature_manager.request_lease` |
| `scene_snapshot` | `meiso_scene.commit` or `meiso_scene.runtime_snapshot` |
| `hud_update` | `meiso_app_hud.set_*` plus `commit` |
| `sensor_sample` | `meiso_sensor_stream.sample` |
| `asset_chunk` | `meiso_asset_catalog.chunk` |

## 6. Desired State And Runtime State

Host-owned desired state:

| Area | Host Owns |
|---|---|
| feature | requested feature lease intent and idempotency key |
| scene | desired entity graph, asset refs, display intent |
| app HUD | desired app HUD elements only |
| sensor | subscription request |
| asset | source catalog and chunks |

Device-owned runtime state:

| Area | Device Owns |
|---|---|
| feature lease | accepted/degraded/rejected/revoked state |
| renderer | renderable scene replica and frame scheduling |
| HUD | final composition, System HUD and safety overlays |
| sensors | hardware adapters, sampling and privacy policy |
| power/thermal | forced downgrade and emergency stop |
| assets | cache state, validation and placeholder behavior |

Host request means desired state was submitted. It does not mean Device hardware state has changed.

## 7. Commit Discipline

Object Protocol does not define a single universal commit payload. Commit is an opcode pattern used by state domains that need atomic desired-state changes.

Each committing interface IDL MUST define:

- Which object owns the desired state.
- Whether commits are full snapshot, delta, or both.
- The version field width and monotonic rule.
- Whether stale base versions are rejected or superseded.
- Whether `valid_until_ns` is present.
- Whether the result is `commit_result`, `runtime_snapshot`, or domain-specific event.

Common rules:

- A commit is atomic within one object commit domain.
- Core ack means frame arrived and passed Core Wire validation.
- `commit_result` means Device validated desired state against capability, policy and resource limits.
- `runtime_snapshot` means Device observed or applied runtime state.
- Newer desired versions MAY supersede older unapplied desired versions only when the interface IDL marks the domain as latest-state.

## 8. Object Error

Object-level errors use `meiso_object.error` event. They are not Core Wire parse errors.

Error fields are encoded by IDL, but V0.1 semantic fields are:

| Field | Meaning |
|---|---|
| `error_code` | stable numeric code |
| `failed_object_id` | target object |
| `failed_opcode` | opcode involved |
| `failed_serial` | original sender serial |
| `severity` | `warning`, `recoverable`, `fatal_object`, `fatal_session` |
| `retryable` | bool |
| `details` | typed binary detail from IDL |

Initial error codes:

```text
unknown_object
unsupported_interface_version
unknown_opcode
invalid_direction
invalid_args
invalid_state
not_owner
permission_denied
policy_rejected
resource_exhausted
stale_commit
conflict
object_gone
timeout
internal_error
```

## 9. Lifecycle

| State | Meaning |
|---|---|
| `Reserved` | ID is not live yet |
| `Live` | receiver accepts messages for this object |
| `Destroying` | destructor accepted; only lifecycle/error events are valid |
| `Dead` | ID is invalid in this session |

Lifecycle transition:

```text
Reserved -> Live by valid new_id or bind
Live -> Destroying by destructor opcode
Destroying -> Dead after release observed
Live -> Dead on fatal_session or reset
```

## 10. IDL And Codegen

Meiso Object Protocol MUST be generated from IDL before public implementation locks.

Codegen outputs:

- C headers, encoder, decoder and dispatch tables for Device.
- Rust typed proxies, event enums and version gates for Host.
- Python bindings for tests, mocks and CLI.
- Markdown tables.
- Binary golden vectors.
- Schema hash for bootstrap diagnostics.

IDL rules:

- interface IDs are stable public numbers.
- opcodes are append-only within an interface version.
- incompatible args require a new opcode or new interface version.
- opcode schema declares direction, destructor, new_id, idempotency, latest-state and arg layout.
- generated code MUST validate object liveness, direction, version, opcode and args length before handler dispatch.
- string debug names MUST NOT be required for wire compatibility.
