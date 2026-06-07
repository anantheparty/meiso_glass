# Reference Implementation Boundary

本文件定义 reference implementation 和 SDK contract 的关系。

## 定义

reference implementation 是为了证明 contract 可运行的一组实现。它可以非常具体，但不能反向定义 SDK contract。

当前 reference implementation 包括：

- UDP JSON control plane
- GStreamer H.264/RTP video smoke test
- generic Linux process probe
- mock endpoint
- mock sdc

当前 reference platform 包括：

- endpoint development board profile
- sdc development board profile
- lab network assumptions

## 规则

- reference implementation 可以出现在 adapter、script、platform profile、docs/platforms。
- core API 不得承诺某个 reference implementation 永久存在。
- core tests 测抽象 contract，reference tests 测具体 pipeline。
- 如果某个具体实现开始被多个平台共享，应先抽象为 port，再提升到 core。

## 迁移方向

短期需要把 runtime 中直接创建的 socket、process、probe 逐步迁移到 composition root。迁移期间保持 CLI 兼容，但新增测试必须优先测试 fake runtime。
