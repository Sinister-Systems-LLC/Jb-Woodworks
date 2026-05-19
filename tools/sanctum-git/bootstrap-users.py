# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""
bootstrap-users.py -- ensure operator + leo users exist on the sanctum-git
(Gitea) instance at http://localhost:3000, with their SSH keys registered.

Reads admin creds from `.env` (same folder).

Idempotent: re-running is safe. Existing users / keys are detected and skipped.

USAGE
    python bootstrap-users.py
    python bootstrap-users.py --leo-key-file C:\\Users\\Zonia\\Desktop\\leo.pub
    python bootstrap-users.py --leo-password "<one-time-leo-pw>"
    python bootstrap-users.py --gitea-url http://localhost:3000 --json-out manifest.json

WHAT IT DOES
    1. Loads .env (GITEA_ADMIN_USER, GITEA_ADMIN_PASSWORD, GITEA_ADMIN_EMAIL,
       optionally GITEA_URL).
    2. Confirms admin can reach GET /api/v1/version.
    3. For each of (operator, leo):
         a. GET /api/v1/users/<name> -- if 404, POST /api/v1/admin/users
         b. Find an SSH public key to register:
            - operator: ~/.ssh/id_ed25519.pub (if present, else skip)
            - leo:      --leo-key-file <path> (operator-supplied)
         c. GET /api/v1/users/<name>/keys -- if the .pub isn't already there,
            POST /api/v1/admin/users/<name>/keys
    4. Emits a JSON manifest on stdout (and optionally to --json-out) describing
       exactly what was created / skipped.

EXIT CODES
    0  success (all required ops completed or were already in place)
    1  config error (missing .env, bad creds, Gitea unreachable)
    2  partial failure (some user/key op failed; manifest shows which)

WIRING
    - Lives under tools/sanctum-git/ alongside docker-compose.yml + .env.example
    - Pairs with setup-vault-data-dir.ps1 (data lives in D:\\sinister-vault\\gitea\\)
    - Documented in vault-integration.md (same folder)
"""

from __future__ import annotations

import argparse
import base64
import datetime as _dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

DEFAULT_GITEA_URL = "http://localhost:3000"
HERE = Path(__file__).resolve().parent
ENV_PATH = HERE / ".env"

# Users we provision. operator = admin, leo = collaborator. Each entry maps to
# the kwargs we'll pass to POST /api/v1/admin/users.
USERS_SPEC: List[Dict[str, Any]] = [
    {
        "username": "operator",
        "email_env": "GITEA_ADMIN_EMAIL",
        "email_default": "operator@sinister.local",
        "must_change_password": False,
        "admin": True,
        "key_source": "ssh_dir",  # ~/.ssh/id_ed25519.pub if present
        "password_env": "GITEA_ADMIN_PASSWORD",  # reuses admin pw
    },
    {
        "username": "leo",
        "email_env": "LEO_EMAIL",
        "email_default": "leo@sinister.local",
        "must_change_password": True,  # forces Leo to rotate on first login
        "admin": False,
        "key_source": "cli_arg",  # operator passes --leo-key-file
        "password_env": "LEO_INITIAL_PASSWORD",  # may be set in .env, or via --leo-password
    },
]


# ---------------------------------------------------------------------------
# tiny .env loader (no python-dotenv dependency)
# ---------------------------------------------------------------------------


def load_env(path: Path) -> Dict[str, str]:
    """Parse a KEY=VALUE .env file. Comments (#) and blanks are skipped.

    Values may be wrapped in single or double quotes; quotes are stripped.
    """
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        out[key] = value
    return out


# ---------------------------------------------------------------------------
# Gitea API client (urllib only; stdlib so no pip install needed)
# ---------------------------------------------------------------------------


class GiteaError(Exception):
    def __init__(self, status: int, body: str, url: str):
        super().__init__(f"HTTP {status} on {url} :: {body[:300]}")
        self.status = status
        self.body = body
        self.url = url


class GiteaClient:
    def __init__(self, base_url: str, admin_user: str, admin_pass: str):
        self.base_url = base_url.rstrip("/")
        token = base64.b64encode(f"{admin_user}:{admin_pass}".encode("utf-8")).decode("ascii")
        self.auth_header = f"Basic {token}"

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 15,
    ) -> Tuple[int, Any]:
        url = f"{self.base_url}{path}"
        data_bytes = None
        if body is not None:
            data_bytes = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url=url, data=data_bytes, method=method)
        req.add_header("Authorization", self.auth_header)
        req.add_header("Accept", "application/json")
        if data_bytes is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                status = resp.status
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
            return e.code, _safe_json(raw)
        except urllib.error.URLError as e:
            raise GiteaError(0, f"network error: {e.reason}", url) from e
        return status, _safe_json(raw)

    # -- convenience ---------------------------------------------------------

    def version(self) -> str:
        status, body = self._request("GET", "/api/v1/version")
        if status != 200 or not isinstance(body, dict):
            raise GiteaError(status, json.dumps(body), "/api/v1/version")
        return str(body.get("version", "unknown"))

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        status, body = self._request("GET", f"/api/v1/users/{urllib.parse.quote(username)}")
        if status == 200 and isinstance(body, dict):
            return body
        if status == 404:
            return None
        raise GiteaError(status, json.dumps(body), f"/api/v1/users/{username}")

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        admin: bool,
        must_change_password: bool,
    ) -> Dict[str, Any]:
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "must_change_password": must_change_password,
            "send_notify": False,
            "source_id": 0,
            "login_name": username,
        }
        if admin:
            payload["admin"] = True
        status, body = self._request("POST", "/api/v1/admin/users", body=payload)
        if status not in (200, 201):
            raise GiteaError(status, json.dumps(body), "/api/v1/admin/users")
        return body if isinstance(body, dict) else {}

    def list_user_keys(self, username: str) -> List[Dict[str, Any]]:
        status, body = self._request("GET", f"/api/v1/users/{urllib.parse.quote(username)}/keys")
        if status == 200 and isinstance(body, list):
            return body
        if status == 404:
            return []
        raise GiteaError(status, json.dumps(body), f"/api/v1/users/{username}/keys")

    def add_user_key(self, username: str, title: str, public_key: str) -> Dict[str, Any]:
        payload = {"title": title, "key": public_key, "read_only": False}
        path = f"/api/v1/admin/users/{urllib.parse.quote(username)}/keys"
        status, body = self._request("POST", path, body=payload)
        if status not in (200, 201):
            raise GiteaError(status, json.dumps(body), path)
        return body if isinstance(body, dict) else {}


def _safe_json(raw: str) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


# ---------------------------------------------------------------------------
# key file discovery
# ---------------------------------------------------------------------------


def discover_operator_ssh_key() -> Optional[Tuple[str, str]]:
    """Return (path_str, key_text) for the operator's ~/.ssh/id_ed25519.pub
    if present, else None.
    """
    home = Path.home()
    candidates = [
        home / ".ssh" / "id_ed25519.pub",
        home / ".ssh" / "id_rsa.pub",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            try:
                text = c.read_text(encoding="utf-8").strip()
                if text:
                    return str(c), text
            except OSError:
                continue
    return None


def read_key_file(path_str: str) -> str:
    p = Path(path_str).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"SSH key file not found: {p}")
    text = p.read_text(encoding="utf-8").strip()
    if not text or not (text.startswith("ssh-") or text.startswith("ecdsa-")):
        raise ValueError(f"{p} does not look like an OpenSSH public key (expected ssh-... or ecdsa-...)")
    return text


def _key_fingerprint_compare(a: str, b: str) -> bool:
    """Loose compare: split off the base64 chunk and match it. Tolerates
    differing comments at the end."""
    def _chunk(s: str) -> str:
        parts = s.strip().split()
        if len(parts) >= 2:
            return parts[1]
        return s.strip()
    return _chunk(a) == _chunk(b)


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------


def provision_user(
    client: GiteaClient,
    spec: Dict[str, Any],
    env: Dict[str, str],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    username = spec["username"]
    entry: Dict[str, Any] = {
        "username": username,
        "user_action": "unknown",
        "key_action": "unknown",
        "details": {},
    }

    # ---- user create / detect ---------------------------------------------
    existing = client.get_user(username)
    if existing is not None:
        entry["user_action"] = "skipped_exists"
        entry["details"]["user_id"] = existing.get("id")
    else:
        email = env.get(spec["email_env"]) or spec["email_default"]
        # Password resolution order:
        #   1. --leo-password CLI arg (only applies to leo)
        #   2. spec.password_env in .env
        #   3. fallback: prompt-equivalent: hard error so operator picks one
        password: Optional[str] = None
        if username == "leo" and getattr(args, "leo_password", None):
            password = args.leo_password
        if not password:
            password = env.get(spec["password_env"])
        if not password:
            raise RuntimeError(
                f"cannot create user '{username}': no password available. Set "
                f"{spec['password_env']} in .env or pass --leo-password."
            )
        created = client.create_user(
            username=username,
            email=email,
            password=password,
            admin=bool(spec.get("admin", False)),
            must_change_password=bool(spec.get("must_change_password", False)),
        )
        entry["user_action"] = "created"
        entry["details"]["user_id"] = created.get("id")
        entry["details"]["email"] = email
        if spec.get("must_change_password"):
            entry["details"]["must_change_password"] = True

    # ---- SSH key registration ---------------------------------------------
    key_text: Optional[str] = None
    key_label: Optional[str] = None

    if spec["key_source"] == "ssh_dir":
        found = discover_operator_ssh_key()
        if found is None:
            entry["key_action"] = "skipped_no_local_key"
            return entry
        key_label, key_text = f"operator-ssh::{Path(found[0]).name}", found[1]

    elif spec["key_source"] == "cli_arg":
        if not args.leo_key_file:
            entry["key_action"] = "skipped_no_cli_arg"
            entry["details"]["hint"] = "re-run with --leo-key-file <path-to-leo.pub>"
            return entry
        try:
            key_text = read_key_file(args.leo_key_file)
            key_label = f"leo-ssh::{Path(args.leo_key_file).name}"
        except (FileNotFoundError, ValueError) as e:
            entry["key_action"] = "failed_read_key"
            entry["details"]["error"] = str(e)
            return entry

    if key_text is None or key_label is None:
        entry["key_action"] = "no_key_to_install"
        return entry

    existing_keys = client.list_user_keys(username)
    already = any(_key_fingerprint_compare(k.get("key", ""), key_text) for k in existing_keys)
    if already:
        entry["key_action"] = "skipped_key_already_present"
        return entry

    added = client.add_user_key(username, title=key_label, public_key=key_text)
    entry["key_action"] = "added"
    entry["details"]["key_id"] = added.get("id")
    entry["details"]["key_title"] = added.get("title", key_label)
    return entry


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap operator + leo users on sanctum-git Gitea.")
    parser.add_argument("--gitea-url", default=None, help="Override Gitea URL (default: GITEA_URL from .env, else http://localhost:3000).")
    parser.add_argument("--leo-key-file", default=None, help="Path to Leo's SSH public key (.pub). Required to install Leo's key.")
    parser.add_argument("--leo-password", default=None, help="One-time initial password for the leo user (overrides .env LEO_INITIAL_PASSWORD).")
    parser.add_argument("--json-out", default=None, help="Write the JSON manifest to this file (in addition to stdout).")
    parser.add_argument("--env-file", default=str(ENV_PATH), help=f"Path to .env (default: {ENV_PATH}).")
    args = parser.parse_args(argv)

    env_path = Path(args.env_file)
    env = load_env(env_path)
    # Layer environment-variable overrides on top of .env (CI / scripted use).
    for k in ("GITEA_URL", "GITEA_ADMIN_USER", "GITEA_ADMIN_PASSWORD",
              "GITEA_ADMIN_EMAIL", "LEO_EMAIL", "LEO_INITIAL_PASSWORD"):
        v = os.environ.get(k)
        if v:
            env[k] = v

    admin_user = env.get("GITEA_ADMIN_USER")
    admin_pass = env.get("GITEA_ADMIN_PASSWORD")
    gitea_url = args.gitea_url or env.get("GITEA_URL") or DEFAULT_GITEA_URL

    if not admin_user or not admin_pass or admin_pass == "set_in_gitea_ui_first_run":
        print("[bootstrap-users] ERROR: .env is missing GITEA_ADMIN_USER / GITEA_ADMIN_PASSWORD.", file=sys.stderr)
        print(f"  expected at: {env_path}", file=sys.stderr)
        print("  did you complete the Gitea install wizard at http://localhost:3000 first?", file=sys.stderr)
        return 1

    client = GiteaClient(gitea_url, admin_user, admin_pass)

    # smoke test
    try:
        version = client.version()
    except GiteaError as e:
        print(f"[bootstrap-users] ERROR: cannot reach Gitea at {gitea_url}: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001 — surface ANY surprise as a clean exit
        print(f"[bootstrap-users] ERROR: unexpected failure pinging Gitea: {e}", file=sys.stderr)
        return 1

    manifest: Dict[str, Any] = {
        "started_at_utc": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "gitea_url": gitea_url,
        "gitea_version": version,
        "admin_user": admin_user,
        "users": [],
        "exit_code": 0,
        "tool": "bootstrap-users.py",
        "tool_version": 1,
    }

    any_failure = False
    for spec in USERS_SPEC:
        try:
            entry = provision_user(client, spec, env, args)
        except GiteaError as e:
            entry = {
                "username": spec["username"],
                "user_action": "failed",
                "key_action": "skipped_user_failed",
                "details": {"error": str(e), "status": e.status},
            }
            any_failure = True
        except Exception as e:  # noqa: BLE001
            entry = {
                "username": spec["username"],
                "user_action": "failed",
                "key_action": "skipped_user_failed",
                "details": {"error": f"{type(e).__name__}: {e}"},
            }
            any_failure = True
        manifest["users"].append(entry)

    if any_failure:
        manifest["exit_code"] = 2

    manifest["finished_at_utc"] = _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"

    out_text = json.dumps(manifest, indent=2, sort_keys=False)
    print(out_text)

    if args.json_out:
        try:
            Path(args.json_out).write_text(out_text, encoding="utf-8")
        except OSError as e:
            print(f"[bootstrap-users] WARN: could not write --json-out file: {e}", file=sys.stderr)

    return manifest["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
