# Outreach draft — SAIHM and the W3C AI Agent Memory Interoperability Community Group

**Status: draft, not sent.**

There are two distinct outreach recipients here. They share a chair, but they are distinct channels and should not be conflated:

- **SAIHM as an I-D** — the author of `draft-saihm-memory-protocol-01` at `architect@saihm.coti.global`.
- **The W3C AI Agent Memory Interoperability Community Group** — the CG's public mailing list `public-ai-agent-memory-interop@w3.org`.

Two separate messages are drafted below. **Send them separately.** Do not paste one into the other's venue.

---

## Message A — to the SAIHM I-D author

**To:** Russell Jackson — `architect@saihm.coti.global`
(Source: Authors' Addresses section, `draft-saihm-memory-protocol-01`. Recheck before sending.)

**From:** (maintainer to fill in personal name and email)

**Subject:** PAMSPEC — internal work-in-progress on agent-memory architecture; coordination note re: SAIHM

---

Dear Russell,

I'm writing about `draft-saihm-memory-protocol-01`. I've been developing a separate, still-internal project called PAMSPEC — the Persistent Agentic Memory Architecture Specification. It sits in an adjacent part of the agent-memory design space to SAIHM, and I want to introduce it accurately and describe how I intend to keep the two efforts distinct.

**About PAMSPEC in one paragraph.** PAMSPEC defines a provider-neutral architecture and authoritative state model for persistent agent memory — scope, stable identity, immutable versions, provenance, state transitions, event history, and isolation of derived retrieval indexes. It is intended to map to multiple interchange formats and protocol bindings rather than mandate one storage engine or transport. Positioning note: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/main/coordination/pamspec-positioning-note.md

**About PAMSPEC's status.** PAMSPEC has NOT been submitted to the IETF Datatracker. No revision has been posted. Active development uses the docname `draft-infantado-agent-memory-architecture-latest`. If and when a first submission occurs, it will be `-00`. Nothing here should be read as a competing IETF filing.

**How PAMSPEC relates to SAIHM.** From what I've read, SAIHM's primary focus is on the memory-layer protocol — post-quantum crypto, wallet-derived per-cell keys, revocable sharing, cryptographic erasure aligned with GDPR Article 17, audit anchoring — and is currently in the Independent Submission Stream under ISE review. PAMSPEC's focus is different: it's the authoritative-state architecture, versioning, provenance, and scope isolation that a memory service would apply *behind* whatever cryptographic and sharing semantics SAIHM specifies. In principle the two are complementary rather than overlapping, but I would appreciate correction if that framing is wrong.

Two things I'd genuinely welcome from you:

1. **Correction on the framing above.** If SAIHM's scope extends into areas I've placed on PAMSPEC's side of the line (or vice versa), please tell me. I'd rather adjust PAMSPEC's own boundary now than push forward a mistaken distinction.
2. **Whether cross-reference in a future PAMSPEC "Related work" section would be welcome.** I intend to reference SAIHM there. If SAIHM has similar preferred wording or a specific citation form you'd like used, I'll follow it.

I am not asking you to adopt PAMSPEC, endorse it, or coordinate at any deeper level than accurate cross-reference. If SAIHM has stronger opinions on where the boundary should sit, I'm listening.

The full concept-by-concept crosswalk (PAMSPEC vs AIMEM, SAIHM, FAF/FAFM, Portable Agent Memory, MCP, and the W3C CG) is at: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/main/reviews/standards-and-research-crosswalk.md

Thank you for the work you've published in this space.

With respect,

(maintainer signature)

---

## Message B — to the W3C AI Agent Memory Interoperability CG mailing list

**To:** `public-ai-agent-memory-interop@w3.org`
(Source: W3C CG page https://www.w3.org/community/ai-agent-memory-interop/. Recheck before sending; confirm the list is the primary published contact channel.)

**From:** (maintainer to fill in personal name and email)

**Subject:** [PAMSPEC] Introduction, positioning, and coordination note

---

Hello,

I'm writing to introduce the group to a separate, still-internal project called PAMSPEC — the Persistent Agentic Memory Architecture Specification. This message is a positioning note and a coordination inquiry, not a proposal to the CG.

**About PAMSPEC in one paragraph.** PAMSPEC defines a provider-neutral architecture and authoritative state model for persistent agent memory — scope, stable identity, immutable versions, provenance, state transitions, event history, and isolation of derived retrieval indexes. It is intended to map to multiple interchange formats and protocol bindings rather than mandate one storage engine or transport. Positioning note: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/main/coordination/pamspec-positioning-note.md

**About PAMSPEC's status.** PAMSPEC has NOT been submitted to the IETF Datatracker. No revision has been posted. Active development uses the docname `draft-infantado-agent-memory-architecture-latest`. If and when a first submission occurs, it will be `-00`. Please do not read this as a competing standards filing.

**How PAMSPEC relates to this CG's scope.** I understand the CG's stated deliverables include a use-case catalogue, a baseline interoperability profile, a conformance and test-vector pack (covering encoding, identity binding, envelope, erasure-receipt verification), and a regulatory crosswalk — and that the CG normatively references `draft-saihm-memory-protocol` and has committed to not develop a competing normative specification. If I've read that correctly, PAMSPEC sits alongside the CG's scope, not inside or against it: PAMSPEC targets the authoritative state architecture that a memory service applies internally, distinct from cryptographic identity, sharing, and erasure semantics that SAIHM (and by reference the CG) covers.

I would appreciate:

1. **Correction if the scope framing above is wrong** — particularly if any CG deliverable is expected to cover the same authoritative-state ground PAMSPEC targets.
2. **Guidance on whether the CG considers PAMSPEC-style cross-reference welcome** — for instance, whether PAMSPEC listing the CG in a "Related work" section is useful, or whether the CG would prefer PAMSPEC to remain unmentioned until the CG's own deliverables mature.

I am NOT asking the CG to endorse PAMSPEC, adopt PAMSPEC, or take any formal action. This is a courtesy notice and a scoping question. The CG's own governance and deliverables timeline are its own; PAMSPEC will not attempt to shape either.

The full concept-by-concept crosswalk against SAIHM, AIMEM, FAF/FAFM, Portable Agent Memory, MCP, and the CG itself is at: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/main/reviews/standards-and-research-crosswalk.md

Happy to correspond on-list or off-list, as the group prefers.

Regards,

(maintainer signature)

---

## Notes for the sender (delete before sending)

- Send Message A and Message B SEPARATELY. Do not cross-post.
- Confirm both destinations (I-D email, W3C list) at their primary sources on the day of sending. The CG page is the source for the list address; the I-D text is the source for the personal email.
- The chair of the CG is also the SAIHM author. Do NOT use the SAIHM I-D email as a CG contact channel, or vice versa.
- Set From: to the maintainer's actual identity; do not send from an unrelated address.
- Public list posts are archived permanently — proofread Message B especially carefully.
- Log both sends separately in `coordination-log-<recipient>-<YYYY-MM-DD>.md`.
