# Pipeline Design

Meiso SDK 的 CI/CD 分成五层。越靠前越快，越靠后越接近发布。

## 1. Local Gate

开发者本地必须能跑：

```bash
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src/meiso_glass
python -m pytest -q
npm run docs:build
```

本地 gate 的目标是快速发现格式、类型、contract test 和文档死链。

## 2. Pull Request Gate

PR 上必须跑：

- SDK unit tests
- protocol contract tests
- AI-native API contract tests
- docs build
- naming fitness

PR gate 不做发布，不上传硬件结果。

## 3. Main Branch Gate

`main` 上额外做 package smoke：

- build sdist/wheel
- `twine check`
- 安装 wheel
- `meiso --help`

这一步证明仓库源码可以被打成可安装 SDK。

## 4. Release Candidate Gate

后续发布前增加：

- API surface snapshot
- protocol fixture compatibility
- example package smoke
- generated docs artifact
- changelog 和 version check

这一步只在准备 tag 时跑。

## 5. Hardware Validation Gate

硬件验证不放进普通 CI。它应该是手动触发、带环境说明和 artifact 的 workflow。

建议 artifact：

- Host/Edge config
- serial log
- power measurement CSV
- protocol trace
- video/frame timing trace
- failure report

只有当硬件事实改变 SDK contract 时，结果才进入 bible 或 API spec。

## 当前 GitHub Actions

当前 `.github/workflows/ci.yml` 已覆盖：

- Python 3.10 到 3.13 matrix
- ruff
- mypy
- pytest
- package smoke
- docs build

后续应补：

- API surface snapshot
- protocol fixture snapshot
- docs link checker
- hardware validation manual workflow
