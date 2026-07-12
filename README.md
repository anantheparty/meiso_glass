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

## 文档

- [系统设计](docs/system.md)
- [Composition 契约](docs/composition.md)
- [链路契约](docs/link.md)
- [开发板验证](docs/validation.md)
- [文档入口](docs/index.md)
