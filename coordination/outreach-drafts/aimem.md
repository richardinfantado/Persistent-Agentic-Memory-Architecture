# Outreach draft — AIMEM

**Status: draft, not sent.**

**To:** Vu Duc Minh, MemoryAI — `founder@memoryai.vn`
(Source: Author's Address section, `draft-vu-aimem-bundle-00`. Recheck before sending.)

**From:** (maintainer to fill in personal name and email)

**Cc / Bcc:** none

**Subject:** PAMSPEC (internal work-in-progress on agent-memory architecture) — coordination questions on AIMEM

---

Dear Vu Duc Minh,

I'm writing about `draft-vu-aimem-bundle-00`. I've been working on a separate, still-internal project called PAMSPEC — the Persistent Agentic Memory Architecture Specification — that overlaps with parts of what AIMEM addresses. I'd like to share what PAMSPEC currently is, describe the overlap honestly, and ask a small number of technical questions so I can better distinguish the two efforts and coordinate where useful.

**About PAMSPEC in one paragraph.** PAMSPEC defines a provider-neutral architecture and authoritative state model for persistent agent memory — scope, stable identity, immutable versions, provenance, state transitions, event history, and isolation of derived retrieval indexes. It is intended to map to multiple interchange formats and protocol bindings rather than mandate one storage engine or transport. Full context and status is in a short positioning note in the repository: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/main/coordination/pamspec-positioning-note.md

**About PAMSPEC's status.** PAMSPEC has NOT been submitted to the IETF Datatracker. No revision has been posted. Active development uses the docname `draft-infantado-agent-memory-architecture-latest`. If and when a first submission occurs, it will be `-00`. I mention this so nothing here reads as a competing IETF filing — because there isn't one.

**How PAMSPEC relates to AIMEM.** I've reviewed `draft-vu-aimem-bundle-00` in some detail and produced a field-and-behavior mapping between PAMSPEC concepts and AIMEM's structure. Some things map cleanly (embedding vector storage; the SHA-256 integrity and COSE_Sign1 story; the shared position that consumers must not silently re-embed under a different model). Some things don't map today without extensions AIMEM `-00` doesn't yet define. And there is one unresolved semantic mismatch around expected-version conflict behavior that I'd like to understand better rather than assume incompatibility.

Based on that mapping, PAMSPEC's current disposition is:

- PAMSPEC and AIMEM remain separate. Coordination with you will be pursued.
- No PAMSPEC bundle. AIMEM already addresses the interchange-bundle interoperability problem; duplicating it would fragment the space.
- No normative AIMEM dependency at this time.
- No AIMEM profile yet. Publishing a PAMSPEC profile of AIMEM is deferred until coordination and mapping produce sufficient evidence to do it well.

The mapping detail is in Appendix A of a research crosswalk in the same repository: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/main/reviews/standards-and-research-crosswalk.md

**What I'd genuinely appreciate.** Seven open technical questions are in a separate file so this message stays short: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/main/coordination/aimem-technical-questions.md — they're framed as open questions, not defect reports. AIMEM's design choices may well be right for AIMEM's stated scope even where they differ from PAMSPEC's. Any answer is useful, including "not planned" or "out of scope for AIMEM."

I'd also welcome direct correction: if PAMSPEC has misread AIMEM's intent anywhere in the mapping, I'd rather fix that now than push it forward into a coordination artifact.

Finally: I am not asking you to endorse PAMSPEC, adopt PAMSPEC, or change AIMEM. If the useful outcome is simply that each project cites the other in "Related work" and stays out of each other's way, that's a good outcome.

Thank you for the work you've published in this space. Happy to correspond over email, on the datatracker, or in whatever venue suits you.

With respect,

(maintainer signature)

---

## Notes for the sender (delete before sending)

- Recheck `founder@memoryai.vn` at the datatracker source URL on the day of sending.
- Confirm the two GitHub links resolve to files that exist on `main`.
- Set From: to the maintainer's actual identity; do not send from an unrelated address.
- Log the send in `coordination-log-<recipient>-<YYYY-MM-DD>.md`.
- If a response comes back, pause before acting on it. Do not answer speculatively.
