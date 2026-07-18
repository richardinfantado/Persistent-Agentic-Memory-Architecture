# PAMSPEC Semantic Consistency Matrix

Each normative concept is anchored to its defining spec section, its schema representation, at least one positive and one negative test vector, its conformance profile, its security and privacy implication, and the mapping expected of a Conforming Implementation. The matrix is the primary review artifact for cross-file consistency.

## Core (from -00)

| Normative concept | Defining section | Schema representation | Positive test | Negative test | Conformance profile | Security/privacy implication | Implementation mapping |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Memory Scope | Sections 3, 7, 10 | `scope_id` | `claim-creation.json` | `missing-scope.json` | PAMSPEC-Core, PAMSPEC-Lite | Prevents cross-scope disclosure | Workspace / tenant mapping |
| Stable object identity | Sections 8, 12 | `object_id` | `object-history.json` | `reused-immutable-version-identifier.json` | PAMSPEC-Core, PAMSPEC-Lite | Correlation risk | Persistent record identifier |
| Immutable versioning | Sections 8, 10, 12 | `version_id`, event `version_id` | `decision-update.json` | `silent-overwrite-attempt.json`, `stale-expected-version.json` | PAMSPEC-Versioning | Tamper evidence and rollback | Version-chain support required |
| Lifecycle State | Sections 3, 9 | lifecycle enum | `lifecycle-transition.json` | `invalid-lifecycle-transition.json` | PAMSPEC-Core, PAMSPEC-Lite | Promotion authorization | Separate status dimension |
| Availability State | Sections 3, 9 | availability enum | `partial-redaction.json`, `deletion-tombstone.json` | `invalid-cross-dimensional-transition.json` | PAMSPEC-Core | Redaction and deletion disclosure | Separate access state |
| Retention State | Sections 3, 9 | retention enum | `expiration.json`, `pending-deletion.json`, `retention-transition.json` | `deletion-blocked-by-legal-hold.json` | PAMSPEC-Core | Legal hold and erasure | Separate retention policy |
| Validation State | Sections 3, 9 | validation enum | `validation-transition.json` | `invalid-validation-transition.json` | PAMSPEC-Core | Prevents silent trust promotion | Separate confidence state |
| Relationship Object | Sections 3, 8, 10, 11 | `relationship.schema.json` | `relationship-creation.json` | `cross-scope-relationship-without-policy.json` | PAMSPEC-Relationship | Traversal authorization | Graph relation mapping |
| Provenance | Sections 3, 8, 15, 16 | `provenance.schema.json` | object examples | `missing-provenance.json` | PAMSPEC-Core | Source confidentiality and forgery | Provenance export required |
| Embedding Space | Sections 7, 11 | `embedding-space.schema.json`, query field | `semantic-query-with-embedding-space.json` | `comparison-across-incompatible-spaces.json`, `vector-without-embedding-space.json` | PAMSPEC-Semantic-Query | Derived Index leakage | Index descriptor required |
| Event-only operations | Sections 7, 8, 12 | event type without version | `derived-index-event-only.json`, `access-denial-event-only.json` | schema conditional checks | PAMSPEC-Ledger | Audit without false versions | Operational event mapping |
| Structured query | Section 11 | query filters | `structured-query.json` | invalid state/filter vectors | PAMSPEC-Structured-Query | Scope-safe filtering | Query adapter mapping |
| Canonical Content extensions | Section 8 | unrestricted JSON plus extension type | `scalar-canonical-content.json` | unsupported-type error | PAMSPEC-Core | Unknown content remains untrusted | Preserve on export/import |
| Idempotency | Section 12 | `idempotency_key` on create/update | `idempotent-repeated-create.json` | `duplicate-operation-different-content.json` | PAMSPEC-Core, PAMSPEC-Lite | Prevents replay-driven duplication | Key + request-digest table; record MUST survive process restart (restart durability MUST, R9) |
| Deterministic envelope content (CR-7) | Section 11 (Query and Retrieval Model) | all envelope fields in query result | `case_bundle_output_is_deterministic` (PAMSPEC-Lite) | per-call timestamp or nonce in query result | PAMSPEC-Lite (provisional) | Prevents non-reproducible audit trails | Implementations MUST NOT introduce per-call varying fields into returned envelopes |

## -01 Enhancement Cycle (P1–P10) and Consolidation Cycle (C1–C10)

| Normative concept | Defining section | Schema representation | Positive test | Negative test | Conformance profile | Security/privacy implication | Implementation mapping |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PAMSPEC-Lite conformance profile | Section 18 (Interoperability and Conformance) | subset of memory-object.schema.json | `implementations/reference-python/tests` | reference-impl rejection cases | PAMSPEC-Lite | Documents non-support of redaction/legal-hold | Reference impl demonstrates |
| MCP binding | Section 14 (Protocol Bindings) | `bindings/mcp/tools.json` | binding manifest example | binding servers rejecting unmapped operations | PAMSPEC-Protocol-Binding | Preserves scope enforcement across transport | `pamspec.<operation>` tool naming |
| `tool_invocation` type | Section 8 (Type System) | `tool-invocation-content.schema.json` | `tool-invocation.json` | `tool-invocation-invalid-outcome.json` (C2) | PAMSPEC-Core | Tool inputs may carry PII | Persist tool call as versioned memory |
| `tool_result` type | Section 8 (Type System) | `tool-result-content.schema.json` | `tool-result.json` | `tool-result-without-invocation.json` (C2) | PAMSPEC-Core | Tool outputs may carry PII | Redactable independently from consumers |
| `working_memory` type | Section 8 (Type System) | `working-memory-content.schema.json` | `working-memory.json` | `working-memory-missing-task-ref.json` (C2) | PAMSPEC-Core | Untrusted-until-promoted default | Scratchpad-tier storage |
| Promote operation | Section 10 (Operation Semantics) | via memory-object create + relationship + transition | `working-memory.json` (source) | `promote-of-non-working-memory.json` (C2) | PAMSPEC-Core | Consolidation review gate | Atomic create-target + transition-source |
| Subscribe operation | Section 10 (Operation Semantics) | `subscription.schema.json` | subscription descriptor test | `subscription-negative-start-sequence.json` (C2) | PAMSPEC-Subscribe | Per-event authorization re-eval | At-least-once delivery, event_id dedup |
| Delegation Object | Section 15 (Security Considerations) | `delegation.schema.json` | `delegation.json` | `delegation-window-inverted.json`, `delegation-unknown-operation.json` (C2) | PAMSPEC-Core, PAMSPEC-Delegation | Bounds confused-deputy blast radius | Bounded time/ops/objects; `policy_basis` mandatory |
| `quality_signals` block | Section 8 (Envelope) | `common.schema.json` `quality_signals` | `claim-with-quality-signals.json` | `quality-signals-out-of-range.json` (C2) | PAMSPEC-Core | Ranking bias if manipulated | Non-authoritative; never overrides `validation_state` |
| Actor `attestation` block | Section 8 (Envelope, actor field) | `actor.schema.json` `attestation` | `attested-agent-actor.json` | `attestation-window-inverted.json` (C2) | PAMSPEC-Core | Spoofing resistance when present | Signature / authority validation out of schema scope |
| Actor `delegation_id` | Section 8 (Envelope, actor field) | `actor.schema.json` `delegation_id` | `attested-agent-actor.json` | referenced by delegation invalid vectors | PAMSPEC-Core | Chains operation to authorizing grant | MUST reference an existing Delegation Object |
| Evaluation Snapshot | Section 18 (Interoperability and Conformance) | `evaluation-snapshot.schema.json` | `evaluation-snapshot.json` | `evaluation-snapshot-unsealed.json` (C2) | PAMSPEC-Evaluation | Read-only within evaluation scope | Deterministic clock / RNG plumbing |
| `pamspec_operation` enum | `common.schema.json` | `common.schema.json` `pamspec_operation` | referenced by delegation valid vector | `delegation-unknown-operation.json` (C2) | PAMSPEC-Core | — | Single source of truth for operation names |
| `source_confidence` vs `assessed_confidence` | Sections 8 (Provenance, quality_signals) | `provenance.schema.json`, `common.schema.json` | any object with either field | — | PAMSPEC-Core | Different meanings must not conflate | Source's self-report vs system assessment |

Every requirement in this matrix has at least one testable outcome. Requirements that depend on policy authorization (Delegation exercise, cross-scope traversal, snapshot sealing) are tested through expected semantic failures (invalid vectors marked with `expected_failure`) rather than schema validation alone.

Test vectors marked `(C2)` are added in the C2 consolidation branch and land alongside this matrix update. Each such vector is present in `test-vectors/{valid,invalid}/` when C2 lands.
