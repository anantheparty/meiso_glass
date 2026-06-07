# Language And Naming Rules

本文件固化语言和命名规则。

## 文件和目录

文件名、目录名必须使用英文 ASCII。允许：

- `SDK_BIBLE.md`
- `MESSAGE_PROTOCOL.md`
- `endpoint.generic.yaml`

禁止：

- 中文文件名
- 中文目录名
- 空格较多且难用于脚本的命名

当前仓库根目录已经叫 `meiso glass`，这是历史初始化结果。仓库内新增路径不再使用空格。

## 文档正文

解释性文档正文使用中文。代码标识、协议字段、配置 key、命令名保留英文。

## Machine Content

以下内容必须使用英文 ASCII 标识：

- JSON field
- binary packet field
- config key
- CLI command
- log field
- metric name
- error code
- session id
- role
- adapter capability
- transport payload

示例：

```json
{
  "type": "heartbeat",
  "src_role": "endpoint",
  "payload": {
    "video_running": true
  }
}
```

## 中文说明的位置

中文可以出现在：

- README
- docs
- 注释性说明
- 调研记录

中文不应出现在：

- wire payload
- fixture payload
- binary field name
- error code
- metric name
- CLI subcommand
