from pathlib import Path


REFERENCE_PLATFORM_TOKENS = {
    "imx8",
    "imx8mm",
    "orin",
    "jetson",
    "tegra",
    "nvidia",
    "nvv4l2",
    "nv3d",
    "lr2021",
    "hm0360",
    "gw1nz",
    "nrf54",
}

MACHINE_CONTENT_PATHS = [
    Path("src"),
    Path("configs"),
    Path("scripts"),
    Path("systemd"),
]


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def normalized_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").lower()


def machine_text_without_comments(path: Path) -> str:
    lines = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            yield path


def test_core_source_has_no_reference_platform_tokens():
    violations = []
    for path in iter_files(Path("src/meiso_glass")):
        if path.suffix != ".py":
            continue
        text = normalized_text(path)
        for token in REFERENCE_PLATFORM_TOKENS:
            if token in text:
                violations.append(f"{path}: {token}")

    assert violations == []


def test_generic_configs_do_not_name_reference_platforms():
    violations = []
    for path in Path("configs/examples").glob("*.yaml"):
        text = normalized_text(path)
        for token in REFERENCE_PLATFORM_TOKENS:
            if token in text:
                violations.append(f"{path}: {token}")

    assert violations == []


def test_machine_readable_content_does_not_contain_chinese():
    violations = []
    for root in MACHINE_CONTENT_PATHS:
        for path in iter_files(root):
            if path.suffix not in {".py", ".yaml", ".yml", ".sh", ".service"}:
                continue
            text = machine_text_without_comments(path)
            if has_cjk(text):
                violations.append(str(path))

    assert violations == []
