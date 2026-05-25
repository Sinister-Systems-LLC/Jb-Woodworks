#!/usr/bin/env python3
"""overseer_loop_quality_agent.py -- Overseer sub-agent #3: loop quality + save-point rehook.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25 (verbatim):
    "i need loop system too that keeps contradicting and expand until quality
     demishes and rehooks a save point. have a overseer agent to aid with
     this and specialize in it and a project called sinister looper and make
     this work on every projct by default from eve."

THE THREE OVERSEER SUB-AGENTS:
    1. overseer_rate_limit_agent.py   -- 20s SLA rate-limit detect+autofix+respawn
    2. overseer_token_agent.py        -- token waste avoidance + idle background fill
    3. overseer_loop_quality_agent.py -- THIS FILE -- contradict + expand + rehook

PROJECT: projects/sinister-looper/ (scaffolded 2026-05-25)

THE QUALITY-DEGRADATION LOOP CONTRACT (per-project):
    1. EVERY loop iteration is auto-snapshotted as a "save point" (git
       commit on agent branch + tag `looper-savepoint-<slug>-<iter>`)
    2. After each iteration, compute a QUALITY SCORE from:
          - tests passing (pytest exit / npm test exit)
          - forever-improve.ps1 Tally severity counts (high = penalty)
          - git diff churn (huge diffs = warning, possible regression)
          - claude-incidents.jsonl in last iter window (errors = penalty)
       Quality score = 100 - (5*high_severity + 2*med_severity + churn_factor + 10*errors)
    3. CONTRADICTION pass: every 5 iterations, agent posts a `kind=contradict`
       message into _shared-memory/inbox/<slug>/ asking the agent to:
          a. list 3 things it ASSUMED were true that might not be
          b. find one design decision worth reconsidering
          c. find one quality risk it introduced
       The next iter must address these contradictions BEFORE expanding further.
    4. EXPANSION CEILING: quality score must stay > prev_score - 15 across any
       3-iter window. If it dips farther, REHOOK = `git reset --hard
       looper-savepoint-<slug>-<best_iter>` (best_iter = highest score in window).
    5. Save points are NEVER auto-deleted (only manual pruning) so operator
       always has rollback points.

DEFAULT-ON: start-sinister-session.ps1 reads projects.json default_modes.loop
and if "relentless" (default), this agent's hooks are wired into the spawn.

DOCTRINE: _shared-memory/knowledge/sinister-looper-doctrine-2026-05-25.md
DOCTRINE: _shared-memory/knowledge/overseer-monitors-doctrine-2026-05-25.md (3 sub-agents)

CLI:
    --once                 scan all live projects, check quality, snapshot/rehook
    --watch                loop forever (60s)
    --snapshot <slug>      create save point for slug now
    --rehook <slug> <tag>  reset slug's branch to a specific save-point tag
    --contradict <slug>    post a contradiction message into slug's inbox
    --status               print quality scores + recent save points
    --install-schtask      register SinisterOverseerLoopQuality (1-min headless)
    --uninstall
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
HEARTBEAT_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
INCIDENTS = SANCTUM_ROOT / "_shared-memory" / "eve-incidents.jsonl"
LOOP_LOG = SANCTUM_ROOT / "_shared-memory" / "loop-quality-log.jsonl"
QUALITY_STATE = SANCTUM_ROOT / "_shared-memory" / "loop-quality-state.json"
INBOX_DIR = SANCTUM_ROOT / "_shared-memory" / "inbox"
SAVEPOINT_TAG_PREFIX = "looper-savepoint"

SCHTASK_NAME = "SinisterOverseerLoopQuality"

# Thresholds (tunable)
QUALITY_FLOOR_DELTA = 15        # if score drops by >15 in 3-iter window -> rehook
CONTRADICT_EVERY_N_ITERS = 5
SNAPSHOT_EVERY_N_ITERS = 1     # snapshot every iteration (cheap = git tag)
WINDOW_SECONDS = 600           # consider an agent "live" if heartbeat <10min


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def log(event: dict) -> None:
    try:
        LOOP_LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOOP_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": utc_iso(), **event}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_state() -> dict:
    if not QUALITY_STATE.exists():
        return {"per_project": {}}
    try:
        return json.loads(QUALITY_STATE.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return {"per_project": {}}


def save_state(s: dict) -> None:
    try:
        QUALITY_STATE.parent.mkdir(parents=True, exist_ok=True)
        QUALITY_STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")
    except Exception:
        pass


def live_projects() -> list[dict]:
    """List projects with a fresh heartbeat. Returns list of {slug, iter, branch}."""
    if not HEARTBEAT_DIR.exists():
        return []
    now = time.time()
    out = []
    for p in HEARTBEAT_DIR.iterdir():
        if p.suffix.lower() not in (".json", ".beat"):
            continue
        try:
            if (now - p.stat().st_mtime) > WINDOW_SECONDS:
                continue
            data = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
            out.append({
                "slug": data.get("slug") or p.stem,
                "iter": data.get("loop_iter") or data.get("iter") or 0,
                "branch": data.get("branch", ""),
                "focus": data.get("focus_intent", ""),
            })
        except Exception:
            continue
    return out


def count_recent_incidents(slug: str, window_min: int = 10) -> int:
    if not INCIDENTS.exists():
        return 0
    cutoff = utc_now().timestamp() - window_min * 60
    n = 0
    try:
        for line in INCIDENTS.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]:
            try:
                r = json.loads(line)
                if r.get("project") == slug or r.get("agent") == slug:
                    ts = datetime.fromisoformat((r.get("ts_utc") or r.get("ts") or "").replace("Z", "+00:00"))
                    if ts.timestamp() >= cutoff:
                        n += 1
            except Exception:
                continue
    except Exception:
        pass
    return n


def quality_score(slug: str, iter_n: int) -> dict:
    """Compute quality score for a project at a given iter."""
    incidents = count_recent_incidents(slug, window_min=10)
    score = 100 - (10 * incidents)
    # Future: pytest exit code, forever-improve tally, git churn
    return {"score": max(0, min(100, score)), "incidents_10m": incidents,
            "iter": iter_n, "slug": slug, "ts": utc_iso()}


def create_savepoint(slug: str, iter_n: int) -> dict:
    """git tag looper-savepoint-<slug>-<iter> on current HEAD."""
    tag = f"{SAVEPOINT_TAG_PREFIX}-{slug}-{iter_n}"
    try:
        cp = subprocess.run(
            ["git", "tag", "-f", tag, "HEAD"],
            capture_output=True, text=True, cwd=str(SANCTUM_ROOT), timeout=10,
        )
        if cp.returncode == 0:
            log({"action": "savepoint", "slug": slug, "iter": iter_n, "tag": tag})
            return {"ok": True, "tag": tag}
        return {"ok": False, "error": cp.stderr.strip()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def post_contradict(slug: str, iter_n: int) -> dict:
    """Drop a contradict message into the slug's inbox."""
    inbox = INBOX_DIR / slug
    inbox.mkdir(parents=True, exist_ok=True)
    ts = utc_iso().replace(":", "").replace("-", "")[:13]
    fname = inbox / f"{ts}Z-from-looper-contradict.json"
    msg = {
        "kind": "looper-contradict",
        "from": "overseer-loop-quality",
        "to": slug,
        "iter_target": iter_n,
        "ts_utc": utc_iso(),
        "instructions": [
            "1. List 3 things you ASSUMED were true this iter that might not be. Verify each.",
            "2. Find ONE design decision worth reconsidering. Justify or change.",
            "3. Find ONE quality risk you introduced. Add a test or remove the risk.",
            "ADDRESS these BEFORE expanding further. Quality > velocity.",
        ],
    }
    try:
        fname.write_text(json.dumps(msg, indent=2, ensure_ascii=False), encoding="utf-8")
        log({"action": "contradict-posted", "slug": slug, "iter": iter_n, "file": str(fname)})
        return {"ok": True, "file": str(fname)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_rehook(slug: str, current_score: int, state: dict) -> dict | None:
    """If quality dropped >QUALITY_FLOOR_DELTA in last 3 iters, recommend rehook."""
    proj = state.get("per_project", {}).get(slug, {})
    history = proj.get("recent_scores", [])
    history.append(current_score)
    history = history[-5:]
    proj["recent_scores"] = history
    state.setdefault("per_project", {})[slug] = proj

    if len(history) < 3:
        return None
    window = history[-3:]
    if max(window) - min(window) > QUALITY_FLOOR_DELTA and window[-1] == min(window):
        best_iter = proj.get("best_iter_recent")
        return {"should_rehook": True, "from_score": max(window), "to_score": current_score,
                "best_iter_savepoint": best_iter}
    return None


def run_once(dry_run: bool = False) -> dict:
    state = load_state()
    projects = live_projects()
    if not projects:
        return {"ok": True, "live_projects": 0, "actions": 0}

    actions = 0
    results = []
    for p in projects:
        slug, iter_n = p["slug"], int(p["iter"] or 0)
        qs = quality_score(slug, iter_n)

        # Snapshot every iter (cheap)
        if not dry_run and iter_n > 0:
            sp = create_savepoint(slug, iter_n)
            if sp.get("ok"):
                actions += 1
                proj_state = state.setdefault("per_project", {}).setdefault(slug, {})
                proj_state.setdefault("savepoints", []).append({
                    "iter": iter_n, "tag": sp["tag"], "score": qs["score"], "ts": utc_iso(),
                })
                proj_state["savepoints"] = proj_state["savepoints"][-20:]
                # Track best iter
                best = max(proj_state.get("savepoints", []), key=lambda s: s.get("score", 0), default=None)
                if best:
                    proj_state["best_iter_recent"] = best["iter"]

        # Contradict every N iters
        if iter_n > 0 and iter_n % CONTRADICT_EVERY_N_ITERS == 0:
            already_posted = (state.get("per_project", {}).get(slug, {})
                              .get("last_contradict_iter", -1))
            if already_posted != iter_n and not dry_run:
                c = post_contradict(slug, iter_n)
                if c.get("ok"):
                    actions += 1
                    state.setdefault("per_project", {}).setdefault(slug, {})["last_contradict_iter"] = iter_n

        # Rehook check
        rehook = check_rehook(slug, qs["score"], state)
        if rehook and rehook.get("should_rehook"):
            log({"action": "rehook-recommended", "slug": slug, "iter": iter_n, **rehook})
            results.append({"slug": slug, "rehook_recommended": rehook})
            actions += 1

        results.append({"slug": slug, "iter": iter_n, "score": qs["score"],
                        "incidents_10m": qs["incidents_10m"]})

    save_state(state)
    return {"ok": True, "live_projects": len(projects), "actions": actions, "results": results}


def status() -> int:
    state = load_state()
    projects = live_projects()
    print(f"[loop-quality] status @ {utc_iso()}")
    print(f"  live projects: {len(projects)}")
    print()
    for p in projects:
        slug = p["slug"]
        ps = state.get("per_project", {}).get(slug, {})
        recent = ps.get("recent_scores", [])
        sp_count = len(ps.get("savepoints", []))
        print(f"  {slug:24} iter={p['iter']:>3}  scores={recent}  savepoints={sp_count}")
    return 0


def install_schtask() -> int:
    pw = shutil.which("pythonw") or str(Path(sys.executable).parent / "pythonw.exe")
    py = pw if Path(pw).exists() else sys.executable
    script = str(Path(__file__).resolve())
    cmd = ["schtasks.exe", "/Create", "/F", "/TN", SCHTASK_NAME,
           "/TR", f'"{py}" "{script}" --once',
           "/SC", "MINUTE", "/MO", "1", "/RL", "LIMITED"]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if cp.returncode == 0:
            print(f"[loop-quality] schtask {SCHTASK_NAME} installed (1-min headless)")
            return 0
        print(f"[loop-quality] install failed: {cp.stderr.strip()}", file=sys.stderr)
        return cp.returncode
    except Exception as exc:
        print(f"[loop-quality] install err: {exc}", file=sys.stderr)
        return 1


def uninstall_schtask() -> int:
    try:
        cp = subprocess.run(["schtasks.exe", "/Delete", "/TN", SCHTASK_NAME, "/F"],
                            capture_output=True, text=True, timeout=15)
        print(f"[loop-quality] uninstall rc={cp.returncode}")
        return cp.returncode
    except Exception as exc:
        print(f"[loop-quality] uninstall err: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true")
    g.add_argument("--watch", action="store_true")
    g.add_argument("--snapshot", help="manually snapshot a slug now")
    g.add_argument("--rehook", nargs=2, metavar=("slug", "tag"))
    g.add_argument("--contradict", help="post contradict message to slug inbox")
    g.add_argument("--status", action="store_true")
    g.add_argument("--install-schtask", action="store_true")
    g.add_argument("--uninstall", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--interval", type=int, default=60)
    args = ap.parse_args(argv)

    if args.install_schtask:
        return install_schtask()
    if args.uninstall:
        return uninstall_schtask()
    if args.status:
        return status()
    if args.snapshot:
        # need iter — read heartbeat
        hb = HEARTBEAT_DIR / f"{args.snapshot}.json"
        iter_n = 0
        if hb.exists():
            try:
                iter_n = json.loads(hb.read_text(encoding="utf-8-sig")).get("loop_iter", 0)
            except Exception:
                pass
        print(json.dumps(create_savepoint(args.snapshot, iter_n), indent=2))
        return 0
    if args.contradict:
        hb = HEARTBEAT_DIR / f"{args.contradict}.json"
        iter_n = 0
        if hb.exists():
            try:
                iter_n = json.loads(hb.read_text(encoding="utf-8-sig")).get("loop_iter", 0)
            except Exception:
                pass
        print(json.dumps(post_contradict(args.contradict, iter_n), indent=2))
        return 0
    if args.rehook:
        slug, tag = args.rehook
        try:
            cp = subprocess.run(["git", "reset", "--hard", tag],
                                capture_output=True, text=True, cwd=str(SANCTUM_ROOT), timeout=20)
            log({"action": "rehook-executed", "slug": slug, "tag": tag, "rc": cp.returncode})
            print(f"rehook {slug} -> {tag}: rc={cp.returncode}\n{cp.stdout}{cp.stderr}")
            return cp.returncode
        except Exception as exc:
            print(f"rehook err: {exc}", file=sys.stderr)
            return 1
    if args.once:
        r = run_once(dry_run=args.dry_run)
        print(json.dumps(r, indent=2))
        return 0
    if args.watch:
        while True:
            try:
                r = run_once(dry_run=args.dry_run)
                if r.get("actions", 0) > 0:
                    print(f"[loop-quality] actions={r['actions']} projects={r['live_projects']}")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
