from __future__ import annotations

from dataclasses import dataclass, field

from .ai import MeisoAiApi
from .features import FeatureRequest
from .hud import HudUpdate
from .protocol import MeisoChannel, MeisoMessage, MeisoMessageType
from .scene import SceneSnapshot
from .sensors import SensorSubscription
from .telemetry import TelemetryReport


@dataclass
class MeisoDeviceApi:
    session_id: str
    sequence: int = 0

    def request_feature(self, request: FeatureRequest) -> MeisoMessage:
        self.sequence += 1
        return MeisoMessage.make(
            message_type=MeisoMessageType.FEATURE_REQUEST,
            channel=MeisoChannel.HIGH_RELIABLE,
            session_id=self.session_id,
            sequence=self.sequence,
            payload=request.to_payload(),
        )


@dataclass
class MeisoSceneApi:
    session_id: str
    sequence: int = 0

    def submit_snapshot(self, snapshot: SceneSnapshot) -> MeisoMessage:
        self.sequence += 1
        return MeisoMessage.make(
            message_type=MeisoMessageType.SCENE_SNAPSHOT,
            channel=MeisoChannel.LATEST_WINS,
            session_id=self.session_id,
            sequence=self.sequence,
            payload=snapshot.to_payload(),
        )


@dataclass
class MeisoHudApi:
    session_id: str
    sequence: int = 0

    def update(self, update: HudUpdate) -> MeisoMessage:
        self.sequence += 1
        return MeisoMessage.make(
            message_type=MeisoMessageType.HUD_UPDATE,
            channel=MeisoChannel.HIGH_RELIABLE,
            session_id=self.session_id,
            sequence=self.sequence,
            payload=update.to_payload(),
        )


@dataclass
class MeisoSensorApi:
    session_id: str
    sequence: int = 0

    def subscribe(self, subscription: SensorSubscription) -> MeisoMessage:
        self.sequence += 1
        return MeisoMessage.make(
            message_type=MeisoMessageType.SENSOR_SUBSCRIBE,
            channel=MeisoChannel.HIGH_RELIABLE,
            session_id=self.session_id,
            sequence=self.sequence,
            payload=subscription.to_payload(),
        )


@dataclass
class MeisoTelemetryApi:
    session_id: str
    sequence: int = 0

    def report(self, report: TelemetryReport) -> MeisoMessage:
        self.sequence += 1
        return MeisoMessage.make(
            message_type=MeisoMessageType.TELEMETRY_REPORT,
            channel=MeisoChannel.LATEST_WINS,
            session_id=self.session_id,
            sequence=self.sequence,
            payload=report.to_payload(),
        )


@dataclass
class MeisoHost:
    session_id: str
    ai: MeisoAiApi = field(init=False)
    device: MeisoDeviceApi = field(init=False)
    scene: MeisoSceneApi = field(init=False)
    hud: MeisoHudApi = field(init=False)
    sensor: MeisoSensorApi = field(init=False)
    telemetry: MeisoTelemetryApi = field(init=False)

    def __post_init__(self) -> None:
        self.ai = MeisoAiApi(self.session_id)
        self.ai.register_default_tools()
        self.device = MeisoDeviceApi(self.session_id)
        self.scene = MeisoSceneApi(self.session_id)
        self.hud = MeisoHudApi(self.session_id)
        self.sensor = MeisoSensorApi(self.session_id)
        self.telemetry = MeisoTelemetryApi(self.session_id)
