from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
source = (root / "draft-infantado-agent-memory-architecture.md").read_text(encoding="utf-8")
required = [
    'title: "Architecture and Data Model for Persistent Memory in Agentic Systems"',
    "docname: draft-infantado-agent-memory-architecture-00",
    "category: info",
    "RFC2119",
    "RFC8174",
    "Persistent State Plane is authoritative",
    "Derived Indexes are non-authoritative",
    "private chain-of-thought",
    "Silent in-place overwrite is non-conforming",
    "version_conflict",
    "duplicate_operation",
    "embedding_space_mismatch",
    "This document has no IANA actions.",
]
missing = [item for item in required if item not in source]
if missing:
    raise SystemExit(f"missing required draft markers: {missing}")
for path in list((root / "schemas").glob("*.json")) + list((root / "examples").glob("*.json")) + list((root / "test-vectors").rglob("*.json")):
    with path.open(encoding="utf-8") as handle:
        json.load(handle)
old_refs = []
for path in root.rglob("*"):
    if path.is_file() and ".git" not in path.parts and path.name != "validate_repository.py":
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        stale = "draft-infantado-" + "pama-architecture"
        if stale in text:
            old_refs.append(str(path.relative_to(root)))
if old_refs:
    raise SystemExit(f"unintended pama draft-name references: {old_refs}")
print("repository metadata, draft-name, and JSON syntax checks passed")
