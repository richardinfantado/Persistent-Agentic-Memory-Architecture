# Practitioner outreach — Mem0 maintainer or active contributor

**Status: draft, not sent.**

**Suggested recipients (verify current maintainer/contributor status before sending):** Mem0 project maintainer, active contributor to `mem0ai/mem0` on GitHub, or an author of recent Mem0 issues concerning scope, update, or search behavior. Contact via GitHub issue or discussion on the Mem0 repository. Do NOT extract personal email from GitHub profiles for this.

**Subject:** Feedback request — memory-behavior evidence report from PAMSPEC (public, pre-submission agent-memory architecture)

---

Hi,

I'm developing PAMSPEC — the Persistent Agentic Memory Architecture Specification — as a public, pre-submission work in progress. I recently ran a small evidence sprint against Mem0 OSS 2.0.12 to check whether PAMSPEC's proposed requirements describe problems Mem0 users actually experience. **I would value your feedback on whether the findings match your on-the-ground view.**

The evidence report is at:
https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/main/validation/reports/real-framework-validation-report.md

The eight scenarios exercised Mem0's public API only (no source modifications). Four are documented as **gaps** where Mem0 does not natively provide behavior that PAMSPEC's authoritative-state contract requires:

1. **Scope immutability.** `update(memory_id, metadata={"user_id": "bob"})` silently mutates the native `user_id` field. This reproduces the failure class in Mem0 issue #6342 category.
2. **Expected-version conflict.** `Memory.update` has no expected-version parameter; concurrent updates are last-write-wins.
3. **Idempotency-key.** `Memory.add` has no idempotency-key parameter; repeated identical adds create new memory ids.
4. **Derived-vector refresh on update.** `update(memory_id, text="dogs")` on a memory that was originally `"cats"` does not refresh the vector index. `search("cats")` still finds the updated memory.

**Five specific questions I'd genuinely appreciate your view on:**

1. Does this describe a real problem you (or Mem0 users you support) experience? Which of the four is most painful in practice?
2. Would semantics guaranteeing scope immutability, expected-version rejection, or derived-vector refresh simplify integration or migration work?
3. Which of the four requirements strikes you as unnecessary or artificial for how Mem0 is actually used?
4. What is missing from the list — a memory-integrity property PAMSPEC should require that this sprint did not test?
5. Would you be interested in consuming a contract like this (as a downstream layer over Mem0), or contributing to one (as an upstream Mem0 feature)?

**What this outreach is not:** I'm not asking you to endorse PAMSPEC, adopt PAMSPEC, or coordinate at any deeper level than technical feedback. PAMSPEC has not been submitted to IETF. Active development is under the `-latest` docname; the first possible posted revision is `-00`. If you don't have time for this, that is a valid answer.

If any part of the evidence report describes Mem0 behavior incorrectly, please tell me — I would rather correct that now than build coordination material on a wrong reading.

Thank you for the work on Mem0.

Regards,

(maintainer signature)

---

## Notes for the sender (delete before sending)

- Verify who the current active maintainer/contributor is at the time of sending. The list of active contributors on `mem0ai/mem0` should be checked on the day of sending, not assumed.
- Prefer a GitHub Discussion or Issue on the Mem0 repository over an unsolicited personal email. Public venues let other Mem0 users chime in.
- If a Mem0 issue that this evidence directly relates to (scope mutation, cross-tenant leakage, expected-version, derived-index staleness) is currently open, referencing it is welcome; do not fabricate issue numbers.
- Do not paste the evidence report content into the outreach message — link to it. Reduces message weight; keeps the source of truth in one place.
