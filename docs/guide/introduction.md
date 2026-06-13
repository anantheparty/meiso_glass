# Introduction

Meiso Glass 是一个面向双设备 AR 眼镜系统的开放 SDK。这个 wiki 的目标不是写最终用户教程，而是把 SDK 的契约、边界、验证计划和实现进度放在同一个可浏览入口里。

SDK 当前围绕这些核心对象维护：

| 对象 | 说明 |
|---|---|
| `SystemProfile` | endpoint、SDC、host 组合后的系统装配声明 |
| `Capability` | SDK 判断能不能做某件事的入口 |
| `Session` | 所有持续行为的生命周期和状态机 |
| `Space` | head、display、camera、eye、world 的坐标关系 |
| `ViewSet` | mono、stereo、multiview、3D display 的视图集合 |
| `PresentationLayer` | HUD、status、video、AR overlay 等呈现层 |
| `PowerBudget` | session 请求侧的能量、功率、热、链路预算 |
| `PowerProfile` | adapter 在不同功耗等级下的成本和证据 |
| `Evidence` | admission、状态迁移、测量、错误和回放证据 |

## 这个 Wiki 维护什么

- SDK bible：当前唯一的设计主线。
- Validation：真机验证、bring-up、测量计划。
- Origin：原始硬件输入文档，只作为事实来源。

## 这个 Wiki 不维护什么

- 不维护多个互相竞争的 bible 版本。
- 不把板级 bring-up 文档当成 SDK contract。
- 不把 OpenXR、WebXR、render engine 或 BSP 文档复制成 SDK 说明。

## 推荐阅读顺序

1. [Architecture Map](./architecture-map.md)
2. [SDK Design Overview](/SDK/bible/SDK_DESIGN_OVERVIEW.md)
3. [SDK Subsystem Design](/SDK/bible/SDK_SUBSYSTEM_DESIGN.md)
4. [SDK Development Plan](/SDK/bible/SDK_DEVELOPMENT_PLAN.md)
5. [Maintenance Loop](./maintenance-loop.md)
