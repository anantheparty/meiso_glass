# Testing Bible

本文件定义测试策略。硬件 bring-up 不能替代 SDK 契约测试。

## 测试层级

`unit-fast`：纯 Python，不访问网络、不启动真实进程、不依赖硬件。

`protocol-compat`：JSON golden fixtures、unknown field、bad magic、bad version、legacy payload、error path。

`telemetry-binary`：hex golden vector、CRC、byte order、payload length、unknown packet type、max payload。

`adapter-contract`：所有 mock 和真实 adapter 共用 contract suite。

`runtime-state`：fake transport、fake video、fake clock 驱动 EndpointAgent/SDCAgent。

`cli-contract`：stdout、stderr、exit code、argparse choices、timeout。

`profile-schema`：遍历 `configs/**/*.yaml`，校验 role、port、capability、平台隔离。

`architecture-fitness`：扫描核心源码和 generic config，阻止参考平台耦合回流。

`hardware-gated`：真实设备、串口、camera、display、radio、power meter，只在标记环境运行。

## PR 要求

- 改 protocol 必须加 fixture。
- 改 adapter interface 必须加 contract test。
- 改 runtime lifecycle 必须加 fake test。
- 改 config schema 必须遍历所有 profile。
- 修 bug 必须先写能失败的测试，除非是纯文档。
- 新硬件 adapter 必须先通过 mock parity，再接硬件测试。

## 测试数据

fixture 文件内容必须是英文 machine payload。中文解释写在 fixture README 或 docs 中，不写入 wire sample。

## 当前优先级

短期先补：

- runtime dependency injection
- protocol negative tests
- adapter contract tests
- config schema tests
- CLI contract tests
