from meiso_glass.adapters.interfaces import StreamConfig
from meiso_glass.adapters.mock import MockCameraAdapter
from meiso_glass.core import Availability
from meiso_glass.core import Capability
from meiso_glass.core import CapabilitySpec
from meiso_glass.core import CapabilityStatus
from meiso_glass.core import Metadata
from meiso_glass.core import ResourceTier
from meiso_glass.core import Session
from meiso_glass.core import SessionRequest
from meiso_glass.core import SessionSpec
from meiso_glass.core import SessionState
from meiso_glass.core import ValidationState
from meiso_glass.power import PowerBand
from meiso_glass.power import PowerBudget
from meiso_glass.power import PowerCostPoint
from meiso_glass.power import PowerProfile
from meiso_glass.power import band_for_level
from meiso_glass.presentation import PresentationLayer
from meiso_glass.presentation import ViewSet
from meiso_glass.presentation import ViewSlot
from meiso_glass.runtime import AdmissionController
from meiso_glass.space import Pose
from meiso_glass.space import SpaceRelation


def test_power_level_bands_are_stable():
    assert band_for_level(0) == PowerBand.OFF
    assert band_for_level(32) == PowerBand.SENTINEL
    assert band_for_level(128) == PowerBand.LOW_STREAM
    assert band_for_level(224) == PowerBand.DEBUG_BOOST


def test_power_profile_selects_highest_allowed_level():
    profile = PowerProfile(
        profile_id="/power/camera/mock",
        adapter_id="camera_mock",
        family="camera",
        supported_levels=[0, 32, 64, 128],
        default_level=64,
        cost_points=[PowerCostPoint(level=level) for level in [0, 32, 64, 128]],
    )

    assert profile.select_level_at_or_below(95) == 64
    assert profile.select_level_at_or_below(None) == 64


def test_admission_rejects_declared_only_capability():
    capability = Capability(
        metadata=Metadata(id="/cap/display/primary/mono", owner_role="endpoint"),
        spec=CapabilitySpec(family="display", role_owner="endpoint"),
        status=CapabilityStatus(
            availability=Availability.AVAILABLE,
            validation_state=ValidationState.DECLARED,
        ),
    )
    session = Session(
        metadata=Metadata(id="sess_001", owner_role="sdc"),
        request=SessionRequest(idempotency_key="req_001", requester_role="sdc", intent="presentation"),
        spec=SessionSpec(session_type="presentation", requested_capabilities=[capability.capability_id]),
    )

    result = AdmissionController.from_lists([capability], []).admit(session)

    assert result.accepted is False
    assert result.session_status.state == SessionState.REJECTED
    assert result.steps[-1].step == "capability_usable"


def test_admission_accepts_mocked_capability_under_power_budget():
    capability = Capability(
        metadata=Metadata(id="/cap/camera/world/lowfi", owner_role="endpoint"),
        spec=CapabilitySpec(
            family="camera",
            role_owner="endpoint",
            resource_tier=ResourceTier(vision="lowfi", payload="tile"),
            power_profile_ref="/power/camera/lowfi",
        ),
        status=CapabilityStatus(
            availability=Availability.AVAILABLE,
            validation_state=ValidationState.MOCKED,
        ),
    )
    profile = PowerProfile(
        profile_id="/power/camera/lowfi",
        adapter_id="camera_lowfi",
        family="camera",
        supported_levels=[0, 32, 64, 128],
        default_level=64,
        cost_points=[
            PowerCostPoint(level=0),
            PowerCostPoint(level=32, expected_mw=2.0),
            PowerCostPoint(level=64, expected_mw=8.0),
            PowerCostPoint(level=128, expected_mw=80.0),
        ],
    )
    session = Session(
        metadata=Metadata(id="sess_002", owner_role="sdc"),
        request=SessionRequest(idempotency_key="req_002", requester_role="sdc", intent="lowfi_sensing"),
        spec=SessionSpec(
            session_type="lowfi_sensing",
            requested_capabilities=[capability.capability_id],
            power_budget=PowerBudget(max_power_level_u8=95, max_avg_mw=10.0),
        ),
    )

    result = AdmissionController.from_lists([capability], [profile]).admit(session)

    assert result.accepted is True
    assert result.session_status.state == SessionState.ADMITTED
    assert result.session_status.selected_power_levels[capability.capability_id] == 64


def test_presentation_and_space_contracts_model_mono_without_core_lock_in():
    viewset = ViewSet(
        viewset_id="/viewset/mono_primary",
        topology="mono",
        views=[ViewSlot(view_id="primary", display_space="/space/display/primary")],
    )
    layer = PresentationLayer(
        layer_id="hud_main",
        layer_type="hud",
        target_views=["primary"],
        surface_ref="/surface/hud/main",
    )
    relation = SpaceRelation(
        from_space="/space/display/primary",
        to_space="/space/head",
        timestamp_ns=1,
        pose=Pose(),
        confidence_level_u8=32,
    )

    assert viewset.primary_view().view_id == "primary"
    assert layer.layer_type == "hud"
    assert relation.to_space == "/space/head"


def test_mock_adapter_reports_power_profile_and_current_level():
    camera = MockCameraAdapter()
    idle_status = camera.get_status()
    running_status = camera.start_stream(StreamConfig(width=320, height=240, fps=5, format="RGB"))

    assert idle_status.current_level_u8 == 0
    assert running_status.current_level_u8 == 128
    assert camera.get_power_profile().family == "camera"
