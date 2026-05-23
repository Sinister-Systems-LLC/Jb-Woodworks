"""
vault - unified MCP façade over the Sinister Vault stack.

Wraps three local backends behind one tool namespace so any Claude session
(including RKOJ-spawned agents) has a single, predictable "talk to the vault"
surface:

  - Vault daemon  http://127.0.0.1:5078   (quota, audit, snapshot)
  - Gitea         http://127.0.0.1:3000   (repos, commit, push, pull, search)
  - Syncthing     http://127.0.0.1:8384   (folder sync state)
  - Filesystem    D:\\sinister-vault\\    (browse, list, accounts)

Tier 1 (pure Python). No LLM. All tools return {ok: bool, ...}.

Author: Sinister Sanctum / vault MCP agent (operator: sinistersocks5g@gmail.com)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import httpx
except ImportError:
    print("[vault] httpx not installed. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[vault] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", r"D:\sinister-vault"))
VAULT_DAEMON_URL = os.environ.get("VAULT_DAEMON_URL", "http://127.0.0.1:5078").rstrip("/")

GITEA_URL = os.environ.get("GITEA_URL", "http://127.0.0.1:3000").rstrip("/")
GITEA_API_TOKEN_ENV = "GITEA_API_TOKEN"
GITEA_ENV_FILE = Path(os.environ.get(
    "GITEA_ENV_FILE",
    str(SANCTUM_ROOT / "tools" / "sanctum-git" / ".env"),
))

SYNCTHING_URL = os.environ.get("SYNCTHING_URL", "http://127.0.0.1:8384").rstrip("/")
SYNCTHING_API_KEY_ENV = "SYNCTHING_API_KEY"
SYNCTHING_CONFIG = Path(os.path.expandvars(os.environ.get(
    "SYNCTHING_CONFIG",
    r"%LOCALAPPDATA%\Syncthing\config.xml",
)))

DEFAULT_BRANCH = os.environ.get("VAULT_GIT_DEFAULT_BRANCH", "main")

USAGE_LOG = Path(os.environ.get(
    "VAULT_USAGE_LOG",
    str(HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"),
))
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

HTTP_TIMEOUT = 8.0  # seconds — vault calls are local; fail fast if backend dead

OFFLINE_HINT_VAULT = (
    "vault daemon offline (start via Sanctum-Vault-Start.bat or "
    "tools\\sinister-vault\\install-vault-task.ps1)"
)
OFFLINE_HINT_GITEA = (
    "Gitea offline (start via D:\\Sinister Sanctum\\tools\\sanctum-git\\Gitea-Start.bat)"
)
OFFLINE_HINT_SYNCTHING = (
    "Syncthing offline (start via Syncthing tray app or `syncthing.exe -no-browser`)"
)


# ---------------------------------------------------------------------------
# Lightweight call logger (matches sinister-bus convention)
# ---------------------------------------------------------------------------

def log_call(tool: str, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "vault",
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    try:
        with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        # never let logging block a tool call
        pass


# ---------------------------------------------------------------------------
# Credential loaders (read once, cached)
# ---------------------------------------------------------------------------

_gitea_token_cache: Optional[str] = None
_syncthing_key_cache: Optional[str] = None


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    try:
        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            out[k.strip()] = v
    except Exception:
        pass
    return out


def get_gitea_token() -> Optional[str]:
    global _gitea_token_cache
    if _gitea_token_cache:
        return _gitea_token_cache
    env_val = os.environ.get(GITEA_API_TOKEN_ENV)
    if env_val:
        _gitea_token_cache = env_val
        return env_val
    parsed = _parse_env_file(GITEA_ENV_FILE)
    token = parsed.get(GITEA_API_TOKEN_ENV) or parsed.get("GITEA_TOKEN")
    if token:
        _gitea_token_cache = token
    return token


def get_syncthing_key() -> Optional[str]:
    global _syncthing_key_cache
    if _syncthing_key_cache:
        return _syncthing_key_cache
    env_val = os.environ.get(SYNCTHING_API_KEY_ENV)
    if env_val:
        _syncthing_key_cache = env_val
        return env_val
    if not SYNCTHING_CONFIG.exists():
        return None
    try:
        tree = ET.parse(SYNCTHING_CONFIG)
        root = tree.getroot()
        # <gui ... ><apikey>KEY</apikey></gui>
        for gui in root.iter("gui"):
            ak = gui.find("apikey")
            if ak is not None and ak.text:
                _syncthing_key_cache = ak.text.strip()
                return _syncthing_key_cache
        # fallback — any <apikey> anywhere
        ak = root.find(".//apikey")
        if ak is not None and ak.text:
            _syncthing_key_cache = ak.text.strip()
            return _syncthing_key_cache
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Tiny HTTP helpers
# ---------------------------------------------------------------------------

def _safe_get(url: str, headers: Optional[dict[str, str]] = None,
              params: Optional[dict[str, Any]] = None) -> tuple[bool, Any, Optional[str]]:
    """Returns (ok, json_or_text, error_or_None)."""
    try:
        r = httpx.get(url, headers=headers or {}, params=params or {}, timeout=HTTP_TIMEOUT)
        if r.status_code >= 400:
            return False, None, f"HTTP {r.status_code}: {r.text[:400]}"
        try:
            return True, r.json(), None
        except Exception:
            return True, r.text, None
    except (httpx.ConnectError, httpx.ConnectTimeout):
        return False, None, "connection_refused"
    except Exception as e:
        return False, None, f"{type(e).__name__}: {e}"


def _safe_post(url: str, headers: Optional[dict[str, str]] = None,
               json_body: Any = None, params: Optional[dict[str, Any]] = None
               ) -> tuple[bool, Any, Optional[str]]:
    try:
        r = httpx.post(url, headers=headers or {}, json=json_body,
                       params=params or {}, timeout=HTTP_TIMEOUT)
        if r.status_code >= 400:
            return False, None, f"HTTP {r.status_code}: {r.text[:400]}"
        try:
            return True, r.json(), None
        except Exception:
            return True, r.text, None
    except (httpx.ConnectError, httpx.ConnectTimeout):
        return False, None, "connection_refused"
    except Exception as e:
        return False, None, f"{type(e).__name__}: {e}"


def _ping(url: str, headers: Optional[dict[str, str]] = None) -> bool:
    try:
        r = httpx.get(url, headers=headers or {}, timeout=2.5)
        return r.status_code < 500
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def _safe_join(root: Path, sub: str) -> Optional[Path]:
    """Join with root and refuse to escape it (no '..' traversal)."""
    sub = (sub or "").strip().lstrip("\\").lstrip("/")
    try:
        candidate = (root / sub).resolve()
        root_resolved = root.resolve()
    except Exception:
        return None
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None
    return candidate


def _entry_for(p: Path) -> dict[str, Any]:
    try:
        st = p.stat()
        kind = "dir" if p.is_dir() else "file"
        size = 0 if p.is_dir() else st.st_size
        return {
            "name": p.name,
            "kind": kind,
            "size": size,
            "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"name": p.name, "kind": "unknown", "error": str(e)}


# ---------------------------------------------------------------------------
# Gitea helpers
# ---------------------------------------------------------------------------

def _gitea_headers(token: Optional[str]) -> dict[str, str]:
    h = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def _resolve_repo_path(repo: str) -> Optional[Path]:
    """Find a local working copy of repo under <vault>/repos/<repo>.
    Falls back to <vault>/repos/<owner>/<repo> if 'owner/repo' is supplied.
    """
    repo_clean = repo.strip().strip("/")
    # owner/name form
    if "/" in repo_clean:
        owner, name = repo_clean.split("/", 1)
        for base in (VAULT_ROOT / "repos" / owner / name, VAULT_ROOT / "repos" / name):
            if (base / ".git").exists():
                return base
        return None
    # bare name — try repos/<name>
    base = VAULT_ROOT / "repos" / repo_clean
    if (base / ".git").exists():
        return base
    return None


def _run_git(args: list[str], cwd: Path, timeout: int = 60) -> tuple[int, str, str]:
    git_exe = shutil.which("git") or "git"
    try:
        p = subprocess.run(
            [git_exe] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "", f"git {' '.join(args)} timed out after {timeout}s"
    except FileNotFoundError:
        return -2, "", "git executable not found on PATH"
    except Exception as e:
        return -3, "", f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("vault")


# ---- vault.health --------------------------------------------------------

@mcp.tool()
def health() -> dict[str, Any]:
    """Quick aggregate status of the vault stack.

    Returns: {ok, used_gb, max_gb, vault_online, gitea_online, syncthing_online}
    Plus per-backend details so the caller can tell which dep is missing.
    """
    log_call("health")

    # Vault daemon
    vault_online = _ping(f"{VAULT_DAEMON_URL}/api/vault/health")
    used_gb: Optional[float] = None
    max_gb: Optional[float] = None
    if vault_online:
        ok, data, _ = _safe_get(f"{VAULT_DAEMON_URL}/api/vault/health")
        if ok and isinstance(data, dict):
            used_gb = data.get("used_gb")
            max_gb = data.get("max_gb")

    # Gitea
    gitea_online = _ping(f"{GITEA_URL}/api/v1/version")
    gitea_token_present = bool(get_gitea_token())

    # Syncthing
    sk = get_syncthing_key()
    syncthing_online = False
    if sk:
        syncthing_online = _ping(
            f"{SYNCTHING_URL}/rest/system/ping",
            headers={"X-API-Key": sk},
        )

    return {
        "ok": True,
        "agent": "vault",
        "vault_root": str(VAULT_ROOT),
        "vault_root_exists": VAULT_ROOT.exists(),
        "vault_online": vault_online,
        "vault_daemon_url": VAULT_DAEMON_URL,
        "used_gb": used_gb,
        "max_gb": max_gb,
        "gitea_online": gitea_online,
        "gitea_url": GITEA_URL,
        "gitea_token_present": gitea_token_present,
        "syncthing_online": syncthing_online,
        "syncthing_url": SYNCTHING_URL,
        "syncthing_key_present": bool(sk),
    }


# ---- vault.list ----------------------------------------------------------

@mcp.tool()
def list(path: str = "", depth: int = 1) -> dict[str, Any]:
    """Browse D:\\sinister-vault\\<path>.

    Args:
        path: subpath under vault root, e.g. "repos" or "accounts/operator"
        depth: 1 = immediate children only; 2 = recurse one level; capped at 4.
    """
    log_call("list", path=path[:200], depth=depth)
    if not VAULT_ROOT.exists():
        return {"ok": False, "error": f"vault root not found: {VAULT_ROOT}"}

    target = _safe_join(VAULT_ROOT, path)
    if target is None:
        return {"ok": False, "error": "path escapes vault root or is invalid"}
    if not target.exists():
        return {"ok": False, "error": f"path not found: {target}"}
    if not target.is_dir():
        # Just describe the single file
        return {"ok": True, "root": str(target), "entries": [_entry_for(target)]}

    depth = max(1, min(int(depth or 1), 4))
    entries: list[dict[str, Any]] = []
    truncated = False
    MAX_ENTRIES = 2000
    try:
        for child in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            entries.append(_entry_for(child))
            if depth > 1 and child.is_dir():
                for sub in _walk(child, depth - 1):
                    entries.append(sub)
                    if len(entries) >= MAX_ENTRIES:
                        truncated = True
                        break
            if len(entries) >= MAX_ENTRIES:
                truncated = True
                break
    except PermissionError as e:
        return {"ok": False, "error": f"permission denied: {e}"}

    return {
        "ok": True,
        "root": str(target),
        "depth": depth,
        "count": len(entries),
        "truncated": truncated,
        "entries": entries,
    }


def _walk(start: Path, depth_left: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if depth_left <= 0:
        return out
    try:
        for child in sorted(start.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            e = _entry_for(child)
            try:
                e["rel"] = str(child.relative_to(VAULT_ROOT))
            except Exception:
                pass
            out.append(e)
            if depth_left > 1 and child.is_dir():
                out.extend(_walk(child, depth_left - 1))
    except (PermissionError, OSError):
        pass
    return out


# ---- vault.audit ---------------------------------------------------------

@mcp.tool()
def audit(limit: int = 50, kind: Optional[str] = None) -> dict[str, Any]:
    """Tail the vault daemon's audit log. Optionally filter by event kind."""
    log_call("audit", limit=limit, kind=kind)
    params: dict[str, Any] = {"limit": int(limit)}
    if kind:
        params["kind"] = kind
    ok, data, err = _safe_get(f"{VAULT_DAEMON_URL}/api/vault/audit", params=params)
    if not ok:
        if err == "connection_refused":
            return {"ok": False, "error": OFFLINE_HINT_VAULT}
        return {"ok": False, "error": err or "audit fetch failed"}
    if isinstance(data, dict) and "events" in data:
        return {"ok": True, "events": data["events"][:limit]}
    if isinstance(data, list):
        return {"ok": True, "events": data[:limit]}
    return {"ok": True, "events": [], "raw": data}


# ---- vault.commit / push / pull -----------------------------------------

@mcp.tool()
def commit(repo: str, file_path: str, message: str,
           account: str = "operator") -> dict[str, Any]:
    """Stage + commit + push a single file to a Gitea-backed repo.

    Args:
        repo: bare name (e.g. "knowledge") or "owner/name"
        file_path: absolute path OR path relative to the repo's working tree
        message: commit message
        account: git author identity (used to set local user.name + user.email)
    """
    log_call("commit", repo=repo, account=account)

    repo_dir = _resolve_repo_path(repo)
    if repo_dir is None:
        return {
            "ok": False,
            "error": f"no working copy under {VAULT_ROOT / 'repos'} for repo '{repo}'. "
                     f"Clone it via Gitea first.",
        }

    # Resolve file_path
    fp = Path(file_path)
    if not fp.is_absolute():
        fp = (repo_dir / file_path).resolve()
    if not fp.exists():
        return {"ok": False, "error": f"file not found: {fp}"}
    try:
        rel = fp.resolve().relative_to(repo_dir.resolve())
    except ValueError:
        return {"ok": False, "error": f"file is outside repo working tree: {fp}"}

    # Configure author (local to this repo)
    author_email = f"{account}@vault.local"
    _run_git(["config", "user.name", account], cwd=repo_dir, timeout=10)
    _run_git(["config", "user.email", author_email], cwd=repo_dir, timeout=10)

    # Stage
    code, out, err = _run_git(["add", "--", str(rel)], cwd=repo_dir, timeout=20)
    if code != 0:
        return {"ok": False, "error": f"git add failed: {err.strip() or out.strip()}"}

    # Commit
    code, out, err = _run_git(["commit", "-m", message], cwd=repo_dir, timeout=30)
    if code != 0:
        msg = (err + out).strip()
        if "nothing to commit" in msg.lower():
            return {"ok": True, "noop": True, "reason": "nothing to commit", "repo": repo}
        return {"ok": False, "error": f"git commit failed: {msg}"}

    # Capture sha + branch
    sha = ""
    code, out, _ = _run_git(["rev-parse", "HEAD"], cwd=repo_dir, timeout=10)
    if code == 0:
        sha = out.strip()
    branch = DEFAULT_BRANCH
    code, out, _ = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir, timeout=10)
    if code == 0 and out.strip():
        branch = out.strip()

    # Push (best-effort; commit still counts)
    push_code, push_out, push_err = _run_git(
        ["push", "origin", branch], cwd=repo_dir, timeout=60,
    )
    pushed = (push_code == 0)
    push_msg = (push_err + push_out).strip() if not pushed else ""

    result: dict[str, Any] = {
        "ok": True,
        "sha": sha,
        "repo": repo,
        "branch": branch,
        "file": str(rel).replace("\\", "/"),
        "pushed": pushed,
    }
    if not pushed:
        result["push_error"] = push_msg[:500]
    return result


@mcp.tool()
def push(repo: str, branch: str) -> dict[str, Any]:
    """git push a repo's branch to origin. Returns ok + pushed_commits."""
    log_call("push", repo=repo, branch=branch)
    repo_dir = _resolve_repo_path(repo)
    if repo_dir is None:
        return {"ok": False, "error": f"no working copy for repo '{repo}'"}

    # Count commits ahead of origin/<branch>
    ahead = 0
    code, out, _ = _run_git(
        ["rev-list", "--count", f"origin/{branch}..{branch}"],
        cwd=repo_dir, timeout=15,
    )
    if code == 0 and out.strip().isdigit():
        ahead = int(out.strip())

    code, out, err = _run_git(["push", "origin", branch], cwd=repo_dir, timeout=120)
    if code != 0:
        return {"ok": False, "error": f"git push failed: {(err + out).strip()[:500]}"}
    return {"ok": True, "pushed_commits": ahead, "repo": repo, "branch": branch}


@mcp.tool()
def pull(repo: str, branch: str) -> dict[str, Any]:
    """git pull a repo's branch from origin. Returns ok + new_commits."""
    log_call("pull", repo=repo, branch=branch)
    repo_dir = _resolve_repo_path(repo)
    if repo_dir is None:
        return {"ok": False, "error": f"no working copy for repo '{repo}'"}

    code, before, _ = _run_git(["rev-parse", "HEAD"], cwd=repo_dir, timeout=10)
    head_before = before.strip() if code == 0 else ""

    code, out, err = _run_git(["pull", "--ff-only", "origin", branch],
                              cwd=repo_dir, timeout=120)
    if code != 0:
        return {"ok": False, "error": f"git pull failed: {(err + out).strip()[:500]}"}

    code, after, _ = _run_git(["rev-parse", "HEAD"], cwd=repo_dir, timeout=10)
    head_after = after.strip() if code == 0 else ""

    new = 0
    if head_before and head_after and head_before != head_after:
        code, cnt, _ = _run_git(
            ["rev-list", "--count", f"{head_before}..{head_after}"],
            cwd=repo_dir, timeout=15,
        )
        if code == 0 and cnt.strip().isdigit():
            new = int(cnt.strip())
    return {"ok": True, "new_commits": new, "repo": repo, "branch": branch,
            "head": head_after}


# ---- vault.search --------------------------------------------------------

_SEARCH_SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "venv",
                     ".idea", ".vscode", "dist", "build", ".next", ".cache"}
_SEARCH_EXTS = {".md", ".txt", ".py", ".ts", ".tsx", ".js", ".jsx", ".json",
                ".yaml", ".yml", ".toml", ".ini", ".cfg", ".html", ".css",
                ".rs", ".go", ".java", ".kt", ".rb", ".sh", ".ps1", ".bat",
                ".sql", ".env"}
_MAX_FILE_BYTES = 1_500_000  # skip very large files


@mcp.tool()
def search(query: str, limit: int = 20) -> dict[str, Any]:
    """Substring grep across every repo + the sync folder under <vault>/.

    Pure-Python (no rg dependency). Searches text files only.
    Args:
        query: substring to find (case-insensitive); ignored if empty
        limit: max number of match records to return
    """
    log_call("search", q=query[:80], limit=limit)
    if not query or not query.strip():
        return {"ok": False, "error": "query must be non-empty"}
    if not VAULT_ROOT.exists():
        return {"ok": False, "error": f"vault root not found: {VAULT_ROOT}"}

    needle = query.strip()
    needle_lc = needle.lower()
    needle_re = re.compile(re.escape(needle), re.IGNORECASE)

    results: list[dict[str, Any]] = []
    files_scanned = 0
    limit = max(1, min(int(limit or 20), 500))

    # Search roots: repos + everything else at top level except 'snapshots'
    candidates: list[Path] = []
    for top in (VAULT_ROOT / "repos", VAULT_ROOT / "sync", VAULT_ROOT / "accounts"):
        if top.exists():
            candidates.append(top)
    # If the conventional dirs don't exist, fall back to the whole root
    if not candidates:
        candidates = [VAULT_ROOT]

    for root in candidates:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _SEARCH_SKIP_DIRS]
            for fn in filenames:
                if len(results) >= limit:
                    break
                p = Path(dirpath) / fn
                ext = p.suffix.lower()
                if ext and ext not in _SEARCH_EXTS:
                    continue
                try:
                    if p.stat().st_size > _MAX_FILE_BYTES:
                        continue
                    with p.open("r", encoding="utf-8", errors="ignore") as f:
                        files_scanned += 1
                        for ln, line in enumerate(f, start=1):
                            if needle_lc in line.lower():
                                results.append({
                                    "file": str(p),
                                    "rel": str(p.relative_to(VAULT_ROOT)).replace("\\", "/"),
                                    "line": ln,
                                    "text": needle_re.sub(
                                        lambda m: m.group(0), line.rstrip()
                                    )[:400],
                                })
                                if len(results) >= limit:
                                    break
                except (OSError, UnicodeDecodeError):
                    continue
            if len(results) >= limit:
                break
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break

    return {
        "ok": True,
        "query": needle,
        "files_scanned": files_scanned,
        "match_count": len(results),
        "truncated": len(results) >= limit,
        "results": results,
    }


# ---- vault.sync_status ---------------------------------------------------

@mcp.tool()
def sync_status() -> dict[str, Any]:
    """Read Syncthing folder state. Returns per-folder completion + conflicts."""
    log_call("sync_status")
    key = get_syncthing_key()
    if not key:
        return {
            "ok": False,
            "error": (
                "Syncthing API key not found. Set SYNCTHING_API_KEY or ensure "
                f"{SYNCTHING_CONFIG} exists with an <apikey> element."
            ),
        }
    headers = {"X-API-Key": key}

    # 1. Enumerate folders from /rest/system/config
    ok, cfg, err = _safe_get(f"{SYNCTHING_URL}/rest/system/config", headers=headers)
    if not ok:
        if err == "connection_refused":
            return {"ok": False, "error": OFFLINE_HINT_SYNCTHING}
        return {"ok": False, "error": err or "config fetch failed"}

    folder_ids: list[str] = []
    if isinstance(cfg, dict):
        for f in cfg.get("folders") or []:
            fid = f.get("id")
            if fid:
                folder_ids.append(fid)

    if not folder_ids:
        # Operator may have only configured the "sinister-vault" folder explicitly
        folder_ids = ["sinister-vault"]

    folders_out: list[dict[str, Any]] = []
    for fid in folder_ids:
        ok, st, _ = _safe_get(
            f"{SYNCTHING_URL}/rest/db/status",
            headers=headers, params={"folder": fid},
        )
        if not ok or not isinstance(st, dict):
            folders_out.append({"id": fid, "state": "unknown", "error": "no status"})
            continue
        # Sample fields: state, globalBytes, inSyncBytes, needBytes,
        # needFiles, errors, stateChanged, version, ...
        global_b = st.get("globalBytes") or 0
        sync_b = st.get("inSyncBytes") or 0
        pct = (100.0 * sync_b / global_b) if global_b > 0 else 100.0
        # /rest/db/completion gives a per-folder completion summary
        ok2, comp, _ = _safe_get(
            f"{SYNCTHING_URL}/rest/db/completion",
            headers=headers, params={"folder": fid},
        )
        completion_pct = pct
        if ok2 and isinstance(comp, dict) and "completion" in comp:
            completion_pct = float(comp.get("completion") or pct)
        folders_out.append({
            "id": fid,
            "state": st.get("state"),
            "completion_pct": round(completion_pct, 2),
            "last_scan": st.get("stateChanged"),
            "conflicts": int(st.get("needFiles") or 0),
            "errors": int(st.get("errors") or 0),
            "global_bytes": global_b,
            "in_sync_bytes": sync_b,
        })

    return {"ok": True, "folders": folders_out}


# ---- vault.accounts ------------------------------------------------------

@mcp.tool()
def accounts() -> dict[str, Any]:
    """Enumerate accounts under D:\\sinister-vault\\accounts\\<name>.

    Each account dir is expected to contain a JSON metadata file
    (e.g. account.json) with hwid + last_seen — but absent that we still
    surface the dir name + mtime so callers can see what exists.
    """
    log_call("accounts")
    accounts_dir = VAULT_ROOT / "accounts"
    if not accounts_dir.exists():
        return {"ok": True, "accounts": [], "note": f"{accounts_dir} does not exist yet"}

    out: list[dict[str, Any]] = []
    try:
        for child in sorted(accounts_dir.iterdir()):
            if not child.is_dir():
                continue
            entry: dict[str, Any] = {"name": child.name}
            # Try standard metadata files
            for meta_name in ("account.json", "meta.json", "info.json"):
                mp = child / meta_name
                if mp.exists():
                    try:
                        meta = json.loads(mp.read_text(encoding="utf-8"))
                        if isinstance(meta, dict):
                            entry["hwid_bound"] = bool(meta.get("hwid") or meta.get("hwid_bound"))
                            entry["last_seen"] = meta.get("last_seen")
                            entry["meta_file"] = mp.name
                    except Exception:
                        pass
                    break
            if "hwid_bound" not in entry:
                entry["hwid_bound"] = (child / ".hwid").exists()
            if "last_seen" not in entry:
                try:
                    entry["last_seen"] = datetime.fromtimestamp(
                        child.stat().st_mtime, tz=timezone.utc,
                    ).isoformat()
                except Exception:
                    entry["last_seen"] = None
            out.append(entry)
    except PermissionError as e:
        return {"ok": False, "error": f"permission denied: {e}"}

    return {"ok": True, "accounts": out, "count": len(out)}


# ---- vault.snapshot ------------------------------------------------------

@mcp.tool()
def snapshot(subtree: str = "repos") -> dict[str, Any]:
    """Trigger an on-demand snapshot via the vault daemon."""
    log_call("snapshot", subtree=subtree)
    ok, data, err = _safe_post(
        f"{VAULT_DAEMON_URL}/api/vault/snapshot",
        json_body={"subtree": subtree},
    )
    if not ok:
        if err == "connection_refused":
            return {"ok": False, "error": OFFLINE_HINT_VAULT}
        return {"ok": False, "error": err or "snapshot request failed"}
    if isinstance(data, dict):
        return {
            "ok": bool(data.get("ok", True)),
            "snapshot_dir": data.get("snapshot_dir"),
            "files": data.get("files"),
            "bytes": data.get("bytes"),
            "raw": data,
        }
    return {"ok": True, "raw": data}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
