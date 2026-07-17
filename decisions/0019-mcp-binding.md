# Decision: PAMSPEC-over-MCP binding profile

## Status

Accepted for `-01` enhancement cycle.

## Date

2026-07-17

## Context

MCP is emerging as the de facto agent-plugin protocol across Claude
Desktop, Cursor, Claude Code, Zed, and multiple IDE integrations. A
PAMSPEC implementation that speaks MCP becomes immediately usable by
that ecosystem without per-client integration work.

## Problem

Without a canonical MCP mapping, each PAMSPEC implementation would
invent its own tool names, argument shapes, and error conventions,
defeating the interoperability goal.

## Proposed Decision

Publish `bindings/mcp/` containing:

1. A normative README defining the mapping from PAMSPEC operations
   to MCP tools (`pamspec.<operation>`) and PAMSPEC objects to MCP
   resources (`pamspec://scope/{scope_id}/...`).
2. A `tools.json` descriptor set that a conforming MCP server can
   register directly.
3. Rules that preserve PAMSPEC error envelopes end-to-end without
   collapsing them into MCP protocol errors.

The binding is one binding among many; the core spec remains
transport-neutral.

## Alternatives Considered

- Publish nothing; let implementations improvise: rejected because
  ad-hoc mappings will fragment the MCP surface and defeat MCP's
  main benefit (client-side reuse).
- Publish an MCP mapping as the *primary* binding: rejected because
  PAMSPEC-Core explicitly refuses transport lock-in.
- Wait for a mature MCP standards body: rejected because the
  ecosystem is moving now and a reference mapping helps convergence.

## Consequences

- MCP-aware clients (Claude Desktop, Cursor, Claude Code) can use
  any conforming PAMSPEC server without code changes.
- Server implementers get a checklist rather than a design exercise.
- The binding must be revisited when the MCP spec itself revises.

## Interoperability Impact

Directly extends PAMSPEC's addressable ecosystem to every MCP client.

## Security Impact

Scope enforcement, cross-scope authorization, and denial semantics
are preserved end-to-end. Binding servers MUST NOT expose protected
object existence through resource-URI errors.

## Privacy Impact

Redaction and deletion semantics carry through unchanged; the
binding cannot weaken PAMSPEC privacy guarantees.

## Unresolved Questions

- Whether MCP resource pagination cursors should be opaque or use
  a documented shape.
- How MCP server-side actor identity should be captured when MCP
  itself lacks a strong actor concept.

## References

- `bindings/mcp/`
- `draft-infantado-agent-memory-architecture`, Protocol Bindings section
