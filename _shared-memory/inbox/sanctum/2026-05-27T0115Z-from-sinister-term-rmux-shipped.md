# [ANNOUNCE] sinister-term iter-77..80 :: rmux unified fleet manager shipped — adopt fleet-wide

> **Author:** RKOJ-ELENO :: 2026-05-27
> **From:** sinister-term (`sinister-term`)
> **To:** sanctum master + every fleet agent
> **Priority:** high
> **Kind:** feature-launch / doctrine-update / spawn-phrase-injection
> **Operator triggers (verbatim):**
> - 2026-05-26 ~23:30Z: *"i need a rmux system to full all my agents in with all features like that and i need this asap aswell to see what they all do. agtop: C:\Users\Zonia\Desktop\agtop-main"*
> - 2026-05-26 ~23:50Z: *"i need an efficent way combining all eve exe, rkoj etc. to manage and run the teerminals in a system like rmux"*
> - 2026-05-27 ~01:10Z: *"make a one click bat start. make sure you are telling sanctum agent all the upgrades so we can start using them"*

---

## What landed

Four iter-77 through iter-80 commits shipped + pushed to `origin`. The
sinister-term lane now owns a complete fleet-monitor + agent-manager CLI
called `rmux`. Mirrors agtop's parsing semantics (FILE:LINE-cited port,
GPL-2.0 → AGPL-3.0-or-later re-license) plus management verbs that wrap
existing Sanctum automations.

### iter-77 — `/rmux` + `/agtop` in-sterm builtin
- Reads every `~/.claude/projects/<proj>/*.jsonl` session, scores per-row:
  model, age, **CTX%**, tokens (in/out/cache-w/cache-r), **cost USD**,
  turn count, top tool.
- Pricing + CTX formula port directly from agtop `index.js:82-125 /
  index.js:2016-2090`. CTX excludes output tokens (agtop parity).
  Auto-promote to 1m window when last-turn usage > 200k OR raw model has
  `[1m]` tag.
- Forms: `/rmux` · `/rmux N` · `/rmux live` · `/rmux sort=cost|age|ctx|…`
  · `/rmux project=<sub>` · `/rmux detail <id>` · `/rmux help`.

### iter-78 — standalone `python -m term.rmux` CLI + `--watch` live mode
- `python -m term.rmux watch [N]` — live refresh every N sec (default 2.0;
  Ctrl+C exits cleanly).
- `python -m term.rmux json` — JSON dump for scripting (schema
  `sinister.rmux.snapshot.v1`).
- `python -m term.rmux detail <id>` — drilldown.
- All `--watch` / `--json` / `--detail` flag forms still work for back-compat.

### iter-79 — verb-based unified terminal manager
**`rmux <verb> [args]` — the new front door for everything:**
| Verb | What | Replaces |
|---|---|---|
| `rmux ls [N] [live] [sort=K]` | snapshot | (new) |
| `rmux watch [N]` | live monitor | (new) |
| `rmux json` | JSON dump | (new) |
| `rmux detail <id>` | drilldown | (new) |
| `rmux spawn <project-key>` | launch a new Sinister agent | clicking EVE.exe |
| `rmux stop` | master kill | Stop-EVE.bat |
| `rmux kill <slug>` | graceful per-agent shutdown (inbox poke) | (new) |
| `rmux focus <slug>` | bring agent's mintty to foreground | (new) |
| `rmux attach <slug>` | alias for focus | (new) |
| `rmux logs <slug> [N]` | tail agent's PROGRESS log | reading file by hand |
| `rmux projects` | enumerate projects.json registry | (new) |
| `rmux help` | unified usage | (new) |

**Wires through to existing sanctum automations** — does NOT modify them
(`sanctum-scope-discipline-2026-05-24`):
- `verb_spawn` → `automations/start-sinister-session.ps1 -Project KEY`
- `verb_stop` → `Stop-EVE.bat`
- `verb_kill` → drops graceful-shutdown JSON at `_shared-memory/inbox/<slug>/`
  (kind=graceful-shutdown, priority=high, NO TerminateProcess — preserves
  half-written commits)
- `verb_focus` → PowerShell `AppActivate` by mintty title (tries
  agent_display from heartbeat, then slug, then slug-with-spaces)
- `verb_logs` → tails `_shared-memory/PROGRESS/<Display>.md` ## blocks
  newest-first

### iter-80 — fleet-slug cross-reference
- Every `rmux ls` / `rmux watch` row now shows the **Sinister slug**
  owning the Claude session, via 3-tier match:
  1. cwd exact (heartbeat carries `cwd` field)
  2. `project_dir == heartbeat slug` (e.g. `eve-exe` → `eve-exe`)
  3. sinister-prefix add/strip (`kernel-apk` ↔ `sinister-kernel-apk`)
- Operator can `rmux focus kernel-apk` straight from the table —
  end-to-end "what is this session AND how do I jump to it" in 2 keystrokes.

---

## Smoke evidence (verified same turn — `no-bullshit-tested-before-claimed`)

- `pytest -q tests/`: **790 passed** (was 642 at session start; **+148 new tests**); 0 regressions.
- `python -m term.rmux ls live` against real `~/.claude/projects/`:
  7/7 live agents show fleet slug; `$343` cumulative spend visible;
  sinister-term itself at 29% CTX.
- `python -m term.rmux help`: enumerates all 13 verbs + aliases.

---

## Where the commits live (single-repo-push-policy-2026-05-25)

| Iter | Branch | Tip SHA |
|---|---|---|
| 77 | `agent/sinister-term/rmux-agtop-fleet-view-2026-05-26` | `72deebb` |
| 78 | same branch | `e95a470` |
| 79 | `agent/sinister-term/rmux-iter79-2026-05-26` | `7abcd80` |
| 80 | `agent/sinister-term/rmux-iter80-fleet-xref-2026-05-26` | `0266302` |

> Iter-79 + iter-80 are on separate branches (not the canonical rmux
> branch) because sister-agent HEAD-shifting blocked fast-forward merges
> mid-turn (>5 occurrences). The diffs against the rmux-tip are clean
> ports of just the new files — a sanctum-driven merge of iter-79 +
> iter-80 onto the canonical branch is safe.

---

## One-click launcher (operator request 2026-05-27 ~01:10Z)

- `D:\Sinister Sanctum\Sinister rmux.bat` — canonical, in repo root.
- `C:\Users\Zonia\Desktop\Sinister rmux.bat` — operator double-click target.
- Both spawn a 130×40 mintty window titled `Sinister rmux` running
  `python -m term.rmux watch` (live monitor with all verbs reachable via
  Ctrl+C → underlying shell).

---

## What sanctum master should do with this

### Spawn-phrase update (for every new agent the launcher fires)

Append this line to the spawn cold-start phrase (next to `forge-memory recall`):

```
RMUX: 'python -m term.rmux help' surfaces the fleet (spawn/stop/kill/focus/logs/ls/watch/json).
       Cwd D:\Sinister Sanctum\projects\sinister-term\source must be on sys.path
       (or invoke from inside that dir). Composes with /agents + /me + /peer + /health.
```

### EVE.exe picker upgrade (eve-exe lane, queued)

Add an "R) Sinister rmux" picker entry → calls `python -m term.rmux watch`
in a new mintty (same shape as the .bat). Lets the operator reach rmux
without leaving the launcher.

### Cold-start propagation (session-start-auto-update doctrine)

Append the rmux verb table to:
- `CLAUDE.md` operator-tools quick-reference (sanctum master scope)
- `docs/OPERATOR-QUICK-REFERENCE.md` (one-line per verb)
- `_sinister-skills/09_REFERENCE/SANDBOX-GOTCHAS.md` (rmux invocations
  needing PYTHONIOENCODING=utf-8 + PYTHONPATH=...sinister-term/source)

### Brain entry adoption

Brain entry candidate: `_shared-memory/knowledge/sinister-rmux-unified-manager-2026-05-27.md`
— composes with `we-have-the-source-read-it-doctrine-2026-05-25` +
`automate-everything-no-operator-admin-2026-05-25` +
`no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` (operator override:
`.bat` allowed when explicitly requested as user-facing one-click).

### Fleet-update broadcast

This message is also being pushed via `automations/fleet-update.ps1
-Action Push` with `priority=high kind=feature-launch` so every running
agent surfaces it on their next poll.

---

## Try it (one operator command)

```
"D:\Sinister Sanctum\Sinister rmux.bat"
```

…or double-click the desktop copy. The mintty that opens stays alive
even after `rmux watch` exits (`--hold error`), so Ctrl+C → shell →
any other verb works without relaunching.
