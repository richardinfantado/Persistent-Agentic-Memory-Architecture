# PAMSPEC Semantic Consistency Matrix

| Normative concept | Defining section | Schema representation | Positive test | Negative test | Conformance profile | Security/privacy implication | Implementation mapping |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Memory Scope | Sections 3, 7, 10 | `scope_id` | `claim-creation.json` | `missing-scope.json` | PAMSPEC-Core | Prevents cross-scope disclosure | OpenBrain workspace mapping |
| Stable object identity | Sections 8, 12 | `object_id` | `object-history.json` | `reused-immutable-version-identifier.json` | PAMSPEC-Core | Correlation risk | Persistent record identifier |
| Immutable versioning | Sections 8, 10, 12 | `version_id`, event `version_id` | `decision-update.json` | `silent-overwrite-attempt.json`, `stale-expected-version.json` | PAMSPEC-Versioning | Tamper evidence and rollback | Version-chain support required |
| Lifecycle State | Sections 3, 9 | lifecycle enum | `lifecycle-transition.json` | `invalid-lifecycle-transition.json` | PAMSPEC-Core | Promotion authorization | Separate status dimension |
| Availability State | Sections 3, 9 | availability enum | `partial-redaction.json`, `deletion-tombstone.json` | `invalid-cross-dimensional-transition.json` | PAMSPEC-Core | Redaction and deletion disclosure | Separate access state |
| Retention State | Sections 3, 9 | retention enum | `expiration.json`, `pending-deletion.json`, `retention-transition.json` | `deletion-blocked-by-legal-hold.json` | PAMSPEC-Core | Legal hold and erasure | Separate retention policy |
| Validation State | Sections 3, 9 | validation enum | `validation-transition.json` | `invalid-validation-transition.json` | PAMSPEC-Core | Prevents silent trust promotion | Separate confidence state |
| Relationship Object | Sections 3, 8, 10, 11 | `relationship.schema.json` | `relationship-creation.json` | `cross-scope-relationship-without-policy.json` | PAMSPEC-Relationship | Traversal authorization | Graph relation mapping |
| Provenance | Sections 3, 8, 15, 16 | `provenance.schema.json` | object examples | `missing-provenance.json` | PAMSPEC-Core | Source confidentiality and forgery | Provenance export required |
| Embedding Space | Sections 7, 11 | `embedding-space.schema.json`, query field | `semantic-query-with-embedding-space.json` | embedding mismatch vectors | PAMSPEC-Semantic-Query | Derived Index leakage | Index descriptor required |
| Event-only operations | Sections 7, 8, 12 | event type without version | `derived-index-event-only.json`, `access-denial-event-only.json` | schema conditional checks | PAMSPEC-Ledger | Audit without false versions | Operational event mapping |
| Structured query | Section 11 | query filters | `structured-query.json` | invalid state/filter vectors | PAMSPEC-Structured-Query | Scope-safe filtering | Query adapter mapping |
| Canonical Content extensions | Section 8 | unrestricted JSON plus extension type | `scalar-canonical-content.json` | unsupported-type error | PAMSPEC-Core | Unknown content remains untrusted | Preserve on export/import |

No requirement in this matrix is intentionally left without a conformance method. Requirements that depend on policy authorization are tested through expected semantic failures rather than schema validation alone.

