from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parents[1]
source = (root / "draft-infantado-agent-memory-architecture.md").read_text(encoding="utf-8")
required = [
    'title: "Architecture and Data Model for Persistent Memory in Agentic Systems"',
    "docname: draft-infantado-agent-memory-architecture-latest",
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
for path in list((root / "schemas").rglob("*.json")) + list((root / "examples").glob("*.json")) + list((root / "test-vectors").rglob("*.json")):
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

# R6.4: evidence-chain validation automatically discovered and run.
# validate_evidence discovers all evidence-chain-*.jsonl files under
# validation/reports/ AND all *.jsonl files under validation/evidence/.
sys.path.insert(0, str(root / "scripts"))
import validate_evidence as _ve  # noqa: E402

_evidence_paths = (
    sorted((root / "validation" / "reports").glob("evidence-chain-*.jsonl"))
    + sorted((root / "validation" / "evidence").glob("*.jsonl"))
)
if _evidence_paths:
    _errs: list[str] = []
    _validator = _ve.make_validator()
    for _p in _evidence_paths:
        _errs.extend(_ve.validate_chain(_p, _validator))
    if _errs:
        raise SystemExit("evidence-chain validation failed:\n" + "\n".join(_errs))
    print(f"evidence chains validated: {len(_evidence_paths)} file(s)")
