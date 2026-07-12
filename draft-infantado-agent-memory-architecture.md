---
title: "Architecture and Data Model for Persistent Memory in Agentic Systems"
abbrev: "PAMSPEC"
docname: draft-infantado-agent-memory-architecture-00
category: info
ipr: trust200902
area: General
submissiontype: IETF
date: 2026-07-11
keyword:
  - agentic systems
  - persistent memory
  - provenance
  - event ledger
  - derived indexes
  - embedding spaces
author:
  -
    ins: R. M. Infantado
    name: Richard M. Infantado
    role: editor
    org: Independent
    email: richard.infantado@gmail.com
normative:
  RFC2119:
  RFC8174:
informative:
  RFC3986:
  RFC8259:
  RFC6902:
  RFC9110:
  RFC9562:
  JSON-SCHEMA:
    title: "JSON Schema: A Media Type for Describing JSON Documents"
    target: "https://json-schema.org/draft/2020-12/json-schema-core.html"
    author:
      - ins: A. Wright
      - ins: H. Andrews
      - ins: B. Hutton
    date: 2022
  RFC3339:
  RFC8141:
  OPENAI-AGENTS-SESSIONS:
    title: "Sessions - OpenAI Agents SDK"
    target: "https://openai.github.io/openai-agents-python/sessions/"
    author:
      - org: OpenAI
    date: 2025
  OPENAI-CONVERSATION-STATE:
    title: "Conversation state - OpenAI API documentation"
    target: "https://platform.openai.com/docs/guides/conversation-state"
    author:
      - org: OpenAI
    date: 2025
  ANTHROPIC-MULTIAGENT:
    title: "How we built our multi-agent research system"
    target: "https://www.anthropic.com/engineering/built-multi-agent-research-system"
    author:
      - org: Anthropic
    date: 2025
  LANGGRAPH-MEMORY:
    title: "Memory - LangGraph documentation"
    target: "https://langchain-ai.github.io/langgraph/concepts/memory/"
    author:
      - org: LangChain
    date: 2025
  LETTA-MEMORY:
    title: "Memory Blocks - Letta documentation"
    target: "https://docs.letta.com/guides/agents/memory"
    author:
      - org: Letta
    date: 2025
  MEMGPT-PAPER:
    title: "MemGPT: Towards LLMs as Operating Systems"
    target: "https://arxiv.org/abs/2310.08560"
    author:
      - ins: C. Packer
      - ins: V. Fang
      - ins: S. G. Patil
      - ins: K. Lin
      - ins: S. Wooders
      - ins: J. E. Gonzalez
    date: 2023
  MEM0-DOCS:
    title: "Mem0 Documentation"
    target: "https://docs.mem0.ai/"
    author:
      - org: Mem0
    date: 2025
  FOWLER-EVENT-SOURCING:
    title: "Event Sourcing"
    target: "https://martinfowler.com/eaaDev/EventSourcing.html"
    author:
      - ins: M. Fowler
    date: 2005
  AGENT-COMMUNICATION-GATEWAY:
    title: "Agent Communication Gateway"
    target: "https://github.com/richardinfantado/Agent-Communication-Gateway"
    author:
      - ins: R. M. Infantado
    date: 2026
  PROV-DM:
    title: "PROV-DM: The PROV Data Model"
    target: "https://www.w3.org/TR/prov-dm/"
    author:
      - ins: L. Moreau
      - ins: P. Missier
    date: 2013
--- abstract

Memory in current agentic systems is often fragmented across model-provider features, application databases, session histories, framework-specific stores, unstructured files, and retrieval indexes. This document distinguishes temporary context supplied to an inference request from persistent memory that remains addressable, machine-readable, and governed beyond a single request. It specifies a provider-independent architecture and data model for persistent memory in agentic systems based on Memory Scope isolation, typed and versioned Memory Objects, machine-readable provenance, append-only Event Ledger history, lifecycle and validation state, and isolated Derived Indexes and Embedding Spaces. The architecture separates a transient Compute Plane from an authoritative Persistent State Plane and treats embeddings, lexical indexes, graph projections, generated retrieval summaries, ranking caches, and retrieval caches as non-authoritative derived state. The architecture is independent of model provider, storage engine, and protocol transport while allowing future bindings and multiple independent implementations. It does not claim that related systems or standards do not exist; rather, it defines a common architectural vocabulary and interoperability target for persistent agentic memory.

--- middle

# Introduction

Agentic systems increasingly perform work across long-running tasks, multiple tools, multiple applications, and multiple execution environments. These systems often need memory that persists beyond an individual inference request or chat session. In this document, memory is persistent, addressable, machine-readable state retained beyond an individual inference request and made available for future agent operations under explicit scope, lifecycle, provenance, and policy controls.

A model context window is not the authoritative memory record. It is a temporary context projection assembled for a particular operation. The projection may include selected Memory Objects, summaries, retrieved passages, tool results, policy facts, and task state, but the context window is transient and may be truncated, reordered, transformed, or discarded.

PAMSPEC is the project shorthand for the Persistent Agentic Memory Architecture Specification. The architecture defined by the project is the Persistent Agentic Memory Architecture. PAMSPEC is not an IETF standard, working group, or published RFC.

The Persistent Agentic Memory Architecture separates transient computation from authoritative state. The Compute Plane performs model inference, planning, orchestration, transformation, tool execution, and context assembly. The Persistent State Plane stores authoritative Memory Objects, versions, relationships, provenance, lifecycle state, validation state, scope and policy metadata, Event Ledger entries, snapshots, and derived-index descriptors.

## Motivation

Existing agentic memory practices are useful, but they are commonly tied to a provider feature, an application schema, a framework-specific persistence mechanism, a vector store layout, a session transcript, or an unstructured file convention. These approaches can make memory difficult to audit, export, replay, migrate, delete, validate, or compare across implementations.

The motivation for this document is to define a common architecture that preserves implementation freedom while making key memory semantics explicit: scope, identity, versioning, provenance, lifecycle, validation, event history, and derived-index identity.

## Scope

This document defines architectural semantics and a review-oriented data model. It is model-independent, provider-independent, runtime-independent, framework-independent, storage-neutral, transport-neutral, and implementation-neutral.

This architecture does not define agent discovery, semantic message routing, capability negotiation, or agent-to-agent protocol adaptation. Communication systems may reference or retrieve Memory Objects conforming to this specification.

## Document Organization

Sections 2 and 3 define requirements language and terminology. Sections 4 through 7 define the problem statement, goals, non-goals, and architecture. Sections 8 through 14 scaffold the memory object model, lifecycle, operations, query model, consistency, protocol bindings, and error model. Sections 15 and 16 provide architecture-level security and privacy considerations. Sections 17 and 18 scaffold operational and conformance considerations. Section 19 records IANA considerations. Appendices provide schema, state-transition, example, rationale, and related-architecture material for review.

# Requirements Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 {{RFC2119}} {{RFC8174}} when, and only when, they appear in all capitals, as shown here.

Uppercase normative terms are used only for behavior that is testable and required for interoperability, security, or consistent conformance. A Conforming Implementation that violates a capitalized requirement is not conformant to the relevant requirement class described in this document. Lowercase terms are descriptive and do not create conformance requirements.

# Terminology

Agent:
: An automated or semi-automated software participant that uses models, tools, policies, and state to perform tasks or assist a user.

Agent Runtime:
: The execution environment that hosts agent logic, invokes models and tools, assembles context, and coordinates operations. An Agent Runtime may be local, hosted, embedded, distributed, or framework-based.

Compute Plane:
: The transient execution plane that performs model inference, planning, orchestration, transformation, tool execution, and context assembly. The Compute Plane does not itself define the authoritative memory record.

Persistent State Plane:
: The authoritative state plane that stores Memory Objects, object versions, relationships, provenance, lifecycle state, validation state, scope and policy metadata, Event Ledger entries, snapshots, and derived-index descriptors.

Memory Client:
: A component used by an Agent Runtime or application to invoke canonical memory operations. A Memory Client may be a library, protocol adapter, command, or embedded component.

Memory Service:
: The logical service boundary that exposes canonical memory operations. A Memory Service can be implemented in many ways and is not required to be a network server.

Memory Scope:
: The administrative, security, retention, policy, and query boundary within which Memory Objects and operations are evaluated.

Workspace:
: The recommended initial top-level Memory Scope profile for project, tenant, user, organization, or task-family isolation.

Memory Object:
: A persistent, addressable, machine-readable unit of memory with stable identity, typed Canonical Content, authoritative metadata, provenance, relationships, lifecycle state, validation state, and version history.

Memory Version:
: An immutable logical revision of a Memory Object or an equivalent immutable state transition record that makes authoritative state evolution inspectable.

Canonical Content:
: The authoritative typed content of a Memory Object, excluding derived representations such as embeddings, caches, or retrieval summaries.

Authoritative State:
: Canonical Content and authoritative metadata stored in the Persistent State Plane, including scope, identity, version, provenance, lifecycle, validation, relationship, and integrity information.

Context Projection:
: A temporary representation assembled from persistent memory and other sources for a specific inference, planning, tool, or review operation.

Derived Index:
: A non-authoritative and regenerable structure derived from authoritative state, such as an embedding, lexical index, graph projection, generated retrieval summary, ranking cache, or retrieval cache.

Embedding Space:
: A named descriptor for vectors that identifies the embedding provider, model, model revision, vector dimensions, distance metric, normalization, preprocessing profile, and embedding kind needed to interpret comparability.

Event Ledger:
: An append-only logical history of memory operations and state changes. It is broader than per-object revision history and can include indexing, access denial, deletion, redaction, and administrative events.

Provenance:
: Machine-readable information describing the origin, actor, method, evidence, time, confidence, and transformation history associated with a Memory Object, version, relationship, event, or derived representation.

Lifecycle State:
: Authoritative state describing whether a Memory Object is active, deprecated, expired, redacted, deleted, retained under legal hold, or otherwise governed by lifecycle policy.

Validation State:
: Authoritative state describing review, verification, confidence, dispute, rejection, supersession, or acceptance status without claiming that the system is a universal truth engine.

Snapshot:
: A stable, inspectable representation of selected authoritative memory state at a logical time, version boundary, event sequence, or export boundary.

Protocol Binding:
: A mapping from the core semantics in this document to a specific transport, library interface, message-bus format, file format, or protocol environment.

Conforming Implementation:
: An implementation that satisfies the applicable conformance requirements for the selected profile while preserving the architectural separation of authoritative and derived state.

# Problem Statement

Agentic memory is emerging in multiple valuable forms. However, interoperability is limited when memory semantics are implicit, provider-specific, framework-specific, or embedded in retrieval infrastructure. The following problem areas motivate a common architecture.

## Provider-Siloed State

Model-provider memory features can improve user experience, but they can also make memory non-portable when identity, scope, provenance, lifecycle, validation, and export semantics are not exposed in a common form. A user or organization may need to move memory across providers or use multiple providers concurrently without losing auditability.

## Context-Window Dependence

Session history and context-window replay are insufficient as authoritative memory. Context windows are bounded, transient, transformed, and optimized for a current inference request. Treating a context window as durable memory weakens deterministic replay, makes deletion and redaction ambiguous, and obscures the difference between canonical facts and prompt-time representations.

## Framework-Specific Persistence

Agent frameworks often define useful persistence formats, but those formats may be tightly coupled to orchestration, tool schemas, runtime metadata, or application-specific storage. Unstructured file memory and application-specific databases can preserve information, but they commonly lack explicit versioning, provenance, lifecycle, validation, and scope semantics.

## Missing Version and Provenance Semantics

Silent overwrite makes it difficult to determine what changed, who or what changed it, what evidence supported the change, and whether a later operation depended on a prior version. Missing immutable version history and provenance reduce auditability, reproducibility, accountability, and safe rollback.

## Scope Leakage

Agentic systems may operate across users, projects, tenants, clients, tasks, legal contexts, and authorization domains. Cross-scope leakage can occur through unscoped global semantic search, shared embedding indexes, derived caches, backups, exported files, or cross-object relationships. Cross-scope references do not themselves grant access.

## Derived-Index Incompatibility

Embeddings, lexical indexes, graph projections, generated summaries, ranking caches, and retrieval caches are derived from authoritative memory. They are valuable for retrieval, but they are not canonical memory. Vectors from incompatible Embedding Spaces are not directly comparable. Failure to identify embedding spaces can produce non-portable retrieval behavior and weak deterministic evaluation.

# Design Goals

The design goals are: provider independence; runtime independence; framework independence; storage neutrality; transport neutrality; explicit scope isolation; typed memory objects; stable object identity; immutable logical revisions; append-only event history; machine-readable provenance; lifecycle governance; separate validation state; embedding-space identity; deterministic evaluation support; interoperable export and import; auditable operations; extensible type system; multiple independent implementations; and protocol-binding independence.

# Non-Goals

This document does not define or require private chain-of-thought or hidden chain-of-thought storage or disclosure, model reasoning behavior, prompt engineering, agent orchestration, agent discovery, semantic message routing, model selection, vector-database internals, graph-database internals, storage-engine internals, user-interface behavior, a universal truth engine, guaranteed memory extraction quality, a mandatory MCP interface, a mandatory HTTP interface, a mandatory authorization mechanism, a mandatory embedding model, or a mandatory vector database.

# Architecture

## Architectural Overview

The architecture separates transient computation from authoritative persistent state.

~~~
Agent Runtime
|
+-- Compute Plane
|   +-- Model inference
|   +-- Planning
|   +-- Orchestration
|   +-- Tool execution
|   +-- Context assembly
|
+-- Memory Client
|
| Canonical memory operations
v
Memory Service
|
+-- Persistent State Plane
+-- Canonical Memory Objects
+-- Immutable logical versions
+-- Relationships
+-- Provenance
+-- Lifecycle State
+-- Validation State
+-- Scope and policy metadata
+-- Event Ledger
+-- Snapshots
+-- Derived Indexes
+-- Lexical indexes
+-- Embedding Spaces
+-- Graph projections
+-- Retrieval caches
~~~

The Compute Plane performs transient computation. The Memory Client invokes canonical memory operations. The Memory Service exposes those operations. The Persistent State Plane is authoritative. A context window is temporary. A Context Projection is derived from persistent memory. Derived Indexes are non-authoritative. Protocol bindings are separate from core semantics.

## Memory Client

A Memory Client is the logical component used by an Agent Runtime or application to create, read, update, transition, relate, query, inspect, delete, or redact memory. A client can be embedded in-process, invoked through a file interface, mapped to HTTP, mapped to MCP, or implemented over a message bus. The client boundary is semantic, not a requirement for a specific SDK.

## Memory Service

A Memory Service exposes canonical memory operations and enforces scope, lifecycle, validation, versioning, event, provenance, and authorization semantics. It may be implemented as a process, library, local store, hosted service, database-backed component, or protocol adapter. This document does not define a mandatory server.

## Persistent State Plane

The Persistent State Plane stores authoritative Memory Objects, object versions, relationships, provenance, lifecycle state, validation state, scope and policy metadata, Event Ledger entries, snapshots, and derived-index descriptors. It is independent from any specific model provider, context-window implementation, agent framework, storage engine, or protocol transport.

## Scope and Isolation Boundary

A Memory Scope is the administrative boundary, security boundary, retention boundary, policy boundary, and query boundary for memory. Workspace is the recommended initial top-level scope profile.

Every Memory Object MUST resolve to exactly one authoritative Memory Scope. Every operation that reads, writes, queries, transitions, relates, exports, imports, deletes, redacts, or indexes memory MUST be evaluated within a Memory Scope. Unscoped global semantic search MUST NOT be the default behavior of a Conforming Implementation. Cross-scope references MUST NOT grant access by themselves. Cross-scope access MUST require explicit policy and authorization. Derived Indexes MUST preserve scope boundaries. Exports MUST preserve scope identity or explicitly remap it.

This document does not mandate role-based access control. Implementations may use RBAC, ABAC, capability-based access, policy engines, or equivalent authorization models.

## Canonical and Derived State

Canonical state consists of Memory Objects, versions, authoritative metadata, relationships, provenance, lifecycle state, validation state, integrity information, snapshots, and Event Ledger entries. Derived Indexes include embeddings, lexical indexes, graph projections, generated summaries used only for retrieval, ranking caches, and retrieval caches.

Derived Indexes are non-authoritative and regenerable. Rebuilding a Derived Index does not itself create a new canonical version. Deleting an embedding does not delete Canonical Content.

## Event Ledger

The Event Ledger is distinct from object revision history. Object revision history describes the evolution of a Memory Object. The Event Ledger records broader operations and state changes, including object_created, object_updated, lifecycle_transitioned, validation_transitioned, relationship_added, relationship_removed, provenance_attached, embedding_generated, index_rebuilt, access_denied, object_expired, object_redacted, and object_deleted.

State-changing operations MUST produce Event Ledger entries. Ledger events MUST NOT be silently rewritten. Event ordering MUST be preserved within an object history. Implementations may support cryptographic continuity. Append-only history does not require permanent retention of prohibited content. Redaction or erasure may retain a content-free tombstone when policy permits. Derived-index deletion must propagate independently from canonical object deletion rules.

## Derived Indexes

A Memory Object may have no embedding, one embedding, or multiple embeddings in different spaces. Every vector MUST reference an Embedding Space. Vectors from incompatible spaces MUST NOT be treated as directly comparable. Semantic-query results MUST identify the Embedding Space used. Embeddings may be regenerated independently.

An Embedding Space descriptor should be capable of identifying provider, model, model revision, vector dimensions, distance metric, normalization, input preprocessing profile, and embedding kind. This document does not require a vector database.

# Memory Object Model

This section defines a transport-neutral candidate interoperability model for Memory Objects. It is intended to make object identity, version identity, scope, authoritative content, lifecycle, validation, provenance, relationships, and integrity semantics testable while preserving the document's Informational architecture status. The model does not prescribe a storage engine, database schema, wire format, SDK, or protocol transport.

A Conforming Implementation for this candidate profile preserves the semantic distinctions in this section when storing, exporting, importing, validating, or exposing Memory Objects through any binding. Required fields are required for the candidate profile. Optional fields are omitted only when the semantics they represent are not used for that object or profile.

## Canonical Envelope

A canonical envelope represents one immutable logical Memory Version. Derived representations and Event Ledger entries are not embedded Canonical Content, although the envelope can reference them. The candidate profile defines these fields:

`spec_version`:
: Required. Identifies the PAMSPEC object model revision used by the envelope. It is set when a version is created; migration to a different model creates a new version or migration event. It can reveal implementation age or migration status.

`object_id`:
: Required. Provides stable identity for the logical Memory Object across versions. It is immutable after create; reuse for unrelated memory is non-conforming. It can enable correlation across exports.

`version_id`:
: Required. Provides immutable identity for this logical version or equivalent state-transition result. New Canonical Content or authoritative state creates a new identifier. Version history can reveal edit frequency.

`scope_id`:
: Required. Identifies the authoritative Memory Scope for the object. It is immutable for a version; cross-scope movement requires export/import, remapping, or policy-governed transition. It can reveal tenant, workspace, project, or legal context.

`object_type`:
: Required. Declares the typed content family. Initial candidates are `claim`, `decision`, `task`, `artifact`, `observation`, `entity`, `relation`, and `summary`. It is immutable for a version; type conversion creates a new version or new object with provenance. It can reveal sensitive purpose or classification.

`schema_id`:
: Optional. Identifies the schema or profile used to interpret `canonical_content`. It is immutable for a version; schema migration creates a new version or migration event. It can reveal application domain.

`canonical_content`:
: Required. Contains authoritative typed content of the version. Changes create a new logical version. Silent in-place overwrite is non-conforming. It can contain personal, confidential, or regulated information.

`lifecycle_state`:
: Required. Records authoritative retention and use posture. Changes create a new version or immutable lifecycle transition record. It can reveal archival, deletion, or legal posture.

`validation_state`:
: Required. Records authoritative review and confidence posture. Changes create a new version or immutable validation transition record. It can reveal disputes, confidence, or review decisions.

`created_at`:
: Required. Records creation time for the logical object. It is immutable after create and can reveal activity timing.

`updated_at`:
: Required. Records commit time for this version or transition. It is set when the version or transition is committed and can reveal edit timing.

`actor`:
: Required. Identifies the actor responsible for the operation that produced this version. It is immutable for a version and can contain personal data.

`provenance`:
: Required. Records machine-readable origin, source, evidence, method, and transformation information. Corrections or additions create a new version or provenance event. It can contain personal or source-sensitive data.

`relationships`:
: Optional. Contains typed references to related objects or versions. Additions or removals create relationship events and may create a new object version if represented in the envelope. Relationships can reveal sensitive associations.

`integrity`:
: Optional. Contains hashes, signatures, ledger references, or other tamper-evidence metadata. It is bound to the version or event material it covers and can expose correlation or verification metadata.

## Type System

The initial candidate object types are `claim`, `decision`, `task`, `artifact`, `observation`, `entity`, `relation`, and `summary`. Additional object types can be defined by profiles or implementations when they have documented schemas or content profiles and export semantics.

A `summary` object is an externally representable abstraction of conclusions, evidence, assumptions, constraints, progress, and unresolved questions. It is not private chain-of-thought and does not require disclosure of hidden model reasoning.

## Object Identity

`object_id` identifies the logical Memory Object. `version_id` identifies an immutable Memory Version. Implementations must not reuse a `version_id` for different content or state, and must not replace the content associated with an existing `version_id`.

## Versioning

Changes to `canonical_content` create a new logical version. Changes to `lifecycle_state` or `validation_state` create a new logical version or an equivalent immutable transition record visible through Inspect History. A modification using an obsolete expected version fails with `version_conflict` and does not silently overwrite a newer version.

## Relationships

Relationships are typed, scope-evaluated references from one object or version to another object or version. A relationship has a relationship type, source identifier, target identifier, scope context, actor, provenance, and lifecycle status. Cross-scope relationships require explicit policy and authorization. A relationship does not grant access to a target object by itself.

## Provenance

Provenance records where memory came from, who or what created it, what method produced it, what evidence supports it, and how it was transformed. Provenance is authoritative metadata. Implementations should align with existing provenance vocabularies where practical while preserving a compact memory-specific profile.

## Integrity Metadata

Integrity metadata can include content digests, version digests, ledger references, signatures, or chain hashes. This -00 candidate profile does not mandate a cryptographic algorithm. If integrity metadata is present, it identifies what material is covered and what verification method is used.

# Lifecycle and Validation

Lifecycle State and Validation State are separate dimensions. Lifecycle governs retention and use. Validation governs review and confidence. Lifecycle promotion does not imply validation, and validation does not imply retention authorization.

## Lifecycle State

| State | Meaning | Retrieval Default |
| --- | --- | --- |
| `scratch` | Persistent working state not yet suitable for normal retrieval. | Excluded unless explicitly requested. |
| `candidate` | Proposed memory pending review or promotion. | Excluded from default trusted retrieval; included in review workflows. |
| `active` | Current memory eligible for normal retrieval. | Included by default when validation policy permits. |
| `superseded` | Replaced by a newer object or version but retained for history. | Excluded unless history or temporal evaluation requests it. |
| `deprecated` | Discouraged for new use but not necessarily replaced. | Excluded unless policy includes deprecated state. |
| `archived` | Retained for audit, legal, historical, or low-frequency use. | Excluded except audit, export, and history operations. |

Not every Memory Object type is required to support every lifecycle state. Supported states are declared by the implementation or profile.

## Validation State

| State | Meaning | Retrieval Default |
| --- | --- | --- |
| `unverified` | Content has not been corroborated. | Included only when caller accepts unverified content. |
| `corroborated` | Content has supporting evidence or review. | Eligible for default retrieval when lifecycle permits. |
| `disputed` | Content is challenged or has conflicting evidence. | Excluded unless disputes are requested. |
| `rejected` | Content failed validation or is no longer accepted. | Excluded except audit and history. |

## State Transitions

Lifecycle transitions require an actor and policy basis. State-changing transitions produce Event Ledger entries. A transition creates a new logical version or equivalent immutable transition record. Invalid transitions fail with `invalid_state_transition`.

| From | Allowed To | Forbidden Without Policy Override |
| --- | --- | --- |
| `scratch` | `candidate`, `archived` | `active`, `superseded`, `deprecated` |
| `candidate` | `active`, `deprecated`, `archived` | `superseded` without replacement reference |
| `active` | `superseded`, `deprecated`, `archived` | `scratch` |
| `superseded` | `archived`, `deprecated` | `active` without review policy |
| `deprecated` | `archived`, `active` with review policy | `scratch` |
| `archived` | `active` with policy override, `deprecated` | `scratch`, `candidate` |

Validation transitions are independent from lifecycle transitions.

| From | Allowed To | Forbidden Without Policy Override |
| --- | --- | --- |
| `unverified` | `corroborated`, `disputed`, `rejected` | none |
| `corroborated` | `disputed`, `rejected`, `unverified` with provenance correction | none |
| `disputed` | `corroborated`, `rejected` | none |
| `rejected` | `disputed`, `corroborated` with review policy | `unverified` |

Machine-readable candidate transition table:

~~~ json
{
  "lifecycle": {
    "scratch": ["candidate", "archived"],
    "candidate": ["active", "deprecated", "archived"],
    "active": ["superseded", "deprecated", "archived"],
    "superseded": ["archived", "deprecated"],
    "deprecated": ["archived", "active"],
    "archived": ["active", "deprecated"]
  },
  "validation": {
    "unverified": ["corroborated", "disputed", "rejected"],
    "corroborated": ["disputed", "rejected", "unverified"],
    "disputed": ["corroborated", "rejected"],
    "rejected": ["disputed", "corroborated"]
  }
}
~~~

## Expiration, Redaction, and Deletion

Expiration is policy-driven lifecycle evaluation and may transition an object to `archived`, `deprecated`, or a redacted/deleted condition represented by operation result and ledger event. Redaction removes or suppresses protected content while retaining a scope-safe tombstone when policy permits. Deletion removes active availability of the object and may retain a tombstone, subject to retention restrictions and legal hold. Deletion blocked by legal hold fails with `legal_hold`.

# Operation Semantics

All operations are evaluated within a Memory Scope and against authorization policy. Bindings can expose different wire forms, but the semantic inputs, preconditions, results, version effects, Event Ledger effects, Derived Index effects, retry behavior, and error codes in this section are preserved.

## Create

Purpose: create a new Memory Object. Required inputs: operation identifier or idempotency key, scope identifier, object type, Canonical Content, Lifecycle State, Validation State, actor, and provenance. Optional inputs: object identifier, schema identifier, relationships, integrity metadata, expected-absence precondition, and Derived Index request. Create evaluates scope and authorization before commit. A successful Create returns object identity, version identity, scope, committed envelope, and ledger event identity. It produces `object_created` and may produce relationship or indexing events. A repeated Create with the same idempotency key and identical request content returns the original result. The same key with different request content fails with `duplicate_operation`. Retry is safe only with the same idempotency key and identical content. Possible errors include `invalid_request`, `invalid_object`, `unsupported_object_type`, `scope_not_found`, `access_denied`, `policy_denied`, `duplicate_operation`, `service_unavailable`, and `internal_error`.

## Read

Purpose: retrieve authoritative object state. Required inputs: operation identifier, scope identifier, and object identifier. Optional inputs: version identifier, snapshot identifier, requested fields, and history hint. Read evaluates scope and authorization. A successful Read returns the requested authoritative version or a scope-safe redacted/deleted result. Read does not create a new object version. It may create access or denial events if policy requires audit. Possible errors include `object_not_found`, `scope_not_found`, `access_denied`, `object_redacted`, `object_deleted`, `snapshot_not_found`, `service_unavailable`, and `internal_error`.

## Update

Purpose: create a new logical version of Canonical Content or authoritative metadata. Required inputs: operation identifier, scope identifier, object identifier, expected version, actor, provenance, and update content. Optional inputs: schema identifier, relationships, integrity metadata, and idempotency key. Update uses expected-version semantics unless a future profile defines conflict-free merge semantics. A stale expected version fails with `version_conflict`. A successful Update returns the new version and produces `object_updated` plus related events. Derived Indexes become stale until rebuilt. Possible errors include `invalid_request`, `invalid_object`, `version_conflict`, `object_not_found`, `access_denied`, `policy_denied`, `retention_restriction`, `object_deleted`, `service_unavailable`, and `internal_error`.

## Transition

Purpose: change Lifecycle State or Validation State. Required inputs: operation identifier, scope identifier, object identifier, expected version, transition dimension, target state, actor, and policy basis. Optional inputs: reason, evidence, replacement object, expiration time, and legal-hold metadata. A successful Transition returns the new version or transition record and produces `lifecycle_transitioned` or `validation_transitioned`. Derived Index filters may need refresh. Possible errors include `invalid_state_transition`, `version_conflict`, `policy_denied`, `access_denied`, `legal_hold`, `object_not_found`, and `retention_restriction`.

## Relate

Purpose: add or remove typed relationships. Required inputs: operation identifier, scope identifier, source object, target object, relationship type, actor, and provenance. Optional inputs: expected versions, cross-scope policy basis, relationship metadata, and idempotency key. Cross-scope relationships require explicit policy and authorization. A successful Relate returns relationship identity or relationship event identity and produces `relationship_added` or `relationship_removed`. Relationship conflicts fail with `relationship_conflict`.

## Query

Purpose: retrieve sets of Memory Objects or versions using structured, semantic, hybrid, temporal, or snapshot criteria. Required inputs: operation identifier, scope identifier, query expression, pagination parameters, and actor. Optional inputs: Lifecycle State filters, Validation State filters, provenance filters, relationship traversal, Embedding Space, snapshot identifier, ordering profile, and ranking explanation request. Query defaults to scope-bound evaluation and does not default to unscoped global semantic search. Query does not create object versions. It may create audit or denial events.

## Inspect History

Purpose: inspect object versions, transitions, relationships, and Event Ledger entries. Required inputs: operation identifier, scope identifier, object identifier or event range, and actor. Optional inputs: version range, event classes, snapshot boundary, and redaction policy. A successful result returns scope-safe history. Redacted content can appear as tombstone metadata rather than content.

## Redact

Purpose: remove or suppress protected content while preserving permitted audit information. Required inputs: operation identifier, scope identifier, object identifier, expected version, actor, policy basis, and redaction target. Optional inputs: tombstone metadata and Derived Index deletion request. A successful Redact returns redacted state or tombstone and produces `object_redacted`. Derived Index deletion is triggered or recorded independently. Redaction blocked by retention or legal hold returns `retention_restriction` or `legal_hold`.

## Delete

Purpose: remove active availability of an object according to policy. Required inputs: operation identifier, scope identifier, object identifier, expected version, actor, and policy basis. Optional inputs: tombstone mode, purge mode if allowed, and Derived Index deletion request. A successful Delete returns deletion state and produces `object_deleted`. Delete does not imply immediate removal from backups unless policy says so. Deletion blocked by legal hold returns `legal_hold`.

# Query and Retrieval Model

Structured retrieval evaluates deterministic filters over authoritative fields, including Memory Scope, object type, Lifecycle State, Validation State, schema identifier, provenance, actor, creation time, update time, version, relationship, and integrity metadata. When evaluated against the same authoritative snapshot and ordering profile, structured retrieval is repeatable.

Semantic retrieval evaluates approximate similarity through a Derived Index. A semantic result should identify the Embedding Space, index or snapshot identity where available, semantic score, reranking score where applicable, applied filters, and stable tie-break information. Semantic retrieval is approximate unless evaluated against a named stable index snapshot with declared ordering behavior.

Hybrid retrieval combines structured filters with semantic ranking or reranking. Structured filters are evaluated within scope before protected content is disclosed. Relationship traversal evaluates authorization for each target object. Cross-scope traversal requires explicit policy.

Temporal evaluation evaluates state as of a timestamp, logical version boundary, event sequence, or snapshot. Snapshot-based evaluation provides repeatable retrieval within a named snapshot. If no stable index snapshot exists, semantic retrieval is best-effort and identifies that no stable index snapshot was used.

Pagination includes a stable cursor or ordering basis when repeatability is claimed. Stable ordering uses deterministic keys such as snapshot identifier, primary score, secondary score, update time, object identifier, and version identifier. Tie-breaking is documented for any profile that claims repeatable retrieval.

Lifecycle and validation defaults are conservative: `active` plus `corroborated` is the normal trusted retrieval target; `scratch`, `candidate`, `superseded`, `deprecated`, `archived`, `unverified`, `disputed`, and `rejected` require explicit query policy or filters unless a profile declares different defaults.

# Consistency and Concurrency

The candidate profile uses optimistic concurrency. Update, Transition, Redact, Delete, and relationship operations that depend on current state use expected-version semantics. An operation with an obsolete expected version fails with `version_conflict` and returns the current version identifier when policy permits.

Idempotency keys identify duplicate requests. A duplicate request with the same idempotency key and identical request content returns the original successful result or original stable error. A duplicate request with the same idempotency key and different content fails with `duplicate_operation`.

A committed object revision and its required Event Ledger entry are atomic from the perspective of Inspect History. If either cannot be committed, the state-changing operation fails. Implementations can use different physical mechanisms to provide this logical atomicity.

Read-after-write behavior applies to authoritative state: after a successful state-changing operation, a scoped Read by an authorized actor observes the committed authoritative state. Derived Indexes can be eventually consistent. Query responses using derived state expose index identity, freshness, or staleness where available.

Snapshots provide a consistent read boundary over authoritative state and, when declared, over derived-index state. Clock timestamps are metadata and are not the only ordering mechanism when deterministic event order is required. Implementations distinguish observed time, request time, commit time, and logical event order.

# Protocol Bindings

This document does not standardize a mandatory transport. Every future binding preserves object identity, Memory Scope, authorization outcome, version preconditions, idempotency behavior, operation semantics, stable error codes, Event Ledger behavior, query parameters, deletion semantics, and redaction semantics.

An embedded library binding can expose operations as local function calls. An HTTP binding can map operations to resources and methods. An MCP binding can map operations to tools or resources. A gRPC binding can map operations to services and messages. Event bus or message bus bindings can expose ledger streams, asynchronous commands, or index rebuild events. None of these bindings is mandatory.

Bindings do not weaken scope enforcement or convert denied cross-scope access into successful partial disclosure. Bindings preserve explainable denial without exposing protected Memory Object content. Bindings document how idempotency keys, operation identifiers, pagination cursors, and snapshot identifiers are represented.

# Error Model

Errors use a stable transport-neutral envelope. A binding can map the envelope to protocol-specific status codes, but it preserves the semantic fields.

Every error identifies a stable `code`, human-readable `message`, `retryable` status, operation identifier, and scope-safe details. It identifies a policy rule identifier where applicable. Optional fields can include object identifier, current version identifier, expected version identifier, correlation identifier, and remediation hint. Explainable denial does not expose protected Memory Object content or confirm protected object existence when policy forbids that disclosure.

| Code | Meaning | Retryable |
| --- | --- | --- |
| `invalid_request` | Request shape or parameters are invalid. | No, unless corrected. |
| `invalid_object` | Object envelope or content violates the candidate model. | No, unless corrected. |
| `unsupported_object_type` | Object type is not supported by the implementation or profile. | No, unless profile changes. |
| `object_not_found` | Object is absent or not visible in scope. | No. |
| `scope_not_found` | Scope is absent or not visible. | No. |
| `access_denied` | Actor lacks authorization. | No, unless authorization changes. |
| `policy_denied` | Policy blocks the operation. | No, unless policy or request changes. |
| `version_conflict` | Expected version is stale or mismatched. | Yes, after refetch and merge. |
| `duplicate_operation` | Idempotency key was reused with different request content. | No. |
| `invalid_state_transition` | Requested lifecycle or validation transition is not allowed. | No, unless state or policy changes. |
| `relationship_conflict` | Relationship operation conflicts with state or policy. | Maybe, after inspection. |
| `embedding_space_mismatch` | Query or comparison uses incompatible Embedding Spaces. | No, unless corrected. |
| `snapshot_not_found` | Requested snapshot does not exist or is not visible. | No. |
| `retention_restriction` | Retention policy restricts redaction, deletion, or export. | No, unless policy changes. |
| `legal_hold` | Legal hold blocks the operation. | No, until hold changes. |
| `object_redacted` | Object content is redacted for this request. | No. |
| `object_deleted` | Object has been deleted or tombstoned. | No. |
| `service_unavailable` | Service cannot complete the operation now. | Yes. |
| `internal_error` | Unexpected implementation failure. | Maybe. |

# Security Considerations

## Threat Model

PAMSPEC systems store durable machine-readable state that can affect future agent behavior. Threats include unauthorized access, cross-scope data leakage, confused-deputy behavior, memory poisoning, persisted prompt injection, provenance forgery, ledger tampering, replay, excessive privilege, malicious cross-object relationships, backup leakage, and derived-index remnants.

## Scope Enforcement

Every operation is evaluated within a Memory Scope. Implementations MUST enforce scope boundaries for reads, writes, queries, exports, imports, indexing, snapshots, and deletion. Unscoped global semantic search MUST NOT be the default because it can reveal protected information across administrative, security, retention, policy, or query boundaries.

## Authorization

Cross-scope access requires explicit policy and authorization. This document does not mandate RBAC. Implementations may use RBAC, ABAC, capability-based authorization, policy engines, or equivalent models. Authorization decisions should be recorded when they affect state, and denied access may be recorded as access_denied events without exposing protected content.

## Confused-Deputy Risks

A Memory Client or Agent Runtime can become a confused deputy if it uses its own authority to retrieve, transform, or relate memory on behalf of a less-authorized actor. Implementations should bind operations to the requesting actor, delegated authority, scope, purpose, and policy version.

## Injection and Memory Poisoning

Prompt injection and malicious tool output can be persisted as memory if extraction and validation are not controlled. Implementations should preserve provenance, distinguish observed content from validated content, support validation states, and prevent unreviewed content from being silently promoted into trusted memory.

## Integrity and Tamper Evidence

Ledger events MUST NOT be silently rewritten. Implementations should protect ledger ordering, version identity, and provenance. Cryptographic continuity, signatures, or content hashing may be used to make tampering evident, but this -00 draft does not mandate a particular cryptographic mechanism.

## Cross-Scope Relationships

A relationship that points to another Memory Object does not grant access to that object. Malicious or accidental relationships can leak identifiers, infer existence, or induce retrieval across scopes. Implementations should evaluate relationship traversal under the target scope policy.

## Derived-Index Leakage

Embeddings, lexical indexes, graph projections, generated summaries, ranking caches, retrieval caches, and backups can retain sensitive content after canonical deletion or redaction. Implementations MUST preserve scope boundaries in Derived Indexes and should propagate deletion and redaction to derived state according to policy.

# Privacy Considerations

## Data Minimization

Systems should store only memory needed for an explicit purpose and scope. Memory extraction should avoid collecting unnecessary personal data, sensitive inferences, or incidental third-party information.

## Retention

Retention policy is part of the Memory Scope boundary. Implementations should support expiration and retention planning for both authoritative state and Derived Indexes.

## Erasure

Append-only history and privacy obligations can coexist by separating immutable operational history from prohibited retained content. Redaction or erasure may remove content while retaining a content-free tombstone when policy permits. Legal hold may delay erasure, but the hold basis should be explicit.

## Sensitive Inferences

Agentic systems can generate sensitive inferences from non-sensitive inputs. Validation state, provenance, and lifecycle controls should distinguish inferred claims from observed evidence and reviewed conclusions.

## Provenance and Personal Data

Provenance can contain personal data, including actors, sources, timestamps, and evidence. Implementations should minimize provenance fields, restrict access, and support redaction where policy permits.

## Embedding Privacy

Embeddings may reveal information about source content or permit membership inference. Embedding Spaces and Derived Indexes should be scoped, access-controlled, rebuildable, and deletable independently from Canonical Content. Export and portability workflows should identify whether embeddings and derived caches are included.

# Operational Considerations

## Backup and Recovery

Backups should preserve authoritative state, version history, scope identity, and ledger ordering while respecting deletion and redaction policy.

## Migration

Migration should preserve object identity, version identity, Event Ledger semantics, scope identity, and provenance, or explicitly document remapping.

## Index Rebuilding

Index rebuilding regenerates Derived Indexes and does not create canonical versions by itself.

## Clock and Time Handling

Implementations should distinguish observed time, event time, commit time, and logical ordering.

## Observability

Observability should expose operational state without leaking protected memory content.

## Capacity and Retention Planning

Capacity planning should account for authoritative versions, ledger entries, snapshots, derived indexes, and tombstones.

# Interoperability and Conformance

## Core Conformance

Core conformance is expected to require scope-bound operations, stable object identity, typed canonical content, provenance, lifecycle state, validation state, and distinction between authoritative and derived state.

## Versioning Conformance

Versioning conformance is expected to require immutable logical revisions or equivalent immutable transition history.

## Ledger Conformance

Ledger conformance is expected to require append-only logical event history for state-changing operations.

## Query Conformance

Query conformance is expected to define structured, semantic, hybrid, temporal, and snapshot expectations.

## Protocol-Binding Conformance

Protocol-binding conformance is expected to require preservation of core semantics without mandating a specific transport.

## Implementation Reports

Implementation reports should document supported profiles, storage choices, authorization model, index behavior, export behavior, deletion behavior, and known deviations.

# IANA Considerations

This document has no IANA actions.

# References

Normative and informative references are declared in the document metadata. This -00 draft uses RFC 2119 {{RFC2119}} and RFC 8174 {{RFC8174}} normatively for requirements language. It uses URI syntax {{RFC3986}}, URN syntax {{RFC8141}}, Internet timestamps {{RFC3339}}, JSON {{RFC8259}}, JSON Patch {{RFC6902}}, HTTP semantics {{RFC9110}}, UUIDs {{RFC9562}}, JSON Schema {{JSON-SCHEMA}}, and W3C PROV-DM {{PROV-DM}} informatively for architectural alignment and review. Related work and implementation context include OpenAI session and conversation-state documentation {{OPENAI-AGENTS-SESSIONS}} {{OPENAI-CONVERSATION-STATE}}, Anthropic multi-agent engineering material {{ANTHROPIC-MULTIAGENT}}, LangGraph memory documentation {{LANGGRAPH-MEMORY}}, Letta memory documentation {{LETTA-MEMORY}}, MemGPT research {{MEMGPT-PAPER}}, Mem0 documentation {{MEM0-DOCS}}, event-sourcing literature {{FOWLER-EVENT-SOURCING}}, and Agent Communication Gateway material {{AGENT-COMMUNICATION-GATEWAY}}.

--- back

# Canonical JSON Schemas

The `schemas/` directory contains minimal, unstable pre-0.1 JSON Schemas for architecture review. They are not intended to freeze the protocol surface in the -00 draft.

# State Transition Tables

The proposed direction is to define lifecycle and validation transition tables after review of use cases for expiration, redaction, deletion, legal hold, validation, dispute, and supersession. Open issue: determine whether transition tables are normative or profile-specific.

# Example Interactions

The `examples/` directory contains review examples for claim, decision, task, artifact, version chain, lifecycle transition, semantic query, and concurrent update conflict. These examples illustrate intended semantics without freezing all fields.

# Design Rationale

The design separates Compute Plane and Persistent State Plane to prevent temporary context from becoming the hidden source of authority. It separates authoritative state from Derived Indexes to support deletion, portability, deterministic evaluation, and independent indexing implementations.

# Comparison with Related Architectures

PAMSPEC is intended to coexist with provider-hosted session memory, conversation persistence, framework-specific stores, extraction-oriented memory systems, stateful-agent runtimes, graph-native memory systems, event-sourced memory databases, and working memory in agent communication gateways. It does not claim to replace those systems.

Provider-hosted session memory and conversation-state systems, including OpenAI session and conversation-state mechanisms {{OPENAI-AGENTS-SESSIONS}} {{OPENAI-CONVERSATION-STATE}}, can preserve interaction continuity. PAMSPEC focuses on persistent, typed, versioned, scoped, auditable Memory Objects whose authoritative state is independent of any single provider-hosted context mechanism.

Framework-specific stores, including LangGraph memory concepts such as stores, namespaces, and semantic indexing {{LANGGRAPH-MEMORY}}, provide practical persistence inside a runtime ecosystem. PAMSPEC defines transport-neutral object, operation, scope, versioning, provenance, and Derived Index semantics that can be mapped by multiple frameworks.

Stateful-agent memory systems, including Letta and MemGPT concepts around memory blocks and long-running agent state {{LETTA-MEMORY}} {{MEMGPT-PAPER}}, demonstrate the value of persistent agent state. PAMSPEC separates the memory architecture from agent runtime behavior, prompt engineering, hidden reasoning, and model-selection policy.

Extraction-oriented memory systems, including Mem0-style memory add, update, delete, and retrieval workflows {{MEM0-DOCS}}, can be compatible implementation approaches when exported memory preserves PAMSPEC object identity, version identity, scope, provenance, lifecycle, validation, Event Ledger, and Embedding Space semantics.

Graph-native memory systems and event-sourced memory databases can provide natural implementations for relationships, immutable transitions, replay, and snapshots. PAMSPEC borrows architectural vocabulary from provenance and event-sourcing practice {{PROV-DM}} {{FOWLER-EVENT-SOURCING}} without mandating a graph database, event store, or replay engine.

Agent Communication Gateway focuses on agent communication, semantic routing, protocol adaptation, and active shared workflow context {{AGENT-COMMUNICATION-GATEWAY}}. PAMSPEC focuses on persistent, typed, versioned, scoped, auditable Memory Objects and Derived Indexes. The two architectures can be complementary: an agent gateway can carry references to PAMSPEC Memory Objects, while PAMSPEC does not define agent discovery, semantic routing, or protocol adaptation.


# Acknowledgements

This initial draft records architectural requirements and open issues for review. Additional acknowledgements will be added when contributors provide review or text.

Robert Leroux contributed project review and specification feedback and is acknowledged as a contributor. Formal co-authorship or editorship remains pending explicit consent and complete public author metadata.
