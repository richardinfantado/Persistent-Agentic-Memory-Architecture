# PAMSPEC-over-MCP Binding Profile

Normative mapping from PAMSPEC canonical operation semantics onto the
Model Context Protocol (MCP) tool and resource surface. Conforming
implementations SHOULD publish a binding manifest at a well-known name
so MCP-aware clients (Claude Desktop, Cursor, Claude Code, and others)
can discover and use the memory service without custom integration.

## Scope

Covers the transport-neutral operations defined in
`draft-infantado-agent-memory-architecture.md`:
`create`, `read`, `update`, `transition`, `relate`, `query`,
`inspect_history`, `redact`, and `delete`. Also covers the
`subscribe` operation defined in ADR-0023.

## Tool naming

Every PAMSPEC operation maps to a single MCP tool named
`pamspec.<operation>`. Names are stable across profile revisions.

| PAMSPEC operation | MCP tool name |
| --- | --- |
| Create             | `pamspec.create` |
| Read               | `pamspec.read` |
| Update             | `pamspec.update` |
| Transition         | `pamspec.transition` |
| Relate             | `pamspec.relate` |
| Query              | `pamspec.query` |
| Inspect History    | `pamspec.inspect_history` |
| Redact             | `pamspec.redact` |
| Delete             | `pamspec.delete` |
| Subscribe          | `pamspec.subscribe` |

## Resource naming

Memory Scopes are exposed as MCP resources:

```
pamspec://scope/{scope_id}
pamspec://scope/{scope_id}/object/{object_id}
pamspec://scope/{scope_id}/object/{object_id}/version/{version_id}
pamspec://scope/{scope_id}/events
pamspec://scope/{scope_id}/snapshot/{snapshot_id}
```

Resource reads MUST enforce scope authorization identically to `read` /
`inspect_history` tool calls. Resource URIs MUST be percent-encoded per
RFC 3986 and MUST NOT reveal protected object existence to unauthorized
callers.

## Envelope preservation

The MCP tool `arguments` object carries PAMSPEC input fields verbatim
using the JSON field names defined in the canonical envelope
(`schemas/0.1-draft/*.schema.json`). MCP tool results return the
canonical envelope for successful state-changing operations and an
error envelope conforming to `error.schema.json` for failures.

The following PAMSPEC control fields MUST be carried in MCP `arguments`
without renaming or restructuring:

- `operation_id`
- `idempotency_key`
- `expected_version_id`
- `scope_id`
- `snapshot_id`
- `cursor` (pagination)
- `after_sequence` (event streams)

## Error mapping

MCP transports errors as tool-result payloads with a distinct shape.
The PAMSPEC binding MUST return a JSON object containing at minimum:

```json
{
  "error": {
    "code": "version_conflict",
    "message": "...",
    "retryable": true,
    "operation_id": "op:...",
    "details": { "expected_version_id": "...", "current_version_id": "..." }
  }
}
```

Binding servers MUST NOT map PAMSPEC error codes onto MCP protocol
errors, because that would hide the retryability, remediation, and
policy metadata that PAMSPEC callers depend on. MCP protocol errors
remain reserved for transport-level failures (parse errors, unknown
tool, transport disconnect).

## Streaming (Subscribe)

`pamspec.subscribe` uses MCP notifications. The server sends one MCP
notification per Event Ledger entry that matches the subscription
filter. Notification payload conforms to `memory-event.schema.json`.
Clients terminate a subscription by calling `pamspec.subscribe.cancel`
with the returned `subscription_id`.

## Discovery manifest

A conforming server MUST advertise a discovery resource at
`pamspec://manifest` returning:

```json
{
  "spec_version": "0.1.0-draft",
  "binding_version": "0.1.0-draft",
  "profiles": ["PAMSPEC-Lite"],
  "scopes_visible": ["workspace:demo"],
  "operations": ["create", "read", "update", "delete", "query"]
}
```

`profiles` lists every PAMSPEC conformance profile the server implements.
`operations` lists every operation the server exposes for this session
under this actor's authorization.

## Idempotency and retries

Every state-changing MCP tool call MUST honor `idempotency_key` per
PAMSPEC semantics: the same key with identical arguments returns the
original result; the same key with different arguments returns
`duplicate_operation`. MCP retries MUST use the same key.

## Non-goals

- Not a replacement for MCP; a client that speaks MCP does not need
  PAMSPEC-specific code to invoke a `pamspec.*` tool.
- Not a mandatory binding; the core spec remains transport-neutral.
- Not a full authorization model; MCP authorization delegates to the
  server, which enforces PAMSPEC scope and policy rules.

## Reference

`draft-infantado-agent-memory-architecture.md`, Protocol Bindings section.
