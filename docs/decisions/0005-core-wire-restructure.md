# 0005 Core Wire Restructure

## Status

Accepted for V0.1 spec drafting. Supersedes conflicting parts of [0001 Core Wire Transport](0001-core-wire-transport.md).

## Context

The earlier Core Wire draft correctly rejected JSON envelope as the low-level protocol, but it still allowed too much runtime and transport behavior to leak into Core Wire:

- runtime message names in `frame_type`.
- per-frame runtime codec and runtime version.
- generic flags for fragment, ack echo, retransmit, compression and encryption.
- object sequence, timestamp, priority, connection id and MTU hint as header/TLV fields.
- generic Core fragmentation before runtime chunk/hash semantics were defined.

This makes the embedded receiver harder to implement and harder to test. Edge C code and low-power helpers need a small decoder that can validate bytes without understanding business objects.

## Decision

Meiso V0.1 splits protocol responsibility:

| Layer | Responsibility |
|---|---|
| Core Wire | normal/tiny frame boundary, version, length, CRC, sequence, delivery class, minimal options |
| Transport Profile | reliability ownership, ordering, security source, link limits |
| Runtime Protocol | canonical runtime encoding and compact runtime IDs |
| Object Protocol | object id, interface id, opcode, lifecycle, async request/event |

Core Wire normal frame is reduced to a 20-byte fixed header:

```text
magic, version, frame_kind, delivery_class, option_len, payload_len, seq, header_crc32c, body_crc32c
```

Tiny frame is a separate 6-byte low-power layout:

```text
magic, version_kind, seq, payload_len, crc16
```

V0.1 removes generic Core fragmentation. Bulk transfer uses runtime chunks and content/hash validation.

## External References

These are references for design direction, not direct dependencies:

- [Wayland Protocol and Object Model](https://wayland.freedesktop.org/docs/html/ch04.html): object/interface/opcode dispatch and generated bindings.
- [QUIC RFC 9000](https://datatracker.ietf.org/doc/html/rfc9000): transport reliability, ordering and TLS boundary.
- [QUIC DATAGRAM RFC 9221](https://datatracker.ietf.org/doc/html/rfc9221): unreliable datagram path inside a QUIC connection.
- [CoAP RFC 7252](https://datatracker.ietf.org/doc/html/rfc7252): compact low-power control precedent, without adopting its REST model.
- [MAVLink Serialization](https://mavlink.io/en/guide/serialization.html): compact binary frame and checksum precedent.
- [ENet Features](https://enet.bespin.org/Features.html): UDP reliability/channel precedent, used only as a reference.

## Consequences

- `wire-protocol.md` no longer lists business runtime messages.
- Runtime payload V0.1 has one canonical encoding: `meiso_object_binary_v1`.
- JSON can be used for tooling/debug views, not peer wire compatibility.
- QUIC profile does not use Meiso ack/retry for QUIC stream reliability.
- C/Rust/Python implementations must share binary golden vectors.
- Future fields require a field proof: producer, consumer, failure without field, tiny behavior and golden test.

## Open Questions

- Whether two-byte normal magic is enough for noisy serial profiles must be verified with resync tests.
- Whether body CRC can be skipped on authenticated transports needs a later fixed convention; V0.1 keeps the field.
- Multiple reliable flows are not proven for V0.1; `flow_id` stays out until required by tests.
- Low-power radio frame limits remain hardware-validation data, not final product claims.
