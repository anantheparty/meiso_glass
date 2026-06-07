# Protocol Change Checklist

改 control message 或 telemetry 前检查：

- [ ] 更新 protocol bible 或 format 文档。
- [ ] 明确兼容性：source、wire、semantic。
- [ ] 新字段是 optional，或明确 breaking change。
- [ ] unknown field 行为已定义。
- [ ] unknown enum/message type 行为已定义。
- [ ] error code 已登记。
- [ ] ACK payload 已定义。
- [ ] `seq`、`timestamp_ns`、`trace_id`、`session_id` 语义已定义。
- [ ] JSON golden fixture 已添加。
- [ ] binary telemetry hex vector 已添加。
- [ ] old endpoint/new sdc 和 new endpoint/old sdc 矩阵已更新。
