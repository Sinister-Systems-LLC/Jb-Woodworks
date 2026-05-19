> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Themed session launcher — the reusable pattern

Every Sinister project (and LetsText) benefits from the same cold-start ritual: double-click a Desktop bat → cinematic boot → live telemetry → surface picker → opening phrase on clipboard → memory docs in Notepad. The pattern is shipped in two reference implementations and this doc is what the third / fourth / fifth uses to skip the discovery curve.

## Reference implementations

| Project | Desktop bat | PowerShell launcher | Accent |
|---|---|---|---|
| Sinister Sanctum | `C:\Users\Zonia\Desktop\Start-Sinister-Session.bat` | `D:\Sinister Sanctum\automations\start-sinister-session.ps1` | purple `#7A3DD4` |
| LetsText 2.0 | `C:\Users\Zonia\Desktop\Start-LetsText-Session.bat` | `D:\LetsText\automations\start-letstext-session.ps1` | iOS blue `#0A84FF` |

## Anatomy of a launcher

Eight sections, top to bottom. Reuse the function helpers verbatim; swap the brand colour, ASCII logo, telemetry queries, surface picker options, and opening-phrase hashtable.

1. **Param block** — `[CmdletBinding()] param([string]$Surface = '', [switch]$NoNotepad, [switch]$Fast)` plus any project-specific switches. `-Fast` is the smoke-test escape hatch (skips every `Start-Sleep`).
2. **Theme palette** — six PowerShell colour tokens (`$Brand / $Bright / $White / $Dim / $Soft / $Accent` + semantic `$Warn / $Ok`). Keep names identical across projects so the helpers below stay portable.
3. **Animation helpers** — `Say`, `Pause-Beat`, `Type-Line`, `Draw-Bar`, `Spin-Check`. Copy verbatim from the Sanctum launcher; honour `-Fast` in every one.
4. **Live telemetry** — project-specific queries: dev server `Invoke-WebRequest` with short timeout, most-recent file mtime, memory file sizes, active plan from `~/.claude/plans/`, deferred-count regex, current round / version read from a canonical source (NOT hardcoded — see *Round / version source* below).
5. **Opening sequence** — block-letter ASCII logo + boot bars + auth handshake + greeting + telemetry panel. Padding column for the telemetry rows MUST be `≥ max(left-cell-length) + buffer` (use 30; padding 20 collides if the left cell hits 20 chars).
6. **Surface picker** — 1..N options + a free-form "other" branch. `if (-not $Surface) { ... }` to allow CLI override via `-Surface inbox`.
7. **Opening phrase** — `$openings = @{ 'surface-key' = "tailored prompt..." }` hashtable. Phrases SHOULD interpolate the dynamic round/version variable, NOT hardcode it. Copy to clipboard via `Set-Clipboard`.
8. **Memory doc auto-open** — `Start-Process notepad.exe -ArgumentList "<file>"` for the project's read-first docs. Honour `-NoNotepad`.

## Three gotchas you WILL hit (shortcut around them)

### 1. PowerShell 5.1 + em-dash without BOM = parse error

Symptom: `MissingEndCurlyBrace` or `Unexpected token` deep in the file, far from any visible problem. Cause: non-ASCII chars (`—`, `–`, `…`, smart quotes) get misinterpreted byte-by-byte without a BOM. Fix: save the file as **UTF-8 with BOM**:

```powershell
$path = 'D:\YourProject\automations\start-yourproject-session.ps1'
$content = Get-Content $path -Raw -Encoding UTF8
[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($true))
```

See `_shared-memory/knowledge/powershell-emdash-non-ascii.md` for the long version. This gotcha bites both Sanctum and LetsText launchers; budget 60 seconds the first time you cold-launch a new sibling.

### 2. `.PadRight(N)` collides when left-cell is exactly N

Symptom: telemetry row shows two cells smushed together — `s=20.0 KB / t=11.9 KBR.md decoder first`. Cause: `.PadRight(20)` on a 20-char string adds zero spaces. Fix: pad to **30** for telemetry rows (the safe ceiling for short-but-bounded strings).

### 3. Hardcoded round / version rots fast

Symptom: launcher says "round 47+" three weeks after round 54 shipped. Fix: read the canonical truth on every launch — typically a comment in the project's `CLAUDE.md` front matter:

```powershell
$currentRound = 0
$claudeMd = Join-Path $ProjectRoot 'CLAUDE.md'
if (Test-Path $claudeMd) {
    try {
        $firstLine = Get-Content $claudeMd -TotalCount 1 -ErrorAction SilentlyContinue
        if ($firstLine) {
            $m = [regex]::Match([string]$firstLine, 'round:\s*(\d+)')
            if ($m.Success) { $currentRound = [int]$m.Groups[1].Value }
        }
    } catch {}
}
# fallback to s.md scan, then a sane constant
```

Then interpolate `$currentRound` everywhere the round number appears — telemetry row, `$openings` strings, surface-picker descriptions.

## Desktop bat (the 25-line wrapper)

```bat
@echo off
REM ============================================================
REM  Start-<Project>-Session.bat
REM  Author: <agent name> (Claude agent, YYYY-MM-DD)
REM ============================================================

TITLE <Project> :: Session Start

IF NOT EXIST "D:\<Project>\automations\start-<project>-session.ps1" (
    echo [FAIL] start-<project>-session.ps1 not found
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\<Project>\automations\start-<project>-session.ps1" %*
exit /b %ERRORLEVEL%
```

`%*` is the only critical token — it forwards `-Fast`, `-NoNotepad`, `-Surface <name>`, and any future switches the PS1 grows.

## Smoke-test recipe

Verify your new launcher with one command before shipping:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\<Project>\automations\start-<project>-session.ps1" -Fast -Surface <default> -NoNotepad
# Then in a fresh terminal:
Get-Clipboard | Select-Object -First 1
```

Expected:
- Exit code 0
- Cinematic boot renders without `ParseException` or `MissingEndCurlyBrace`
- Telemetry rows show visible column gaps
- Clipboard contents start with your composed opening phrase

If any of those fail, walk the gotchas above in order.

## Accent rules (binding, per `docs/UI-DESIGN-SYSTEM.md`)

- Sanctum-side surfaces (master agent, RKOJ, sanctum-* tools) → **Sanctum purple** `#7A3DD4`
- Panel-side / LetsText / product UIs without bespoke brand → **iOS blue** `#0A84FF`
- Don't invent new accents — pick one of the two

## Authorship line

Every new `.bat` / `.ps1` carries an author line per Sanctum standing rule #7. Format:

```bat
REM Author: <Agent Name> (Claude agent, YYYY-MM-DD)
```

```powershell
# Author: <Agent Name> (Claude agent, YYYY-MM-DD)
```

When you cross-lane-touch an existing launcher, append a "Last-touched" comment beside the original Author rather than overwriting it. Both lines preserved.

## Cross-references

- Sanctum launcher source: `D:\Sinister Sanctum\automations\start-sinister-session.ps1`
- LetsText launcher source: `D:\LetsText\automations\start-letstext-session.ps1`
- BOM gotcha: `_shared-memory/knowledge/powershell-emdash-non-ascii.md`
- Padding gotcha (this doc, section above)
- Authorship rule: `_shared-memory/DIRECTIVES.md` standing rule #7
- Accent rule: `docs/UI-DESIGN-SYSTEM.md`
- Cold-start protocol (what the launcher's opening phrase invokes): `SESSION-START/README.md`
