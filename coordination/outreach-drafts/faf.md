# Outreach draft — FAF / FAFM

**Status: draft, not sent.**

**To:** James Wolfe, FAF Foundation — `team@faf.one`
(Source: Author's Address section, `draft-wolfe-faf-format-02`. Recheck before sending.)

**From:** (maintainer to fill in personal name and email)

**Subject:** PAMSPEC — internal work-in-progress on agent-memory architecture; coordination note re: FAF/FAFM

---

Dear James,

I'm writing about `draft-wolfe-faf-format-02`. I've been developing a separate, still-internal project called PAMSPEC — the Persistent Agentic Memory Architecture Specification. It sits adjacent to what FAF/FAFM describes, and I want to introduce it accurately and describe how the two efforts relate.

**About PAMSPEC in one paragraph.** PAMSPEC defines a provider-neutral architecture and authoritative state model for persistent agent memory — scope, stable identity, immutable versions, provenance, state transitions, event history, and isolation of derived retrieval indexes. It is intended to map to multiple interchange formats and protocol bindings rather than mandate one storage engine or transport. Positioning note: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/main/coordination/pamspec-positioning-note.md

**About PAMSPEC's status.** PAMSPEC has NOT been submitted to the IETF Datatracker. No revision has been posted. Active development uses the docname `draft-infantado-agent-memory-architecture-latest`. If and when a first submission occurs, it will be `-00`. Nothing here should be read as a competing IETF filing.

**How PAMSPEC relates to FAF/FAFM.** From what I've read, FAF separates static project context (`.faf`) from mutating persistent agent memory (`.fafm`) with YAML media types, `etch`/`recall`/`forget` operations, retention policies, and a `/.well-known/faf` discovery mechanism. PAMSPEC's Compute Plane / Persistent State Plane separation is a similar architectural distinction at a different layer: FAF specifies file formats and operations; PAMSPEC specifies the authoritative state semantics behind those operations (object identity, version identity, monotonic ordering, minimal provenance, scope isolation, deletion semantics, and so on). YAML vs JSON is a real serialization difference; the more interesting question is whether the semantic distinctions map cleanly between the two.

I'd genuinely appreciate:

1. **Correction on any part of the framing above.** If FAF's scope overlaps PAMSPEC's authoritative-state territory more than I've assumed, please tell me. I'd rather adjust PAMSPEC now than build a mistaken distinction into a coordination artifact.
2. **Whether cross-reference in a future PAMSPEC "Related work" section would be welcome.** PAMSPEC intends to reference FAF/FAFM there. If FAF Foundation has a preferred citation form, I'll follow it.
3. **A short discussion of the memory-to-context "promotion" concept.** FAF's context/memory split anticipates part of PAMSPEC's lifecycle language. If there's a concept or operation on the FAF side that PAMSPEC should learn from (or align with), I'd like to know about it before PAMSPEC's Lite semantics stabilize in an upcoming internal branch.

I am NOT asking you to adopt PAMSPEC, endorse it, or coordinate at any deeper level than accurate cross-reference. If FAF Foundation prefers no coordination at this stage, that's an acceptable answer.

The full concept-by-concept crosswalk (PAMSPEC vs AIMEM, SAIHM, FAF/FAFM, Portable Agent Memory, MCP, and the W3C AI Agent Memory Interoperability CG) is at: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/main/reviews/standards-and-research-crosswalk.md

Thank you for the work you've published in this space.

With respect,

(maintainer signature)

---

## Notes for the sender (delete before sending)

- Recheck `team@faf.one` at the datatracker source URL on the day of sending. `team@` addresses can move.
- Confirm the two GitHub links resolve to files on `main`.
- FAF has three primary-source contact surfaces: the I-D email (`team@faf.one`), the foundation site (`https://foundation.faf.one`), and the GitHub repo (`https://github.com/Wolfe-Jam/faf`). This draft uses the I-D email because it's the canonical contact channel for I-D authorship. Do not blind-copy the other two channels without a reason.
- Set From: to the maintainer's actual identity; do not send from an unrelated address.
- Log the send in `coordination-log-<recipient>-<YYYY-MM-DD>.md`.
