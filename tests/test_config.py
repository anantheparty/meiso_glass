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
