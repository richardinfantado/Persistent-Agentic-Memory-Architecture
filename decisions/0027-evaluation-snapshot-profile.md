# Decision: PAMSPEC-Evaluation sub-profile with sealed snapshots

## Status

Accepted for `-01` enhancement cycle.

## Date

2026-07-17

## Context

Every serious agent team maintains an evaluation harness. Those
harnesses reinvent state capture, clock injection, RNG seeding, and
regression comparison. PAMSPEC's existing snapshot concept is
almost sufficient but leaves determinism as an implementation detail.

## Problem

Without a formal evaluation sub-profile:

- Wall-clock timestamps in evaluation-time operations differ across
  reruns, breaking equality-based regression checks.
- Retrieval tie-breaks vary across runs, giving nondeterministic
  ranking outputs.
- Evaluation-authored memory pollutes production data because it
  is not distinguishable in provenance.
- Regression comparison between evaluation runs is DIY.

## Proposed Decision

Add a **PAMSPEC-Evaluation** sub-profile requiring:

1. Sealed Snapshots (`evaluation-snapshot.schema.json`) with fixed
   `ledger_sequence_high_watermark` and optional explicit membership.
2. Optional `deterministic_clock` injection consumed by
   evaluation-time operations instead of wall time.
3. Optional `deterministic_rng_seed` for reproducible sampling and
   tie-breaks.
4. Mandatory `evaluation_run_id` propagation into provenance of any
   evaluation-time memory operation.
5. Snapshot comparison exposed through the same query surface as
   Inspect History.

## Alternatives Considered

- Extend the existing Snapshot concept in place: rejected because
  most Snapshot uses are non-evaluation; loading them with
  evaluation determinism obligations would be heavy-handed.
- Publish an evaluation *tool* rather than a profile: rejected
  because a tool cannot substitute for cross-implementation
  determinism guarantees.
- Require evaluation snapshots to be signed: deferred; the schema
  provides `digest` fields to enable this later without a
  breaking change.

## Consequences

- Agent regression testing becomes cross-implementation portable.
- Evaluation-authored memory is provably distinct from production
  memory via provenance `evaluation_run_id`.
- Implementations must plumb the deterministic clock/RNG through
  their operation paths.

## Interoperability Impact

Evaluation snapshots and their comparison outputs can be shared
across PAMSPEC implementations, enabling third-party evaluation
services.

## Security Impact

Evaluation runs cannot silently mutate production state; the
sub-profile forbids cross-scope side effects without policy.

## Privacy Impact

Evaluation snapshots reference the same data as production; scope
enforcement and access control extend unchanged.

## Unresolved Questions

- Should snapshot comparison output have its own schema, or just
  reuse Inspect History output shape?
- How should evaluation runs against redacted objects be represented
  when the redaction happened after the snapshot was sealed?

## References

- `schemas/0.1-draft/evaluation-snapshot.schema.json`
- `test-vectors/valid/evaluation-snapshot.json`
- `draft-infantado-agent-memory-architecture`, Interoperability and Conformance section
