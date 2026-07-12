# Decision: Deterministic retrieval profile

## Status

Proposed for `draft-infantado-agent-memory-architecture-00` review.

## Date

2026-07-11

## Context

The PAMSPEC Object and Operation Model -00 milestone needs a coherent candidate interoperability model while preserving Informational architecture status.

## Problem

Implementations need shared semantics for testing and review, but unresolved design matters must not be silently finalized or over-specified.

## Proposed Decision

Distinguish deterministic structured retrieval, repeatable snapshot retrieval, approximate semantic retrieval, and best-effort retrieval.

## Alternatives Considered

- Leave this topic as scaffolding; rejected because Sections 8 through 14 need candidate testable semantics.
- Standardize a full protocol or storage format now; rejected because bindings and storage remain future work.
- Defer entirely to implementations; rejected because portability and review would remain weak.

## Consequences

This creates reviewable semantics and explicit open questions without claiming final standardization.

## Interoperability Impact

The decision improves export, import, replay, query, history inspection, and operation compatibility by naming the semantic contract.

## Security Impact

The decision clarifies scope, authorization, event, denial, and tamper-evidence expectations that reduce accidental disclosure or silent mutation.

## Privacy Impact

The decision clarifies retention, redaction, tombstone, provenance, and derived-index exposure risks while leaving policy details implementation-specific.

## Unresolved Questions

- Which parts should become mandatory conformance requirements in a future revision?
- Which parts should remain profile-specific?
- What implementation reports are needed before freezing field names or transition tables?

## References

- `draft-infantado-agent-memory-architecture-00`
