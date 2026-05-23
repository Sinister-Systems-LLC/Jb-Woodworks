# Leo Setup — Sinister Sanctum on a fresh Windows box

> **Author:** RKOJ-ELENO :: 2026-05-23

One-page bring-up. Install the prereqs, clone to the expected path, double-click the launcher. Skim "Common pitfalls" before your first run.

---

## 1. Prerequisites

Install in this order. The launcher (`tools/session-launcher/Sinister Start.bat`) probes for each — if any is missing it will warn or fall back.

### Git for Windows (required)

Provides `mintty.exe` / `git-bash.exe` / `bash.exe` — the bat probes these exact paths (lines 76-89):

```
C:\Program Files\Git\usr\bin\mintty.exe
C:\Program Files\Git\git-bash.exe
C:\Program Files\Git\bin\bash.exe
```

Install from <https://gitforwindows.org>. Accept defaults (the bat assumes `C:\Program Files\Git`).

### Claude Code CLI (required)

The `claude` command must be on PATH and **v2.1+** — earlier versions choke on the positional prompt the launcher passes as the cold-start phrase.

```powershell
claude --version
# expect: 2.1.x or newer
```

Install: <https://docs.claude.com/en/docs/claude-code/setup> (npm or native installer).

### Python 3.10+ (optional)

Only needed if you want to:
- Rebuild `EVE.exe` (`automations/eve-launcher/build.ps1` uses PyInstaller).
- Run `sinister-term` (the standalone Python terminal).
- Run any of the MCP bots directly instead of via Claude Code.

Standard install from <https://www.python.org/downloads>; check "Add to PATH".

### `ANTHROPIC_API_KEY` env var (required for full power)

Without it the fleet still runs (Claude Code itself uses your Anthropic login), but these features go dark per `docs/ENV-VARIABLES.md`:

- **RKOJ.exe Anthropic SDK direct path** falls back to slower `claude -p` subprocess.
- **Tier-3 bots** (`scribe`, `curator`, `sinister-chatbot` server-side) all return `{ok:false, error:"no API key"}`.

Set it (User scope — survives reboots, doesn't leak system-wide):

```powershell
[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-api03-...','User')
```

Restart any open shells. Format is the standard Anthropic SDK key `sk-ant-api03-...`.

Optional sibling keys (skip unless you need them): `GEMINI_API_KEY` (image-gen), `OPENAI_API_KEY` (Codex peer-review).

---

## 2. Clone + path setup

### Recommended: clone to the zero-config path

The bat defaults to `D:\Sinister Sanctum` when `SINISTER_SANCTUM_ROOT` is unset:

```powershell
git clone -b agent/sinister-sanctum/grant-autonomy-followup-2026-05-23 https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git "D:\Sinister Sanctum"
```

### Alternative: clone anywhere, point the env var at it

The bat probes `%SINISTER_SANCTUM_ROOT%` first (lines 43-46), then falls through to `D:\`, `C:\`, then `%USERPROFILE%\`.

```powershell
git clone -b agent/sinister-sanctum/grant-autonomy-followup-2026-05-23 https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git "E:\my-path\Sanctum"
[Environment]::SetEnvironmentVariable('SINISTER_SANCTUM_ROOT','E:\my-path\Sanctum','User')
```

### Switch to a different branch later

```powershell
git -C "D:\Sinister Sanctum" fetch origin
git -C "D:\Sinister Sanctum" checkout main
```

---

## 3. First-run sequence

1. **Copy the launcher to your Desktop** (or just run from the tools dir):

   ```powershell
   Copy-Item "D:\Sinister Sanctum\tools\session-launcher\Sinister Start.bat" "$env:USERPROFILE\Desktop\"
   ```

2. **Double-click** `Sinister Start.bat`.

3. **First run only** — the bat sees no `%USERPROFILE%\.sanctum-autonomy-granted` marker, so it triggers `automations/grant-claude-autonomy.ps1`. This writes the `bypassPermissions` defaults into `~/.claude/settings.json` and creates the marker. One-time, ~5 seconds.

4. **Plugin check** runs in the background (`automations/check-required-plugins.ps1 -AutoInstall -Silent`) — auto-installs `understand-anything`, `code-review`, `commit-commands` if missing. Logs to `%USERPROFILE%\.claude\sanctum-plugin-check.log`. Non-blocking.

5. **EVE.exe picker** opens in its own window. Pick a project:
   - `1`-`15` → spawn that project's lane (Sanctum, Showmasters, JB Woodworks, etc.)
   - `G` → grant autonomy re-run
   - `A` → all-lanes spawn
   - `N` → new project bootstrap
   - `R` → resume last
   - `K` → kill all sessions
   - `S` → status dashboard

If EVE.exe is missing or stale (zero bytes / `--version` fails within 3s), the bat falls through to the PowerShell picker at `automations/start-sinister-session.ps1` — same menu, slightly slower boot.

---

## 4. What you'll see on a healthy launch

- **~0.6s ASCII banner** — animated jcode-style "C" intro inside the spawned mintty window.
- **Status pill row**:
  ```
  sanctum :: resume :: claude-opus-4-7[1m] :: mcp:NN :: bots:NN :: --skip-perms
  ```
  Numbers vary by what MCP servers + bots loaded.
- **Claude Code UI** opens with the cold-start phrase pre-loaded as the first user message. EVE reads `CLAUDE.md` step 0 → invokes `understand-anything:understand-explain` on the lane root → then proceeds through cold-start steps 1-6.

You're live. The first turn will be EVE acknowledging the lane + reading hard rules.

---

## 5. Common pitfalls

### Zombie EVE.exe windows
A crashed picker can leave EVE.exe orphaned. Force-kill:
```powershell
taskkill /IM EVE.exe /F
```

### `index.lock` from a crashed git process
A crashed git command can leave `.git/index.lock` lying around — every later git call then errors with `Another git process seems to be running`. Remove it once you've confirmed no `git.exe` is actually running:
```powershell
Get-Process git -ErrorAction SilentlyContinue          # confirm none
Remove-Item "D:\Sinister Sanctum\.git\index.lock" -Force
```

### Plugin install appears hung
The background install can take 10-30s on a cold cache. Tail the log to confirm progress:
```powershell
Get-Content "$env:USERPROFILE\.claude\sanctum-plugin-check.log" -Tail 40 -Wait
```
If it's actually wedged, kill any orphaned `powershell.exe` running `check-required-plugins.ps1` and re-run the bat.

### Claude can't find the project
Symptom: cold-start references `D:\Sinister Sanctum\` files that don't exist on your box.
- Confirm the clone landed at `D:\Sinister Sanctum` OR `SINISTER_SANCTUM_ROOT` is set:
  ```powershell
  Test-Path "D:\Sinister Sanctum\CLAUDE.md"
  [Environment]::GetEnvironmentVariable('SINISTER_SANCTUM_ROOT','User')
  ```
- If you set the env var, restart the shell (env is cached at spawn time).

### "No spawn-capable shell found" warning
Git for Windows is missing or installed to a non-default path. Reinstall to `C:\Program Files\Git` or symlink the expected paths.

---

## 6. Verification commands

### Non-spawning prereq probe
```cmd
"D:\Sinister Sanctum\tools\session-launcher\Sinister Start.bat" --diagnose
```
Reports every probe (root, shells, EVE.exe, plugin script) without launching a session.

### Confirm you're on the right commit
```powershell
git -C "D:\Sinister Sanctum" log --oneline -5
```
Expect the top commit to match the operator's latest (currently `d587bcc fix(launcher): harden Sinister Start.bat spawn + ship EVE.exe build + diagnose flag` on branch `agent/sinister-sanctum/grant-autonomy-followup-2026-05-23`).

### Confirm Claude Code is installed + version-correct
```powershell
claude --version
```

### Audit all Sanctum env vars in one shot
```powershell
@(
  'ANTHROPIC_API_KEY','GEMINI_API_KEY','OPENAI_API_KEY',
  'SINISTER_VAULT_PASSPHRASE','LEO_ANTHROPIC_API_KEY',
  'SINISTER_HUB_ROOT','SINISTER_AGENT_NAME','SINISTER_SANCTUM_ROOT'
) | ForEach-Object {
  $v = [Environment]::GetEnvironmentVariable($_,'User')
  '{0,-30} {1}' -f $_, $(if ($v) { 'set' } else { 'unset' })
}
```

---

## See also

- `docs/ENV-VARIABLES.md` — every env var the fleet reads, full cross-reference.
- `CLAUDE.md` — the cold-start protocol EVE runs on every session.
- `SESSION-START/` — the 00-06 hard-rule sequence (also auto-loaded on cold start).
- `tools/session-launcher/Sinister Start.bat` — the launcher source if you need to read what's actually probed.
