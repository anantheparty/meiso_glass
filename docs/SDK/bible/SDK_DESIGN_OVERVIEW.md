# Meiso SDK V0.1 Design Overview

本页是 Meiso SDK V0.1 的唯一设计 bible。它定义角色、边界、平面和公开 SDK 面。更细的 wire、object、render、transport 文档都是本页的派生 contract。

## 1. System Position

Meiso 是双角色空间端点系统。

| Role | Owns | Does Not Own |
|---|---|---|
| Host | 业务逻辑、AI、物理、场景期望状态、资产生产、调试工具 | 本地姿态、最终显示时钟、System HUD、硬件安全策略 |
| Device | 设备能力、Feature Lease 执行、本地姿态、Frame Loop、轻量渲染、System HUD、传感器采集、功耗/温度降级 | 完整 Unity/Godot、远程 OpenGL、任意脚本、业务权威世界 |

Hard rules:

- Host and Device communicate through Meiso Object Protocol and link profiles.
- Device does not run full Unity/Godot.
- Device does not receive OpenGL/GPU command streams.
- Device Frame Loop never waits for Host, network retry, asset download, AI or sensor upload.
- AI is optional. Meiso Core must run without AI.

## 2. Runtime Planes

SDK V0.1 has three runtime planes.

```text
Control Plane
  capability, feature lease, permission, policy decision, session health

Presentation Plane
  scene desired state, asset references/cache, app HUD, system HUD, render profile, frame loop

Data Plane
  sensor streams, processed results, telemetry, optional AI context/tool adapter
```

Transport, Core Wire, Runtime Encoding and Object Protocol are internal carriage. They are not product modules and not Host-facing business APIs.

## 3. Control Plane

Control Plane decides what the Device is allowed to do.

Inputs:

- capability profile
- feature request
- permission state
- power and thermal state
- link/session state
- safety state

Outputs:

- accepted/degraded/rejected feature lease
- lease expiry/revoke events
- capability snapshots
- session status
- policy rejection reasons

V0.1 public concept:

```text
Feature Lease
```

There is no public `DeviceManager` or `PolicyManager` in V0.1. Those are implementation internals behind Feature Lease decisions.

## 4. Presentation Plane

Presentation Plane decides what the user sees.

Inputs:

- latest accepted scene desired state
- asset cache state
- app HUD desired state
- system HUD state
- local pose/tracking
- render profile and device budget

Outputs:

- rendered frame
- placeholder/degraded content
- frame telemetry
- asset missing events

Device owns the final presentation. Host submits desired state only.

Composition order is fixed:

```text
3D Scene -> App HUD -> System HUD
```

System HUD is Device-owned and cannot be created or hidden by Host.

## 5. Data Plane

Data Plane moves observations from Device to Host.

Sources:

- camera/audio/eye/IMU samples
- local processed results
- input events
- telemetry
- optional AI context snapshots

Rules:

- High-power streams require an active Feature Lease.
- Sensor subscription does not grant hardware access by itself.
- Telemetry is primarily Device -> Host.
- AI context/tool surfaces are optional adapters over existing Control, Presentation and Data planes.

## 6. Host SDK Surface

V0.1 Host SDK exposes only these stable concepts:

| Surface | Purpose |
|---|---|
| `Session` | connect, close, query capability, receive events |
| `FeatureLease` | request/release camera, microphone, eye, render, network and other feature leases |
| `Scene` | submit desired 3D state by entity and asset reference |
| `Hud` | submit desired App HUD state |
| `SensorStream` | receive samples/results after lease approval |
| `AssetCatalog` | publish asset metadata and chunks; map content hash to compact runtime aliases |
| `Telemetry` | receive health, frame, transport, policy, asset and sensor events |

Not public V0.1 SDK surface:

- Core Wire
- Object Protocol dispatch tables
- Transport Manager
- Device Runtime internals
- Policy Manager
- Frame Scheduler internals
- AI tool registry
- Render backend internals

Python prototype APIs are mocks and test harnesses, not final SDK contract.

## 7. Device Runtime Spine

Device Runtime is organized around the Frame Loop, not around manager objects.

```text
wait local frame boundary
read latest complete presentation state
read asset/cache status
read control/lease state
predict local pose for target display time
choose render / HUD-only / cached frame path
draw 3D Scene if needed
draw App HUD
draw System HUD
present
emit telemetry
```

Inputs are snapshots. Network threads and sensor upload threads must not mutate render-thread state directly.

## 8. Scene Model V0.1

Scene V0.1 is a renderable desired-state model, not a game engine.

Allowed entity fields:

- `entity_id`
- `parent_id`
- `transform`
- `mesh_ref`
- `material_ref`
- `visibility`
- `animation_state_token`
- `lifetime`
- `replication_mode`

Forbidden in Scene V0.1:

- scripts
- colliders and complex physics
- behavior trees
- lights beyond Render Profile 0
- particles
- material graphs
- inline mesh/texture/font bytes
- engine object handles

## 9. Asset Model V0.1

Scene messages reference assets. They do not carry asset bytes.

Asset identity:

- long-term identity: content hash
- runtime identity: compact session-local alias
- validation target: render profile and device budget

Missing or invalid asset behavior:

- Device may reject the commit.
- Device may accept with placeholder if the interface allows degraded presentation.
- Device frame loop must not block on asset download.

## 10. Render Profile V0.1

Only Meiso Profile 0 is in V0.1 contract.

Profile 0 supports:

- OpenGL ES 2.0 target
- static low-poly mesh
- transform
- unlit color
- unlit texture
- vertex color
- alpha blend
- simple depth test
- fixed small material/texture budgets
- text/image/panel/progress App HUD primitives

Profile 0 forbids:

- arbitrary shader
- dynamic shadow
- post-processing
- full particle system
- gameplay script on Device
- complex local physics
- full Unity/Godot runtime
- arbitrary native OpenXR app
- remote GPU command protocol

Profile 1+ are roadmap, not V0.1 contract.

## 11. Resource Policy

V0.1 does not guarantee automatic compute/network/sensor upgrade behavior.

Device may:

- accept
- degrade
- reject
- revoke
- freeze
- hide
- show placeholder

Host must tolerate all of these outcomes.

Resource levels and thresholds are hardware-validation data, not stable SDK API.

## 12. Failure Rules

- Host absent: Device keeps System HUD and local safety behavior.
- No new scene state: Device may reuse latest valid snapshot.
- State stale: Device may freeze, hide or degrade affected objects.
- Asset missing: Device may show placeholder or reject commit.
- Feature lease expired: Device stops high-power feature.
- Temperature or battery unsafe: Device may revoke leases and lower presentation quality.
- Network degraded: Device must not block Frame Loop.

## 13. Explicit Non-Goals

V0.1 does not provide:

- OpenXR runtime compatibility.
- full Unity/Godot runtime on Device.
- remote OpenGL/GPU command streaming.
- arbitrary shaders.
- complex local physics.
- engine-specific scene graph transport.
- mandatory AI runtime.
- public SDK access to Core Wire internals.
