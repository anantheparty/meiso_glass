# Meiso Glass SDK Bible：子系统详细设计案

> 状态：Bible v0.4 XR-core 草案
> 修订日期：2026-06-13
> 目标：把 Meiso SDK 的稳定 contract 写成可落代码、可 mock、可测试、可扩展到单眼/双眼/depth/spatial 的结构。

## 0. 本文件边界

本文是 `SDK_DESIGN_OVERVIEW.md` 的展开，负责字段和 contract。本文不写使用教程，不写板级飞线，不写完整 OpenXR runtime，也不写 render engine。

规范词：

| 词 | 含义 |
|---|---|
| MUST / 必须 | 不满足就不是兼容实现 |
| SHOULD / 应该 | 默认要求；例外要写入 evidence/unknowns |
| MAY / 可以 | 可选能力 |
| MUST NOT / 不得 | 会破坏边界或兼容性 |

## 1. 目标源码分层

```text
src/meiso_glass/
  core/           identity, path, profile, capability, session, error, condition
  space/          space ref, pose, relation, calibration, spatial capability
  presentation/   view set, layer, surface, frame timing, frame stats
  power/          level, budget, profile, cost point, measurement, policy
  adapters/       base contract and family contracts
  runtime/        admission, session manager, degradation, scheduler
  control/        envelope, command, ack, error, idempotency
  telemetry/      packet header, payload families, replay
  evidence/       trace, validation, measurement summary
  simulation/     fake endpoint, fake SDC, fake adapters
```

V0 可以不立刻重构目录，但代码结构不得反向定义 SDK 边界。public contract 必须先稳定，UDP/GStreamer/mock 只是实现之一。

## 2. 通用结构

### 2.1 Metadata

```yaml
Metadata:
  id: string
  revision: string
  owner_role: endpoint | sdc | host
  device_id: string | null
  instance_id: string | null
  profile_id: string | null
  created_at_realtime_ns: int | null
  labels: map[string,string]
```

### 2.2 SemanticPath

Meiso 使用语义路径命名 capability、space、profile、surface、policy：

```text
/cap/camera/world/lowfi
/cap/display/primary/mono
/space/display/primary
/surface/hud/main
/policy/product/default
```

规则：

- public contract 使用语义路径。
- adapter 内部可以记录 `/dev/video0`、socket、I2C addr，但不能作为 public identity。
- 路径必须稳定，重命名需要 revision。

### 2.3 Condition

```yaml
Condition:
  type: Ready | Admitted | Running | Degraded | Blocked | PowerConstrained | LinkConstrained | ThermalConstrained | Measuring
  status: true | false | unknown
  reason: string
  message: string
  observed_generation: int
  last_transition_time_ns: int
```

Condition 用于异步状态，不替代 session state。

### 2.4 StructuredError

```yaml
StructuredError:
  code: string
  message: string
  retryable: bool
  severity: info | warning | error | fatal
  related_session_id: string | null
  related_capability_id: string | null
  failed_state: string | null
  details: map
```

错误码必须稳定，不能把 Python exception 或驱动日志原样暴露为 public API。

## 3. Core domain contract

### 3.1 SystemProfile

```yaml
SystemProfile:
  metadata: Metadata
  spec:
    role: endpoint | sdc | host
    platform_family: string
    capabilities: list[CapabilityRef]
    adapter_bindings: list[AdapterBinding]
    default_policy_ref: string
    network_paths: list[NetworkPath]
    measurement_sources: list[string]
    extension_slots: list[ExtensionSlot]
  status:
    validation_state: declared | mocked | detected | smoke_tested | measured | blocked
    available_capabilities: list[string]
    blocked_capabilities: list[string]
    conditions: list[Condition]
  evidence:
    unknowns: list[string]
    validation_results: list[ValidationResult]
```

Profile 的职责是装配，不是业务逻辑。Profile 可以声明 future slot，但 `declared` slot 不可被 runtime admission 当成可用能力。

### 3.2 Capability

```yaml
Capability:
  metadata: Metadata
  spec:
    family: camera | display | presentation | audio | radio | sensor | compute | power | storage | spatial | debug
    role_owner: endpoint | sdc | host
    resource_tier: ResourceTier
    output_forms: list[string]
    required_spaces: list[string]
    dependencies: list[string]
    limits: map
    power_profile_ref: string | null
    quality_profile: map
    latency_profile: map
    privacy_class: none | low | medium | high
  status:
    availability: available | unavailable | degraded | blocked
    validation_state: declared | mocked | detected | smoke_tested | measured | blocked
    current_level_u8: int | null
    conditions: list[Condition]
  evidence:
    measurement_source: string
    confidence_level_u8: int
    last_validated_at_ns: int | null
    unknowns: list[string]
```

Capability MUST 是 SDK 判断“能不能做某事”的唯一入口。Adapter 不能绕过 capability 直接接受上层请求。

### 3.3 ResourceTier

```yaml
ResourceTier:
  compute: none | sentinel | low_power_helper | app_cpu | sdc_ai | debug
  vision: none | lowfi | eye_hint | rich | depth_future | calibration
  audio: none | wake | voice_hint | capture | array | debug
  display: none | status | hud | interactive | video | calibration
  link: none | low_power_control | telemetry | high_bandwidth_rx | high_bandwidth_tx | debug
  payload: none | event | tuple | tile | compressed_stream | raw
```

ResourceTier 只描述功耗/调度层级，不描述具体硬件型号。

### 3.4 Session

```yaml
Session:
  metadata: Metadata
  request:
    idempotency_key: string
    requester_role: endpoint | sdc | host
    intent: string
    priority: background | normal | user_visible | critical | debug
  spec:
    session_type: lowfi_sensing | eye_hint | rich_video | presentation | audio_capture | spatial_query | power_measurement | debug_capture
    requested_capabilities: list[string]
    required_spaces: list[string]
    power_budget: PowerBudget
    quality_budget: map
    information_budget: map
    allowed_degradation: list[string]
  status:
    state: proposed | admitted | rejected | starting | running | degraded | recovering | stopping | stopped | failed
    selected_capabilities: list[string]
    selected_power_levels: map[string,int]
    selected_plan: map
    degradation_reason: string | null
    conditions: list[Condition]
  evidence:
    admission_trace: list[AdmissionStep]
    state_transitions: list[StateTransition]
    metrics_summary: map
    power_summary: map | null
    errors: list[StructuredError]
```

所有非瞬时操作 MUST 是 session。Session request、selected plan、真实 status 必须分开。

## 4. Space / Spatial contract

### 4.1 SpaceRef

```yaml
SpaceRef:
  space_id: string
  kind: head | display | camera | eye | world | local | sdc_world | sensor | unknown
  owner_role: endpoint | sdc | host
  persistence: session | boot | factory | product
```

建议保留的基础 space：

```text
/space/head
/space/display/primary
/space/camera/world_lowfi
/space/camera/world_rich
/space/camera/eye_primary
/space/sdc/world
/space/local
```

### 4.2 Pose and SpaceRelation

```yaml
Pose:
  position_m: [number, number, number]
  orientation_xyzw: [number, number, number, number]
```

```yaml
SpaceRelation:
  from: string
  to: string
  timestamp_ns: int
  timebase: monotonic | source | realtime
  pose: Pose
  linear_velocity_mps: [number, number, number] | null
  angular_velocity_radps: [number, number, number] | null
  validity: valid | estimated | unavailable
  confidence_level_u8: int
  source: declared_only | factory_calibration | runtime_tracking | sdc_fusion | mock
```

V0 可以只支持 declared/factory calibration，但 schema 必须存在。

### 4.3 SensorSlot

```yaml
SensorSlot:
  slot_id: string
  sensor_role: world | eye | depth | ir | event | imu | mic | wear | calibration | debug
  capture_modality: mono | rgb | rgbir | ir | event | depth_tof | structured_light | stereo_pair | imu | audio | unknown
  mounted_space: string
  owner_role: endpoint | sdc | host
  validation_state: declared | mocked | detected | smoke_tested | measured | blocked
```

Future depth camera、stereo pair、IR、event camera 先进入 SensorSlot，不写具体 adapter。

### 4.4 SpatialCapability

```yaml
SpatialCapability:
  metadata: Metadata
  spec:
    spatial_role: pose | gaze | depth | occlusion | hit_test | anchor | mesh | scene_semantics | calibration
    source_slots: list[string]
    output_forms: list[pose | ray | depth_map | confidence_map | point_cloud | plane | mesh | anchor | hit_result | semantic_label]
    coordinate_space: string
    update_rate_hz: number | null
    privacy_class: none | low | medium | high
  status:
    validation_state: declared | mocked | detected | smoke_tested | measured | blocked
    availability: available | unavailable | degraded | blocked
  evidence:
    confidence_level_u8: int
    unknowns: list[string]
```

## 5. Presentation contract

### 5.1 ViewSet

```yaml
ViewSet:
  viewset_id: string
  topology: mono | stereo | multiview | three_d
  views: list[ViewSlot]
  stereo_mode: none | side_by_side | dual_surface | time_multiplexed | optical_engine_specific
  depth_composition: unsupported | declared | supported | measured
```

```yaml
ViewSlot:
  view_id: string
  eye: none | left | right | both | other
  display_space: string
  viewport: [int, int, int, int] | profile_declared
  recommended_resolution: [int, int] | null
  supported_refresh_hz: list[number]
  projection_kind: profile_declared | pinhole | optical_engine_specific
  fov_hint: map | null
```

规则：

- Mono V0 是 profile，不是 core 假设。
- Stereo/multiview/3D 通过 ViewSet 扩展。
- ViewSlot 不绑定 shader 或 graphics API。

### 5.2 PresentationSurface

```yaml
PresentationSurface:
  surface_id: string
  producer_role: endpoint | sdc | host
  kind: local_buffer | sdc_stream | video_stream | static_asset | diagnostic
  format_hint: rgba | yuv | compressed_video | opaque_handle | unknown
  size_px: [int, int] | null
  max_update_hz: number | null
  transport_ref: string | null
```

它是 OpenXR swapchain 思路的轻量版。V0 不要求实现真正 swapchain，只要求能表达“谁生产了什么 surface，给哪个 layer 用”。

### 5.3 PresentationLayer

```yaml
PresentationLayer:
  layer_id: string
  layer_type: status | hud | ar_overlay | video | calibration | depth_mask | passthrough_hint | debug
  target_views: list[string]
  surface_ref: string
  composition:
    order: int
    alpha_mode: opaque | premultiplied | additive
    space: string
    pose_in_space: Pose | null
  constraints:
    max_latency_ms: number | null
    min_refresh_hz: number | null
    allow_drop: bool
  power_hints:
    allow_refresh_degrade: bool
    allow_brightness_cap: bool
    allow_viewport_scale: bool
    allow_layer_disable: bool
```

Layer 是 SDK core；渲染 layer 内容的方式不是 SDK core。

### 5.4 PresentationSessionSpec

```yaml
PresentationSessionSpec:
  viewset_ref: string
  layers: list[PresentationLayer]
  frame_timing_policy:
    target_refresh_hz: number
    max_frame_latency_ms: number
    allow_frame_skip: bool
  display_policy:
    brightness_mode: auto | capped | fixed
    max_brightness_pct: int | null
    content_update_region: full | partial | sparse
  degradation_order:
    - disable_debug_layer
    - reduce_refresh
    - scale_viewport
    - disable_video_layer
    - mono_only
```

### 5.5 FrameTiming and FrameStats

```yaml
FrameTiming:
  frame_index: int
  predicted_display_time_ns: int
  deadline_ns: int
  submitted_time_ns: int | null
  displayed_time_ns: int | null
  missed_deadline: bool
  drop_reason: none | late | power_policy | link_congestion | adapter_busy
```

```yaml
PresentationFrameStats:
  session_id: string
  frames_submitted: int
  frames_displayed: int
  frames_dropped: int
  avg_latency_ms: number | null
  p95_latency_ms: number | null
  refresh_hz_observed: number | null
  selected_brightness_pct: int | null
  selected_viewport_scale: number | null
```

## 6. Power contract

### 6.1 PowerBudget

```yaml
PowerBudget:
  budget_id: string | null
  max_avg_mw: number | null
  max_peak_mw: number | null
  max_thermal_risk_u8: int | null
  max_wake_latency_ms: number | null
  max_session_duration_ms: int | null
  max_airtime_ms_per_s: number | null
  policy: conservative | balanced | performance | debug
```

Budget 是请求侧约束，不是测量结果。

### 6.2 PowerLevel

```yaml
PowerLevel:
  scheme: u8
  value: int  # 0..255
  band: off | retention | wake_ready | sentinel | sparse_capture | local_process | low_stream | rich_stream | peak_stream | debug_boost
```

Level 只在同一个 adapter/family 内做强排序；跨 family 只能粗略比较。

### 6.3 PowerProfile

```yaml
PowerProfile:
  profile_id: string
  adapter_id: string
  family: string
  supported_levels: list[int]
  default_level: int
  cost_points: list[PowerCostPoint]
  transitions: list[PowerTransition]
  unknowns: list[string]
```

### 6.4 PowerCostPoint

```yaml
PowerCostPoint:
  level: int
  adapter_state: off | retention | idle | active | suspended | debug
  settings: map
  expected_mw: number | null
  peak_mw: number | null
  thermal_risk_u8: int
  wake_latency_ms: number | null
  settle_latency_ms: number | null
  unit_cost:
    uj_per_event: number | null
    uj_per_frame: number | null
    bytes_per_joule: number | null
  measurement_source: declared_only | datasheet_estimate | driver_counter | os_powerstats | rail_probe | bench_fixture | product_calibrated
  confidence_level_u8: int
```

V0 只要求少量 supported levels，例如 `[0, 32, 64, 128, 160]`。

### 6.5 PowerTransition

```yaml
PowerTransition:
  from_level: int
  to_level: int
  wake_latency_ms_typ: number | null
  wake_latency_ms_max: number | null
  settle_latency_ms_typ: number | null
  requires: list[string]
  forbidden_when: list[string]
```

### 6.6 MeasuredPowerPoint

```yaml
MeasuredPowerPoint:
  point_id: string
  adapter_id: string
  session_id: string | null
  rail_id: string | null
  level: int
  settings: map
  mw_avg: number | null
  mw_peak: number | null
  uj_per_event: number | null
  uj_per_frame: number | null
  sample_window_ms: int
  measurement_source: declared_only | datasheet_estimate | driver_counter | os_powerstats | rail_probe | bench_fixture | product_calibrated
  confidence_level_u8: int
```

功耗数据必须带 source 和 confidence。低 confidence 数据不能进入精细自动调度，只能用于保守 admission 或人工分析。

## 7. Adapter contract

### 7.1 Base Adapter

```yaml
AdapterContract:
  adapter_id: string
  family: string
  owner_role: endpoint | sdc | host
  provides_capabilities(): list[Capability]
  probe(): AdapterProbeResult
  get_status(): AdapterStatus
  get_power_profile(): PowerProfile
  start_session(plan): AdapterStartResult
  stop_session(session_id, reason): AdapterStopResult
  validate(): ValidationResult
```

所有 adapter MUST：

- 声明 capability。
- 声明 power profile。
- 返回 structured status。
- 返回 structured error。
- 支持 mock contract test。

### 7.2 AdapterStatus

```yaml
AdapterStatus:
  adapter_id: string
  availability: available | unavailable | degraded | blocked
  current_level_u8: int | null
  busy: bool
  active_sessions: list[string]
  conditions: list[Condition]
  last_error: StructuredError | null
  evidence_ref: string | null
```

### 7.3 CameraAdapter

CameraAdapter 负责 image/media/sparse vision source，不负责空间融合。

```yaml
CameraCapabilitySpec:
  sensor_role: wake | lowfi | eye_hint | world_rich | calibration | debug | future_depth
  capture_modality: mono | rgb | rgbir | ir | event | depth_tof | structured_light | stereo_pair | unknown
  pixel_formats: list[string]
  frame_sizes: list[[int,int]]
  frame_intervals: list[number]
  crop_modes: list[string]
  binning_modes: list[string]
  roi_modes: list[string]
  output_forms: event | tuple | tile | compressed_stream | raw_frame
  mounted_space: string
  privacy_class: none | low | medium | high
```

Camera-specific cost detail MAY include：

```yaml
camera_cost_detail:
  capture_level_u8: int
  process_level_u8: int
  egress_level_u8: int
  information_level_u8: int
```

规则：

- 高 capture 不等于高 egress。
- 高 information 不等于高 byte rate。
- Eye hint 输出默认是 camera-space sparse tuple，不是 screen-space gaze final。
- Depth/future camera 不在 V0 写 adapter，只写 SensorSlot/SpatialCapability。

### 7.4 DisplayAdapter

DisplayAdapter 只负责面板和显示链路。

```yaml
DisplayCapabilitySpec:
  display_role: status | hud | ar | debug
  display_space: string
  resolution: [int,int]
  supported_refresh_hz: list[number]
  brightness_range_pct: [int,int]
  supports_partial_update: bool | unknown
  supports_low_refresh: bool | unknown
  link_type: dsi | spi | parallel | internal | unknown
```

DisplayAdapter 不负责 layer 排序、view topology 或 render engine。

### 7.5 PresentationPort

PresentationPort 不是 RenderAdapter。它是 runtime 和 display/media/link 之间的呈现 contract 执行口。

```yaml
PresentationPort:
  supports_viewsets: list[string]
  supports_layer_types: list[string]
  supports_surface_kinds: list[string]
  max_layers: int
  max_surfaces: int
  frame_timing_source: endpoint | sdc | display_adapter | mock
```

V0 可先做 mock，真实实现后接 display path。

### 7.6 RadioLinkAdapter

```yaml
RadioCapabilitySpec:
  link_role: low_power_control | telemetry_tx | media_rx | media_tx | debug
  phy: lr2021 | ble | wifi | ethernet | usb | unknown
  direction: tx | rx | bidirectional
  payload_budget_bps: number | null
  airtime_budget_ms_per_s: number | null
  wake_interval_ms: number | null
  tx_power_dbm: number | null
  retry_policy: map
```

Radio power 主要看 airtime、TX power、wake interval、监听窗口、重传和 payload，不看协议名。

### 7.7 SensorAdapter

```yaml
SensorCapabilitySpec:
  sensor_role: imu | mic_wake | mic_capture | wear | als | prox | temp | touch | gnss | debug
  output_forms: event | sample | tuple | stream
  sample_rates_hz: list[number]
  mounted_space: string | null
  power_profile_ref: string
```

### 7.8 ComputeBridge：M4 / FPGA / helper

```yaml
ComputeBridgeSpec:
  bridge_role: wake | sensor_hub | fpga_control | lowfi_vision | packet_filter | timing | debug
  compute_tier: sentinel | low_power_helper | app_cpu | sdc_ai
  input_forms: list[string]
  output_forms: list[string]
  mailbox_rate_hz: number | null
  shared_memory_bytes: int | null
  firmware_state: unknown | loaded | running | blocked
```

M4/GW1NZ 的存在进入 adapter/profile，不进入 core enum。

### 7.9 PowerAdapter

```yaml
PowerAdapterSpec:
  power_entities: list[string]
  rails: list[string]
  sampling_modes: coarse | session | high_rate | bench_fixture
  supports_state_residency: bool
  supports_energy_counter: bool
```

PowerAdapter 自己也耗电，高频采样必须进入 session budget。

### 7.10 StorageAdapter

```yaml
StorageCapabilitySpec:
  storage_role: log | replay | recording | model_cache | debug_dump
  write_rate_bps: number | null
  flush_policy: immediate | interval | session_end | manual
  retention_policy: volatile | session | persistent | debug_only
```

## 8. Runtime admission

Admission 输入：

```yaml
AdmissionRequest:
  session_spec: Session.spec
  current_system_status: map
  profile_snapshot: SystemProfile
  policy_ref: string
```

Admission 步骤 MUST 记录：

1. capability 是否存在。
2. validation_state 是否足够。
3. dependencies 是否满足。
4. resource_tier 是否被当前 power mode 允许。
5. link/airtime 是否足够。
6. display/presentation view/layer/refresh 是否可执行。
7. power budget 是否足够。
8. 是否需要降级。
9. 选择哪些 adapter 和 power level。

```yaml
AdmissionStep:
  step: string
  result: pass | fail | degraded | skipped
  reason: string
  evidence_ref: string | null
```

## 9. Control plane

### 9.1 Envelope

```yaml
ControlEnvelope:
  version: 1
  msg_id: string
  seq: int
  time_ns: int
  source_role: endpoint | sdc | host
  target_role: endpoint | sdc | host
  msg_type: command | ack | error | event | heartbeat
  payload: map
```

### 9.2 Commands

V0 commands：

```text
ping
query_system_profile
query_capabilities
propose_session
start_session
stop_session
get_session_status
set_policy
subscribe_telemetry
get_evidence
```

`start_session` MUST 支持 idempotency key。重复请求不能重复启动硬件。

### 9.3 ACK

```yaml
AckPayload:
  request_msg_id: string
  ok: bool
  session_id: string | null
  state: string | null
  idempotency_hit: bool
  selected_plan: map | null
  warnings: list[StructuredError]
```

## 10. Telemetry plane

第一批 payload family：

| family | 用途 |
|---|---|
| `imu_sample` | 小传感器运动样本 |
| `lowfi_vision_tuple` | ROI/tile/motion hint |
| `eye_hint_tuple` | pupil/blob/glint/blink/confidence |
| `space_relation_sample` | space 间 pose 关系 |
| `presentation_frame_stats` | frame timing/drop/latency/refresh |
| `adapter_power_state` | adapter current level/state/confidence |
| `power_rail_sample` | rail voltage/current/power |
| `link_stats` | RSSI/packet loss/airtime/rate |
| `session_event` | state transition/degradation/error |

时间字段必须区分：

```text
monotonic_time_ns  # 排序/延迟/session 统计
source_time_ns     # 传感器/M4/FPGA 原始时间
realtime_ns        # 人类日志关联
```

## 11. Evidence / observability

每个 session 至少记录：

```yaml
SessionEvidence:
  session_id: string
  request_snapshot: map
  capability_snapshot: list[Capability]
  admission_trace: list[AdmissionStep]
  selected_plan: map
  adapter_status_start: list[AdapterStatus]
  adapter_status_end: list[AdapterStatus]
  telemetry_summary: map
  power_summary: map | null
  errors: list[StructuredError]
  stop_reason: string
```

Evidence 是 Meiso SDK 的核心资产：它让调度、功耗、质量和硬件实验可以被回放，而不是靠口头判断。

## 12. V0 profile examples

### 12.1 Endpoint mono display profile

```yaml
ViewSet:
  viewset_id: /viewset/endpoint/mono_primary
  topology: mono
  views:
    - view_id: primary
      eye: none
      display_space: /space/display/primary
      viewport: profile_declared
      recommended_resolution: null
      supported_refresh_hz: [30, 60]
      projection_kind: profile_declared
  stereo_mode: none
  depth_composition: unsupported
```

### 12.2 Future stereo/depth declared slots

```yaml
ExtensionSlot:
  slot_id: /slot/display/stereo_future
  kind: viewset
  validation_state: declared
  usable_for_admission: false
```

```yaml
ExtensionSlot:
  slot_id: /slot/camera/depth_front_future
  kind: sensor
  validation_state: declared
  usable_for_admission: false
```

## 13. Contract tests

V0 必须先写这些测试：

| Test | 目的 |
|---|---|
| schema roundtrip | 所有 core object 可序列化/反序列化 |
| invalid field rejection | 缺关键字段或错 enum 会失败 |
| session state machine | 非法状态迁移会失败 |
| idempotency | 重复 start 不重复启动 |
| adapter contract | mock 和 real adapter 同一测试套 |
| power admission | 预算不足会 reject/degrade |
| presentation admission | view/layer/refresh 不满足会 reject/degrade |
| declared slot safety | `declared` future depth/stereo 不能被当成可用 |
| evidence completeness | session 停止后有 evidence |

## 14. 当前明确不做

- 不做完整 OpenXR bridge。
- 不做 RenderAdapter。
- 不做 DepthCameraAdapter。
- 不做 full controller action map。
- 不做 anchors/hit-test/mesh public API。
- 不做 graphics API binding。
- 不做 shader/material/scene graph。
- 不把硬件 bring-up 脚本放进 core。
