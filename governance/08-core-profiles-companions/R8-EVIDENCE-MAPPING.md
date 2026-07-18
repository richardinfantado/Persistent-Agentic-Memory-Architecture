# R8 Evidence Mapping: Core Requirements

**Branch:** `governance/08-core-profiles-companions`  
**Base:** `c1b4380`  
**Status:** Draft — not yet merged

This document maps each of the seven PAMSPEC Core requirements (defined in `R8-FORMALIZATION-PROPOSAL.md`) to its authoritative sources: draft section, schema field, conformance test case, EvidenceRecord identifiers, implementation support status, and known limitations.

All requirement identifiers (e.g., `PAMSPEC.scope.immutable_across_update`) are the canonical `requirement_id` values appearing in `validation/evidence/mem0-r5-portability.jsonl` and `validation/evidence/mem0-r6-conformance.jsonl`. All probe identifiers (e.g., `v08.s1.scope-immutability.probe`) are `record_id` values in those same files.

---

## CR-1: Stable Identity

### Draft anchor
§8.3 Object Identity

### Schema field
`canonical_envelope.object_id` — opaque string, assigned at create, immutable.

### Conformance test cases (PAMSPEC-Lite)
- `case_create_returns_object_and_version_ids` — verifies `object_id` is returned on create and has stable type
- `case_read_returns_current_envelope` — verifies `object_id` in read response matches create response
- `case_delete_creates_tombstone_and_blocks_default_read` — verifies `object_id` persists in tombstone

### Evidence records

| record_id | requirement_id | classification | source |
|---|---|---|---|
| `v08.s2.identity-history.probe` | `PAMSPEC.identity.stable_object_and_history_ledger` | native | `mem0-r6-conformance.jsonl` |

**Classification rationale:** Mem0 2.0.12 natively assigns a stable UUID at add time and never reassigns it. No adapter intervention required. The conformance probe verified that the same `object_id` is returned on read, after update, and after a history query.

### Implementation support

| Implementation | Status | Notes |
|---|---|---|
| reference-python | Native | SQLite primary key for `object_id`; never updated |
| Mem0EnforcementAdapter | Native (Mem0 behavior) | Mem0 assigns stable UUIDs; adapter reads and surfaces the same id |

### Known limitation
Mem0 does not expose a way to pre-specify an `object_id` at create time. The R5 round-trip workaround (passing `object_id=orig_id` to `reference-python.create()`) is specific to reference-python's API. Cross-implementation portability with pre-specified identity requires both ends to accept a caller-supplied `object_id`.

---

## CR-2: Immutable Scope

### Draft anchor
§7.5 Scope and Isolation Boundary — "Every Memory Object MUST resolve to exactly one authoritative Memory Scope. Scope MUST NOT change after the object is created."

### Schema field
`canonical_envelope.scope` — string, set at create, never updated.

### Conformance test cases (PAMSPEC-Lite)
- `case_scope_isolation` — creates two objects in different scopes, verifies each is invisible from the other scope's query perspective

### Evidence records

| record_id | requirement_id | classification | source |
|---|---|---|---|
| `v08.s1.scope-immutability.probe` | `PAMSPEC.scope.immutable_across_update` | gap | `mem0-r6-conformance.jsonl` |
| `r5.scope_mutation_rejected` | `PAMSPEC.scope.immutable_across_update` | gap | `mem0-r5-portability.jsonl` |

**Classification rationale (gap):** Mem0 native API does not enforce scope immutability — an update call can supply a different `user_id` (the Mem0 scope analogue) and Mem0 will accept it. The adapter enforces this by checking the stored scope in the SQLite sidecar on every `update()` call and raising `PAMSPECError("scope_immutable")` if the scope differs. Because enforcement is in the adapter layer, not the underlying framework, the classification is gap.

### Implementation support

| Implementation | Status | Notes |
|---|---|---|
| reference-python | Native | Scope is stored at create; update path raises `ScopeImmutableError` if scope differs |
| Mem0EnforcementAdapter | Adapter-enforced | `_get_scope_info()` / `_set_scope_info()` in SQLite sidecar; check in `update()` |

### Known limitation
The conformance test `case_scope_isolation` probes read-time isolation but not write-time scope mutation rejection. The R5 test `r5.scope_mutation_rejected` tests mutation rejection on the adapter. The PAMSPEC-Lite suite does not yet include a `case_scope_mutation_rejected` test case; adding one would strengthen the Lite profile but is out of scope for R8.

---

## CR-3: Canonical Content

### Draft anchor
§8.1 Canonical Envelope — "canonical_content MUST be stored verbatim"; §7.6 Canonical and Derived State — "The Persistent State Plane is authoritative and normative."

### Schema fields
- `canonical_envelope.canonical_content` — verbatim object payload
- `canonical_envelope.extensions` — unknown/extension fields MUST be preserved

### Conformance test cases (PAMSPEC-Lite)
- `case_read_returns_current_envelope` — verifies canonical_content returned verbatim
- `case_unknown_extension_fields_preserved_on_read` — verifies extension fields survive create → read

### Evidence records

| record_id | requirement_id | classification | source |
|---|---|---|---|
| `v08.s8.unknown-fields.probe` | `PAMSPEC.extensibility.unknown_fields_survive_roundtrip` | gap | `mem0-r6-conformance.jsonl` |
| `r5.extension_field_preservation` | `PAMSPEC.extensibility.unknown_fields_survive_roundtrip` | gap | `mem0-r5-portability.jsonl` |
| `r5.round_trip_pass` | `PAMSPEC.portability.mem0_to_refimpl_round_trip` | emulated | `mem0-r5-portability.jsonl` |

**Classification rationale (gap/emulated):** Mem0 stores memory as a flat text string and does not preserve structured extension fields natively — unknown dict keys are discarded. The adapter serializes `canonical_content` to JSON and stores it in the SQLite sidecar, preserving extension fields through export/import. Round-trip fidelity (Mem0 → bundle → reference-python → re-export) is demonstrated as emulated because it requires the adapter's sidecar storage, not Mem0's own persistence.

### Implementation support

| Implementation | Status | Notes |
|---|---|---|
| reference-python | Native | Stores `canonical_content` as JSON blob; full round-trip fidelity |
| Mem0EnforcementAdapter | Adapter-enforced | Sidecar stores canonical_content; Mem0's own storage used for search/embedding only |

### Known limitation
Mem0's core semantic is to summarize/consolidate memories, not to store them verbatim. The adapter's sidecar storage is authoritative for canonical content, meaning Mem0's built-in memory text diverges from PAMSPEC canonical content if Mem0 applies consolidation logic. This is a fundamental gap: Mem0 is used as a vector-search layer, not as the authoritative store.

---

## CR-4: Immutable Versions

### Draft anchor
§8.4 Versioning — "Every change to Authoritative State MUST create a new immutable Memory Version and MUST create a corresponding Event Ledger entry. The sequence number MUST be strictly increasing. A Memory Version, once created, MUST NOT be modified."  
§7.7 Event Ledger — "State-changing operations MUST produce entries. Ledger entries MUST NOT be rewritten."

### Schema fields
- `canonical_envelope.version_id` — opaque string for the current version
- `canonical_envelope.sequence` — strictly increasing integer per object
- `version.version_id` — stable identifier for each immutable version

### Conformance test cases (PAMSPEC-Lite)
- `case_read_specific_version` — reads an older version by `version_id`; verifies it is not overwritten
- `case_update_creates_new_version` — verifies a new `version_id` is returned after update
- `case_history_is_monotonic` — verifies sequence numbers are strictly increasing across all versions

### Evidence records

| record_id | requirement_id | classification | source |
|---|---|---|---|
| `v08.s2.identity-history.probe` | `PAMSPEC.identity.stable_object_and_history_ledger` | native | `mem0-r6-conformance.jsonl` |
| `v08.s3.expected-version.probe` | `PAMSPEC.mutation.expected_version_conflict_rejection` | gap | `mem0-r6-conformance.jsonl` |

**Classification rationale (native/gap):** Mem0 maintains an append-only history log (queryable via `history(memory_id)`), which is native behavior. However, Mem0 does not expose `version_id` in any structured way: its history returns ADD/UPDATE/DELETE events without stable version identifiers. The adapter synthesizes `version_id` values and sequence numbers in the SQLite sidecar, making the structured version API adapter-emulated.

### Implementation support

| Implementation | Status | Notes |
|---|---|---|
| reference-python | Native | Full version table with `version_id`, `sequence`, immutable rows |
| Mem0EnforcementAdapter | Partially native (history log) + adapter-enforced (structured version_id) | `_get_version_id()`, `_get_version_seq()`, `_set_version()` in sidecar |

### Known limitation
Read-by-version-id is not possible on Mem0's native API. The conformance profile's `case_read_specific_version` passes on reference-python but is not covered by R5 evidence for Mem0. Reading a specific historical version via Mem0 requires reconstructing it from the history event log, which `_extract_content_sequence()` does for portability purposes, but not for general read-by-version-id.

---

## CR-5: Expected-Version Mutation

### Draft anchor
§8.4 Versioning — "A modification using an obsolete expected version MUST fail with `version_conflict` and MUST NOT overwrite a newer version."

### Schema fields
- `update_request.expected_version_id` — optional; if supplied, must match current version
- error code `version_conflict`

### Conformance test cases (PAMSPEC-Lite)
- `case_stale_expected_version_raises_version_conflict` — updates twice, second uses original version_id, expects `version_conflict`
- `case_update_creates_new_version` — provides correct expected_version_id, expects success

### Evidence records

| record_id | requirement_id | classification | source |
|---|---|---|---|
| `v08.s3.expected-version.probe` | `PAMSPEC.mutation.expected_version_conflict_rejection` | gap | `mem0-r6-conformance.jsonl` |
| `r5.expected_version_conflict` | `PAMSPEC.mutation.expected_version_conflict_rejection` | gap | `mem0-r5-portability.jsonl` |

**Classification rationale (gap):** Mem0's update API accepts any update without version checking. The adapter implements expected-version checks by storing current `version_id` in the sidecar and comparing on every `update()` call. Mismatch raises `PAMSPECError("version_conflict")`. This is entirely adapter-implemented, so the classification is gap.

### Implementation support

| Implementation | Status | Notes |
|---|---|---|
| reference-python | Native | `update()` raises `VersionConflictError` on stale `expected_version_id` |
| Mem0EnforcementAdapter | Adapter-enforced | Sidecar `_get_version_id()` check in `update()` before calling `mem0.update()` |

### Known limitation
If two concurrent callers read the same version and one updates it before the other, the second update will fail with `version_conflict` — this is correct PAMSPEC behavior. However, because the Mem0 adapter's check-then-update is not atomic at the Mem0 storage layer (only at the SQLite sidecar layer), a race between the sidecar check and the actual Mem0 write is theoretically possible in multi-process scenarios. The SQLite WAL mode and threading lock mitigate in-process races; cross-process races on the same Mem0 collection remain a known gap.

---

## CR-6: Idempotency

### Draft anchor
§10.1 Create — "If an `idempotency_key` is supplied and a prior create with the same key is on record, the implementation MUST return the original response without creating a new object. If the key is on record but the request body differs, the implementation MUST return `duplicate_operation`."

### Schema fields
- `create_request.idempotency_key` — optional string
- error code `duplicate_operation`
- idempotency state MUST be durable across process restart

### Conformance test cases (PAMSPEC-Lite)
- `case_idempotent_create_returns_same_result` — create twice with same key and body; verifies same `object_id` returned
- `case_idempotent_key_reuse_with_different_body_fails` — create once, retry with same key but different body; expects `duplicate_operation`

### Evidence records

| record_id | requirement_id | classification | source |
|---|---|---|---|
| `v08.s4.idempotency.probe` | `PAMSPEC.mutation.idempotent_create` | gap | `mem0-r6-conformance.jsonl` |
| `r5.idempotency_key` | `PAMSPEC.mutation.idempotent_create` | gap | `mem0-r5-portability.jsonl` |
| `r5.idempotency_restart_durable` | `PAMSPEC.mutation.idempotent_create.durable_across_restart` | gap | `mem0-r5-portability.jsonl` |

**Classification rationale (gap):** Mem0 has no idempotency key concept. The adapter implements idempotency by storing `(idempotency_key, content_hash, object_id)` in the SQLite sidecar's `idempotency_store` table. On `create()`, if the key is already present and content matches, the original `object_id` is returned. If the key is present and content differs, `PAMSPECError("duplicate_operation")` is raised. The durability test (`r5.idempotency_restart_durable`) verified that closing the adapter and creating a new one with the same sidecar file returns the original `object_id`.

### Implementation support

| Implementation | Status | Notes |
|---|---|---|
| reference-python | Native | `idempotency_store` table; `duplicate_operation` raised for key collision with different content |
| Mem0EnforcementAdapter | Adapter-enforced | SQLite `idempotency_store` table; `_get_idempotency()` / `_set_idempotency()` helpers |

### Known limitation
The sidecar path must be explicitly specified via `sidecar_path` on `Mem0EnforcementAdapter.__init__()`. If the caller uses `:memory:` (the default), idempotency is not durable. Real deployments MUST provide a persistent file path. The conformance test `test_idempotency_survives_adapter_restart` uses a `tempfile.mkstemp()` file and verifies durability; it FAILS if `:memory:` is accidentally used.

---

## CR-7: Deterministic Outcomes

### Draft anchor
§7.6 Canonical and Derived State — "The Persistent State Plane is authoritative and normative. Derived Indexes are non-authoritative and MUST NOT be used as the source of truth for any mutation."  
§8.1 Canonical Envelope — sequence monotonicity requirement implies deterministic serialization order.

### Schema fields
- `bundle.objects[]` — MUST be sorted by `object_id` for deterministic output
- `bundle.exported_at` — excluded from determinism comparison (timestamp is non-deterministic)

### Conformance test cases (PAMSPEC-Lite)
No direct Lite test case for bundle determinism. Covered by:
- `case_history_is_monotonic` (proxy: verifies canonical version order is stable)

### Evidence records

| record_id | requirement_id | classification | source |
|---|---|---|---|
| `r5.bundle_determinism` | `PAMSPEC.portability.deterministic_bundle_output` | emulated | `mem0-r5-portability.jsonl` |

**Environment manifest:** `validation/evidence/r5-environment-manifest.json` (sha256 pinned in evidence record)  
**Results artifact:** `validation/evidence/r5-determinism-results.json` (sha256 pinned in evidence record)

**Classification rationale (emulated):** Bundle determinism requires normalizing the serialized output. The `export_bundle()` / `round_trip.py` normalization sorts by `object_id` and removes timestamp fields before comparison. The determinism guarantee is enforced by the bundle format code, not the underlying Mem0 or reference-python storage. An implementation that exports objects in insertion order would fail determinism; sorting is mandatory and non-negotiable.

### Implementation support

| Implementation | Status | Notes |
|---|---|---|
| reference-python | Emulated (via bundle format) | `export_bundle()` sorts by `object_id` |
| Mem0EnforcementAdapter | Emulated (via bundle format) | `export_bundle()` sorts by `object_id`; Mem0's native `get_all()` order is not deterministic |

### Known limitation
Determinism is defined only for the portability bundle format, not for in-memory query results. A `query()` call may return objects in vector-similarity order (non-deterministic). The bundle format is the only PAMSPEC-normative serialization path. Implementations that skip the bundle format for cross-system transfer must specify their own determinism guarantee.

---

## Tombstone Requirement (not yet a named CR)

Tombstone behavior (delete creates a tombstone, identity is reserved, default read is blocked) is exercised by `case_delete_creates_tombstone_and_blocks_default_read` in PAMSPEC-Lite but is not yet promoted to a named Core requirement. The evidence record is:

| record_id | requirement_id | classification | source |
|---|---|---|---|
| `v08.s5.tombstone.probe` | `PAMSPEC.deletion.tombstone_and_identity_reservation` | gap | `mem0-r6-conformance.jsonl` |
| `r5.tombstone_deterministic` | `PAMSPEC.deletion.tombstone_and_identity_reservation` | gap | `mem0-r5-portability.jsonl` |

This is recorded here as a gap against CR-1 (Stable Identity) and CR-4 (Immutable Versions) and a candidate for elevation to CR-8 in a future milestone.

---

## Provenance Requirement (not yet a named CR)

Source actor and activity provenance (`canonical_envelope.provenance.source_actor`, `.source_activity`) is required by §8.6 Provenance but is not yet a named Core requirement because the draft does not yet define the full provenance model normatively. Evidence:

| record_id | requirement_id | classification | source |
|---|---|---|---|
| `v08.s6.provenance.probe` | `PAMSPEC.provenance.source_actor_and_activity` | gap | `mem0-r6-conformance.jsonl` |
| `r5.provenance_preservation` | `PAMSPEC.provenance.source_actor_and_activity` | gap | `mem0-r5-portability.jsonl` |

Candidate for elevation to CR-8 once §8.6 carries normative MUST language.

---

## Summary Table

| CR | requirement_id(s) | Classification | reference-python | Mem0EnforcementAdapter |
|---|---|---|---|---|
| CR-1 Stable Identity | `PAMSPEC.identity.stable_object_and_history_ledger` | native | native | native (Mem0 behavior) |
| CR-2 Immutable Scope | `PAMSPEC.scope.immutable_across_update` | gap | native | adapter-enforced |
| CR-3 Canonical Content | `PAMSPEC.extensibility.unknown_fields_survive_roundtrip`, `PAMSPEC.portability.mem0_to_refimpl_round_trip` | gap / emulated | native | adapter-enforced (sidecar) |
| CR-4 Immutable Versions | `PAMSPEC.identity.stable_object_and_history_ledger`, `PAMSPEC.mutation.expected_version_conflict_rejection` | native / gap | native | partially native + adapter-enforced |
| CR-5 Expected-Version Mutation | `PAMSPEC.mutation.expected_version_conflict_rejection` | gap | native | adapter-enforced |
| CR-6 Idempotency | `PAMSPEC.mutation.idempotent_create`, `PAMSPEC.mutation.idempotent_create.durable_across_restart` | gap | native | adapter-enforced (SQLite) |
| CR-7 Deterministic Outcomes | `PAMSPEC.portability.deterministic_bundle_output` | emulated | emulated (bundle format) | emulated (bundle format) |

**Gap count by implementation:**

- reference-python: 0 gaps on CR-1 through CR-7 (all native or emulated via bundle format which is designed behavior)
- Mem0EnforcementAdapter: 5 gaps (CR-2, CR-3, CR-5, CR-6, CR-7) — all requiring adapter enforcement or SQLite sidecar; CR-1 and partial CR-4 are native Mem0 behavior
