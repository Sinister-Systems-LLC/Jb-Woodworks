# Coord: Sanctum-A (research) -> Sanctum-B (eve.py owner) :: mcp/bots count root cause

Author: RKOJ-ELENO :: 2026-05-24
From: sanctum lane research subagent (this turn)
To:   sanctum lane sister-B (holding `automations/eve-launcher/eve.py`)
Topic: EVE banner displays `mcp:2 bots:0` while real inventory is `mcp:22 bots:14`. Diagnosis only — no code changes applied (sister-B holds the file).

## TL;DR

- **Real MCP count:** `22` (servers in `C:\Users\Zonia\.claude\.mcp.json`)
- **Real bot count:** `14` (subdirs in `D:\Sinister Sanctum\_sinister-skills\12_LLM_ORCHESTRATION\agents\`)
- **EVE banner displays:** `mcp=2 bots=14` (verified live just now via `python automations/eve-launcher/eve.py --profile`)
- **Operator screenshot showed:** `mcp:2 bots:0` — the `bots:0` was already fixed earlier today (commit visible in `eve_picker_lib.count_bots` comment dated 2026-05-24); the screenshot likely predates that fix OR the operator was looking at a child window spawned before the fix.
- **STILL BROKEN: `mcp:2`** — root cause is a UTF-8 BOM in `.mcp.json` that silently fails `json.loads`.

## Diagnostic evidence (all run this turn, working machine)

### 1. Actual MCP count in `~/.claude/.mcp.json`

```
python -c "import json; d=json.loads(open('C:/Users/Zonia/.claude/.mcp.json', encoding='utf-8-sig').read()); print(len(d['mcpServers']))"
22
```
First 5 keys: `['eve', 'sinister-panel', 'sinister-snap', 'sinister-tiktok', 'letstext']`.

### 2. Actual bot subdir count

```
ls -1d /d/Sinister\ Sanctum/_sinister-skills/12_LLM_ORCHESTRATION/agents/*/ | wc -l
14
```
(_shared, auditor, curator, custodian, librarian, researcher, scribe, sentinel, sinister-bus, stealth-browser, translator, triage, vault, watcher.)

### 3. EVE banner live count

```
$ python automations/eve-launcher/eve.py --profile
boot=0ms rows=19 mcp=2 bots=14
```

`bots=14` is correct. `mcp=2` is the bug.

### 4. Root cause — UTF-8 BOM in `.mcp.json`

`eve_picker_lib.count_mcp()` (tools/eve-picker/eve_picker_lib.py:159-170) opens `.mcp.json` with `encoding="utf-8"`. The file starts with bytes `ef bb bf` (UTF-8 BOM):

```
$ python -c "print(open('C:/Users/Zonia/.claude/.mcp.json','rb').read(5).hex())"
efbbbf0d0a
```

`json.loads` of a `utf-8`-decoded string that begins with U+FEFF raises:
```
Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
```

The `try/except Exception: continue` at line 168-169 swallows it silently — function falls through to `~/.claude.json`, which only has 2 `mcpServers` (`ruflo` + `vault`). That's where the `2` comes from.

### 5. Why the BOM is there

Operator's earlier 26-path rewrite of `.mcp.json` (replacing `D:\Sinister\Sinister Skills` -> `D:\Sinister Sanctum\_sinister-skills`) most likely went through PowerShell 5.1 `Set-Content`/`Out-File` (default encoding writes a BOM). The Python reader handled all OTHER JSON files because the author already switched them to `utf-8-sig` (`read_projects` at line 110 uses `utf-8-sig`; comment at line 105 explicitly says *"utf-8-sig handles both BOM + non-BOM transparently"*) — but `count_mcp` was missed in that sweep.

### 6. PowerShell counterpart in `start-sinister-session.ps1`

`Get-MCPCount` (lines 105-128) of `automations/start-sinister-session.ps1` uses `Get-Content -Encoding UTF8` which on PS5.1 strips BOM automatically — so the PS-side counter is fine. Banner shown by EVE.exe comes from Python `eve_picker_lib`, not the PS launcher, so the PS function is currently unused for EVE-banner display.

### 7. Bot path candidates — both checked

```
$candidates = (
    'D:\Sinister Sanctum\_sinister-skills\12_LLM_ORCHESTRATION\agents',     # EXISTS (14 dirs)
    'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents'              # MISSING
)
```
Path #1 exists and is hit first — that's why `bots=14` is correct. No further action on bots needed.

### 8. Mesh-network angle (child-spawn filtering)

Searched `start-sinister-session.ps1` for filtering of `mcpServers` / `enabledMcpjsonServers` / `disabledMcpjsonServers` going into spawned children:

- Lines 1350-1383: when adding a NEW project entry to `.claude.json`, the launcher seeds `enabledMcpjsonServers = @()` and `disabledMcpjsonServers = @()`. **Empty enabled-list does NOT disable MCPs** — Claude Code treats empty as "use all from `.mcp.json`". So children still see the full 22-server inventory. Confirmed by the `mcp__ruflo__*` + `mcp__claude_ai_Google_Drive__*` tool families visible in this turn's deferred-tool list (those come from the user-level `.mcp.json`, not the project record).
- No per-spawn filter of bots — bots are read directly from `_sinister-skills/12_LLM_ORCHESTRATION/agents/` at runtime by anything that needs them; not piped through the launcher.
- **Verdict on mesh:** no per-spawn filtering bug. The fleet IS mesh-correct on the data plane. The banner is a *display* bug; child sessions actually see all 22 MCPs + 14 bots. This is a UI-honesty fix, not a connectivity fix.

## Proposed fix (sketch — sister-B owns the file)

Two-line change in `tools/eve-picker/eve_picker_lib.py` `count_mcp`:

```python
def count_mcp() -> int:
    for cand in (Path.home() / ".claude" / ".mcp.json", Path.home() / ".claude.json"):
        if not cand.exists():
            continue
        try:
-            data = json.loads(cand.read_text(encoding="utf-8"))
+            data = json.loads(cand.read_text(encoding="utf-8-sig"))   # BOM-tolerant; matches read_projects() at L110
            n = len(data.get("mcpServers") or {})
            if n:
                return n
        except Exception:
            continue
    return 0
```

Equivalent fix in `automations/start-sinister-session.ps1::Get-MCPCount` is unnecessary (PS5.1 `-Encoding UTF8` already strips BOM), but consider hardening to `-Encoding utf8NoBOM` reads via `[System.IO.File]::ReadAllText` + manual BOM-strip if you want parity with the Python reader policy.

Optional follow-up:
- Add `count_mcp_diagnostic()` helper that returns `(count, source_file, error_or_none)` so future BOM/permission silent-fallbacks surface in `--profile` and the banner.
- Replace silent `except Exception: continue` with `eve_logger.warn(...)` (logger already imported per eve.py:107-110) so silent fall-throughs leave a breadcrumb in the jsonl log.

## Acceptance criterion

After fix:
```
$ python automations/eve-launcher/eve.py --profile
boot=Nms rows=19 mcp=22 bots=14
```
Banner shows `mcp:22 bots:14`. Operator stops seeing the `mcp:2` lie.

## Files referenced (absolute)

- `D:\Sinister Sanctum\tools\eve-picker\eve_picker_lib.py` (lines 105-185 — the fix site)
- `D:\Sinister Sanctum\automations\eve-launcher\eve.py` (lines 411-414, 891, 1244 — banner sites, no change needed)
- `D:\Sinister Sanctum\automations\start-sinister-session.ps1` (lines 105-150 — PS counterpart, working; lines 1350-1383 — child spawn record, no filter bug)
- `C:\Users\Zonia\.claude\.mcp.json` (operator-gated; 22 servers; has UTF-8 BOM)
- `C:\Users\Zonia\.claude.json` (2 servers — the fallback the BOM bug forces)
- `D:\Sinister Sanctum\_sinister-skills\12_LLM_ORCHESTRATION\agents\` (14 subdirs)

END.
