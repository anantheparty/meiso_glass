# Maintenance Loop

Web wiki 和 SDK 代码必须一起维护。任何新增设计都要回答：它是否需要 contract、mock、test、validation 记录。

## 常规流程

1. 先改三份 SDK bible 中对应章节。
2. 再落最小代码模型或 adapter contract。
3. 补 mock 或 fake 实现。
4. 补测试。
5. 运行文档构建和 Python 测试。
6. commit 并 push。

## 本地命令

```bash
npm run docs:dev
npm run docs:build
.venv/bin/python -m pytest -q
```

## 合并原则

- active SDK wiki 只使用 `docs/SDK/bible/SDK_*.md` 三份文件。
- 本地更新包和 zip 是输入源，不作为 active docs 提交。
- 原始硬件事实只有在改变 contract、profile、adapter、power 或 validation plan 时才进入 SDK bible。

## 下一批 SDK 改进

- 把 `AdapterStatus` 拆到更明确的 base contract。
- 让 mock endpoint 使用 `Session` 和 `AdmissionController`。
- 把 telemetry 增加 `adapter_power_state` 和 `presentation_frame_stats`。
- 给 `SystemProfile` 增加 YAML schema 或 fixture。
