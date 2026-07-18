# Practitioner outreach — Letta maintainer or active user

**Status: draft. HOLD — do NOT send. Reviewer verdict: build a Letta adapter or a smaller Letta migration probe before asking Letta maintainers to validate a conclusion based on Mem0 evidence.**

**Suggested recipient (verify before sending):** A Letta project maintainer or an active user working on memory-model migrations. Reach out via a Letta GitHub issue or discussion; do NOT extract personal contact from social profiles.

**Subject:** Memory-model migration feedback — evidence report from PAMSPEC (public, pre-submission work)

---

Hi,

I'm developing PAMSPEC — the Persistent Agentic Memory Architecture Specification — as a public, pre-submission work in progress. It targets the correctness of authoritative agent memory across create/update/history/delete operations, particularly the properties that matter when memory has to *migrate* between stores or versions.

I ran a small evidence sprint against Mem0 OSS 2.0.12 to check whether PAMSPEC's proposed requirements describe problems that actually happen. The report is at:
https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/6ae806bbeb591c82c91236a191514b1775f24dbf/validation/reports/real-framework-validation-report.md  <!-- replace 6ae806bbeb591c82c91236a191514b1775f24dbf with the V08.1 commit or wait until merged to main -->

Letta is on my short list of frameworks to run the same eight scenarios against, but I haven't done that work yet. Before I do, I'd genuinely value your view on **whether the memory-model migration pain-class we've mapped to Letta issue #2117 matches your experience.**

The report cites Letta memory-model migration as an issue class where stable identity, distinct version identity, and preserved prior content matter — properties Mem0 currently provides natively (scenario 2 in the report). Whether Letta provides them at the migration boundary is what I'd like to understand.

**Five specific questions:**

1. When Letta agents migrate from the original single-column memory model to the newer memory-block model, what is the actual failure mode users hit? Is it identity loss, content loss, provenance loss, timestamp loss, or something else?
2. If a portable memory contract guaranteed stable identity + distinct version identity + preserved prior content + preserved provenance, would that materially simplify Letta's migration work?
3. Letta memory blocks are described as always-present in the agent's context — is that a *storage* property or a *retrieval-eligibility* property in Letta's model? (This affects whether PAMSPEC's Working Memory concept should exist at all — see `validation/reports/working-memory-evidence.md` in the same repo.)
4. Which memory-integrity property is Letta's model strong on today that a portable contract should learn from?
5. Would you be interested in a Letta-side adapter that ran the eight PAMSPEC scenarios against Letta unmodified, so we could produce evidence comparable to the Mem0 report?

**What this outreach is not:** not asking for endorsement, adoption, or coordination beyond feedback. PAMSPEC has not been submitted to IETF. Active development is under `-latest`; the first possible posted revision is `-00`. A "no thanks" is a fine answer.

If any part of the framing above misrepresents Letta's architecture or migration pain, I'd rather hear the correction now than build on a wrong reading.

Thank you for the work on Letta.

Regards,

(maintainer signature)

---

## Notes for the sender (delete before sending)

- Verify current Letta maintainer / active user on the Letta GitHub repository at time of sending.
- Prefer a Letta GitHub Discussion or Issue over unsolicited personal email.
- Do NOT cite Letta issue #2117 by number unless you have verified the issue is current and still open at time of sending. Referencing it as a "class" is safer than as a specific ticket.
- Do NOT extract personal email from GitHub profiles for this outreach.
