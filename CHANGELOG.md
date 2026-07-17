# Changelog

## PAMSPEC -01 Enhancement Cycle (P1-P10)

Ten additive enhancements, each merged from its own feature branch:

- **P1** — Reference implementation (Python, SQLite-backed) and
  PAMSPEC-Lite conformance profile. Two-day on-ramp; 12 pytest
  tests. See `implementations/reference-python/` and ADR-0018.
- **P2** — PAMSPEC-over-MCP binding profile. Normative tool
  naming (`pamspec.<operation>`), resource URIs, error envelope
  preservation, discovery manifest. See `bindings/mcp/` and
  ADR-0019.
- **P3** — `tool_invocation` and `tool_result` standard object
  types with canonical content schemas. See
  `schemas/0.1-draft/tool-invocation-content.schema.json`,
  `tool-result-content.schema.json`, and ADR-0020.
- **P4** — `working_memory` standard object type plus **Promote**
  operation with atomic create-of-target, transition-of-source,
  and derived_from relationship. See
  `working-memory-content.schema.json` and ADR-0021.
- **P5** — Optional `resource_usage` block on Event Ledger entries
  (tokens, cost, latency, model_ref). New event types
  `working_memory_promoted`, `tool_invoked`, `tool_completed`.
  See ADR-0022.
- **P6** — **Subscribe** operation for reactive memory consumption
  (at-least-once, per-event authorization). New event types
  `subscription_opened`, `subscription_closed`. See
  `subscription.schema.json` and ADR-0023.
- **P7** — **Delegation Object** for auditable multi-agent handoff
  (granting_actor, delegated_actor, granted_operations,
  time/usage bounds, policy_basis). New event types
  `delegation_granted`, `delegation_revoked`,
  `delegation_exercised`. See `delegation.schema.json` and
  ADR-0024.
- **P8** — Optional `quality_signals` block on Memory Object
  envelope (confidence, contradiction_score, staleness_score,
  evidence_strength, source_diversity, verification metadata).
  Non-authoritative; MUST NOT override Validation State. See
  ADR-0025.
- **P9** — Optional `attestation` block, `on_behalf_of_actor_id`,
  and `delegation_id` on actor schema. Supports agent manifests,
  signatures, W3C DIDs. See ADR-0026.
- **P10** — **PAMSPEC-Evaluation** sub-profile with sealed
  Evaluation Snapshots (deterministic clock, RNG seed,
  evaluation_run_id propagation, snapshot comparison). See
  `evaluation-snapshot.schema.json` and ADR-0027.

All changes are additive. All schema, test-vector, and repository
validators pass; reference implementation tests (12) pass.

## PAMSPEC -00 Review Feedback Pass (fix/review-feedback-critical)

- Removed the internally inconsistent `relation` type name and clarified that Relationship Objects are represented separately from Memory Object types; removed `relationship` from `standard_object_type` enum in `common.schema.json`.
- Removed misuse of `schema_id` in examples and test vectors where it incorrectly pointed at the envelope schema rather than a content schema.
- Extracted an `integrity` definition into `common.schema.json` and referenced it from both `memory-object.schema.json` and `relationship.schema.json` so tamper-evidence structure is consistent across authoritative objects.
- Added top-level `actor` as a required field on `relationship.schema.json`, aligning with the Relate operation semantics.
- Constrained `id` values in `common.schema.json` to a scheme-prefixed form and documented that a future revision may narrow this to URNs or UUIDs.
- Added a conditional in `relationship.schema.json` requiring `policy_basis` whenever `target_scope_id` is present (cross-scope relationship).
- Added `relationship_type` naming guidance to the Relationships subsection (well-known short label or reverse-domain/URI extension form).
- Clarified that `valid_from`/`valid_until` are informational and do not by themselves change Retention, Lifecycle, or Availability State.
- Specified strict monotonicity of `sequence` within a single object's version history.
- Replaced `canonicalization_profile: "unresolved"` in examples and test vectors with the illustrative value `"none"` so `valid/` vectors no longer contain design-open markers.
- Rewrote ADR-0006 with specific rationale, alternatives, consequences, and cross-references (previously duplicated ADR-0001 boilerplate).

## PAMSPEC -00 Semantic Consistency Pass

- Separated Lifecycle, Availability, Retention, and Validation State.
- Required a new immutable Memory Version and Event Ledger entry for every Authoritative State change.
- Defined independently versioned Relationship Objects.
- Added versioned public schema IDs and removed instance warning fields.
- Added explicit conformance profiles, temporal semantics, provenance structure, type extensions, and canonical-content shape.
- Froze numbered `-00` artifacts and moved active development builds to `latest`.
- Added REUSE-compliant licensing metadata, version manifests, and a cross-artifact consistency matrix.
- Corrected Agent Communication Gateway to `draft-agent-gw-01`.

## draft-infantado-agent-memory-architecture-00 - PAMSPEC -00 External Review and Publication Candidate

- Updated public project shorthand to PAMSPEC while preserving the Internet-Draft identifier.
- Updated primary author metadata to Richard M. Infantado, Independent.
- Added Robert Leroux to contributor acknowledgements outside formal author front matter.
- Added dual-license documentation for CC BY 4.0 documentation and Apache-2.0 technical artifacts.
- Added reference audit, related-work strengthening, and external review package.

## draft-infantado-agent-memory-architecture-00 - PAMSPEC Object and Operation Model -00

- Completed candidate interoperability model for Sections 8 through 14.
- Added architecture decision records for object, lifecycle, operation, retrieval, and error model decisions.
- Updated schemas, examples, and test vectors for the candidate model.

## draft-infantado-agent-memory-architecture-00 - Initial local repository

- Initial individual Internet-Draft repository.
- Defined provider-independent Persistent Agentic Memory Architecture principles.
