from pathlib import Path

from meiso_glass.config import load_config


def test_generic_endpoint_config_is_platform_neutral():
    cfg = load_config(Path("configs/examples/endpoint.generic.yaml"))

    assert cfg.role == "endpoint"
    assert cfg.platform == "generic-linux"
    assert cfg.peer_host == "127.0.0.1"
    assert cfg.video_encoder == "x264enc"


def test_platform_profiles_are_not_default_examples():
    example_names = {path.name for path in Path("configs/examples").glob("*.yaml")}
    platform_names = {path.name for path in Path("configs/platforms").glob("*.yaml")}

    assert "endpoint.generic.yaml" in example_names
    assert "sdc.generic.yaml" in example_names
    assert "endpoint.imx8mm.yaml" in platform_names
    assert "sdc.orin.yaml" in platform_names
    assert example_names.isdisjoint(platform_names)


def test_all_config_profiles_load_with_valid_roles_and_ports():
    for path in Path("configs").rglob("*.yaml"):
        cfg = load_config(path)

        assert cfg.role in {"endpoint", "sdc", "host"}
        assert 0 < cfg.heartbeat_port < 65536
        assert 0 < cfg.control_port < 65536
        assert 0 < cfg.video_port < 65536


def test_generic_sdc_decoder_is_a_pipeline_not_a_core_alias():
    cfg = load_config(Path("configs/examples/sdc.generic.yaml"))

    assert cfg.video_decoder == "avdec_h264 ! videoconvert ! autovideosink sync=false"
