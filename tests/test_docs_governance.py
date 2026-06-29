from pathlib import Path
import re

ALLOWED_DOC_TOP_LEVEL = {
    ".vitepress",
    "README.md",
    "SDK",
    "ci-cd",
    "decisions",
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


def test_docs_directory_entries_use_index_pages():
    directory_entries = [
        Path("docs/SDK"),
        Path("docs/ci-cd"),
        Path("docs/decisions"),
        Path("docs/origin"),
        Path("docs/spec"),
    ]

    missing_indexes = [str(path) for path in directory_entries if not (path / "index.md").is_file()]

    assert missing_indexes == []


def test_vitepress_sidebar_links_have_matching_docs_pages():
    config = Path("docs/.vitepress/config.mts").read_text(encoding="utf-8")
    links = re.findall(r"link: '(/[^']+)'", config)

    missing_pages = []
    for link in links:
        if link.startswith(("http://", "https://")):
            continue

        route = link.removeprefix("/").rstrip("/")
        if route == "":
            expected = Path("docs/index.md")
        else:
            expected = Path("docs") / route / "index.md" if link.endswith("/") else Path("docs") / f"{route}.md"

        if not expected.is_file():
            missing_pages.append(link)

    assert missing_pages == []


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
