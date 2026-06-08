# Platform Acceptance Checklist

新增 platform profile 前检查：

- [ ] profile 位于 `configs/platforms/` 或后续约定目录。
- [ ] role 使用 `endpoint`、`sdc` 或 `host`。
- [ ] board/vendor 名只出现在 profile、adapter、reference docs。
- [ ] profile 通过 schema test。
- [ ] 对应 adapter 通过 contract test。
- [ ] health probe 不进入 core。
- [ ] video/audio/radio/power capability 明确声明。
- [ ] bring-up 文档写明网络、串口、权限、依赖。
- [ ] 不修改 generic example 以适配该平台。
