from pathlib import Path


REQUIRED_DOCS = [
    "docs/SDK/bible/SDK_DESIGN_OVERVIEW.md",
    "docs/SDK/bible/SDK_SUBSYSTEM_DESIGN.md",
    "docs/SDK/bible/SDK_DEVELOPMENT_PLAN.md",
]

ALLOWED_SDK_TOP_LEVEL = {"README.md", "bible"}
ALLOWED_SDK_BIBLE_DOCS = {
    "SDK_DESIGN_OVERVIEW.md",
    "SDK_SUBSYSTEM_DESIGN.md",
    "SDK_DEVELOPMENT_PLAN.md",
}

IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "meiso_glass.egg-info",
}


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def iter_project_paths(root: Path):
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def test_required_governance_docs_exist():
    missing = [path for path in REQUIRED_DOCS if not Path(path).is_file()]

    assert missing == []


def test_sdk_docs_stay_consolidated():
    sdk_entries = {path.name for path in Path("docs/SDK").iterdir() if not path.name.startswith(".")}
    bible_docs = {path.name for path in Path("docs/SDK/bible").glob("*.md")}

    assert sdk_entries == ALLOWED_SDK_TOP_LEVEL
    assert bible_docs == ALLOWED_SDK_BIBLE_DOCS


def test_repository_paths_use_english_names():
    bad_paths = [str(path) for path in iter_project_paths(Path(".")) if has_cjk(path.name)]

    assert bad_paths == []
