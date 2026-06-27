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

dev server 绑定在 `127.0.0.1`，用于本地预览。

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
