# 系统形式

> 状态：产品级权威规范。

## 目标

Meiso Glass 只解决两件事：

1. `Edge` 驱动设备、采集传感器并完成本地显示。
2. `Host` 消费 `Edge` 数据、完成较重处理，再把显示决策返回 `Edge`。

系统只有两个公开角色：

```text
Host <-> Edge
```

`Host Runtime`、CLI 和调试工具都只是 `Host` 上层的包装，不是新的系统角色。

## 产品形式

正式产品由两个嵌入式部分组成。

| Role | Owns |
|---|---|
| `Edge` | 驱动、传感器、采样时间、本地姿态、设备状态、显示合成和最终显示时机 |
| `Host` | 数据处理、应用逻辑和应用显示内容的决策 |

产品接口不依赖具体操作系统，也不依赖 Wi-Fi、TCP、UDP、Linux、Android 或某一种 RTOS。

正式穿戴设备直接呈现应用内容，不需要把内容与 camera 背景合成。

## 开发板验证形式

当前验证使用：

- i.MX8MM 开发板作为 `Edge`。
- Jetson Orin Nano 作为 `Host`。
- Wi-Fi 作为可替换链路的验证载体。
- USB 和串口只用于 bring-up、日志与恢复。

开发板可根据实际 BSP、驱动和 accelerator 支持使用不同操作系统。开发板验证形式不改变产品形式，详见[开发板验证](validation.md)。

## 首个数据流

1. `Host` 发布 sensor 配置及 lease。
2. `Edge` 配置硬件并产生带本地采样时间的 camera 与 IMU 数据。
3. `Host` 处理输入并发布 `OverlayState`。
4. `Edge` 根据本地姿态历史修正 overlay。
5. `Edge` 在本地显示时机完成呈现。

`Host` 决定应用内容；`Edge` 决定最终何时以及如何安全地显示。

## 所有权

每个被同步的值只有一个 truth owner。

- `Host` 拥有 sensor 配置、lease 和 `OverlayState`。
- `Edge` 拥有 sensor sample、实际设备状态、本地姿态和最终显示状态。
- 非 owner 只持有同步副本，双方不同时修改同一事实。

数据所有权与投递方式的关系由[链路契约](link.md)定义。

## 本地约束

- `Edge` 的采集和显示不得等待 `Host`。
- `Host` 延迟或断开时，`Edge` 继续执行本地时序和安全行为。
- 高功耗 sensor lease 过期、session 丢失或设备重启后，`Edge` 不得无限继续采集。
- 链路接收不得直接修改正在显示的数据；显示侧只读取一个完整状态。
- 姿态修正使用 `Edge` 本地姿态，不增加一次 `Host` 往返。

## 当前非目标

当前不定义：

- 通用应用平台或完整 SDK。
- Scene、Asset、HUD、AI、Policy 等通用子系统。
- 远程图形命令或引擎内部对象传输。
- 所有传感器和显示模块的完整接口。
- 没有开发板证据的性能数字、资源档位或自动策略。
