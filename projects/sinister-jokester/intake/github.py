"""GitHub URL intake.

Author: RKOJ-ELENO :: 2026-05-26

Given a `https://github.com/owner/repo` URL:
  1. Compute a stable id (`gh-<owner>-<repo>-<8-char-hash>`).
  2. Shallow-clone (depth=1) into `vault/intake/<id>/clone/`.
  3. Extract metadata via `gh repo view --json` (falls back to git-only fields if `gh` unavailable).
  4. Return a dict ready to be inserted into the intake_items row.

No network call unless the URL is actually intaken. Re-intake is idempotent (skips if dir exists, unless --force).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_INTAKE = REPO_ROOT / "vault" / "intake"

GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/#?]+?)(?:\.git)?/?(?:[#?].*)?$",
    re.IGNORECASE,
)


def parse_github_url(url: str) -> tuple[str, str]:
    m = GITHUB_URL_RE.match(url.strip())
    if not m:
        raise ValueError(f"not a github URL: {url!r}")
    return m.group("owner"), m.group("repo")


def compute_id(owner: str, repo: str) -> str:
    h = hashlib.sha1(f"{owner}/{repo}".encode("utf-8")).hexdigest()[:8]
    safe_owner = re.sub(r"[^a-z0-9]+", "-", owner.lower()).strip("-")
    safe_repo = re.sub(r"[^a-z0-9]+", "-", repo.lower()).strip("-")
    return f"gh-{safe_owner}-{safe_repo}-{h}"


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 60) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _gh_metadata(owner: str, repo: str) -> dict[str, Any]:
    """Best-effort metadata via `gh` CLI. Returns {} if gh missing or auth fails."""
    if shutil.which("gh") is None:
        return {}
    fields = (
        "name,description,stargazerCount,licenseInfo,primaryLanguage,"
        "pushedAt,createdAt,isArchived,isFork,defaultBranchRef,repositoryTopics,url"
    )
    rc, out, err = _run(
        ["gh", "repo", "view", f"{owner}/{repo}", "--json", fields],
        timeout=30,
    )
    if rc != 0:
        return {"_gh_error": err.strip()}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"_gh_error": "json-decode-failed"}


def _git_metadata(clone_dir: Path) -> dict[str, Any]:
    """Lightweight metadata pulled straight from the cloned repo."""
    meta: dict[str, Any] = {}
    if not (clone_dir / ".git").exists():
        return meta
    rc, out, _ = _run(["git", "log", "-1", "--format=%H|%cI|%s"], cwd=clone_dir, timeout=10)
    if rc == 0 and out.strip():
        sha, ci, subj = out.strip().split("|", 2)
        meta["last_commit_sha"] = sha
        meta["last_commit_ci"] = ci
        meta["last_commit_subject"] = subj
    rc, out, _ = _run(["git", "rev-list", "--count", "HEAD"], cwd=clone_dir, timeout=10)
    if rc == 0 and out.strip().isdigit():
        meta["commit_count_shallow"] = int(out.strip())
    return meta


def _read_readme(clone_dir: Path) -> str:
    for name in ("README.md", "README.rst", "README.txt", "README", "readme.md"):
        p = clone_dir / name
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:20_000]
            except OSError:
                return ""
    return ""


def intake(url: str, force: bool = False, shallow: bool = True) -> dict[str, Any]:
    owner, repo = parse_github_url(url)
    item_id = compute_id(owner, repo)
    intake_dir = VAULT_INTAKE / item_id
    clone_dir = intake_dir / "clone"

    intake_dir.mkdir(parents=True, exist_ok=True)

    if clone_dir.exists() and not force:
        clone_status = "already-present"
    else:
        if clone_dir.exists():
            shutil.rmtree(clone_dir, ignore_errors=True)
        cmd = ["git", "clone"]
        if shallow:
            cmd += ["--depth", "1"]
        cmd += [f"https://github.com/{owner}/{repo}.git", str(clone_dir)]
        rc, _, err = _run(cmd, timeout=180)
        if rc != 0:
            return {
                "id": item_id,
                "source_url": url,
                "source_type": "github",
                "intake_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "status": "pending",
                "title": f"{owner}/{repo}",
                "short_summary": f"clone-failed: {err.strip()[:200]}",
                "raw_metadata_json": json.dumps({"clone_error": err.strip()}),
                "clone_dir": str(clone_dir),
                "intake_dir": str(intake_dir),
                "readme_excerpt": "",
                "_intake_ok": False,
            }
        clone_status = "fresh-clone"

    gh_meta = _gh_metadata(owner, repo)
    git_meta = _git_metadata(clone_dir)
    readme = _read_readme(clone_dir)

    title = gh_meta.get("name") or f"{owner}/{repo}"
    short_summary = (gh_meta.get("description") or "").strip()
    if not short_summary and readme:
        first_para = readme.strip().split("\n\n", 1)[0].strip()
        short_summary = first_para[:200].replace("\n", " ")

    topics = gh_meta.get("repositoryTopics") or []
    tag_names: list[str] = []
    for t in topics:
        if isinstance(t, dict):
            n = t.get("name")
            if n:
                tag_names.append(n)
        elif isinstance(t, str):
            tag_names.append(t)
    if gh_meta.get("primaryLanguage"):
        lang = gh_meta["primaryLanguage"]
        if isinstance(lang, dict) and lang.get("name"):
            tag_names.append(f"lang:{lang['name'].lower()}")
        elif isinstance(lang, str):
            tag_names.append(f"lang:{lang.lower()}")

    raw_meta = {
        "owner": owner,
        "repo": repo,
        "clone_status": clone_status,
        "gh": gh_meta,
        "git": git_meta,
        "readme_chars": len(readme),
    }

    return {
        "id": item_id,
        "source_url": f"https://github.com/{owner}/{repo}",
        "source_type": "github",
        "intake_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "analyzing",
        "title": title,
        "short_summary": short_summary,
        "tags": ",".join(sorted(set(tag_names))),
        "raw_metadata_json": json.dumps(raw_meta, default=str),
        "clone_dir": str(clone_dir),
        "intake_dir": str(intake_dir),
        "readme_excerpt": readme[:4_000],
        "_intake_ok": True,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    result = intake(args.url, force=args.force)
    result.pop("readme_excerpt", None)
    print(json.dumps(result, indent=2, default=str))
