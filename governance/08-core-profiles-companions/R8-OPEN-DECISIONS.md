# R8 Open Decisions

**Branch:** `governance/08-core-profiles-companions`  
**Base:** `c1b4380`  
**Status:** Draft — not yet merged

This document lists open questions and decisions that require resolution before any of the R8 formalization materials can be considered normative. Items are grouped by the layer they affect: Core, Profiles, or Companions. Each item includes the decision to be made, the options under consideration, and the information needed to decide.

---

## Core Open Decisions

### OD-C1: Tombstone elevation to CR-8

**Decision needed:** Should tombstone behavior (`PAMSPEC.deletion.tombstone_and_identity_reservation`) be promoted to a named Core requirement (CR-8), or remain a conformance test case without a named CR entry?

**Current state:** The deletion behavior is tested by `case_delete_creates_tombstone_and_blocks_default_read` in PAMSPEC-Lite and backed by two gap evidence records (`v08.s5.tombstone.probe`, `r5.tombstone_deterministic`). It is not named as CR-1 through CR-7 in R8's proposal.

**Options:**
1. **Promote to CR-8** — Adds a named requirement with the same draft anchor (§9 Lifecycle), rationale, and evidence table as the existing conformance test. Aligns the CR list with what is already tested.
2. **Leave as test-only** — The deletion behavior remains implicitly covered by CR-1 (object_id stability post-deletion) and CR-4 (event ledger entry for delete). No new CR numbering.

**Blocker before deciding:** Whether the draft's §9 Lifecycle text will carry a MUST for tombstone identity reservation. If §9 currently uses SHOULD, promoting to a CR would overstate the normative strength.

**Owner:** PAMSPEC editorial

---

### OD-C2: Provenance elevation to CR-8 or CR-9

**Decision needed:** Should provenance (`PAMSPEC.provenance.source_actor_and_activity`) become a Core requirement?

**Current state:** §8.6 Provenance exists in the draft, but R8 source audit did not confirm whether it carries normative MUST language for `source_actor` and `source_activity`. Both evidence records (`v08.s6.provenance.probe`, `r5.provenance_preservation`) are classified gap.

**Options:**
1. **Promote to CR** — Requires confirming that §8.6 uses MUST and aligning the conformance test suite with a `case_provenance_fields_required` test.
2. **Leave as gap evidence only** — Provenance remains tracked in evidence but not as a named CR until the draft text is strengthened.

**Blocker before deciding:** Read §8.6 in the current draft and confirm whether `source_actor` is MUST or SHOULD. If SHOULD, option 2 is correct. This is a one-paragraph source check.

**Owner:** PAMSPEC editorial

---

### OD-C3: Determinism scope for query results

**Decision needed:** Does CR-7 (Deterministic Outcomes) apply only to the portability bundle format, or also to in-memory query results?

**Current state:** `R8-EVIDENCE-MAPPING.md` notes that determinism is currently defined only for the bundle format. Query results from `query()` are returned in vector-similarity order, which is non-deterministic across implementations. The draft's §7.6 language ("Persistent State Plane is authoritative") addresses storage but not query-result ordering.

**Options:**
1. **Bundle-only** — CR-7 scope remains limited to serialized bundle output. Query result ordering is implementation-defined. Simplest for conformance testing.
2. **Extend to query results** — Requires specifying a sort key (e.g., `object_id`) for query results when no explicit sort is requested, and adding a conformance test case. Significantly harder to verify across embedding-based retrievers.

**Blocker before deciding:** Whether the IETF audience (R9 target) expects query-result determinism or only bundle determinism. This is a design decision, not a source-verification task.

**Owner:** PAMSPEC editorial + potential IETF reviewer input

---

### OD-C4: Cross-process idempotency guarantee

**Decision needed:** Does CR-6 (Idempotency) require that idempotency be enforced across concurrent processes accessing the same memory store, or only within a single process?

**Current state:** The SQLite sidecar in Mem0EnforcementAdapter uses WAL mode and a threading lock, providing in-process idempotency. Cross-process idempotency (multiple adapter instances against the same Mem0 collection and same sidecar file) is not tested. The R5 restart durability test (`r5.idempotency_restart_durable`) only proves that a second sequential process reads the same sidecar state; it does not test concurrent access.

**Options:**
1. **Single-process only** — CR-6 requires durability (across restart) but not concurrent-process atomicity. Current evidence is sufficient.
2. **Cross-process required** — Requires SQLite transaction isolation guarantees (EXCLUSIVE lock or SERIALIZABLE isolation) and a concurrent-write test. Changes the Mem0EnforcementAdapter implementation.

**Blocker before deciding:** Whether the agentic deployment model for PAMSPEC assumes single-process per memory store or multi-process shared stores. If multi-agent systems always run behind a single memory API server, option 1 is sufficient. If agents access the store directly, option 2 is required.

**Owner:** PAMSPEC architecture (Richard M. Infantado)

---

## Profile Open Decisions

### OD-P1: PAMSPEC-Lite CR coverage completeness *(R9 blocker)*

**Decision needed:** Should PAMSPEC-Lite add `case_scope_mutation_rejected` (testing CR-2 write-path enforcement) and `case_bundle_output_is_deterministic` (testing CR-7) before the profile is considered a complete Core conformance signal?

**Current state:** Two gaps exist:
1. `case_scope_isolation` tests read-time scope isolation but does not test that an update with a different scope is rejected. CR-2's write-path enforcement is tested only by R5 evidence (`r5.scope_mutation_rejected`), not by any PAMSPEC-Lite case.
2. CR-7 bundle determinism has no direct PAMSPEC-Lite test. The current proxy (`case_history_is_monotonic`) does not verify bundle serialization output.

Without closing these gaps, PAMSPEC-Lite cannot credibly claim to fully instantiate Core, and CR-7 cannot be promoted from provisional to established Core.

**Options:**
1. **Add both missing cases to PAMSPEC-Lite** — Closes CR-2 write-path and CR-7 gaps. Requires adding two tests to `conformance/suite/test_lite.py` and updating the profile case count (15 → 17). Required before claiming full Core coverage.
2. **Add only `case_scope_mutation_rejected`** — Closes CR-2 write-path; leaves CR-7 provisional. Profile count becomes 16.

**Impact if neither is added:** Implementations can pass PAMSPEC-Lite without satisfying CR-2 write-path or CR-7. The formalization proposal cannot be presented as complete Core coverage.

**Owner:** Conformance engineering — R9 prep task, not an R8 implementation item

---

### OD-P2: Placeholder profile lifecycle

**Decision needed:** What is the formal lifecycle for a placeholder profile (Ledger, Relationships, Retrieval, Evaluation, Working Memory)?

**Current state:** R8 records five placeholder profiles. They have no harness suites, no evidence records, and no implementation work. The proposal includes them to prevent future naming collisions and to make the profile list visible.

**Options:**
1. **Informal registry only** — The placeholder entry in R8 is sufficient. Future milestones can claim profile names by producing a harness suite. No formal lifecycle document needed.
2. **Add a formal proposal gate** — A profile moves from Placeholder to Active only after (a) a draft section anchor exists, (b) at least 3 test cases are written, and (c) at least one EvidenceRecord with claim_status=confirmed or inconclusive is emitted. This mirrors the Core requirement criteria.

**Recommendation:** Option 2 prevents premature profile declarations. Applies to Working Memory first since it is the most likely to be claimed in the near term.

**Owner:** PAMSPEC editorial

---

### OD-P3: PAMSPEC-Delegation dependency on PAMSPEC-Lite

**Decision needed:** Should PAMSPEC-Delegation's runner formally require PAMSPEC-Lite to pass first, or remain independently testable?

**Current state:** The proposal says Delegation "layers on top of PAMSPEC-Lite." However, the conformance harness (`conformance/harness/runner.py`) runs profiles independently. An implementation could claim Delegation without running Lite.

**Options:**
1. **Enforce prerequisite in runner** — The runner raises an error if PAMSPEC-Delegation is requested without a prior passing PAMSPEC-Lite run in the same session.
2. **Prerequisite by convention only** — The proposal states the dependency; implementations self-declare compliance with both. No runner enforcement.

**Blocker before deciding:** Whether CI pipelines will run profiles independently (option 2 is simpler) or in a dependency graph (option 1 requires runner changes).

**Owner:** Conformance engineering

---

## Companion Open Decisions

### OD-X1: MCP binding stabilization for R9 *(R9 blocker)*

**Decision needed:** Should the existing MCP binding work be stabilized and formally included as a Companion for R9, or deferred to a post-submission milestone?

**Current state:** The repository already contains a PAMSPEC-over-MCP binding profile, `bindings/mcp/tools.json`, a `bindings/mcp/server-python/` prototype, and defined MCP tools, resources, error mapping, discovery, and idempotency semantics. This is not a question of whether to start MCP work — it already exists. The question is whether to finalize and promote it as a stable Companion before IETF -00 submission.

**Options:**
1. **Stabilize for R9** — Audit the existing binding for completeness against Core (CR-1 through CR-6), write at least one round-trip test via the MCP server, promote to stable Companion in the R9 governance documents.
2. **Defer finalization to post-R9** — The existing work remains in `bindings/mcp/` as a draft artifact. The R9 submission does not reference it as a stable Companion. Finalization becomes a named milestone after -00 review.

**Constraint:** R9 is IETF submission preparation. If the MCP binding has unresolved gaps or untested paths, including it as a stable Companion adds risk to the submission narrative. Option 2 is lower risk unless the prototype already passes a basic round-trip test.

**Owner:** Richard M. Infantado (R9 scope decision)

---

### OD-X2: Mem0EnforcementAdapter maintenance commitment

**Decision needed:** Is the Mem0EnforcementAdapter a long-lived companion or a one-time proof artifact?

**Current state:** The adapter was designed specifically for R5 validation. It wraps Mem0 2.0.12 (pinned). If Mem0 releases 2.1.x or 3.x with breaking changes, the adapter will silently fail or produce incorrect results without any failure signal.

**Options:**
1. **Time-boxed artifact** — The adapter is explicitly documented as a proof artifact for Mem0 2.0.12 only. It will not be updated for future Mem0 versions. R5 evidence remains valid; new Mem0 evidence would require a new milestone.
2. **Living companion** — The adapter is maintained and updated with each major Mem0 release. Requires ongoing effort and a CI pin-bump process.

**Recommendation:** Option 1. The adapter's purpose was to generate R5 evidence. That evidence is in the chain at `r5.round_trip_pass` etc. and will not be retracted just because Mem0 upgrades. If future Mem0 compatibility is needed, start fresh from R5's adapter as a baseline.

**Owner:** PAMSPEC companion maintenance

---

### OD-X3: Evidence tooling versioning

**Decision needed:** The evidence schema is pinned at `0.1-draft`. What triggers a version bump, and what is backward compatibility policy?

**Current state:** `conformance/schemas/0.1-draft/evidence-record.schema.json` is the only schema version. The R6 evidence emitter emits records with `schema_version: "0.1-draft"`. All existing chain files use this version.

**Options:**
1. **Bump to `0.2-draft` on any additive change** — New optional fields trigger a minor bump. Incompatible changes (removing required fields, changing enum values) trigger a major bump. Old chains remain valid under their pinned version; the validator must support both.
2. **Stay at `0.1-draft` until IETF submission** — No version bumps before R9. The `0.1-draft` label signals pre-normative status. Post-R9, the schema becomes `1.0`.

**Recommendation:** Option 2. Pre-IETF versions should accumulate changes without proliferating version numbers. The `0.1-draft` label is already a signal of instability.

**Owner:** PAMSPEC editorial

---

## Decision Registry

| ID | Layer | Status | Owner | Blocking R9? |
|---|---|---|---|---|
| OD-C1 | Core | Open | Editorial | No — unless CR count changes |
| OD-C2 | Core | Open (needs §8.6 source check) | Editorial | No |
| OD-C3 | Core | Open (design decision) | Editorial + IETF input | Possibly — determinism scope affects -00 text |
| OD-C4 | Core | **Resolved (R9)** — restart durability required; cross-process atomicity is deployment concern. See `decisions/0031-idempotency-durability-scope.md`. | Architecture | Closed |
| OD-P1 | Profile | **Resolved (R9)** — `case_scope_mutation_rejected` and `case_bundle_output_is_deterministic` added; suite 15 → 17; all 143 tests pass. | Conformance engineering | Closed |
| OD-P2 | Profile | Open | Editorial | No |
| OD-P3 | Profile | Open | Conformance engineering | No |
| OD-X1 | Companion | **Resolved (R9)** — MCP stabilization deferred to post-R9 milestone. See `decisions/0032-mcp-companion-stabilization-deferred.md`. | Richard M. Infantado | Closed |
| OD-X2 | Companion | Recommended (option 1) | Companion maintenance | No |
| OD-X3 | Companion | Recommended (option 2) | Editorial | No |

**R9 blockers resolved:** OD-C4, OD-P1, and OD-X1 are all closed as of R9 (commit `e5d8856`). Remaining open decisions (OD-C1, OD-C2, OD-C3, OD-P2, OD-P3, OD-X2, OD-X3) do not block IETF -00 submission.
