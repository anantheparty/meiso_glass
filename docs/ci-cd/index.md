# CI/CD

CI/CD 的第一目标是保护 SDK contract，不是部署。当前仓库仍处于 V0.1 contract 建设阶段，所以 pipeline 必须优先回答：API 是否漂移、协议是否破坏、文档是否还跟唯一 bible 对齐。

## 当前 Gates

- Python lint：`ruff check src tests`
- Python format：`ruff format --check src tests`
- Type check：`mypy src/meiso_glass`
- Unit tests：`pytest -q`
- Package smoke：build wheel、twine check、安装 wheel、运行 `meiso --help`
- Docs build：`npm ci && npm run docs:build`
- Naming fitness：禁止历史 public role 和旧 CLI 进入 active SDK

## 本地等价命令

```bash
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src/meiso_glass
python -m pytest -q
python -m build
python -m twine check dist/*
npm ci
npm run docs:build
```

## 约束

CI 不刷硬件，不发布包，不自动部署 Pages。真实硬件验证先写成 development validation，再决定是否进入 SDK contract。

GitHub Pages workflow 目前只允许手动触发，因为 private repo 的当前 GitHub plan 不支持 Pages 自动部署。
