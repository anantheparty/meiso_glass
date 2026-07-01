# 渲染能力等级规范

Meiso Render Profile 定义 Device micro renderer 能渲染什么。它不是 Unity/Godot 功能列表，也不是 OpenXR runtime。

V0.1 只定义 Meiso Profile 0。Profile 1+ 不属于 V0.1 contract。

## 1. 通用规则

- Device 不接收 OpenGL command stream。
- Device 不运行完整 Unity/Godot。
- Scene message 只发送 entity state 和 asset reference。
- Asset cooker 必须在构建阶段验证 profile。
- 超出 profile 的资产必须报错，不能静默降级。
- Runtime 不得为了渲染缺失资产而阻塞 Frame Loop。

## 2. Meiso Profile 0

目标：最低可用 3D + App HUD，适合早期嵌入式硬件和 GLES2 路径。

| 范围 | 支持内容 |
|---|---|
| 图形 API 目标 | OpenGL ES 2.0 |
| Mesh | 静态低多边形 mesh |
| Transform | 位置、旋转、缩放 |
| Material | unlit color、unlit texture |
| Vertex | position，可选 normal、uv、vertex color |
| Transparency | alpha blend |
| Depth | simple depth test |
| Texture | 固定小纹理预算 |
| Material count | 固定小材质预算 |
| App HUD | text、image、panel、progress |

Profile 0 禁止：

- 任意 shader
- material graph
- dynamic shadow
- 超出 unlit preset 的 lighting model
- particle system
- post-processing
- Device 上的 gameplay script
- complex local physics
- collider / rigid body simulation
- skeletal animation
- video plane
- remote engine object
- scene message 中 inline mesh/texture/font bytes

## 3. 必需预算字段

具体 Device Profile 0 实现必须发布以下预算字段，才能宣称 Profile 0 兼容：

| 字段 | 含义 |
|---|---|
| `maxEntities` | 单次已提交 scene state 中允许的最大可见 entity 数 |
| `maxTriangles` | 最大可见三角形总数 |
| `maxDrawCalls` | 每帧最大 draw submission 数 |
| `maxTextureSizePx` | 单张 texture 最大宽高 |
| `maxTextureBytes` | presentation 可驻留 texture bytes |
| `maxTextures` | 可驻留 texture 数量 |
| `maxMaterials` | 可驻留 material 数量 |
| `maxHudElements` | 最大 App HUD 元素数量 |
| `targetFrameHz` | Profile 0 路径的目标本地显示节奏 |
| `maxFrameTimeMs` | render + compose 的帧时预算 |

如果字段未知，该实现不能宣称稳定 Profile 0 budget；只能作为 experimental profile 运行。

## 4. 资产包要求

Asset package metadata 必须包含：

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

Validator 必须检查：

- target profile
- feature allowlist
- forbidden feature denylist
- asset hash
- referenced texture/material count
- triangle count
- binary size
- texture memory estimate
- declared budget use against target Device Profile

## 5. Runtime 行为

当 scene 引用某个 asset 时：

- asset 存在并通过 Profile 0 验证时，Device 可以渲染它。
- asset 缺失时，Device 发出 asset-missing event；如果 scene interface 允许 degraded presentation，可以使用 placeholder。
- asset 超出 profile budget 时，Device 拒绝 scene commit 或拒绝受影响对象。
- Device 不得在 render thread 上下载、解码或验证大型 asset。

## 6. 后续 Profile

Profile 1+ 可以在以后加入 animation、atlas、video plane、lighting 或更丰富的 material template。它们不属于 V0.1 contract，也不得出现在 V0.1 兼容性声明中。
