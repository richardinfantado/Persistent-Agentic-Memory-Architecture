# Decision: Optional machine-readable quality_signals block

## Status

Accepted for `-01` enhancement cycle.

## Date

2026-07-17

## Context

Automated agent memory systems increasingly compute quality signals:
confidence scores, contradiction detection, staleness assessments,
evidence strength, source diversity. Systems like Mem0, LangGraph
memory, and various retrieval-augmented frameworks all have some
version of this but with incompatible field names and scales.

## Problem

Without a common vocabulary:

- Retrieval ranking cannot easily combine quality signals from
  different producers.
- Migration between memory systems loses computed quality data.
- Confusion arises between machine-derived quality (this block)
  and authoritative validation (Validation State).

## Proposed Decision

Add an optional `quality_signals` block to the Memory Object
envelope with standardized fields, all normalized to `[0, 1]`
where applicable:

- `confidence`, `contradiction_score`, `staleness_score`,
  `evidence_strength`, `source_diversity`
- `last_verified_at`, `last_verified_by_actor_id`,
  `verification_method_id`
- `assessed_at`, `assessed_by_actor_id`

The block is explicitly non-authoritative. Retrieval ranking and
default filters MAY use it. It MUST NOT be used to override
Validation State — those two remain distinct concepts (automated
signal vs authoritative review).

## Alternatives Considered

- Add quality signals to `provenance`: rejected because provenance
  describes origin/evidence, not derived quality assessments.
- Add them as a distinct object type (like `assessment`): rejected
  as over-engineered for signals that need to travel with the
  object they describe.
- Leave to implementations: rejected because divergent field names
  block retrieval interop.

## Consequences

- Cross-implementation retrieval ranking becomes composable.
- Automated quality pipelines can update the block via Update
  without needing a special operation.
- Consumers must remain aware that these signals are opinions,
  not truth.

## Interoperability Impact

Quality signals now round-trip through export/import cycles.

## Security Impact

Manipulating quality signals can bias retrieval; access control
on Update remains the enforcement point.

## Privacy Impact

Verifier and assessor actor IDs are recorded; standard actor
privacy considerations apply.

## Unresolved Questions

- Should there be a canonical list of `verification_method_id`
  values, or should this remain free-form?
- Should quality signal *history* be modeled? Current answer: no,
  because a new Memory Version already captures the change.

## References

- `schemas/0.1-draft/common.schema.json` (`quality_signals` definition)
- `schemas/0.1-draft/memory-object.schema.json`
- `test-vectors/valid/claim-with-quality-signals.json`
