# Conformance Harness Subprocess Protocol

Version: `1`
Status: internal harness plumbing; not a PAMSPEC memory protocol.

## Purpose

Let the PAMSPEC conformance harness talk to an implementation over
stdin/stdout as a subprocess, so implementations in any language can
be tested by the same suite. The Python reference implementation
also runs behind this protocol so the in-process and subprocess
paths test the same behavior.

This is transport plumbing only. It defines nothing about PAMSPEC
memory semantics.

## Wire format

- **Framing:** newline-delimited JSON (one JSON object per line).
- **Encoding:** UTF-8.
- **Channels:** the adapter subprocess uses `stdout` exclusively for
  protocol JSON and `stderr` exclusively for logs. The harness never
  parses `stderr` as protocol; it may capture `stderr` for diagnostics.
- **Ordering:** responses MAY arrive out of order relative to
  requests; the harness matches by `request_id`. In practice the
  reference wrapper is single-threaded and responds in order, but
  the protocol does not require it.

## Handshake (mandatory)

Immediately after start, the adapter MUST emit exactly one JSON
object on the first line of stdout describing itself:

```json
{
  "type": "hello",
  "protocol_version": 1,
  "adapter": {"name": "reference-python-subprocess", "version": "0.1.0"},
  "implementation": {"name": "pamspec_ref", "version": "0.1.0-draft"},
  "spec_commit": "45c42db6069212b5237d577b99fa7c7b03840d85",
  "profiles_supported": ["PAMSPEC-Lite", "PAMSPEC-Delegation", "PAMSPEC-Subscribe"]
}
```

The harness verifies `protocol_version == 1`. On mismatch the
harness closes stdin, waits for graceful shutdown up to
`shutdown_timeout_ms`, then kills the process.

## Requests

The harness sends one request per line:

```json
{"request_id": "1", "operation": "create", "arguments": { ... }}
```

- `request_id` is a stable string; the adapter MUST echo it on the
  matching response.
- `operation` is a PAMSPEC operation name from `pamspec_operation`
  in `common.schema.json`, PLUS the following harness-only
  operations for Delegation and Subscribe support:
  `grant_delegation`, `check_delegation`, `revoke_delegation`,
  `subscribe`, `poll_subscription`, `close_subscription`.
- `arguments` is a JSON object whose keys and shapes match the
  adapter method signature for that operation.

## Responses

Every request produces exactly one response line:

**Success:**

```json
{"request_id": "1", "result": { ... }}
```

`result` is a JSON object matching the return shape defined by the
in-process Adapter interface.

**Error:**

```json
{"request_id": "1", "error": {
  "code": "version_conflict",
  "message": "expected version is stale",
  "retryable": true,
  "details": {"expected_version_id": "ver:1", "current_version_id": "ver:2"}
}}
```

`code` is a PAMSPEC error code from `error.schema.json`.

**Protocol errors** (malformed request, unknown operation) use
`code = "invalid_request"`.

## Shutdown

The harness signals shutdown by closing stdin. The adapter SHOULD
exit within `shutdown_timeout_ms` (default 2000 ms). If it does
not, the harness sends `SIGTERM` and, after another
`shutdown_timeout_ms`, `SIGKILL` (or the platform equivalent).

## Timeouts

Every request has a hard timeout. Default is 10 seconds. On
timeout, the harness records `TIMEOUT` for the case, kills the
subprocess, and starts a fresh one for the next case.

## What the protocol deliberately does NOT do

- No streaming responses (Subscribe returns a subscription
  identifier and the harness then polls; there is no server-push).
- No binary framing.
- No JSON-RPC compatibility (this is a smaller surface, on
  purpose).
- No transport authentication (subprocess is local).
- No network transport (out of R7 scope; keep the surface for
  possible HTTP/MCP bindings in a later branch).
