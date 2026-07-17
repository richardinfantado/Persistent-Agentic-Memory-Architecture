"""Adapter that talks to any implementation over the harness
subprocess protocol (see PROTOCOL.md).

The implementation binary runs as a subprocess; the harness sends
one JSON request per line on stdin and reads one JSON response per
line from stdout. stderr is captured for diagnostics only and is
never parsed as protocol.

This lets the same suite drive:
  - the Python reference impl (via the wrapper in
    conformance/adapters/reference_python_subprocess.py)
  - a TypeScript impl (future)
  - any implementation that speaks the protocol
"""

from __future__ import annotations

import json
import shlex
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .adapter import Adapter, PamspecErrorLike


DEFAULT_REQUEST_TIMEOUT_S = 10.0
DEFAULT_SHUTDOWN_TIMEOUT_S = 2.0
PROTOCOL_VERSION = 1


class ProtocolError(Exception):
    pass


@dataclass
class AdapterInfo:
    protocol_version: int
    adapter_name: str
    adapter_version: str
    implementation_name: str
    implementation_version: str
    spec_commit: str
    profiles_supported: list[str]


class SubprocessAdapter(Adapter):
    """Adapter that dispatches operations to a subprocess."""

    def __init__(
        self,
        argv: list[str] | str,
        request_timeout_s: float = DEFAULT_REQUEST_TIMEOUT_S,
        shutdown_timeout_s: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ):
        if isinstance(argv, str):
            argv = shlex.split(argv)
        self._argv = argv
        self._request_timeout_s = request_timeout_s
        self._shutdown_timeout_s = shutdown_timeout_s
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._closed = False
        self._start(env=env, cwd=cwd)

    def _start(self, env: dict[str, str] | None, cwd: str | None) -> None:
        self._proc = subprocess.Popen(
            self._argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
            cwd=cwd,
        )
        hello_line = self._readline_with_timeout(self._request_timeout_s)
        try:
            hello = json.loads(hello_line)
        except json.JSONDecodeError as e:
            raise ProtocolError(f"invalid hello: {hello_line!r}") from e
        if hello.get("type") != "hello":
            raise ProtocolError(f"expected hello, got: {hello!r}")
        if hello.get("protocol_version") != PROTOCOL_VERSION:
            raise ProtocolError(
                f"protocol_version mismatch: harness supports "
                f"{PROTOCOL_VERSION}, adapter offers {hello.get('protocol_version')!r}"
            )
        self._info = AdapterInfo(
            protocol_version=hello["protocol_version"],
            adapter_name=hello.get("adapter", {}).get("name", "unknown"),
            adapter_version=hello.get("adapter", {}).get("version", "unknown"),
            implementation_name=hello.get("implementation", {}).get("name", "unknown"),
            implementation_version=hello.get("implementation", {}).get("version", "unknown"),
            spec_commit=hello.get("spec_commit", ""),
            profiles_supported=hello.get("profiles_supported", []),
        )

    @property
    def info(self) -> AdapterInfo:
        return self._info

    def supported_profiles(self) -> list[str]:
        return list(self._info.profiles_supported)

    def _readline_with_timeout(self, timeout_s: float) -> str:
        assert self._proc is not None and self._proc.stdout is not None
        deadline = time.monotonic() + timeout_s
        result: list[str | None] = [None]

        def _read():
            try:
                result[0] = self._proc.stdout.readline()
            except Exception:
                result[0] = None

        t = threading.Thread(target=_read, daemon=True)
        t.start()
        t.join(max(0.0, deadline - time.monotonic()))
        if t.is_alive():
            raise ProtocolError(f"read timeout after {timeout_s}s")
        line = result[0]
        if not line:
            stderr_tail = ""
            try:
                stderr_tail = self._proc.stderr.read() if self._proc.stderr else ""
            except Exception:
                pass
            raise ProtocolError(f"adapter subprocess closed stdout unexpectedly; stderr={stderr_tail[-1000:]!r}")
        return line.rstrip("\n")

    def _request(self, operation: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self._closed:
            raise ProtocolError("adapter already closed")
        assert self._proc is not None and self._proc.stdin is not None
        request_id = str(uuid.uuid4())
        line = json.dumps(
            {"request_id": request_id, "operation": operation, "arguments": arguments},
            sort_keys=True,
        )
        with self._lock:
            try:
                self._proc.stdin.write(line + "\n")
                self._proc.stdin.flush()
            except (BrokenPipeError, ValueError) as e:
                raise ProtocolError(f"failed to send request: {e}") from e
            response_line = self._readline_with_timeout(self._request_timeout_s)
        try:
            response = json.loads(response_line)
        except json.JSONDecodeError as e:
            raise ProtocolError(f"invalid response JSON: {response_line!r}") from e
        if response.get("request_id") != request_id:
            raise ProtocolError(
                f"request_id mismatch: sent {request_id!r}, got {response.get('request_id')!r}"
            )
        if "error" in response:
            err = response["error"]
            raise PamspecErrorLike(
                code=err.get("code", "invalid_request"),
                message=err.get("message", ""),
                retryable=bool(err.get("retryable", False)),
                **(err.get("details") or {}),
            )
        if "result" not in response:
            raise ProtocolError(f"response missing both 'result' and 'error': {response!r}")
        return response["result"]

    # ------------- CRUD / Lite -------------

    def create(self, **kwargs) -> dict[str, Any]:
        return self._request("create", kwargs)

    def read(self, **kwargs) -> dict[str, Any]:
        return self._request("read", kwargs)

    def update(self, **kwargs) -> dict[str, Any]:
        return self._request("update", kwargs)

    def transition(self, **kwargs) -> dict[str, Any]:
        return self._request("transition", kwargs)

    def delete(self, **kwargs) -> dict[str, Any]:
        return self._request("delete", kwargs)

    def query(self, **kwargs) -> list[dict[str, Any]]:
        return self._request("query", kwargs)

    def history(self, **kwargs) -> list[dict[str, Any]]:
        return self._request("history", kwargs)

    # ------------- Delegation -------------

    def grant_delegation(self, **kwargs) -> dict[str, Any]:
        return self._request("grant_delegation", kwargs)

    def check_delegation(self, **kwargs) -> dict[str, Any]:
        return self._request("check_delegation", kwargs)

    def revoke_delegation(self, delegation_id: str) -> None:
        self._request("revoke_delegation", {"delegation_id": delegation_id})

    # ------------- Subscribe -------------

    def subscribe(self, **kwargs) -> Any:
        result = self._request("subscribe", kwargs)
        return result["subscription_id"]

    def poll_subscription(self, subscription, max_events: int = 100) -> list[dict[str, Any]]:
        result = self._request(
            "poll_subscription",
            {"subscription_id": subscription, "max_events": max_events},
        )
        return result["events"]

    def close_subscription(self, subscription, reason: str = "client_closed") -> None:
        self._request(
            "close_subscription",
            {"subscription_id": subscription, "reason": reason},
        )

    # ------------- Teardown -------------

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        proc = self._proc
        if proc is None:
            return
        try:
            if proc.stdin and not proc.stdin.closed:
                try:
                    proc.stdin.close()
                except BrokenPipeError:
                    pass
            try:
                proc.wait(timeout=self._shutdown_timeout_s)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=self._shutdown_timeout_s)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=self._shutdown_timeout_s)
        finally:
            self._proc = None
