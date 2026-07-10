# 链路契约

> 状态：产品级权威规范。

## 分层

公开模型只有三层：

```text
Application
Link
Physical
```

- `Application` 只使用同步对象。
- `Link` 负责对象投递、session 生命周期和链路资源。
- `Physical` 是 Wi-Fi、未来自定义链路、有线链路或其他载体。

Wi-Fi 是当前验证 adapter，不是应用接口。adapter 内部可以使用平台网络栈，但这些细节不得泄漏到 `Application`。

## Object

`Object` 是一种同步或消息形式，不要求对应 heap object，也不要求发送端长期保存它。

每个 `Object` 只有一个 owner。owner 持有 truth，另一端接收副本。

| Alias | Name | Semantics |
|---|---|---|
| `a` | `Observation` | 无 ACK、允许丢失；适合 sensor sample、日志和实时状态 |
| `b` | `LatestState` | 有 ACK；较新的版本取代较旧的待发送版本，最终状态不能静默丢失 |
| `c` | `OrderedEvent` | 有 ACK、保持顺序；链路已接受的事件不得静默丢失 |
| `d` | `Bulk` | 有 ACK；允许分块，但整体只能完整交付或明确失败、取消 |

`Observation` 可以采集后直接编码发送，不必建立长期对象。

无法按 `LatestState` 完整投递的数据必须改用 `Bulk`，不能截断。未完成校验的 `Bulk` 不得作为完整数据暴露给应用。

## 典型所有权

Sensor 控制使用两个方向：

```text
Host-owned LatestState
  sensor configuration + lease
  -> Edge

Edge-owned Observation
  sensor samples
  -> Host
```

显示决策通常是 `Host` 拥有的 `LatestState`；设备输入事件通常是 `Edge` 拥有的 `OrderedEvent`；首个验证中的限流完整 camera frame 使用 `Bulk`。

## 有界资源

多个 `Object` 更新可以共享一个 carrier packet，但所有 packet、queue 和重组资源都必须有界。

拥塞时的保留与准入顺序为：

```text
c > b > a > d
```

- `LatestState` 可以用新版本替换尚未发送的旧版本。
- `Observation` 可以在过期或拥塞时丢弃。
- `Bulk` 可以暂停，但不能阻塞更高优先级数据。
- `OrderedEvent` 无法继续接收时必须显式报告 backpressure、失败或 session fault。
- 不允许用无限 queue 掩盖链路能力不足。

该顺序不是允许 `Bulk` 永久饥饿的完整调度算法。具体 packet 大小、queue 深度、公平性和调度策略等待真实链路测量后由 adapter profile 定义。

## DeliveryHandle

发送 `LatestState`、`OrderedEvent` 或 `Bulk` 时，调用者应获得可观察投递状态的 `DeliveryHandle`，至少能够区分：

- 对端已确认接收。
- 旧版本已被新版本取代。
- 投递失败、取消或 session 已失效。

链路 ACK 只表示投递状态，不表示设备已经执行成功。需要业务结果时，由该结果的 truth owner 另行发布状态。

`Observation` 默认不创建需要等待的 `DeliveryHandle`。

## Link 责任

`Link` 统一拥有 adapter 和 session。应用不得自行拥有 socket、port 或 per-application connection。

`Link` 负责：

- 发现与 session 建立。
- session 关闭和 liveness。
- 重启与重连。
- 各 object 形式需要的确认、去重、重试和顺序。
- clock offset 与 uncertainty 的估计。

Heartbeat 可以同时携带时钟观测；这里不规定 NTP 或其他具体格式。

重连后：

- owner 重新发布仍然有效的 `LatestState`。
- 过期 `Observation` 不重放。
- `OrderedEvent` 和 `Bulk` 的保留或失败规则必须在对应 adapter 实现前明确。
- 旧 session 的状态不得继续被当成当前 truth。

## 时间

实时数据携带 sender 的 monotonic timestamp 和 clock epoch。同步精度未知时，上层不得把两端时钟当成同一个精确时间轴。

首个闭环的姿态修正只使用 `Edge` 本地时间关系，因此不以跨设备高精度同步为前置条件；跨端延迟分析仍需记录 offset uncertainty。

## Wire 约束

当前只规定 wire 必须：

- 有界且可版本化。
- 携带满足去重、乱序或丢失判断所需的 sequence 信息。
- 在读取 payload 前检查长度。
- 在分发前检测传输错误。
- 不把 carrier 暴露为应用契约。

当前不规定 header、field offset、endianness、checksum 算法、MTU、重传窗口或 byte layout。这些内容必须依据目标链路和接收端资源实测后再写。

## 验收条件

一个 `Link` adapter 合格需要证明：

- 替换 loopback、Wi-Fi 或未来自定义载体时，`Application` object 接口不变。
- 持续过载时内存保持有界。
- 在 session 有效且链路持续可用时，`LatestState` 收敛到最新版本；否则显式报告失败。
- `OrderedEvent` 不会静默缺失。
- `Bulk` 完整完成，或显式失败、取消。
- `Observation` 丢失不会阻塞后续数据。
- 断线、重启和时钟不确定性对上层可见。
