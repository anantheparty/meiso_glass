# 0001 Core Wire Transport

## Status

Partially superseded by [0005 Core Wire Restructure](0005-core-wire-restructure.md).

0001 remains useful for the original decision to reject JSON envelope as Core Wire. The 28-byte header, generic flags, runtime payload codec and generic fragmentation model are no longer current.

## Context

早期 spec 把 wire message 写成 JSON envelope，并把 `ack`、`messageType`、`channel` 混在同一层。这不适合 Edge runtime、MCU、FPGA helper 或低功耗 radio。

Meiso core wire 的基本要求：

- 接收端先读固定长度二进制头，就能知道版本、长度、类型、flags 和 CRC。
- Core 层不解析 JSON field。
- Runtime 层再解析 JSON、CBOR、Protobuf、FlatBuffers 或 raw payload。
- Transport ack 不等于业务成功。
- Delivery class 定义异步投递语义，不定义业务 API。

## Decision

采用二进制 core frame：

```text
fixed_header[28] | header_extension[header_ext_len] | payload[payload_len]
```

固定头使用 byte offset。多 byte 整数使用 network byte order。

Core delivery class：

- `reliable_ordered`
- `unreliable_latest`
- `bulk_resumable`
- `tiny_control`

Transport ack 使用 `ack_range` TLV piggyback，不再作为 runtime `messageType`。

## External References

这些是借鉴对象，不是直接锁定依赖：

- [ENet Features](https://enet.bespin.org/Features.html)：借鉴 UDP 上的 multiple channels、reliable/unreliable、fragmentation、sequencing。
- [KCP README](https://github.com/skywind3000/kcp/blob/master/README.en.md)：借鉴轻量 ARQ/retransmission 思路。
- [QUIC RFC 9000](https://datatracker.ietf.org/doc/html/rfc9000)：借鉴 packet number、ack、stream/datagram 分层和拥塞控制边界。
- [QUIC DATAGRAM RFC 9221](https://datatracker.ietf.org/doc/html/rfc9221)：借鉴可靠 transport 中并存 unreliable datagram 的设计。
- [WebRTC DataChannel RFC 8831](https://datatracker.ietf.org/doc/html/rfc8831)：借鉴 reliable/unreliable、ordered/unordered channel 语义。
- [RTP RFC 3550](https://datatracker.ietf.org/doc/html/rfc3550)：借鉴实时媒体 sequence、timestamp、RTCP feedback 思路。
- [MAVLink Serialization](https://mavlink.io/en/guide/serialization.html)：借鉴轻量二进制 frame、message id 和 CRC 风格。
- [CoAP RFC 7252](https://datatracker.ietf.org/doc/html/rfc7252)：借鉴低频 control/confirmable message，但不采用其 REST 模型作为主实时链路。
- [CBOR RFC 8949](https://datatracker.ietf.org/doc/html/rfc8949)：作为 compact runtime payload 候选。
- [FlatBuffers](https://flatbuffers.dev/)：作为 Host/Edge 高性能 runtime payload 候选。
- [nanopb](https://jpa.kapsi.fi/nanopb/)：作为 MCU/firmware payload 候选。

## Consequences

- `docs/spec/wire-protocol.md` 不再描述 JSON envelope。
- Core frame size、offset、length 默认按 byte。
- bit 只用于 flags 内部位编号。
- 旧 `high_reliable/latest_wins/low_reliable/low_power` 命名被新的 delivery class 取代。
- 后续代码必须增加 binary golden vectors，避免跨语言实现漂移。

## Open Questions

- 是否直接采用 ENet-style implementation，还是仅借鉴其机制。
- `header_crc32c` 和 `body_crc32c` 是否足够，何时加入 AEAD/MAC。
- Low-power radio 的真实 MTU 需要硬件验证后固化。
- Runtime payload V0.1 是否先用 JSON debug payload，还是直接 CBOR/Protobuf。
