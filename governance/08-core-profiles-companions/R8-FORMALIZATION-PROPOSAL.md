# R8 Formalization Proposal: Core, Profiles, and Companions

**Branch:** `governance/08-core-profiles-companions`  
**Base:** `c1b4380` (merge: R5 Mem0 enforcement and portability proof)  
**Status:** Draft — not yet merged  
**Scope:** Documentation only. No implementation changes, schema redesign, new framework work, or IETF submission.

---

## 1. Purpose

This document proposes the formal three-tier organizational structure for PAMSPEC requirements: **Core**, **Profiles**, and **Companions**. The structure is derived from the evidence collected in R5 (Mem0 enforcement and portability proof) and the R6 evidence model. It formalizes what was already empirically characterized, not what is newly designed.

---

## 2. Definitions

### 2.1 Core

Core requirements are the minimum behavioral guarantees that every conforming PAMSPEC implementation MUST satisfy, regardless of which profiles it declares. A conforming implementation that satisfies only Core is a valid PAMSPEC implementation; it does not need to support any Profile.

Core requirements are backed by:
- At least one normative MUST or MUST NOT in `draft-infantado-agent-memory-architecture-latest`
- At least one confirmed EvidenceRecord in a `validation/evidence/*.jsonl` chain
- For established Core (CR-1 through CR-6): at least one passing conformance test in the PAMSPEC-Lite profile that directly exercises the requirement

CR-7 (Deterministic Outcomes) is a provisional candidate Core requirement. It has R5 evidence and a draft anchor but lacks a direct normative bundle-determinism statement in the current draft and a dedicated PAMSPEC-Lite test case. It is included here to make the gap visible; it cannot be treated as established Core until those two conditions are met (OD-C3, OD-P1).

### 2.2 Profiles

Profiles are named, independently testable feature sets layered above Core. An implementation MAY declare support for zero or more Profiles. Profile conformance is tested by the dedicated conformance suite module for that profile.

Profile conformance is additive: a Profile declaration implies Core conformance plus the profile-specific behavioral guarantees.

Three profiles are currently formalized with passing harness suites:
- `PAMSPEC-Lite` — the Core behavioral profile
- `PAMSPEC-Delegation` — scoped permission grants
- `PAMSPEC-Subscribe` — event subscription and delivery

The following profiles are named in the draft but do not yet have harness suites; they are recorded here as placeholders:
- Ledger — strict event-ordering guarantees beyond PAMSPEC-Lite
- Relationships — object-to-object relationship semantics (§8.5)
- Retrieval — semantic query and derived-index guarantees (§7.8)
- Evaluation — validation-state lifecycle semantics (§9.2)
- Working Memory — experimental; not yet under normative development

### 2.3 Companions

Companions are non-normative artifacts that demonstrate or enable PAMSPEC conformance. They are not part of the specification text and do not carry normative status. Implementations are not required to use or ship any Companion.

Current companions:

| Companion | Location | Purpose |
|---|---|---|
| reference-python | `implementations/reference-python/` | Canonical SQLite-backed implementation; native conformance |
| Mem0EnforcementAdapter | `validation/r5_mem0_portability/mem0_enforcement_adapter.py` | Adapter enforcing PAMSPEC semantics over Mem0 2.0.12 |
| Portability bundle format | `validation/r5_mem0_portability/round_trip.py` | Deterministic export/import format for cross-implementation transport |
| MCP binding | `bindings/mcp/` | Draft binding and Python prototype implemented; not yet finalized or promoted as a stable Companion |
| Evidence tooling | `conformance/harness/evidence_emitter.py` | R6 EvidenceRecord emission and chain validation |
| Conformance harness | `conformance/harness/runner.py` | Profile runner and report generator |

---

## 3. Core Requirements

The following seven requirements constitute PAMSPEC Core. Each requirement is named, anchored to the draft, and backed by verified evidence. Detailed per-requirement mapping is in `R8-EVIDENCE-MAPPING.md`.

### CR-1: Stable Identity

An object's `object_id` is assigned at creation and MUST NOT change across any subsequent operation, including update, lifecycle transition, and deletion.

**Rationale:** Two independent implementations that receive the same portability bundle MUST agree on which object is which. Identity instability makes cross-implementation comparison undefined.

**Draft anchor:** §8.3 Object Identity

**Evidence:** `PAMSPEC.identity.stable_object_and_history_ledger` — `v08.s2.identity-history.probe` (native, Mem0 2.0.12 assigns stable IDs)

### CR-2: Immutable Scope

An object's scope MUST NOT change after creation. Any update or transition operation that supplies a different scope for an existing object MUST be rejected.

**Rationale:** Scope defines the isolation boundary and access control domain. Allowing scope mutation would allow cross-boundary data leakage.

**Draft anchor:** §7.5 Scope and Isolation Boundary — "Every Memory Object MUST resolve to exactly one authoritative Memory Scope."

**Evidence:** `PAMSPEC.scope.immutable_across_update` — `v08.s1.scope-immutability.probe` (gap, Mem0 native), `r5.scope_mutation_rejected` (gap, adapter-enforced)

### CR-3: Canonical Content

An object's `canonical_content` MUST be stored verbatim and returned unmodified on read. Extension fields within `canonical_content` MUST be preserved through create, update, export, and import.

**Rationale:** Frameworks that summarize or transform content on write break round-trip fidelity. PAMSPEC distinguishes canonical state (authoritative, verbatim) from derived indexes (non-authoritative).

**Draft anchor:** §8.1 Canonical Envelope; §7.6 Canonical and Derived State

**Evidence:** `PAMSPEC.extensibility.unknown_fields_survive_roundtrip` — `v08.s8.unknown-fields.probe` (gap), `r5.extension_field_preservation` (gap, adapter-enforced); `PAMSPEC.portability.mem0_to_refimpl_round_trip` — `r5.round_trip_pass` (emulated)

### CR-4: Immutable Versions

Every state-changing operation MUST create a new immutable Memory Version. Sequence numbers within a single object's history MUST be strictly increasing and MUST NOT be reused. Past versions MUST remain readable by `version_id`.

**Rationale:** Auditability and rollback require that the history ledger is append-only. Overwriting a version violates the provenance chain.

**Draft anchor:** §8.4 Versioning — "Every change to Authoritative State MUST create a new immutable Memory Version and MUST create a corresponding Event Ledger entry."

**Evidence:** `PAMSPEC.mutation.expected_version_conflict_rejection` — `v08.s3.expected-version.probe` (gap); `PAMSPEC.identity.stable_object_and_history_ledger` — `v08.s2.identity-history.probe`

### CR-5: Expected-Version Mutation

An update that supplies an `expected_version_id` MUST be rejected with `version_conflict` if the object's current version does not match. An update that supplies no `expected_version_id` MUST still create a new version without silently overwriting.

**Rationale:** Concurrent agents operating on the same object need a conflict-detection mechanism. Without expected-version checking, the last writer silently wins.

**Draft anchor:** §8.4 Versioning — "A modification using an obsolete expected version MUST fail with `version_conflict` and MUST NOT overwrite a newer version."

**Evidence:** `PAMSPEC.mutation.expected_version_conflict_rejection` — `v08.s3.expected-version.probe` (gap), `r5.expected_version_conflict` (gap, adapter-enforced)

### CR-6: Idempotency

A create operation that supplies an `idempotency_key` with identical request content MUST return the original result without creating a duplicate object. The same key with different request content MUST be rejected with `duplicate_operation`. Idempotency state MUST be durable: it MUST survive the implementation process restarting.

**Rationale:** Agents operating under at-least-once delivery semantics will replay failed operations. Without durable idempotency, retried creates produce duplicates that corrupt the memory state.

**Draft anchor:** §10.1 Create

**Evidence:** `PAMSPEC.mutation.idempotent_create` — `v08.s4.idempotency.probe` (gap), `r5.idempotency_key` (gap); `PAMSPEC.mutation.idempotent_create.durable_across_restart` — `r5.idempotency_restart_durable` (gap, SQLite sidecar durability proven)

### CR-7: Deterministic Outcomes *(provisional — candidate Core)*

An implementation that serializes the same set of objects into a portability bundle MUST produce the same normalized output on repeated calls, given identical object state. The normalized output MUST be independent of the call timestamp and process identity.

**Provisional status:** The current draft does not yet contain a direct normative MUST for bundle-deterministic serialization, and PAMSPEC-Lite has no test case that directly exercises this property. CR-7 is a candidate requirement recorded here to make the gap visible and to give R9 a concrete target. CR-1 through CR-6 are the established proposed Core.

**Rationale:** Cross-implementation comparison and evidence reproducibility require that the same inputs always produce the same bundle bytes. Non-determinism would make `results_artifact` SHA-256 pinning meaningless.

**Draft anchor:** §7.6 Canonical and Derived State — "Persistent State Plane is authoritative"; §8.1 Canonical Envelope (sequence monotonicity)

**Evidence:** `PAMSPEC.portability.deterministic_bundle_output` — `r5.bundle_determinism` (emulated, normalized bundle output verified)

---

## 4. Profiles

### 4.1 PAMSPEC-Lite (formalized)

**Suite module:** `conformance/suite/test_lite.py`  
**Runner profile key:** `PAMSPEC-Lite`  
**Cases (15):**

| Case | Requirement covered |
|---|---|
| `case_create_returns_object_and_version_ids` | CR-1 Stable Identity, CR-4 Immutable Versions |
| `case_read_returns_current_envelope` | CR-3 Canonical Content |
| `case_read_specific_version` | CR-4 Immutable Versions |
| `case_update_creates_new_version` | CR-4 Immutable Versions, CR-5 Expected-Version Mutation |
| `case_stale_expected_version_raises_version_conflict` | CR-5 Expected-Version Mutation |
| `case_missing_object_raises_object_not_found` | error semantics |
| `case_scope_isolation` | CR-2 Immutable Scope |
| `case_idempotent_create_returns_same_result` | CR-6 Idempotency |
| `case_idempotent_key_reuse_with_different_body_fails` | CR-6 Idempotency |
| `case_delete_creates_tombstone_and_blocks_default_read` | `PAMSPEC.deletion.tombstone_and_identity_reservation` |
| `case_lifecycle_transition_active_to_archived` | §9.1 Lifecycle State |
| `case_invalid_lifecycle_transition_rejected` | §9.5 State Transitions |
| `case_query_default_filters_apply` | §10 Operation Semantics (query) |
| `case_history_is_monotonic` | CR-4 Immutable Versions, §7.7 Event Ledger |
| `case_unknown_extension_fields_preserved_on_read` | CR-3 Canonical Content |

PAMSPEC-Lite is the current Core-oriented conformance suite but does not yet provide complete test coverage for every proposed Core requirement. Specifically: CR-2's write-path scope mutation rejection is not tested (only read-time isolation is tested); CR-7 bundle determinism has no direct test case. An implementation passing all 15 Lite cases satisfies CR-1, CR-3, CR-4, CR-5, and CR-6. CR-2 write-path and CR-7 require additional test coverage before PAMSPEC-Lite can serve as a complete Core conformance signal (see OD-P1).

### 4.2 PAMSPEC-Delegation (formalized)

**Suite module:** `conformance/suite/test_delegation.py`  
**Runner profile key:** `PAMSPEC-Delegation`  
**Cases (7):** grant/check/deny/revoke/time-window/usage-limit/object-restriction semantics.

Delegation is a separate profile because not all implementations need multi-agent access-control semantics. It layers on top of PAMSPEC-Lite.

### 4.3 PAMSPEC-Subscribe (formalized)

**Suite module:** `conformance/suite/test_subscription.py`  
**Runner profile key:** `PAMSPEC-Subscribe`  
**Cases (4):** event delivery, filter exclusion, cursor advance, close stops delivery.

Subscribe is a separate profile because event streaming requires infrastructure (queues, cursors) that not all implementations provide.

### 4.4 Placeholder Profiles (not yet under development)

The following profiles are named here for tracking. They have no harness suite and are not candidate for merge in R8 or any near-term milestone.

| Profile | Draft anchor | Status |
|---|---|---|
| Ledger | §7.7 Event Ledger | Placeholder — no suite |
| Relationships | §8.5 Relationships | Placeholder — no suite |
| Retrieval | §7.8 Derived Indexes | Placeholder — requires embedding-space formalization first |
| Evaluation | §9.2 Validation State | Placeholder — no suite |
| Working Memory | not yet in draft | Experimental — not under normative development |

---

## 5. Companions

Companions are non-normative. Their presence in this document does not make them part of PAMSPEC normative requirements.

### 5.1 reference-python

The canonical reference implementation. SQLite-backed, in-process. Passes PAMSPEC-Lite, PAMSPEC-Delegation, and PAMSPEC-Subscribe with `classification=native` evidence. Used as the import target in R5 portability proofs.

**Location:** `implementations/reference-python/pamspec_ref/service.py`

### 5.2 Mem0EnforcementAdapter

Wraps Mem0 2.0.12 (unmodified) to enforce PAMSPEC semantics that Mem0 does not natively provide. Maintains durable side state in a SQLite sidecar. R5 evidence establishes the following distinctions:

- **Native (Mem0 behavior):** object identity assignment (CR-1), append-only history log (partial CR-4)
- **Mem0 gap, adapter-enforced:** scope immutability (CR-2), expected-version conflict detection (CR-5), idempotency (CR-6), tombstone tracking (candidate CR-8)
- **Adapter-emulated portability:** round-trip fidelity (CR-3) and deterministic bundle output (CR-7 provisional) — provided by the adapter's sidecar storage and bundle format layer, not Mem0's native persistence

"Adapter-enforced" means Mem0 does not provide the behavior and the adapter adds it via the SQLite sidecar. "Adapter-emulated portability" means the guarantee is delivered by the bundle format layer on top of sidecar storage; Mem0's own storage is not the authoritative source.

**Location:** `validation/r5_mem0_portability/mem0_enforcement_adapter.py`

### 5.3 Portability Bundle Format

The deterministic export/import format used in R5. Objects are sorted by `object_id`, content is in canonical form, and the normalized JSON produces a stable SHA-256. Defined by `Mem0EnforcementAdapter.export_bundle()` and `round_trip.py`.

**Location:** `validation/r5_mem0_portability/round_trip.py`

### 5.4 Evidence and Conformance Tooling

The R6 evidence model (`EvidenceRecord` schema, emission harness, chain validator) and R7 conformance harness (profile runner, broken adapters, subprocess parity tests). These are used to generate and validate the evidence chains in `validation/evidence/`.

**Key files:**
- `conformance/harness/evidence_emitter.py` — `build_retrospective_record()` and `run_and_emit()`
- `conformance/harness/runner.py` — `run_profile()`, three registered profiles
- `scripts/validate_evidence.py` — chain-level invariant validation
- `scripts/validate_repository.py` — repository-wide validation including evidence chains
- `conformance/schemas/0.1-draft/evidence-record.schema.json` — JSON Schema 2020-12

### 5.5 MCP Binding

A PAMSPEC-over-MCP binding profile, tools definition (`bindings/mcp/tools.json`), and Python prototype server (`bindings/mcp/server-python/`) are already present in the repository. The binding defines MCP tools, resources, error mapping, discovery semantics, and idempotency semantics for PAMSPEC operations.

**Location:** `bindings/mcp/`

**Status:** Draft binding and Python prototype implemented; not yet finalized or promoted as a stable Companion. The open question for R9 is whether to stabilize and formally include this existing work as a Companion, or defer finalization to a post-submission milestone (see OD-X1).

---

## 6. What R8 Does Not Change

R8 produces only these three governance documents. It does not:

- Modify the draft specification text
- Add new normative requirements
- Change any schema
- Create new profiles or promote Working Memory
- Add conformance tests to any existing profile
- Change any implementation
- Touch the Mem0 adapter or reference-python
- Expand MCP scope
- Submit to IETF

The next implementation milestone after R8 is R9 (IETF -00 submission preparation), which requires R8's Core/Profile/Companion framing to be stable.
