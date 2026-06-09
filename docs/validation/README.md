# 真机验证计划

## 当前判断

MX8MM 当前预装 Android 9，只适合做硬件存在性确认，不适合作为长期 SDK reference path。原因是摄像头、显示、编码、Wi-Fi 和系统权限都会被 Android framework 和 HAL 包住；如果现在在 Android 9 上做完整 demo，之后换 Linux 或其它系统时很可能要重新做一遍。

因此当前验证顺序调整为：

1. 先确认恢复路径，再刷到更接近最终开发形态的 Linux 系统。
2. 在 Linux 上建立 MX8MM endpoint 与 SBC/Orin SDC 的真实 reference path。
3. 再做单摄像机到多 adapter、多链路、SDC 识别、结果回传、端侧显示重组的验证。

刷机不是为了追求某个发行版本身，而是为了让摄像头、显示、VPU、网络和进程模型尽早进入后续实际开发会继续使用的形态。

## 为什么原 demo-0 需要降级

原先的 demo-0 如果只在 Android 9 或纯 mock 环境里跑通：

- 能验证消息 envelope、`stream_id`、`frame_id`、ACK 和基本进程通信。
- 不能验证 MX8MM 摄像头真实采集路径。
- 不能验证 MX8MM VPU/软件编码路径。
- 不能验证屏幕 overlay 的真实显示路径。
- 不能验证 Linux 下后续 SDK adapter 的真实边界。
- 不能验证 Wi-Fi/以太网在真机上的吞吐、抖动和丢包。

所以它不能作为主验证路径。最多保留为刷机前的安全基线和工具链检查：确认两块板能互通、串口能恢复、U-Boot 可进入、当前系统信息可记录。它不能证明 SDK 的 reference path 成立。

## 刷机前必须保存的状态

刷机前要先记录：

- 当前 U-Boot 版本、启动日志和环境变量。
- 当前 eMMC 分区表和 Android 系统信息。
- 当前屏幕、摄像头、Wi-Fi、以太网、串口的可见状态。
- 当前 DIP/boot mode 设置。
- USB OTG 刷机通道是否能被主机识别。
- 是否有厂家恢复镜像、烧录工具和设备树源码。

验收标准：

- 能从串口进入 U-Boot。
- 能确认 USB OTG/Serial Downloader 或厂家烧录工具可用。
- 能说明刷坏后如何恢复。
- 能说明当前 Android 9 状态已经被记录，不依赖记忆。

## 刷机后目标系统

第一目标不是 Zephyr-only，而是 MX8MM A53 上的 Linux reference path：

```text
MX8MM A53: Linux, camera/display/network/VPU reference path
MX8MM M4: 后续作为 sentinel/wake/control 验证对象
SBC/Orin: Linux, inference/reference SDC
```

短期选择 Linux 的原因：

- 摄像头可以走 V4L2/media controller。
- 视频编码可以走 GStreamer、V4L2 M2M 或 BSP 提供的硬件编码路径。
- 显示可以走 DRM/KMS、Wayland 或板厂提供的显示栈。
- 网络和 Wi-Fi 调试路径更直接。
- SDK adapter 可以更接近未来真实实现。

Zephyr-only 可以作为长期低功耗目标继续研究，但不适合作为第一条摄像头、Wi-Fi、屏幕、识别闭环的验证路径。

## 视觉闭环验证目标

目标链路：

```text
MX8MM camera
  -> camera adapter
  -> frame/encode adapter
  -> link adapter
  -> SBC/Orin inference adapter
  -> detection result protocol
  -> MX8MM display/overlay adapter
```

只把识别结果传回 MX8MM：

```text
stream_id
frame_id
boxes
labels
scores
model_id
inference_latency_ms
```

MX8MM 端负责根据 `stream_id + frame_id` 把识别框和标签重新组合到显示画面上。不要依赖两台机器的系统时间来匹配结果；时间戳只用于延迟统计和日志关联。

## Adapter 矩阵

### Camera Adapter

- `mock_camera`：只用于协议和自动化测试。
- `file_replay_camera`：用于可重复输入。
- `v4l2_camera`：Linux 真机主路径。
- `android_camera_proxy`：只作为过渡，不作为长期主路径。

### Frame / Encode Adapter

视频可以压缩，而且必须把压缩格式作为 adapter 维度验证。

候选格式：

- `raw_yuv`：带宽大，但延迟和调试最直接。
- `jpeg` / `mjpeg`：实现简单，适合早期对比。
- `h264_rtp`：第一条重点压缩视频路径。
- `h265_rtp`：后续视 BSP/VPU 支持情况再验证。

第一阶段不追求最小码率，而是记录不同格式下的带宽、延迟、丢帧和重组正确性。

### Link Adapter

- `direct_ethernet`：第一条真机基线链路。
- `wifi_client`：MX8MM 和 SBC 接入同一 Wi-Fi。
- `wifi_ap_private`：后续模拟眼镜到 SDC 私有高速链路。
- `usb_rndis`：调试和恢复链路。

### Inference Adapter

- `mock_detector`：只用于验证协议闭环。
- `opencv_detector`：轻量真实检测路径。
- `orin_tensorrt_detector`：SBC/Orin 目标推理路径。

### Display Adapter

- `mock_overlay`：自动化测试。
- `drm_kms_overlay`：Linux 目标路径之一。
- `wayland_overlay`：Linux 用户态目标路径之一。
- `android_surface_overlay`：只作为过渡。

## 协议对象

### FrameRef

```text
session_id
stream_id
frame_id
source_role
source_capability
capture_timestamp_mono
width
height
pixel_format
encode_format
transport_adapter
payload_ref
```

`payload_ref` 可以是 RTP 序列、共享文件、ring buffer 位置或其它 adapter 定义的引用。SDK core 不应该假设图像一定在某种具体传输里。

### DetectionResult

```text
session_id
stream_id
frame_id
result_id
model_id
boxes
labels
scores
inference_latency_ms
received_timestamp_mono
```

`boxes` 使用归一化坐标，避免不同分辨率、裁剪和缩放导致协议变化：

```text
x_min
y_min
x_max
y_max
```

取值范围为 `0.0` 到 `1.0`。

## 验证阶段

### V0：刷机安全基线

目标：确认刷机可恢复，不把 Android 9 demo 当作 SDK 验证。

验收：

- 串口可进入 U-Boot。
- 当前系统、分区、设备状态已记录。
- USB OTG 或厂家工具刷机通道可确认。
- MX8MM 和 SBC 的直连网络可恢复。

### V1：Linux 系统 bring-up

目标：让 MX8MM 进入后续开发会继续使用的系统形态。

验收：

- Linux 可启动。
- 串口 shell 可用。
- 以太网可用。
- 摄像头节点可见。
- 屏幕可显示。
- 基础 GStreamer 或 V4L2 工具可运行。

### V2：单链路视觉闭环

目标：先用一条链路证明真实闭环。

建议路径：

```text
MX8MM v4l2_camera
  -> h264_rtp
  -> direct_ethernet
  -> SBC mock_detector 或 opencv_detector
  -> DetectionResult UDP
  -> MX8MM overlay
```

验收：

- 每个检测结果能关联回正确 `frame_id`。
- MX8MM 屏幕能显示对应识别框。
- 能记录端到端延迟、上行带宽、下行带宽、丢帧率。

### V3：多 adapter 对比

目标：验证 SDK adapter 边界，而不是只证明一条命令能跑。

对比维度：

- `raw_yuv` vs `mjpeg` vs `h264_rtp`。
- `direct_ethernet` vs `wifi_client` vs `wifi_ap_private`。
- `mock_detector` vs `opencv_detector` vs `orin_tensorrt_detector`。
- `mock_overlay` vs 真实显示 overlay。

验收：

- 替换 adapter 不需要改 core 协议对象。
- 测量项能按 adapter 分组记录。
- 某条链路失败时能返回结构化错误，而不是只在日志里报错。

### V4：功耗前置数据

目标：不在第一轮优化功耗，但不要丢失后续分析所需的数据。

记录：

- MX8MM CPU 使用率。
- 编码器/VPU 使用情况。
- Wi-Fi 速率、RSSI、重传或丢包。
- SBC 推理延迟。
- MX8MM 温度。
- 如果有电流表或电源日志，记录系统级功耗。

## 当前不做

- 不在 Android 9 上做完整 SDK reference path。
- 不在第一轮追求最低码率。
- 不在第一轮做 M4 常驻低功耗闭环。
- 不把厂家板级脚本写进 SDK core。
- 不把某一个 Wi-Fi 或摄像头驱动细节硬编码进协议。

## 当前结论

应该先刷机，但刷机前必须完成恢复路径确认和现状记录。刷机后的第一条有效验证不是“能不能跑一个 demo”，而是：

```text
真实摄像头输入
真实编码或帧格式 adapter
真实 endpoint-to-SDC 链路
真实 SBC 推理或可替换推理 adapter
真实检测结果协议
真实端侧显示重组
```

这条链路能验证 SDK 最关键的边界：camera、frame、link、inference、result protocol、display overlay，以及它们能否被 adapter 化替换。
