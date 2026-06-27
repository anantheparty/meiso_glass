from pathlib import Path

import pytest

from meiso_glass.config import load_config
from meiso_glass.protocol import MeisoRole


def test_generic_configs_use_host_edge_roles():
    edge = load_config(Path("configs/examples/edge.generic.yaml"))
    host = load_config(Path("configs/examples/host.generic.yaml"))

    assert edge.meiso_role == MeisoRole.EDGE
    assert host.meiso_role == MeisoRole.HOST
    assert edge.platform == "generic-linux"
    assert host.platform == "generic-linux"


def test_all_config_profiles_load_with_valid_ports():
    for path in Path("configs").rglob("*.yaml"):
        cfg = load_config(path)

        assert cfg.role in {"edge", "host"}
        assert 0 < cfg.control_port < 65536
        assert 0 < cfg.high_reliable_port < 65536
        assert 0 < cfg.latest_wins_port < 65536
        assert 0 < cfg.low_reliable_port < 65536
        assert 0 < cfg.low_power_port < 65536


def test_unknown_role_is_rejected(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text("device:\n  role: tool\n", encoding="utf-8")

    with pytest.raises(ValueError, match="role"):
        load_config(path)


def test_single_public_cli_entry_in_pyproject():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    old_compute_cli = "meiso-" + "s" + "dc"
    old_device_cli = "meiso-" + "end" + "point"

    assert 'meiso = "meiso_glass.cli:main"' in text
    assert old_compute_cli not in text
    assert old_device_cli not in text
