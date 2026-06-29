# Capability Profile Spec

Capability Profile 描述 Host 能向 Edge 请求什么，以及 Edge 在什么功耗、权限和渲染约束下可以接受请求。

## Profile Object

```json
{
  "profileId": "edge.generic.v0",
  "role": "edge",
  "coreWireVersion": 1,
  "runtimeVersion": 1,
  "features": [],
  "renderProfiles": [],
  "sensors": [],
  "power": {},
  "transports": [],
  "policy": {}
}
```

`profileId` 是能力快照 ID。能力改变后必须产生新的 profile 或增加 `profileRevision`。

## Feature Capability

```json
{
  "feature": "camera",
  "modes": ["still", "stream", "lowfi"],
  "requiresPermission": true,
  "requiresUserConfirmation": true,
  "maxLeaseMs": 30000,
  "defaultLeaseMs": 5000,
  "powerVector": {
    "cameraLevel": [32, 191],
    "networkLevel": [96, 223],
    "computeLevel": [32, 159]
  }
}
```

Feature capability 只说明设备可做什么，不代表 Host 已获得授权。真实开启仍然必须走 `FeatureRequest` 和 policy。

## Sensor Capability

| Field | Meaning |
|---|---|
| `sensor` | `camera`、`audio`、`eye`、`imu`、`local_result` |
| `formats` | resolution、rate、encoding、dataType 组合 |
| `powerVector` | 该格式需要的功耗向量范围 |
| `maxDurationMs` | 单次订阅最长持续时间 |
| `privacyClass` | `public`、`motion`、`scene`、`biometric`、`audio` |
| `requiresFeature` | 需要先获得的 feature lease |

示例：

```json
{
  "sensor": "imu",
  "formats": [
    {
      "rateHz": 100,
      "encoding": "none",
      "dataType": "imu_6dof"
    }
  ],
  "privacyClass": "motion",
  "requiresFeature": "imu"
}
```

## Render Capability

```json
{
  "profile": "meiso_profile_0",
  "graphicsApi": "opengl_es_2_0",
  "maxTextures": 8,
  "maxMaterials": 32,
  "supported": true
}
```

`supported: true` 只表示 runtime 可以执行该 profile。资产是否合格由 asset validator 决定。

## Power Vector

功耗不是单个等级。每个 adapter 必须声明多维 `PowerVector`，每个维度使用 `uint8`，范围 `0..255`。

| Range | Band | Meaning |
|---:|---|---|
| `0` | off | 关闭 |
| `1..31` | sentinel | 常开哨兵、极低功耗 |
| `32..95` | low | 低采样、低带宽、短时唤醒 |
| `96..159` | interactive | 交互级，允许明显功耗 |
| `160..223` | rich | 高带宽或高刷新 session |
| `224..255` | debug | 调试、校准或临时 override |

标准维度：

| Dimension | Owner | Meaning |
|---|---|---|
| `computeLevel` | Edge runtime | CPU/GPU/VPU/M4 计算压力 |
| `sensorLevel` | Device manager | 传感器总体采集压力 |
| `cameraLevel` | Camera adapter | 分辨率、fps、曝光、ISP/encoder |
| `audioLevel` | Audio adapter | mic 数量、采样率、wake/audio stream |
| `displayLevel` | Display adapter | 亮度、刷新率、显示面积 |
| `renderLevel` | Renderer | 3D/HUD 复杂度和 redraw 频率 |
| `networkLevel` | Transport manager | Wi-Fi/BLE/low-power radio 活跃度 |
| `storageLevel` | Asset/log manager | 写入、缓存、replay 压力 |

Adapter 至少要给出：

```json
{
  "idleLevel": 0,
  "activeLevel": 96,
  "peakLevel": 191,
  "wakeLatencyMs": 30,
  "transitionCost": "medium",
  "estimatedMw": null
}
```

`estimatedMw` 可以未知，但 level 不能未知。未知功耗不能被当成低功耗。

## Degrade Rules

- Edge 可以返回 `degraded`，但必须说明 `reason` 和 `grantedParams`。
- 降级不能破坏 privacy 或 security policy。
- Host 必须按 `grantedParams` 工作，不能继续假设原请求已满足。
- Edge 可以因 thermal、battery、permission、transport 或 profile 限制拒绝请求。

## Open Questions

- Profile 0/1/2 的具体 triangle、texture memory、frame time budget 需要硬件测量后固定。
- 256 档 power level 与真实 mW 的映射需要按 adapter 实测校准。
- 低功耗 radio 的 payload 上限需要目标芯片确认后写入 transport capability。
