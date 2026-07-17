# PAMSPEC Reference Implementation (Python)

Minimal, SQLite-backed, in-process reference implementation of the PAMSPEC
`PAMSPEC-Lite` conformance profile. **This is a reference, not a production
system** — it is optimized for readability and correctness against the spec,
not throughput, high availability, or hardened security.

## Scope

Implements `PAMSPEC-Lite`:

- Memory Scope enforcement
- Canonical Memory Object envelope (schemas/0.1-draft/memory-object.schema.json)
- Lifecycle State (subset: `active`, `superseded`, `archived`)
- Availability State (subset: `available`, `deleted`)
- Retention State (subset: `retained`, `pending_deletion`)
- Validation State (subset: `unverified`, `corroborated`)
- Immutable Memory Versions with expected-version preconditions
- Append-only Event Ledger with atomic version+event commit
- Create, Read, Update, Transition, Delete, Query operations

## Non-goals

- Relationship Objects (PAMSPEC-Relationship profile)
- Semantic query / Embedding Spaces
- Redaction beyond deletion tombstone
- Snapshots
- Authorization/RBAC (all operations run as the caller's declared actor)

## Install

```bash
pip install jsonschema
```

## Use

```python
from pamspec_ref import MemoryService

svc = MemoryService(":memory:")  # or a file path

result = svc.create(
    scope_id="workspace:demo",
    object_type="claim",
    canonical_content={"statement": "The sky is blue."},
    actor={"actor_id": "actor:demo", "actor_kind": "human"},
    provenance={
        "provenance_id": "prov:1",
        "actor": {"actor_id": "actor:demo", "actor_kind": "human"},
        "activity": "created",
    },
)
print(result["version_id"])

read = svc.read(scope_id="workspace:demo", object_id=result["object_id"])
print(read["canonical_content"])
```

## Test

```bash
python -m pytest implementations/reference-python/tests
```

## Conformance

Passes every `test-vectors/valid/*.json` object supported by `PAMSPEC-Lite`
and rejects every `test-vectors/invalid/*.json` object with the expected
error code within its supported subset.
