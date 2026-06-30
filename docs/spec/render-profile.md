# Render Profile Spec

Meiso Render Profile 定义 Device micro renderer 能渲染什么。它不是 Unity/Godot feature list，也不是 OpenXR runtime。

V0.1 只定义 Meiso Profile 0。Profile 1+ 不属于 V0.1 contract。

## 1. Common Rules

- Device 不接收 OpenGL command stream。
- Device 不运行完整 Unity/Godot。
- Scene message 只发送 entity state 和 asset reference。
- Asset cooker 必须在构建阶段验证 profile。
- 超出 profile 的资产必须报错，不能静默降级。
- Runtime 不得为了渲染缺失资产而阻塞 Frame Loop。

## 2. Meiso Profile 0

目标：最低可用 3D + App HUD，适合早期嵌入式硬件和 GLES2 路径。

| Area | Supported |
|---|---|
| Graphics API target | OpenGL ES 2.0 |
| Mesh | static low-poly mesh |
| Transform | position, rotation, scale |
| Material | unlit color, unlit texture |
| Vertex | position, normal optional, uv optional, vertex color optional |
| Transparency | alpha blend |
| Depth | simple depth test |
| Texture | fixed small texture budget |
| Material count | fixed small material budget |
| App HUD | text, image, panel, progress |

Profile 0 禁止：

- arbitrary shader
- material graph
- dynamic shadow
- lighting model beyond unlit preset
- particle system
- post-processing
- gameplay script on Device
- complex local physics
- collider/rigid body simulation
- skeletal animation
- video plane
- remote engine object
- inline mesh/texture/font bytes in scene message

## 3. Required Budget Fields

A concrete Device Profile 0 implementation MUST publish these budget fields before claiming Profile 0 compatibility:

| Field | Meaning |
|---|---|
| `maxEntities` | maximum visible scene entities accepted in one committed scene state |
| `maxTriangles` | maximum total visible triangles |
| `maxDrawCalls` | maximum draw submissions per frame |
| `maxTextureSizePx` | maximum width/height per texture |
| `maxTextureBytes` | maximum resident texture bytes for presentation |
| `maxTextures` | maximum resident textures |
| `maxMaterials` | maximum resident materials |
| `maxHudElements` | maximum App HUD elements |
| `targetFrameHz` | target local display cadence for Profile 0 path |
| `maxFrameTimeMs` | frame time budget for render + compose path |

If a field is unknown, the implementation cannot advertise a stable Profile 0 budget. It may run as an experimental profile only.

## 4. Asset Package Requirements

Asset package metadata MUST include:

```json
{
  "assetId": "asset:sha256:...",
  "targetProfile": "meiso_profile_0",
  "requiredFeatures": ["static_mesh", "unlit_texture"],
  "budgetUse": {
    "triangles": 1200,
    "textures": 1,
    "materials": 1,
    "textureBytes": 65536
  }
}
```

Validator MUST check:

- target profile
- feature allowlist
- forbidden feature denylist
- asset hash
- referenced texture/material count
- triangle count
- binary size
- texture memory estimate
- declared budget use against target Device Profile

## 5. Runtime Behavior

When a scene references an asset:

- If asset exists and validates against Profile 0, Device may render it.
- If asset is missing, Device emits asset-missing event and may use placeholder if the scene interface allows degraded presentation.
- If asset exceeds profile budget, Device rejects the scene commit or affected object.
- Device MUST NOT download, decode or validate large assets on the render thread.

## 6. Future Profiles

Profile 1+ may later add animation, atlas, video plane, lighting or richer material templates. They are not V0.1 contract and must not appear in V0.1 compatibility claims.
