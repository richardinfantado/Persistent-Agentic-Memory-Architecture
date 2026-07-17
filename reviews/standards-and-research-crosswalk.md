# PAMSPEC Standards and Research Crosswalk

Repository: https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture
Pinned commit: 45c42db6069212b5237d577b99fa7c7b03840d85 (main tip, 2026-07-17T15:32:02Z, "Merge C11: portable conformance harness")
Review date: 2026-07-18
Author: research subagent (R2 evidence gathering)

## Framing statement

This document is a research crosswalk. It compares the PAMSPEC draft in the pinned repository against (a) adjacent standards work already visible in the IETF datatracker and at W3C, (b) primary academic evidence on persistent agent memory, and (c) the actual IETF process and venue rules. It is intended to inform, not to justify, downstream decisions about wording, scope, and submission timing.

Three framing rules apply throughout and are the reason several confident-sounding claims elsewhere in the ecosystem must be softened here. First, an individual Internet-Draft is not an IETF standard; per RFC 2026 "Internet-Drafts have no formal status, and are subject to change or removal at any time." Second, a W3C Community Group is not the W3C Recommendation track; CG output is licensed and useful but is not a W3C standard. Third, a preprint on arXiv is not peer-reviewed and must be cited as a preprint. Where evidence is preliminary or contested, this document says so.

## 1. Executive conclusion

1. **Distinct problem?** Partially. PAMSPEC's stated centre of gravity — a provider-independent, machine-readable data model for persistent agent memory with an append-only Event Ledger, versioned Memory Objects, embedding-space identity, and profile-based conformance — is a coherent problem. However, at least two of its sub-problems (interchange bundle format and memory-cell portability) are already occupied by `draft-vu-aimem-bundle-00` (AIMEM) and by `draft-saihm-memory-protocol-01` (SAIHM). PAMSPEC as a whole is not duplicative, but a "PAMSPEC bundle" would be.
2. **Overlap?** Material overlap exists with AIMEM on bundle envelope, chunk records, identifier URN scheme, embedding metadata, and idempotent import; with SAIHM on cell shape, sharing contracts, and cryptographic erasure; with FAF/FAFM on the memory-vs-context distinction and mutation semantics; with the arXiv preprint 2605.11032 (Portable Agent Memory) on Merkle-DAG provenance and capability-scoped disclosure; and with MCP on transport binding surface.
3. **Differentiation?** PAMSPEC's plausible differentiators are (a) an explicit atomic version+event commit protocol with a `version_conflict` semantic, (b) an "Embedding Space" identity descriptor that lets consumers reject incompatible-space vectors rather than silently re-embed, (c) a conformance-profile system (`PAMSPEC-Lite`, `-Ledger`, `-Semantic-Query`, `-Evaluation`, plus Delegation and Subscribe extensions), and (d) a portable adapter-based conformance harness. None of these is proven novel in the sense that no adjacent work touches them; each is a defensible refinement.
4. **Remove/defer?** Delegation Objects and Subscribe operations should stay as *extension profiles*, not core, until independent implementation evidence justifies core status; agent-identity work is being actively drafted elsewhere (draft-singla, draft-aip, draft-drake, draft-larsson, draft-sharif) and PAMSPEC should not annex it. Working Memory as a first-class *portable* type is not currently supported by strong evidence and should stay optional.
5. **IETF venue?** For a memory data-model spec with a small individual author team, no WG has jurisdiction today. The realistic near-term venues are (i) an individual submission on the standard I-D track with Intended Status **Informational** or **Experimental**, (ii) the Independent Submissions Editor (RFC Editor stream) if the IESG does not sponsor, or (iii) participation in the W3C AI Agent Memory Interoperability CG to influence conformance and test-vector work. IRTF is a plausible home if the project reframes as a research report rather than an engineering spec.
6. **What -00 should claim.** A `-00` may claim exactly this: that it is an individual submission of an Internet-Draft, that it defines a candidate data model and event ledger for persistent agent memory, that a reference implementation exists, and that it is not endorsed by the IETF and has no formal status. It must not claim: "IETF standard," "adopted," "reviewed," or novelty over documented prior art without a direct comparison paragraph.

## 2. Concern-by-concern standards matrix (R2-A)

### 2.1 Cross-cutting matrix

| PAMSPEC concern | AIMEM (draft-vu-aimem-bundle-00) | SAIHM (draft-saihm-memory-protocol-01) | FAF/FAFM (draft-wolfe-faf-format-02) | Portable Agent Memory (arXiv 2605.11032, preprint) | W3C AI Agent Memory Interop CG | MCP (2026-07-28 RC) |
|---|---|---|---|---|---|---|
| Normative scope | Interchange bundle format | Wire protocol + tool surface | Two YAML media types (context + memory) | Cross-agent memory transfer protocol | Interop profile + tests atop SAIHM | Client–server context protocol |
| Object model | envelope, ChunkRecord, edges, entities, embeddings (§2) | memory cells with encrypted body (§2–§4) | .faf units + .fafm memory units (§3–§4) | 5-component structured memory | Cell shape (from CG scope) | resources / tools / prompts |
| Identifier model | `urn:aimem:<producer>:<local-id>` (§2) | wallet-derived per-cell keys (§4) | namepoint (§2) | content-addressable (BLAKE3) | identity binding via ML-DSA-65 | URI-scoped resource IDs |
| Versioning | envelope version + idempotent re-import (§2, §7) | rotation versioning (§4) | multi-profile + retention (§4) | Merkle-DAG derivation chain | rotation versioning | schema versioned per release |
| Provenance | producer namespace + checksum (§2) | audit anchors on public chain (§5) | promotion lineage (§5) | signed Merkle-DAG root (Ed25519) | audit anchor properties | not in-scope |
| Scope / tenancy | tenant_id UUID/URI + FULL/DNA_ONLY/SINCE scopes (§2) | per-cell encryption keys (§4) | profiles (§4) | capability-scoped disclosure | sharing contracts | session scope |
| Event history | idempotent chunk re-ingest (§2) | receipts (§5) | etch/recall/forget ops (§2) | derivation-graph edges | not explicitly | notifications |
| Embedding metadata | base64 float32 + declared model id (§2) | not central | optional | included | not central | not in-scope |
| Lifecycle / governance | DNA-class invariant, no silent decay (§5) | GDPR Art. 17 erasure (§5) | retention policies (§4) | not central | GDPR Art. 17 erasure | deprecation policy (2026 RC) |
| Import / export | HTTP profile (§3) | tool surface (§3) | well-known URI (§6) | JSON-first + optional CBOR | test-vector pack | resources API |
| Canonicalization / integrity | SHA-256 checksum + optional COSE_Sign1 (§2, §5) | post-quantum sigs (§5) | YAML 1.2 canonical | BLAKE3 content-address | conformance vectors | JSON-RPC 2.0 framing |
| Conformance model | Producer / Consumer / Bidirectional levels (§4) | reference deployment (App.) | recommended fields | 54-test Python SDK | conformance & test-vector pack | client + server conformance |
| Protocol bindings | HTTP export/import (§3) | MCP tool surface (§3) | well-known URI | JSON/CBOR wire | not yet | HTTP + stdio + streaming |
| Implementation evidence | Apache-2.0 reference implementation cited | reference deployment in appendix | reference tools referenced | Python SDK (54 tests) | none yet | multiple production impls |
| Security model | erasure, replay, authenticity, embedding privacy (§5) | PQ crypto, wallet keys, erasure receipts (§6–§7) | prompt-injection, YAML risks (§7) | injection-resistant rehydration | atop SAIHM | authorization hardening (2026 RC) |

Note: section-number references are drawn from the datatracker landing pages and (where accessible) the HTML rendering. Where a section is inferred from an abstract or from the CG charter rather than directly read, the row is phrased in general terms.

### 2.2 AIMEM (`draft-vu-aimem-bundle-00`)

- Document identifier and revision: `draft-vu-aimem-bundle-00`; posted 2026-06-14; author Vu Duc Minh (MemoryAI); intended status Informational; individual submission; not endorsed by IETF.
- Status: Active Internet-Draft; -00 revision; will expire six months after posting per RFC 2026 unless updated.
- Standards venue: IETF individual submission (datatracker only; no WG, no stream assignment).
- Scope: interchange bundle format only. Explicitly names Producer, Consumer, and Bidirectional conformance. Defines DNA-class chunk types (`preference`, `decision`, `identity`, `pitfall`, `procedure`) with an invariant that they cannot be silently decayed or deleted.
- Object model: envelope (`format`, `version`, `producer`, `tenant_id`, `scope`, `checksum`) + ChunkRecord + edges + entities + embeddings (§2). Identifiers: `urn:aimem:<producer>:<local-id>`. Embeddings: base64 float32 with declared model identifier, precisely to prevent silent re-embedding — the same problem PAMSPEC's Embedding Space descriptor targets.
- Integrity/canonicalization: SHA-256 envelope checksum plus optional COSE_Sign1 signature (§5).
- Import/export: HTTP profile in §3.
- Conformance: three levels in §4.
- Security: §5 covers DNA-class invariant, right to erasure with cascade, authenticity, replay protection, embedding privacy.
- Implementation evidence: Apache-2.0 reference implementation cited in the draft.
- **Direct implication for PAMSPEC.** AIMEM already occupies "memory-bundle exchange semantics" as an individual I-D. A PAMSPEC-defined bundle that duplicates envelope, chunk record, URN identifier scheme, and embedding-metadata fields cannot honestly be described as novel. The safe dispositions are: (i) profile AIMEM as PAMSPEC's exchange binding, (ii) coordinate with the AIMEM author on shared IANA registrations, or (iii) explicitly compare and justify divergences.

### 2.3 SAIHM (`draft-saihm-memory-protocol-01`)

- Identifier and revision: `draft-saihm-memory-protocol-01`; dated 2026-05-27; expires 2026-11-28; author Russell Jackson; intended status Informational; individual submission; not endorsed by IETF.
- Scope: memory-layer protocol featuring post-quantum crypto, public-blockchain audit anchoring, per-cell encryption with wallet-derived keys, revocable sharing, GDPR-Article-17-aligned cryptographic erasure. Explicitly complements MCP.
- Object model: memory cells with encrypted body; wire formats (§4); receipts and audit semantics (§5); MCP tool binding (§3).
- Governance and jurisdiction: SAIHM is the *normative* target that the W3C AI Agent Memory Interoperability CG builds atop; that CG will not develop a competing normative spec.
- **Direct implication for PAMSPEC.** SAIHM asserts jurisdiction over the "portable memory cell with post-quantum identity and cryptographic erasure" problem, and it has a matching W3C CG behind it. PAMSPEC's Scope and Delegation profiles will look adjacent to SAIHM's sharing contracts. PAMSPEC should either coordinate with SAIHM (and cite it) or restrict its scope so no reader could reasonably confuse the two.

### 2.4 FAF/FAFM (`draft-wolfe-faf-format-02`)

- Identifier and revision: `draft-wolfe-faf-format-02`; dated 2026-06-28, updated 2026-07-03; author James Wolfe (FAF Foundation); intended status Informational via Independent Submission stream; not endorsed by IETF.
- Scope: two YAML media types. `.faf` = "static project context — architecture, conventions, dependencies, goals — read once and treated as canonical." `.fafm` = "persistent agent memory — facts, preferences, accumulated knowledge — which mutates across sessions."
- Object model: memory units, profiles, namepoint identifier; core operations `etch`/`recall`/`forget`; retention policies.
- Discovery: `/.well-known/faf` registration requested (§8).
- **Direct implication for PAMSPEC.** FAF's context/memory split resembles PAMSPEC's separation of Compute Plane and Persistent State Plane. YAML vs JSON is a material serialization choice; the object-model overlap is thematic rather than structural, but the "memory-to-context promotion" concept anticipates part of PAMSPEC's lifecycle language and should be cited when PAMSPEC discusses lifecycle.

### 2.5 Portable Agent Memory (arXiv 2605.11032, preprint)

- Citation: Santhosh Kumar Ravindran, "Portable Agent Memory: A Protocol for Cryptographically-Verified Memory Transfer Across Heterogeneous AI Agents," arXiv:2605.11032, submitted 2026-05-10. Preprint; not peer-reviewed.
- Contributions: (1) five-component structured memory; (2) Merkle-DAG provenance with BLAKE3 content-addressing and Ed25519 root signing; (3) capability-based access control with scoped tokens; (4) injection-resistant rehydration adapting recalled content to heterogeneous target LLMs; (5) JSON-first serialization with optional CBOR compaction; (6) Python SDK with 54 passing tests demonstrating cross-model transfer among GPT-4, Claude, Gemini, Llama; (7) Apache-2.0.
- **Direct implication for PAMSPEC.** This preprint holds the space for "Merkle-DAG provenance for portable memory with capability-scoped disclosure." Any PAMSPEC provenance construct that resembles a signed derivation DAG must cite this work; PAMSPEC's Delegation Objects overlap conceptually with the paper's capability tokens.

### 2.6 W3C AI Agent Memory Interoperability Community Group

- Exact name: "AI Agent Memory Interoperability Community Group."
- Status: proposed 2026-05-18; call for participation 2026-06-03; chair Russell Jackson (SAIHM author). Supporters listed publicly.
- Stated 12-month deliverables: (i) use-case catalogue, (ii) baseline interoperability profile, (iii) conformance and test-vector pack (covering encoding, identity binding, envelope, erasure-receipt verification), (iv) regulatory crosswalk (GDPR Art. 17, EU AI Act 2024/1689, NIST AI RMF 1.0, ISO/IEC 27001:2022, ISO/IEC 42001:2023).
- Relationship to SAIHM: the CG normatively references `draft-saihm-memory-protocol` and commits it "will not develop a competing normative specification."
- **Framing rule reminder.** A W3C Community Group is not the W3C Recommendation track. CG output is not a W3C standard and does not carry Recommendation-track patent commitments.

### 2.7 MCP (Model Context Protocol, 2026-07-28 RC)

- Anthropic-originated open protocol; not an IETF or W3C work item. Repository `modelcontextprotocol/modelcontextprotocol`.
- Adjacent, not competing. MCP frames itself as the connection protocol between an AI client and external tools/resources. Memory, orchestration, and higher-level workflow are explicitly outside MCP.
- The 2026-07-28 RC introduces a stateless protocol core, Extensions, Tasks, MCP Apps, authorization hardening, and a formal deprecation policy. `tools/list` responses now carry `ttlMs` and `cacheScope`.
- **Implication for PAMSPEC.** PAMSPEC's `bindings/mcp/` directory is the correct posture: PAMSPEC provides the memory data model and event ledger; MCP provides the transport that a Compute-Plane agent uses to reach a memory service. The two are complementary. PAMSPEC should not restate anything MCP already normalizes.

### 2.8 Agent-identity landscape (context only)

Datatracker shows multiple active individual submissions on agent identity: `draft-singla-agent-identity-protocol-03`, `draft-aip-agent-identity-protocol-00`, `draft-larsson-aitlp-00`, `draft-sharif-agent-identity-framework-00`, `draft-drake-agent-identity-registry-00`. None is a WG document. PAMSPEC's Delegation Objects should reference this space rather than redefine identity.

## 3. Academic evidence matrix (R2-B)

### 3.1 Source-by-source table

| Source | Class | Method | Finding paraphrase | Limitation | Supports which PAMSPEC concept | Does NOT prove |
|---|---|---|---|---|---|---|
| Packer et al., "MemGPT: Towards LLMs as Operating Systems," arXiv:2310.08560; PhD extension in Packer, "Building Agentic Systems in an Era of Large Language Models," UC Berkeley EECS-2024-223, Dec 2024 | Preprint + dissertation | Systems | Virtual-context paging with a hierarchical memory tier lets agents operate beyond fixed context windows | Focuses on a runtime tier, not a portable data model | Persistent memory beyond context is a real problem | That any specific portable data model is universally required |
| Maharana et al., "Evaluating Very Long-Term Conversational Memory of LLM Agents (LoCoMo)," ACL 2024 | Peer-reviewed | Benchmark (~600 turns, up to 32 sessions, 200 QA/dialog) | LLMs lag humans on multi-session recall and temporal/causal reasoning; long context and RAG help but do not close the gap | Focused on dialog; no schema claims | Need for long-horizon memory, temporal metadata | Any specific event-ledger shape |
| Sumers, Yao, Narasimhan, Griffiths, "Cognitive Architectures for Language Agents (CoALA)," TMLR/arXiv 2309.02427 | Peer-reviewed (TMLR) | Framework / survey | Language agents benefit from explicit modular memory: working, episodic, semantic, procedural | Descriptive; does not prescribe wire format | Multi-type memory taxonomy | That the taxonomy is universal or that portable Working Memory is required |
| Chhikara et al. and follow-ups, LongMemEval | Preprint | Benchmark (500 questions over ~115k-token histories, five ability categories) | Retrieval + working-context designs vary widely; memory quality varies with extraction, temporal reasoning, updates, abstention | English chat only | Evaluation is essential; memory updates and knowledge revision are real workloads | That any specific revision operator is standardized |
| Gutiérrez et al., "HippoRAG: Neurobiologically Inspired Long-Term Memory for LLMs," NeurIPS 2024 | Peer-reviewed | Systems + retrieval evaluation | Personalized PageRank over a KG plus LLM entity linking improves multi-hop QA by up to ~20%, ~10–30× cheaper than iterative RAG | Retrieval architecture only; no interchange claim | Motivates first-class relational/graph memory | Portable format |
| Zhong et al., "MEMORYBANK: Enhancing Large Language Models with Long-Term Memory," AAAI 2024 | Peer-reviewed | Systems | Ebbinghaus-style forgetting curve applied to memory retention improves long-term dialog | Runtime construct | Motivates retention as a state dimension | Universality of a four-dimension state model |
| McClelland, McNaughton, O'Reilly, "Why there are complementary learning systems in the hippocampus and neocortex," Psychological Review 1995 | Peer-reviewed (foundational) | Theory | Complementary fast/slow learning; motivation for consolidation | Not about LLMs | Consolidation and multi-tier memory | Not a spec |
| Tulving, "Episodic and Semantic Memory," 1972 | Foundational chapter | Theory | Distinguishes episodic vs semantic memory | Cognitive, not computational | CoALA taxonomy inheritance | Not a spec |
| Ravindran, "Portable Agent Memory," arXiv:2605.11032 | Preprint | Systems + protocol | Merkle-DAG provenance + capability disclosure + injection-resistant rehydration + JSON-first serialization; Python SDK with 54 tests | Preprint; single implementation | Provenance and portable-memory concepts | Any specific event ledger or Embedding Space descriptor |
| "Is Agent Memory a Database? Rethinking Data Foundations for Long-Term AI Agent Memory," arXiv:2605.26252 | Preprint | Systems + formal | Frames long-term agent memory as a new data-management workload; proposes GEM: ingestion / revision / forgetting / retrieval under six correctness conditions | Preprint; no benchmarks yet | State-level operators (echoes PAMSPEC's event ledger + version model) | Universality of four state dimensions |
| "A Survey on the Security of Long-Term Memory in LLM Agents: Toward Mnemonic Sovereignty," arXiv:2604.16548 | Preprint (survey) | Literature synthesis | Long-term memory is a novel attack surface; poisoning persists across sessions | Preprint | Provenance and validation as safety features | Any specific validation state field |
| Chen et al., "AgentPoison" (2024) and Agent Security Bench (ASB) | Peer-reviewed / benchmark | Empirical attacks | >80% attack success at <0.1% poison rate; ASB reports ~84% average success across 400+ tools | Adversarial-only settings | Motivates provenance and pre-ingestion validation | That immutable versioning alone prevents poisoning |
| Hu et al., "Learning Backward-Compatible Embeddings," KDD 2022 (arXiv:2206.03040) | Peer-reviewed | Systems + ML | Learned alignment functions can keep new embeddings usable by consumers of old space | Requires training the alignment | Motivates Embedding Space identity + incompatible-space rejection | That declaring model id is sufficient |
| Moschella et al., "Relative Representations Enable Zero-Shot Latent-Space Communication," ICLR 2023 | Peer-reviewed | Representation learning | Anchor-based relative reps make representations comparable across model instances | Not a wire format | Reinforces that embedding-space identity matters | Standardized descriptor |
| Kusupati et al., "Matryoshka Representation Learning," NeurIPS 2022 | Peer-reviewed | ML | Nested-dimensional embeddings enable flexible truncation | Not portability | Embedding-space metadata design | A universal descriptor |
| W3C PROV-DM (Recommendation, 2013-04-30) and PROV-O | W3C Recommendation | Standard | Conceptual model for provenance: entities, agents, activities | Not agent-memory-specific | Provenance requirement grounding | That PROV alone captures agent-memory provenance |
| Model Cards (Mitchell et al., FAT* 2019); Datasheets for Datasets (Gebru et al., CACM 2021) | Peer-reviewed | Documentation frameworks | Structured metadata improves accountability | Model-level, not memory-level | Motivates provenance metadata | Any specific record shape |
| Fowler, "Event Sourcing" (industry pattern, 2005) | Non-peer-reviewed foundational essay | Pattern | Append-only event log + derived state is a proven persistence pattern | Not agent-memory-specific | Grounds Event Ledger design | That an Event Ledger must be universal for agents |

### 3.2 Principle-by-principle verdict

| PAMSPEC principle | Verdict | Notes |
|---|---|---|
| Four mandatory state dimensions (lifecycle + availability + retention + validation) as universal | Plausible but unproven | No academic source demonstrates that exactly these four dimensions are necessary and sufficient. LoCoMo and LongMemEval motivate at least lifecycle and retention; "Is Agent Memory a Database?" motivates revision (partly overlaps validation). Recommend positioning as "candidate universal set" pending empirical study. |
| Append-only Event Ledger as universally required | Partially supported | Event sourcing is a proven persistence pattern (Fowler); the GEM framework (arXiv:2605.26252) argues correctness lives in the state trajectory. But "universally required" is stronger than any cited source establishes. |
| Immutable version creation for every authoritative change | Partially supported | GEM's revision operator, PROV-DM's activity model, and memory-poisoning literature all motivate durable, attributable state changes. Immutability specifically is a design choice, not an empirical necessity. |
| Standard memory-type taxonomies (episodic/semantic/procedural/working) | Strongly supported (as taxonomy), weak (as portable-format claim) | CoALA + Tulving + McClelland ground the taxonomy. No source shows portability across vendors requires these categories to be encoded in the wire format. |
| Embedding Space descriptors as universally required | Partially supported | Backward-compatible-embeddings work (KDD 2022) and Relative Representations (ICLR 2023) show that embedding spaces are not interoperable by default. This justifies *declaring* an embedding-space identity. Whether that descriptor is universally required, or optional with graceful re-embedding, is a design choice. |
| Mandatory provenance across all implementations | Strongly supported (as principle) | PROV-DM, Model Cards, Datasheets, and the 2026 poisoning survey collectively establish provenance as necessary. What fields must be captured is unresolved. |
| Scope isolation as universally applicable | Plausible but unproven | Multi-tenant systems literature supports isolation; SAIHM and AIMEM both encode tenant/scope fields. No empirical study proves a single scope model dominates. |
| Delegation Objects as a memory (not authorization) concern | Contradicted (partly) | Delegation is typically framed as an identity/authorization concern; see the active agent-identity I-D landscape. PAMSPEC can *record* delegation events in memory, but promoting delegation semantics into the memory data model risks overlap with agent-identity work. |
| Subscribe operations as a memory (not runtime) concern | Plausible but unproven | Push notification of memory changes is a runtime protocol concern typically handled by MCP, message brokers, or webhooks. Keeping Subscribe as an extension profile is defensible; making it core is not evidenced. |
| Working Memory as a first-class portable type | Outside academic evidence | CoALA treats working memory as a runtime construct. No cited source argues working memory should be portable across vendors. Recommend keeping optional. |

## 4. IETF process and venue analysis (R2-C)

Each item is tagged **P** (procedural — you must do this to submit), **R** (recommended by IETF/RFC-Editor guidance), or **V** (voluntary PAMSPEC quality gate, not required by the IETF).

- **P — Internet-Draft definition.** Internet-Drafts are working documents; they "have no formal status, and are subject to change or removal at any time" (RFC 2026, §2.2).
- **P — Six-month expiration.** An Internet-Draft that has "remained unchanged in the Internet-Drafts directory for more than six months without being recommended by the IESG for publication as an RFC, is simply removed" (RFC 2026, §2.2).
- **P — Revision numbering.** First submission of a given draft name is `-00`; subsequent revisions increment by one (IETF Author Tools guidance at authors.ietf.org).
- **P — Individual submission vs WG document.** Individual submissions are posted by any author with a datatracker account; they are not IETF products. Working Group documents are adopted only after a WG call for adoption and become the WG's collective output.
- **P — IPR / contribution obligations.** BCP 78 (RFC 5378) covers contribution rights; BCP 79 (RFC 8179) covers IPR disclosure. All authors must accept these terms at submission.
- **P — Submission cutoffs.** The datatracker enforces a submission blackout for the days immediately surrounding IETF meeting weeks; check the current IETF meeting calendar before scheduling a `-00`.
- **P — Intended status options.** Informational, Experimental, Standards Track (further split into Proposed Standard and Internet Standard per RFC 6410), and Best Current Practice.
- **P — "Not endorsed by IETF" statement.** Individual submissions carry the standard boilerplate noting they are not the product of an IETF WG and do not represent IETF consensus. This wording is required and must not be paraphrased away in marketing.
- **R — Working Group adoption path.** An author may seek WG adoption by identifying a WG whose charter covers the topic, presenting the draft to the WG, and asking the chairs to call for adoption. There is no WG today for agent-memory data models specifically; the closest ecosystem venues are `agents@ietf.org` and related non-WG lists.
- **R — Independent Stream.** For self-contained specifications outside any WG's charter, the Independent Submissions Editor (RFC Editor stream, `rfc-editor.org/pubprocess/`) is the correct route for eventual RFC publication.
- **R — IETF vs IRTF.** IETF engineering; IRTF research. If the project's near-term posture is "we want empirical study and are still iterating on core abstractions," an IRTF Research Group (or presenting at an existing RG) is more honest than pushing for a WG.
- **R — Implementation experience for Proposed Standard.** RFC 7127: "Usually, neither implementation nor operational experience is required for the designation of a specification as a Proposed Standard," but the IESG may require it for specifications with significant operational impact, and implementation experience is a strong argument in favor.
- **R — Advancement to Internet Standard.** RFC 6410 requires "at least two independent interoperating implementations with widespread deployment and successful operational experience." This is a *later-stage* requirement, not a prerequisite for `-00` or for Proposed Standard.
- **V — PAMSPEC quality gates.** The project's own R1–R8 completion criterion, the requirement for a TypeScript reference implementation before promoting past `-00`, and any additional interop-testing gates PAMSPEC has adopted are *voluntary project standards*. They are not IETF process. They should be described as such internally.

Critically, none of the following are IETF rules: "you must have a TypeScript reference implementation before submitting `-00`"; "you must complete N research reviews before `-00`"; "your `-00` needs peer review before submission." These are legitimate voluntary quality gates; they must not be described as IETF requirements.

## 5. Claims register

| Proposed PAMSPEC Claim | Evidence | Safe Wording | Unsafe Wording |
|---|---|---|---|
| PAMSPEC is a novel data model for persistent agent memory | AIMEM, SAIHM, FAF, Portable Agent Memory all exist in adjacent space | "PAMSPEC is a candidate specification that refines and combines ideas explored by AIMEM (draft-vu-aimem-bundle), SAIHM (draft-saihm-memory-protocol), FAF/FAFM, and Portable Agent Memory (arXiv:2605.11032), and adds an explicit atomic version+event commit model and profile-based conformance." | "PAMSPEC is the first data model for persistent agent memory." |
| Portable memory across vendors is a real need | LoCoMo (ACL 2024), MemGPT thesis, LongMemEval, Portable Agent Memory preprint | "Multiple peer-reviewed benchmarks show that memory beyond a single session materially affects agent quality." | "Vendor lock-in is universally recognized as the top agent problem." |
| Embedding-space incompatibility is a real problem | KDD 2022 backward-compatible embeddings; ICLR 2023 relative representations | "Embeddings from different models are not directly comparable without alignment; declaring an embedding space identity lets consumers detect incompatible-space vectors." | "PAMSPEC solves cross-model embedding transfer." |
| Provenance is required for trustworthy memory | W3C PROV-DM Recommendation; Model Cards; Datasheets; 2026 poisoning survey | "Structured provenance is a recognized requirement for trustworthy AI systems; PAMSPEC records producer, timestamp, and event lineage in the Event Ledger." | "PAMSPEC provides cryptographic guarantees against memory poisoning." (only true if such guarantees are formally specified) |
| Long-term memory is necessary for capable agents | MemGPT thesis; LoCoMo; LongMemEval; HippoRAG | "Peer-reviewed evaluations demonstrate that agents benefit from memory beyond a single context window." | "Working memory must be portable across vendors." |
| Append-only Event Ledger is required | Fowler event-sourcing pattern; GEM (arXiv:2605.26252) | "PAMSPEC adopts an append-only event ledger, a persistence pattern with a long track record in transactional systems and recently proposed for agent memory (arXiv:2605.26252)." | "Any conforming agent-memory system must implement an append-only ledger." |
| PAMSPEC hardens against memory poisoning | 2026 security survey; AgentPoison; ASB | "Explicit provenance and versioning are necessary but not sufficient defenses against memory poisoning; PAMSPEC provides the recording surface." | "PAMSPEC prevents memory-poisoning attacks." |
| PAMSPEC and MCP relationship | MCP 2026-07-28 RC scope statement | "PAMSPEC defines the memory data model and event ledger; MCP defines the transport by which a Compute-Plane agent reaches a memory service. The two are complementary." | "PAMSPEC extends MCP." (unless explicitly registered as an MCP extension) |
| Standards status | RFC 2026; IETF process page | "PAMSPEC is an individual contribution. If posted as `draft-<lastname>-pamspec-00`, it will be an Internet-Draft, not an IETF standard, and will expire six months after posting unless updated." | "PAMSPEC is an IETF draft standard." |
| Implementation evidence | Repository shows Python reference implementation and conformance harness | "A Python reference implementation and portable conformance harness exist at the pinned commit." | "PAMSPEC has multiple independent interoperable implementations." (not yet true) |

## 6. AIMEM disposition

**Recommendation: coordinate but remain separate; do NOT create a PAMSPEC bundle at this time.**

Justification. AIMEM (`draft-vu-aimem-bundle-00`) already defines memory-bundle exchange semantics, including envelope with `format`/`version`/`producer`/`tenant_id`/`scope`, ChunkRecord + edges + entities, URN identifier scheme, embedding metadata with declared model identifier, SHA-256 integrity and optional COSE_Sign1, DNA-class chunk invariants, and Producer/Consumer/Bidirectional conformance levels. A second bundle format that duplicates these choices cannot honestly be called novel and increases fragmentation.

Options, in order of decreasing preference:

1. **Adopt AIMEM as PAMSPEC's exchange binding.** Reference `draft-vu-aimem-bundle` normatively for envelope, chunk record, and URN identifier. Focus PAMSPEC's own contribution on the parts AIMEM does not define: atomic version+event commit protocol, Event Ledger semantics, Embedding Space descriptor beyond `model_id`, and conformance profiles.
2. **Profile AIMEM.** Publish a PAMSPEC profile that pins AIMEM options (which conformance level, which optional fields, which security posture is required) and adds PAMSPEC-specific extensions in a namespaced way.
3. **Coordinate but remain separate.** Cite AIMEM explicitly in `-00` and enumerate divergences with justification. Acceptable only if there is a specific technical reason PAMSPEC cannot use the AIMEM envelope.
4. **Define a different format.** Discouraged unless a technical incompatibility is documented; would require an explicit prior-art section refuting the "duplicative" reading.

Under all four options, PAMSPEC's `-00` must include a "Relationship to prior art" section naming AIMEM, SAIHM, FAF/FAFM, and Portable Agent Memory.

## 7. Submission timing recommendation

Recommend that the first `-00` be posted **after R1–R8 complete**, and only after the "Relationship to prior art" section, the Claims Register wording in §5 of this document, and an AIMEM disposition are integrated into the draft. The pinned repository at commit `45c42db6` shows a Python reference implementation, a portable conformance harness, 27 ADRs, and JSON schemas; that is enough implementation evidence to satisfy RFC 7127's language on Proposed Standard *if* PAMSPEC eventually targets Proposed Standard, and it exceeds what is required to post an Informational or Experimental `-00`.

Explicit clarification per the framing rules: a TypeScript reference implementation is **supporting evidence for later revisions**, not a prerequisite for `-00`. RFC 7127 states "Usually, neither implementation nor operational experience is required for the designation of a specification as a Proposed Standard"; RFC 6410's two-independent-implementation rule applies to advancement to Internet Standard, not to initial posting. Requiring TypeScript before `-00` is a legitimate *voluntary* PAMSPEC quality gate; it must be described as such, not as an IETF requirement.

A defensible near-term plan:

- Complete R1–R8.
- Integrate the Relationship-to-prior-art section and Claims Register wording.
- Post `draft-<lastname>-pamspec-00` with Intended Status Informational or Experimental.
- Announce on relevant non-WG lists (e.g., `agents@ietf.org` if that list is active at the time, plus the W3C AI Agent Memory Interoperability CG if PAMSPEC decides to engage there).
- Do not seek WG adoption until at least one independent implementation exists and a WG whose charter covers agent-memory data models has been identified or proposed.

## 8. Open questions

1. Is `agents@ietf.org` or an equivalent non-WG list the correct home for early PAMSPEC discussion in July 2026, and does an IRTF Research Group covering agent memory exist or is one being proposed?
2. Would AIMEM's author (Vu Duc Minh) accept PAMSPEC profiling AIMEM as its exchange binding, and are the conformance levels in AIMEM §4 compatible with PAMSPEC's profile system?
3. What is the current status of the "agent memory" IANA media-type registration space, and are AIMEM (`application/aimem-bundle+json` or similar) and PAMSPEC candidates likely to collide?
4. Does the W3C AI Agent Memory Interoperability CG's baseline interoperability profile intend to constrain the wire format beyond SAIHM, and if so, does PAMSPEC belong inside or beside that profile?
5. Is there peer-reviewed evidence (not preprint) beyond CoALA and LoCoMo that supports mandatory Working Memory portability, or does all available evidence treat working memory as a runtime construct?
6. Do any of the active agent-identity Internet-Drafts (`draft-singla-agent-identity-protocol-03`, `draft-aip-agent-identity-protocol-00`, `draft-larsson-aitlp-00`, `draft-sharif-agent-identity-framework-00`, `draft-drake-agent-identity-registry-00`) already define delegation semantics that PAMSPEC's Delegation Objects would duplicate?
7. Is the "Is Agent Memory a Database?" GEM framework (arXiv:2605.26252) headed toward peer-reviewed publication at CIDR or SIGMOD, and if so, should PAMSPEC's Event Ledger vocabulary align with GEM's four operators (ingestion, revision, forgetting, retrieval)?
8. What is the current state of empirical evidence on the effectiveness of provenance metadata (as opposed to filtering or sandboxing) as a defense against the "Poison Once, Exploit Forever" class of attacks?

## Sources

**R2-A (Standards)**

- draft-vu-aimem-bundle-00, "AIMEM Memory Interchange Bundle Format," Vu Duc Minh, 2026-06-14. https://datatracker.ietf.org/doc/draft-vu-aimem-bundle/ (accessed 2026-07-18)
- draft-saihm-memory-protocol-01, "Sovereign AI Horizontal Memory Protocol," Russell Jackson, 2026-05-27. https://datatracker.ietf.org/doc/draft-saihm-memory-protocol/ (accessed 2026-07-18)
- draft-wolfe-faf-format-02, "Foundation Agent Format / FAFM," James Wolfe, 2026-06-28 (updated 2026-07-03). https://datatracker.ietf.org/doc/draft-wolfe-faf-format/ (accessed 2026-07-18)
- W3C AI Agent Memory Interoperability Community Group (proposed 2026-05-18). https://www.w3.org/community/ai-agent-memory-interop/ ; https://www.w3.org/groups/cg/ai-agent-memory-interop/ (accessed 2026-07-18)
- Model Context Protocol, 2026-07-28 Release Candidate. https://modelcontextprotocol.io/specification/ ; https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/ (accessed 2026-07-18)
- Agent-identity landscape (context): draft-singla-agent-identity-protocol-03; draft-aip-agent-identity-protocol-00; draft-larsson-aitlp-00; draft-sharif-agent-identity-framework-00; draft-drake-agent-identity-registry-00. All at https://datatracker.ietf.org/ (accessed 2026-07-18)

**R2-B (Academic)**

- Packer, C. et al., "MemGPT: Towards LLMs as Operating Systems," arXiv:2310.08560 (preprint, 2023).
- Packer, C., "Building Agentic Systems in an Era of Large Language Models," UC Berkeley EECS-2024-223, Dec 2024 (dissertation). https://www2.eecs.berkeley.edu/Pubs/TechRpts/2024/EECS-2024-223.html
- Maharana, A. et al., "Evaluating Very Long-Term Conversational Memory of LLM Agents (LoCoMo)," ACL 2024 (peer-reviewed). https://aclanthology.org/2024.acl-long.747/
- Sumers, T. et al., "Cognitive Architectures for Language Agents (CoALA)," arXiv:2309.02427 (TMLR, peer-reviewed).
- Chhikara et al., LongMemEval (benchmark, preprint).
- Gutiérrez et al., "HippoRAG: Neurobiologically Inspired Long-Term Memory for LLMs," NeurIPS 2024 (peer-reviewed). https://neurips.cc/virtual/2024/poster/94043
- Zhong, W. et al., "MEMORYBANK," AAAI 2024 (peer-reviewed).
- McClelland, McNaughton, O'Reilly, "Why there are complementary learning systems...," Psychological Review, 1995.
- Tulving, E., "Episodic and Semantic Memory," 1972 (foundational chapter).
- Ravindran, S. K., "Portable Agent Memory: A Protocol for Cryptographically-Verified Memory Transfer Across Heterogeneous AI Agents," arXiv:2605.11032, 2026-05-10 (preprint). https://arxiv.org/abs/2605.11032
- "Is Agent Memory a Database? Rethinking Data Foundations for Long-Term AI Agent Memory," arXiv:2605.26252 (preprint). https://arxiv.org/abs/2605.26252
- "A Survey on the Security of Long-Term Memory in LLM Agents: Toward Mnemonic Sovereignty," arXiv:2604.16548 (preprint).
- AgentPoison (2024, peer-reviewed); Agent Security Bench (ASB) (benchmark).
- Hu, W. et al., "Learning Backward-Compatible Embeddings," KDD 2022 (peer-reviewed). arXiv:2206.03040
- Moschella et al., "Relative Representations Enable Zero-Shot Latent-Space Communication," ICLR 2023 (peer-reviewed).
- Kusupati et al., "Matryoshka Representation Learning," NeurIPS 2022 (peer-reviewed).
- W3C PROV-DM (Recommendation, 2013-04-30). https://www.w3.org/TR/prov-dm/
- Mitchell, M. et al., "Model Cards for Model Reporting," FAT* 2019 (peer-reviewed).
- Gebru, T. et al., "Datasheets for Datasets," CACM 2021 (peer-reviewed).
- Fowler, M., "Event Sourcing" (2005, industry foundational essay).

**R2-C (IETF process)**

- RFC 2026 (BCP 9), "The Internet Standards Process — Revision 3." https://www.rfc-editor.org/info/rfc2026
- RFC 7127, "Characterization of Proposed Standards." https://www.rfc-editor.org/info/rfc7127
- RFC 6410, "Reducing the Standards Track to Two Maturity Levels." https://www.rfc-editor.org/info/rfc6410
- BCP 78 (RFC 5378), "Rights Contributors Provide to the IETF Trust." https://www.rfc-editor.org/info/rfc5378
- BCP 79 (RFC 8179), "Intellectual Property Rights in IETF Technology." https://www.rfc-editor.org/info/rfc8179
- IETF Standards Process overview. https://www.ietf.org/standards/process/
- Internet-Draft Author Resources. https://authors.ietf.org/
- IETF Datatracker Submission Tool. https://datatracker.ietf.org/submit/
- RFC Editor Publication Process (Independent Stream). https://www.rfc-editor.org/pubprocess/

**Repository under review**

- Persistent-Agentic-Memory-Architecture, pinned commit `45c42db6069212b5237d577b99fa7c7b03840d85`, main tip 2026-07-17. https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture
