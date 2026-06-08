# ADR 0005: Chinese Docs English Contracts

## Status

Accepted

## Context

当前协作需要中文解释，但 SDK 未来面向开放生态和跨语言实现，wire payload、config、CLI、log、metric 必须可移植。

## Decision

解释性文档正文使用中文。文件名、目录名、wire payload、config key、CLI command、log field、metric name、error code 使用英文 ASCII。

## Consequences

贡献者阅读中文文档，机器契约保持英文。CI 会检查新增路径不含中文，并检查机器可读内容不含中文字符。
