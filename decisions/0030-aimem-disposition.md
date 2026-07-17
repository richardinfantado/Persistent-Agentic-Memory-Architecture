# Decision: PAMSPEC ↔ AIMEM disposition

## Status

**Accepted — current disposition.** This ADR records PAMSPEC's current
position on AIMEM based on the evidence available at the review date.
A later ADR MAY supersede this one when material new evidence changes
that position. This ADR is not "locked"; ADRs record best-available
decisions and are open to revision when facts change.

## Date

2026-07-18 (revised)

## Context

AIMEM (`draft-vu-aimem-bundle-00`, posted 2026-06-14, individual
submission on the IETF datatracker) already defines memory-bundle
exchange semantics: envelope with `format`/`version`/`producer`/
`tenant_id`/`scope`, ChunkRecord + edges + entities, `urn:aimem:`
identifier scheme, embedding metadata with declared model identifier,
SHA-256 integrity and optional COSE_Sign1, DNA-class chunk invariants,
and Producer/Consumer/Bidirectional conformance levels.

The R2 crosswalk performed a field-and-behavior mapping of every
PAMSPEC concept against AIMEM (see
[`../reviews/standards-and-research-crosswalk.md`](../reviews/standards-and-research-crosswalk.md),
Appendix A). Two observations are load-bearing for this decision:

1. **Extension mechanism gap.** AIMEM `-00` does not define or
   reserve a per-object or per-chunk extension mechanism (no `x-*`
   namespace, no extension block). Every PAMSPEC concept AIMEM does
   not carry natively (§Appendix A.2–A.6) would need a namespaced
   extension mechanism AIMEM does not currently provide.
2. **Unresolved expected-version-behavior mismatch.** AIMEM is
   primarily an exchange-bundle proposal. It does not currently
   guarantee PAMSPEC's strict expected-version rejection semantics
   (AIMEM permits consumer discretion in resolving updates; PAMSPEC
   mandates rejection of stale expected versions with
   `version_conflict`). A future AIMEM profile might carry PAMSPEC
   version metadata and impose stricter consumer behavior without
   AIMEM's default changing — the mismatch is unresolved, not
   necessarily incompatible in principle.

Additional not-representable core concepts (distinct version
identity, version sequence, event history, Lifecycle State,
Validation State, tombstone semantics) reinforce the same
conclusion but do not change the disposition.

## Decision

**PAMSPEC and AIMEM remain separate. Coordination with the AIMEM
author will be pursued.**

Restated as explicit rules for this repository:

1. **No PAMSPEC bundle.** PAMSPEC does not define its own
   memory-bundle format. The interoperability problem a PAMSPEC
   bundle would address is currently occupied by AIMEM.
2. **No normative AIMEM dependency.** PAMSPEC does not declare a
   normative dependency on AIMEM and does not publish an AIMEM
   profile at this time.
3. **No AIMEM profile yet.** Publishing an AIMEM profile is
   deferred until the coordination and mapping work below produces
   sufficient evidence.
4. **Perform author coordination and implementation mapping before
   reconsideration.** Reaching out to the AIMEM author (planned as
   R6) and completing the implementation mapping (Appendix A of the
   R2 crosswalk) are prerequisites to any reconsideration of the
   disposition.

## Reconsideration triggers

An ADR records the best decision based on current evidence. A later
ADR MAY supersede this one when material new evidence changes the
picture. Examples of material new evidence:

- A new AIMEM revision that closes one or both of the gaps in §Context.
- Clarification from the AIMEM author (e.g., an agreed extension
  mechanism, or a compatible profile that PAMSPEC can adopt without
  loss).
- A PAMSPEC scope change that removes concepts AIMEM cannot carry.
- Argument (with evidence) that operational conflict semantics do
  not belong in a bundle binding, so the expected-version mismatch
  is not blocking.
- Emergence of another industry interchange format worth mapping
  to.
- Implementation-mapping evidence showing a viable AIMEM-based
  binding for the PAMSPEC concept set.

Reopening does not require both of the R2 unlocking conditions to
be satisfied in advance. It requires material new evidence and a
follow-up ADR that supersedes this one.

## Consequences

- The first PAMSPEC `-00` submission text will include a "Relationship
  to prior art" section citing AIMEM, SAIHM, FAF/FAFM, and Portable
  Agent Memory. It will REFERENCE this ADR rather than re-argue the
  disposition.
- Coordination with the AIMEM author (R6) is authorized as the
  primary work track that can produce evidence for a future
  disposition change.
- No PAMSPEC bundle work is authorized under this ADR. A future ADR
  that supersedes this one may authorize bundle work.

## Interoperability impact

Sets a stable boundary between PAMSPEC and AIMEM that prevents
accidental duplication of bundle interchange work while keeping the
door open for later coordination and, if warranted, revision.

## Security impact

None directly. The disposition does not change PAMSPEC's
scope-isolation, provenance, or version-conflict requirements.

## Privacy impact

None directly. AIMEM's cryptographic-erasure and DNA-class semantics
remain AIMEM's concern; PAMSPEC's tombstone/retention model remains
PAMSPEC's concern.

## Unresolved questions

1. What is the correct coordination artifact for author-to-author
   coordination? A comparison table published in PAMSPEC `-00` is one
   option; a joint appendix in a co-authored companion document is
   another; a datatracker cross-reference is a third.
2. If the AIMEM `-00` expires (six months after posting per RFC 2026)
   without a revision that addresses the unresolved mismatch, does
   this disposition remain in force or should the ADR be revisited?
3. Are there other adjacent drafts (e.g., from the W3C AI Agent
   Memory Interoperability CG) that will emerge and should also be
   part of the coordination scope?

## References

- R2 crosswalk: [`../reviews/standards-and-research-crosswalk.md`](../reviews/standards-and-research-crosswalk.md) — matching disposition text and mapping in §6 and Appendix A.
- AIMEM: `draft-vu-aimem-bundle-00`, https://datatracker.ietf.org/doc/draft-vu-aimem-bundle/
- ADR-0029 (Scope boundary and anti-drift rule, this branch)
