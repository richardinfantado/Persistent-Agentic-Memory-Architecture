# Implementation Report — Reference Python Implementation

**Implementation name:** `pamspec_ref` (reference Python implementation)
**Version:** 0.1.0-draft (built from PAMSPEC repo commit at report time)
**Language / runtime:** Python 3.10+, SQLite-backed, in-process
**License:** Apache-2.0
**Report date:** 2026-07-17
**Report author:** Richard M. Infantado

## Purpose

This is the reference implementation cited by the specification. The
report is a worked example showing what other implementations should
submit under `reviews/implementation-report-<name>.md`.

## Profiles claimed

| Profile | Claimed | Conformance cases passed |
| --- | --- | --- |
| PAMSPEC-Lite | Yes | 14 / 14 |
| PAMSPEC-Delegation | Yes | 7 / 7 |
| PAMSPEC-Subscribe | Yes | 4 / 4 |
| PAMSPEC-Core | Partial | (see below) |
| PAMSPEC-Versioning | Yes | Covered by Lite `case_stale_expected_version_raises_version_conflict` and `case_update_creates_new_version` |
| PAMSPEC-Ledger | Partial | Ledger append and cost/latency fields supported; event-only operations recorded; snapshot-atomic commit covered by write path |
| PAMSPEC-Structured-Query | Partial | Scope-bound filters over four state dimensions; no snapshot-repeatable ordering yet |
| PAMSPEC-Semantic-Query | No | Not implemented in reference |
| PAMSPEC-Relationship | No | Not implemented in reference |
| PAMSPEC-Protocol-Binding | Yes | Reference MCP binding under `bindings/mcp/server-python/` wraps this implementation |
| PAMSPEC-Evaluation | No | Not implemented in reference |

## How to reproduce

```bash
git clone https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture
cd Persistent-Agentic-Memory-Architecture
python -m pip install -r requirements.txt
python -m pip install pytest

# reference implementation unit tests (24)
PYTHONPATH=implementations/reference-python python -m pytest implementations/reference-python/tests -q

# MCP binding adapter tests (6)
PYTHONPATH=implementations/reference-python:bindings/mcp/server-python python -m pytest bindings/mcp/server-python/tests -q

# portable conformance suite (25 cases across 3 profiles)
PYTHONPATH=.:implementations/reference-python python -m pytest conformance/tests -q
```

Expected: 24 + 6 + 4 = 34 tests pass, all schema and repository
validators pass, all 25 conformance cases pass.

## Storage choices

- **Backend:** SQLite (`:memory:` for tests, file path for durable
  deployments).
- **Concurrency:** single-writer via `threading.RLock`, optimistic on
  version. Not designed for cross-process concurrency.
- **Retention:** all authoritative versions retained; no automatic
  compaction. Deletion writes tombstone versions preserving audit
  chain.
- **Derived Indexes:** none.

## Authorization model

None. All operations execute as the caller's declared actor. This
implementation is a reference, not a production system; it is
appropriate for embedded / single-tenant contexts.

## Known deviations from spec

- Snapshot-repeatable structured query ordering is not implemented.
- Semantic query and Relationship Objects are not implemented.
- Evaluation snapshots (`PAMSPEC-Evaluation`) are not implemented.
- The MCP binding server (`bindings/mcp/server-python/`) is a
  protocol-adapter stub — it dispatches to the reference impl but
  does not itself speak an MCP transport.

## Test-vector coverage

- All `test-vectors/valid/*.json` positive vectors are consumed by
  the schema validator (`python scripts/validate_test_vectors.py`).
- All `test-vectors/invalid/*.json` negative vectors either fail
  schema validation as expected or are recognized as documented
  semantic rules.
- The four semantic rules that the reference implementation can
  execute at runtime (`delegation_window_inverted`,
  `attestation_window_inverted`,
  `promote_source_must_be_working_memory`,
  `evaluation_snapshot_membership_frozen`) are covered by
  behavioral cases in the conformance suite where the profile
  applies (delegation window is enforced; the others are covered
  by the schema layer or noted as deviations above).

## Points for external reviewers

- The `check_delegation` implementation decrements `usage_count`
  inside the same DB transaction as the check itself. Is that the
  right semantics, or should exhaustion be checked but not
  decremented on denial? (Reference currently denies without
  decrementing, but this could be tightened.)
- The subscription cursor advances past events that fail
  authorization or filter — is that the right semantics, or should
  cursor advance only on delivered events?
- The reference deliberately does not implement the semantic
  Promote operation; the harness has no case for it yet.
