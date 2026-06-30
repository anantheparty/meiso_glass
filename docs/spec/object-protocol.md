# 对象协议规范

本页定义 Meiso Object Protocol V0.1。它位于 Runtime Encoding 内，负责 Host 和 Device Runtime 之间的对象、接口、opcode、参数和异步事件。

Core Wire 只看到 `runtime_data` payload bytes。Object Protocol 才知道 feature、scene、HUD、sensor、asset、telemetry。

## 1. 设计立场

Object Protocol 借鉴 Wayland 的 object/interface/opcode 模型，但不复制 Wayland 的显示语义。

V0.1 边界：

- Host 拥有 desired state。
- Device 拥有 runtime state。
- Request/event 都是异步消息。
- Transport ack 不等于 request accepted。
- Object ID 是紧凑整数，不是 string。
- Interface/version 是 object binding 属性，不得在每条 message 中重复携带。
- Opcode、direction、new_id、destructor、idempotency、args schema 必须来自 IDL/codegen。
- Per-message correlation key 不是通用字段；如果某个 opcode 需要幂等或关联字段，应由该 opcode 的 args schema 定义。

## 2. Runtime Payload 形状

Runtime Encoding `meiso_object_binary_v1` 是一串 object message：

```text
object_message | object_message | ...
```

每个 object message：

```text
object_header[8] | args[args_len]
```

| Offset | Size | Field | Type | Rule |
|---:|---:|---|---|---|
| 0 | 4 | `object_id` | uint32 | dispatch target |
| 4 | 2 | `opcode` | uint16 | bound interface 内的 request/event opcode |
| 6 | 2 | `args_len` | uint16 | args byte count |

`message_len = 8 + args_len`。

Header 只有 8 bytes 的原因：

- `object_id` 映射到 live object record。
- Live object record 已保存 interface id 和 negotiated version。
- Direction 和 opcode validity 由 bound interface table 生成。
- Message serial 不是通用需求；可靠投递和重复包统计属于 Link Profile，业务幂等属于 opcode args。

V0.1 没有 per-message object flags。Destructor、new_id、snapshot、idempotent、latest-state 都是 opcode schema 属性，不是 wire flag。

## 3. Object ID 分配

| Range | Owner |
|---:|---|
| `0x00000000` | reserved null |
| `0x00000001` | `meiso_registry` |
| `0x00000002..0x7FFFFFFF` | Host-created objects |
| `0x80000000..0xFFFFFFFE` | Device-created objects |
| `0xFFFFFFFF` | reserved invalid |

规则：

- Sender 只能从自己拥有的范围分配 ID。
- Runtime bootstrap 后，`object_id=1` 必须为 live。
- 只有 IDL 声明了 `new_id` 的 opcode 才能创建新对象。
- Receiver 必须拒绝 unknown object、wrong opcode、unsupported version、wrong direction、duplicate live ID 或 reserved ID。
- Session reset 会销毁 transient objects 和 proxies。

## 4. Registry

`object_id=1` 是 `meiso_registry`。

| Opcode | Direction | Name | Args |
|---:|---|---|---|
| `0` | Device to Host | `global` | `name_id`, `interface_id`, `version_min`, `version_max`, `capability_bits` |
| `1` | Device to Host | `global_remove` | `name_id` |
| `2` | Host to Device | `bind` | `name_id`, `interface_id`, `interface_version`, `new_object_id` |
| `3` | Host to Device | `sync` | `sync_id` |
| `4` | Device to Host | `done` | `sync_id`, `registry_revision` |

Interface name 只存在于 IDL、文档和 debug metadata 中，不得在每条 runtime message 中携带。

## 5. 初始接口

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

业务消息属于 Object Protocol，不属于 Core Wire：

| 旧概念 | Object Protocol 归属 |
|---|---|
| `feature_request` | `meiso_feature_manager.request_lease` |
| `scene_snapshot` | `meiso_scene.commit` 或 `meiso_scene.runtime_snapshot` |
| `hud_update` | `meiso_app_hud.set_*` 加 `commit` |
| `sensor_sample` | `meiso_sensor_stream.sample` |
| `asset_chunk` | `meiso_asset_catalog.chunk` |

## 6. Desired State 与 Runtime State

Host-owned desired state：

| Area | Host Owns |
|---|---|
| feature | requested feature lease intent and idempotency key |
| scene | desired entity graph, asset refs, display intent |
| app HUD | desired app HUD elements only |
| sensor | subscription request |
| asset | source catalog and chunks |

Device-owned runtime state：

| Area | Device Owns |
|---|---|
| feature lease | accepted/degraded/rejected/revoked state |
| renderer | renderable scene replica and frame scheduling |
| HUD | final composition, System HUD and safety overlays |
| sensors | hardware adapters, sampling and privacy policy |
| power/thermal | forced downgrade and emergency stop |
| assets | cache state, validation and placeholder behavior |

Host request 只表示 desired state 已提交，不表示 Device 硬件状态已经改变。

## 7. Commit 纪律

Object Protocol 不定义通用 commit payload。Commit 是需要原子 desired-state 变更的接口使用的 opcode 模式。

每个 committing interface 的 IDL 必须定义：

- 哪个 object 拥有 desired state。
- commit 是 full snapshot、delta，还是两者都支持。
- version 字段宽度和单调规则。
- stale base version 是被拒绝还是可被 supersede。
- 是否包含 `valid_until_ns`。
- 结果事件是 `commit_result`、`runtime_snapshot`，还是 domain-specific event。

通用规则：

- Commit 在一个 object commit domain 内是原子的。
- Core/profile ack 只表示 bytes 到达，不表示 desired state 已接受。
- `commit_result` 表示 Device 已根据 capability、policy 和 resource limit 验证 desired state。
- 只有当 interface IDL 将 domain 标记为 latest-state 时，新 desired version 才能 supersede 尚未应用的旧 desired version。

## 8. Object Error

Object-level error 使用 `meiso_object.error` event。它不是 Core Wire parse error。

Error fields 由 IDL 编码，但 V0.1 的语义字段是：

| Field | Meaning |
|---|---|
| `error_code` | stable numeric code |
| `failed_object_id` | target object |
| `failed_opcode` | opcode involved |
| `severity` | `warning`, `recoverable`, `fatal_object`, `fatal_session` |
| `retryable` | bool |
| `details` | typed binary detail from IDL |

初始 error codes：

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

## 9. 生命周期

| State | Meaning |
|---|---|
| `Reserved` | ID 还不是 live |
| `Live` | receiver 接受该 object 的 message |
| `Destroying` | destructor 已接受；只允许 lifecycle/error event |
| `Dead` | 该 ID 在当前 session 中无效 |

生命周期转换：

```text
Reserved -> Live by valid new_id or bind
Live -> Destroying by destructor opcode
Destroying -> Dead after release observed
Live -> Dead on fatal_session or reset
```

## 10. IDL 与 Codegen

Meiso Object Protocol 在 public implementation 锁定前必须由 IDL 生成。

Codegen 输出：

- Device 侧 C header、encoder、decoder 和 dispatch table。
- Host 侧 Rust typed proxy、event enum 和 version gate。
- 测试、mock 和 CLI 使用的 Python binding。
- Markdown 表格。
- Binary golden vector。
- Bootstrap diagnostics 使用的 schema hash。

IDL 规则：

- interface ID 是稳定 public number。
- 同一 interface version 内 opcode 只能 append-only。
- 不兼容 args 需要新 opcode 或新 interface version。
- opcode schema 声明 direction、destructor、new_id、idempotency、latest-state 和 arg layout。
- 生成代码必须在 handler dispatch 前验证 object liveness、direction、version、opcode 和 args length。
- string debug name 不得成为 wire compatibility 的必要条件。
