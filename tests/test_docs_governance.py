from pathlib import Path


ACTIVE_DOCS = {
    Path("docs/index.md"),
    Path("docs/system.md"),
    Path("docs/link.md"),
    Path("docs/validation.md"),
}
HISTORICAL_DOCS = {Path("docs/manual-origin.md")}


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def test_markdown_tree_is_minimal_and_explicit():
    actual = set(Path("docs").rglob("*.md"))

    assert actual == ACTIVE_DOCS | HISTORICAL_DOCS


def test_index_names_the_only_active_authorities():
    index = Path("docs/index.md").read_text(encoding="utf-8")

    for path in sorted(ACTIVE_DOCS - {Path("docs/index.md")}):
        assert f"]({path.name})" in index


def test_manual_input_is_not_an_active_authority():
    source = Path("docs/manual-origin.md").read_text(encoding="utf-8")

    assert "Non-normative manual input" in source
    assert "70c364376a07f7c4a7ec713b8979bf37295e9cb1" in source
    for protected_text in (
        "Edge Core ↔ Host Core",
        "meisoObject",
        "c>b>a>d",
        "TCP UDP",
        "bulk object",
        "docs/spec/wire-protocol.md",
        "chat[2]",
        "docs/spec/data-link.md",
    ):
        assert protected_text in source


def test_protected_manual_concepts_map_to_active_specs():
    active = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            Path("docs/system.md"),
            Path("docs/link.md"),
            Path("docs/validation.md"),
        )
    )

    for constraint in (
        "Host <-> Edge",
        "truth owner",
        "| `a` | `Observation`",
        "| `b` | `LatestState`",
        "| `c` | `OrderedEvent`",
        "| `d` | `Bulk`",
        "c > b > a > d",
        "socket、port",
        "FrameKey",
    ):
        assert constraint in active


def test_vitepress_sidebar_lists_only_active_spec_pages():
    sidebar = Path("docs/.vitepress/sidebar.mjs").read_text(encoding="utf-8")

    assert "ACTIVE_PAGE_FILES = ['system.md', 'link.md', 'validation.md']" in sidebar
    assert "manual-origin.md" not in sidebar


def test_active_docs_do_not_link_removed_document_tree():
    removed_roots = (
        "SDK/",
        "ci-cd/",
        "decisions/",
        "development/",
        "origin/",
        "spec/",
        "standards/",
    )
    violations = []

    for path in ACTIVE_DOCS | {Path("README.md")}:
        text = path.read_text(encoding="utf-8")
        if any(root in text for root in removed_roots):
            violations.append(str(path))

    assert violations == []


def test_repository_paths_use_english_names():
    ignored = {
        ".git",
        ".pytest_cache",
        ".venv",
        "node_modules",
        "__pycache__",
        "meiso_glass.egg-info",
    }
    bad_paths = []

    for path in Path(".").rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if has_cjk(path.name):
            bad_paths.append(str(path))

    assert bad_paths == []
