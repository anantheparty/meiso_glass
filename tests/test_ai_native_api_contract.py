import pytest

from meiso_glass.ai import (
    AiToolKind,
    AiToolResultStatus,
    ContextItem,
    ContextKind,
    MeisoAiApi,
    StatePatch,
    ToolCall,
    ToolResult,
    ToolSpec,
)
from meiso_glass.api import MeisoHost
from meiso_glass.protocol import MeisoChannel, MeisoMessageType


def test_host_exposes_ai_native_tools_context_and_state():
    host = MeisoHost(session_id="session-ai")

    tool_names = {tool.name for tool in host.ai.tools.list_tools()}

    assert "meiso.device.request_feature" in tool_names
    assert "meiso.scene.submit_snapshot" in tool_names
    assert "meiso.hud.update" in tool_names
    assert host.ai.context
    assert host.ai.state


def test_ai_tool_specs_require_meiso_prefix_and_capture_channel_policy():
    spec = ToolSpec(
        name="meiso.scene.submit_snapshot",
        kind=AiToolKind.SCENE,
        description="Submit scene.",
        channel=MeisoChannel.LATEST_WINS,
    )

    assert spec.channel == MeisoChannel.LATEST_WINS
    with pytest.raises(ValueError, match="prefix"):
        ToolSpec(name="scene.submit_snapshot", kind=AiToolKind.SCENE, description="bad")


def test_ai_tool_call_and_result_are_explicit_and_traceable():
    call = ToolCall(
        call_id="call-1",
        tool_name="meiso.device.request_feature",
        arguments={"feature": "camera"},
        idempotency_key="req-1",
        context_refs=("ctx-session",),
        state_refs=("state-session",),
    )
    result = ToolResult(call_id=call.call_id, status=AiToolResultStatus.OK, payload={"accepted": True})

    assert call.idempotency_key == "req-1"
    assert result.payload["accepted"] is True
    with pytest.raises(ValueError, match="error"):
        ToolResult(call_id="call-2", status=AiToolResultStatus.ERROR)


def test_context_packet_compacts_by_priority_and_ignores_expired_items():
    ai = MeisoAiApi(session_id="session-ai")
    ai.tools.register(ToolSpec(name="meiso.context.query", kind=AiToolKind.CONTEXT_QUERY, description="Query context."))
    ai.context.put(ContextItem("low", ContextKind.SESSION, {"text": "low"}, priority=1))
    ai.context.put(ContextItem("high", ContextKind.SCENE, {"text": "high"}, priority=10))
    ai.context.put(ContextItem("expired", ContextKind.POLICY, {"text": "old"}, priority=99, expires_at_ns=5))

    packet = ai.context.packet("session-ai", now_ns=10).compact(max_items=1)

    assert [item.context_id for item in packet.items] == ["high"]


def test_state_patch_uses_version_precondition_and_snapshot_is_read_only():
    ai = MeisoAiApi(session_id="session-ai")

    first = ai.state.apply(StatePatch(state_id="state-session", base_version=0, set_values={"mode": "idle"}))
    second = ai.state.apply(StatePatch(state_id="state-session", base_version=1, set_values={"mode": "scene"}))

    assert first.version == 1
    assert second.version == 2
    assert second.values["mode"] == "scene"
    with pytest.raises(TypeError):
        second.values["mode"] = "bad"
    with pytest.raises(ValueError, match="base_version"):
        ai.state.apply(StatePatch(state_id="state-session", base_version=1, set_values={"mode": "stale"}))


def test_protocol_names_ai_native_message_types():
    assert MeisoMessageType.AI_CONTEXT_UPDATE.value == "ai_context_update"
    assert MeisoMessageType.AI_STATE_PATCH.value == "ai_state_patch"
    assert MeisoMessageType.AI_TOOL_CALL.value == "ai_tool_call"
    assert MeisoMessageType.AI_TOOL_RESULT.value == "ai_tool_result"
