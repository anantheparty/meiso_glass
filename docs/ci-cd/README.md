# CI/CD

当前 CI 目标是保护 SDK contract，不做部署。

## Gates

- Python lint：`ruff check src tests`
- Python format：`ruff format --check src tests`
- Type check：`mypy src/meiso_glass`
- Unit tests：`pytest -q`
- Package smoke：build wheel、twine check、安装 wheel、运行 `meiso --help`
- Docs build：`npm ci && npm run docs:build`
- Naming fitness：禁止旧 public role 和旧 CLI 进入 active SDK

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

CI 不发布包、不部署文档、不刷硬件。真实硬件验证先写成 development validation，再决定是否进入 SDK contract。
