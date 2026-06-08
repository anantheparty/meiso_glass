# SDK 文档设计与维护评审

日期：2026-06-08

本文记录当前 SDK 文档体系中已经暴露出的具体设计问题和项目维护问题。本文不记录实验室本地敏感信息、串口路由、私钥、密码或临时网络地址。

## 总结

当前 SDK 文档的大方向是正确的：SDK core 应保持平台中立，明确 endpoint、SDC、host 三种角色，把板卡相关内容隔离到 profile、adapter 和 reference implementation 中，并把 i.MX8MM + Orin 作为参考路径，而不是永久绑定。

主要问题不是 SDK 过于抽象，而是文档还没有把这些抽象设计成可执行的工程契约。现在文档已经说明“哪些东西不能耦合”，但还没有充分说明“哪些契约是绑定的、哪些只是参考、哪些还是草案、硬件验证如何反向修正 SDK 设计、哪些维护门禁能阻止项目漂移”。

## 文档设计问题

### 1. 治理文档缺少优先级模型

仓库里有 bible、rule、checklist、ADR、architecture、guide、platform 等多类文档。这个结构有价值，但目前没有说明当文档互相冲突时以谁为准。

具体风险：

- `docs/SDK/bible/*` 看起来像稳定契约。
- `docs/SDK/architecture/SDK_ARCHITECTURE.md` 也像稳定契约。
- `docs/SDK/platforms/REFERENCE_PLATFORM_IMX8MM_ORIN.md` 是参考平台说明。
- `configs/platforms/*.yaml` 虽然是配置文件，但会影响测试和实际运行。

如果没有优先级，未来贡献者可以引用不同文档来支持互相矛盾的改动。

需要补充：

- 增加文档权威顺序，例如：
  1. ADR 记录已经接受的决策。
  2. bible 文档定义稳定契约。
  3. rules/checklists 作为评审门禁。
  4. architecture 文档解释结构。
  5. guides/platforms 文档提供操作参考。
- 每份主要文档都应声明状态：`draft`、`binding`、`reference` 或 `deprecated`。

### 2. 平台中立原则清楚，但 reference implementation 的责任不清楚

文档正确要求 SDK core 不依赖 i.MX8MM、Orin、LR2021、HM0360、GW1NZ 或某个 BSP。但项目仍然需要一条真实的 i.MX8MM + Orin reference path 来校验 SDK 设计。

具体风险：

- “平台中立”可能被误用为推迟真实硬件约束的理由。
- “只是参考实现”可能变成无人维护的旁支，无法证明 core API 是否合理。

需要补充：

- 增加 reference implementation 契约：
  - 可以位于 core 之外。
  - 必须只使用公开 SDK 契约。
  - 必须把验证结果反馈到文档和测试。
  - 当真实硬件证明抽象错误时，必须允许它推动 API 修改。

### 3. Runtime 契约没有定义 composition root

文档说硬件能力应放在 adapter 后面，但没有清楚定义 agent 如何由 transport、health provider、video runner、power reader、sensor adapter 和 platform probe 组合起来。

具体风险：

- runtime 代码可以直接创建 UDP socket、GStreamer process、文件日志和 Linux probe，同时仍声称自己是 adapter-backed。
- 测试可能只验证目录边界，却漏掉 runtime 的实际耦合。

需要补充：

- 增加 composition-root 规则：
  - core 定义协议、接口和状态机。
  - platform/reference 层创建具体 adapter。
  - CLI/systemd 入口选择 profile 并组装 runtime graph。
  - agent 接收依赖对象，而不是直接构造板卡或系统相关对象。

### 4. Control plane 缺少真正的命令状态机

消息文档定义了 UDP JSON envelope 和消息名，但还没有定义命令生命周期。

缺失内容：

- `command.name` 与 `msg_type` 的职责边界。
- `start`/`stop` 类操作的 `session_id`。
- UDP 重复命令的幂等键。
- ACK 关联和重复包处理。
- 结构化错误：`code`、`message`、`retryable`、`details`。
- timeout 与 retry 策略。
- capability negotiation。
- 版本兼容和扩展字段。

具体风险：

- `start_video`、`start_lowfi`、`display_session` 会逐渐变成不兼容的临时命令。
- UDP retry 可能重复启动 session 或造成状态分裂。

需要补充：

- 在继续增加命令类型前，先补 control-plane state-machine 文档。
- `ping`、`health` 可以是简单 request/response。
- video、lowfi、power mode、display、firmware 应按 session command 设计。

### 5. Adapter 文档覆盖面广，但契约不够硬

adapter 名称覆盖了正确方向：camera、display、video encoder、radio、power、M4、FPGA、sensor、storage、audio。但每类 adapter 的最小契约还不够明确。

缺失内容：

- capability discovery schema。
- 结构化 adapter error。
- 长时间运行操作的 session handle。
- 每类 adapter 必须输出的 metrics。
- real adapter 和 mock adapter 共享的 contract tests。
- 可能改变功耗状态或硬件状态的安全边界。

具体风险：

- adapter 退化成一组松散字典。
- mock adapter 与真实硬件 adapter 很快漂移。

需要补充：

- 为每个 adapter family 定义：
  - capabilities。
  - commands。
  - events。
  - error model。
  - required observability。
  - contract test cases。

### 6. Telemetry header 已有雏形，但 payload 治理太松

二进制 telemetry packet header 是一个好的起点。文档刻意不锁死 payload 编码，这对早期探索有利，但现在已经开始阻碍低功耗验证。

缺失内容：

- payload family version。
- 单位和坐标系 registry。
- sensor timebase 与同步规则。
- fragmentation 或最大包长策略。
- 面向 LR2021 的 airtime 和 payload budget。
- 每类 payload 的 golden binary vectors。

具体风险：

- `LOWFI_VISION`、`EYE_HINT`、`POWER_STATE`、`LINK_STATS` 只剩标签，payload 变成任意 bytes。
- M4、A53、FPGA、radio 的功耗和延迟结果无法横向比较。

需要补充：

- 保持 payload 可扩展，但先定义前四类 payload contract：
  - IMU sample。
  - Lowfi vision tile/ROI sample。
  - Eye hint tuple。
  - Power rail sample。

### 7. 功耗文档方向正确，但还不能直接执行

功耗基准文档列出了正确的 mode 和 metrics，但还没有定义可复现实验需要的日志 schema 和 adapter interface。

缺失内容：

- session record schema。
- rail 命名规则。
- meter source metadata。
- sampling rate 和时间同步要求。
- 必须记录的 start/stop events。
- 如何合并 A53、M4、radio、display、camera、VPU 和 rail samples。

具体风险：

- 功耗数据变成散落笔记，无法复核。
- 低功耗结论无法承受硬件变更。

需要补充：

- 增加机器可读 power session log format。
- `power_state` 应返回结构化 rail 与 mode 数据，而不是自由字典。

### 8. Platform profile 没有表达硬件能力状态

当前 platform YAML 主要定义 role、host、port 和 video 默认值，没有表达 reference platform 的 capability matrix。

缺失内容：

- OS/BSP family：Android、embedded Linux、Jetson Linux。
- network paths：direct Ethernet、Wi-Fi AP/client、USB gadget。
- video path capabilities：synthetic、V4L2、CSI、VPU、software encode。
- lowfi path status：absent、mock、M4、A53、FPGA、LR2021。
- power instrumentation status。
- M4 firmware 和 mailbox status。
- display path status。

具体风险：

- 一个 profile 只写了 IP 地址和 codec 字符串，却看起来像“平台已支持”。

需要补充：

- 增加 capability profile schema，并使用明确验证状态：
  - `not_present`
  - `planned`
  - `detected`
  - `smoke_tested`
  - `measured`
  - `blocked`

### 9. First-run 文档对真实 bring-up 不够具体

首次运行文档适合 generic Linux smoke test，但还不能覆盖真实双设备 bring-up。

缺失内容：

- host 到板子的部署路径。
- direct Ethernet 静态地址设置。
- network proof：link、IP、route、ping、UDP request/response、iperf。
- Orin 部署和 `tegrastats` 采集。
- Android endpoint 备选路径。
- log bundle 采集和 artifact 命名规则。

具体风险：

- 贡献者通过 localhost smoke test 后，误以为真实 endpoint/SDC 路径已经可用。

需要补充：

- 把 first-run 拆成：
  - 本机 smoke test。
  - Linux-to-Linux 双设备 smoke test。
  - reference Orin SDC setup。
  - reference i.MX8MM endpoint setup。
  - 如果 Android 仍在 scope 内，增加 Android endpoint bring-up 附录。

### 10. 文档没有定义 Done 标准

多份文档列出了目标，但项目缺少从 mock 到真实硬件的验收阶梯。

需要补充：

- 增加 staged readiness labels：
  - `S0`：只有文档。
  - `S1`：mock 通过。
  - `S2`：本机 smoke test 通过。
  - `S3`：双设备 Linux smoke test 通过。
  - `S4`：reference hardware 可检测。
  - `S5`：真实 video/control/telemetry 可运行。
  - `S6`：功耗与延迟已测量。

## 项目维护问题

### 1. 文档太多，但缺少 owner

当前文档体系已经足够大，需要明确维护责任，否则很快会出现过期文档。

需要补充：

- 在主要文档中增加元信息：
  - `owner`
  - `status`
  - `last_reviewed`
  - `applies_to`
  - `supersedes`

### 2. Checklists 尚未进入自动门禁

仓库里有检查清单，但测试主要验证文件存在和命名规则，还没有强制执行深层契约。

需要补充：

- 增加 CI 检查：
  - config schema validity。
  - protocol golden vectors。
  - telemetry golden vectors。
  - adapter contract tests。
  - CLI exit-code behavior。
  - core 中不得出现平台专有依赖。

### 3. 测试过于 happy path

现有测试有价值，但容易给出过强信心。它们主要验证对象能 round-trip、mock 能跑、路径命名合规。

需要补充：

- 增加 negative tests：
  - malformed UDP datagram 不能打死 agent。
  - unsupported protocol version 返回结构化错误。
  - unknown command 返回稳定 error code。
  - 重复 `start_video` 不能启动两个 session。
  - 缺少 required config 必须 fail loudly。

### 4. UTF-8 和 Windows 工作流需要明确政策

文档正文使用中文、路径使用英文是合理的。但 Windows PowerShell 输出可能因 code page 出现 mojibake。

需要补充：

- 文档化 UTF-8 期望。
- 优先使用保留 UTF-8 的命令。
- 自动化检查不要依赖控制台渲染出的中文。

### 5. Release readiness 没有绑定 reference hardware 状态

release checklist 还没有清楚要求 reference hardware 状态。对本项目而言，每个 SDK release 都应说明自己是 mock-only、Linux smoke-tested、Orin-tested、i.MX8MM-tested，还是 power-measured。

需要补充：

- 每次 release note 必须包含：
  - supported roles。
  - supported platform profiles。
  - hardware validation stage。
  - known blocked hardware paths。
  - power/latency measurement availability。

### 6. Public SDK 与 lab tooling 的边界不清

SDK 需要平台中立的公开契约，但项目也需要实际可用的实验室工具。两者应该分层，而不是假装 lab layer 不存在。

需要补充：

- 增加 `lab` 或 `reference` 层，放在 core 外：
  - host orchestration。
  - probe collection。
  - serial/SSH/ADB wrappers。
  - log bundle generation。
  - reference platform deployment。
- lab-local 敏感配置不得进入 remote 仓库。

## 近期推荐文档工作

1. 增加文档权威顺序和状态模型。
2. 增加 config schema 和 platform capability schema。
3. 增加 command/session state-machine 文档。
4. 补齐 adapter contract 细节和 contract-test 要求。
5. 定义前四类 telemetry payload contract。
6. 增加 power session log schema。
7. 拆分 first-run 文档：本机、双设备、Orin SDC、i.MX8MM endpoint。
8. 把 release readiness 与 validation stage 绑定。

## 非目标

- 不把实验室本地敏感信息、串口日志、私钥、密码或临时本地 IP 写入 remote 仓库。
- 不把 SDK core 硬编码到 i.MX8MM 或 Orin。
- 不等真实硬件全部完成后再设计 SDK 结构。目标是设计能经受硬件 bring-up 修正的契约，而不是回避契约设计。
