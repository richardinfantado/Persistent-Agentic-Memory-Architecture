# Persistent Agentic Memory Architecture Specification (PAMSPEC)

PAMSPEC is the project shorthand for the **Persistent Agentic Memory Architecture Specification**. The architecture defined by the project is the **Persistent Agentic Memory Architecture**.

Internet-Draft (working title): **Architecture and Data Model for Persistent Memory in Agentic Systems**

**IETF submission status: not submitted.** No revision of this document has been submitted to or posted by the IETF Datatracker. Active development lives at the docname `draft-infantado-agent-memory-architecture-latest`. If and when a first individual Internet-Draft is posted, it will be `-00`. See [`REVIEW-CANDIDATE-ARCHIVE.md`](REVIEW-CANDIDATE-ARCHIVE.md) for the internal review-candidate archive and [`pamspec-version.json`](pamspec-version.json) for machine-readable status.

PAMSPEC defines a provider-independent architecture and data model for persistent, machine-readable memory in agentic systems. It separates transient agent computation from authoritative persistent state so memory can be audited, exported, reviewed, and implemented independently of any model provider, runtime, framework, storage engine, vector database, or transport protocol.

## Foundational Principles

1. Compute Plane and Persistent State Plane separation
2. Memory Scope and Workspace isolation
3. Typed and versioned Memory Objects
4. Append-only Event Ledger
5. Isolated Derived Indexes and Embedding Spaces

## Conformance Profiles

| Profile | Purpose |
| --- | --- |
| **PAMSPEC-Lite** | Minimal on-ramp for prototypes and single-developer agents |
| **PAMSPEC-Core** | Full envelope, four state dimensions, error envelope |
| **PAMSPEC-Versioning** | Expected-version concurrency + `version_conflict` |
| **PAMSPEC-Ledger** | Append-only Event Ledger with atomic version+event commit |
| **PAMSPEC-Structured-Query** | Scope-bound filters, temporal, snapshot-repeatable |
| **PAMSPEC-Semantic-Query** | Embedding Space identity, incompatible-space rejection |
| **PAMSPEC-Relationship** | Versioned Relationship Objects, cross-scope policy |
| **PAMSPEC-Protocol-Binding** | Preserves semantics across transports |
| **PAMSPEC-Evaluation** | Sealed snapshots, deterministic clock/RNG, run-id provenance |

## Repository Contents

- Editable Internet-Draft source (docname `-latest`): [`draft-infantado-agent-memory-architecture.md`](draft-infantado-agent-memory-architecture.md)
- Internal review-candidate archive (never submitted to IETF): [`review-candidates/`](review-candidates/) — see [`REVIEW-CANDIDATE-ARCHIVE.md`](REVIEW-CANDIDATE-ARCHIVE.md)
- JSON Schemas (16): [`schemas/0.1-draft/`](schemas/0.1-draft/)
- Examples: [`examples/`](examples/)
- Test vectors (positive + negative): [`test-vectors/`](test-vectors/)
- Architecture decisions (27 ADRs): [`decisions/`](decisions/)
- Reference implementation (Python, PAMSPEC-Lite + Delegation + Subscribe): [`implementations/reference-python/`](implementations/reference-python/)
- MCP binding profile + Python stub server: [`bindings/mcp/`](bindings/mcp/)
- **Portable conformance harness** (adapter-based, implementation-agnostic): [`conformance/`](conformance/)
- Implementation report for the reference impl: [`reviews/implementation-report-reference-python.md`](reviews/implementation-report-reference-python.md)
- External review guides: [`reviews/`](reviews/)
- Consistency matrix (cross-file review artifact): [`CONSISTENCY-MATRIX.md`](CONSISTENCY-MATRIX.md)
- Version manifest: [`pamspec-version.json`](pamspec-version.json)
- Contributors: [`CONTRIBUTORS.md`](CONTRIBUTORS.md)
- Pre-publication checklist: [`PREPUBLICATION-CHECKLIST.md`](PREPUBLICATION-CHECKLIST.md)

## Quick start (adopter, 5 minutes)

```bash
git clone https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture
cd Persistent-Agentic-Memory-Architecture
python -m pip install -r requirements.txt
python scripts/validate_test_vectors.py
PYTHONPATH=implementations/reference-python python -m pytest implementations/reference-python/tests
```

The reference implementation is < 800 LOC, SQLite-backed, and satisfies PAMSPEC-Lite plus Delegation and Subscribe. See [`implementations/reference-python/README.md`](implementations/reference-python/README.md).

## Proving conformance of any implementation

```bash
PYTHONPATH=.:implementations/reference-python python -m pytest conformance/tests
```

To claim conformance from a different implementation, write a
~100-line adapter under `conformance/adapters/<yourimpl>.py`
satisfying `conformance.harness.Adapter`, then a pytest file under
`conformance/tests/` that runs the same suite against your adapter.
The harness ships 25 behavioral cases across three profiles
(PAMSPEC-Lite, PAMSPEC-Delegation, PAMSPEC-Subscribe) and prints a
report you can attach to an implementation report under
[`reviews/`](reviews/).

## Architecture Tracks

The core architecture defines memory semantics independently of bindings. An internal enhancement cycle added a reference MCP binding profile ([`bindings/mcp/`](bindings/mcp/)) and a stub Python MCP server that wraps the reference implementation. HTTP, embedded libraries, gRPC, and message buses are future bindings; none is mandatory for the core architecture. All of this remains subject to the current scope-narrowing pass before any IETF submission.

## Licensing

Specification text and documentation are licensed under CC BY 4.0 as described in [`LICENSE-DOCUMENTATION.md`](LICENSE-DOCUMENTATION.md). Technical repository artifacts, including schemas, examples, test vectors, reference implementations, validation scripts, Makefile, and workflows, are licensed under Apache License 2.0 as described in [`LICENSE-APACHE-2.0`](LICENSE-APACHE-2.0). Internet-Draft submissions are also subject to applicable IETF contribution, copyright, and legal provisions.

## Building

```sh
gem install kramdown-rfc
python -m pip install -r requirements.txt
make draft
make validate
```

Active development builds use `draft-infantado-agent-memory-architecture-latest` metadata and write temporary outputs under `build/`. No numbered Datatracker revision has been produced or posted. If a first IETF submission is prepared in the future, it will be `-00`; the tooling that would generate it is out of scope for this working copy — see [`REVIEW-CANDIDATE-ARCHIVE.md`](REVIEW-CANDIDATE-ARCHIVE.md) for the process description.

## Review

Critical review, interoperability feedback, security analysis, privacy analysis, and independent implementation reports are welcome. Please use public issues, pull requests, written architecture decisions, and the review guides in [`reviews/`](reviews/). The [`reviews/implementation-report-template.md`](reviews/implementation-report-template.md) is the template for submitting an implementation report against any conformance profile.

## Contributors

Richard M. Infantado is the primary author and specification editor. Robert Leroux is acknowledged as a project contributor. Contributor listing is separate from formal Internet-Draft authorship.
