# Meiso Glass

Meiso Glass 是一个面向双设备 AR 系统的 Meiso Host/Edge SDK 骨架。

Host 负责业务逻辑、AI、物理、场景权威状态和资产生产。Edge 负责设备控制、数据采集、本地追踪、轻量渲染、显示和功耗管理。两者通过 Meiso Protocol 通信，不传 OpenGL 命令，不传引擎内部对象。

## 当前范围

- Meiso Protocol：binary core frame、delivery class、payload length 和 CRC 校验。
- Host contract：Device、Scene、HUD、Sensor 和 Telemetry。
- Edge Runtime：FeatureRequest lease、Scene Replica、HUD 合成顺序、Frame Scheduler contract。
- Render Profile 0：OpenGL ES 2.0 的最小可移植渲染约束。
- Mock 和 reference path：用于本机开发，不定义最终硬件绑定。

## 安装

当前仓库里的 Python 包是 prototype、mock、CLI 和本机验证 harness，不代表 core SDK 必须用 Python 实现。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## 本地冒烟测试

终端 A：

```bash
meiso host --config configs/examples/host.generic.yaml
```

终端 B：

```bash
meiso edge --config configs/examples/edge.generic.yaml
```

终端 C：

```bash
meiso send \
  --host 127.0.0.1 \
  --port 42001 \
  --session-id session-dev \
  --feature camera \
  --mode stream \
  --request-id req-camera-001 \
  --lease-ms 5000
```

## 本地 Wiki

本仓库使用 VitePress 维护 `docs/` 下的 Web wiki。它只用于本地预览和静态构建验证，不包含部署配置。

```bash
npm install
npm run docs:dev
npm run docs:build
```

日常本地查看用 `npm run docs:dev`。需要后台启动一次时用 `npm run docs:ensure`；需要长期保活时只运行 `npm run docs:watch`。改动 `docs/` 后浏览器会热更新。左侧侧栏由 `docs/` 文件树自动生成，页面标题来自 Markdown 的一级标题。

## 项目结构

```text
src/meiso_glass/        当前 Python prototype / mock / CLI 包
configs/examples/       平台中立示例配置
configs/platforms/      板卡专用上电调试 profile
scripts/                可移植的开发/探针/视频冒烟脚本
docs/                   Web wiki、唯一 bible、spec、标准、开发和 CI/CD 文档
systemd/                通用 service 模板
tests/                  聚焦 SDK 契约的测试
```

当前 Python prototype 优先使用 `meiso_glass.api.MeisoHost`。正式 core wire、Host runtime 和 Edge runtime 不以 Python API 作为 contract。

## 文档

- [文档索引](docs/README.md)
- [SDK 文档索引](docs/SDK/)
- [唯一 SDK bible](docs/SDK/bible/SDK_DESIGN_OVERVIEW.md)
- [Spec](docs/spec/)
- [Coding Standard](docs/standards/coding-standard.md)
- [Development Environment](docs/development/environment.md)
- [CI/CD](docs/ci-cd/)

## 硬件上下文

实验室候选硬件是 bring-up 目标，不是 SDK 约束。硬件差异必须通过 adapter、profile 和 validation evidence 表达，不能进入核心 API。
