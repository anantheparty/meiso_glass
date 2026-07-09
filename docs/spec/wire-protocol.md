# Wire 协议规范

## Basic Wire   Host Core ↔ Edge Core
把一个包发到另一端的手段，有可能会丢包
这里已经是抽象底层了，不考虑LoRA or WiFi or BLE 或者实际上是有线

基本包结构
| Offset | Size | Field | Type | Rule |
|---:|---:|---|---|---|
| 0 | 2 | `magic` | chat[2] | fixed `"MS"` |
| 2 | 1 | `version_kind` | uint8 | V0.1 = `1`|
| 3 | 1 | `seq` | uint8 | sequence |
| 4 | 1 | `seq` | uint8 | Xor Check |
| 5 | 2 | `payload_len` | uint8 | payload len byte |
payload should less than 65536Byte


## Meiso Net Queue