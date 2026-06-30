# SDK Surface Spec

本页定义 Meiso SDK V0.1 的稳定 Host-facing surface。它刻意排除 wire、transport、runtime manager 和 AI registry 这类内部实现面。

## 1. Public Surface

| Surface | Direction | Purpose |
|---|---|---|
| `Session` | Host <-> Device | connect, close, query capability, receive events |
| `FeatureLease` | Host -> Device -> Host | request/release/revoke high-power or privileged capabilities |
| `Scene` | Host -> Device | commit desired 3D state by compact entities and asset refs |
| `Hud` | Host -> Device | commit App HUD desired state |
| `SensorStream` | Device -> Host | deliver samples or processed results after lease approval |
| `AssetCatalog` | Host -> Device | publish metadata/chunks and assign runtime asset aliases |
| `Telemetry` | Device -> Host | emit health, frame, transport, asset, sensor and policy events |

## 2. Not Public In V0.1

The following are internal or generated implementation details:

- Core Wire records
- Object Protocol dispatch tables
- Runtime Encoding records
- Transport Manager
- Device Manager
- Policy Manager
- Power Manager
- Frame Scheduler
- Render backend
- AI tool registry
- Python debug message envelope

They may appear in tests or prototype code, but they are not stable SDK contract.

## 3. Session

Session owns connection lifetime and capability discovery.

Required operations:

```text
connect
close
query_capabilities
subscribe_events
```

Session events include:

- connected
- disconnected
- capability_changed
- link_changed
- fatal_error

## 4. FeatureLease

FeatureLease is the only public way to request privileged or high-power Device capability.

Required operations:

```text
request_feature(feature, mode, params, lease_time)
release_feature(lease_id)
```

Required outcomes:

```text
accepted
degraded
rejected
expired
revoked
```

Sensor access, high-resolution camera, microphone, eye tracking and similar features MUST go through FeatureLease before data streaming.

## 5. Scene

Scene commits desired visual state. Device owns final runtime state.

Required operations:

```text
commit_scene(scene_state)
clear_scene
```

Scene state contains only:

- entity id
- parent id
- transform
- visibility
- asset reference
- material reference
- simple animation state token
- lifetime
- replication mode

Scene state MUST NOT contain asset bytes, scripts, engine objects, shader graphs or physics objects.

## 6. Hud

Hud commits App HUD desired state only.

Required operations:

```text
commit_app_hud(hud_state)
clear_app_hud
```

Allowed V0.1 App HUD elements:

- text
- image
- panel
- progress

System HUD is Device-owned and not exposed as Host-created elements.

## 7. SensorStream

SensorStream delivers data after a FeatureLease is active.

Required operations:

```text
subscribe_sensor_stream(lease_id, stream_spec)
unsubscribe_sensor_stream(subscription_id)
```

SensorStream cannot create or extend a lease. It only binds to an already accepted lease.

## 8. AssetCatalog

AssetCatalog maps long-term asset identity to session-local aliases.

Required operations:

```text
publish_asset_metadata
send_asset_chunk
remove_asset_alias
```

Rules:

- content hash is the long-term identity.
- alias is session-local.
- Device validates assets against Render Profile and Device budget.
- Scene commits may reference aliases only after catalog registration.

## 9. Telemetry

Telemetry is read/event surface, not a control API.

Required event classes:

- frame metrics
- feature lease events
- transport metrics
- asset cache events
- sensor stream health
- thermal/power events
- policy degrade/reject reasons

Host may subscribe to telemetry. Device owns telemetry production.

## 10. AI Adapter Boundary

AI support is optional in V0.1.

An AI adapter MAY:

- read context derived from Session, Telemetry, Scene and Sensor results.
- request actions through public SDK surfaces.
- receive ToolResult events.

An AI adapter MUST NOT:

- bypass FeatureLease.
- write System HUD directly.
- access Core Wire internals.
- become required for Session, Scene, HUD, Sensor or Telemetry operation.

## 11. Prototype Boundary

The current Python package may provide debug factories, mocks and CLI helpers. These are allowed to differ from the final C ABI / Rust / C++ implementation.

A Python type becomes contract only when this spec explicitly lists it as public surface or when generated from approved IDL.
