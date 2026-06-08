# SDK Documentation And Maintenance Review

Date: 2026-06-08

This note records concrete design and maintenance issues found in the current SDK documentation set. It intentionally avoids lab-local secrets, serial routes, private keys, passwords, and transient network addresses.

## Summary

The current SDK documentation has the right strategic direction: keep the SDK core platform-neutral, define endpoint/SDC/host roles, isolate board-specific work into profiles and adapters, and treat i.MX8MM + Orin as a reference path rather than a permanent constraint.

The main problem is not that the SDK is too abstract. The problem is that the documentation does not yet define enough structure for that abstraction to be executable. The docs say what must stay decoupled, but they do not yet say which contracts are binding, which are reference-only, which are draft placeholders, how hardware validation feeds back into SDK design, or which maintenance gates prevent the repo from drifting into a pile of good intentions.

## Documentation Design Issues

### 1. Governance Docs Have No Precedence Model

The repository has many "bible", rule, checklist, ADR, architecture, guide, and platform documents. That is useful, but the docs do not define which document wins when they conflict.

Concrete risk:

- `docs/bible/*` reads as binding.
- `docs/architecture/SDK_ARCHITECTURE.md` also reads as binding.
- `docs/platforms/REFERENCE_PLATFORM_IMX8MM_ORIN.md` is reference-only.
- `configs/platforms/*.yaml` are executable enough to affect tests and usage.

Without a precedence model, future contributors can justify incompatible changes by citing different docs.

Required fix:

- Add a short documentation authority order, for example:
  1. ADRs for accepted decisions.
  2. Bible documents for stable contracts.
  3. Rules/checklists for review gates.
  4. Architecture docs for explanatory structure.
  5. Guides/platform docs for operational reference.
- Each document should declare status: `draft`, `binding`, `reference`, or `deprecated`.

### 2. Platform Neutrality Is Stated, But Reference Implementation Duty Is Underspecified

The docs correctly insist that SDK core must not depend on i.MX8MM, Orin, LR2021, HM0360, GW1NZ, or a specific BSP. However, the original project needs a real i.MX8MM + Orin path to shape the SDK. The docs do not yet define how the reference implementation validates or changes SDK contracts.

Concrete risk:

- "Platform-neutral" can become an excuse to postpone real hardware constraints.
- "Reference-only" can become a dead branch that never proves the core API.

Required fix:

- Add a reference implementation contract:
  - It may live outside core.
  - It must use public SDK contracts.
  - It must expose validation results back into docs/tests.
  - It must be allowed to force API changes when real hardware proves the abstraction wrong.

### 3. Runtime Contract Is Not Specified As A Composition Root

The docs say hardware belongs behind adapters, but they do not clearly define how an agent is assembled from transports, health providers, video runners, power readers, sensor adapters, and platform probes.

Concrete risk:

- Runtime code can instantiate concrete UDP, GStreamer, filesystem, and Linux probes directly while still claiming to be adapter-backed.
- Tests can validate source layout while missing runtime coupling.

Required fix:

- Document a composition-root rule:
  - Core defines protocols/interfaces and state machines.
  - Platform packages create concrete adapters.
  - CLI/systemd entrypoints select a profile and build the runtime graph.
  - Agents receive dependencies, not device-specific constructors.

### 4. Control Plane Docs Do Not Define A Real Command State Machine

The message docs define UDP JSON envelope fields and message names, but they do not define command lifecycle semantics.

Missing pieces:

- `command.name` vs `msg_type`.
- `session_id` for start/stop operations.
- Idempotency key for repeated UDP commands.
- ACK correlation and duplicate handling.
- Structured errors: `code`, `message`, `retryable`, `details`.
- Timeout and retry policy.
- Capability negotiation.
- Version compatibility and extension fields.

Concrete risk:

- `start_video`, `start_lowfi`, and `display_session` will become incompatible ad hoc commands.
- UDP retries may restart sessions or create split state.

Required fix:

- Add a control-plane state-machine doc before adding more command types.
- Treat `ping` and `health` as simple request/response commands, but treat video, lowfi, power mode, display, and firmware commands as sessions.

### 5. Adapter Documentation Is Broad But Not Contractual Enough

The adapter surface names the right domains: camera, display, video encoder, radio, power, M4, FPGA, sensor, storage, and audio. But the documentation does not yet define a minimum contract for each adapter family.

Missing pieces:

- Capability discovery schema.
- Structured adapter errors.
- Session handles for long-running operations.
- Required metrics emitted by each adapter.
- Contract tests that all real and mock adapters must pass.
- Safety boundaries for destructive or power-state-changing calls.

Concrete risk:

- Adapters become thin dictionaries that cannot enforce behavior.
- Mock adapters drift away from real hardware adapters.

Required fix:

- For each adapter family, define:
  - Capabilities.
  - Commands.
  - Events.
  - Error model.
  - Required observability.
  - Contract test cases.

### 6. Telemetry Header Exists, But Payload Governance Is Too Loose

The binary telemetry packet header is a good start. The docs intentionally leave payload encoding open, but the current looseness blocks low-power validation.

Missing pieces:

- Payload family version.
- Unit and coordinate-system registry.
- Sensor timebase and synchronization rules.
- Fragmentation or maximum packet size policy.
- LR2021-oriented airtime and payload budget.
- Golden binary vectors for each payload family.

Concrete risk:

- `LOWFI_VISION`, `EYE_HINT`, `POWER_STATE`, and `LINK_STATS` become labels over arbitrary bytes.
- Power and latency results cannot be compared across M4, A53, FPGA, and radio implementations.

Required fix:

- Keep payloads extensible, but define the first four payload contracts early:
  - IMU sample.
  - Lowfi vision tile/ROI sample.
  - Eye hint tuple.
  - Power rail sample.

### 7. Power Documentation Is Conceptually Good But Not Operational

The power benchmark docs name the right modes and metrics, but they do not define a concrete logging schema or adapter interface that makes a benchmark reproducible.

Missing pieces:

- Session record schema.
- Rail naming convention.
- Meter source metadata.
- Sampling rate and synchronization requirements.
- Required start/stop events.
- How A53, M4, radio, display, camera, VPU, and rail samples are joined.

Concrete risk:

- Power data becomes notes instead of comparable evidence.
- Low-power claims cannot survive hardware changes.

Required fix:

- Add a machine-readable power session log format.
- Make `power_state` return structured rail and mode data, not a free-form dictionary.

### 8. Platform Profiles Do Not Yet Carry Hardware Capability State

The platform YAML files define role, host, ports, and video defaults. They do not encode the actual reference platform capability matrix.

Missing pieces:

- OS/BSP family: Android, embedded Linux, Jetson Linux.
- Network paths: direct Ethernet, Wi-Fi AP/client, USB gadget.
- Video path capabilities: synthetic, V4L2, CSI, VPU, software encode.
- Lowfi path status: absent, mock, M4, A53, FPGA, LR2021.
- Power instrumentation status.
- M4 firmware and mailbox status.
- Display path status.

Concrete risk:

- A platform profile can look "supported" when it only contains an IP address and a codec string.

Required fix:

- Add a capability profile schema with validation status values:
  - `not_present`
  - `planned`
  - `detected`
  - `smoke_tested`
  - `measured`
  - `blocked`

### 9. First-Run Docs Are Too Generic For Bring-Up Reality

The first-run guide is useful for a generic Linux smoke test, but it does not define a realistic two-device bring-up path.

Missing pieces:

- Host-to-board deployment path.
- Static direct-Ethernet setup.
- Network proof: link, IP, route, ping, UDP request/response, iperf.
- Orin-specific deployment and tegrastats capture.
- Android endpoint alternative path.
- Log bundle collection and artifact naming.

Concrete risk:

- A contributor can pass localhost smoke tests while the real endpoint/SDC path is not functional.

Required fix:

- Split first run into:
  - Local smoke test.
  - Linux-to-Linux two-device smoke test.
  - Reference Orin SDC setup.
  - Reference i.MX8MM endpoint setup.
  - Android endpoint bring-up appendix if Android remains in scope.

### 10. Documentation Does Not Define "Done"

Several docs list ambitions, but the project lacks a clear acceptance ladder from mock to real hardware.

Required fix:

- Add staged readiness labels:
  - `S0`: docs only.
  - `S1`: mock passes.
  - `S2`: local smoke test.
  - `S3`: two-device Linux smoke test.
  - `S4`: reference hardware detected.
  - `S5`: real video/control/telemetry working.
  - `S6`: power and latency measured.

## Project Maintenance Issues

### 1. Too Many Docs Without Ownership

The current doc set is broad enough that it needs ownership. Otherwise stale docs will accumulate quickly.

Required fix:

- Add owner/status/frontmatter to major docs:
  - `owner`
  - `status`
  - `last_reviewed`
  - `applies_to`
  - `supersedes`

### 2. Checklists Are Not Yet Enforced

The repo has checklists, but tests mostly verify file existence and naming. They do not yet enforce the deeper contracts.

Required fix:

- Add CI checks for:
  - Config schema validity.
  - Protocol golden vectors.
  - Telemetry golden vectors.
  - Adapter contract tests.
  - CLI exit-code behavior.
  - No platform-specific dependencies in core.

### 3. Tests Are Too Happy-Path

Existing tests are useful but too reassuring. They mainly prove that basic objects round-trip and mock examples run.

Required fix:

- Add negative tests:
  - Malformed UDP datagram does not kill agent.
  - Unsupported protocol version returns structured error.
  - Unknown command returns stable error code.
  - Duplicate `start_video` does not start two sessions.
  - Missing required config fails loudly.

### 4. Encoding And Windows Workflow Need A Policy

The docs are UTF-8 Chinese body text with English paths, which is fine. But Windows PowerShell output can show mojibake depending on code page and console settings.

Required fix:

- Document UTF-8 expectations for contributors.
- Prefer commands that preserve UTF-8.
- Avoid relying on console-rendered Chinese text for automated checks.

### 5. Release Readiness Does Not Gate Reference Hardware

The release checklist does not clearly require reference hardware status. For this project, SDK releases should state whether they are mock-only, Linux smoke-tested, Orin-tested, i.MX8MM-tested, or power-measured.

Required fix:

- Every release note should include:
  - Supported roles.
  - Supported platform profiles.
  - Hardware validation stage.
  - Known blocked hardware paths.
  - Power/latency measurement availability.

### 6. No Clear Separation Between Public SDK And Lab Tooling

The SDK needs platform-neutral public contracts, but the project also needs practical lab tools. These should be separated without pretending the lab layer does not exist.

Required fix:

- Add a `lab` or `reference` layer outside core:
  - Host orchestration.
  - Probe collection.
  - Serial/SSH/ADB wrappers.
  - Log bundle generation.
  - Reference platform deployment.
- Keep sensitive lab-local configuration out of the remote repo.

## Recommended Near-Term Documentation Work

1. Add a documentation authority/status model.
2. Add config schema and platform capability schema.
3. Add command/session state-machine documentation.
4. Add adapter contract details and contract-test requirements.
5. Add telemetry payload contracts for the first four payload families.
6. Add power session log schema.
7. Split first-run docs into local, two-device, Orin SDC, and i.MX8MM endpoint paths.
8. Add release readiness gates tied to validation stage.

## Non-Goals

- Do not put lab-local secrets, serial logs, private keys, passwords, or transient local IPs into this remote repository.
- Do not hard-code the SDK core to i.MX8MM or Orin.
- Do not delay all SDK structure until real hardware is complete. The point is to design contracts that can survive hardware bring-up, not to avoid contract design.
