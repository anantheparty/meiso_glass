# Development Environment

本机开发只需要 Python SDK 环境和 VitePress 文档环境。当前仓库不包含部署配置。

## Python

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
npm run docs:build
npm run docs:preview
```

```bash
npm run docs:ensure
npm run docs:watch
npm run docs:stop
```

dev server 绑定在 `127.0.0.1`，默认端口是 `5173`，用于本地预览。日常本地查看用 `docs:dev`；它使用 VitePress 原生文件监听，改动 `docs/` 后浏览器会热更新。`docs:ensure` 用于后台启动一次或确认本地文档站已启动；`docs:watch` 用于长期保活；`docs:stop` 只停止由 `docs:ensure` 启动并记录 pid 的后台服务。

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
