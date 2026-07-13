# 开发板验证

> 状态：当前验证计划。它约束实验，但不改变产品规范。

## 两种形式

| Aspect | Product | Board Validation |
|---|---|---|
| `Edge` | 穿戴设备端 | K230D 目标平台；到板前使用 i.MX8MM 临时验证代理 |
| `Host` | 外部计算设备 | Jetson Orin Nano |
| `Carrier` | 可替换 | 标准 Wi-Fi 与同链路 UDP/IP adapter |
| Display | Edge 最终合成与安全显示 | 按 source 分别验证；camera 背景只用于观察 |

开发板的 camera 背景合成只是可视化工具，不得进入产品数据流或产品验收定义。

## 独立验证

`Host` 与 `Edge` 不互相阻塞开发：

- Host-only profile 用确定的 Edge fixture 产生相同的 `CameraFrame`、`ImuObservation`、session 和异常输入，验证 Host 输出的 `CaptureIntent` 与 `OverlayState`。
- Edge-only profile 用确定的 Host fixture 产生相同的 intent、overlay、session 和异常输入，验证驱动、采集、本地姿态、显示与安全降级。
- fixture 只替代暂时缺席的 peer，不替代 Link 或业务 contract；接入真实 peer 时不得改变 object 和角色逻辑。

## 操作系统边界

Edge 操作系统与 compute domain 是平台选择，不属于产品契约。当前目标按以下边界接入：

- K230D 是目标 Edge SoC；具体板卡、runtime、toolchain、camera、display、IMU 与 Wi-Fi 接口必须从实机证据建立，不能由芯片名称推断。
- K230D 到板前，i.MX8MM 用作临时 Edge 验证代理。它的 A53 与 M4 只是 platform adapter 内部 compute domain，按当前 slice 所需的已验证 driver 与资源选择；Object、Composition、LinkSession 和 Edge 角色不得因此分叉。
- 当前 i.MX8MM 代理建立一个可启动、可恢复且经过验证的非 Android runtime。A53/M4 只按当前 slice 的 driver、资源、时延或隔离证据放置；板级镜像与 bring-up 记录留在私有实验室，不成为产品接口。
- 本项目消费一个已经可启动、可恢复的 K230D 开发基线，并验证其 platform adapter 与产品行为；系统镜像构建、刷写和发行不属于本项目。
- runtime、compute domain、driver 与硬件加速差异必须停留在 Edge platform adapter/HAL 后面，上层 Object、Composition 与 LinkSession 行为不随之改变。
- Orin Nano 的主要 CPU、GPU 和 accelerator 路径固定使用受支持的 Linux Host 环境；辅助 RTOS core 不承担完整 `Host`。
- Linux process 不得被描述为 RTOS 实现。

SoC 变更首先影响 Edge 的 decode、render、format、compositor、display 与资源边界；当前 Host-only、Object、时间、pose 数学和进程内 adapter 不因 K230D 而改写，但目标编译与资源占用仍需实证。i.MX8MM 可以验证 contract、fixture、carrier 与 platform-adapter 形状，不能替代 K230D 的目标编译、资源、driver、render 或性能证据。

目标内存、计算、格式和 buffer 预算，以及目标工具链编译与板上运行，都必须从选定 K230D 平台实证。x64、Orin 和旧目标的通过结果仍是功能与移植性证据，但不能代替目标证据。

## Composition source 验证

- `REMOTE_PROJECTION` profile 证明 Host 生成的 projection payload 能由 Edge 解码、按协商 profile 修正并进入最终显示。
- `EDGE_NATIVE` profile 证明 Host 的意图、状态与资源能驱动 Edge 在已声明能力内本地生成 layer。
- 每个 slice 只需验证它声明的 source；只有分别通过的 source 才能被报告为受支持。两种 source 可以共存，但不是两条 carrier。
- 当前 box/overlay slice 是 `EDGE_NATIVE` 方向的有界前置验证，不代表通用 `PresentationPlan` 或完整 renderer 已实现。

## 首个闭环对象

| Object | Truth owner | Form | Current use |
|---|---|---|---|
| `CaptureIntent` | `Host` | `b` | camera/IMU 配置与 lease |
| `CameraFrame` | `Edge` | `d` | 按需或限流的完整帧 |
| `ImuObservation` | `Edge` | `a` | 带测量时间的 IMU sample 或 batch |
| `OverlayState` | `Host` | `b` | 指向源 frame 的 box、版本、坐标映射和 hide 状态 |

首个闭环不为了覆盖 `c` 而虚构输入事件。

`CameraFrame(d)` 只验证按需或限流完整帧，不代表连续媒体。连续 camera 或 Projection 使用独立 [MediaStream](link.md#mediastream)，其资源参数等待真实链路测量。

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

1. 用 recorded camera 与 deterministic pose 在进程内 adapter 验证 object 所有权、关联、姿态数学、过期处理和有界 queue。
2. 在 Orin Linux 上用 Edge fixture 独立建立并验证 Host 环境、输入处理和 overlay 决策。
3. 记录 i.MX8MM 当前非 Android runtime、可恢复性与接口基线；平台准备作为私有实验室前置条件处理。
4. 用 Host fixture 在 i.MX8MM 上逐个验证 Edge platform adapter；先验证 compositor/display 边界，再接入 camera 与 pose source。A53/M4 放置不改变公开接口。
5. 对每个计划支持的 Composition source 分别完成 Edge-only profile；单侧缺失不阻塞另一侧工作。
6. 保持 Object、Composition 与业务逻辑不变，只把 fixture/进程内 adapter 换成 i.MX8MM 与 Orin 间的标准 Wi-Fi + 同链路 UDP/IP carrier adapter。
7. 在 i.MX8MM 上依次接入真实 camera、IMU 和 display；每次只增加一个硬件依赖，并注入 Host 延迟、断线、重启、丢包、旧版本和不完整 bulk。
8. 先测量 UDP reference profile；只有预先声明的延迟、功耗、CPU、丢包或调度指标显示明确收益时，才用同一 workload 验证 raw Wi-Fi adapter。
9. K230D 到板后，记录外部提供的板卡/runtime/toolchain、可恢复性与接口基线，并以相同 contract、fixture 和 workload 重跑目标编译、Edge-only 与 Integration profile；不在本项目内构建或刷写 K230D 系统镜像。

K230D 目标的具体板卡与传感器清单尚未记录；当前 i.MX8MM 板上也没有可直接充当产品 IMU 的已验证器件。synthetic 或 recorded pose 只能验证协议与数学路径；完成真实 IMU 的时钟映射和外参标定后，才能声明硬件姿态修正成立。

## 当前进程内 profile

首个可执行实现只选择当前闭环需要的内容：

- 核心使用可移植 C11；CMake 只负责本机 build/test，不属于产品接口。
- 进程内 adapter 使用调用者提供的固定容量 storage，单线程同步执行，不使用 heap、socket、OS API 或后台任务。
- adapter 只承载当前的 `CaptureIntent(b)`、`CameraFrame(d)`、`ImuObservation(a)` 与 `OverlayState(b)`：`b` 可替换待消费旧版本，`a` 可覆盖并计数丢失，`d` 必须完整复制或明确失败。
- `CaptureIntent` 携带 lease duration；Edge 在收到它时用本地 monotonic clock 形成 deadline。Host 的绝对时间不得直接当作 Edge deadline。
- 当前 adapter 的容量是测试输入，不是产品 queue/MTU profile；它只维护一个全局 active session，更高 generation 会原子取消全部 pending slot。正常 session loss 或任一 `b` 版本回绕都使用同一 end 行为：清空整个 adapter，在更高 generation 建立前拒绝所有 object，并让 Capture 停止、Edge 隐藏。该严格递增 generation 只验证进程内隔离，不是产品 LinkSession identity。完整 DeliveryHandle、恢复、wire、MediaStream 与 Composition 状态机尚未实现。
- synthetic frame 使用 `GRAY8`。Host 直接在原始 frame 坐标中用固定阈值找亮区包围框，所以当前 mapping 是 identity；以后若加入 crop、resize 或畸变校正，必须显式携带坐标 mapping。算法精度不是验收目标。
- demo 把修正后的四边形画到目标 frame 并写出 PPM。PPM 与 camera 背景都只是开发可视化。
- demo 的 Edge fixture 在发送前用本地、带 sequence/time 的恒定角速度 synthetic IMU sample 积分出已知 target orientation；Host 收到的副本只验证 Observation 关联，不参与 Edge 姿态生成。orientation 的支撑区间记录实际积分区间。该路径只用于把 Observation 与姿态数学接成确定测试，不是产品 IMU fusion。

数学坐标约定：camera 光学坐标为 `+X` 向右、`+Y` 向下、`+Z` 向前；`q_A_from_B=(w,x,y,z)` 是 Hamilton 主动旋转。姿态提供者给出 `q_W_from_I(t_source)`、`q_W_from_I(t_target)`，标定给出 `q_I_from_C`。静态源射线到目标 camera 的旋转为：

```text
q_Ct_from_Cs = inverse(q_I_from_C)
             * inverse(q_W_from_I(t_target))
             * q_W_from_I(t_source)
             * q_I_from_C
```

box 四角固定为 `TL, TR, BR, BL`。反投影和重投影使用同一组校准内参；目标射线不在 camera 前方时整块拒绝，不生成极大坐标或 NaN。超出画面的点由 demo rasterizer 裁剪，数学层不静默 clamp。

当前 calibration 显式绑定 camera stream instance 与 image geometry；数值有效但属于其他 stream/分辨率的内参必须拒绝。orientation 同时携带求值时间和支撑它的 IMU 时间区间，gate 分别检查 frame-to-pose 偏差与最大支撑空洞。

当前 gate 使用显式输入的测试 limits，不把数值写成产品默认值。它按 session、`b` 版本、完整 `FrameKey`、源/目标时间、完整 bulk、calibration、pose 有效性/间隔/支撑空洞/uncertainty、投影的顺序产生确定 drop reason。当前进程内 profile 用非零、严格递增的 session generation；复用或倒退的 generation 不得重置任何版本 gate。Edge 先 ingest 并保存当前 `OverlayState`，再可对多个 target frame 用新姿态重复 render。新的 `OverlayState` version 一经接收就先隐藏旧 overlay；即使该版本随后因 frame 或 pose 不能显示，也不得回退。该规则只属于当前 overlay slice；通用 `PresentationPlan` 保留旧 generation，直到新 generation 准备完成并原子激活。重复、旧版本或错误 session 不替换当前 candidate，hide 版本立即隐藏。接受新的 session generation 时必须显式隐藏旧显示；任一 `b` 版本回绕都视为 session fault，原子失效当前状态、进入安全的隐藏或停止采集状态，并要求使用更大的 generation 重新开始 session。

## 当前 i.MX8MM 代理闭环完成条件

当前代理闭环完成必须同时满足：

- Host-only profile 能从确定的 Edge fixture 输入产生精确关联的 overlay，并在 session loss、旧版本和不完整输入下给出确定失败。
- Edge-only profile 能从确定的 Host fixture 输入驱动当前 i.MX8MM 代理的同一平台接口，并在 Host 缺席或 session loss 时继续本地安全行为。
- 每个声明支持的 Composition source 都有独立可复现的 profile；不能用一个 source 的通过结果代替另一个。
- 软件黄金测试证明零旋转不改变四角，已知旋转的方向、矩阵顺序和结果在声明的像素容差内正确。
- 未知 `FrameKey`、错误 epoch、旧 `b` 版本、超龄 frame、过大 IMU 空洞、缺少 calibration 和不完整 `d` 都不会上屏，并产生确定的 drop reason。
- 同一 object 与业务代码先通过进程内 adapter，再通过 Wi-Fi + UDP/IP carrier adapter；切换 adapter 不改变 object 结构。
- i.MX8MM 与 Orin trace 能关联同一源 frame、Host overlay 版本、Edge 背景 frame 和最终修正结果。
- `Host` 实际消费 `Edge` camera 数据并返回 box，真实 IMU 能改变最终 box 姿态，结果可在开发板显示上观察。
- `Host` 延迟或断开不阻塞 `Edge` 的采集、显示和本地安全行为。
- 持续拥塞时内存与 queue 保持有界。
- 公开证据经过脱敏，camera 背景合成明确标为开发板辅助。

首轮先记录实际分布，不预设没有测量依据的性能数字、MTU、queue 深度或 timeout。

## K230D 支持声明

i.MX8MM 与 Orin 完成当前代理闭环，只证明契约、流程和代理平台路径成立，不构成 K230D 支持声明。K230D 支持必须由其目标编译、资源、driver、render、板上运行以及相同 profile/workload 的重跑证据单独建立。
