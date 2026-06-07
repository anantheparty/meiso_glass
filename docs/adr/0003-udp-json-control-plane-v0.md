# ADR 0003: UDP JSON Control Plane V0

## Status

Accepted

## Context

早期 bring-up 需要简单、可抓包、可手写的控制面。UDP JSON 方便实验室调试和 PC mock。

## Decision

V0 control plane 使用 UDP JSON reference implementation。协议 envelope 仍独立于 UDP，public API 不应绑定 UDP。

## Consequences

UDP JSON 是第一实现，不是最终架构。后续 BLE、serial、TCP、low-power radio、file replay 必须能复用相同 message contract。
