import pytest

from meiso_glass.api import SDCRegistry
from meiso_glass.messages import Message, MessageType, Role


def test_sdc_registry_accepts_endpoint_heartbeat():
    registry = SDCRegistry(endpoints={})
    heartbeat = Message(msg_type=MessageType.HEARTBEAT, src_role=Role.ENDPOINT, src_id="endpoint-1")

    registry.register_endpoint(heartbeat)

    assert registry.endpoints["endpoint-1"] == heartbeat


def test_sdc_registry_rejects_non_heartbeat():
    registry = SDCRegistry(endpoints={})
    msg = Message(msg_type=MessageType.PING, src_role=Role.HOST, src_id="host-1")

    with pytest.raises(ValueError, match="heartbeat"):
        registry.register_endpoint(msg)
