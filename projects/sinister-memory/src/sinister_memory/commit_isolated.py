# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: commit-isolated.

Codifies the cross-agent monorepo branch-pointer collision recovery pattern
(`cross-agent-monorepo-branch-collision-recovery-2026-05-25` doctrine) as a
reusable CLI primitive. Pattern proven across iter-31 + iter-34 commits;
turns a 7-command sequence into one call.

Why: multiple parallel agents share `.git/` in this monorepo. The default
`git add` + `git commit` race against each other agent's `git checkout`,
producing dangerous outcomes (deletion-bomb stages from sparse worktrees;
silent lost stages from concurrent reset). The recovery pattern uses an
isolated `GIT_INDEX_FILE` + low-level plumbing (`read-tree` / `update-index` /
`write-tree` / `commit-tree` / `branch -f` / `push`) that never touches the
shared `.git/HEAD` or `.git/index`. Zero collision risk; zero impact on
concurrent agents.

Public API:
  commit_isolated(parent_sha, branch_name, files, message, push=False,
                  remote="origin") -> dict

CLI:
  sinister-memory commit-isolated --parent <sha> --branch <name>
    --message-file <path> --files <file1> [<file2> ...] [--push] [--remote origin]
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence


def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> tuple[int, str, str]:
    """Subprocess wrapper returning (rc, stdout, stderr)."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    p = subprocess.run(
        cmd, cwd=str(cwd), env=full_env,
        capture_output=True, text=True, timeout=60,
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def commit_isolated(
    repo_root: Path,
    parent_sha: str,
    branch_name: str,
    files: Sequence[str],
    message: str,
    push: bool = False,
    remote: str = "origin",
) -> dict:
    """Build + commit a tree via git plumbing with an isolated GIT_INDEX_FILE.

    Args:
      repo_root  : git repo root (where .git/ lives)
      parent_sha : SHA of parent commit (e.g. "abc1234" or full SHA); your branch
                   will be set to a new commit with this as parent
      branch_name: target branch name (e.g. "agent/my-lane/topic-2026-05-25")
      files      : list of repo-relative paths to stage (each must exist on disk)
      message    : commit message body
      push       : if True, push the branch to `remote` after commit
      remote     : remote name (default "origin")

    Returns dict: {
      ok, commit_sha, parent_sha, branch, tree_sha, files_count, push_result?, error?
    }
    """
    repo_root = Path(repo_root)
    if not (repo_root / ".git").exists():
        return {"ok": False, "error": f".git not found at {repo_root}"}

    files = list(files)
    if not files:
        return {"ok": False, "error": "no files provided"}

    # Verify all files exist on disk before any git ops
    missing = [f for f in files if not (repo_root / f).exists()]
    if missing:
        return {"ok": False, "error": f"missing files: {missing[:3]}{'...' if len(missing)>3 else ''}"}

    # Resolve parent_sha to full SHA
    rc, full_parent, err = _run(["git", "rev-parse", parent_sha], repo_root)
    if rc != 0:
        return {"ok": False, "error": f"git rev-parse {parent_sha} failed: {err}"}

    # Isolated index file
    fd, idx_path = tempfile.mkstemp(prefix="sm-commit-isolated-", suffix=".idx")
    os.close(fd)
    os.unlink(idx_path)  # git read-tree needs to create it fresh
    env = {"GIT_INDEX_FILE": idx_path}

    try:
        # 1. Seed isolated index from parent's tree
        rc, _, err = _run(["git", "read-tree", full_parent], repo_root, env=env)
        if rc != 0:
            return {"ok": False, "error": f"git read-tree {full_parent} failed: {err}"}

        # 2. Add target files to isolated index
        rc, _, err = _run(
            ["git", "update-index", "--add", "--"] + files,
            repo_root, env=env,
        )
        if rc != 0:
            return {"ok": False, "error": f"git update-index failed: {err}"}

        # 3. Write tree from isolated index
        rc, tree_sha, err = _run(["git", "write-tree"], repo_root, env=env)
        if rc != 0 or not tree_sha:
            return {"ok": False, "error": f"git write-tree failed: {err}"}

        # 4. Build commit-tree (message via stdin to handle special chars cleanly)
        commit_proc = subprocess.run(
            ["git", "commit-tree", tree_sha, "-p", full_parent],
            cwd=str(repo_root), input=message, text=True,
            capture_output=True, timeout=30,
        )
        if commit_proc.returncode != 0:
            return {"ok": False, "error": f"git commit-tree failed: {commit_proc.stderr.strip()}"}
        commit_sha = commit_proc.stdout.strip()

        # 5. Update branch ref (force, since we're often advancing from a
        # previously-pushed commit OR creating a new branch)
        rc, _, err = _run(
            ["git", "branch", "-f", branch_name, commit_sha],
            repo_root,
        )
        if rc != 0:
            return {"ok": False, "error": f"git branch -f failed: {err}", "commit_sha": commit_sha}

        result = {
            "ok": True,
            "commit_sha": commit_sha,
            "parent_sha": full_parent,
            "tree_sha": tree_sha,
            "branch": branch_name,
            "files_count": len(files),
        }

        # 6. Optional push
        if push:
            rc, out, err = _run(["git", "push", remote, branch_name], repo_root)
            push_ok = (rc == 0)
            result["push_result"] = {
                "ok": push_ok,
                "rc": rc,
                "stdout": out[-500:],  # last 500 chars
                "stderr": err[-500:],
                "remote": remote,
            }
            if not push_ok:
                result["ok"] = False
                result["error"] = f"push failed: {err}"

        return result
    finally:
        # Clean up isolated index
        try:
            os.unlink(idx_path)
        except OSError:
            pass
