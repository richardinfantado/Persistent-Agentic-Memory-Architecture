---
title: "Architecture and Data Model for Persistent Memory in Agentic Systems"
abbrev: "PAMSPEC"
docname: draft-infantado-agent-memory-architecture-latest
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
    title: "Agent Communication Gateway for Semantic Routing and Working Memory"
    target: "https://datatracker.ietf.org/doc/draft-agent-gw/"
    author:
      - ins: X. Xie
      - ins: Z. Wang
      - ins: T. Hu
      - ins: Y. Cui
    date: 2026
  PROV-DM:
    title: "PROV-DM: The PROV Data Model"
    target: "https://www.w3.org/TR/prov-dm/"
    author:
      - ins: L. Moreau
      - ins: P. Missier
    date: 2013
  COALA:
    title: "Cognitive Architectures for Language Agents"
    target: "https://arxiv.org/abs/2309.02427"
    author:
      - ins: T. R. Sumers
      - ins: S. Yao
      - ins: K. Narasimhan
      - ins: T. L. Griffiths
    date: 2024
  GENERATIVE-AGENTS:
    title: "Generative Agents: Interactive Simulacra of Human Behavior"
    target: "https://arxiv.org/abs/2304.03442"
    author:
      - ins: J. S. Park
      - ins: J. C. O'Brien
      - ins: C. J. Cai
      - ins: M. R. Morris
      - ins: P. Liang
      - ins: M. S. Bernstein
    date: 2023
  HIPPORAG:
    title: "HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models"
    target: "https://arxiv.org/abs/2405.14831"
    author:
      - ins: B. J. Gutiérrez
      - ins: Y. Shu
      - ins: Y. Gu
      - ins: M. Yasunaga
      - ins: Y. Su
    date: 2024
  AGENT-MEMORY-SURVEY:
    title: "A Survey on the Memory Mechanism of Large Language Model Based Agents"
    target: "https://arxiv.org/abs/2404.13501"
    author:
      - ins: Z. Zhang
      - ins: X. Bo
      - ins: C. Ma
    date: 2024
  LONGMEMEVAL:
    title: "LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory"
    target: "https://arxiv.org/abs/2410.10813"
    author:
      - ins: D. Wu
    date: 2024
  LOCOMO:
    title: "Evaluating Very Long-Term Conversational Memory of LLM Agents"
    target: "https://arxiv.org/abs/2402.17753"
    author:
      - ins: A. Maharana
      - ins: D.-H. Lee
      - ins: S. Tulyakov
      - ins: M. Bansal
      - ins: F. Barbieri
      - ins: Y. Fang
    date: 2024
  MAS-LLM-SURVEY:
    title: "Large Language Model based Multi-Agents: A Survey of Progress and Challenges"
    target: "https://arxiv.org/abs/2402.01680"
    author:
      - ins: T. Guo
      - ins: X. Chen
      - ins: Y. Wang
    date: 2024
  METAGPT:
    title: "MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework"
    target: "https://arxiv.org/abs/2308.00352"
    author:
      - ins: S. Hong
      - ins: M. Zhuge
    date: 2024
  MODEL-CARDS:
    title: "Model Cards for Model Reporting"
    target: "https://dl.acm.org/doi/10.1145/3287560.3287596"
    author:
      - ins: M. Mitchell
      - ins: S. Wu
      - ins: A. Zaldivar
      - ins: P. Barnes
      - ins: L. Vasserman
      - ins: B. Hutchinson
      - ins: E. Spitzer
      - ins: I. D. Raji
      - ins: T. Gebru
    date: 2019
  DATASHEETS:
    title: "Datasheets for Datasets"
    target: "https://arxiv.org/abs/1803.09010"
    author:
      - ins: T. Gebru
      - ins: J. Morgenstern
      - ins: B. Vecchione
      - ins: J. W. Vaughan
      - ins: H. Wallach
      - ins: H. Daumé III
      - ins: K. Crawford
    date: 2021
  PROV-AGENT:
    title: "PROV-AGENT: Unified Provenance for Tracking AI Agent Interactions in Agentic Workflows"
    target: "https://arxiv.org/abs/2508.02866"
    author:
      - ins: R. Souza
      - ins: L. Azevedo
    date: 2025
  RELATIVE-REPRESENTATIONS:
    title: "Relative Representations Enable Zero-Shot Latent Space Communication"
    target: "https://arxiv.org/abs/2209.15430"
    author:
      - ins: L. Moschella
      - ins: V. Maiorca
      - ins: M. Fumero
      - ins: A. Norelli
      - ins: F. Locatello
      - ins: E. Rodolà
    date: 2023
  MATRYOSHKA:
    title: "Matryoshka Representation Learning"
    target: "https://arxiv.org/abs/2205.13147"
    author:
      - ins: A. Kusupati
      - ins: G. Bhatt
    date: 2022
  W3C-DID:
    title: "Decentralized Identifiers (DIDs) v1.0"
    target: "https://www.w3.org/TR/did-core/"
    author:
      - ins: M. Sporny
      - ins: D. Longley
      - ins: M. Sabadello
      - ins: D. Reed
      - ins: O. Steele
      - ins: C. Allen
    date: 2022
  AIP-DRAFT:
    title: "Agent Identity Protocol (AIP): Decentralized Identity and Delegation for AI Agents"
    target: "https://datatracker.ietf.org/doc/draft-singla-agent-identity-protocol/"
    author:
      - ins: A. Singla
    date: 2025
  AGENT-ID-FRAMEWORK:
    title: "Self-Certifying Identity and Capability-Based Delegation for Autonomous AI Agents"
    target: "https://datatracker.ietf.org/doc/draft-duda-agent-id-framework/"
    author:
      - ins: K. Duda
    date: 2025
  SCITT:
    title: "An Architecture for Trustworthy and Transparent Digital Supply Chains"
    target: "https://datatracker.ietf.org/doc/draft-ietf-scitt-architecture/"
    author:
      - ins: H. Birkholz
      - ins: A. Delignat-Lavaud
      - ins: C. Fournet
      - ins: Y. Deshpande
      - ins: S. Lasker
    date: 2025
  AI-PROTOCOLS-FRAMEWORK:
    title: "Framework, Use Cases and Requirements for AI Agent Protocols"
    target: "https://datatracker.ietf.org/doc/draft-rosenberg-ai-protocols/"
    author:
      - ins: J. Rosenberg
    date: 2025
  MCP-OVER-MOQ:
    title: "Model Context Protocol and Agent Skills over Media over QUIC Transport"
    target: "https://datatracker.ietf.org/doc/draft-jennings-ai-mcp-over-moq/"
    author:
      - ins: C. Jennings
    date: 2025
  MCP-SECURITY:
    title: "Security Considerations for Model Context Protocol (MCP) Implementations in AI Agent Systems"
    target: "https://datatracker.ietf.org/doc/draft-mohiuddin-mcp-security-considerations/"
    author:
      - ins: T. Mohiuddin
    date: 2025
  RAGAS:
    title: "RAGAS: Automated Evaluation of Retrieval Augmented Generation"
    target: "https://arxiv.org/abs/2309.15217"
    author:
      - ins: S. Es
      - ins: J. James
      - ins: L. Espinosa-Anke
      - ins: S. Schockaert
    date: 2024
  RGB-BENCHMARK:
    title: "Benchmarking Large Language Models in Retrieval-Augmented Generation"
    target: "https://arxiv.org/abs/2309.01431"
    author:
      - ins: J. Chen
      - ins: H. Lin
      - ins: X. Han
      - ins: L. Sun
    date: 2024
  TULVING-EPISODIC:
    title: "Episodic and Semantic Memory"
    author:
      - ins: E. Tulving
    date: 1972
  BADDELEY-WM:
    title: "Working Memory"
    author:
      - ins: A. D. Baddeley
      - ins: G. Hitch
    date: 1974
  BADDELEY-EPISODIC-BUFFER:
    title: "The Episodic Buffer: A New Component of Working Memory?"
    target: "https://doi.org/10.1016/S1364-6613(00)01538-2"
    author:
      - ins: A. D. Baddeley
    date: 2000
  CLS-THEORY:
    title: "Why There Are Complementary Learning Systems in the Hippocampus and Neocortex"
    target: "https://doi.org/10.1037/0033-295X.102.3.419"
    author:
      - ins: J. L. McClelland
      - ins: B. L. McNaughton
      - ins: R. C. O'Reilly
    date: 1995
  SQUIRE-MEMORY-SYSTEMS:
    title: "Memory Systems of the Brain: A Brief History and Current Perspective"
    target: "https://doi.org/10.1016/j.nlm.2004.06.005"
    author:
      - ins: L. R. Squire
    date: 2004
--- abstract

Memory in current agentic systems is often fragmented across model-provider features, application databases, session histories, framework-specific stores, unstructured files, and retrieval indexes. This document distinguishes temporary context supplied to an inference request from persistent memory that remains addressable, machine-readable, and governed beyond a single request. It specifies a provider-independent architecture and data model for persistent memory in agentic systems based on Memory Scope isolation, typed and versioned Memory Objects, machine-readable provenance, append-only Event Ledger history, separate lifecycle, availability, retention, and validation state, and isolated Derived Indexes and Embedding Spaces. The architecture separates a transient Compute Plane from an authoritative Persistent State Plane and treats embeddings, lexical indexes, graph projections, generated retrieval summaries, ranking caches, and retrieval caches as non-authoritative derived state. The architecture is independent of model provider, storage engine, and protocol transport while allowing future bindings and multiple independent implementations. It does not claim that related systems or standards do not exist; rather, it defines a common architectural vocabulary and interoperability target for persistent agentic memory.

--- middle

# Introduction

Agentic systems increasingly perform work across long-running tasks, multiple tools, multiple applications, and multiple execution environments. These systems often need memory that persists beyond an individual inference request or chat session. In this document, memory is persistent, addressable, machine-readable state retained beyond an individual inference request and made available for future agent operations under explicit scope, lifecycle, provenance, and policy controls.

A model context window is not the authoritative memory record. It is a temporary context projection assembled for a particular operation. The projection may include selected Memory Objects, summaries, retrieved passages, tool results, policy facts, and task state, but the context window is transient and may be truncated, reordered, transformed, or discarded.

PAMSPEC is the project shorthand for the Persistent Agentic Memory Architecture Specification. The architecture defined by the project is the Persistent Agentic Memory Architecture. PAMSPEC is not an IETF standard, working group, or published RFC.

The Persistent Agentic Memory Architecture separates transient computation from authoritative state. The Compute Plane performs model inference, planning, orchestration, transformation, tool execution, and context assembly. The Persistent State Plane stores authoritative Memory Objects, Relationship Objects, versions, provenance, lifecycle, availability, retention, and validation state, scope and policy metadata, Event Ledger entries, snapshots, and Derived Index descriptors.

## Motivation

Existing agentic memory practices are useful, but they are commonly tied to a provider feature, an application schema, a framework-specific persistence mechanism, a vector store layout, a session transcript, or an unstructured file convention. These approaches can make memory difficult to audit, export, replay, migrate, delete, validate, or compare across implementations.

The motivation for this document is to define a common architecture that preserves implementation freedom while making key memory semantics explicit: scope, identity, versioning, provenance, lifecycle, validation, event history, and derived-index identity.

## Scope

This document defines architectural semantics and a review-oriented data model. It is model-independent, provider-independent, runtime-independent, framework-independent, storage-neutral, transport-neutral, and implementation-neutral.

This architecture does not define agent discovery, semantic message routing, capability negotiation, or agent-to-agent protocol adaptation. Communication systems may reference or retrieve Memory Objects conforming to this specification.

## Document Organization

Sections 2 and 3 define requirements language and terminology. Sections 4 through 7 define the problem statement, goals, non-goals, and architecture. Sections 8 through 14 define the candidate object, state, operation, query, consistency, protocol-binding, and error models. Sections 15 and 16 provide security and privacy considerations. Section 17 defines operational considerations. Section 18 defines testable conformance profiles. Section 19 records IANA considerations. Appendices summarize schemas, state transitions, examples, rationale, and related architectures.

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
: A persistent, addressable, machine-readable unit of memory with stable identity, typed Canonical Content, authoritative metadata, provenance, lifecycle, availability, retention, and validation state, and version history.

Memory Version:
: An immutable logical revision of a Memory Object. Every authoritative state change creates a new Memory Version and a corresponding Event Ledger entry.

Canonical Content:
: The authoritative typed content of a Memory Object, excluding derived representations such as embeddings, caches, or retrieval summaries.

Authoritative State:
: Canonical Content and authoritative metadata stored in the Persistent State Plane, including scope, identity, version, provenance, lifecycle, availability, retention, validation, relationship references, temporal fields, and integrity information.

Context Projection:
: A temporary representation assembled from persistent memory and other sources for a specific inference, planning, tool, or review operation.

Derived Index:
: A non-authoritative and regenerable structure derived from authoritative state, such as an embedding, lexical index, graph projection, generated retrieval summary, ranking cache, or retrieval cache.

Embedding Space:
: A named descriptor for vectors that identifies the embedding provider, model, model revision, vector dimensions, distance metric, normalization, preprocessing profile, and embedding kind needed to interpret comparability.

Event Ledger:
: An append-only logical history of memory operations and state changes. It is broader than per-object revision history and can include indexing, access denial, deletion, redaction, and administrative events.

Provenance:
: Machine-readable information describing an entity or source reference, actor or agent, generation activity, evidence, observation and recording time, confidence assertion, transformation parent, and optional integrity reference.

Lifecycle State:
: Authoritative maturity and operational-use state: `scratch`, `candidate`, `active`, `superseded`, `deprecated`, or `archived`.

Availability State:
: Authoritative state describing whether Canonical Content is `available`, `partially_redacted`, `redacted`, or `deleted`.

Retention State:
: Authoritative policy state describing whether an object is `retained`, `expired`, `pending_deletion`, or subject to `legal_hold`.

Validation State:
: Authoritative review state: `unverified`, `corroborated`, `disputed`, or `rejected`. `corroborated` means that supporting evidence or an authorized validation process exists; it does not guarantee objective truth.

Relationship Object:
: An independently identified, typed, versioned, scope-bound authoritative object that links a source Memory Object to a target Memory Object. Relationship projections embedded in query results are non-authoritative.

Tombstone:
: A terminal Memory Version that retains only policy-permitted metadata after redaction or deletion.

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

The Event Ledger is distinct from object revision history. Object revision history describes the evolution of a Memory Object. The Event Ledger records broader operations and state changes, including `object_created`, `object_updated`, `lifecycle_transitioned`, `availability_transitioned`, `retention_transitioned`, `validation_transitioned`, `relationship_created`, `relationship_updated`, `provenance_updated`, `embedding_generated`, `index_rebuilt`, `access_denied`, `object_redacted`, and `object_deleted`.

State-changing operations MUST produce Event Ledger entries. Ledger events MUST NOT be silently rewritten. Event ordering MUST be preserved within an object history. Implementations may support cryptographic continuity. Append-only history does not require permanent retention of prohibited content. Redaction or erasure may retain a content-free tombstone when policy permits. Derived-index deletion must propagate independently from canonical object deletion rules.

Event Ledger entries MAY carry an optional `resource_usage` block recording cost, latency, and model attribution for the operation that produced the event (`input_tokens`, `output_tokens`, `cached_input_tokens`, `wall_clock_ms`, `compute_ms`, `cost_amount`, `cost_currency`, `cost_unit`, `model_ref`, `provider_ref`, `region_ref`). This block is non-authoritative and its absence carries no meaning; its presence enables per-scope, per-actor, and per-task cost and latency analysis without requiring a separate observability path.

## Derived Indexes

A Memory Object may have no embedding, one embedding, or multiple embeddings in different spaces. Every vector MUST reference an Embedding Space. Vectors from incompatible spaces MUST NOT be treated as directly comparable. Semantic-query results MUST identify the Embedding Space used. Embeddings may be regenerated independently.

An Embedding Space descriptor identifies `embedding_space_id`, provider, model, model revision, dimensions, distance metric, normalization, preprocessing profile, embedding kind, and canonicalization rules, plus optional creation metadata. `embedding_space_id` is authoritative for identity. Compatibility MUST NOT be inferred solely from equal dimensions, provider, model name, or distance metric. Exported vectors MUST include or reference enough descriptor information to interpret the space. An identifier MAY later be derived from a canonical descriptor hash, but this revision does not define canonical serialization or require hashing.

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
: Required. Declares the typed content family. Standard object types are `claim`, `decision`, `task`, `artifact`, `observation`, `entity`, and `summary`. Relationship Objects are represented separately (see the Relationships subsection) and are not a Memory Object type. It is immutable for a version; type conversion creates a new version or new object with provenance. It can reveal sensitive purpose or classification.

`schema_id`:
: Optional. Identifies the schema or profile used to interpret `canonical_content`. It is immutable for a version; schema migration creates a new version or migration event. It can reveal application domain.

`canonical_content`:
: Required. Contains authoritative typed content of the version. Changes create a new logical version. Silent in-place overwrite is non-conforming. It can contain personal, confidential, or regulated information.

`lifecycle_state`:
: Required. Records maturity and operational-use posture. Changes create a new Memory Version and Event Ledger entry.

`availability_state`:
: Required. Records whether Canonical Content is available, partially redacted, redacted, or deleted. Changes create a new Memory Version and Event Ledger entry.

`retention_state`:
: Required. Records retained, expired, pending-deletion, or legal-hold policy. Changes create a new Memory Version and Event Ledger entry.

`validation_state`:
: Required. Records authoritative review and confidence posture. Changes create a new Memory Version and Event Ledger entry. `corroborated` does not guarantee objective truth.

`observed_at`, `asserted_at`, `valid_from`, and `valid_until`:
: Optional client- or source-supplied temporal assertions. They do not establish Event Ledger order and may require validation. A `valid_until` value in the past is a client-asserted validity boundary and does not by itself change Retention State, Lifecycle State, or any other authoritative dimension; any lifecycle, retention, or availability effect requires an explicit Transition operation. Implementations MAY use these fields as inputs to temporal queries or scheduled policy evaluation but MUST NOT treat them as authoritative state changes.

`committed_at` and `recorded_at`:
: Required service-assigned timestamps for the Memory Version and Event Ledger record. They are not the sole ordering mechanism.

`sequence`:
: Required service-assigned logical ordering value within the authoritative object history. Sequence values within a single object's version history MUST be strictly increasing. Sequence values MUST NOT be reused within an object history and are not required to be globally unique across objects or scopes.

`actor`:
: Required. Identifies the actor responsible for the operation that produced this version. It is immutable for a version and can contain personal data. The actor MAY declare `on_behalf_of_actor_id` when acting for another principal, `delegation_id` when the operation was authorized by a Delegation Object, and an optional `attestation` block containing a verifiable identity attestation for the actor (agent manifest reference and digest, attestation authority and method, signature, validity window, and declared capabilities). Attestation is non-authoritative in the base profile; a future profile MAY require attestation for specific `actor_kind` values (for example, `agent`) or in specific scopes.

`provenance`:
: Required. Records machine-readable origin, source, evidence, method, and transformation information. Corrections or additions create a new version or provenance event. It can contain personal or source-sensitive data.

`relationship_refs`:
: Optional non-authoritative projection of Relationship Object identifiers. Updating a Relationship Object does not create new versions of its source or target objects.

`integrity`:
: Optional. Contains hashes, signatures, ledger references, or other tamper-evidence metadata. It is bound to the version or event material it covers and can expose correlation or verification metadata.

`quality_signals`:
: Optional machine-readable quality signals produced by automated processes: `assessed_confidence`, `contradiction_score`, `staleness_score`, `evidence_strength`, `source_diversity`, `last_verified_at`, `last_verified_by_actor_id`, `verification_method_id`, `assessed_at`, and `assessed_by_actor_id`. These signals are non-authoritative and MUST NOT be used to override Validation State; retrieval ranking and default filters MAY use them, and profiles MAY define standard thresholds for their use. `assessed_confidence` is the system's or assessor's confidence in the claim after review, distinct from `provenance.source_confidence`, which is the original source's own asserted confidence in what they reported.

## Type System

The standard Memory Object types are `claim`, `decision`, `task`, `artifact`, `observation`, `entity`, `summary`, `tool_invocation`, and `tool_result`. Relationships between Memory Objects are represented as independently identified Relationship Objects and do not appear in this enumeration; see the Relationships subsection. Extension types use a collision-resistant reverse-domain name or absolute URI and include `schema_id`. Implementations MUST preserve unknown extension types during export and import. Implementations MAY reject unsupported extension types during creation. A reader SHOULD return the canonical envelope even when it cannot interpret extension content, subject to policy.

A `tool_invocation` object records that an agent, tool, or user requested execution of a named tool with specified arguments. Its canonical content conforms to `tool-invocation-content.schema.json`. A `tool_result` object records the outcome of a corresponding invocation and references the invocation via `invocation_object_id`; its canonical content conforms to `tool-result-content.schema.json`. Together they make an agent's tool-call history first-class, versioned, and provenanced memory rather than transcript ephemera. Relationship Objects MAY link a `decision` or `claim` to the `tool_result` that informed it (`informed_by`) and a `tool_result` to its `tool_invocation` (`produced_by`).

A `working_memory` object holds persistent per-task scratchpad state that survives process restarts but is distinct from consolidated long-term memory. Its canonical content conforms to `working-memory-content.schema.json`. Working memory objects are created with `lifecycle_state` `scratch` by default, are excluded from default trusted retrieval, and are expected to be either promoted (via the Promote operation) to a canonical Memory Object type such as `claim`, `decision`, `task`, or `summary`, or archived once the associated task is complete. Working memory is how PAMSPEC distinguishes "state the agent needs to resume" from "beliefs the agent has committed to."

Canonical Content MAY be any JSON value. `schema_id` defines type-specific validation. An extension type MUST include `schema_id`.

A `summary` object is an externally representable abstraction of conclusions, evidence, assumptions, constraints, progress, and unresolved questions. It is not private chain-of-thought and does not require disclosure of hidden model reasoning.

## Object Identity

`object_id` identifies the logical Memory Object. `version_id` identifies an immutable Memory Version. Implementations must not reuse a `version_id` for different content or state, and must not replace the content associated with an existing `version_id`.

## Versioning

Every change to Authoritative State MUST create a new immutable Memory Version and MUST create a corresponding Event Ledger entry. Authoritative State includes Canonical Content, authoritative metadata, Lifecycle State, Availability State, Retention State, Validation State, authoritative provenance, authoritative relationship references, and integrity metadata that represents authoritative content. A modification using an obsolete expected version MUST fail with `version_conflict` and MUST NOT overwrite a newer version.

Non-authoritative operational events, including `embedding_generated`, `index_rebuilt`, and `access_denied`, create Event Ledger entries but do not create Memory Versions. Retrieval-cache refresh does not create a Memory Version.

## Relationships

A Relationship Object is independently identified, typed, versioned, and scope-bound. It contains `relationship_id`, `version_id`, `scope_id`, `relationship_type`, source and target object identifiers, directionality, Canonical Content or attributes, provenance, Lifecycle State, Validation State, Availability State, Retention State, temporal fields, and integrity metadata.

A Relationship Object change creates a new Relationship Version and Event Ledger entry. It does not automatically create new versions of source or target objects. Deleting an object does not silently delete related Relationship Objects. Cross-scope relationships require explicit policy. A relationship reference does not grant access, and traversal applies scope and authorization checks at every step.

`relationship_type` values SHOULD use either a short, well-known label from an implementation- or profile-defined vocabulary (for example, `supports`, `contradicts`, `derives_from`, `references`, `supersedes`, `part_of`), or a collision-resistant identifier following the same conventions as extension `object_type` values (reverse-domain name or absolute URI). A future revision may define a registry of well-known relationship types. Implementations MUST preserve unknown `relationship_type` values during export and import.

## Provenance

Provenance records `provenance_id`, source reference, actor, generation activity, evidence references, observed time, recorded time, transformation parent, `source_confidence` (the source's own confidence in what they reported), and optional signature or integrity reference. `source_confidence` is distinct from `quality_signals.assessed_confidence`, which records the system's or reviewer's confidence in the resulting claim. Provenance is authoritative metadata. A provenance modification creates a new Memory Version and Event Ledger entry. Provenance cannot be silently removed. Provenance visibility may be restricted independently from Canonical Content, and a provenance reference does not grant access to its source. The entity, activity, and agent concepts align informatively with W3C PROV {{PROV-DM}} without requiring PROV-O.

## Integrity Metadata

Integrity metadata can include content digests, version digests, ledger references, signatures, or chain hashes. This -00 candidate profile does not mandate a cryptographic algorithm. If integrity metadata is present, it identifies what material is covered and what verification method is used.

# Lifecycle, Availability, Retention, and Validation

Lifecycle State, Availability State, Retention State, and Validation State are separate authoritative dimensions. Lifecycle governs maturity and operational use. Availability governs access to Canonical Content. Retention governs preservation and disposal policy. Validation governs evidence and authorized review. A transition in one dimension does not imply a transition in another.

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

## Availability State

| State | Meaning | Retrieval Default |
| --- | --- | --- |
| `available` | Canonical Content is available subject to normal authorization. | Eligible when other filters permit. |
| `partially_redacted` | A policy-permitted subset of Canonical Content is available. | Returns only the permitted projection. |
| `redacted` | Canonical Content is unavailable; a Tombstone remains. | Excluded except history and policy review. |
| `deleted` | The object is represented only by a terminal Tombstone. | Excluded except authorized history. |

## Retention State

| State | Meaning | Disposal Behavior |
| --- | --- | --- |
| `retained` | Normal retention policy applies. | No disposal is pending. |
| `expired` | Retention time has elapsed. | Policy evaluates deletion or archival. |
| `pending_deletion` | Deletion is authorized and awaits completion or propagation. | New retrieval is policy-restricted. |
| `legal_hold` | Disposal is suspended by explicit policy. | Delete and incompatible redaction operations fail with `legal_hold`. |

## State Transitions

Transitions require an actor and policy basis. Every successful transition creates a new Memory Version and Event Ledger entry. Invalid transitions fail with `invalid_state_transition`.

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

Availability transitions are:

| From | Allowed To |
| --- | --- |
| `available` | `partially_redacted`, `redacted`, `deleted` |
| `partially_redacted` | `available`, `redacted`, `deleted` |
| `redacted` | `available` with restoration policy, `deleted` |
| `deleted` | none |

Retention transitions are:

| From | Allowed To |
| --- | --- |
| `retained` | `expired`, `pending_deletion`, `legal_hold` |
| `expired` | `retained`, `pending_deletion`, `legal_hold` |
| `pending_deletion` | `retained`, `legal_hold` |
| `legal_hold` | `retained`, `expired`, `pending_deletion` after hold release |

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
  },
  "availability": {
    "available": ["partially_redacted", "redacted", "deleted"],
    "partially_redacted": ["available", "redacted", "deleted"],
    "redacted": ["available", "deleted"],
    "deleted": []
  },
  "retention": {
    "retained": ["expired", "pending_deletion", "legal_hold"],
    "expired": ["retained", "pending_deletion", "legal_hold"],
    "pending_deletion": ["retained", "legal_hold"],
    "legal_hold": ["retained", "expired", "pending_deletion"]
  }
}
~~~

## Expiration, Redaction, and Deletion

Expiration changes Retention State to `expired`; it does not change Lifecycle State by itself. Redaction creates a new terminal or non-terminal Memory Version with Availability State `partially_redacted` or `redacted` and a corresponding Event Ledger entry. Deletion creates a final immutable Tombstone Memory Version with Availability State `deleted` and a corresponding Event Ledger entry. A legal hold is represented only by Retention State `legal_hold`.

# Operation Semantics

All operations are evaluated within a Memory Scope and against authorization policy. Bindings can expose different wire forms, but the semantic inputs, preconditions, results, version effects, Event Ledger effects, Derived Index effects, retry behavior, and error codes in this section are preserved.

## Create

Purpose: create a new Memory Object. Required inputs are an operation identifier or idempotency key, scope identifier, object type, Canonical Content, Lifecycle State, Availability State, Retention State, Validation State, actor, provenance, and `schema_id` when required by the type. Optional inputs include object identifier, temporal assertions, integrity metadata, expected-absence precondition, and Derived Index request. Create evaluates scope and authorization before commit. A successful Create returns object identity, version identity, scope, committed envelope, and ledger event identity. It produces `object_created`. A repeated Create with the same idempotency key and identical request content returns the original result. The same key with different request content fails with `duplicate_operation`.

## Read

Purpose: retrieve authoritative object state. Required inputs: operation identifier, scope identifier, and object identifier. Optional inputs: version identifier, snapshot identifier, requested fields, and history hint. Read evaluates scope and authorization. A successful Read returns the requested authoritative version or a scope-safe redacted/deleted result. Read does not create a new object version. It may create access or denial events if policy requires audit. Possible errors include `object_not_found`, `scope_not_found`, `access_denied`, `object_redacted`, `object_deleted`, `snapshot_not_found`, `service_unavailable`, and `internal_error`.

## Update

Purpose: create a new logical version of Canonical Content or authoritative metadata. Required inputs: operation identifier, scope identifier, object identifier, expected version, actor, provenance, and update content. Optional inputs: schema identifier, relationships, integrity metadata, and idempotency key. Update uses expected-version semantics unless a future profile defines conflict-free merge semantics. A stale expected version fails with `version_conflict`. A successful Update returns the new version and produces `object_updated` plus related events. Derived Indexes become stale until rebuilt. Possible errors include `invalid_request`, `invalid_object`, `version_conflict`, `object_not_found`, `access_denied`, `policy_denied`, `retention_restriction`, `object_deleted`, `service_unavailable`, and `internal_error`.

## Transition

Purpose: change Lifecycle State, Availability State, Retention State, or Validation State. Required inputs are operation identifier, scope identifier, object identifier, expected version, transition dimension, target state, actor, and policy basis. A successful Transition always returns a new Memory Version and produces the dimension-specific Event Ledger entry. Derived Index filters may need refresh. Possible errors include `invalid_state_transition`, `version_conflict`, `policy_denied`, `access_denied`, `legal_hold`, `object_not_found`, and `retention_restriction`.

## Relate

Purpose: create or update a Relationship Object. Required inputs are operation identifier, scope identifier, source object, target object, relationship type, directionality, actor, provenance, and the four state dimensions. Updating requires relationship identifier and expected Relationship Version. Cross-scope relationships require explicit policy and authorization. A successful Relate returns the new Relationship Version and produces `relationship_created` or `relationship_updated`. It does not change source or target object versions.

## Query

Purpose: retrieve sets of Memory Objects, Relationship Objects, or versions using structured, semantic, hybrid, temporal, or snapshot criteria. Required inputs are operation identifier, scope identifier, query expression, pagination parameters, and actor. Optional inputs include Lifecycle State, Availability State, Retention State, Validation State, provenance, object type, temporal, and relationship filters; Embedding Space; snapshot identifier; ordering profile; and ranking explanation request. Query defaults to scope-bound evaluation and does not default to unscoped global semantic search.

## Inspect History

Purpose: inspect object versions, transitions, relationships, and Event Ledger entries. Required inputs: operation identifier, scope identifier, object identifier or event range, and actor. Optional inputs: version range, event classes, snapshot boundary, and redaction policy. A successful result returns scope-safe history. Redacted content can appear as tombstone metadata rather than content.

## Subscribe

Purpose: open a durable stream of Event Ledger entries that match a filter within a scope, so that agents and integrators react to memory changes instead of polling. Required inputs are operation identifier, scope identifier, actor, and a filter expression. Optional inputs include object type, event class list, object identifier, `after_sequence` (a starting point in the ledger for at-least-once catch-up), and delivery preferences (batching, keepalive interval, backpressure policy).

A successful Subscribe returns a `subscription_id`, the resolved filter, the ledger sequence at which delivery starts, and a delivery channel identifier appropriate to the binding (for example, a WebSocket URL, an MCP notification stream, or a message-bus topic). While the subscription is open, the Memory Service MUST deliver every event that (a) satisfies the filter, (b) occurs within an authorized scope, and (c) has a ledger sequence greater than the last acknowledged sequence for that subscription. Ordering within a single scope MUST be preserved.

Delivery guarantees are at-least-once. Subscribers are responsible for idempotent processing keyed by `event_id`. Subscriptions MAY be closed by the caller (`Unsubscribe`, referencing `subscription_id`) or by the service on authorization revocation, scope deletion, prolonged unacknowledged backpressure, or shutdown. On service-initiated close, a terminal close event identifies the last delivered `ledger_sequence` so the subscriber can resume against a new subscription with `after_sequence` set appropriately.

Subscribe does not create Memory Versions. Subscribe creates a `subscription_opened` Event Ledger entry when the subscription starts and a `subscription_closed` entry when it ends. Filter evaluation and authorization MUST be applied per event, not only at subscription time, so that events an actor loses authorization for during the subscription lifetime are excluded from further delivery. Possible errors include `invalid_request`, `scope_not_found`, `access_denied`, `policy_denied`, `service_unavailable`, and `internal_error`.

## Redact

Purpose: remove or suppress protected content while preserving permitted audit information. Required inputs are operation identifier, scope identifier, object identifier, expected version, actor, policy basis, and redaction target. A successful Redact creates a new Tombstone or partially redacted Memory Version, changes Availability State, and produces `object_redacted`. Derived Index deletion is triggered or recorded independently. Redaction blocked by policy returns `retention_restriction` or `legal_hold`.

## Promote

Purpose: convert a `working_memory` object into a canonical Memory Object of a target type such as `claim`, `decision`, `task`, or `summary`, preserving provenance and creating an explicit link. Required inputs are operation identifier, scope identifier, source `working_memory` object identifier, expected version, target `object_type`, target `canonical_content` (which MUST conform to the target type's content schema when one is defined), actor, and provenance. Optional inputs include target `object_id`, target Lifecycle State, target Validation State, and idempotency key.

A successful Promote creates a new canonical Memory Object with `provenance.transformation_parent` set to the source `working_memory` version identifier, and transitions the source `working_memory` object's Lifecycle State to `superseded` in a paired ledger event. Both new versions and their events commit atomically. The Promote operation produces `object_created` for the new object, `lifecycle_transitioned` for the source, and a `working_memory_promoted` Event Ledger entry that links the two. Possible errors include `invalid_request`, `object_not_found`, `version_conflict`, `access_denied`, `policy_denied`, and `invalid_state_transition`.

Promote does not require deletion of the source; consolidation history remains inspectable through `inspect_history` and via the Relationship Object that Promote creates (`derived_from`, directed from the new object to the source `working_memory`).

## Delete

Purpose: remove active availability of an object according to policy. Required inputs are operation identifier, scope identifier, object identifier, expected version, actor, and policy basis. A successful Delete creates the final Tombstone Memory Version with Availability State `deleted` and produces `object_deleted`. Existing Relationship Objects remain independently governed. Delete does not imply immediate removal from backups unless policy says so. Deletion blocked by legal hold returns `legal_hold`.

# Query and Retrieval Model

Structured retrieval evaluates deterministic filters over authoritative fields, including Memory Scope, object type, Lifecycle State, Availability State, Retention State, Validation State, schema identifier, provenance, actor, observation time, validity interval, commit time, record time, sequence, version, Relationship Object, and integrity metadata. When evaluated against the same authoritative snapshot and ordering profile, structured retrieval is repeatable.

Semantic retrieval evaluates approximate similarity through a Derived Index. A semantic result should identify the Embedding Space, index or snapshot identity where available, semantic score, reranking score where applicable, applied filters, and stable tie-break information. Semantic retrieval is approximate unless evaluated against a named stable index snapshot with declared ordering behavior.

Hybrid retrieval combines structured filters with semantic ranking or reranking. Structured filters are evaluated within scope before protected content is disclosed. Relationship traversal evaluates authorization for each target object. Cross-scope traversal requires explicit policy.

Temporal evaluation explicitly selects observation time, assertion time, validity interval, commit time, record time, logical sequence, or snapshot. Client-supplied times do not control conflict resolution or Event Ledger ordering. Snapshot-based evaluation provides repeatable retrieval within a named snapshot. If no stable index snapshot exists, semantic retrieval is best-effort and identifies that no stable index snapshot was used.

Pagination includes a stable cursor or ordering basis when repeatability is claimed. Stable ordering uses deterministic keys such as snapshot identifier, primary score, secondary score, update time, object identifier, and version identifier. Tie-breaking is documented for any profile that claims repeatable retrieval.

Default retrieval is conservative: Lifecycle State `active`, Availability State `available`, Retention State `retained`, and Validation State `corroborated` form the normal trusted retrieval target. Other states require explicit query policy or filters unless a profile declares different defaults.

# Consistency and Concurrency

The candidate profile uses optimistic concurrency. Update, Transition, Redact, Delete, and Relationship Object operations use expected-version semantics. An operation with an obsolete expected version fails with `version_conflict` and returns the current version identifier when policy permits.

Idempotency keys identify duplicate requests. A duplicate request with the same idempotency key and identical request content returns the original successful result or original stable error. A duplicate request with the same idempotency key and different content fails with `duplicate_operation`.

A committed Memory Version and its required Event Ledger entry are atomic from the perspective of Inspect History. If either cannot be committed, the state-changing operation fails. Implementations can use different physical mechanisms to provide this logical atomicity.

Read-after-write behavior applies to authoritative state: after a successful state-changing operation, a scoped Read by an authorized actor observes the committed authoritative state. Derived Indexes can be eventually consistent. Query responses using derived state expose index identity, freshness, or staleness where available.

Snapshots provide a consistent read boundary over Authoritative State and, when declared, over Derived Index state. The Memory Service assigns commit time, record time, and logical sequence. Wall-clock time alone never establishes authoritative ordering. Client-supplied future timestamps, clock skew, forged observation times, and ambiguous time zones are treated as untrusted temporal assertions.

# Protocol Bindings

This document does not standardize a mandatory transport. Every future binding preserves object identity, Memory Scope, authorization outcome, version preconditions, idempotency behavior, operation semantics, stable error codes, Event Ledger behavior, query parameters, deletion semantics, and redaction semantics.

An embedded library binding can expose operations as local function calls. An HTTP binding can map operations to resources and methods. An MCP binding can map operations to tools or resources. A gRPC binding can map operations to services and messages. Event bus or message bus bindings can expose ledger streams, asynchronous commands, or index rebuild events. None of these bindings is mandatory.

A non-normative reference MCP binding is published under `bindings/mcp/`. It maps every PAMSPEC operation to a stable tool name (`pamspec.<operation>`), maps Memory Scopes to MCP resources (`pamspec://scope/{scope_id}/...`), preserves the PAMSPEC error envelope end-to-end rather than collapsing errors into MCP protocol errors, and defines a discovery manifest that advertises supported profiles and operations. Servers that implement the reference binding become usable by any MCP-aware client without per-client integration work.

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

Delegated authority SHOULD be represented explicitly as a **Delegation Object** (`delegation.schema.json`). A Delegation Object is an independently identified, typed, versioned, scope-bound authoritative object that binds a `granting_actor` to a `delegated_actor` over a bounded set of `granted_operations`, an optional `granted_object_types` and `granted_object_ids` restriction, an optional `target_scope_id` for cross-scope delegation, a required `policy_basis`, a `not_before` / `not_after` window, an optional `usage_limit`, and a `revocable` flag. Every exercise of a delegation MUST reference the `delegation_id` in provenance so an audit can reconstruct the chain from operation back to grant. Delegation Objects produce `delegation_granted`, `delegation_revoked`, and `delegation_exercised` Event Ledger entries. A delegation whose `not_after` has passed, whose `usage_limit` is exhausted, or whose grantor no longer holds the granted operations MUST be treated as no longer effective, regardless of Lifecycle State. Delegation Objects do not themselves grant authority — they record that authority was granted by an actor who held it; authorization enforcement remains the responsibility of the Memory Service and its policy engine.

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

Implementations distinguish observation time, assertion time, validity interval, commit time, record time, and logical sequence. The Memory Service assigns commit time, record time, and sequence. Client-supplied observation or assertion times may be absent and are untrusted until validated.

## Observability

Observability should expose operational state without leaking protected memory content.

## Capacity and Retention Planning

Capacity planning should account for authoritative versions, ledger entries, snapshots, derived indexes, and tombstones.

# Interoperability and Conformance

Implementations declare the profile name and version they support. Partial implementation is permitted, but an implementation MUST NOT claim a profile unless it satisfies every mandatory requirement for that profile.

## PAMSPEC-Lite

PAMSPEC-Lite is a minimal on-ramp profile for single-developer agents, prototypes, and embedded deployments. A Conforming Implementation of PAMSPEC-Lite MUST support:

- Memory Scope enforcement for reads, writes, and queries.
- The canonical Memory Object envelope with stable `object_id` and immutable `version_id`.
- The Lifecycle State subset `active`, `superseded`, and `archived`.
- The Availability State subset `available` and `deleted` (with a terminal tombstone).
- The Retention State subset `retained` and `pending_deletion`.
- The Validation State subset `unverified` and `corroborated`.
- Append-only Event Ledger recording of `object_created`, `object_updated`, `object_deleted`, `lifecycle_transitioned`, and `validation_transitioned` events, with atomic version+event commit.
- Expected-version preconditions on Update, Transition, and Delete, and `version_conflict` on stale expectations.
- Idempotency-key handling for Create.

PAMSPEC-Lite deliberately omits Relationship Objects, Semantic Query, Snapshots, Redaction (beyond deletion), Legal Hold, and Derived Index management. Implementations that support any of those areas SHOULD declare the corresponding full profile instead of, or in addition to, PAMSPEC-Lite.

A reference implementation of PAMSPEC-Lite is provided under `implementations/reference-python/` for illustration; it is not normative.

## PAMSPEC-Core

Requires Memory Scope enforcement, the canonical Memory Object envelope, stable object identity, immutable version identity, the four state dimensions, Authoritative State versus Derived Index separation, the core error envelope, and exportable representation.

## PAMSPEC-Versioning

Requires expected-version semantics, a new immutable Memory Version for every Authoritative State change, `version_conflict`, and historical reads.

## PAMSPEC-Ledger

Requires append-only event recording, object-version linkage, authoritative-change events, event-only operational events, logical ordering, and Tombstone behavior compatible with erasure and legal hold.

## PAMSPEC-Structured-Query

Requires scope filtering, filters for all four state dimensions, temporal filters, stable ordering, pagination, and snapshot-bound repeatability.

## PAMSPEC-Semantic-Query

Requires Embedding Space descriptors, semantic-result metadata, incompatible-space rejection, approximate-retrieval disclosure, and index or snapshot identity where available.

## PAMSPEC-Relationship

Requires independently identified and versioned Relationship Objects, cross-scope policy, source and target authorization, and traversal checks at every step.

## PAMSPEC-Protocol-Binding

Requires preservation of operation semantics, stable error-code mapping, authorization outcomes, idempotency, version preconditions, query parameters, Event Ledger behavior, redaction, and deletion semantics without mandating a transport.

## PAMSPEC-Evaluation

Sub-profile for deterministic agent evaluation. A Conforming Implementation of PAMSPEC-Evaluation MUST support:

- **Sealed Snapshots**: immutable Snapshot descriptors conforming to `evaluation-snapshot.schema.json`, with a fixed `ledger_sequence_high_watermark` and explicit or implicit object and Embedding Space membership. Once sealed, a snapshot's authoritative membership and derived-index identity MUST NOT change; a new snapshot MUST be created for any change.
- **Deterministic clock injection**: when a snapshot declares `deterministic_clock`, evaluation-time operations conducted against the snapshot MUST use the declared clock as the source for any authoritative timestamp that would otherwise be wall-clock derived, so replays yield identical timestamps.
- **Deterministic RNG seeding**: when a snapshot declares `deterministic_rng_seed`, evaluation-time operations MUST seed randomness (retrieval tie-break jitter, sampling) with the declared seed.
- **Evaluation-run propagation**: when a snapshot declares `evaluation_run_id`, that identifier MUST be propagated into the `provenance` of every Memory Version and Event Ledger entry produced during evaluation-time operations, so evaluation-authored memory is distinguishable from production-authored memory.
- **Snapshot comparison**: implementations MUST support inspecting two sealed snapshots and reporting authoritative differences (added or removed objects, version deltas, state transition deltas) using the same query surface as Inspect History, so regression comparison between evaluation runs is expressible.

PAMSPEC-Evaluation composes with other profiles. It does not by itself require Semantic Query or Relationship support. Evaluation-time operations MUST NOT modify state outside the evaluation scope unless policy explicitly permits it.

## Implementation Reports

Implementation reports MUST document supported profile names and versions. They SHOULD document storage choices, authorization model, index behavior, export behavior, deletion behavior, test-vector results, and known deviations.

# IANA Considerations

This document has no IANA actions.

# References

Normative and informative references are declared in the document metadata. This draft uses RFC 2119 {{RFC2119}} and RFC 8174 {{RFC8174}} normatively for requirements language. It uses URI syntax {{RFC3986}}, URN syntax {{RFC8141}}, Internet timestamps {{RFC3339}}, JSON {{RFC8259}}, JSON Patch {{RFC6902}}, HTTP semantics {{RFC9110}}, UUIDs {{RFC9562}}, JSON Schema {{JSON-SCHEMA}}, and W3C PROV-DM {{PROV-DM}} informatively for architectural alignment and review.

Related implementation context includes OpenAI session and conversation-state documentation {{OPENAI-AGENTS-SESSIONS}} {{OPENAI-CONVERSATION-STATE}}, Anthropic multi-agent engineering material {{ANTHROPIC-MULTIAGENT}}, LangGraph memory documentation {{LANGGRAPH-MEMORY}}, Letta memory documentation {{LETTA-MEMORY}}, MemGPT research {{MEMGPT-PAPER}}, Mem0 documentation {{MEM0-DOCS}}, event-sourcing literature {{FOWLER-EVENT-SOURCING}}, and Agent Communication Gateway material {{AGENT-COMMUNICATION-GATEWAY}}.

Related academic and industry research on agent memory architectures includes the Cognitive Architectures for Language Agents (CoALA) taxonomy {{COALA}}, the Generative Agents memory-stream-plus-reflection pattern {{GENERATIVE-AGENTS}}, HippoRAG's neurobiologically inspired long-term memory {{HIPPORAG}}, a survey of the memory mechanism of LLM-based agents {{AGENT-MEMORY-SURVEY}}, and the LongMemEval {{LONGMEMEVAL}} and LoCoMo {{LOCOMO}} benchmarks for long-term interactive memory. Multi-agent coordination context includes a survey of LLM-based multi-agent systems {{MAS-LLM-SURVEY}} and MetaGPT {{METAGPT}}.

Provenance context includes Model Cards {{MODEL-CARDS}}, Datasheets for Datasets {{DATASHEETS}}, and PROV-AGENT, a PROV extension for agentic workflows {{PROV-AGENT}}. Embedding-space portability research includes Relative Representations {{RELATIVE-REPRESENTATIONS}} and Matryoshka Representation Learning {{MATRYOSHKA}}.

Agent identity and attestation context includes W3C Decentralized Identifiers {{W3C-DID}}, the Agent Identity Protocol IETF draft {{AIP-DRAFT}}, the Agent-ID Framework IETF draft {{AGENT-ID-FRAMEWORK}}, and the SCITT transparency architecture {{SCITT}}. IETF work adjacent to PAMSPEC includes the AI Agent Protocols framework draft {{AI-PROTOCOLS-FRAMEWORK}}, MCP-over-MoQ {{MCP-OVER-MOQ}}, and MCP security considerations {{MCP-SECURITY}}.

Retrieval evaluation context includes RAGAS {{RAGAS}} and the Retrieval-Augmented Generation Benchmark {{RGB-BENCHMARK}}. Cognitive-science analogues for the PAMSPEC memory-type vocabulary include Tulving's episodic and semantic memory distinction {{TULVING-EPISODIC}}, Baddeley and Hitch's working-memory model {{BADDELEY-WM}}, Baddeley's episodic buffer {{BADDELEY-EPISODIC-BUFFER}}, the Complementary Learning Systems theory {{CLS-THEORY}}, and Squire's overview of the brain's memory systems {{SQUIRE-MEMORY-SYSTEMS}}. These are cited informatively; PAMSPEC does not require or endorse any specific cognitive theory.

--- back

# Canonical JSON Schemas

The `schemas/0.1-draft/` directory contains the candidate interoperability schema profile. Schema identifiers are versioned under the provisional public GitHub namespace. Schema warnings are metadata and are not transmitted in PAMSPEC instances.

# State Transition Tables

Section 9 defines human-readable and machine-readable transition tables for Lifecycle State, Availability State, Retention State, and Validation State. Object-type profiles may further restrict transitions but cannot move values between dimensions.

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

Agent Communication Gateway for Semantic Routing and Working Memory, currently `draft-agent-gw-01` and a Work in Progress, focuses on agent communication, semantic routing, protocol adaptation, capability discovery, and active workflow or working context {{AGENT-COMMUNICATION-GATEWAY}}. PAMSPEC focuses on persistent, typed, versioned, scoped, auditable Memory Objects, Relationship Objects, Event Ledger history, and Derived Indexes. The architectures are complementary: an agent gateway can carry references to PAMSPEC Memory Objects, while PAMSPEC does not define agent discovery, semantic routing, capability negotiation, or protocol adaptation.

Cognitive-architecture research on language agents, particularly the Cognitive Architectures for Language Agents (CoALA) taxonomy {{COALA}}, distinguishes working, episodic, semantic, and procedural memory. PAMSPEC's standard object types (`claim`, `decision`, `task`, `artifact`, `observation`, `entity`, `summary`, `tool_invocation`, `tool_result`, `working_memory`) approximate this taxonomy without adopting it as normative: `working_memory` maps to CoALA working memory, `claim` and `entity` to semantic memory, `observation` to episodic memory, and `tool_invocation` and `tool_result` to procedural memory traces. Cognitive-science foundations for the distinctions include Tulving's episodic and semantic memory {{TULVING-EPISODIC}}, Baddeley and Hitch's working-memory model {{BADDELEY-WM}} and the episodic buffer {{BADDELEY-EPISODIC-BUFFER}}, the Complementary Learning Systems theory {{CLS-THEORY}}, and Squire's overview of memory systems of the brain {{SQUIRE-MEMORY-SYSTEMS}}. These are cited informatively; conformance does not require adopting any specific cognitive theory.

Concrete memory architectures inform PAMSPEC's design: Generative Agents' memory-stream-plus-reflection pattern {{GENERATIVE-AGENTS}} inspired the append-only Event Ledger plus generated retrieval summaries as Derived Indexes; HippoRAG {{HIPPORAG}} demonstrates hippocampus-indexing-style retrieval that a PAMSPEC-conformant Derived Index can implement; a survey of memory mechanisms in LLM agents {{AGENT-MEMORY-SURVEY}} maps the design space PAMSPEC positions within. Long-term memory benchmarks LongMemEval {{LONGMEMEVAL}} and LoCoMo {{LOCOMO}} are suitable evaluation targets for PAMSPEC-conformant stores.

Provenance for AI systems has multiple related standards. Model Cards {{MODEL-CARDS}} and Datasheets for Datasets {{DATASHEETS}} document the model and data sides of ML provenance; PAMSPEC provenance objects SHOULD reference these where applicable. PROV-AGENT {{PROV-AGENT}} extends W3C PROV specifically for agentic workflows; PAMSPEC's provenance model is compatible in spirit and cites PROV-DM directly.

Embedding-space portability is an open research area. Relative Representations {{RELATIVE-REPRESENTATIONS}} and Matryoshka Representation Learning {{MATRYOSHKA}} suggest paths toward cross-model comparability. PAMSPEC's Embedding Space identity model reflects the current state of the art: vectors from different spaces MUST NOT be treated as directly comparable, but explicit re-projection or alignment is not forbidden.

Agent identity and attestation is an emerging standards area. The IETF Agent Identity Protocol {{AIP-DRAFT}}, the Agent-ID Framework {{AGENT-ID-FRAMEWORK}}, W3C DIDs {{W3C-DID}}, and the SCITT transparency architecture {{SCITT}} provide the identity, delegation, and provenance-anchoring substrate that a PAMSPEC actor attestation block can reference. PAMSPEC deliberately does not mandate any specific identity mechanism; the `attestation` block is designed to carry the identifiers and signatures produced by whichever mechanism an implementation chooses.

Adjacent IETF work on AI agent protocols includes a framework document {{AI-PROTOCOLS-FRAMEWORK}}, MCP-over-MoQ transport {{MCP-OVER-MOQ}}, and MCP security considerations {{MCP-SECURITY}}. PAMSPEC's transport-neutral core plus its reference MCP binding (see Protocol Bindings) are intended to be compatible with all of them.


# Acknowledgements

This initial draft records architectural requirements and open issues for review. Additional acknowledgements will be added when contributors provide review or text.

Robert Leroux contributed project review and specification feedback and is acknowledged as a contributor. Formal co-authorship or editorship remains pending explicit consent and complete public author metadata.
