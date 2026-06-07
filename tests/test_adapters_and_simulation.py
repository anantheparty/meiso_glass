from meiso_glass.adapters.interfaces import StreamConfig
from meiso_glass.adapters.mock import FakeIMU, FakePowerMonitor, FakeRadioLink, MockCameraAdapter
from meiso_glass.messages import MessageType, Role
from meiso_glass.simulation.mock_devices import MockEndpoint, MockSDC
from meiso_glass.telemetry.packet import TelemetryPacket, TelemetryPacketType


def test_mock_camera_tracks_stream_state():
    camera = MockCameraAdapter()

    assert camera.get_status().running is False
    status = camera.start_stream(StreamConfig(width=640, height=480, fps=15, format="RGB"))

    assert status.running is True
    assert status.details["config"].width == 640
    assert camera.stop_stream().running is False


def test_fake_sensor_power_and_radio_are_pc_runnable():
    imu = FakeIMU()
    power = FakePowerMonitor()
    radio = FakeRadioLink()

    assert imu.read_sample("fake_imu")["seq"] == 1
    assert power.set_mode("always_on_sentinel").details["mode"] == "always_on_sentinel"
    assert radio.send_packet(b"hello").details["queued"] == 1
    assert radio.receive_packet() == b"hello"


def test_mock_endpoint_and_sdc_create_protocol_objects():
    endpoint = MockEndpoint()
    sdc = MockSDC()

    heartbeat = endpoint.heartbeat()
    sdc.receive(heartbeat)
    packet = endpoint.lowfi_packet()
    ping = sdc.ping(endpoint.device_id)

    assert heartbeat.msg_type == MessageType.HEARTBEAT
    assert heartbeat.src_role == Role.ENDPOINT
    assert heartbeat.dst_role == Role.SDC
    assert sdc.received == [heartbeat]
    assert isinstance(packet, TelemetryPacket)
    assert packet.packet_type == TelemetryPacketType.LOWFI_VISION
    assert ping.msg_type == MessageType.PING
