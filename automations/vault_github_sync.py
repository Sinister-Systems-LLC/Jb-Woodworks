#!/usr/bin/env python3
"""vault_github_sync.py — Bidirectional sync between Sanctum vault mirror and GitHub.

Author: RKOJ-ELENO :: 2026-05-25

Composes with:
  - sinister-vault-architecture (vault is the canonical mirror substrate)
  - single-repo-push-policy-2026-05-25 (always push agent/<slug>/<topic>, never main directly)
  - version-snapshot-disaster-recovery-doctrine-2026-05-25 (vault snapshots before destructive ops)
  - automate-everything-no-operator-admin-2026-05-25 (zero operator clicks)

Actions:
  --scan              detect drift; write delta tables to log; print summary
  --push-to-github    copy vault-newer files into working tree, commit, push to agent branch
  --pull-from-github  fetch origin, copy github-newer files into vault
  --auto              scan; if no conflicts run push + pull; if conflicts log + skip
  --install-schtask   register SinisterVaultGitHubSync schtask (15 min cadence)
  --dry-run           print plan without mutating

Conflict resolution policy (deterministic):
  Path-prefix routing —
    _shared-memory/   -> prefer VAULT  (live runtime state, vault is source of truth)
    automations/      -> prefer GITHUB (CI-reviewed scripts)
    docs/             -> prefer GITHUB (versioned documentation)
    deploy/           -> prefer GITHUB (release artifacts)
    versions/         -> prefer GITHUB (immutable snapshots)
    CLAUDE.md         -> prefer GITHUB (operator-canonical doctrine)
    *everything else* -> CONFLICT (operator decides; logged + skipped)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_ROOT = REPO_ROOT / "_vault" / "sanctum-mirror"
LOG_PATH = REPO_ROOT / "_shared-memory" / "vault-github-sync-log.jsonl"
SCHTASK_NAME = "SinisterVaultGitHubSync"

# Path prefixes that govern conflict resolution. Order matters (longest match first).
PREFER_VAULT = ("_shared-memory/",)
PREFER_GITHUB = (
    "automations/",
    "docs/",
    "deploy/",
    "versions/",
    "CLAUDE.md",
)

# Walk exclusions (heavy / generated / not vault candidates).
EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "_vault",            # vault never mirrors itself
    "_vault-backups",
    "_tmp",
}


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _machine_id() -> str:
    return os.environ.get("SINISTER_MACHINE_ID") or socket.gethostname().lower().replace(" ", "-")


def _log(event: str, **fields) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": _now_iso(), "event": event, **fields}
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _walk_tree(root: Path) -> Dict[str, str]:
    """Return {relpath_posix: sha256} for every file under root, skipping EXCLUDE_DIRS."""
    out: Dict[str, str] = {}
    if not root.exists():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded dirs in-place
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                rel = p.relative_to(root).as_posix()
                out[rel] = _sha256(p)
            except (OSError, ValueError):
                continue
    return out


def _classify(relpath: str) -> str:
    """Return 'vault' / 'github' / 'conflict' for given path under conflict."""
    if relpath in PREFER_GITHUB or any(relpath.startswith(p) for p in PREFER_GITHUB if p.endswith("/")):
        return "github"
    if any(relpath.startswith(p) for p in PREFER_VAULT):
        return "vault"
    return "conflict"


def _vault_machine_dir() -> Path:
    return VAULT_ROOT / _machine_id()


def _scan() -> Dict[str, List[str]]:
    """Compute three delta lists: vault_newer, github_newer, conflicts."""
    vault_dir = _vault_machine_dir()
    if not vault_dir.exists():
        _log("scan.skip", reason="vault mirror not yet created", path=str(vault_dir))
        return {"vault_newer": [], "github_newer": [], "conflicts": [], "vault_missing": True}

    repo_files = _walk_tree(REPO_ROOT)
    vault_files = _walk_tree(vault_dir)

    vault_newer: List[str] = []
    github_newer: List[str] = []
    conflicts: List[str] = []

    for rel, vhash in vault_files.items():
        if rel not in repo_files:
            vault_newer.append(rel)
            continue
        if vhash == repo_files[rel]:
            continue
        # Both exist + differ — apply policy
        verdict = _classify(rel)
        if verdict == "vault":
            vault_newer.append(rel)
        elif verdict == "github":
            github_newer.append(rel)
        else:
            conflicts.append(rel)

    for rel in repo_files:
        if rel not in vault_files:
            github_newer.append(rel)

    return {
        "vault_newer": sorted(vault_newer),
        "github_newer": sorted(github_newer),
        "conflicts": sorted(conflicts),
        "vault_missing": False,
    }


def _git(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=REPO_ROOT, capture_output=True, text=True, check=check)


def _current_branch() -> str:
    try:
        return _git(["branch", "--show-current"]).stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def _ensure_agent_branch() -> str:
    """Single-repo push policy: never push to main directly."""
    branch = _current_branch()
    if branch and branch != "main" and branch != "master":
        return branch
    new_branch = f"agent/sinister-sanctum/vault-sync-{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    _git(["checkout", "-b", new_branch])
    return new_branch


def _push_to_github(delta: Dict[str, List[str]], dry_run: bool) -> int:
    files = delta["vault_newer"]
    if not files:
        print("[push] nothing to push")
        return 0
    vault_dir = _vault_machine_dir()
    print(f"[push] {len(files)} files vault->github")
    if dry_run:
        for f in files[:20]:
            print(f"  +{f}")
        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more")
        _log("push.dryrun", count=len(files))
        return 0
    branch = _ensure_agent_branch()
    for rel in files:
        src = vault_dir / rel
        dst = REPO_ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dst)
            _git(["add", "--", rel], check=False)
    commit_msg = f"vault-sync: {len(files)} files updated from vault ({_machine_id()})"
    res = _git(["commit", "-m", commit_msg], check=False)
    if res.returncode != 0 and "nothing to commit" not in (res.stdout + res.stderr):
        _log("push.commit_fail", stderr=res.stderr[:500])
        return 2
    push = _git(["push", "-u", "origin", branch], check=False)
    _log("push.done", branch=branch, count=len(files), push_rc=push.returncode)
    return 0 if push.returncode == 0 else 3


def _pull_from_github(delta: Dict[str, List[str]], dry_run: bool) -> int:
    files = delta["github_newer"]
    if not files:
        print("[pull] nothing to pull")
        return 0
    print(f"[pull] {len(files)} files github->vault")
    if dry_run:
        for f in files[:20]:
            print(f"  +{f}")
        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more")
        _log("pull.dryrun", count=len(files))
        return 0
    _git(["fetch", "origin"], check=False)
    vault_dir = _vault_machine_dir()
    vault_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for rel in files:
        src = REPO_ROOT / rel
        if not src.exists():
            continue
        dst = vault_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    _log("pull.done", count=copied)
    return 0


def _install_schtask() -> int:
    script_path = Path(__file__).resolve()
    cmd_str = f'python "{script_path}" --auto'
    args = [
        "schtasks.exe", "/Create", "/F",
        "/SC", "MINUTE", "/MO", "15",
        "/TN", SCHTASK_NAME,
        "/TR", cmd_str,
        "/RL", "LIMITED",
    ]
    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[schtask] FAIL: {res.stderr.strip()}", file=sys.stderr)
        _log("schtask.fail", stderr=res.stderr[:500])
        return res.returncode
    print(f"[schtask] registered {SCHTASK_NAME} (15-min cadence)")
    _log("schtask.installed", name=SCHTASK_NAME)
    return 0


def _print_summary(delta: Dict[str, List[str]]) -> None:
    if delta.get("vault_missing"):
        print(f"[scan] vault mirror not yet present at {_vault_machine_dir()} (Sub-M may not have mirrored yet) — nothing to compare")
        return
    print(f"[scan] vault_newer={len(delta['vault_newer'])} github_newer={len(delta['github_newer'])} conflicts={len(delta['conflicts'])}")
    if delta["conflicts"]:
        print("[scan] CONFLICTS (operator must resolve):")
        for c in delta["conflicts"][:10]:
            print(f"  !{c}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Vault <-> GitHub bidirectional sync")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--push-to-github", action="store_true")
    ap.add_argument("--pull-from-github", action="store_true")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--install-schtask", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.install_schtask:
        return _install_schtask()

    if not any([args.scan, args.push_to_github, args.pull_from_github, args.auto]):
        ap.print_help()
        return 0

    delta = _scan()
    _log("scan", vault_newer=len(delta["vault_newer"]),
         github_newer=len(delta["github_newer"]),
         conflicts=len(delta["conflicts"]),
         vault_missing=delta.get("vault_missing", False))
    _print_summary(delta)

    if delta.get("vault_missing"):
        return 0

    rc = 0
    if args.scan and not (args.push_to_github or args.pull_from_github or args.auto):
        return 0

    if args.auto:
        if delta["conflicts"]:
            print(f"[auto] {len(delta['conflicts'])} conflicts — skipping push/pull; operator must resolve")
            _log("auto.blocked", conflicts=len(delta["conflicts"]))
            return 0
        rc |= _push_to_github(delta, args.dry_run)
        rc |= _pull_from_github(delta, args.dry_run)
        return rc

    if args.push_to_github:
        rc |= _push_to_github(delta, args.dry_run)
    if args.pull_from_github:
        rc |= _pull_from_github(delta, args.dry_run)
    return rc


if __name__ == "__main__":
    sys.exit(main())
