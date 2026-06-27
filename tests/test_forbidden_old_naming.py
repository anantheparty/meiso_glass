import re
from pathlib import Path

ACTIVE_PATHS = [
    Path("README.md"),
    Path("pyproject.toml"),
    Path("src"),
    Path("tests"),
    Path("configs"),
    Path("systemd"),
    Path("docs/SDK"),
    Path("docs/spec"),
    Path("docs/standards"),
    Path("docs/development"),
    Path("docs/ci-cd"),
    Path("docs/index.md"),
    Path("docs/README.md"),
    Path("docs/.vitepress/config.mts"),
]

OLD_COMPUTE = "s" + "dc"
OLD_DEVICE = "end" + "point"
OLD_DEVICE_TITLE = "End" + "point"
OLD_DEVICE_UPPER = "END" + "POINT"
OLD_CLI_COMPUTE = "meiso-" + OLD_COMPUTE
OLD_CLI_DEVICE = "meiso-" + OLD_DEVICE
OLD_VIDEO_START = "start" + "_video"
OLD_VIDEO_STOP = "stop" + "_video"
OLD_SPARSE_START = "start" + "_low" + "fi"
OLD_SPARSE_STOP = "stop" + "_low" + "fi"
OLD_DISPLAY = "display" + "_session"

FORBIDDEN = re.compile(
    "|".join(
        re.escape(term)
        for term in [
            OLD_CLI_COMPUTE,
            OLD_CLI_DEVICE,
            OLD_COMPUTE.upper(),
            OLD_COMPUTE,
            OLD_DEVICE_TITLE,
            OLD_DEVICE,
            OLD_DEVICE_UPPER,
            OLD_VIDEO_START,
            OLD_VIDEO_STOP,
            OLD_SPARSE_START,
            OLD_SPARSE_STOP,
            OLD_DISPLAY,
        ]
    )
)


def iter_active_text_files():
    for root in ACTIVE_PATHS:
        if root.is_file():
            yield root
            continue
        for path in root.rglob("*"):
            suffixes = {".py", ".md", ".yaml", ".yml", ".toml", ".service", ".mts"}
            if path.is_file() and "__pycache__" not in path.parts and path.suffix in suffixes:
                yield path


def test_active_code_and_docs_use_host_edge_not_old_roles():
    violations = []
    for path in iter_active_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        if FORBIDDEN.search(text):
            violations.append(str(path))

    assert violations == []


def test_machine_readable_content_does_not_contain_chinese():
    violations = []
    for root in [Path("src"), Path("tests"), Path("configs"), Path("systemd"), Path(".github")]:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix not in {".py", ".yaml", ".yml", ".service"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if any("\u4e00" <= char <= "\u9fff" for char in text):
                violations.append(str(path))

    assert violations == []
