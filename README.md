# Meiso Glass

Meiso Glass is the working repository for the AR glasses endpoint and SDC SDK.

The project is still in hardware bring-up and SDK draft stage. The current goal
is to define stable protocol, replay, simulation, and host tooling boundaries
before binding the SDK to a specific board image, radio, camera, or Jetson
runtime.

## Hardware Context

- Endpoint candidate: i.MX 8M Mini development board for early interface and
  BSP validation.
- Endpoint peripheral validation target: HM0360 low-power vision, GW1NZ-2
  helper, LR2021 telemetry radio, nRF54L15 command receiver, ICM-45686 IMU,
  and two T5838 PDM microphones.
- SDC candidate: Jetson Orin Nano / Orin NX class SBC or SOM.
- High-bandwidth path: Wi-Fi between SDC and glasses endpoint.
- Low-power telemetry path: endpoint sensor island to SDC over LR2021-class
  telemetry.

## SDK Direction

The first SDK pass should focus on interfaces that can be developed before the
final hardware is available:

- telemetry schemas for IMU, low-power vision, eye hints, audio wake events,
  thermal state, battery state, and rail power samples
- command schemas for power mode, display mode, sensor enablement, radio policy,
  calibration state, and session control
- transport abstraction for serial, UDP/TCP, Wi-Fi, BLE, LR2021, and file replay
- fake endpoint simulator for SDC-side development
- record, replay, and inspect tools for logs and protocol traces

## Initial Milestones

1. Define protocol and capability schemas.
2. Implement a fake endpoint that emits deterministic telemetry.
3. Implement record/replay tooling for local development.
4. Add adapters for the i.MX 8M Mini bring-up board.
5. Add SDC runtime adapters for Jetson Orin Nano once the SBC is connected.

## Repository Status

This repository is newly initialized. Hardware-specific code should remain
behind adapters until the i.MX 8M Mini endpoint wiring, device tree changes, and
SDC runtime targets are stable.
