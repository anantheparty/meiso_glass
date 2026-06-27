from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class Transform:
    position_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_xyzw: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass(frozen=True)
class SceneEntity:
    entity_id: str
    parent_id: str | None = None
    transform: Transform = field(default_factory=Transform)
    mesh_id: str | None = None
    material_id: str | None = None
    visibility: bool = True
    animation_state: str | None = None
    lifetime_ms: int | None = None
    replication_mode: str = "latest_wins"

    def asset_ids(self) -> tuple[str, ...]:
        return tuple(asset for asset in (self.mesh_id, self.material_id) if asset)


@dataclass(frozen=True)
class SceneSnapshot:
    snapshot_id: str
    session_id: str
    sequence: int
    entities: tuple[SceneEntity, ...]
    asset_refs: tuple[str, ...] = ()

    @classmethod
    def from_entities(
        cls,
        snapshot_id: str,
        session_id: str,
        sequence: int,
        entities: list[SceneEntity],
    ) -> SceneSnapshot:
        refs: list[str] = []
        for entity in entities:
            refs.extend(entity.asset_ids())
        return cls(
            snapshot_id=snapshot_id,
            session_id=session_id,
            sequence=sequence,
            entities=tuple(entities),
            asset_refs=tuple(dict.fromkeys(refs)),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "snapshotId": self.snapshot_id,
            "sessionId": self.session_id,
            "sequence": self.sequence,
            "assetRefs": list(self.asset_refs),
            "entities": [
                {
                    "entityId": entity.entity_id,
                    "parentId": entity.parent_id,
                    "transform": {
                        "position": entity.transform.position_m,
                        "rotation": entity.transform.rotation_xyzw,
                        "scale": entity.transform.scale,
                    },
                    "meshId": entity.mesh_id,
                    "materialId": entity.material_id,
                    "visibility": entity.visibility,
                    "animationState": entity.animation_state,
                    "lifetime": entity.lifetime_ms,
                    "replicationMode": entity.replication_mode,
                }
                for entity in self.entities
            ],
        }


@dataclass
class SceneReplica:
    _latest: SceneSnapshot | None = None

    def publish_complete_snapshot(self, snapshot: SceneSnapshot) -> None:
        self._latest = snapshot

    def latest_snapshot(self) -> SceneSnapshot | None:
        return self._latest


def immutable_snapshot_view(snapshot: SceneSnapshot) -> Mapping[str, Any]:
    return MappingProxyType(snapshot.to_payload())


def assert_scene_payload_uses_asset_ids_only(payload: dict[str, Any]) -> None:
    raw = repr(payload).lower()
    forbidden = ("meshbytes", "texturebytes", "fontbytes", "assetbytes")
    if any(token in raw for token in forbidden):
        raise ValueError("scene payload must reference assets by id, not inline bytes")
