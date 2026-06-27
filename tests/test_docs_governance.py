from pathlib import Path

ALLOWED_DOC_TOP_LEVEL = {
    ".vitepress",
    "README.md",
    "SDK",
    "ci-cd",
    "development",
    "index.md",
    "origin",
    "public",
    "spec",
    "standards",
}


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def test_single_bible_is_the_only_sdk_bible_doc():
    bible_docs = {path.name for path in Path("docs/SDK/bible").glob("*.md")}

    assert bible_docs == {"SDK_DESIGN_OVERVIEW.md"}


def test_docs_top_level_is_governed():
    entries = {path.name for path in Path("docs").iterdir() if not path.name.startswith(".DS_Store")}

    assert entries <= ALLOWED_DOC_TOP_LEVEL


def test_active_docs_do_not_link_removed_bible_files():
    violations = []
    for root in [Path("README.md"), Path("docs")]:
        paths = [root] if root.is_file() else [path for path in root.rglob("*.md") if "origin" not in path.parts]
        for path in paths:
            text = path.read_text(encoding="utf-8", errors="replace")
            if "SDK_SUBSYSTEM_DESIGN.md" in text or "SDK_DEVELOPMENT_PLAN.md" in text:
                violations.append(str(path))

    assert violations == []


def test_repository_paths_use_english_names():
    ignored = {".git", ".pytest_cache", ".venv", "node_modules", "__pycache__", "meiso_glass.egg-info"}
    bad_paths = []
    for path in Path(".").rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if has_cjk(path.name):
            bad_paths.append(str(path))

    assert bad_paths == []
