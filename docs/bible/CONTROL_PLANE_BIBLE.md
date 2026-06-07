# Control Plane Bible

本文件定义 control plane 的职责和边界。

## 职责

control plane 负责：

- heartbeat
- ping
- health
- command dispatch
- session start/stop
- power state
- firmware status
- log event
- crash report
- capability negotiation

control plane 不负责：

- bulk video bytes
- raw camera frames
- high-rate IMU stream
- model artifact transfer

这些数据应走 video plane、telemetry plane 或 storage plane。

## Transport

V0 使用 UDP JSON 只是开发便利，不是 SDK API 本身。public API 应面向 command、session 和 capability，而不是绑定 UDP。

后续 transport 可以包括：

- UDP JSON
- TCP
- Unix socket
- serial
- BLE
- low-power radio
- file replay
- in-memory fake transport

## Reliability

每个 command 都要显式定义：

- `seq`
- retry policy
- timeout
- duplicate handling
- ACK correlation
- error code

不可靠 transport 上的 retry 不得导致 `start_video` 这类 command 重复启动多个 session。
