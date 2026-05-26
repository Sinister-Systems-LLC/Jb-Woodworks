#!/usr/bin/env python3
"""loop_open_agents.py — looper that watches the live spawned fleet.

Author: RKOJ-ELENO :: 2026-05-25

Operator (verbatim 2026-05-25 ~18:09Z): "i need looper to work on the
open agents".

For each live agent (heartbeat <30 min fresh), this looper:
  1. Reads the agent's PROGRESS.md tail + recent commit count + open-task
     count as a composite quality score.
  2. Calls automations/loop_checkpoint.py save for the agent's owned
     paths (read from projects.json `lane_dir` field).
  3. Appends a row to _shared-memory/quality-loop-log.jsonl with
     kind=open-agent-tick + score components.
  4. On regression vs best-seen score for this agent's run_id, prints
     a WARN (revert is opt-in via --revert flag; shared multi-agent repo
     means auto-revert without operator confirmation is too risky).

USAGE:
  python automations/loop_open_agents.py              # one tick
  python automations/loop_open_agents.py --watch --interval-s 600
  python automations/loop_open_agents.py --revert     # auto-revert on regression
  python automations/loop_open_agents.py --json       # JSON output

Stdlib only. Per no-bat-no-ps1-doctrine.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SANCTUM = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
HB_DIR = SANCTUM / "_shared-memory" / "heartbeats"
LOG_JSONL = SANCTUM / "_shared-memory" / "quality-loop-log.jsonl"
CKPT_PY = SANCTUM / "automations" / "loop_checkpoint.py"
PROJECTS = SANCTUM / "automations" / "session-templates" / "projects.json"

FRESH_S = 30 * 60  # 30 min per auto-start doctrine


def _utcnow_s() -> float: return time.time()


def _utcnow_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_projects() -> dict:
    if not PROJECTS.exists(): return {}
    try:
        # UTF-8 BOM tolerant
        txt = PROJECTS.read_text(encoding="utf-8-sig")
        return json.loads(txt)
    except Exception:
        return {}


def _project_root_for_slug(slug: str) -> str | None:
    """Read projects.json and return the repo-relative `root` for slug.
    Used to checkpoint each agent's owned slice on every tick.

    iter-27: try exact slug match first, then prefix match (heartbeat
    slugs like 'eve-compliance-train-loop' map to project key
    'eve-compliance'), then fall back to projects/<slug>/ if the dir
    exists -- so newly-spawned lanes get checkpointed even before
    projects.json registers them."""
    d = _load_projects()
    projects = d.get("projects", [])
    # exact
    for p in projects:
        if p.get("key") == slug:
            return _rel(p.get("root"))
    # prefix (heartbeat slug starts with project key + '-')
    for p in projects:
        k = p.get("key")
        if k and slug.startswith(k + "-"):
            return _rel(p.get("root"))
    # directory probe fallback
    guess = SANCTUM / "projects" / slug
    if guess.exists() and guess.is_dir():
        return f"projects/{slug}"
    return None


def _rel(root: str | None) -> str | None:
    if not root: return None
    try:
        rp = Path(root).resolve().relative_to(SANCTUM.resolve())
        return str(rp).replace("\\", "/")
    except Exception:
        return None


def list_live_agents() -> list[dict]:
    """Walk heartbeats dir, return list of dicts for agents whose
    heartbeat is fresher than FRESH_S seconds."""
    out = []
    if not HB_DIR.exists(): return out
    cutoff = _utcnow_s() - FRESH_S
    for hb in HB_DIR.glob("*.json"):
        try:
            mtime = hb.stat().st_mtime
        except OSError: continue
        if mtime < cutoff: continue
        try:
            data = json.loads(hb.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        out.append({
            "slug": hb.stem,
            "display": data.get("display") or hb.stem,
            "heartbeat_age_s": int(_utcnow_s() - mtime),
            "branch": data.get("branch"),
            "status": data.get("status", "unknown"),
            "data": data,
        })
    return sorted(out, key=lambda a: a["heartbeat_age_s"])


def _progress_file(slug: str, display: str) -> Path | None:
    candidates = [
        SANCTUM / "_shared-memory" / "PROGRESS" / f"{display}.md",
        SANCTUM / "_shared-memory" / "PROGRESS" / f"{slug}.md",
        SANCTUM / "projects" / slug / "PROGRESS.md",
    ]
    for c in candidates:
        if c.exists(): return c
    return None


def _commit_count_last_hour(slug: str) -> int:
    """Count commits matching slug in last 1h via git log."""
    cutoff = _utcnow_s() - 3600
    try:
        r = subprocess.run(
            ["git", "-C", str(SANCTUM), "log", "--since=1.hour", "--oneline",
             "--all"],
            capture_output=True, text=True, timeout=15,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
        if r.returncode != 0: return 0
        lines = [l for l in r.stdout.splitlines() if slug.lower() in l.lower()]
        return len(lines)
    except Exception:
        return 0


def score_agent(slug: str, display: str) -> dict:
    """Composite score = progress_bytes/100 + 50*recent_commits + heartbeat_freshness_bonus."""
    pf = _progress_file(slug, display)
    progress_bytes = pf.stat().st_size if pf else 0
    commits_1h = _commit_count_last_hour(slug)
    hb = HB_DIR / f"{slug}.json"
    fresh_s = int(_utcnow_s() - hb.stat().st_mtime) if hb.exists() else FRESH_S
    fresh_bonus = max(0, 100 - fresh_s // 60)  # newer = higher; 0 if 100min+
    score = round(progress_bytes / 100 + 50 * commits_1h + fresh_bonus, 2)
    return {
        "slug": slug,
        "score": score,
        "components": {
            "progress_bytes": progress_bytes,
            "commits_1h": commits_1h,
            "fresh_bonus": fresh_bonus,
        },
    }


def _ckpt(*args: str) -> dict:
    cmd = [sys.executable, str(CKPT_PY), *args]
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
        return json.loads(r.stdout) if r.stdout.strip() else {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _best_score_for_agent(slug: str) -> tuple[float, int]:
    """Walk quality-loop-log.jsonl filtered to lane=slug + kind=open-agent-tick.
    Returns (best_score, best_iter) or (-inf, -1)."""
    if not LOG_JSONL.exists(): return float("-inf"), -1
    best_s, best_i = float("-inf"), -1
    with LOG_JSONL.open(encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            try: r = json.loads(ln.strip())
            except Exception: continue
            if r.get("lane") != slug: continue
            if r.get("kind") != "open-agent-tick": continue
            s = r.get("score")
            if not isinstance(s, (int, float)): continue
            if s > best_s:
                best_s = float(s); best_i = int(r.get("iter", -1))
    return best_s, best_i


def _next_iter_for_agent(slug: str) -> int:
    if not LOG_JSONL.exists(): return 0
    n = 0
    with LOG_JSONL.open(encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            try: r = json.loads(ln.strip())
            except Exception: continue
            if r.get("lane") == slug and r.get("kind") == "open-agent-tick":
                n += 1
    return n


def tick(agents: list[dict], do_revert: bool = False, dry_run: bool = False,
         do_checkpoint: bool = True) -> list[dict]:
    """Run one looper tick across all live agents. Returns score rows.

    iter-24: now actually saves a checkpoint per agent each tick (using the
    project's `root` path from projects.json). Revert (--revert) is still
    opt-in. Per-agent run_id is stable across ticks of one daemon process
    so restore-best can find the peak across the whole watch window."""
    results = []
    # Stable run_id per process invocation (so consecutive ticks of one
    # `--watch` daemon share a peak-tracker; one-shot calls still get a
    # fresh run_id each invocation).
    run_id = globals().setdefault(
        "_RUN_ID",
        time.strftime("oa-%Y%m%dT%H%M%SZ", time.gmtime())
    )
    for ag in agents:
        slug = ag["slug"]; display = ag["display"]
        s = score_agent(slug, display)
        s["heartbeat_age_s"] = ag["heartbeat_age_s"]
        s["branch"] = ag.get("branch")
        prev_best, prev_best_iter = _best_score_for_agent(slug)
        cur_iter = _next_iter_for_agent(slug)
        s["iter"] = cur_iter
        s["prev_best"] = prev_best if prev_best > float("-inf") else None
        s["regressed"] = (
            prev_best > float("-inf") and s["score"] < prev_best - 0.001
        )
        s["action"] = "ok"
        # iter-24: SAVE a checkpoint of the agent's `root` path. This is the
        # missing piece -- without it, restore-best has nothing to restore to.
        root_rel = _project_root_for_slug(slug)
        if do_checkpoint and root_rel and not dry_run:
            sv = _ckpt(
                "save", "--lane", slug, "--run-id", run_id,
                "--iter", str(cur_iter), "--paths", root_rel,
                "--sanctum-root", str(SANCTUM),
            )
            s["checkpoint_ok"] = sv.get("ok", False)
            s["checkpoint_files"] = sv.get("files", 0)
        else:
            s["checkpoint_ok"] = False
        if s["regressed"]:
            s["action"] = "regress-warn"
            if do_revert and not dry_run:
                rs = _ckpt(
                    "restore-best", "--lane", slug, "--run-id", run_id,
                    "--sanctum-root", str(SANCTUM),
                )
                s["restore"] = rs
                s["action"] = "reverted" if rs.get("ok") else "revert-failed"
        # Append to log
        if not dry_run:
            row = {
                "kind": "open-agent-tick", "ts_utc": _utcnow_iso(),
                "lane": slug, "task": "live-agent-loop",
                "iter": cur_iter, "score": s["score"],
                "best_score": max(s["score"], prev_best) if prev_best > float("-inf") else s["score"],
                "best_iter": cur_iter if s["score"] > prev_best else prev_best_iter,
                "run_id": run_id, "components": s["components"],
                "action": s["action"],
                "checkpoint_files": s.get("checkpoint_files", 0),
            }
            try:
                with LOG_JSONL.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row) + "\n")
            except OSError: pass
        results.append(s)
    return results


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--watch", action="store_true",
                   help="loop forever; default = one tick")
    p.add_argument("--interval-s", type=int, default=600)
    p.add_argument("--revert", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-checkpoint", dest="no_checkpoint", action="store_true",
                   help="skip the per-agent loop_checkpoint.save call")
    p.add_argument("--json", dest="json_out", action="store_true")
    args = p.parse_args()

    def _once():
        ags = list_live_agents()
        do_ck = not args.no_checkpoint
        if args.json_out:
            print(json.dumps({"live": len(ags),
                              "results": tick(ags, args.revert, args.dry_run, do_ck)},
                             indent=2))
        else:
            print(f"loop_open_agents tick @ {_utcnow_iso()} ({len(ags)} live)")
            results = tick(ags, args.revert, args.dry_run, do_ck)
            for r in results:
                comp = r["components"]
                tag = r["action"].upper()
                ck = f"ck={r.get('checkpoint_files', 0)}f" if r.get("checkpoint_ok") else "ck=-"
                print(f"  [{tag:14s}] {r['slug']:30s} score={r['score']:>8.2f}  {ck}  "
                      f"(progress_b={comp['progress_bytes']} commits_1h={comp['commits_1h']} "
                      f"fresh+{comp['fresh_bonus']} hb={r['heartbeat_age_s']}s)")

    if not args.watch:
        _once()
        return 0
    while True:
        try:
            _once()
        except KeyboardInterrupt:
            return 0
        except Exception as e:
            print(f"[ERR] tick: {e}", file=sys.stderr)
        time.sleep(args.interval_s)


if __name__ == "__main__":
    sys.exit(main())
