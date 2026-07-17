# Changelog

> **Terminology note.** Entries below sometimes refer to `-00` and `-01` "cycles" or "candidates" — these are INTERNAL milestone labels only. No revision of this document has been submitted to or posted by the IETF Datatracker. The next possible Datatracker revision remains `-00`. See [`REVIEW-CANDIDATE-ARCHIVE.md`](REVIEW-CANDIDATE-ARCHIVE.md).

## R1 — Repository truth correction (2026-07-18)

- Renamed `CORRECTION-BASELINE.md` to [`REVIEW-CANDIDATE-ARCHIVE.md`](REVIEW-CANDIDATE-ARCHIVE.md); removed all language implying an IETF submission had occurred.
- Moved formerly root-level `draft-infantado-agent-memory-architecture-{00,01}.{xml,txt,html}` into `review-candidates/2026-07-18/candidate-{a,b}/rendering.{xml,txt,html}` with per-candidate `MANIFEST.md` preserving source commit, generator, and SHA-256 checksums.
- Rewrote `pamspec-version.json`: removed `frozen_internet_draft_revision` and `enhancement_cycle`; added `ietf_submission_status: not_submitted`, `next_datatracker_revision: 00`, `posted_datatracker_revisions: []`, and `latest_internal_review_candidate` pointing at the archived candidate B.
- Rewrote `review-candidate-manifest.json` to remove `frozen_revision` and add the same submission-status keys.
- Updated `README.md` to state submission status explicitly and remove the "-01 enhancement cycle in progress" and "frozen -00 baseline" wording.

## Internal enhancement cycle C11 — Portable conformance harness (2026-07-17)

Response to external review pointing out that the -01 test-vector
coverage validated documents against schemas but did not give
third-party implementations a portable way to prove behavior.

- `conformance/harness/adapter.py`: abstract `Adapter` interface
  covering PAMSPEC-Lite (7 methods) + Delegation (3 methods) +
  Subscribe (3 methods), plus `PamspecErrorLike` and `expect_error`
  helper for behavioral assertions.
- `conformance/harness/runner.py`: discovers `case_*` functions in
  a profile's suite module, executes them against a fresh Adapter
  produced by a factory, returns a `ConformanceReport`.
- `conformance/suite/`: 25 portable behavioral cases across three
  profiles that MUST NOT touch implementation internals.
- `conformance/adapters/reference_python.py`: reference adapter
  translating `pamspec_ref.PamspecError` into `PamspecErrorLike`
  and dispatching to `MemoryService`.
- `conformance/tests/test_conformance_reference.py`: pytest wiring
  that proves the harness works end-to-end (all 25 cases pass).
- CI: extended `.github/workflows/build-internet-draft.yml` to run
  the conformance suite on every push.
- `reviews/implementation-report-reference-python.md`: worked
  implementation report using the harness output.
- ADR-0028 documents the design and the review it responds to.

Adopting implementations now have a two-step path to a checkable
conformance claim: write an adapter, run the suite. No PAMSPEC
internals need to be understood.

## Internal consolidation cycle (C1-C10)

Ten consolidation branches targeting IETF-review readiness, each
merged from its own branch:

- **C1** — Extended `CONSISTENCY-MATRIX.md` with 15 rows for -01
  and consolidation concepts (PAMSPEC-Lite profile, MCP binding,
  tool types, working memory, Promote, resource_usage, Subscribe,
  Delegation, quality_signals, attestation, delegation_id,
  Evaluation Snapshot, pamspec_operation enum, source vs assessed
  confidence).
- **C2** — Added 12 invalid test vectors covering delegation,
  subscription, evaluation snapshot, quality signals, tool
  invocation/result, working memory, event resource usage,
  attestation window, promotion source, snapshot mutation.
- **C3** — Expanded `pamspec-version.json` with full schema
  inventory (16 schemas), all 9 conformance profiles, bindings,
  and reference implementation.
- **C4** — CI workflow (`.github/workflows/build-internet-draft.yml`)
  extended to build XML/TXT/HTML on every push, run all test
  suites, and produce numbered internal-review renderings via
  workflow_dispatch. (Superseded by R1: the CORRECTION-BASELINE.md
  file this milestone introduced has been replaced by
  REVIEW-CANDIDATE-ARCHIVE.md, and any language it contained
  about "published `-00` baseline" or "`-01` release procedure"
  was factually wrong and has been corrected.)
- **C5** — MCP binding completed: `pamspec.relate`, `pamspec.redact`,
  `pamspec.promote`, `pamspec.unsubscribe` added to `tools.json`;
  stub Python MCP server (`bindings/mcp/server-python/`) that
  wraps the reference implementation with 6 pytest cases.
- **C6** — Reference implementation gap-fill:
  `pamspec_ref.DelegationStore` (grant/revoke/check with time
  window, granted_operations, granted_object_ids/types, usage
  limit, revocation enforcement) and `pamspec_ref.Subscription`
  /`SubscriptionManager` (cursor-based pull, filter matching,
  per-event authorization, close semantics). 12 new pytest cases.
- **C7** — Deduplicated `confidence`: `provenance.confidence` →
  `source_confidence` (source's own confidence in what they
  reported); `quality_signals.confidence` → `assessed_confidence`
  (system's or reviewer's confidence in the claim).
- **C8** — Extracted `pamspec_operation` enum to
  `common.schema.json` as single source of truth for operation
  names; `delegation.schema.json` and MCP binding now reference it.
- **C9** — Integrated 30+ academic and IETF informative references:
  CoALA, Generative Agents, HippoRAG, LongMemEval, LoCoMo, MAS-LLM
  survey, MetaGPT, Model Cards, Datasheets, PROV-AGENT, Relative
  Representations, Matryoshka, W3C DIDs, AIP I-D, Agent-ID
  Framework I-D, SCITT I-D, AI Agent Protocols framework I-D,
  MCP-over-MoQ, MCP security considerations, RAGAS, RGB, Tulving,
  Baddeley & Hitch, Baddeley (episodic buffer), CLS theory, Squire.
  Extended Comparison with Related Architectures to map PAMSPEC
  object types onto the CoALA taxonomy.
- **C10** — Refreshed all READMEs (top-level, `schemas/`,
  `test-vectors/`, `decisions/`, `examples/`) with -01 surface,
  conformance profile table, quick start, schema inventory,
  invalid vector shapes and semantic rules, -01 ADR index.

Post-consolidation totals: 16 schemas; 27 ADRs; 30+ informative
references; PAMSPEC-Lite Python reference (24 tests) plus MCP
adapter (6 tests). All validators and test suites pass on every
merge to main.

## Internal enhancement cycle (P1-P10)

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

## Internal semantic-consistency review pass (label: -00)

- Separated Lifecycle, Availability, Retention, and Validation State.
- Required a new immutable Memory Version and Event Ledger entry for every Authoritative State change.
- Defined independently versioned Relationship Objects.
- Added versioned public schema IDs and removed instance warning fields.
- Added explicit conformance profiles, temporal semantics, provenance structure, type extensions, and canonical-content shape.
- Archived the internal rendering set produced by this pass under `review-candidates/2026-07-18/candidate-a/` (never submitted to IETF); active development continued under the `latest` docname.
- Added REUSE-compliant licensing metadata, version manifests, and a cross-artifact consistency matrix.
- Corrected Agent Communication Gateway to `draft-agent-gw-01`.

## Internal review-and-publication candidate (label: -00 candidate)

- Updated public project shorthand to PAMSPEC while preserving the Internet-Draft identifier.
- Updated primary author metadata to Richard M. Infantado, Independent.
- Added Robert Leroux to contributor acknowledgements outside formal author front matter.
- Added dual-license documentation for CC BY 4.0 documentation and Apache-2.0 technical artifacts.
- Added reference audit, related-work strengthening, and external review package.

## Internal object-and-operation-model milestone (label: -00 candidate)

- Completed candidate interoperability model for Sections 8 through 14.
- Added architecture decision records for object, lifecycle, operation, retrieval, and error model decisions.
- Updated schemas, examples, and test vectors for the candidate model.

## draft-infantado-agent-memory-architecture-00 - Initial local repository

- Initial individual Internet-Draft repository.
- Defined provider-independent Persistent Agentic Memory Architecture principles.
