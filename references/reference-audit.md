# Reference Audit

This audit records references retained for `draft-infantado-agent-memory-architecture-00`. Verification means the citation was checked against a primary or official source during preparation of the PAMSPEC -00 external review candidate.

## Normative References

| Key | Exact title | Author/editor | Publisher | Date | URL or identifier | Section using reference | Reason | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RFC2119 | Key words for use in RFCs to Indicate Requirement Levels | S. Bradner | RFC Editor / IETF | March 1997 | RFC 2119 | Section 2 | Defines requirements terminology | Verified primary RFC reference |
| RFC8174 | Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words | B. Leiba | RFC Editor / IETF | May 2017 | RFC 8174 | Section 2 | Defines uppercase interpretation with RFC 2119 | Verified primary RFC reference |

Normative references are intentionally limited to BCP 14 terminology because the core architecture remains transport-neutral and storage-neutral. JSON, URI, timestamp, JSON Schema, provenance, and event-sourcing material are informative in this revision unless a future conformance profile makes them required.

## Informative References

| Key | Exact title | Author/editor | Publisher | Date | URL or identifier | Section using reference | Reason | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RFC3986 | Uniform Resource Identifier (URI): Generic Syntax | T. Berners-Lee, R. Fielding, L. Masinter | RFC Editor / IETF | January 2005 | RFC 3986 | References, object identity discussion | URI background for identifiers | Verified primary RFC reference |
| RFC8141 | Uniform Resource Names (URNs) | P. Saint-Andre, J. Klensin | RFC Editor / IETF | April 2017 | RFC 8141 | References, examples using URN-like identifiers | URN background only | Verified primary RFC reference |
| RFC3339 | Date and Time on the Internet: Timestamps | G. Klyne, C. Newman | RFC Editor / IETF | July 2002 | RFC 3339 | References, schema timestamp formats | Timestamp background for examples and schemas | Verified primary RFC reference |
| RFC8259 | The JavaScript Object Notation (JSON) Data Interchange Format | T. Bray | RFC Editor / IETF | December 2017 | RFC 8259 | Schemas and examples | JSON data format background | Verified primary RFC reference |
| RFC6902 | JavaScript Object Notation (JSON) Patch | P. Bryan, M. Nottingham | RFC Editor / IETF | April 2013 | RFC 6902 | Operation model background | Candidate update semantics background only | Verified primary RFC reference |
| RFC9110 | HTTP Semantics | R. Fielding, M. Nottingham, J. Reschke | RFC Editor / IETF | June 2022 | RFC 9110 | Protocol binding considerations | Future HTTP binding background | Verified primary RFC reference |
| RFC9562 | Universally Unique IDentifiers (UUIDs) | K. Davis, B. Peabody, P. Leach | RFC Editor / IETF | May 2024 | RFC 9562 | Object identity discussion | UUID background only | Verified primary RFC reference |
| JSON-SCHEMA | JSON Schema: A Media Type for Describing JSON Documents | A. Wright, H. Andrews, B. Hutton | JSON Schema project | 2022 | https://json-schema.org/draft/2020-12/json-schema-core.html | Schemas and test vectors | Candidate schema validation | Verified official specification |
| PROV-DM | PROV-DM: The PROV Data Model | L. Moreau, P. Missier | W3C | 2013 | https://www.w3.org/TR/prov-dm/ | Provenance and related work | Provenance vocabulary alignment | Verified W3C recommendation |
| OPENAI-AGENTS-SESSIONS | Sessions - OpenAI Agents SDK | OpenAI | OpenAI | 2025 | https://openai.github.io/openai-agents-python/sessions/ | Related work | Session persistence comparison | Verified official OpenAI documentation |
| OPENAI-CONVERSATION-STATE | Conversation state - OpenAI API documentation | OpenAI | OpenAI | 2025 | https://platform.openai.com/docs/guides/conversation-state | Related work | Provider conversation-state comparison | Verified official OpenAI documentation |
| ANTHROPIC-MULTIAGENT | How we built our multi-agent research system | Anthropic | Anthropic | 2025 | https://www.anthropic.com/engineering/built-multi-agent-research-system | Related work | Multi-agent context architecture comparison | Verified official Anthropic engineering publication |
| LANGGRAPH-MEMORY | Memory - LangGraph documentation | LangChain | LangChain | 2025 | https://langchain-ai.github.io/langgraph/concepts/memory/ | Related work | Framework memory store comparison | Verified official LangGraph documentation |
| LETTA-MEMORY | Memory Blocks - Letta documentation | Letta | Letta | 2025 | https://docs.letta.com/guides/agents/memory | Related work | Stateful-agent memory comparison | Verified official Letta documentation |
| MEMGPT-PAPER | MemGPT: Towards LLMs as Operating Systems | C. Packer, V. Fang, S. G. Patil, K. Lin, S. Wooders, J. E. Gonzalez | arXiv | 2023 | https://arxiv.org/abs/2310.08560 | Related work | Stateful memory research background | Verified arXiv primary paper |
| MEM0-DOCS | Mem0 Documentation | Mem0 | Mem0 | 2025 | https://docs.mem0.ai/ | Related work | Extraction-oriented memory behavior comparison | Verified official Mem0 documentation |
| FOWLER-EVENT-SOURCING | Event Sourcing | M. Fowler | martinfowler.com | 2005 | https://martinfowler.com/eaaDev/EventSourcing.html | Event Ledger and related work | Event sourcing background | Verified author-hosted source |
| AGENT-COMMUNICATION-GATEWAY | Agent Communication Gateway for Semantic Routing and Working Memory | Xiaohui Xie, Zian Wang, Tianshuo Hu, Yong Cui | IETF Internet-Draft | 2026 | `draft-agent-gw-01`, Work in Progress; https://datatracker.ietf.org/doc/draft-agent-gw/ | Appendix E | Distinguishes communication, semantic routing, protocol adaptation, capability discovery, and working context from persistent memory | Verified canonical IETF Datatracker record |

## Not Cited Because Primary Verification Was Unavailable

- Kumiho: no authoritative primary source sufficient to verify the requested architecture claims was identified during this pass. It is not cited.
- MemoriesDB: no authoritative primary source sufficient to verify the requested architecture claims was identified during this pass. It is not cited.
- Additional long-term memory, temporal memory, memory poisoning, and semantic retrieval reproducibility research remains candidate material for future revisions.

## Candidate Removals

No unverified reference is retained in the Internet-Draft bibliography. Future revisions should remove unused references if they no longer appear in the generated reference section.
