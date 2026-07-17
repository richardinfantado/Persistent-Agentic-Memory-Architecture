# Changelog

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
