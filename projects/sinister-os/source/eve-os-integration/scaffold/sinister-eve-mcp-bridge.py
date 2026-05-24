#!/usr/bin/env python3
"""sinister-eve-mcp-bridge.py — Python prototype of the EVE OS-integration daemon.

Author: RKOJ-ELENO :: 2026-05-24
License: operator-owned (Sinister fleet, internal)

This is a runnable, single-file prototype of the daemon described in DESIGN.md.
It is intentionally NOT production code — that role belongs to the Rust crate
that ships at source/eve-control/ once the P3 gate opens. This file exists so the
operator can boot the CachyOS VM, run it, and see the surface area live before
greenlighting Rust work.

Run (dev mode, no systemd, no /run/sinister/ paths required):

    python3 sinister-eve-mcp-bridge.py --dev

Then in another terminal:

    curl -s http://127.0.0.1:7331/health | python -m json.tool
    curl -s http://127.0.0.1:7331/v1/tools/list | python -m json.tool
    curl -s -X POST http://127.0.0.1:7331/v1/intent/dispatch \
        -H 'content-type: application/json' \
        -d '{"intent":"status"}' | python -m json.tool
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

LOG = logging.getLogger("sinister-eve")

DEFAULT_MEMORY_ROOT = Path("/var/lib/sinister/memory")
DEFAULT_MCP_DIR = Path("/etc/sinister/mcp")
DEFAULT_BIND = ("127.0.0.1", 7331)

# In --dev mode we use $XDG_RUNTIME_DIR / a temp dir so the prototype runs as the
# operator without needing /var/lib/sinister/ to exist.
DEV_MEMORY_ROOT = Path(os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir())) / "sinister-eve-dev" / "memory"
DEV_MCP_DIR = Path(__file__).resolve().parent / "etc" / "sinister" / "mcp"


# --------------------------------------------------------------------------- #
# Memory layer (Layer 1)
# --------------------------------------------------------------------------- #
@dataclass
class MemoryStore:
    root: Path

    def ensure(self) -> None:
        for sub in ("heartbeats", "knowledge", "resume-points", "inbox", "cross-agent", "PROGRESS"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        utterances = self.root / "operator-utterances.jsonl"
        utterances.touch(exist_ok=True)

    def _safe_path(self, key: str) -> Path:
        # Disallow path-traversal. Keys are slash-delimited under the memory root.
        if ".." in key.split("/") or key.startswith("/"):
            raise ValueError(f"unsafe memory key: {key!r}")
        return self.root / key

    def get(self, key: str) -> str | None:
        p = self._safe_path(key)
        if not p.is_file():
            return None
        return p.read_text(encoding="utf-8")

    def set(self, key: str, value: str) -> None:
        p = self._safe_path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        # Atomic: write temp + fsync + rename.
        tmp = tempfile.NamedTemporaryFile("w", dir=p.parent, delete=False, encoding="utf-8")
        try:
            tmp.write(value)
            tmp.flush()
            os.fsync(tmp.fileno())
        finally:
            tmp.close()
        os.replace(tmp.name, p)

    def list(self, prefix: str = "") -> list[str]:
        base = self._safe_path(prefix) if prefix else self.root
        if not base.exists():
            return []
        out = []
        for entry in base.rglob("*"):
            if entry.is_file():
                out.append(str(entry.relative_to(self.root)).replace(os.sep, "/"))
        return sorted(out)

    def append_utterance(self, row: dict[str, Any]) -> None:
        p = self.root / "operator-utterances.jsonl"
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())


# --------------------------------------------------------------------------- #
# Tool registry (Layer 3 discovery)
# --------------------------------------------------------------------------- #
@dataclass
class ToolRegistration:
    name: str
    description: str
    exec: str
    subcommands: list[dict[str, Any]] = field(default_factory=list)
    intents: list[dict[str, Any]] = field(default_factory=list)
    transport: str = "exec"  # exec | http

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ToolRegistration:
        return cls(
            name=data["tool"],
            description=data.get("description", ""),
            exec=data.get("exec", ""),
            subcommands=data.get("subcommands", []),
            intents=data.get("intents", []),
            transport=data.get("transport", "exec"),
        )


@dataclass
class ToolRegistry:
    mcp_dir: Path
    tools: dict[str, ToolRegistration] = field(default_factory=dict)

    def load(self) -> None:
        self.tools.clear()
        if not self.mcp_dir.exists():
            LOG.warning("mcp dir does not exist: %s", self.mcp_dir)
            return
        for f in sorted(self.mcp_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                tool = ToolRegistration.from_json(data)
                self.tools[tool.name] = tool
                LOG.info("registered tool %s from %s", tool.name, f.name)
            except Exception as exc:  # noqa: BLE001
                LOG.error("failed to load %s: %s", f, exc)

    def list_tools(self) -> list[dict[str, Any]]:
        out = []
        for tool in self.tools.values():
            for sub in tool.subcommands:
                out.append({
                    "name": f"{tool.name}.{sub['name']}",
                    "description": sub.get("description", ""),
                    "args": sub.get("args", []),
                })
        return out

    def call(self, fq_name: str, args: dict[str, Any]) -> dict[str, Any]:
        if "." not in fq_name:
            raise ValueError(f"tool name must be tool.subcommand, got {fq_name!r}")
        tool_name, sub_name = fq_name.split(".", 1)
        tool = self.tools.get(tool_name)
        if tool is None:
            raise KeyError(f"unknown tool {tool_name!r}")
        sub = next((s for s in tool.subcommands if s["name"] == sub_name), None)
        if sub is None:
            raise KeyError(f"unknown subcommand {sub_name!r} on tool {tool_name!r}")
        if tool.transport == "http":
            return self._call_http(tool, sub, args)
        return self._call_exec(tool, sub, args)

    def _call_exec(self, tool: ToolRegistration, sub: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        cmd = [tool.exec, sub["name"]]
        for spec in sub.get("args", []):
            name = spec["name"]
            if name in args:
                cmd.append(f"--{name}")
                cmd.append(str(args[name]))
            elif spec.get("required"):
                raise ValueError(f"missing required arg {name!r}")
        # In --dev mode the exec may not exist; we report dry-run.
        if not Path(tool.exec).exists():
            return {"dry_run": True, "cmd": cmd, "reason": "exec not found on this host"}
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            "cmd": cmd,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    def _call_http(self, tool: ToolRegistration, sub: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        # Prototype: report the dispatch plan; real proxy lives in Rust.
        return {
            "dispatch": "http",
            "url": tool.exec.rstrip("/") + sub.get("http_path", ""),
            "method": sub.get("http_method", "POST"),
            "body": args,
            "note": "Python prototype does not perform the HTTP call; Rust impl will.",
        }

    def match_intent(self, intent: str) -> tuple[ToolRegistration, dict[str, Any], dict[str, Any]] | None:
        for tool in self.tools.values():
            for rule in tool.intents:
                m = re.match(rule["regex"], intent.strip(), flags=re.IGNORECASE)
                if not m:
                    continue
                sub_name = rule["subcommand"]
                sub = next((s for s in tool.subcommands if s["name"] == sub_name), None)
                if sub is None:
                    continue
                # Substitute capture groups into args template.
                args = {}
                for k, tmpl in rule.get("args", {}).items():
                    args[k] = tmpl.format(**m.groupdict(), **{str(i): g for i, g in enumerate(m.groups())})
                return tool, sub, args
        return None


# --------------------------------------------------------------------------- #
# LLM backend
# --------------------------------------------------------------------------- #
class LLMBackend:
    """Thin adapter. Real client lives in the Rust daemon; this is enough to prove the route."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.model = os.environ.get("EVE_MODEL", "claude-opus-4-7")

    def status(self) -> dict[str, Any]:
        return {
            "anthropic_configured": bool(self.api_key),
            "ollama_host": self.ollama_host,
            "model": self.model,
        }

    def chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        # Prototype-grade: never actually calls the network. Returns a stub so the
        # surface is shaped right for the Rust port without burning API credits in dev.
        return {
            "backend": "anthropic" if self.api_key else ("ollama" if self.ollama_host else "none"),
            "model": self.model,
            "stub": True,
            "note": "Prototype does not call the LLM. Rust daemon will. See DESIGN.md sec 2.4.",
            "echo": messages[-1] if messages else None,
        }


# --------------------------------------------------------------------------- #
# HTTP surface (Layer 2)
# --------------------------------------------------------------------------- #
class EVEHandler(BaseHTTPRequestHandler):
    daemon: "EVEDaemon"  # injected via factory

    def log_message(self, fmt: str, *args: Any) -> None:  # quieter than default
        LOG.info("http %s - " + fmt, self.address_string(), *args)

    def _send_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.path == "/health":
                self._send_json(HTTPStatus.OK, self.daemon.health())
            elif self.path == "/v1/tools/list":
                self._send_json(HTTPStatus.OK, {"tools": self.daemon.registry.list_tools()})
            elif self.path.startswith("/v1/memory/get"):
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                key = (qs.get("key") or [""])[0]
                val = self.daemon.memory.get(key)
                if val is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found", "key": key})
                else:
                    self._send_json(HTTPStatus.OK, {"key": key, "value": val})
            elif self.path.startswith("/v1/memory/list"):
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                prefix = (qs.get("prefix") or [""])[0]
                self._send_json(HTTPStatus.OK, {"prefix": prefix, "entries": self.daemon.memory.list(prefix)})
            else:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "no such endpoint", "path": self.path})
        except Exception as exc:  # noqa: BLE001
            LOG.exception("GET %s failed", self.path)
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._read_json()
            if self.path == "/v1/tools/call":
                result = self.daemon.registry.call(body["tool"], body.get("args", {}))
                self._send_json(HTTPStatus.OK, result)
            elif self.path == "/v1/memory/set":
                v = body["value"]
                self.daemon.memory.set(body["key"], v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
                self._send_json(HTTPStatus.OK, {"ok": True, "key": body["key"]})
            elif self.path == "/v1/intent/dispatch":
                intent = body.get("intent", "")
                self.daemon.memory.append_utterance({
                    "ts": time.time(),
                    "kind": "intent",
                    "intent": intent,
                })
                match = self.daemon.registry.match_intent(intent)
                if match is not None:
                    tool, sub, args = match
                    result = self.daemon.registry.call(f"{tool.name}.{sub['name']}", args)
                    self._send_json(HTTPStatus.OK, {"matched": True, "tool": f"{tool.name}.{sub['name']}", "args": args, "result": result})
                else:
                    # No regex hit → ask the LLM. Prototype returns the stub.
                    llm_resp = self.daemon.llm.chat([
                        {"role": "system", "content": "You are EVE. Match the user intent to one of the tools."},
                        {"role": "user", "content": intent},
                    ])
                    self._send_json(HTTPStatus.OK, {"matched": False, "llm": llm_resp})
            elif self.path == "/v1/llm/chat":
                self._send_json(HTTPStatus.OK, self.daemon.llm.chat(body.get("messages", [])))
            elif self.path == "/v1/heartbeat":
                slug = body.get("slug", "unknown")
                self.daemon.memory.set(f"heartbeats/{slug}.json", json.dumps({
                    "slug": slug,
                    "ts": time.time(),
                    "payload": body.get("payload", {}),
                }, ensure_ascii=False, indent=2))
                self._send_json(HTTPStatus.OK, {"ok": True, "slug": slug})
            else:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "no such endpoint", "path": self.path})
        except KeyError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"missing field {exc}"})
        except Exception as exc:  # noqa: BLE001
            LOG.exception("POST %s failed", self.path)
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})


# --------------------------------------------------------------------------- #
# Daemon
# --------------------------------------------------------------------------- #
@dataclass
class EVEDaemon:
    memory: MemoryStore
    registry: ToolRegistry
    llm: LLMBackend
    bind: tuple[str, int]
    started_at: float = field(default_factory=time.time)

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "uptime_secs": round(time.time() - self.started_at, 2),
            "tool_count": len(self.registry.tools),
            "memory_root": str(self.memory.root),
            "llm": self.llm.status(),
        }

    def serve(self) -> None:
        EVEHandler.daemon = self
        httpd = ThreadingHTTPServer(self.bind, EVEHandler)
        LOG.info("listening on http://%s:%s", *self.bind)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            LOG.info("shutting down")
            httpd.server_close()


# --------------------------------------------------------------------------- #
# CLI entry
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sinister-eve", description="EVE OS-integration daemon (Python prototype).")
    parser.add_argument("command", nargs="?", default="daemon", choices=["daemon", "health"])
    parser.add_argument("--config", default=os.environ.get("EVE_CONFIG", "/etc/sinister/eve.toml"))
    parser.add_argument("--dev", action="store_true", help="dev-mode: use temp dirs, do not require /var/lib/sinister.")
    parser.add_argument("--bind", default=None, help="host:port (default 127.0.0.1:7331).")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    if args.dev:
        memory_root = DEV_MEMORY_ROOT
        mcp_dir = DEV_MCP_DIR
    else:
        memory_root = Path(os.environ.get("EVE_MEMORY_ROOT", str(DEFAULT_MEMORY_ROOT)))
        mcp_dir = Path(os.environ.get("EVE_MCP_TOOL_DIR", str(DEFAULT_MCP_DIR)))

    if args.bind:
        host, port = args.bind.split(":")
        bind = (host, int(port))
    else:
        bind = DEFAULT_BIND

    memory = MemoryStore(memory_root)
    memory.ensure()
    registry = ToolRegistry(mcp_dir)
    registry.load()
    llm = LLMBackend()
    daemon = EVEDaemon(memory=memory, registry=registry, llm=llm, bind=bind)

    if args.command == "health":
        print(json.dumps(daemon.health(), indent=2))
        return 0

    LOG.info("memory root: %s", memory_root)
    LOG.info("mcp dir:     %s", mcp_dir)
    LOG.info("tools:       %d", len(registry.tools))
    daemon.serve()
    return 0


if __name__ == "__main__":
    sys.exit(main())
