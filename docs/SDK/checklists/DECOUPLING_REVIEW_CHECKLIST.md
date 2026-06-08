# Decoupling Review Checklist

PR 合并前检查：

- [ ] `src/meiso_glass` 没有新增参考平台 token。
- [ ] generic config 没有新增 board/vendor/lab-only assumption。
- [ ] runtime 没有新增 concrete transport、process、probe 的直接依赖。
- [ ] 新硬件能力位于 adapter 或 platform profile。
- [ ] 新 adapter 有 mock/fake。
- [ ] 新协议字段有 fixture。
- [ ] 新 runtime 分支有 fake test。
- [ ] 新 config 字段有 schema 或遍历测试。
- [ ] 文档正文中文，文件名英文。
- [ ] wire payload、log field、metric name 使用英文。
