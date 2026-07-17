# Real-world issue mapping

For each cited public issue, this document records what was observed, which PAMSPEC requirement (if any) would prevent it, and whether PAMSPEC currently makes that requirement normative and testable. Sources are named at the issue-tracker level; the maintainer should re-verify specific issue numbers against the primary source before external reference.

The mapping is deliberately narrow — only the three issue classes named in the R8 spec are included. Real-world evidence for PAMSPEC needs to grow beyond these three; this table is a starting point, not a completed audit.

## 1. Mem0 — scope mutation / cross-tenant leakage

- **Observed failure class:** `update(memory_id, metadata={"user_id": <different>})` silently changes the native scope field of a memory, moving it from one tenant to another without any explicit re-scope operation and without warning.
- **Affected framework:** Mem0 OSS.
- **Reproduced in scenario 7-1 (this sprint):** Yes. `after_native_user_id == "bob"` when the memory was created with `user_id="alice"`. Classification: **GAP**.
- **What PAMSPEC currently says:**
  - ADR-0029 §3.1 lists Memory Scope with enforcement as a normative Lite requirement whose concrete failure is "Two impls with mismatched scope enforcement leak a memory object across users/tenants/agents that should never have seen it (cross-scope read succeeds when it should return `object_not_found`)."
  - The `scope_id` field is described as immutable for a version in the draft's Memory Object Model section.
- **Does PAMSPEC directly prevent it?** *Partially.* PAMSPEC declares scope immutable at the version level, and any operation that would change scope is out of PAMSPEC's operation set. In binding to Mem0, an adapter would have to guard against `update(metadata={"user_id": ...})`. **What is missing in PAMSPEC today:** an explicit normative statement that a binding MUST NOT let a scope-mutating operation succeed silently, and a conformance case that verifies it. Adding that case is a natural R5/R8 follow-up.

## 2. Letta — memory-model migration without loss

- **Observed failure class:** Requests for migrating existing agent memory from the original single-column model to Letta's newer block-based memory model, specifically to preserve existing memory during the migration.
- **Affected framework:** Letta.
- **Reproduced in this sprint?** Not directly; Letta was not the framework under test in R8. The Mem0 evidence still speaks to migration concerns indirectly: without stable identity + distinct version identity + preserved prior content (scenario 2 — Mem0 has these natively), a migration cannot replay history losslessly.
- **What PAMSPEC currently says:** ADR-0029 §3.1 makes stable `object_id` and immutable `version_id` + monotonic `version_sequence` normative Lite requirements. The rationale explicitly cites replay history correctness.
- **Does PAMSPEC directly prevent it?** *Architecturally, yes.* A migration between two PAMSPEC-conformant stores would preserve identity + version chain + provenance by construction. **What is missing today:** PAMSPEC has no Letta adapter or Letta-mapping evidence. A future sprint should validate this claim by writing a Letta adapter and running the same eight scenarios. Until then, the claim is architectural, not empirical.

## 3. LangGraph — persistence/checkpointer state loss

- **Observed failure class:** `langgraph dev` ignored the configured persistent checkpointer and used an in-memory runtime, causing all agent state to disappear after restart.
- **Affected framework:** LangGraph.
- **Reproduced in this sprint?** Not directly; LangGraph was not the framework under test. The failure is architectural in nature — a runtime silently substituted a non-persistent state store for a persistent one.
- **What PAMSPEC currently says:** ADR-0029 §2.1 lists **Compute Plane vs Persistent State Plane separation** as *architectural context*, not a wire-level conformance requirement. The rationale is that "an implementation is not conformant to these; it either instantiates the pattern or it doesn't."
- **Does PAMSPEC directly prevent it?** *No — it describes the failure, but the current normative contract would not detect it.* This is a real limit of PAMSPEC's current design. Making a runtime "wire up a persistent memory service, not an in-memory stub" durable would require an operational-configuration requirement PAMSPEC deliberately does not enter. The value here is that PAMSPEC provides the vocabulary (Compute Plane / Persistent State Plane / Persistent State is not a substitutable transient) to make the failure describable and to require binding-level documentation. Making it *preventable* would require a runtime-configuration requirement PAMSPEC currently avoids.

## Aggregate

- 1 of 3 issues (Mem0 scope mutation) is directly probable by a PAMSPEC conformance case in the very-near-term, and reproducing it was straightforward.
- 1 of 3 (Letta migration) is architecturally addressed but requires a Letta adapter to validate empirically.
- 1 of 3 (LangGraph checkpointer state loss) is described but not preventable under PAMSPEC's current normative contract. PAMSPEC's honest posture is that this is an implementation-configuration failure that a memory-data-model spec cannot enforce without stepping outside its scope.

Do not force every issue to justify PAMSPEC. Two of three yield real leverage; one does not.
