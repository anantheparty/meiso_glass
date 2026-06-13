from __future__ import annotations

from dataclasses import dataclass, field

from ..core import Capability, Session, SessionState, SessionStatus
from ..power import PowerProfile


@dataclass(frozen=True)
class AdmissionStep:
    step: str
    result: str
    reason: str = ""
    evidence_ref: str | None = None


@dataclass(frozen=True)
class AdmissionResult:
    accepted: bool
    session_status: SessionStatus
    steps: list[AdmissionStep] = field(default_factory=list)


@dataclass
class AdmissionController:
    capabilities: dict[str, Capability]
    power_profiles: dict[str, PowerProfile]

    @classmethod
    def from_lists(cls, capabilities: list[Capability], power_profiles: list[PowerProfile]) -> "AdmissionController":
        return cls(
            capabilities={cap.capability_id: cap for cap in capabilities},
            power_profiles={profile.profile_id: profile for profile in power_profiles},
        )

    def admit(self, session: Session) -> AdmissionResult:
        steps: list[AdmissionStep] = []
        selected_levels: dict[str, int] = {}
        selected_caps: list[str] = []

        for capability_id in session.spec.requested_capabilities:
            cap = self.capabilities.get(capability_id)
            if cap is None:
                return self._reject(steps, "capability_exists", f"missing capability {capability_id}")
            steps.append(AdmissionStep("capability_exists", "pass", capability_id))

            if not cap.usable_for_admission():
                return self._reject(steps, "capability_usable", f"capability not usable {capability_id}")
            steps.append(AdmissionStep("capability_usable", "pass", capability_id))

            if cap.spec.power_profile_ref:
                profile = self.power_profiles.get(cap.spec.power_profile_ref)
                if profile is None:
                    return self._reject(steps, "power_profile_exists", f"missing power profile {cap.spec.power_profile_ref}")
                try:
                    level = profile.select_level_at_or_below(session.spec.power_budget.max_power_level_u8)
                except ValueError as exc:
                    return self._reject(steps, "power_level_select", str(exc))
                point = profile.cost_for_level(level)
                if not session.spec.power_budget.allows(point):
                    return self._reject(steps, "power_budget", f"power budget rejects {capability_id} at level {level}")
                selected_levels[capability_id] = level
                steps.append(AdmissionStep("power_budget", "pass", f"{capability_id}:{level}"))

            selected_caps.append(capability_id)

        return AdmissionResult(
            accepted=True,
            session_status=SessionStatus(
                state=SessionState.ADMITTED,
                selected_capabilities=selected_caps,
                selected_power_levels=selected_levels,
            ),
            steps=steps,
        )

    @staticmethod
    def _reject(steps: list[AdmissionStep], step: str, reason: str) -> AdmissionResult:
        new_steps = [*steps, AdmissionStep(step, "fail", reason)]
        return AdmissionResult(
            accepted=False,
            session_status=SessionStatus(state=SessionState.REJECTED, degradation_reason=reason),
            steps=new_steps,
        )
