# CI/CD

CI/CD 的第一目标是保护 SDK contract，不是部署，也不是提前建设复杂发布系统。

当前只保留三类流程：

1. CI Gate
2. Release Gate
3. Hardware Validation

本地命令只是开发便利，不单独算一层 gate。

## 1. CI Gate

CI Gate 是日常唯一强制 gate，运行在 `pull_request` 和 `main` push 上。

当前检查：

- Python lint：`ruff check src tests`
- Python format：`ruff format --check src tests`
- Type check：`mypy src/meiso_glass`
- Unit tests：`pytest -q`
- Package smoke：build wheel、twine check、安装 wheel、运行 `meiso --help`
- Docs build：`npm ci && npm run docs:build`

当前实现文件是 `.github/workflows/ci.yml`。它可以拆成多个 job，但治理语义上仍然只算一个 CI Gate。

本地等价命令：

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

## 2. Release Gate

Release Gate 只在准备 tag 或正式发布时需要。现在不主动增加复杂发布流程。

后续真正发布前再补：

- API surface snapshot
- protocol fixture compatibility
- wheel install smoke
- version 和 changelog check

如果没有 release，就不新增 release-only job。

## 3. Hardware Validation

Hardware Validation 不放进普通 CI。它是手动验证记录，用来沉淀硬件事实。

建议 artifact：

- Host/Edge config
- serial log
- power measurement CSV
- protocol trace
- video/frame timing trace
- failure report

只有当硬件事实改变 SDK contract 时，结果才进入 bible 或 API spec。

## Complexity Rule

- 不因为“以后可能需要”新增 gate。
- 不把本地命令、PR、main、release 拆成多套重复制度。
- 不让硬件验证阻塞普通 SDK CI。
- 不在当前本机仓库处理部署服务器问题。
- 新增 gate 必须对应已经存在的 contract 风险、发布需求或反复出现的失败模式。

GitHub Pages workflow 目前只允许手动触发，因为 private repo 的当前 GitHub plan 不支持 Pages 自动部署。
