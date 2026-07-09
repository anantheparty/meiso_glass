# Spec

本页定义 Meiso SDK V0.1 的初版 contract 形状。`SDK_DESIGN_OVERVIEW.md` 仍是唯一 bible；本页只把 bible 落成可开发、可测试的 spec。



## 命名

- `Host` 是业务和计算侧角色名。
- `Edge` 是设备和显示侧 runtime 角色名。
- 公开 CLI 使用 `meiso`，子命令使用 `host`、`edge`、`send`、`probe`。
- 公开类名前缀使用 `Meiso`，例如 `MeisoHost`、`MeisoEdgeRuntime`、`MeisoMessage`。

## Language Neutrality

本 spec 是语言中立 contract。示例使用 payload shape 或伪代码表达

实现分层原则：

| Layer | Preferred Implementation |
|---|---|
| Edge HAL / MCU firmware | C （非本篇内容）|
| Edge embedded runtime core | C |
| Host core runtime / transport / daemon | Rust or C++ |
| Host Full runtime SDK| Rust |
| CLI | Rust |

## 基本结构
Edge Core ↔ Host Core 底层双端通信协议，所有协议都会通过这里
Host Core ↔ Host Runtime Host层对Core的进一步封装
Host Core/Runtime ↔ CLI/Dashboard 本质是对Host的进一步封装

## 网络基本Core
1. meisoObject 是为了同步而存在的，一个meisoObject一定由单侧持有（truth），另一侧被同步
2. meisoObject分为4类
    a. 不带ACK的Object：如传感器数据，日志，电量。允许丢失
    b. 带ACK但是Last抢占的Object：如功能开关。需保证最后状态不丢失
    c. 带ACK的queue：如眼镜触摸屏或按键交互事件。需要有明确顺序，且所有不可丢失
    d. 带ACK的bulk object：如图片。允许分块发送，且必须完整送达
3. 每一次发送网络包允许携带X byte数据，多个Object的同步数据可以打包发送。同步内容过多时允许小buffer，再多了丢弃。保留顺序：c>b>a>d
4. 对于应用层来说，只有上述4种object可以使用，对于底层连接建立来说，还需拟定一个过程，利用链路层发现设备，建立连接，以及在重启重连的时候恢复状态。心跳包可以和NTP同步包共用，这样时间同步就在网络底层里了，还省一个心跳包
5. 主流接口返回各种object handle，object handle里有是否收到回包ack等内容

## 网络设计参考
比如传感器数据：
传感器本身是一个b object，由Host持有，Host修改b的参数或者开关，同步到Edge
Edge创建传感器的Data object，是一个a object，由Edge持有，并持续同步给Host直到本地的时钟超过传感器租约
开关传感器可以简化为：修改传感器租约到期时间，传一个过去的时间等于关闭
a object的创建也可以不带ACK，收到任意包直接创建
唯一需要注意的是，如果设备重启关机，需要完善的释放逻辑
核心设计点在于：网卡全部由meiso持有，不需要端口，不需要建立连接（每个应用不需要），允许合并 会话层，表示层和应用层和传输层 四层的数据
TCP UDP也不需要了
同时点到点传输不需要路由，网络层也扬了
3层网络结构
物理层
链路层
应用层
这样和linux也不沾边了

## 其余系统位置
开关系统功能： Host修改对应b object，Edge接收到包后响应ACK。接口返回object handle，查询object handle的状态就可以知道本次开关是否成功了送达了
系统电量，传感器数据，State：Edge持有对应的a object，持续传回给Host，Host无需回应Edge （a object 无ACK）
HUD，Render Profile：上层系统，基本上是由Host持有各种object然后传给Edge处理
功能开关，各种Flag：b object

## Q&A
Q:如果一个a object 或 b object塞不进一个网络包如何？
A:b object塞不进应该用bulk object。另外，这里叫object并不代表一定需要创建一个管理生命周期的object，也指代一种消息格式，特别是a object这种没有ACK的，我edge完全可以不存，传感器数据直接转成a object的数据丢出去。



## Spec Index

这些页面是当前 V0.1 contract 的专项 spec：

- [Wire Protocol](./wire-protocol.md)：主要讲具体怎么建立连接，打包object数据，接受后对buffer是如何处理的
- [Web Data Link Layer](./data-link.md)：主要是链路层如何处理网络包，如何建立连接，识别到目标设备
- [States](./states.md)：Host、Edge、link、Feature Lease、传感器、资产缓存状态。
- [Time Model](./time-model.md)：时钟同步、基于系统心跳包。
- [Frame Sync Mode](./frame-sync-mode.md)：帧同步模式和显示时序。
- [Sensor](./sensor.md)：传感器能力与采样接口。
- [Audio](./audio.md)：音频能力与音频链路。
- [HUD](./hud.md)：HUD 表达与合成边界。
- [Render](./render.md)：渲染能力和 profile 边界。


## Host Contract

Host 侧 contract 暂定五组接口：

| API | 责任 |
|---|---|
| `device` | 连接 Edge、查询能力、申请 feature、释放 feature |
| `scene` | 提交 `SceneSnapshot` 或后续增量更新 |
| `hud` | 提交 App HUD 的 text、image、panel、progress、anchor、layout |
| `sensor` | 订阅 camera、audio、eye、IMU 或 Edge 本地处理结果 |
| `telemetry` | 读取温度、电量、FPS、丢帧、网络、缓存和错误 |

伪代码：

```text
host = open_host_session("session-dev")

request = FeatureRequest {
  feature: "camera",
  mode: "stream",
  leaseTime: 5000,
  requestId: "req-camera-001"
}

host.device.request_feature(request)
```

## Edge Contract

Edge 侧不是普通应用 SDK，而是设备 runtime contract。Edge 负责接收 core wire、执行 policy、管理 feature lease、控制 adapter、维护 Scene Replica、合成 HUD、调度 frame、发布 telemetry。

Edge extension boundary 默认是 C ABI / C adapter。详细边界后续在 Edge runtime spec 中展开。

## Meiso Core Wire

Core wire 使用二进制 frame，不使用 JSON envelope。V0.1 分为 normal frame 和 tiny frame：

| Frame | 说明 |
|---|---|
| `normal` | 20-byte fixed header，承载 Object Protocol payload |
| `tiny` | 6-byte low-power header，承载 wake/status/probe 小包 |

Core Wire 不携带 runtime message name、payload codec、object id、timestamp 或权限字段。Runtime payload V0.1 使用 `meiso_object_binary_v1`。

## Delivery Classes

Logical channel 在 V0.1 改名为 delivery class。它是 core transport 的异步投递语义，不是业务 API 分类：

| Delivery Class | 用途 |
|---|---|
| `reliable_ordered` | 控制、权限、FeatureRequest、关键状态 |
| `unreliable_latest` | Transform、连续输入、实时遥测、最新状态 |
| `bulk_resumable` | 资产、日志、配置、replay |
| `tiny_control` | 唤醒、状态查询、缓存内容 ID、建立高速链路 |

Transport ack 不代表业务成功。业务成功或失败必须由 Object Protocol event 表达。

## FeatureRequest

Host 只能通过 `FeatureRequest` 显式开启 Edge 上的高功耗功能。

Wire payload：

```json
{
  "feature": "camera",
  "mode": "stream",
  "params": {},
  "priority": "normal",
  "leaseTime": 5000,
  "requestId": "req-camera-001"
}
```

Edge 只返回三类结果：

- `accepted`
- `degraded`
- `rejected`

`degraded` 和 `rejected` 必须带 `reason`。`accepted` 和 `degraded` 可以带 `leaseExpiresAt`。

## Scene API

最小实体模型：

- `EntityId`
- `ParentId`
- `Transform`
- `MeshId`
- `MaterialId`
- `Visibility`
- `AnimationState`
- `Lifetime`
- `ReplicationMode`

Scene message 只引用 asset ID，不内嵌 mesh、texture、font bytes。

## HUD API

Host 只能创建 App HUD。System HUD 属于 Edge runtime，应用不能遮挡。

固定合成顺序：

```text
3D Scene -> App HUD -> System HUD
```

## Sensor API

订阅字段包括：

- sensor 类型
- 分辨率
- 频率
- encoding
- data type
- max duration
- params

Camera、microphone、eye 使用独立权限和独立状态。
