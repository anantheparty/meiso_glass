# ADR 0004: Adapter Backed Hardware

## Status

Accepted

## Context

AR 眼镜生态会涉及 camera、display、radio、power、sensor、MCU、FPGA、storage、audio。直接在 runtime 写硬件逻辑会让 SDK 难以移植和测试。

## Decision

所有硬件能力必须通过 adapter interface 暴露。真实 adapter 和 mock adapter 共享同一 contract。

## Consequences

runtime 不直接知道硬件型号。新增硬件前必须先定义 contract，再实现 mock 和真实 adapter。
