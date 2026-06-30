# Runtime Planes Spec

本页定义 Meiso SDK V0.1 的三条 runtime plane。它用于避免 SDK 继续按 manager/API 名称膨胀。

## 1. Plane Model

```text
Control Plane
  decides what may run

Presentation Plane
  decides what is shown

Data Plane
  moves observations out of Device
```

Object Protocol、Runtime Encoding、Core Wire 和 Transport Profile 只负责承载这些 plane 的消息。它们不是第四条业务 plane。

## 2. Control Plane

Purpose: decide whether a requested capability may become active.

Owns:

- capability snapshot
- feature lease table
- permission state
- session state
- power and thermal guard inputs
- policy rejection reasons

Inputs:

- Host feature request
- Device capability
- user/system permission
- battery/thermal state
- link/session state
- safety state

Outputs:

- lease accepted
- lease degraded
- lease rejected
- lease expired
- lease revoked
- capability update
- session status

Public V0.1 concept: `FeatureLease`.

Non-public implementation names:

- Device Manager
- Policy Manager
- Power Manager
- Sensor Manager

Those may exist in code, but they are not SDK concepts.

## 3. Presentation Plane

Purpose: maintain the latest safe visual state and render it on the Device's local frame schedule.

Owns:

- scene desired-state replica
- asset cache view
- app HUD desired state
- system HUD state
- render profile enforcement
- frame loop
- placeholder/degraded presentation state

Inputs:

- accepted scene commit
- asset catalog/cache events
- accepted app HUD commit
- local pose/tracking
- system status
- control plane lease/capability state

Outputs:

- presented frame
- frame telemetry
- stale/freeze/hide decisions
- asset missing or asset invalid events

Rules:

- Frame Loop is the spine of Device Runtime.
- Frame Loop reads snapshots; it does not wait for Host.
- App HUD is Host desired state.
- System HUD is Device runtime state and has highest priority.
- Asset bytes never travel inside scene commits.

## 4. Data Plane

Purpose: send observations, measurements and processed results from Device to Host.

Owns:

- sensor stream objects
- processed result streams
- input events
- telemetry events
- optional AI context snapshots

Inputs:

- active feature leases
- sensor hardware data
- local processing results
- frame/transport/asset metrics
- runtime errors

Outputs:

- sensor samples
- processed results
- telemetry snapshots/events
- optional AI context packets

Rules:

- High-power sensor streams require an active Control Plane lease.
- Sensor subscription cannot grant access by itself.
- Telemetry is Device-owned and primarily Device to Host.
- AI is an adapter over Data and Control, not a required runtime dependency.

## 5. Cross-Plane Rules

- Data Plane MUST NOT enable sensors without Control Plane lease approval.
- Presentation Plane MAY read Control Plane state to show permission/thermal/network overlays.
- Presentation Plane MUST NOT wait for Data Plane upload completion.
- Control Plane MAY revoke leases based on telemetry, thermal or safety state.
- Host desired state never overrides Device System HUD.
- Transport failure must not block Frame Loop.

## 6. Anti-Patterns

V0.1 rejects these designs:

- independent `PolicyManager` as a public SDK module.
- Host API returning transport messages as its main abstraction.
- AI tool registry as mandatory core SDK surface.
- sensor subscription bypassing feature lease.
- render thread reading mutable network state.
- scene commit carrying asset bytes.
- Core Wire carrying business message names.
