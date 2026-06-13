from __future__ import annotations

from dataclasses import dataclass, field

from ..core.types import StringEnum, clamp_u8


class PowerBand(StringEnum):
    OFF = "off"
    RETENTION = "retention"
    WAKE_READY = "wake_ready"
    SENTINEL = "sentinel"
    SPARSE_CAPTURE = "sparse_capture"
    LOCAL_PROCESS = "local_process"
    LOW_STREAM = "low_stream"
    RICH_STREAM = "rich_stream"
    PEAK_STREAM = "peak_stream"
    DEBUG_BOOST = "debug_boost"


class MeasurementSource(StringEnum):
    DECLARED_ONLY = "declared_only"
    DATASHEET_ESTIMATE = "datasheet_estimate"
    DRIVER_COUNTER = "driver_counter"
    OS_POWERSTATS = "os_powerstats"
    RAIL_PROBE = "rail_probe"
    BENCH_FIXTURE = "bench_fixture"
    PRODUCT_CALIBRATED = "product_calibrated"


def band_for_level(value: int) -> PowerBand:
    value = clamp_u8(value)
    if value == 0:
        return PowerBand.OFF
    if value <= 15:
        return PowerBand.RETENTION
    if value <= 31:
        return PowerBand.WAKE_READY
    if value <= 63:
        return PowerBand.SENTINEL
    if value <= 95:
        return PowerBand.SPARSE_CAPTURE
    if value <= 127:
        return PowerBand.LOCAL_PROCESS
    if value <= 159:
        return PowerBand.LOW_STREAM
    if value <= 191:
        return PowerBand.RICH_STREAM
    if value <= 223:
        return PowerBand.PEAK_STREAM
    return PowerBand.DEBUG_BOOST


@dataclass(frozen=True)
class PowerLevel:
    value: int
    scheme: str = "u8"

    def __post_init__(self) -> None:
        clamp_u8(self.value)
        if self.scheme != "u8":
            raise ValueError(f"unsupported power level scheme: {self.scheme}")

    @property
    def band(self) -> PowerBand:
        return band_for_level(self.value)


@dataclass(frozen=True)
class UnitCost:
    uj_per_event: float | None = None
    uj_per_frame: float | None = None
    bytes_per_joule: float | None = None


@dataclass(frozen=True)
class PowerCostPoint:
    level: int
    adapter_state: str = "idle"
    settings: dict[str, object] = field(default_factory=dict)
    expected_mw: float | None = None
    peak_mw: float | None = None
    thermal_risk_u8: int = 0
    wake_latency_ms: float | None = None
    settle_latency_ms: float | None = None
    unit_cost: UnitCost = field(default_factory=UnitCost)
    measurement_source: MeasurementSource = MeasurementSource.DECLARED_ONLY
    confidence_level_u8: int = 0

    def __post_init__(self) -> None:
        clamp_u8(self.level)
        clamp_u8(self.thermal_risk_u8)
        clamp_u8(self.confidence_level_u8)


@dataclass(frozen=True)
class PowerTransition:
    from_level: int
    to_level: int
    wake_latency_ms_typ: float | None = None
    wake_latency_ms_max: float | None = None
    settle_latency_ms_typ: float | None = None
    requires: list[str] = field(default_factory=list)
    forbidden_when: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        clamp_u8(self.from_level)
        clamp_u8(self.to_level)


@dataclass(frozen=True)
class PowerProfile:
    profile_id: str
    adapter_id: str
    family: str
    supported_levels: list[int]
    default_level: int
    cost_points: list[PowerCostPoint] = field(default_factory=list)
    transitions: list[PowerTransition] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.supported_levels:
            raise ValueError("power profile must declare at least one supported level")
        for level in self.supported_levels:
            clamp_u8(level)
        clamp_u8(self.default_level)
        if self.default_level not in self.supported_levels:
            raise ValueError("default level must be in supported levels")

    def cost_for_level(self, level: int) -> PowerCostPoint | None:
        clamp_u8(level)
        for point in self.cost_points:
            if point.level == level:
                return point
        return None

    def select_level_at_or_below(self, max_level: int | None) -> int:
        if max_level is None:
            return self.default_level
        max_level = clamp_u8(max_level)
        candidates = [level for level in self.supported_levels if level <= max_level]
        if not candidates:
            raise ValueError(f"no supported level at or below {max_level}")
        return max(candidates)


@dataclass(frozen=True)
class PowerBudget:
    budget_id: str | None = None
    max_power_level_u8: int | None = None
    max_avg_mw: float | None = None
    max_peak_mw: float | None = None
    max_thermal_risk_u8: int | None = None
    max_wake_latency_ms: float | None = None
    max_session_duration_ms: int | None = None
    max_airtime_ms_per_s: float | None = None
    policy: str = "balanced"

    def __post_init__(self) -> None:
        if self.max_power_level_u8 is not None:
            clamp_u8(self.max_power_level_u8)
        if self.max_thermal_risk_u8 is not None:
            clamp_u8(self.max_thermal_risk_u8)

    def allows(self, point: PowerCostPoint | None) -> bool:
        if point is None:
            return True
        if self.max_power_level_u8 is not None and point.level > self.max_power_level_u8:
            return False
        if self.max_avg_mw is not None and point.expected_mw is not None and point.expected_mw > self.max_avg_mw:
            return False
        if self.max_peak_mw is not None and point.peak_mw is not None and point.peak_mw > self.max_peak_mw:
            return False
        if self.max_thermal_risk_u8 is not None and point.thermal_risk_u8 > self.max_thermal_risk_u8:
            return False
        if (
            self.max_wake_latency_ms is not None
            and point.wake_latency_ms is not None
            and point.wake_latency_ms > self.max_wake_latency_ms
        ):
            return False
        return True


@dataclass(frozen=True)
class MeasuredPowerPoint:
    point_id: str
    adapter_id: str
    level: int
    session_id: str | None = None
    rail_id: str | None = None
    settings: dict[str, object] = field(default_factory=dict)
    mw_avg: float | None = None
    mw_peak: float | None = None
    uj_per_event: float | None = None
    uj_per_frame: float | None = None
    sample_window_ms: int = 0
    measurement_source: MeasurementSource = MeasurementSource.DECLARED_ONLY
    confidence_level_u8: int = 0

    def __post_init__(self) -> None:
        clamp_u8(self.level)
        clamp_u8(self.confidence_level_u8)
