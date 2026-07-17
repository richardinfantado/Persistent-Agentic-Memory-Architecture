# Decision: PAMSPEC scope boundary and anti-drift rule

## Status

**Proposed — decision-only.** This ADR establishes the intended scope
boundary and the anti-drift test that governs future feature
additions. It does NOT move files, edit schemas, rename profiles,
delete tests, change conformance behavior, rewrite the draft, or add
features. Any reclassification that follows will be executed under
separate branches (R4a, R4b, R4c, R5, R6, R8) after review.

## Date

2026-07-18 (revised)

## Context

Between the initial architecture (five foundational principles) and
the current source (16 schemas, 28 ADRs, 10 standard object types,
17 event types, 9 named conformance profiles, delegation,
subscription, evaluation-snapshot, resource-usage, and MCP binding),
PAMSPEC's surface has expanded well beyond its stated centre of
gravity. The R2 research crosswalk documents that adjacent standards
work (AIMEM, SAIHM, FAF/FAFM, W3C AI Agent Memory Interoperability
CG) now occupies parts of the same design space. Some of PAMSPEC's
own additions are either redundant with adjacent work, unproven
against academic evidence, or better classified as identity,
authorization, observability, or runtime concerns rather than
persistent memory.

The purpose of this ADR is to make the scope narrowing decision
explicitly, capture the four gates that gate any future addition,
capture the three-layer separation between architectural context and
normative requirements, and enumerate — without moving anything —
how every current concept classifies.

## Proposed decision

Adopt the four gates in §1 as the governing test. Adopt the
three-layer separation in §2 as the target structure for the first
`-00`. Adopt the classification in §3 as the target scope. Do NOT
execute file moves, schema edits, or draft rewrites in this ADR —
those are separate branches, gated on approval of this decision.

### 1. Anti-drift gates (four gates, all four required, all four auditable)

A capability belongs in the PAMSPEC normative core if and only if
**all four gates** hold. Each gate is stated to be checkable
independently, so every normative-core row in §3 must claim all four
gates AND name the concrete interoperability failure that gate 2
guards against.

1. **Persistent-memory boundary.** The concept concerns persistent
   memory semantics, or a security property necessary to preserve or
   interpret persistent memory. Adjacent concerns (identity,
   authorization, billing, observability, transport, streaming,
   runtime coordination) fail this gate.
2. **Concrete interoperability failure.** Leaving the concept
   unspecified would cause two independent implementations to
   exchange, update, retrieve, or interpret memory incompatibly.
   The row must name that failure concretely (a described scenario,
   not "in general").
3. **Core necessity.** An extension, binding, or optional profile
   cannot adequately preserve the interoperability property named
   under gate 2.
4. **Implementable specification.** The concept can be defined
   implementation-neutrally and tested through examples, schemas,
   or behavioral conformance cases.

Descriptive architectural material that fails any of these gates
does not become normative-core. It may still belong in
architectural context (§2 layer 1) so long as it is not phrased as
a wire-level conformance requirement.

### 2. Three-layer separation (architecture context / Lite normative / optional profiles)

Concepts fall into exactly one of the three layers below. The
distinction between "architectural context" and "normative Lite
semantics" is deliberate: descriptive architecture must not be
silently converted into a mandatory implementation surface.

#### 2.1 Architectural context (descriptive; NOT wire-level conformance)

These are foundational models that shape how PAMSPEC is understood.
They are prose and reasoning aids, not conformance fields. An
implementation is not "conformant" to these; it either instantiates
the pattern or it doesn't.

- Compute Plane versus Persistent State Plane separation.
- Authoritative versus derived state.
- Event Ledger as an architectural pattern (append-only history,
  ordering across authoritative changes). Behavioral requirements
  belong in the Ledger profile (layer 3).
- Isolation of Derived Indexes from authoritative state.

#### 2.2 Normative Lite semantics (must pass all four gates in §1)

Every row here MUST be justified against all four gates and name
its concrete interoperability failure in §3.

- Memory Scope with enforcement of isolation on read, write, query,
  export, and import.
- Stable object identity (`object_id`).
- Immutable version identity and monotonic ordering (`version_id`,
  `version_sequence`).
- Canonical Content (arbitrary typed payload).
- Minimal provenance (a small required block).
- Extensible object typing (mechanism for standard and extension
  types; NOT a normative cognitive taxonomy).
- Conditional Embedding Space identity (required only when an
  implementation carries embeddings).
- Basic operation semantics: `create`, `read`, `update`, `history`,
  `delete`.
- Concurrency: expected-version conflict semantics (`version_conflict`).
- Idempotency: idempotent `create` semantics.
- Error envelope.
- Minimal deletion semantics (see §4 below — deletion is locked at
  the Lite level, not deferred to a profile).

#### 2.3 Optional profiles

Each of these already passes gate 1 (persistent memory state), but
gate 3 (core necessity) fails: the capability CAN be adequately
expressed as an optional profile without going into core.

- Full Event Ledger ordering, replay, and atomicity — **PAMSPEC-Ledger**.
- Full lifecycle / availability / retention / validation governance
  — **Governance Profile**.
- Relationship Objects — **Relationship Profile**.
- Structured query beyond basic filters, semantic query, snapshots
  — **Query Profile**.
- Semantic retrieval / Embedding-index query — **Query Profile** (or its own).

### 3. Classification of every current concept

Each core row lists all four gates AND names the concrete
interoperability failure that gate 2 prevents. This is the audit
promised by §1.

#### 3.1 Normative Lite semantics (each MUST pass all four gates)

| Concept | (1) Memory? | (2) Concrete failure | (3) Cannot be extension/profile? | (4) Implementable? |
|---|---|---|---|---|
| Memory Scope + isolation enforcement | Yes | Two impls with mismatched scope enforcement leak a memory object across users/tenants/agents that should never have seen it (cross-scope read succeeds when it should return `object_not_found`). | Yes — cannot be an extension; every operation reads it. | Yes — schema + `case_scope_isolation`. |
| `object_id` (stable object identity) | Yes | Two impls with divergent identifier semantics silently create duplicates on re-import, or overwrite unrelated memory when identifiers collide. | Yes — identity is required by every operation. | Yes — schema + envelope test. |
| `version_id` + `version_sequence` (distinct identity + monotonic order) | Yes | Two impls that do not agree on distinct version identity replay history in the wrong order; expected-version updates cannot be checked; AIMEM already does not carry these (R2 App. A). | Yes — required by concurrency semantics. | Yes — schema + `case_update_creates_new_version`, `case_history_is_monotonic`. |
| Canonical Content (arbitrary typed payload) | Yes | Two impls that disagree on where the payload lives cannot exchange the data at all; the content is why memory exists. | Yes — the payload is the memory. | Yes — schema + read/write cases. |
| Minimal provenance (`actor_id`, `activity`, `recorded_at`; details in R5) | Yes | Two impls that drop or invent provenance cannot answer "who wrote this and when"; audit and rollback fail. R2 verdict: defensible design requirement (not proven mandatory, but concrete failure exists on the audit path). | Yes — dropping to a profile means Lite-conformant systems cannot audit at all. | Yes — schema + envelope test. |
| Extensible object typing (mechanism) | Yes | Two impls that lack an agreed extension mechanism either reject every new type or silently strip it; forward compatibility breaks. | Yes — extension mechanism itself must be in core to be authoritative. | Yes — schema `oneOf` between `standard_object_type` and `extension_object_type`. |
| Conditional Embedding Space identity | Yes (retrieval-integrity property) | Two impls that carry vectors from different models silently compare them and produce wrong retrieval on the same query. AIMEM already prohibits silent re-embedding. | Partly — the fact of the descriptor is core; individual descriptor fields (metric, canonicalization) can be profile-scoped. | Yes — schema + `case_...` when Embedding Space adopter exists. |
| `create`, `read`, `update`, `history`, `delete` operation semantics | Yes | Two impls that disagree on what these operations MEAN cannot round-trip anything. | Yes — base operation set. | Yes — behavioral conformance cases in `test_lite.py`. |
| Concurrency: expected-version conflict + `version_conflict` | Yes | Two impls that permit silent overwrite of a stale expected version corrupt authoritative state under normal concurrent update. AIMEM currently permits consumer discretion here (R2 App. A) — this is exactly the semantic gap that concrete failure names. | Yes — cannot be pushed to a profile without breaking the update contract. | Yes — `case_stale_expected_version_raises_version_conflict`. |
| Idempotency: idempotent `create` | Yes | Two impls that treat idempotency keys differently produce duplicate persistence under retry, or accept different content under the same key silently. | Yes — the idempotency semantics of `create` are part of the operation contract. | Yes — `case_idempotent_create_returns_same_result`, `case_idempotent_key_reuse_with_different_body_fails`. |
| Error envelope | Yes | Two impls that emit different failure shapes cannot cross-diagnose or programmatically retry; every consumer must special-case each producer. | Yes — the envelope is on every failure path. | Yes — `error.schema.json`. |
| Minimal deletion semantics (see §4) | Yes | Two impls that disagree on what "deleted" means round-trip deleted content as if it still exists, or lose identity so the same object can be silently recreated with the same id. | Yes — deletion behavior on the base operation set must be locked. | Yes — `case_delete_creates_tombstone_and_blocks_default_read` + §4 rules. |

**`PAMSPEC-Lite` profile definition** is a normative-core row too: it names the required subset of the above and is what implementers claim conformance to.

#### 3.2 Architectural context (not wire-level; not audited by the four gates)

| Concept | Purpose in the document |
|---|---|
| Compute Plane versus Persistent State Plane separation | Foundational model. Prose. |
| Authoritative versus derived state | Foundational model. Prose. |
| Event Ledger as an architectural pattern (append-only history, ordering of authoritative changes) | Foundational model. Behavioral ledger requirements are in the profile below. |
| Isolation of Derived Indexes from authoritative state | Foundational model. Prose. |

These appear in the first `-00` as architectural context. They are NOT called out as wire-level conformance fields.

#### 3.3 Optional profiles

Each satisfies gate 1 but fails gate 3 — the capability can be adequately expressed as an optional profile without going into core.

| Concept | Target profile | Rationale |
|---|---|---|
| Full Event Ledger — atomic version+event commit, replay, ordering guarantees | `PAMSPEC-Ledger` | Behavioral requirements distinct from the architectural context (§2.1). |
| Full lifecycle / availability / retention / validation governance | Governance Profile | R2 verdict: "plausible but unproven" as universal. Lite carries the slim subset in §4. |
| Relationship Objects (independently identified, versioned) | Relationship Profile | Not needed for basic exchange; adds significant surface. |
| Structured query beyond basic filters | Query Profile | Filter mechanics are useful but not universal. |
| Semantic query (embedding-based) | Query Profile (or its own) | Requires Embedding Space; not universal. |
| Snapshots | Query Profile | Advanced retrieval feature. |

#### 3.4 Experimental / companion (repository subtree; not in first `-00`)

Each fails at least one of gates 1-4 as an interoperability requirement OR lacks independent-implementation pressure. A repository profile would imply that PAMSPEC is standardizing the behavior; there is not yet enough evidence for that in these cases.

| Concept | Destination | Failing gate and reason |
|---|---|---|
| Delegation Object | `experimental/delegation/` | Gate 1 fails: identity/authorization, not memory. R2 verdict: partly contradicted. Active agent-identity draft landscape covers this. |
| Subscribe operation | `experimental/subscribe/` | Gate 1 fails: runtime coordination / event streaming, not memory. |
| Tool invocation / tool result archives | `experimental/tool-trace/` | Gate 1 fails: MCP already models tool calls in-band. |
| Actor `attestation` block | `experimental/actor-attestation/` (or coordination with AIP) | Gate 1 fails: identity concern; multiple active agent-identity I-Ds cover it. |
| **Working Memory type + Promote operation** | `experimental/working-memory/` | Gate 1 boundary: portable Working Memory is described as *outside academic evidence* in R2. There is not yet enough cross-implementation pressure for a repository profile; keep in experimental until a concrete cross-implementation failure and an adopter exist. Graduation to a profile requires a new ADR. |
| **Evaluation Snapshot** | `experimental/evaluation/` | Gate 1 fails: evaluation snapshots are testing infrastructure, not exchange semantics. Anti-drift boundary explicitly excludes adjacent concerns. Graduation to a profile requires a new ADR. |
| MCP binding profile | `bindings/experimental/mcp/` (see §5) | Binding, not a memory profile. Retained under `bindings/` so the binding-vs-profile distinction is preserved; nested under `experimental/` so the non-normative status is unmistakable. |
| `quality_signals` block | `experimental/quality-signals/` | Gates 2 and 3 fail: no named consumer for these signals in the exchange contract. |

#### 3.5 Removed and re-classified telemetry (field-level disposition)

`memory-event.schema.json` currently carries a `resource_usage` block whose fields do not all warrant the same treatment.

| Field | Disposition | Rationale |
|---|---|---|
| `input_tokens` | **Remove** | Billing/observability; gate 1 fails. |
| `output_tokens` | **Remove** | Billing/observability; gate 1 fails. |
| `cached_input_tokens` | **Remove** | Billing/observability; gate 1 fails. |
| `wall_clock_ms` | **Remove** | Observability latency; gate 1 fails. |
| `compute_ms` | **Remove** | Observability latency; gate 1 fails. |
| `cost_amount` | **Remove** | Billing; gate 1 fails. |
| `cost_currency` | **Remove** | Billing; gate 1 fails. |
| `cost_unit` | **Remove** | Billing; gate 1 fails. |
| `region_ref` | **Remove** | Deployment metadata; gate 1 fails. |
| `model_ref` | **Evaluate for relocation to provenance-generation context** | Reproducibility metadata for model-generated memory. Not billing. R5 (Lite simplification) will decide whether this belongs inside `provenance` for `object_type = "claim" \| "summary"` or under an optional generation-context block. Removed from `resource_usage`; destination decided in R5. |
| `provider_ref` | **Evaluate for relocation to provenance-generation context** | Same as `model_ref`. Removed from `resource_usage`; destination decided in R5. |

Nothing is preserved merely because it existed. Nothing that carries reproducibility metadata is discarded under the label "billing."

### 4. Minimal deletion semantics (locked at the Lite level)

Deletion is a core operation. It cannot remain underspecified while the governance machinery moves to an optional profile. The Lite level locks the following:

- A successful `delete` MUST create a persistent deletion marker or a terminal deleted Memory Version (tombstone).
- After a successful `delete`, ordinary `read` MUST NOT return the deleted content and MUST raise `object_deleted` (or the binding's equivalent error).
- Identity MUST be preserved sufficiently to prevent accidental recreation or stale resurrection: subsequent `create` with the same `object_id` MUST be treated as an error or as an idempotent replay of the deletion, at the implementation's choice; it MUST NOT silently recreate the object as if it had never been deleted.
- Version history remains inspectable via `history` (subject to profile-level Availability rules).
- The Lite level does NOT require: redaction, legal hold, retention schedules, physical purge, restoration policy, erasure evidence, or content-free tombstone metadata beyond what Lite already stores.

Governance profiles MAY add:

- redaction,
- legal hold,
- retention schedules,
- physical purge,
- restoration policy,
- erasure evidence.

This gives every Lite implementation a deterministic delete contract while leaving records-management to those who need it.

### 5. Lite state subset (locked)

Lite is defined against a slim subset of the state dimensions. The full state machinery moves to the Governance Profile.

Locked minimal Lite subset:

- `lifecycle_state`: `active | archived`
- `availability_state`: `available | deleted`
- **No mandatory Retention State** at Lite.
- **No mandatory Validation State** at Lite.

Rationale for retaining two slim dimensions rather than dropping Lifecycle entirely: existing behavior already distinguishes "archive" (present, not surfaced by default) from "delete" (tombstoned per §4). Removing Lifecycle would force implementations to conflate the two. Retention and Validation impose governance processes a prototype may not have and belong in the Governance Profile.

### 6. Planned file-move and impact matrix (planning only — NOT executed here)

Execution is split across four branches (R4a, R4b, R4c, R5) as detailed under §7 below. **No files are moved by this ADR.**

| Source path (current) | Planned destination | Branch | Impact scope |
|---|---|---|---|
| `memory-event.schema.json` `resource_usage` block (remove `input_tokens`, `output_tokens`, `cached_input_tokens`, `wall_clock_ms`, `compute_ms`, `cost_amount`, `cost_currency`, `cost_unit`, `region_ref`; hold `model_ref` and `provider_ref` for R5 decision) | **removed / relocated field-level** | **R4a** | ADR-0022; test vector `event-with-resource-usage.json`; spec `draft-*.md` `resource_usage` paragraph. |
| `schemas/0.1-draft/delegation.schema.json` | `experimental/delegation/schema.json` | **R4b** | validator schema-list; test-vector routing in `scripts/validate_test_vectors.py`; ADR-0024 cross-refs; delegation test vectors; reference-impl `pamspec_ref/delegation.py`; conformance harness Delegation profile; spec delegation section; CI workflow references. |
| `schemas/0.1-draft/subscription.schema.json` | `experimental/subscribe/schema.json` | **R4b** | validator schema-list; ADR-0023; subscription-related event types (need re-scoping decision in R5); reference-impl `pamspec_ref/subscription.py`; conformance harness Subscribe profile; spec Subscribe section. |
| `schemas/0.1-draft/tool-invocation-content.schema.json`, `tool-result-content.schema.json` | `experimental/tool-trace/` | **R4b** | validator schema-list; ADR-0020; tool-invocation and tool-result test vectors; standard-object-type enum in `common.schema.json` (coordinated with core-type freeze in R5). |
| `schemas/0.1-draft/evaluation-snapshot.schema.json` | `experimental/evaluation/schema.json` | **R4b** | validator schema-list; ADR-0027; evaluation test vectors; spec Evaluation section. |
| `schemas/0.1-draft/working-memory-content.schema.json` | `experimental/working-memory/schema.json` | **R4b** | ADR-0021; spec Type System + Promote operation paragraphs; `working-memory.json` valid vector; `working-memory-missing-task-ref.json` invalid vector. Standard-object-type enum update coordinated with R5. |
| `actor.schema.json` `attestation` sub-block | `experimental/actor-attestation/` | **R4b** | ADR-0026; test vector `attested-agent-actor.json`; may coordinate with AIP. |
| `common.schema.json` `quality_signals` definition | `experimental/quality-signals/` | **R4b** | ADR-0025; test vector `claim-with-quality-signals.json`; spec `quality_signals` paragraph. |
| `bindings/mcp/` | **`bindings/experimental/mcp/`** (nested, preserves binding-vs-profile distinction) | **R4b** | ADR-0019; `bindings/mcp/server-python/`; CI workflow if it references the path; spec MCP binding paragraph. |
| `profiles/governance/` (new) — full state transitions, redact, legal hold | new subtree | **R4c** | ADR-0004, ADR-0013; state-transition tables in spec; conformance suite lifecycle cases; multiple test vectors. |
| `profiles/relationship/` (new) — Relationship Objects | new subtree | **R4c** | ADR-0005; `relationship.schema.json`; relationship test vectors. |
| `profiles/query/` (new) — structured/semantic query, snapshots | new subtree | **R4c** | Query schema (if any), spec Query and Retrieval Model section, query test vectors. |
| Slim Lite state subset (§5), minimal provenance (per R2 downgrade), simplified deletion semantics per §4, standard-object-type enum aligned with experimental moves | Lite schema + spec + conformance | **R5** | `common.schema.json`, `memory-object.schema.json`, `provenance.schema.json`, Lite spec section, `conformance/suite/test_lite.py`, test vectors. R5 owns semantic changes so schema, implementation, conformance suite, and documentation move together. |

### 7. Execution plan (branch split, not executed by this ADR)

Do NOT execute all file movements in one branch. Split by risk and semantic footprint:

- **R4a — Remove and extract telemetry.** Removes the resource_usage fields listed under §3.5 (except `model_ref`/`provider_ref`, which are held). Non-semantic for Lite. Small, contained. Cannot alter any conformance test that isn't specifically for `resource_usage`.
- **R4b — Move experimental capabilities.** Moves delegation, subscribe, tool-trace, evaluation, working-memory, attestation, quality-signals, and MCP binding to `experimental/*` and `bindings/experimental/mcp/`. Updates validator schema-lists, ADRs, test vectors, and conformance harness routing (retire the experimental-profile harness cases OR relocate them under `conformance/experimental/`). Does NOT alter Lite semantics.
- **R4c — Establish optional profile directories.** Creates `profiles/governance/`, `profiles/relationship/`, `profiles/query/` and relocates the corresponding material. Documents each profile's boundary. Does NOT alter Lite semantics.
- **R5 — Simplify Lite and align schemas/tests.** Owns all semantic changes: applies §4 deletion semantics, §5 Lite state subset, minimal provenance shape, standard-object-type enum trim, `model_ref`/`provider_ref` relocation decision, matching updates to `conformance/suite/test_lite.py`, and cross-file consistency.
- **R6 — Adjacent-author coordination.** Reaches out to AIMEM, SAIHM/W3C CG, FAF authors per ADR-0030. No repository changes required beyond coordination artifacts.
- **R8 — Rewrite draft-latest.** Aligns the draft to the narrowed core after R4a-R5 land.

R4a-R4c are non-semantic for Lite. R5 is where semantic changes concentrate; that split keeps schema, implementation, conformance suite, and documentation moving together and prevents an in-flight schema move from making conformance tests fail for the wrong reason.

### 8. Non-goals of this ADR

- Does NOT move any file.
- Does NOT edit any schema.
- Does NOT rename any conformance profile.
- Does NOT delete or alter any test.
- Does NOT change conformance behavior.
- Does NOT rewrite the draft.
- Does NOT add features.

Everything above is a proposal for the reviewer to accept, modify, or reject before any narrowing branches are authorized.

## Alternatives considered

- **Do not narrow.** Rejected: R2 documents overlap with adjacent standards, and the current source has grown beyond what the four gates permit in core.
- **Narrow more aggressively (drop Lifecycle entirely from Lite; remove all extensions).** Rejected: dropping Lifecycle conflates archive with deletion; removing extensibility prevents legitimate future types.
- **Keep Delegation and Subscribe in core.** Rejected: both fail gate 1 and active adjacent drafts make PAMSPEC's inclusion a duplication.
- **Promote Working Memory and Evaluation to optional profiles now.** Rejected: R2 shows insufficient independent-implementation pressure. A repository profile implies PAMSPEC is standardizing the behavior. Keep them in `experimental/` until an adopter and a concrete cross-implementation failure appear; graduation requires a new ADR.
- **Remove the entire resource_usage block indiscriminately.** Rejected: `model_ref` and `provider_ref` are provenance metadata for model-generated memory, not billing.
- **Move MCP binding to `experimental/mcp-binding/`.** Rejected: loses the binding-vs-profile distinction. Use `bindings/experimental/mcp/` instead.

## Consequences

- Establishes an auditable rule (§1) that governs every future feature-addition proposal.
- Distinguishes descriptive architecture from wire-level conformance (§2), preventing foundational models from being silently converted into mandatory implementation surfaces.
- Locks the deletion contract (§4) and the Lite state subset (§5) BEFORE any schema movement, so R5 can execute against a fixed target.
- Creates zero repository churn; downstream branches (R4a, R4b, R4c, R5) do that under explicit authorization.
- Forces every future ADR to answer the four gates and name the concrete failure it prevents.

## Interoperability impact

The four gates explicitly protect interoperability. The Lite deletion lock (§4) and state subset (§5) close the two gaps the reviewer identified: an unspecified core delete would let implementations diverge on the meaning of "deleted"; an unspecified Lite state subset would let R5 negotiate the subset piecemeal.

## Security impact

Scope isolation is retained in core as an engineering (security) requirement (R2 §3.2). Deletion is locked to prevent stale resurrection. Removing billing telemetry, Delegation, and Subscribe from core avoids PAMSPEC's role in domains where security guarantees are the identity/authz/streaming layer's job.

## Privacy impact

Retention and legal-hold governance move to an optional Governance Profile (§3.3). Any implementation that needs those guarantees adopts that profile; Lite implementations are not silently exposed to a governance regime they cannot implement.

## Unresolved questions

1. `model_ref` and `provider_ref` relocation destination: R5 will decide whether these belong inside `provenance` for `object_type = "claim" | "summary"`, under a separate `generation_context` block, or in a distinct experimental subtree.
2. Standard-object-type enum handling for experimental types: when R4b moves `working_memory`, `tool_invocation`, `tool_result` to `experimental/`, should their names remain in the `standard_object_type` enum in Lite (as reserved) or be removed? R5 owns this.
3. Conformance harness treatment of the retired Delegation/Subscribe profile cases: R7 built cases against the current harness. When R4b moves these to `experimental/`, do the cases move to `conformance/experimental/` or retire? Recommend the former to preserve the harness's ability to test experimental behavior when someone opts in.
4. Whether Event Ledger architectural context in the first `-00` needs a normative reference to the future `PAMSPEC-Ledger` profile, or whether that reference can be added when the profile lands.

## References

- R2 crosswalk: [`../reviews/standards-and-research-crosswalk.md`](../reviews/standards-and-research-crosswalk.md)
- ADR-0030 (AIMEM disposition, this branch)
- `draft-infantado-agent-memory-architecture.md`
