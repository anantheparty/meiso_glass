# Meiso Glass

Meiso Glass 是一套面向分体式 XR/AR 眼镜的开放系统契约。

- `Edge` 是穿戴设备端，拥有传感器、姿态、最终合成与显示安全。
- `Host` 是外部计算设备，运行业务与重计算，可以是 Linux、macOS 或其他受支持平台。

项目的目标不是绑定某一颗 SoC、图形 API 或无线方案，而是让应用、Host 与 Edge 围绕稳定契约独立演进。渲染后端、操作系统和 carrier 都是可替换实现。

当前仓库只验证一条有界的 C11 合成闭环：

```text
Edge camera + timestamped IMU
  -> Host overlay decision
  -> Edge pose correction
  -> Edge display
```

开发板上的 camera 背景合成只是可观察的验证工具，不是产品显示模型。仓库尚未实现生产 LinkSession、连续媒体或通用 Composition API。

## 进程内验证

当前实现使用固定容量进程内 adapter，不依赖 socket、Wi-Fi、Linux 或 RTOS。可复现路径使用 Visual Studio 2022 x64 Developer PowerShell、v143 toolset、Ninja 与 CMake 3.21 以上版本：

```powershell
cmake --preset windows-msvc-debug
cmake --build --preset windows-msvc-debug
ctest --preset windows-msvc-debug
```

demo 生成的 `build/slice_preview.ppm` 只是开发可视化，不是产品输出格式。

## 开发与迭代

`main` 只表示已经接受并验证过的基线。每个 work unit 与 PR 只回答一个范围明确的问题：

1. 从最新 `main` 开始；会改变可执行产品行为时，声明适用的 `Host-only`、`Edge-only` 或 `Integration` profile，涉及 Composition 时同时声明 layer source。
2. 行为或契约变化先修改最小权威文档与 fixture 预期；现有契约已经足够时直接引用，不制造空文档改动。
3. fixture 对本单元涉及的公开 contract 使用真实代际和失败语义，不建立只供 mock 使用的另一套接口。
4. 只实现当前问题，实际 build/run，并同时检查期望输出和失败行为；观察结果写回验证文档。
5. 合同变化按 `spec/acceptance -> fixture/test -> implementation/evidence` 组织；一个 PR 不混入无关清理。
6. PR 合入后切回本地 `main`，fetch origin，以 `--ff-only` 同步到 `origin/main`，确认两者同一 commit 并重跑基线，再开下一分支。

未达到晋级条件的 renderer、模型或 raw Wi-Fi 实验留在分支或私有实验记录中，不提前改变公开 contract。

## 文档

- [系统设计](docs/system.md)
- [Composition 契约](docs/composition.md)
- [链路契约](docs/link.md)
- [开发板验证](docs/validation.md)
- [文档入口](docs/index.md)
