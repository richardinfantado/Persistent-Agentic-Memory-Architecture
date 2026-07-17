# PAMSPEC-over-MCP reference server (Python stub)

Non-production reference server demonstrating the PAMSPEC-over-MCP
binding contract. Wraps the `pamspec_ref.MemoryService` (PAMSPEC-Lite)
and exposes it as a set of MCP tools with the naming and error
semantics defined in `bindings/mcp/README.md`.

## Status

Stub. This is a **protocol adapter reference**, not a working MCP
transport implementation. It shows exactly:

- How `pamspec.<operation>` tool arguments map to PAMSPEC operation
  inputs.
- How PAMSPEC errors are returned as tool-result payloads (never
  as MCP protocol errors, per the binding spec).
- How the discovery manifest is constructed.

To turn it into a live MCP server, wire the `dispatch()` function
into an MCP transport implementation (e.g., `mcp` PyPI package,
or a custom stdio/websocket layer). No PAMSPEC logic changes are
required at that layer.

## Use

```python
from pathlib import Path
from pamspec_ref import MemoryService
from pamspec_mcp_server import PamspecMcpAdapter

adapter = PamspecMcpAdapter(MemoryService(":memory:"))

# Discovery
print(adapter.manifest())

# Dispatch a tool call (as an MCP server would after parsing)
result = adapter.dispatch("pamspec.create", {
    "scope_id": "workspace:demo",
    "object_type": "claim",
    "canonical_content": {"statement": "hi"},
    "actor": {"actor_id": "actor:demo", "actor_kind": "human"},
    "provenance": {
        "provenance_id": "prov:1",
        "actor": {"actor_id": "actor:demo", "actor_kind": "human"},
        "activity": "created",
        "recorded_at": "2026-07-17T00:00:00Z"
    }
})
print(result)
```

## Test

```bash
python -m pytest bindings/mcp/server-python/tests
```
