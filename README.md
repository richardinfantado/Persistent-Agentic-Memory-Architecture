# Persistent Agentic Memory Architecture Specification (PAMSPEC)

PAMSPEC is the project shorthand for the **Persistent Agentic Memory Architecture Specification**. The architecture defined by the project is the **Persistent Agentic Memory Architecture**.

Internet-Draft: **Architecture and Data Model for Persistent Memory in Agentic Systems**

Draft status: initial `-00` individual contribution. This repository is not an official RFC, is not an adopted IETF working-group document, and is not an IETF standard.

PAMSPEC defines a provider-independent architecture and data model for persistent, machine-readable memory in agentic systems. It separates transient agent computation from authoritative persistent state so memory can be audited, exported, reviewed, and implemented independently of any model provider, runtime, framework, storage engine, vector database, or transport protocol.

## Foundational Principles

1. Compute Plane and Persistent State Plane separation
2. Memory Scope and Workspace isolation
3. Typed and versioned Memory Objects
4. Append-only Event Ledger
5. Isolated Derived Indexes and Embedding Spaces

## Repository Contents

- Editable Internet-Draft source: [`draft-infantado-agent-memory-architecture.md`](draft-infantado-agent-memory-architecture.md)
- Generated RFCXML: [`draft-infantado-agent-memory-architecture-00.xml`](draft-infantado-agent-memory-architecture-00.xml)
- Generated text: [`draft-infantado-agent-memory-architecture-00.txt`](draft-infantado-agent-memory-architecture-00.txt)
- Generated HTML: [`draft-infantado-agent-memory-architecture-00.html`](draft-infantado-agent-memory-architecture-00.html)
- Review schemas: [`schemas/`](schemas/)
- Examples: [`examples/`](examples/)
- Test vectors: [`test-vectors/`](test-vectors/)
- Architecture decisions: [`decisions/`](decisions/)
- External review package: [`reviews/`](reviews/)
- Contributors: [`CONTRIBUTORS.md`](CONTRIBUTORS.md)
- Pre-publication checklist: [`PREPUBLICATION-CHECKLIST.md`](PREPUBLICATION-CHECKLIST.md)

## Architecture Tracks

The core architecture defines memory semantics independently of bindings. Later interoperability tracks may define protocol bindings, export profiles, conformance profiles, implementation reports, and test vectors. MCP, HTTP, embedded libraries, gRPC, and message buses may be future bindings, but none is mandatory for the core architecture.

## Licensing

Specification text and documentation are licensed under CC BY 4.0 as described in [`LICENSE-DOCUMENTATION.md`](LICENSE-DOCUMENTATION.md). Technical repository artifacts, including schemas, examples, test vectors, validation scripts, Makefile, and workflows, are licensed under Apache License 2.0 as described in [`LICENSE-APACHE-2.0`](LICENSE-APACHE-2.0). Internet-Draft submissions are also subject to applicable IETF contribution, copyright, and legal provisions.

## Building

```sh
gem install kramdown-rfc
python -m pip install -r requirements.txt
make draft
make validate
```

Active development builds use `draft-infantado-agent-memory-architecture-latest` metadata and write temporary outputs under `build/`. The committed `-00` XML, TXT, and HTML files are frozen baseline artifacts. To intentionally generate a numbered revision, run:

```sh
make release REV=01
```

The numbered release is written under `release/01/` for review before any artifact is committed.

## Review

Critical review, interoperability feedback, security analysis, privacy analysis, and independent implementation reports are welcome. Please use public issues, pull requests, written architecture decisions, and the review guides in [`reviews/`](reviews/).

## Contributors

Richard M. Infantado is the primary author and specification editor. Robert Leroux is acknowledged as a project contributor. Contributor listing is separate from formal Internet-Draft authorship.
