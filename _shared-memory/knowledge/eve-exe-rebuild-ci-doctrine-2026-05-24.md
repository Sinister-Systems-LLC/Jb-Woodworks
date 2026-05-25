<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->

# EVE.exe Rebuild CI Doctrine (analyzer gap-fill #3 of 3)

**Created:** 2026-05-24T23:38Z
**Authority:** Brain semantic-graph analyzer 2026-05-24T22:07Z recommendation #1:
> *"Surface #4 of session-start (eve.py rebuild) is the only manual gap; codify auto-rebuild-on-source-mtime + sibling-EVE notification + mirror-sync as a doctrine, not just a checklist."*

Completes the 3-doctrine analyzer gap-fill set (#1 brain-decay-implementation + #2 stale-state-reconciliation-pattern + #3 this one). Codifies the discipline that turns the session-start-auto-update-propagation checklist into an enforceable contract for eve.py edits.

---

## 1. The 5-surface propagation reality

Per `session-start-auto-update-propagation-2026-05-24` (sibling doctrine), there are five surfaces where fleet-wide changes land. Four auto-propagate; ONE does not:

| Surface | Auto-propagates? | What happens if you skip rebuild |
|---|---|---|
| `.ps1` automations | YES (read live each spawn) | n/a |
| `CLAUDE.md` hard-canonical blocks | YES (read fresh on cold-start) | n/a |
| Brain entries | YES (push to fleet-update + `_INDEX.md` row) | n/a |
| JSON configs | YES (read on each spawn) | n/a |
| **`eve.py` source** | **NO** | EVE.exe bundle stays stale; running instances hold OLD bundle until restart |

This doctrine binds the eve.py surface.

## 2. The post-eve.py-edit checklist (binding)

Any lane that touches `automations/eve-launcher/eve.py` (or any module under `automations/eve-launcher/*.py`) MUST execute, same iter, before claiming the change "shipped":

```powershell
# (1) Parse-clean check
python -m py_compile automations\eve-launcher\eve.py

# (2) Trigger auto-rebuild + mirror sync via verify-eve-features.ps1
powershell -File automations\verify-eve-features.ps1 -AutoRebuild -SyncMirror

# (3) If verify-eve-features.ps1 reports STALE / FAIL, manually wipe + retry:
Remove-Item -Recurse -Force automations\eve-launcher\dist\EVE,automations\eve-launcher\build\EVE -ErrorAction SilentlyContinue
cmd /c "automations\eve-launcher\build-eve-exe.bat"

# (4) Verify byte-match dist <-> mirror (auto-stable-mirror in build-eve-exe.bat does this;
#     fallback robocopy /MIR if mismatch detected)
```

**If any of (1)-(4) fails:** the change is `claimed-but-unverified` per `no-bullshit-tested-before-claimed-doctrine-2026-05-23`. NOT shipped.

## 3. Known rebuild failure modes (from iter 11-13 + 14 incidents)

### 3a. Windows Defender chmod race
- **Symptom:** `FileNotFoundError: [WinError 2]` at PyInstaller `os.chmod(dest_path, 0o755)` step
- **Cause:** Defender scans `dist/EVE/EVE.exe` immediately after PyInstaller drops it; lock prevents chmod
- **Fix:** retry (timing-dependent; second attempt usually succeeds)

### 3b. PyInstaller modulegraph TypeError on `--hidden-import`
- **Symptom:** `TypeError: required field "func" missing from Call`
- **Cause:** PyInstaller analysis chokes on certain Python 3.12 AST nodes for some hidden-imported modules
- **Fix:** drop the `--hidden-import` line for that module; if eve.py has a `try: import <mod>` block, PyInstaller's normal analysis follows it without `--hidden-import`

### 3c. Stale `dist/EVE` blocks rebuild
- **Symptom:** `ERROR: The output directory ... is not empty. Please remove all its contents`
- **Cause:** Prior rebuild left partial contents; `rmdir /S /Q` in build-eve-exe.bat couldn't fully clean (file locks)
- **Fix:** manual `rm -rf dist/EVE build/EVE` (Git Bash) OR `Remove-Item -Recurse -Force ...` (PowerShell) before re-running

### 3d. verify-eve-features.ps1 `-SyncMirror` stale logic
- **Symptom:** Reports "mirror synced OK" but `~/.eve/EVE.exe` mtime/size unchanged
- **Cause:** Old `--onefile` sync logic copies only EVE.exe, ignoring the `_internal/` tree required by `--onedir` builds
- **Workaround:** force-sync via `robocopy "dist\EVE" "%USERPROFILE%\.eve" /MIR` (matched dir-tree)
- **Permanent fix shipped iter 12 (sibling lane):** `build-eve-exe.bat` now auto-xcopy-mirrors the entire dist/EVE tree to `%USERPROFILE%\.eve` after every successful build

### 3e. mintty `-t TITLE` choke (iter 11 incident)
- **Symptom:** Spawned mintty PID logged but window invisible (process exits immediately)
- **Cause:** title containing `::` + spaces choked mintty arg parsing
- **Fix:** removed `-t TITLE` from mintty args; bash OSC printf in launch.sh sets title from inside the shell

### 3f. powershell.exe -File with bash-style POSIX path (iter 11 incident)
- **Symptom:** bash-line `powershell.exe -File "$bashSanctumRoot/automations/foo.ps1"` fails silently
- **Cause:** `$bashSanctumRoot` is `/d/Sinister Sanctum/...` (POSIX); powershell.exe wants Windows path
- **Fix:** use `$SanctumRoot` (the Windows-format variable) instead

## 4. Live verification commands

```powershell
# Status snapshot
powershell -File automations/verify-eve-features.ps1

# Full rebuild + sync (canonical post-eve.py-edit invocation)
powershell -File automations/verify-eve-features.ps1 -AutoRebuild -SyncMirror

# Byte-match check (catches stale mirror)
$src = (Get-Item "automations/eve-launcher/dist/EVE/EVE.exe").Length
$dst = (Get-Item "$env:USERPROFILE/.eve/EVE.exe").Length
if ($src -ne $dst) { Write-Host "MISMATCH src=$src dst=$dst -- robocopy /MIR" }
```

## 5. Sibling-EVE notification protocol

When eve.py edit ships, push a `fleet-update` row with priority=high so OTHER spawned EVE.exe instances see the update. They can choose to close+reopen at next operator interaction.

```powershell
powershell -File automations/fleet-update.ps1 -Action Push -Kind fix -Priority high `
    -PushedBy <slug> -Message "eve.py edited (<feature>); rebuild OK + mirror synced. Close+reopen EVE.exe to pick up."
```

## 6. Anti-patterns

1. **Edit eve.py + claim shipped without rebuild** -- bundle stale; operator sees old binary; gets confused.
2. **Skip the byte-match check** -- mirror can be stale even when build "succeeds" (cf. 3d).
3. **Retry rebuild without clean wipe** -- partial dist/EVE contents block PyInstaller (cf. 3c).
4. **Add `--hidden-import` for every imported module** -- PyInstaller modulegraph chokes on some; rely on the normal `try: import` followed by analysis.
5. **Skip fleet-update push after rebuild** -- other spawned EVE.exe instances stay on old bundle without knowing.

## 7. Composes with

- `session-start-auto-update-propagation-2026-05-24` (sibling's; this doctrine BINDS the eve.py surface from that 5-surface map)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 4 self-audit; rebuild = part of the smoke evidence)
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R2 EVE.exe-reachable on next spawn)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (claim mesh-lock on eve.py before edit; release after rebuild)
- `stale-state-reconciliation-pattern-2026-05-24` (3d mirror-mismatch is a stale-state instance; reconcile via byte-match check)
- `eve-exe-uniform-ui-infinite-accounts-2026-05-24` (UI changes go through this rebuild discipline)

## 8. Verification

```powershell
# This doctrine itself is operator-canonical preference; reinforce when cited:
powershell -File automations/brain-decay-score.ps1 -Action Reinforce -Slug eve-exe-rebuild-ci-doctrine-2026-05-24
```
