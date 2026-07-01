# Development Environment

本机当前只需要 Python prototype 环境和 VitePress 文档环境。Python 用于 mock、CLI、测试和上层验证，不代表 core SDK 语言选择。当前仓库不包含部署配置。

## Python Prototype

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

常用检查：

```bash
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src/meiso_glass
python -m pytest -q
```

## Docs

```bash
npm ci
npm run docs:dev
npm run docs:check-sidebar
npm run docs:build
npm run docs:preview
```

```bash
npm run docs:ensure
npm run docs:watch
npm run docs:stop
```

dev server 绑定在 `127.0.0.1`，默认端口是 `5173`，用于本地预览。日常本地查看用 `docs:dev`；它使用 VitePress 原生文件监听，改动 `docs/` 后浏览器会热更新。左侧侧栏由 `docs/` 文件树自动生成，页面标题来自 Markdown 一级标题；`docs:build` 会先运行 `docs:check-sidebar`，GitHub Pages 部署同样会执行这一步。`docs:ensure` 用于后台启动一次或确认本地文档站已启动；`docs:watch` 用于长期保活；`docs:stop` 只停止由 `docs:ensure` 启动并记录 pid 的后台服务。

## CLI

```bash
meiso --help
meiso host --config configs/examples/host.generic.yaml
meiso edge --config configs/examples/edge.generic.yaml
meiso probe
```

发送一个 feature request：

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
