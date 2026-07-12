# OpenBrain Mapping to PAMSPEC

This document is informative and non-normative. PAMSPEC terminology and conformance requirements do not depend on OpenBrain, and OpenBrain is not mandatory for PAMSPEC.

## Compatible Concepts

- Project or workspace boundaries can map to PAMSPEC Memory Scopes when they provide administrative, policy, retention, security, and query isolation.
- Persistent records can map to PAMSPEC Memory Objects when they expose stable object identity, version identity, Canonical Content, provenance, Lifecycle State, and Validation State.
- Audit logs can map to the PAMSPEC Event Ledger if state-changing operations are append-only and inspectable.
- Embedding indexes can map to PAMSPEC Derived Indexes when every vector identifies an Embedding Space.

## Gaps

- Hidden in-place overwrite behavior must be replaced with immutable logical versions or equivalent transition records.
- Cross-workspace search must preserve scope boundaries and must not default to unscoped global semantic retrieval.
- Embedding comparisons need explicit Embedding Space descriptors and mismatch handling.
- Lifecycle and validation should be separate dimensions rather than a single status field.

## Implementation-Specific Extensions

OpenBrain can define local object types, policy hooks, UI labels, storage layouts, and runtime integrations as implementation extensions if exported PAMSPEC semantics remain stable.

## Required Conformance Changes

- Expose or export PAMSPEC-compatible object envelopes.
- Emit Event Ledger entries for state-changing operations.
- Preserve expected-version and idempotency semantics.
- Return stable transport-neutral error codes or a lossless mapping to them.
- Treat Derived Indexes as non-authoritative and regenerable.

## Unresolved Areas

- Exact mapping of existing OpenBrain record identifiers to `object_id` and `version_id`.
- Migration behavior for legacy records that lack provenance or version history.
- Redaction and tombstone behavior across existing backups and indexes.
- Implementation-report format for documenting conformance gaps.

