# 开发板验证

> 状态：当前验证计划。它约束实验，但不改变产品规范。

## 两种形式

| Aspect | Product | Board Validation |
|---|---|---|
| `Edge` | 穿戴设备嵌入式端 | i.MX8MM 开发板 |
| `Host` | 配套嵌入式计算端 | Jetson Orin Nano |
| `Link` | 最终自定义链路 | Wi-Fi adapter |
| Display | 直接呈现应用内容 | camera frame 与 overlay 合成，便于观察 |

开发板的 camera 背景合成只是可视化工具，不得进入产品数据流或产品验收定义。

## 操作系统边界

产品目标仍是 direct firmware 或 RTOS。当前开发板按实际 BSP 和驱动能力使用：

- i.MX8MM 的实时子域可运行 RTOS。
- camera、display 和 Wi-Fi 若暂时没有可用 RTOS 驱动，可由受支持的 A53 系统承担开发板验证。
- Orin Nano 的主要 CPU、GPU 和 accelerator 路径使用其受支持的 Host 系统；辅助 RTOS core 不能替代完整 `Host`。
- Linux process 不得被描述为 RTOS 实现。

可以单独进行 i.MX8MM A53 RTOS 网络 smoke test，用来测量未来移植缺口；它不证明 multimedia 已受 RTOS 支持。

## 首个闭环对象

| Object | Truth owner | Form | Current use |
|---|---|---|---|
| `CaptureIntent` | `Host` | `b` | camera/IMU 配置与 lease |
| `CameraFrame` | `Edge` | `d` | 按需或限流的完整帧 |
| `ImuObservation` | `Edge` | `a` | 带测量时间的 IMU sample 或 batch |
| `OverlayState` | `Host` | `b` | 指向源 frame 的 box、版本、坐标映射和 hide 状态 |

首个闭环不为了覆盖 `c` 而虚构输入事件。

连续实时视频不承诺每帧最终送达。它需要在测得 MTU、吞吐、延迟和缓冲限制后另定 stream profile。

## 数据流

```text
Edge CameraFrame + ImuObservation
  -> Link
  -> Host OverlayState
  -> Link
  -> Edge pose correction
  -> development-only preview composition
  -> Edge display
```

detector 精度不属于首个闭环；第一版只需要简单、确定且可复现的 box decision。

## 关联与时间

- 每个 camera frame 必须有跨重启不混淆的 `FrameKey`。它至少区分 `Edge` clock epoch、camera stream instance 和 frame sequence；具体 wire 编码后定。
- `OverlayState` 必须引用准确的源 `FrameKey`，不能按“最近收到的帧”猜测。
- box 使用校准后的源相机像素坐标。detector 若使用 crop、resize 或 distortion 空间，`OverlayState` 必须携带能还原到该坐标的映射。
- camera 与 IMU 的测量时刻必须映射到同一个 `Edge` monotonic epoch。驱动出队或网络到达时刻不能冒充测量时刻。
- camera timestamp 的曝光语义和硬件 clock 映射必须在接入真实驱动前声明，并记录 uncertainty。
- `Host` monotonic clock 是独立时钟域。没有 uncertainty 时不得直接与 `Edge` 时间比较。

## 姿态修正边界

`Edge` 使用源 `FrameKey/t_source`、目标背景 `FrameKey/t_target`、相机内参、camera-to-IMU 外参，以及 `orientation(t_source)` 到 `orientation(t_target)` 的相对旋转变换 box 四角。trace 必须同时记录源 frame 与目标背景 frame。若显示接口只接受轴对齐矩形，它只能绘制变换后四边形的包围框近似。

目标姿态是被合成背景 frame 的采集姿态，不是屏幕 scanout 时刻。若要修正到实际显示时刻，必须同时 time-warp 背景画面；这不属于首个闭环。

当前修正只承诺短时间旋转补偿，不修正：

- 相机平移造成的深度相关视差。
- 动态物体、遮挡和尺度变化。
- 未建模的镜头畸变或滚动快门。
- 未校准的 camera、IMU 或 display 外参。
- IMU 偏置、漂移造成的长期绝对姿态误差。

原始 IMU 不等于可靠 orientation。具体融合算法不进入当前公共 contract，但 `Edge` 必须提供带有效性和 uncertainty 的本地 `orientation(t)`；无法插值或预测时，不得声称完成修正。

## 执行顺序

1. 在不改变 boot/storage 的前提下确认两块板卡、接口、系统、恢复路径和日志基线。
2. 用 recorded camera 与 deterministic pose 在进程内 adapter 验证 object 所有权、关联、姿态数学、过期处理和有界 queue。
3. 保持 object 与业务逻辑不变，只把 adapter 换成双板 Wi-Fi。
4. 依次接入真实 camera、外接 IMU 和 display；每次只增加一个硬件依赖。
5. 注入 Host 延迟、断线、重启、丢包、旧版本和不完整 bulk，验证失败行为。

i.MX8MM 开发板当前没有集成 IMU。synthetic 或 recorded pose 只能验证协议与数学路径；完成真实 IMU 的时钟映射和外参标定后，才能声明硬件姿态修正成立。

## 完成条件

首个闭环完成必须同时满足：

- 软件黄金测试证明零旋转不改变四角，已知旋转的方向、矩阵顺序和结果在声明的像素容差内正确。
- 未知 `FrameKey`、错误 epoch、旧 `b` 版本、超龄 frame、过大 IMU 空洞、缺少 calibration 和不完整 `d` 都不会上屏，并产生确定的 drop reason。
- 同一 object 与业务代码先通过进程内 adapter，再通过 Wi-Fi adapter；切换 adapter 不改变 object 结构。
- 两块开发板 trace 能关联同一源 frame、Host overlay 版本、Edge 背景 frame 和最终修正结果。
- `Host` 实际消费 `Edge` camera 数据并返回 box，真实 IMU 能改变最终 box 姿态，结果可在开发板显示上观察。
- `Host` 延迟或断开不阻塞 `Edge` 的采集、显示和本地安全行为。
- 持续拥塞时内存与 queue 保持有界。
- 公开证据经过脱敏，camera 背景合成明确标为开发板辅助。

首轮先记录实际分布，不预设没有测量依据的性能数字、MTU、queue 深度或 timeout。
