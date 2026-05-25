#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# claude_oauth_pasteback.py -- Helper for the Claude Login wizard's paste-back
# fallback path.
#
# Operator (verbatim 2026-05-25 ~03:10Z): "i need you to allow me to paste this
# back" -- referring to the OAuth flow where the browser redirect doesn't land
# back in the local `claude auth login` window (machine mismatch / CLI already
# closed / fallback paste mode). The wizard needs to accept the URL or code
# the operator pastes and turn it into either:
#   (a) a relay file that re-spawned `claude auth login` reads from stdin
#   (b) a parsed code string the caller can use for direct API exchange
#
# THIS HELPER IS PURE PARSING. It does NOT spawn claude, does NOT touch the
# network, does NOT write any auth/credentials files. The PowerShell wizard
# composes the parsed result into the actual flow.
#
# Why Python (per "no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25"): all NEW
# cross-platform helpers are Python; .ps1 files persist for legacy callers.
# The existing eve-bulk-oauth-login.ps1 (legacy, large) keeps the orchestration
# role; this tiny helper handles the new paste-parsing slice.
#
# USAGE:
#   python claude_oauth_pasteback.py parse "<pasted-text>"
#       -> stdout JSON: {"ok": true, "code": "abc", "kind": "url"|"bare-code", "raw": "..."}
#       -> exit 0 if parse-clean, exit 1 if junk
#
#   python claude_oauth_pasteback.py parse --stdin
#       (reads one line of pasted text from stdin)
#
#   python claude_oauth_pasteback.py write-relay <sandbox-home> "<pasted-text>"
#       -> writes <sandbox-home>/.claude/.oauth-paste-relay.txt with the parsed
#          code on the first line. The relay file is what the spawned bash
#          login script reads on its second-pass `claude auth login` attempt.
#       -> exit 0 on success
#
#   python claude_oauth_pasteback.py --help
#
# PARSE RULES:
#   1. If input contains `claude.com/cai/oauth` AND `code=` -> extract `code`
#      query param value (urlparse / parse_qs).
#   2. If input contains any `?code=...&state=...` URL shape (from console
#      flow which redirects to console.anthropic.com) -> extract `code`.
#   3. If input looks like a bare token (no `://`, no whitespace, 16+ chars,
#      mostly base64url-ish chars) -> accept as-is.
#   4. Otherwise -> exit 1, message to stderr.
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Anthropic OAuth redirect hosts we accept code= from. Listed here for clarity
# rather than gated -- the parser accepts ANY URL with a `code=` query param,
# but logs the host for telemetry/debug.
KNOWN_OAUTH_HOSTS = (
    "claude.com",
    "console.anthropic.com",
    "anthropic.com",
    "auth.anthropic.com",
)

# A bare OAuth code from Anthropic is typically a long opaque string. We
# accept anything 16+ chars of [A-Za-z0-9._\-#] (the `#` shows up because
# Anthropic's CLI sometimes prints `code#state` joined by hash).
_BARE_CODE_RE = re.compile(r"^[A-Za-z0-9._\-#]{16,512}$")


def parse_paste(raw: str) -> dict:
    """Parse a pasted line. Returns dict with at minimum {ok: bool}.

    On success: {ok: True, code: str, kind: "url"|"bare-code", host: str|None,
                 state: str|None, raw: str}.
    On failure: {ok: False, error: str, raw: str}.
    """
    s = (raw or "").strip()
    # Trim wrapping quotes the operator's terminal might have copied along.
    while len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1].strip()
    if not s:
        return {"ok": False, "error": "empty paste", "raw": raw}

    # --- URL path ----------------------------------------------------------
    if "://" in s or s.lower().startswith("//"):
        try:
            # Tolerate //host paths by prefixing https
            url = s if "://" in s else "https:" + s
            u = urlparse(url)
            # parse_qs the query AND the fragment (Anthropic sometimes uses
            # fragment-style #code=... -- belt and suspenders).
            qs = parse_qs(u.query, keep_blank_values=False)
            if "code" not in qs and u.fragment:
                qs = parse_qs(u.fragment, keep_blank_values=False)
            if "code" in qs and qs["code"]:
                code = qs["code"][0]
                state = qs.get("state", [None])[0]
                return {
                    "ok": True,
                    "code": code,
                    "kind": "url",
                    "host": u.hostname,
                    "state": state,
                    "raw": s,
                }
            return {
                "ok": False,
                "error": "URL has no `code` query param",
                "raw": s,
            }
        except Exception as e:  # pragma: no cover (defensive)
            return {"ok": False, "error": f"URL parse failed: {e}", "raw": s}

    # --- Bare-code path ----------------------------------------------------
    if " " in s or "\t" in s:
        return {
            "ok": False,
            "error": "input has whitespace and is not a URL",
            "raw": s,
        }
    if _BARE_CODE_RE.match(s):
        return {
            "ok": True,
            "code": s,
            "kind": "bare-code",
            "host": None,
            "state": None,
            "raw": s,
        }
    return {
        "ok": False,
        "error": (
            "input is not a recognized OAuth URL (must contain ://...code=...) "
            "or a bare code (16+ chars, [A-Za-z0-9._-#])"
        ),
        "raw": s,
    }


def write_relay(sandbox_home: str, raw: str) -> int:
    """Write a relay file inside the sandbox so the bash login script can pick
    up the pasted code on its second-pass `claude auth login` invocation.

    Layout: <sandbox-home>/.claude/.oauth-paste-relay.txt
    File contents (UTF-8, LF-terminated):
        line 1: <code>
        line 2: <kind>          (url|bare-code)
        line 3: <host or "">
        line 4: <state or "">
        line 5: <raw paste>
    """
    parsed = parse_paste(raw)
    if not parsed.get("ok"):
        sys.stderr.write(
            f"[paste-relay] refused: {parsed.get('error', 'unknown')}\n"
        )
        json.dump(parsed, sys.stdout)
        sys.stdout.write("\n")
        return 1
    home = Path(sandbox_home)
    claude_dir = home / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    relay = claude_dir / ".oauth-paste-relay.txt"
    body = "\n".join(
        [
            parsed["code"],
            parsed["kind"],
            parsed.get("host") or "",
            parsed.get("state") or "",
            parsed["raw"],
        ]
    ) + "\n"
    relay.write_text(body, encoding="utf-8", newline="\n")
    parsed["relay_path"] = str(relay)
    json.dump(parsed, sys.stdout)
    sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="claude_oauth_pasteback",
        description=(
            "Parse a Claude OAuth paste (full redirect URL or bare code) and "
            "optionally write a relay file inside a wizard sandbox."
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_parse = sub.add_parser("parse", help="Parse a paste; print JSON.")
    sp_parse.add_argument("paste", nargs="?", default=None)
    sp_parse.add_argument(
        "--stdin",
        action="store_true",
        help="Read one line from stdin instead of arg.",
    )

    sp_relay = sub.add_parser(
        "write-relay",
        help="Parse a paste + write relay file into a sandbox HOME.",
    )
    sp_relay.add_argument("sandbox_home")
    sp_relay.add_argument("paste", nargs="?", default=None)
    sp_relay.add_argument("--stdin", action="store_true")

    args = p.parse_args(argv)

    if args.cmd == "parse":
        raw = (
            sys.stdin.readline()
            if args.stdin
            else (args.paste if args.paste is not None else "")
        )
        result = parse_paste(raw)
        json.dump(result, sys.stdout)
        sys.stdout.write("\n")
        return 0 if result.get("ok") else 1

    if args.cmd == "write-relay":
        raw = (
            sys.stdin.readline()
            if args.stdin
            else (args.paste if args.paste is not None else "")
        )
        return write_relay(args.sandbox_home, raw)

    return 2


if __name__ == "__main__":
    sys.exit(main())
