from pathlib import Path


REQUIRED_DOCS = [
    "docs/SDK/bible/SDK_BIBLE.md",
    "docs/SDK/bible/ARCHITECTURE_BIBLE.md",
    "docs/SDK/bible/DECOUPLING_BIBLE.md",
    "docs/SDK/bible/TESTING_BIBLE.md",
    "docs/SDK/bible/PROTOCOL_BIBLE.md",
    "docs/SDK/bible/VERSIONING_BIBLE.md",
    "docs/SDK/bible/AGENT_RUNTIME_BIBLE.md",
    "docs/SDK/bible/ADAPTER_CONTRACT_BIBLE.md",
    "docs/SDK/bible/CONFIG_PROFILE_BIBLE.md",
    "docs/SDK/bible/CONTROL_PLANE_BIBLE.md",
    "docs/SDK/bible/OBSERVABILITY_BIBLE.md",
    "docs/SDK/bible/SUPPLY_CHAIN_BIBLE.md",
    "docs/SDK/bible/REFERENCE_IMPLEMENTATION_BOUNDARY.md",
    "docs/SDK/rules/LANGUAGE_AND_NAMING_RULES.md",
    "docs/SDK/rules/CORE_BOUNDARY_RULES.md",
    "docs/SDK/rules/TRANSPORT_PAYLOAD_RULES.md",
    "docs/SDK/checklists/DECOUPLING_REVIEW_CHECKLIST.md",
    "docs/SDK/checklists/PROTOCOL_CHANGE_CHECKLIST.md",
    "docs/SDK/checklists/ADAPTER_ACCEPTANCE_CHECKLIST.md",
    "docs/SDK/checklists/PLATFORM_ACCEPTANCE_CHECKLIST.md",
    "docs/SDK/checklists/RELEASE_READINESS_CHECKLIST.md",
    "docs/SDK/adr/0001-platform-neutral-core.md",
    "docs/SDK/adr/0002-sdc-role-name.md",
    "docs/SDK/adr/0003-udp-json-control-plane-v0.md",
    "docs/SDK/adr/0004-adapter-backed-hardware.md",
    "docs/SDK/adr/0005-chinese-docs-english-contracts.md",
    "docs/SDK/research/REFERENCE_SOURCES.md",
]

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


def test_repository_paths_use_english_names():
    bad_paths = [str(path) for path in iter_project_paths(Path(".")) if has_cjk(path.name)]

    assert bad_paths == []
