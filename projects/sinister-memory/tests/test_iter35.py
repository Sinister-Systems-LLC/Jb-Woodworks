# Author: RKOJ-ELENO :: 2026-05-25
"""Iter-35 commit-isolated regression tests."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _git(args: list[str], cwd: Path) -> str:
    p = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True, timeout=10)
    if p.returncode != 0:
        raise RuntimeError(f"git {args} failed: {p.stderr}")
    return p.stdout.strip()


def test_commit_isolated_creates_commit_without_touching_head(tmp_path: Path) -> None:
    """Core invariant: commit_isolated must NEVER touch the working tree's HEAD."""
    from sinister_memory import commit_isolated

    # Setup: fresh git repo with one commit
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "test"], repo)
    (repo / "seed.md").write_text("initial", encoding="utf-8")
    _git(["add", "seed.md"], repo)
    _git(["commit", "-q", "-m", "initial"], repo)
    parent_sha = _git(["rev-parse", "HEAD"], repo)
    head_branch_before = _git(["symbolic-ref", "--short", "HEAD"], repo)

    # New file to commit via plumbing
    (repo / "new-file.md").write_text("commit-isolated payload", encoding="utf-8")

    result = commit_isolated.commit_isolated(
        repo_root=repo,
        parent_sha=parent_sha,
        branch_name="agent/test/iso-test",
        files=["new-file.md"],
        message="iso test commit",
        push=False,
    )
    assert result["ok"], f"expected ok=True; got {result}"
    assert result["commit_sha"] != parent_sha
    assert result["files_count"] == 1

    # HEAD must NOT have moved
    head_branch_after = _git(["symbolic-ref", "--short", "HEAD"], repo)
    head_sha_after = _git(["rev-parse", "HEAD"], repo)
    assert head_branch_after == head_branch_before, (
        f"HEAD branch changed: was {head_branch_before}, now {head_branch_after}"
    )
    assert head_sha_after == parent_sha, "HEAD SHA must not move"

    # But the new branch must exist + point to the new commit
    new_branch_sha = _git(["rev-parse", "agent/test/iso-test"], repo)
    assert new_branch_sha == result["commit_sha"]


def test_commit_isolated_rejects_missing_files(tmp_path: Path) -> None:
    from sinister_memory import commit_isolated
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "t@t"], repo)
    _git(["config", "user.name", "t"], repo)
    (repo / "seed.md").write_text("x", encoding="utf-8")
    _git(["add", "seed.md"], repo)
    _git(["commit", "-q", "-m", "x"], repo)
    parent = _git(["rev-parse", "HEAD"], repo)

    result = commit_isolated.commit_isolated(
        repo_root=repo,
        parent_sha=parent,
        branch_name="agent/test/missing",
        files=["seed.md", "nonexistent.md"],
        message="should fail",
    )
    assert result["ok"] is False
    assert "missing" in result.get("error", "").lower()


def test_commit_isolated_with_empty_files_list(tmp_path: Path) -> None:
    from sinister_memory import commit_isolated
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "t@t"], repo)
    _git(["config", "user.name", "t"], repo)
    (repo / "seed.md").write_text("x", encoding="utf-8")
    _git(["add", "seed.md"], repo)
    _git(["commit", "-q", "-m", "x"], repo)
    parent = _git(["rev-parse", "HEAD"], repo)

    result = commit_isolated.commit_isolated(
        repo_root=repo,
        parent_sha=parent,
        branch_name="agent/test/empty",
        files=[],
        message="should fail",
    )
    assert result["ok"] is False
    assert "no files" in result.get("error", "").lower()


def test_iter38_commit_isolated_push_failure_reports_clearly(tmp_path: Path) -> None:
    """Iter-38 contradict-fix for iter-35: push to a NONEXISTENT remote must
    return ok=False with a clear error so callers can chain conditionally.
    Prevents the silent committed-but-not-pushed footgun.
    """
    from sinister_memory import commit_isolated

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "t@t"], repo)
    _git(["config", "user.name", "t"], repo)
    (repo / "seed.md").write_text("x", encoding="utf-8")
    _git(["add", "seed.md"], repo)
    _git(["commit", "-q", "-m", "x"], repo)
    parent = _git(["rev-parse", "HEAD"], repo)

    (repo / "new.md").write_text("payload", encoding="utf-8")
    result = commit_isolated.commit_isolated(
        repo_root=repo,
        parent_sha=parent,
        branch_name="agent/test/push-fail",
        files=["new.md"],
        message="should commit but push fail",
        push=True,
        remote="origin-nonexistent",
    )
    # Commit itself succeeded (local branch updated) but push failed
    assert result["ok"] is False, f"push to nonexistent remote should fail; got {result}"
    assert "error" in result, "must report error"
    assert "push" in result["error"].lower(), f"error should mention push; got {result['error']}"
    # Even though push failed, the COMMIT was created locally (caller can recover)
    assert "commit_sha" in result
    assert len(result["commit_sha"]) == 40
    # And push_result has the structured failure details
    pr = result.get("push_result", {})
    assert pr.get("ok") is False
    assert pr.get("rc") != 0
