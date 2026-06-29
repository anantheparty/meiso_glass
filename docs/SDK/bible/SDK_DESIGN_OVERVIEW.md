MEISO SDK V0.1 系统草案

1. 系统定位
   Host：业务逻辑、AI、物理、场景权威状态、资产生产。
   Edge：设备控制、数据采集、本地追踪、轻量渲染、显示与功耗管理。
   两者通过 Meiso Protocol 通信，不传 OpenGL 命令，不传引擎内部对象。
   Edge 不运行完整 Unity/Godot，只运行固定的 Meiso Edge Runtime。

2. 核心数据方向
   Host → Edge：
   a. Control：设备与传感器控制。
   b. Scene：3D 场景状态与资产引用。
   c. HUD：应用要求显示的 2D 内容。
   Edge → Host：
   a. 原始传感器流。
   b. Edge 本地处理后的结果。
   c. 输入、状态、性能和错误信息。

3. Edge Runtime
   3.1 Device Manager
       管理相机、麦克风、眼动、IMU、屏幕和无线模块。
       所有高功耗采集默认关闭。
       Host 通过显式请求开启，并指定参数和有效期限。
       设备可因温度、电量、权限拒绝或降级请求。

   3.2 Transport Manager
       管理 LoRa、BLE、Wi-Fi 的发现、建立、切换和恢复。
       对上层隐藏具体链路，只暴露逻辑消息通道。
       负责认证、加密、序号、重传、去重、时钟同步。

   3.3 Scene Replica
       保存 Host 权威场景在 Edge 上的可渲染副本。
       网络线程只能生成完整 Snapshot，不能直接修改正在渲染的数据。
       渲染线程始终读取最近一个完整且不可变的 Snapshot。

   3.4 Asset Cache
       保存 Mesh、Texture、字体、图标和简单动画。
       资产以 Content Hash 和版本号标识。
       场景消息只引用 Asset ID，不重复发送资产。
       缺少资产时显示占位内容，并异步请求下载。

   3.5 Tracking Service
       管理本地头部、眼动及其他低延迟姿态。
       姿态使用单调时间戳。
       最终视图姿态只由 Edge 本地决定，不经过 Host 往返。

   3.6 Micro Renderer
       使用 OpenGL ES 2.0。
       只支持 Meiso Render Profile 内规定的功能。
       不支持任意 Unity Shader、任意脚本和任意后处理。
       3D GPU 绘制场景；2D GPU 能否用于 HUD 合成由驱动验证决定。

   3.7 HUD Composer
       System HUD：电量、网络、权限、温度、错误、安全提示。
       App HUD：由 Host 提交的文字、图标、面板、进度和简单动画。
       固定顺序：3D Scene → App HUD → System HUD。
       System HUD 永远拥有最高显示优先级，应用不可遮挡。

   3.8 Frame Scheduler
       由 Edge 本地 VSync 驱动。
       永远不等待 Host 的“下一帧”。
       负责选择 Snapshot、预测姿态、渲染、合成和 Present。

   3.9 Policy Manager
       根据帧率、延迟、温度、电量和链路质量自动调整资源档位。
       策略默认由系统控制，SDK 仅提供偏好，不允许应用强制突破安全限制。

4. Host SDK
   4.1 Device API
       连接设备、查询能力、申请传感器、设置参数、关闭功能。

   4.2 Scene API
       创建和销毁实体。
       设置 Transform、Mesh、Material、可见性和动画状态。
       提交 Snapshot 或增量更新。

   4.3 HUD API
       创建 Text、Image、Panel、Progress、Anchor 和简单 Layout。
       设置层级、位置、生命周期和更新策略。

   4.4 Sensor API
       订阅 Camera、Audio、Eye、IMU 或本地处理结果。
       指定分辨率、频率、编码、数据类型和最长采集时间。

   4.5 Telemetry API
       获取温度、电量、帧率、丢帧、网络延迟、丢包、缓存和错误。

5. 网络逻辑通道
   5.1 Reliable Ordered
       用于控制、权限、创建/销毁实体、关键事件和状态切换。
       有序、可靠、独立队列，不得被资产传输阻塞。

   5.2 Unreliable Latest
       用于 Transform、速度、眼动、连续输入和实时遥测。
       每个对象独立序号；新数据到达后旧数据可直接丢弃。
       不因旧包丢失而阻塞新包。

   5.3 Bulk Resumable
       用于资产、日志、配置、非紧急数据库同步。
       可靠但可限速、暂停和断点续传。

   5.4 Tiny Control / Low-Power Profile
       运行于 LoRa 或 BLE。
       只支持唤醒、通知、状态查询、缓存内容 ID 和建立 Wi-Fi。
       不支持实时 3D Scene Stream 和大资产。

6. Meiso Core Wire
   Core wire 使用二进制 frame，不使用 JSON envelope。
   固定头只包含接收、长度、校验和底层传输需要的信息：
   magic
   version
   fixed_header_len
   flags
   frame_type
   header_ext_len
   total_len
   payload_len
   header_crc32c
   body_crc32c
   业务对象 ID、权限、参数和 JSON 字段只属于 runtime payload。
   所有会产生副作用的 runtime 操作都必须幂等；重复消息不得导致重复创建或重复执行。

7. 设备功能控制模型
    Host 发送 FeatureRequest：
   feature、模式、参数、优先级、leaseTime、requestId。
    Edge 返回 Accepted、Degraded 或 Rejected。
   Lease 到期或连接消失后，高功耗传感器自动关闭。
   Camera/Microphone/Eye 使用独立权限和明确状态指示。

8. 3D 场景最小模型
   EntityId
   ParentId
   Transform
   MeshId
   MaterialId
   Visibility
   AnimationState
   Lifetime
   ReplicationMode

9. Meiso Render Profile 0
   静态低多边形 Mesh。
   位置、旋转和缩放。
   Unlit Color 与 Unlit Texture。
   顶点色、透明混合、简单深度测试。
   固定数量纹理和材质。
   不支持动态阴影、任意 Shader、粒子和后处理。

10. Unity / Godot 工具链
    编辑器插件将引擎资产离线转换为 Meiso Asset Package。
    构建阶段检查多边形、纹理、材质、骨骼和内存预算。
    超出 Render Profile 的内容直接报错，不允许静默降级。
    运行时插件只发送 Meiso Entity 状态，不发送 GameObject 或 Node。

11. Edge 帧循环
    等待本地 VSync。
    读取最新完整 Scene Snapshot。
    根据目标显示时刻预测本地头部姿态。
    判断本帧是否需要 3D 重绘、仅 HUD 更新或复用缓存帧。
    绘制 3D Scene。
    绘制 App HUD。
    绘制 System HUD。
    提交显示缓冲。
    记录 CPU、GPU、帧时和丢帧指标。

12. 资源档位
    Compute C0：低频、无实时 3D。
    Compute C1：HUD 或轻量 3D。
    Compute C2：最高允许频率、完整实时岛。
    Network N0：LoRa，仅控制与通知。
    Network N1：BLE，控制和小数据。
    Network N2：Wi-Fi，实时状态和资产。
    Sensor S0：关闭。
    Sensor S1：低分辨率或低采样率。
    Sensor S2：高分辨率或高采样率。

13. 自动升级条件
    连续丢帧或 CPU 帧时超标：C0/C1 → C2。
    High Reliable 队首延迟超阈值：N0/N1 → N2。
    Latest Wins 丢包率或数据年龄超阈值：提高链路等级。
    Low Reliable 只在长期堵塞且电量允许时提升链路。
    降级必须使用更长滞回时间，避免频繁开关 Wi-Fi 和频率抖动。

14. 失效策略
    Host 暂时无新状态：继续渲染最近 Snapshot。
    实时状态过期：短时间预测，随后冻结或隐藏对象。
    Wi-Fi 断开：保留 System HUD，并尝试 BLE/LoRa 恢复。
    资产缺失：显示占位符，不阻塞整个场景。
    温度或电量过高：降低刷新、画质、传感器规格或关闭 3D。

15. V0.1 明确不做
    不兼容任意 OpenXR 本地应用。
    不在 Edge 运行完整 Unity/Godot。
    不支持远程 OpenGL 调用。
    不支持任意 Shader 和复杂本地物理。
    不允许网络线程阻塞显示线程。
