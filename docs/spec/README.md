# Spec Index

V0.1 spec docs are derived from `docs/SDK/bible/SDK_DESIGN_OVERVIEW.md`.

Read in this order:

1. [`runtime-planes.md`](runtime-planes.md) — Control, Presentation and Data plane ownership.
2. [`sdk-surface.md`](sdk-surface.md) — stable Host-facing SDK surface.
3. [`render-profile.md`](render-profile.md) — Meiso Profile 0 render contract.
4. [`object-protocol.md`](object-protocol.md) — object/interface/opcode dispatch.
5. [`runtime-protocol.md`](runtime-protocol.md) — canonical runtime encoding.
6. [`wire-protocol.md`](wire-protocol.md) — optional Core Wire record wrappers.
7. [`transport-profile.md`](transport-profile.md) — link-specific reliability, security and limits.
8. [`wire-test-vectors.md`](wire-test-vectors.md) — binary compatibility vectors.

Guideline:

- product concepts live in runtime planes and SDK surface.
- object/runtime/wire/transport docs define carriage only.
- future profiles and manager names must not become public SDK surface without an explicit spec change.
