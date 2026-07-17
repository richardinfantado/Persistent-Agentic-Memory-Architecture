# Decision: PAMSPEC ↔ AIMEM disposition (locked)

## Status

**Accepted (locked).** This ADR records the current, singular AIMEM
disposition and the *only* conditions under which the disposition
may be reopened. It supersedes any prior repository language that
ranked "adopt AIMEM" or "profile AIMEM" as preferred options.

## Date

2026-07-18

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
Appendix A). Two concrete gaps are load-bearing for this decision:

1. **Extension mechanism gap.** AIMEM `-00` does not define or
   reserve an extension prefix (no `x-*` namespace, no per-chunk
   extension block). Every PAMSPEC concept that AIMEM cannot carry
   natively (§Appendix A.2 through A.6) would need a namespaced
   extension mechanism that AIMEM does not currently provide.
2. **Expected-version conflict semantics — incompatible.** AIMEM
   explicitly permits consumer discretion in resolving updates
   (Appendix A.2). PAMSPEC mandates rejection of stale expected
   versions with `version_conflict`. This is not a shape difference;
   it is a semantic conflict.

Additional not-representable core concepts (distinct version
identity, version sequence, event history, Lifecycle State,
Validation State, tombstone semantics) reinforce the same conclusion
but do not change the disposition.

## Decision (locked wording)

> **PAMSPEC and AIMEM remain separate but coordinated. PAMSPEC will
> not define a bundle or normatively depend on AIMEM at this stage.
> Profiling or adoption may be reconsidered only after joint
> technical work or an AIMEM revision resolves the documented
> extension and conflict-semantics gaps.**

Restated as explicit rules for this repository:

1. **Coordinate but remain separate.** Cite AIMEM (`draft-vu-aimem-bundle-00`) explicitly in any PAMSPEC `-00` and any subsequent revision. Reference the R2 cross-cutting matrix (§2.1) and field-and-behavior mapping (Appendix A) as the concrete basis for coordination.
2. **No PAMSPEC bundle.** PAMSPEC MUST NOT define its own memory-bundle format at this stage. The interoperability problem a PAMSPEC bundle would address is currently occupied by AIMEM.
3. **No normative AIMEM dependency.** PAMSPEC MUST NOT declare a normative dependency on AIMEM, MUST NOT specify AIMEM as PAMSPEC's exchange binding, and MUST NOT publish an AIMEM profile at this stage.
4. **Reopening conditions (both required).** The adoption or profiling options may be reopened only when *both* of the following are true:
    - (a) An agreed extension mechanism exists between PAMSPEC and AIMEM authors (e.g., a reserved `x-*` namespace agreed with the AIMEM editor, or an AIMEM-defined extension block).
    - (b) The expected-version conflict incompatibility is resolved (either AIMEM revises to permit strict rejection, or a compatible profile is negotiated that PAMSPEC can adopt without loss).
   Either gap on its own is sufficient to block reopening. Both must be resolved before a follow-up ADR reopens the disposition.

## Alternatives considered

The following were considered and are formally **out of scope** at this stage under the disposition above; they are recorded here to prevent future ADRs from treating them as re-openable without the two conditions in §4 being satisfied.

- **Adopt AIMEM as PAMSPEC's exchange binding.** Out of scope. Would inherit AIMEM's currently-incompatible expected-version conflict semantics AND silently drop core PAMSPEC concepts (distinct version identity, sequence, event history, Lifecycle State, Validation State, tombstones) on round-trip. Reopens only when both gaps in §4 are resolved.
- **Profile AIMEM.** Out of scope. Requires a namespaced extension mechanism that AIMEM `-00` does not provide, AND resolution of the version-conflict incompatibility. Reopens only when both gaps in §4 are resolved.
- **Define a PAMSPEC bundle that competes with AIMEM.** Out of scope under rule (2). Would duplicate work already in progress on the datatracker.

## Consequences

- The PAMSPEC first `-00` submission text will include a "Relationship to prior art" section citing AIMEM, SAIHM, FAF/FAFM, and Portable Agent Memory. It will REFERENCE this ADR rather than re-argue the disposition.
- No PAMSPEC bundle work is authorized until this ADR is superseded by a follow-up ADR that satisfies the reopening conditions.
- Coordination with the AIMEM author (R6 in the project plan) is the only work track that can produce the evidence needed to reopen; that work is authorized separately.

## Interoperability impact

Sets a stable boundary between PAMSPEC and AIMEM that prevents accidental duplication of bundle interchange work while keeping the door open for later coordination.

## Security impact

None directly. The disposition does not change PAMSPEC's scope-isolation, provenance, or version-conflict requirements.

## Privacy impact

None directly. AIMEM's cryptographic-erasure and DNA-class semantics remain AIMEM's concern; PAMSPEC's tombstone/retention model remains PAMSPEC's concern.

## Unresolved questions

1. What is the correct coordination artifact for §1 (matrix + Appendix A)? A comparison table published in PAMSPEC `-00` is one option; a joint appendix in a co-authored companion document is another; a datatracker cross-reference is a third.
2. If the AIMEM `-00` expires (six months after posting per RFC 2026) without a revision that closes the gaps in §4, does this disposition remain in force, or should the ADR be revisited?
3. Are there other adjacent drafts that will emerge before the reopening conditions can be evaluated (e.g., a bundle-interchange draft from the W3C AI Agent Memory Interoperability CG)? If so, the disposition may need to consider more than two counterparts.

## References

- R2 crosswalk: [`../reviews/standards-and-research-crosswalk.md`](../reviews/standards-and-research-crosswalk.md) — locked disposition text and mapping in §6 and Appendix A.
- AIMEM: `draft-vu-aimem-bundle-00`, https://datatracker.ietf.org/doc/draft-vu-aimem-bundle/
- ADR-0029 (Scope boundary and anti-drift rule, this branch)
