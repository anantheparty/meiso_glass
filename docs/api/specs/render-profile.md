# Render Profile Spec

Meiso Render Profile 定义 Edge micro renderer 能渲染什么。它不是 Unity/Godot feature list，也不是 OpenXR runtime。

## Common Rules

- Edge 不接收 OpenGL command stream。
- Edge 不运行完整 Unity/Godot。
- Scene message 只发送 entity state 和 asset reference。
- Asset cooker 必须在构建阶段验证 profile。
- 超出 profile 的资产必须报错，不能静默降级。

## Meiso Profile 0

目标：最低可用 3D + HUD，适合 V0.1 和早期硬件。

| Area | Supported |
|---|---|
| Graphics API | OpenGL ES 2.0 |
| Mesh | static low-poly mesh |
| Transform | position、rotation、scale |
| Material | unlit color、unlit texture |
| Vertex | vertex color |
| Transparency | alpha blend |
| Depth | simple depth test |
| Texture | fixed texture count |
| Material count | fixed material count |
| HUD | text、image、panel、progress、anchor、layout |

Profile 0 禁止：

- dynamic shadow
- arbitrary shader
- particle
- post-processing
- script
- complex local physics
- remote engine object
- inline mesh/texture/font bytes in scene message

当前代码基线：

| Limit | Value |
|---|---:|
| `maxTextures` | 8 |
| `maxMaterials` | 32 |

## Meiso Profile 1

目标：轻量交互场景。Profile 1 是后续目标，不是当前默认实现。

Profile 1 可以在 Profile 0 基础上增加：

- bounded transform animation
- texture atlas
- simple sprite sheet animation
- limited dynamic mesh update
- limited alpha sorting
- optional video plane
- larger material and texture budget

Profile 1 仍然禁止：

- arbitrary shader
- dynamic shadow
- full particle system
- post-processing chain
- gameplay script on Edge
- complex local physics
- engine-specific scene graph

## Meiso Profile 2

目标：更丰富但仍受限的本地 runtime。Profile 2 只能在硬件验证后启用。

Profile 2 可以考虑：

- material template library
- limited lighting model
- limited skeletal animation
- bounded particle preset
- offscreen composition layer
- richer video / camera overlay

Profile 2 仍然不是：

- full Unity runtime
- full Godot runtime
- arbitrary native OpenXR app
- arbitrary shader pipeline
- remote GPU command protocol

## Asset Validation

Asset package 必须声明：

```json
{
  "assetId": "asset:sha256:...",
  "targetProfile": "meiso_profile_0",
  "features": ["static_low_poly_mesh", "unlit_texture"],
  "budgets": {
    "textures": 2,
    "materials": 1,
    "triangles": null,
    "textureBytes": null
  }
}
```

Validator 必须检查：

- `targetProfile`
- feature allowlist / denylist
- asset hash
- referenced texture/material count
- binary size
- optional hardware-specific budget

## Open Questions

- Profile 0 triangle budget 未定，需要真机 frame time 和 thermal 数据。
- Profile 1/2 的 texture memory、video plane 和 animation budget 未定。
- HUD font rendering 是否完全在 GPU 或 CPU raster 后上传纹理，需要驱动验证。
