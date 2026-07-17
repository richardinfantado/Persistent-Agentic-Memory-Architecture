# Decision: Version creation rules

## Status

Accepted for the semantic consistency pass.

## Date

2026-07-11

## Context

PAMSPEC separates Authoritative State from operational activity. Two categories of change occur against Memory Objects: changes that mutate Canonical Content or any authoritative dimension (Lifecycle, Availability, Retention, Validation, provenance, or authoritative relationship references), and operational activity that observes or supports the object without changing its authoritative meaning (embedding generation, derived index rebuilds, retrieval-cache refreshes, access denials, and read audits).

## Problem

If every operational event created a new Memory Version, version histories would be dominated by non-authoritative churn (embedding rebuilds, cache refreshes, read audits), harming replay, diff, and audit clarity. If, conversely, authoritative state changes did not always create a new Memory Version, silent overwrite becomes possible and rollback, deterministic replay, and tamper evidence weaken.

## Proposed Decision

1. Every change to Authoritative State MUST produce a new immutable Memory Version and a corresponding Event Ledger entry, committed atomically from the perspective of Inspect History.
2. Authoritative State comprises Canonical Content, authoritative metadata, Lifecycle State, Availability State, Retention State, Validation State, authoritative provenance, authoritative relationship references, and integrity metadata that covers authoritative content.
3. Operational events (`embedding_generated`, `index_rebuilt`, `access_denied`, retrieval-cache refresh, and equivalent non-authoritative activity) MUST produce Event Ledger entries but MUST NOT produce a new Memory Version.
4. Update, Transition, Redact, and Delete use expected-version preconditions. A stale expected version MUST fail with `version_conflict` and MUST NOT overwrite the newer version.
5. `sequence` values within a single object's version history MUST be strictly increasing.

## Alternatives Considered

- Version-per-event (including derived-index rebuilds): rejected because it conflates operational churn with authoritative history and defeats deterministic replay.
- No mandatory version bump for state transitions (e.g., availability changes recorded only as events): rejected because it makes redaction, deletion, and legal-hold history ambiguous and complicates authorization audit.
- Last-write-wins without expected-version preconditions: rejected because silent overwrite of a newer version by an actor holding stale state is a tamper and correctness hazard.
- CRDT/merge semantics as the default: rejected for this candidate profile because merge semantics vary by content type and require type-specific specification; a future profile may define conflict-free merge for specific object types.

## Consequences

- Object histories reflect only authoritative changes and remain diff- and replay-friendly.
- Derived indexes may be rebuilt aggressively without polluting authoritative history.
- Implementations must provide atomic commit of the version and its ledger entry, or fail the operation.
- Callers must supply an expected version on state-changing operations and handle `version_conflict` with refetch-and-merge.

## Interoperability Impact

Export and import can reconstruct the authoritative history without replaying operational noise. Cross-implementation replay and comparison rely on the shared invariant that authoritative changes and only authoritative changes correspond one-to-one with Memory Versions.

## Security Impact

Expected-version semantics prevent stale-actor silent overwrite. Atomic version-plus-ledger commit prevents forged histories where a version exists without a corresponding ledger record (or vice versa). Availability, Retention, and Validation transitions are always attributable to a specific actor and version.

## Privacy Impact

Redaction and deletion produce new Memory Versions with tombstone semantics, keeping the operational record while allowing content-level erasure. Operational events such as `access_denied` are recorded without creating a Memory Version and therefore without implying that Canonical Content changed.

## Unresolved Questions

- Should a future profile define conflict-free merge semantics for specific object types (for example, `summary` or `task` progress fields)?
- Should `sequence` be required to be globally monotonic within a scope, or only within an object history? (Current answer: only within an object history.)
- What implementation reports are needed before freezing atomicity guarantees across storage backends that lack native multi-write transactions?

## References

- `draft-infantado-agent-memory-architecture-00`, sections 8 (Versioning), 12 (Consistency and Concurrency), and 13 (Error Model).
- ADR-0007 (deletion, redaction, and tombstone behavior)
- ADR-0008 (event ordering and causality)
- ADR-0010 (operation idempotency)
