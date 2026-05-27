# Sinister Term :: rmux_verbs.py
# Author: RKOJ-ELENO :: 2026-05-26
# License: AGPL-3.0-or-later
#
# Sinister rmux management verbs — spawn / stop / kill / attach / focus / logs
# / projects. The companion to term/rmux.py (which owns monitoring). Together
# they give the operator one front door for the whole fleet:
#
#   rmux ls                   # what's running
#   rmux watch                # live monitor
#   rmux spawn <project>      # launch a new Sinister agent
#   rmux stop                 # graceful stop of every Sinister mintty
#   rmux kill <slug>          # stop one agent (per-slug)
#   rmux focus <slug>         # bring that agent's mintty to foreground
#   rmux attach <slug>        # alias for focus
#   rmux logs <slug> [N]      # tail per-agent log
#   rmux projects             # list known projects
#
# Operator directive 2026-05-26 ~23:50Z (verbatim):
#   "i need an efficent way combining all eve exe, rkoj etc. to manage and run
#    the teerminals in a system like rmux"
#
# Wires through to existing automations:
#   - automations/start-sinister-session.ps1   (spawn pipeline)
#   - Stop-EVE.bat                              (master kill — every mintty)
#   - automations/session-templates/projects.json  (project registry)
#   - _shared-memory/heartbeats/<slug>.json     (per-agent state)
#   - _shared-memory/PROGRESS/<Display>.md      (per-agent log)
#
# Composes with doctrines:
#   - no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25 — we DRIVE the existing
#     .ps1 / .bat files from Python; no NEW shells.
#   - automate-everything-no-operator-admin-2026-05-25 — verbs execute
#     directly, no operator confirmation prompts.
#   - single-repo-push-policy-2026-05-25 — all writes stay under Sanctum.
#   - sanctum-scope-discipline-2026-05-24 — these are sterm-lane surfaces
#     calling sanctum-lane automations; we do not modify sanctum scripts.

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _sanctum_root() -> Path:
    return Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")


def _heartbeats_dir() -> Path:
    return _sanctum_root() / "_shared-memory" / "heartbeats"


def _progress_dir() -> Path:
    return _sanctum_root() / "_shared-memory" / "PROGRESS"


def _projects_json() -> Path:
    return _sanctum_root() / "automations" / "session-templates" / "projects.json"


def _spawn_script() -> Path:
    return _sanctum_root() / "automations" / "start-sinister-session.ps1"


def _stop_bat() -> Path:
    return _sanctum_root() / "Stop-EVE.bat"


def _inbox_dir(slug: str) -> Path:
    return _sanctum_root() / "_shared-memory" / "inbox" / slug


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class VerbResult:
    """Uniform return for every verb. `ok=False` means action failed."""
    ok: bool
    text: str
    detail: dict | None = None

    def __str__(self) -> str:
        return self.text


# ---------------------------------------------------------------------------
# Project registry helpers
# ---------------------------------------------------------------------------


def load_projects() -> list[dict]:
    pj = _projects_json()
    if not pj.is_file():
        return []
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
    except Exception:
        return []
    projects = data.get("projects")
    if not isinstance(projects, list):
        return []
    return projects


def lookup_project(key_or_substring: str) -> tuple[dict | None, list[dict]]:
    """Return (exact-or-unique-match, candidates).

    If we resolve to one project, it goes in slot 1 and candidates is empty.
    On ambiguity, slot 1 is None and candidates holds the matching projects.
    """
    needle = (key_or_substring or "").strip().lower()
    if not needle:
        return None, []
    projects = load_projects()
    # exact key
    for p in projects:
        if (p.get("key") or "").lower() == needle:
            return p, []
    # substring on key / display_name
    cands = [
        p for p in projects
        if needle in (p.get("key") or "").lower()
        or needle in (p.get("display_name") or "").lower()
    ]
    if len(cands) == 1:
        return cands[0], []
    return None, cands


# ---------------------------------------------------------------------------
# Heartbeat helpers
# ---------------------------------------------------------------------------


def load_heartbeat(slug: str) -> dict | None:
    hb = _heartbeats_dir() / f"{slug}.json"
    if not hb.is_file():
        return None
    try:
        return json.loads(hb.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_live_slugs(max_age_minutes: float = 30.0) -> list[tuple[str, float]]:
    """Slugs whose heartbeat mtime is within `max_age_minutes`."""
    out: list[tuple[str, float]] = []
    d = _heartbeats_dir()
    if not d.is_dir():
        return []
    cutoff = time.time() - max_age_minutes * 60.0
    try:
        for p in d.iterdir():
            if p.suffix != ".json":
                continue
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if mt >= cutoff:
                age_min = (time.time() - mt) / 60.0
                out.append((p.stem, age_min))
    except OSError:
        return []
    out.sort(key=lambda t: t[1])
    return out


def resolve_slug(slug_or_sub: str) -> tuple[str | None, list[str]]:
    """Resolve a slug substring against `_shared-memory/heartbeats/*.json`."""
    needle = (slug_or_sub or "").strip().lower()
    if not needle:
        return None, []
    d = _heartbeats_dir()
    if not d.is_dir():
        return None, []
    try:
        all_slugs = sorted({p.stem for p in d.iterdir() if p.suffix == ".json"})
    except OSError:
        return None, []
    if needle in all_slugs:
        return needle, []
    cands = [s for s in all_slugs if needle in s]
    if len(cands) == 1:
        return cands[0], []
    return None, cands


# ---------------------------------------------------------------------------
# Verb: projects (list known projects)
# ---------------------------------------------------------------------------


def verb_projects(_args: list[str]) -> VerbResult:
    projects = load_projects()
    if not projects:
        return VerbResult(False, "(no projects.json found or empty)")
    lines = ["Sinister project registry:"]
    for p in projects:
        key = p.get("key") or "?"
        display = p.get("display_name") or key
        tier = p.get("tier")
        accent = p.get("accent") or "-"
        line = f"  {key:<22} {display:<28} accent={accent}"
        if tier is not None:
            line += f"  tier={tier}"
        lines.append(line)
    lines.append(f"\n{len(projects)} project(s). Use `rmux spawn <key>` to launch one.")
    return VerbResult(True, "\n".join(lines), {"count": len(projects)})


# ---------------------------------------------------------------------------
# Verb: ls (alias of monitor snapshot)
# ---------------------------------------------------------------------------


def verb_ls(args: list[str]) -> VerbResult:
    """One-shot snapshot. Delegates to term.rmux.render_snapshot."""
    from term import rmux as _r
    limit = 30
    live_only = False
    sort_key = "age"
    project = ""
    for a in args:
        if a.isdigit():
            limit = max(1, min(500, int(a)))
        elif a in ("live", "--live"):
            live_only = True
        elif a.startswith("sort="):
            sort_key = a.split("=", 1)[1]
        elif a.startswith("project="):
            project = a.split("=", 1)[1]
    if sort_key not in _r.SORT_KEYS:
        return VerbResult(False, f"unknown sort key: {sort_key}")
    text = _r.render_snapshot(limit=limit, live_only=live_only, sort=sort_key,
                              project=project)
    return VerbResult(True, text)


def verb_watch(args: list[str]) -> VerbResult:
    """Live monitor — delegates to rmux.watch_loop. Returns when Ctrl+C exits."""
    from term import rmux as _r
    interval = _r._DEFAULT_WATCH_INTERVAL
    sort_key = "age"
    live_only = False
    limit = 30
    project = ""
    for a in args:
        if re.match(r"^\d+(\.\d+)?$", a):
            interval = max(0.25, float(a))
        elif a in ("live", "--live"):
            live_only = True
        elif a.startswith("sort="):
            sort_key = a.split("=", 1)[1]
        elif a.startswith("project="):
            project = a.split("=", 1)[1]
        elif a.startswith("limit="):
            try:
                limit = max(1, min(500, int(a.split("=", 1)[1])))
            except Exception:
                pass
    if sort_key not in _r.SORT_KEYS:
        return VerbResult(False, f"unknown sort key: {sort_key}")
    _r.watch_loop(interval=interval, limit=limit, live_only=live_only,
                  sort=sort_key, project=project)
    return VerbResult(True, "")  # output streamed; no trailing text


def verb_json(args: list[str]) -> VerbResult:
    from term import rmux as _r
    limit = 200
    live_only = False
    sort_key = "age"
    project = ""
    for a in args:
        if a.isdigit():
            limit = max(1, min(5000, int(a)))
        elif a in ("live", "--live"):
            live_only = True
        elif a.startswith("sort="):
            sort_key = a.split("=", 1)[1]
        elif a.startswith("project="):
            project = a.split("=", 1)[1]
    if sort_key not in _r.SORT_KEYS:
        return VerbResult(False, f"unknown sort key: {sort_key}")
    text = _r.render_json(limit=limit, live_only=live_only, sort=sort_key,
                          project=project)
    return VerbResult(True, text)


def verb_detail(args: list[str]) -> VerbResult:
    from term import rmux as _r
    if not args:
        return VerbResult(False, "usage: rmux detail <session-id-or-substring>")
    return VerbResult(True, _r.render_detail(args[0]))


# ---------------------------------------------------------------------------
# Verb: spawn — start a new Sinister agent for a project
# ---------------------------------------------------------------------------


def _resolve_powershell() -> str | None:
    for name in ("pwsh.exe", "powershell.exe", "pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    return None


def verb_spawn(args: list[str],
               run_fn=subprocess.Popen) -> VerbResult:
    """Spawn a new Sinister agent for <project>.

    Usage:
      rmux spawn <project-key> [--mode <loop|relentless|...>] [--detached]

    Wraps `automations/start-sinister-session.ps1 -Project <key>` so the
    operator never needs to run EVE.exe to launch a single project.
    """
    if not args:
        return VerbResult(False,
            "usage: rmux spawn <project-key> [--mode X] "
            "(try `rmux projects` for the registry)")
    project_arg = args[0]
    extra: list[str] = []
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--mode" and i + 1 < len(args):
            extra += ["-Mode", args[i + 1]]
            i += 2
        elif a == "--detached":
            extra += ["-Detached"]
            i += 1
        else:
            extra.append(a)
            i += 1
    p, cands = lookup_project(project_arg)
    if p is None:
        if cands:
            keys = ", ".join((c.get("key") or "?") for c in cands[:8])
            return VerbResult(False,
                f"ambiguous project '{project_arg}'. Candidates: {keys}")
        return VerbResult(False,
            f"no project matches '{project_arg}'. Try `rmux projects`.")
    project_key = p.get("key") or project_arg
    script = _spawn_script()
    if not script.is_file():
        return VerbResult(False, f"spawn script not found: {script}")
    ps = _resolve_powershell()
    if not ps:
        return VerbResult(False, "powershell not in PATH; cannot spawn.")
    cmd = [ps, "-NoLogo", "-NoProfile", "-File", str(script),
           "-Project", project_key, *extra]
    try:
        run_fn(cmd, cwd=str(_sanctum_root()))
    except Exception as e:
        return VerbResult(False, f"spawn failed: {e}")
    return VerbResult(True,
        f"spawned {project_key} via {script.name}; check `rmux ls` in ~5s",
        {"project": project_key, "cmd": cmd})


# ---------------------------------------------------------------------------
# Verb: stop — master kill (every Sinister mintty)
# ---------------------------------------------------------------------------


def verb_stop(args: list[str],
              run_fn=subprocess.run) -> VerbResult:
    """Master kill via Stop-EVE.bat. Closes every Sinister mintty session."""
    bat = _stop_bat()
    if not bat.is_file():
        return VerbResult(False, f"stop bat not found: {bat}")
    quiet = ("--quiet" in args) or ("-q" in args)
    try:
        result = run_fn([str(bat)], cwd=str(_sanctum_root()),
                        capture_output=True, text=True, timeout=20)
    except Exception as e:
        return VerbResult(False, f"stop failed: {e}")
    rc = getattr(result, "returncode", 1)
    out = (getattr(result, "stdout", "") or "").strip()
    err = (getattr(result, "stderr", "") or "").strip()
    if rc == 0:
        msg = "stopped: every Sinister mintty asked to exit"
        if out and not quiet:
            msg += f"\n{out}"
        return VerbResult(True, msg, {"rc": rc})
    return VerbResult(False,
        f"stop returned rc={rc}\nstderr: {err[:400]}\nstdout: {out[:400]}",
        {"rc": rc})


# ---------------------------------------------------------------------------
# Verb: kill — graceful stop of a single agent via inbox poke
# ---------------------------------------------------------------------------


def verb_kill(args: list[str]) -> VerbResult:
    """Drop a graceful-shutdown notice in the agent's inbox so its loop exits
    at the next iteration boundary. (We don't TerminateProcess — that risks
    half-written commits / dirty repos.)
    """
    if not args:
        return VerbResult(False, "usage: rmux kill <slug>")
    slug_arg = args[0]
    slug, cands = resolve_slug(slug_arg)
    if slug is None:
        if cands:
            return VerbResult(False,
                f"ambiguous '{slug_arg}'. Candidates: " + ", ".join(cands[:8]))
        return VerbResult(False, f"no agent matches '{slug_arg}'.")
    box = _inbox_dir(slug)
    try:
        box.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return VerbResult(False, f"could not create inbox dir: {e}")
    ts = time.strftime("%Y-%m-%dT%H%MZ", time.gmtime())
    msg_path = box / f"{ts}-from-sinister-term-rmux-kill.json"
    payload = {
        "schema_version": "sinister.cross-agent-msg.v1",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "from_slug": "sinister-term",
        "from_display": "Sinister Term",
        "to_slug": slug,
        "priority": "high",
        "kind": "graceful-shutdown",
        "subject": "[SHUTDOWN] operator-requested graceful loop exit (rmux kill)",
        "body": (
            "Operator invoked `rmux kill " + slug + "`. Finish the current "
            "deliverable, commit + push, write resume-point, then exit "
            "cleanly. Do NOT take new work this turn."
        ),
        "expected_action": "exit-loop-after-this-iteration",
        "author": "RKOJ-ELENO :: 2026-05-26",
    }
    try:
        msg_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as e:
        return VerbResult(False, f"could not write kill notice: {e}")
    return VerbResult(True,
        f"kill notice dropped at {msg_path}; agent will exit at next loop "
        f"boundary. (Use `rmux stop` to close every mintty.)",
        {"slug": slug, "path": str(msg_path)})


# ---------------------------------------------------------------------------
# Verb: focus / attach — bring agent's mintty to foreground
# ---------------------------------------------------------------------------


def _focus_window_via_powershell(title_substr: str,
                                  run_fn=subprocess.run) -> tuple[bool, str]:
    """Use AppActivate to bring a window with matching title to foreground."""
    ps = _resolve_powershell()
    if not ps:
        return False, "powershell not in PATH"
    # `AppActivate` returns True on success; we surface that.
    script = (
        "$ws=New-Object -ComObject WScript.Shell;"
        f"$r=$ws.AppActivate('{title_substr}');"
        "if ($r) { 'OK' } else { 'NOMATCH' }"
    )
    try:
        result = run_fn(
            [ps, "-NoLogo", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=8,
        )
    except Exception as e:
        return False, str(e)
    out = (getattr(result, "stdout", "") or "").strip()
    if "OK" in out:
        return True, "focused"
    if "NOMATCH" in out:
        return False, "no window matched"
    return False, f"unexpected output: {out[:200]}"


def verb_focus(args: list[str], run_fn=subprocess.run) -> VerbResult:
    """Bring the agent's mintty window to foreground.

    We match by title substring — sterm sessions tag the title via
    `theme.set_title()`; mintty windows are titled `<Display Name> ...`.
    """
    if not args:
        return VerbResult(False, "usage: rmux focus <slug>")
    slug_arg = args[0]
    slug, cands = resolve_slug(slug_arg)
    if slug is None:
        if cands:
            return VerbResult(False,
                f"ambiguous '{slug_arg}'. Candidates: " + ", ".join(cands[:8]))
        return VerbResult(False, f"no agent matches '{slug_arg}'.")
    # title patterns we try in order
    hb = load_heartbeat(slug) or {}
    display = (hb.get("agent_display")
               or " ".join(w.capitalize() for w in slug.split("-")))
    candidates = [display, slug, slug.replace("-", " ")]
    last_err = ""
    for c in candidates:
        ok, msg = _focus_window_via_powershell(c, run_fn=run_fn)
        if ok:
            return VerbResult(True,
                f"focused mintty matching '{c}' for slug={slug}")
        last_err = msg
    return VerbResult(False,
        f"no mintty window matched any of {candidates}. ({last_err})")


def verb_attach(args: list[str], run_fn=subprocess.run) -> VerbResult:
    """Alias for focus — mintty has no true attach so we bring-to-foreground."""
    return verb_focus(args, run_fn=run_fn)


# ---------------------------------------------------------------------------
# Verb: logs — tail per-agent PROGRESS log
# ---------------------------------------------------------------------------


_KNOWN_ALL_CAPS_PARTS = {
    # Short common acronyms that the Sinister PROGRESS file naming convention
    # already renders ALL-CAPS in the display name (e.g. "Sinister OS.md",
    # "Sinister Kernel APK.md").
    "os", "apk", "ui", "ux", "ai", "ml", "tv", "api", "cli", "sdk",
    "rkoj", "kpi", "qr", "vr", "ar", "gpu", "cpu", "vm", "io", "pi",
    "rka", "fm",
}


def _slug_to_display(slug: str) -> str:
    """Hyphenated slug → spaced display name.

    sinister-term -> Sinister Term
    sinister-os   -> Sinister OS
    kernel-apk    -> Kernel APK
    """
    if not slug:
        return ""
    parts = slug.split("-")
    out = []
    for p in parts:
        if p.lower() in _KNOWN_ALL_CAPS_PARTS:
            out.append(p.upper())
        else:
            out.append(p.capitalize())
    return " ".join(out)


def verb_logs(args: list[str]) -> VerbResult:
    """Tail an agent's PROGRESS log (newest at top)."""
    if not args:
        return VerbResult(False, "usage: rmux logs <slug> [N]")
    slug_arg = args[0]
    limit = 5
    if len(args) > 1 and args[1].isdigit():
        limit = max(1, min(50, int(args[1])))
    slug, cands = resolve_slug(slug_arg)
    if slug is None:
        if cands:
            return VerbResult(False,
                f"ambiguous '{slug_arg}'. Candidates: " + ", ".join(cands[:8]))
        return VerbResult(False, f"no agent matches '{slug_arg}'.")
    # locate the PROGRESS file — convention varies across the fleet
    pdir = _progress_dir()
    if not pdir.is_dir():
        return VerbResult(False, f"PROGRESS dir not found: {pdir}")
    display = _slug_to_display(slug)
    candidates_path = [
        pdir / f"{display}.md",
        pdir / f"{slug}.md",
    ]
    target: Path | None = next((p for p in candidates_path if p.is_file()), None)
    if target is None:
        # fallback: substring match on filenames in PROGRESS dir
        try:
            files = sorted(pdir.iterdir())
        except OSError:
            return VerbResult(False, "could not enumerate PROGRESS dir")
        cand2 = [p for p in files if slug in p.name.lower()
                 or display.lower() in p.name.lower()]
        if len(cand2) == 1:
            target = cand2[0]
    if target is None:
        return VerbResult(False, f"no PROGRESS log for slug={slug}")
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return VerbResult(False, f"could not read {target.name}: {e}")
    # split on `## ` blocks newest-first (mirrors /progress-of)
    blocks = re.split(r"^(?=## )", text, flags=re.MULTILINE)
    blocks = [b.strip() for b in blocks if b.strip().startswith("## ")]
    blocks = blocks[:limit]
    if not blocks:
        return VerbResult(True, f"(no ## entries in {target.name})")
    return VerbResult(True,
        f"-- {target.name} (top {len(blocks)}) --\n\n" + "\n\n".join(blocks))


# ---------------------------------------------------------------------------
# Verb: help
# ---------------------------------------------------------------------------


_HELP_TEXT = """
Sinister rmux — unified terminal manager for the Sinister fleet.

Usage:
  rmux                           one-shot snapshot of every Claude session
  rmux ls [N] [live] [sort=K]    snapshot with options
  rmux watch [N]                 live refresh every N sec (default 2.0)
  rmux json                      dump session data as JSON
  rmux detail <id>               drilldown of a single session
  rmux spawn <project>           launch a new Sinister agent
                                 (replaces clicking EVE.exe)
  rmux stop                      master kill (every Sinister mintty)
                                 (replaces Stop-EVE.bat)
  rmux kill <slug>               graceful per-agent shutdown (inbox poke)
  rmux focus <slug>              bring agent's mintty to foreground
  rmux attach <slug>             alias for focus
  rmux logs <slug> [N]           tail agent's PROGRESS log
  rmux projects                  list known projects
  rmux help                      this text

Project keys: `rmux projects` to list. Slugs: `rmux ls` to see active.

Composes EVE.exe (spawn), Stop-EVE.bat (stop), RKOJ workbench, and every
mintty session into one CLI surface so the operator never needs to
remember where a button is.
""".strip()


def verb_help(_args: list[str]) -> VerbResult:
    return VerbResult(True, _HELP_TEXT)


# ---------------------------------------------------------------------------
# Verb registry + dispatcher
# ---------------------------------------------------------------------------


VERBS = {
    # monitor surface (delegates to rmux.py renderers)
    "ls":       verb_ls,
    "list":     verb_ls,            # alias
    "watch":    verb_watch,
    "json":     verb_json,
    "detail":   verb_detail,
    # management surface
    "spawn":    verb_spawn,
    "start":    verb_spawn,         # alias
    "stop":     verb_stop,
    "kill":     verb_kill,
    "focus":    verb_focus,
    "attach":   verb_attach,
    "logs":     verb_logs,
    "log":      verb_logs,          # alias
    "projects": verb_projects,
    "help":     verb_help,
    "?":        verb_help,          # alias
}


def is_verb(name: str) -> bool:
    return name in VERBS


def dispatch_verb(name: str, args: list[str]) -> VerbResult:
    fn = VERBS.get(name)
    if fn is None:
        return VerbResult(False,
            f"unknown verb: {name!r}. Try `rmux help` for the list.")
    return fn(args)
