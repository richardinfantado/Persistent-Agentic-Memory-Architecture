# Decision: PAMSPEC scope boundary and anti-drift rule

## Status

**Proposed — decision-only.** This ADR establishes the intended scope
boundary and the anti-drift test that governs future feature
additions. It does NOT move files, edit schemas, rename profiles,
delete tests, change conformance behavior, rewrite the draft, or add
features. Any reclassification that follows will be executed under
separate branches after review.

## Date

2026-07-18

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
explicitly, capture the four-part test that gates any future
addition, and enumerate — without moving anything — how every
current concept classifies.

## Proposed decision

Adopt the four-part anti-drift rule below as the governing test.
Adopt the scope classification in §3 as the target scope for the
first `-00` submission. Do NOT execute file moves, schema edits, or
draft rewrites in this ADR — those are separate branches, gated on
approval of this decision.

### 1. The four-part anti-drift rule

A capability belongs in the PAMSPEC normative core if and only if
**all four** conditions hold:

1. **Interoperability failure:** Two independent implementations
   would otherwise exchange the same persistent-memory concept with
   materially incompatible semantics.
2. **Cannot be handled by extension or profile:** The concept cannot
   be adequately expressed through an extension mechanism or an
   optional profile outside the normative core.
3. **Concrete failure named:** A specific, documentable
   interoperability failure can be named — a concrete example of
   two systems miscommunicating in the field.
4. **In-scope: persistent memory state.** The capability concerns
   persistent memory state — not general runtime coordination,
   transport behavior, identity, authorization, billing, or
   observability.

If any one of the four conditions fails, the feature does NOT
belong in the PAMSPEC normative core. It may belong in an optional
profile, in a companion document, in an experimental repository
subtree, or outside PAMSPEC entirely. Which of those homes is the
right one is decided per-feature under §3 below.

The fourth condition is deliberate: without it, adjacent concerns
(identity, authorization, streaming, observability) tend to pass
the first three conditions through creative reasoning. Persistent
memory state is what PAMSPEC standardizes; everything else
belongs elsewhere.

### 2. Proposed first-`-00` normative boundary

For the first Datatracker submission (`draft-infantado-agent-memory-architecture-00`), the normative core is intended to contain only the following concepts:

- Compute Plane versus Persistent State Plane separation.
- Memory Scope with enforcement of isolation on read, write, query, export, and import.
- Stable object identity (`object_id`).
- Immutable version identity and monotonic ordering (`version_id`, `version_sequence`).
- Canonical Content (arbitrary typed payload).
- Minimal provenance (a small required block; details left to the profile document, but the base requirement lives in `-00`).
- Extensible object typing (mechanism for standard and extension types; NOT a normative cognitive taxonomy).
- Conditional Embedding Space identity (required only when an implementation carries embeddings).
- Basic operation semantics for `create`, `read`, `update`, `history`, `delete`.
- Expected-version conflict semantics (`version_conflict`).
- Idempotent `create` semantics.
- Error envelope.
- Definition of the `PAMSPEC-Lite` conformance profile.
- Architectural description of the Event Ledger; full behavioral requirements deferred to `PAMSPEC-Ledger` profile.

Everything else described in §3 is architectural background,
optional profile material, experimental/companion work, or
out-of-scope.

### 3. Classification of every current concept

Classifications follow the four-part rule. "Move to" columns are
target destinations; they are not executed by this ADR.

#### 3.1 Core (belongs in first `-00` normative section)

| Concept | Rationale under the four-part rule |
|---|---|
| Compute Plane / Persistent State Plane separation | (1)(2)(3)(4) all hold. Two impls that conflate transient context with authoritative state exchange incoherent memory. |
| Memory Scope + isolation enforcement | Engineering (security) requirement per R2. Concrete failure: cross-tenant/user leakage. |
| `object_id` (stable object identity) | (1)(2)(3)(4). Two impls that reuse identifiers for unrelated memory silently corrupt round-trips. |
| `version_id` + `version_sequence` (distinct identity + monotonic order) | (1)(2)(3)(4). AIMEM does not carry either; without them replay is ambiguous. |
| Canonical Content (arbitrary typed payload) | (1)(2)(4). Content interoperability is the point of the format. |
| Minimal provenance block | (1)(3)(4). PAMSPEC design requirement per R2 (defensible, not "proven mandatory"). |
| Extensible object typing (mechanism) | (1)(2)(4). Without an extension mechanism, every new object type forces a spec revision. |
| Conditional Embedding Space identity | (1)(3)(4). Concrete failure: silent re-embedding under a different model on import; AIMEM already prohibits this. |
| `create`, `read`, `update`, `history`, `delete` operation semantics | (1)(4). Base operation set. |
| Expected-version conflict + `version_conflict` | (1)(3)(4). Documented incompatibility with AIMEM's consumer-discretion model (R2 Appendix A). |
| Idempotent `create` | (1)(3)(4). Prevents duplicate persistence on retries — well-established distributed-systems concern. |
| Error envelope | (1)(2)(4). Without a shared error taxonomy, cross-impl failure modes are un-interoperable. |
| `PAMSPEC-Lite` profile definition | (1)(2)(4). Minimum on-ramp profile. |
| Event Ledger architectural description (not full behavioral requirements) | (4). Architectural concept belongs in `-00`; full ledger semantics are `PAMSPEC-Ledger`. |

#### 3.2 Core architecture, optional conformance (Event Ledger)

The Event Ledger is one of PAMSPEC's genuinely distinctive ideas
and belongs in the architecture. Full atomic ledger behavior would
force every Lite implementation into complete event sourcing, which
is not required for basic exchange interoperability.

| Concept | Destination |
|---|---|
| Event Ledger — architectural concept and event vocabulary | Core (in `-00`) |
| Event Ledger — full atomic version+event commit behavior, event ordering guarantees, replay semantics | Optional profile: `PAMSPEC-Ledger` |

#### 3.3 Optional profiles (defined in the repository under `profiles/` when the reclassification runs)

Each satisfies rule (4) — persistent memory state — but rule (2) is
also satisfied: the capability can be adequately expressed as an
optional profile without going into core.

| Concept | Target profile | Rationale |
|---|---|---|
| Full lifecycle / availability / retention / validation governance | Governance Profile | Enterprise governance dimension; R2 verdict: "plausible but unproven" as universal; keep out of Lite. |
| Relationship Objects (independently identified, versioned) | Relationship Profile | Not needed for basic exchange; adds significant surface. |
| Structured query beyond basic filters | Query Profile | Filter mechanics are useful but not universal. |
| Semantic query (embedding-based) | Query Profile (or its own) | Requires Embedding Space; not universal. |
| Snapshots | Query Profile | Advanced retrieval feature. |
| Working Memory (`working_memory` type + Promote) | Working-Memory Profile | R2 verdict: "outside academic evidence" for portability; belongs as optional. |
| Evaluation Snapshot sub-profile | Evaluation Profile | Testing infrastructure — not exchange semantics. |

#### 3.4 Experimental / companion (repository subtree; not in first `-00`)

Each fails at least one of rules (1)-(4) as an interoperability
requirement, but retains value as experimental exploration.

| Concept | Destination | Failing rule and reason |
|---|---|---|
| Delegation Object | `experimental/delegation/` | (4) fails: identity/authorization, not memory. R2 verdict: "contradicted (partly)". Active agent-identity draft landscape covers this. |
| Subscribe operation | `experimental/subscribe/` | (4) fails: runtime coordination / event streaming, not memory. R2 verdict: "plausible but unproven" as memory concern. |
| Tool invocation / tool result archives | `experimental/tool-trace/` | (4) fails: MCP already models tool calls in-band; PAMSPEC records are archives of MCP interactions, best treated as observation records if kept at all. |
| Actor `attestation` block | `experimental/actor-attestation/` (or coordination with AIP) | (4) fails: identity concern; multiple active agent-identity I-Ds cover it. |
| MCP binding profile | `experimental/mcp-binding/` (rename from `bindings/mcp/`) | Binding is optional and belongs outside the normative core; profile is exploratory pending stable MCP spec. |
| `quality_signals` block | `experimental/quality-signals/` | (1)(3) fail: no named consumer for these signals in the exchange contract. |

#### 3.5 Remove from PAMSPEC scope entirely

| Concept | Reason |
|---|---|
| `resource_usage` on Event Ledger (tokens, cost, latency, model_ref, provider_ref, region_ref) | (4) fails: billing/observability telemetry, not persistent memory state. Every provider produces this in its own format; PAMSPEC does not solve a memory interop failure by standardizing it. |
| Token cost accounting | (4) fails: billing, not memory. |
| Billing and provider telemetry generally | (4) fails: observability, not memory. |

### 4. Planned file-move and impact matrix (planning only — NOT executed here)

For each destination in §3, the following is the planned file
movement AND the identified impact. **No files are moved by this
ADR.** Execution happens under separate branches (R4 and later),
each of which will:

- update the destination path,
- update every cross-reference (README, CHANGELOG, CONSISTENCY-MATRIX, ADR indexes, spec source, conformance harness routing, and any code imports),
- run the schema, repository, test-vector, reference-impl, MCP adapter, and conformance test suites, and
- state a rollback plan.

| Source path (current) | Planned destination | Impact scope |
|---|---|---|
| `schemas/0.1-draft/delegation.schema.json` | `experimental/delegation/schema.json` | validator schema-list; test-vector routing in `scripts/validate_test_vectors.py`; ADR-0024 cross-refs; delegation test vectors; reference-impl `pamspec_ref/delegation.py` (moved with schema OR remains as experimental); conformance harness `PAMSPEC-Delegation` profile (renamed or moved); spec `draft-*.md` delegation section; CI workflow references. |
| `schemas/0.1-draft/subscription.schema.json` | `experimental/subscribe/schema.json` | validator schema-list; ADR-0023 cross-refs; subscription-related event types in `memory-event.schema.json` (need re-scoping decision); reference-impl `pamspec_ref/subscription.py`; conformance harness `PAMSPEC-Subscribe` profile; spec `draft-*.md` Subscribe operation section. |
| `schemas/0.1-draft/evaluation-snapshot.schema.json` | `experimental/evaluation/schema.json` (interim); may promote to `profiles/evaluation/` if profile decision confirms | validator schema-list; ADR-0027; evaluation test vectors; spec `draft-*.md` Evaluation profile section. |
| `schemas/0.1-draft/tool-invocation-content.schema.json`, `tool-result-content.schema.json` | `experimental/tool-trace/` | validator schema-list; ADR-0020; tool-invocation and tool-result test vectors; standard-object-type enum in `common.schema.json` (needs coordination with core-type freeze). |
| `actor.schema.json` `attestation` sub-block | `experimental/actor-attestation/` (split out of `actor.schema.json`) | ADR-0026; test vector `attested-agent-actor.json`; conformance suite has no direct coverage; may coordinate with AIP. |
| `common.schema.json` `quality_signals` definition | `experimental/quality-signals/` (split out of `common.schema.json`) | ADR-0025; test vector `claim-with-quality-signals.json`; spec `draft-*.md` quality_signals paragraph. |
| `bindings/mcp/` (directory) | `experimental/mcp-binding/` (rename) | ADR-0019; `bindings/mcp/server-python/` adapter tests; CI workflow if it references the path; spec `draft-*.md` MCP binding paragraph. |
| `memory-event.schema.json` `resource_usage` block | **Removed** (not moved) | ADR-0022; test vector `event-with-resource-usage.json`; spec `draft-*.md` `resource_usage` paragraph. |
| Lifecycle/Availability/Retention/Validation full state machinery | `profiles/governance/` (retain slimmed subset in Lite core; details moved) | ADR-0004, ADR-0013; state-transition tables in spec; conformance suite lifecycle cases; test vectors for expiration, redaction, pending-deletion, retention-transition, validation-transition, lifecycle-transition, deletion-tombstone, invalid-lifecycle-transition, invalid-validation-transition, invalid-cross-dimensional-transition. |
| Relationship Objects (schema + spec section) | `profiles/relationship/` | ADR-0005; `relationship.schema.json`; test vectors `relationship-creation.json`, `cross-scope-relationship-without-policy.json`; conformance harness (no direct cases yet). |
| Structured / semantic query, snapshots | `profiles/query/` | Query schema (if any), spec Query and Retrieval Model section, semantic-query and structured-query test vectors. |
| Working Memory type + Promote operation | `profiles/working-memory/` | `working-memory-content.schema.json`; ADR-0021; spec Type System + Promote operation paragraphs; `working-memory.json` test vector; `working-memory-missing-task-ref.json` invalid vector. |

### 5. Non-goals of this ADR

- Does NOT move any file.
- Does NOT edit any schema.
- Does NOT rename any conformance profile.
- Does NOT delete or alter any test.
- Does NOT change conformance behavior.
- Does NOT rewrite the draft.
- Does NOT add features.

Everything above is a proposal for the reviewer to accept, modify,
or reject before any narrowing branches are authorized.

## Alternatives considered

- **Do not narrow.** Rejected: R2 documents overlap with adjacent standards, and the current source has grown well beyond what the four-part rule permits in core. Doing nothing preserves the drift.
- **Narrow more aggressively (remove Working Memory, remove all extensions).** Rejected: R2 supports Working Memory as an optional-profile concept; removing extensibility entirely would prevent legitimate future object types.
- **Narrow less aggressively (keep Delegation and Subscribe in core).** Rejected: both fail rule (4) and the active adjacent drafts (agent-identity landscape, MCP-side streaming) make PAMSPEC's inclusion a duplication of work happening elsewhere.
- **Rewrite the draft first, then classify.** Rejected: classifying before rewriting is safer — reviewers can push back on classification without a rewrite being in flight.

## Consequences

- Establishes a stable rule (§1) that governs every future feature-addition proposal.
- Establishes a stable target scope (§2, §3) for the first `-00`.
- Creates zero repository churn; downstream branches will do that under explicit authorization.
- Forces every future ADR to answer the four-part test.

## Interoperability impact

The four-part test explicitly gates interoperability-relevant additions. Narrowing to the §2 boundary makes the eventual `-00` reviewable without dragging in adjacent identity/authorization/observability concerns that other IETF/W3C work already addresses.

## Security impact

Scope isolation is retained in core as an engineering (security) requirement (R2 §3.2). Removing `resource_usage`, Delegation, and Subscribe from core reduces PAMSPEC's role in domains where security guarantees are actually the identity/authz/streaming layer's job.

## Privacy impact

Retention and legal-hold governance move to an optional Governance Profile. Any implementation that needs those guarantees adopts that profile; Lite implementations are not silently exposed to a governance regime they cannot implement.

## Unresolved questions

1. Should some of the `experimental/*` subtrees become deprecated instead of moved, given adjacent standards work is already better positioned to own them (e.g., delegation → AIP; MCP binding → post-2026-07-28 MCP spec; tool trace → MCP)?
2. Should Working Memory remain as a standard object type in the core (with the type mechanism) or move entirely to `profiles/working-memory/`? Current classification puts it in the profile; the extensible type mechanism in core is what would let it live there.
3. Are there any core concepts in §3.1 that DO NOT satisfy the four-part rule and should be re-examined? Reviewers should challenge specific rows.
4. Timing: R4 executes §3 file moves and R8 rewrites the draft. Do we execute R4 in one branch or split by destination (`experimental/`, `profiles/`, and remove `resource_usage`)?

## References

- R2 crosswalk: [`../reviews/standards-and-research-crosswalk.md`](../reviews/standards-and-research-crosswalk.md)
- ADR-0030 (AIMEM disposition, this branch)
- `draft-infantado-agent-memory-architecture.md`
