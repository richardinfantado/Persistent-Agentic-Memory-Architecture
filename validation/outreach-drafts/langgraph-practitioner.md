# Practitioner outreach — LangGraph maintainer or active stateful-agent builder

**Status: draft. HOLD — do NOT send. Reviewer verdict: PAMSPEC describes the LangGraph checkpointer failure but does not prevent runtime misconfiguration, which makes this weak outreach material for PAMSPEC's normative memory contract. Better retained as a scope-boundary example.**

**Suggested recipient (verify before sending):** A LangGraph project maintainer, someone actively building stateful multi-agent systems on LangGraph, or someone who has recently opened or commented on issues about `langgraph dev` checkpointer behavior. Reach out via a LangGraph GitHub issue or discussion.

**Subject:** Persistent-state contract feedback — evidence report from PAMSPEC (public, pre-submission work)

---

Hi,

I'm developing PAMSPEC — the Persistent Agentic Memory Architecture Specification — as a public, pre-submission work in progress. Its subject is the correctness of authoritative agent memory: identity, versioning, provenance, scope, deletion, and the distinction between authoritative and derived state.

I ran a small evidence sprint against Mem0 OSS 2.0.12 to check whether PAMSPEC's proposed requirements describe real problems agents actually encounter. The report is at:
https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/<COMMIT-SHA>/validation/reports/real-framework-validation-report.md  <!-- replace <COMMIT-SHA> with the V08.1 commit or wait until merged to main -->

The report cites a LangGraph-related issue class: `langgraph dev` ignoring the configured persistent checkpointer and silently substituting an in-memory runtime, causing all agent state to disappear on restart. PAMSPEC's *architectural* language (Compute Plane vs Persistent State Plane) describes this failure, but PAMSPEC's *normative* contract does not currently detect or prevent it — a memory-data-model spec can't force a runtime to wire up the right backing store. Honest limit.

I want your view on **whether a memory-data-model spec that stops before runtime-configuration enforcement is still useful for your work.**

**Five specific questions:**

1. Which is more valuable for stateful-agent development: a portable data model for memory (identity, versioning, provenance, scope, tombstones) that leaves runtime-wiring unspecified, or something that also constrains *how* the runtime attaches persistent storage?
2. LangGraph explicitly separates short-term (`Checkpointer`) from long-term (`Store`). Do these two feel like the same *kind* of memory expressed at different scopes, or genuinely different memory concepts? (This affects whether PAMSPEC's `working_memory` object type should exist — see `validation/reports/working-memory-evidence.md`.)
3. When Mem0 exhibits behaviors like "update silently mutates scope" or "update does not refresh the vector index," do LangGraph users see analogous behavior when swapping in different `Store` backends?
4. Would you be interested in a LangGraph-side adapter (over `Store`, `Checkpointer`, or both) that ran the eight PAMSPEC scenarios against LangGraph unmodified?
5. Is there a specific real failure your users hit that PAMSPEC's current normative core (see `validation/what-pamspec-is-for.md`) does NOT address, but should?

**What this outreach is not:** not asking for endorsement, adoption, or coordination beyond feedback. PAMSPEC has not been submitted to IETF. Active development is under `-latest`; the first possible posted revision is `-00`. A "no thanks" is a fine answer.

If the LangGraph checkpointer example in the evidence report is inaccurate or out of date, please correct it — I'd rather revise now than propagate a wrong claim.

Thank you for the work on LangGraph.

Regards,

(maintainer signature)

---

## Notes for the sender (delete before sending)

- Verify who the current active LangGraph maintainer or notable stateful-agent builder is at the time of sending. Do not assume long-lived roles.
- Prefer a LangGraph GitHub Discussion over a personal email or DM.
- If specific LangGraph issues about `langgraph dev` checkpointer behavior are open at time of sending, reference them by number ONLY after confirming they are the correct issues.
- Do not paste the evidence report body into the outreach; link.
