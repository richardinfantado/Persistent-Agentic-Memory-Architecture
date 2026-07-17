# PAMSPEC positioning note

## What PAMSPEC is

> PAMSPEC defines a provider-neutral architecture and authoritative state model for persistent agent memory, including scope, stable identity, immutable versions, provenance, state transitions, event history, and isolation of derived retrieval indexes. It is intended to map to multiple interchange formats and protocol bindings rather than mandate one storage engine or transport.

## Current status (must-know facts for anyone reading PAMSPEC material)

- **PAMSPEC has not been submitted to the IETF Datatracker.** No revision of the draft has been posted or published; the repository's version manifest records `ietf_submission_status: "not_submitted"`.
- **Active development docname:** `draft-infantado-agent-memory-architecture-latest`. Numbered artifacts in the repository history are internal review candidates only, not IETF-published revisions.
- **The first possible posted revision would be `-00`.** No `-00` has been posted. There is no `-01` or later revision in the IETF publication sequence.

## What PAMSPEC does not claim

- Not an IETF standard.
- Not an adopted IETF Working Group document.
- Not endorsed by IETF, W3C, or any standards body.
- Not the first, only, or definitive agent-memory specification.
- Not "MCP for memory," and not a replacement for any existing format or protocol.
- Not currently defining a memory-bundle format.
- Not normatively dependent on any adjacent draft.

## What PAMSPEC deliberately does not contain today

- No PAMSPEC bundle. Interchange-bundle semantics are addressed by `draft-vu-aimem-bundle` (AIMEM) in the IETF datatracker; PAMSPEC does not duplicate that work.
- No normative AIMEM dependency. See ADR-0030 in the PAMSPEC repository.
- Neither identity, authorization, transport, streaming, billing, nor observability is part of PAMSPEC's normative core. Those are governed by adjacent work (SAIHM, the agent-identity draft landscape, MCP, message-bus bindings, telemetry systems).

## What PAMSPEC's current core covers

- **Persistent-memory boundary:** the concept concerns persistent memory semantics or a security property necessary to preserve or interpret persistent memory.
- **Authoritative state model:** stable object identity, immutable version identity and monotonic ordering, canonical content, minimal provenance, extensible typing, error envelope.
- **Concurrency and idempotency:** expected-version conflict semantics and idempotent create.
- **Scope isolation:** enforced on read, write, query, export, and import.
- **Deletion semantics:** persistent tombstone; ordinary read blocked; identity preserved to prevent stale resurrection.
- **Event Ledger as architectural pattern.** Full atomic ledger behavior is an optional profile, not required for basic exchange.
- **Conditional Embedding Space identity:** required when an implementation carries embeddings; prevents silent cross-model vector comparison.

See the R2 crosswalk in the repository for the full concept-by-concept mapping against AIMEM, SAIHM, FAF/FAFM, Portable Agent Memory, MCP, and the W3C AI Agent Memory Interoperability CG.

## Current goal

Differentiation and coordination — not ownership of the space.

## References

- Repository: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture
- Version manifest: `pamspec-version.json` in the repository root
- Review-candidate archive: `REVIEW-CANDIDATE-ARCHIVE.md`
- R2 crosswalk: `reviews/standards-and-research-crosswalk.md`
- Scope decision: `decisions/0029-scope-boundary-and-anti-drift-rule.md`
- AIMEM disposition: `decisions/0030-aimem-disposition.md`

Anyone linking to this positioning note should link to the repository copy, not to any personal channel; the repository is the source of truth.
