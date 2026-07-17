# Decision: tool_invocation and tool_result as standard object types

## Status

Accepted for `-01` enhancement cycle.

## Date

2026-07-17

## Context

Agent tool calls carry causal weight: a decision is defensible or not
depending on which tool result it was informed by, and a tool result
containing PII must be redactable independently from the decisions
that referenced it. Today, most frameworks stash tool calls in a
session transcript or an application-specific table.

## Problem

Without first-class memory types for tool invocation and result:

- Tool call history is not versioned, so retries and re-runs are
  ambiguous.
- Tool results lack provenance, so audit questions ("why did the
  agent think X?") are answered by log grepping instead of memory
  query.
- Redaction of a sensitive tool result requires ad-hoc mechanisms
  outside the memory model.
- Cost and latency are logged in one place, memory in another,
  making per-decision accounting hard.

## Proposed Decision

Add `tool_invocation` and `tool_result` to the standard object type
enum. Publish canonical content schemas
(`tool-invocation-content.schema.json`, `tool-result-content.schema.json`)
and provide test vectors. Relationship Objects link tool_result
`produced_by` tool_invocation and decision/claim `informed_by`
tool_result.

## Alternatives Considered

- Keep tool calls as an application concern: rejected because it
  fragments audit and undercuts the interoperability goal.
- Model as an extension type only: rejected because tool invocation
  is universal enough to justify a standard type; extension types
  add ceremony (`schema_id` required) that is friction here.
- Merge invocation and result into one object: rejected because they
  have different actors (requester vs tool), different lifetimes
  (invocation is authored on request, result on completion), and
  different redaction profiles (results often contain the sensitive
  payload).

## Consequences

- Agent frameworks can persist their tool loop through a standard
  memory contract.
- Cost/latency evolves naturally on `tool_result` and via P5
  (ledger cost fields).
- Existing implementations that store tool calls in their own tables
  can map to these types at the export boundary.

## Interoperability Impact

Cross-framework tool history becomes portable. An OpenAI Agents SDK
export and a LangGraph checkpoint can both round-trip tool calls
through PAMSPEC.

## Security Impact

Tool inputs and outputs are common vectors for prompt injection.
Modeling them as memory with `validation_state` allows implementations
to keep untrusted tool output out of the default retrieval path until
reviewed.

## Privacy Impact

Tool results are frequently the payload with PII or regulated data.
Making them first-class objects with independent lifecycle,
availability, and retention means erasure and redaction work as
designed.

## Unresolved Questions

- Should tool arguments and result payloads support content-addressable
  references to `artifact` objects for large payloads?
- Should the `outcome` enum grow (e.g., `rate_limited`)?

## References

- `schemas/0.1-draft/tool-invocation-content.schema.json`
- `schemas/0.1-draft/tool-result-content.schema.json`
- `test-vectors/valid/tool-invocation.json`
- `test-vectors/valid/tool-result.json`
