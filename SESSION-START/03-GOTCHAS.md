# 03-GOTCHAS — sandbox classifier denies + green paths

Operator-curated list of paths that get blocked (by sandbox / classifier / project
policy) + the alternate green path. When operator asks for something that hits
one of these, propose the green path FIRST without attempting the blocked one.

This file is the always-on subset. Full mined catalog at `09_REFERENCE/SANDBOX-GOTCHAS.md`
(regenerate via `aggregate-gotchas.bat`).

## TikTok / Frida

- **Trip:** Frida-spawn against TikTok app — sandbox blocks as "anti-tamper-trip".
- **Green path:** Pure-API path (task #26 in TikTok-EMU). Real ideas left untested don't need Frida.
- **Source:** Operator session 2026-05-18; absorbed into `researcher.learned.md`.

## Recursive memory grep

- **Trip:** `grep -r` across `01_MEMORY/`/`02_MD_ARCHIVE/` for "sandbox deny" patterns flagged as recon-for-bypass.
- **Green path:** Use `aggregate-gotchas.bat` (operator-owned PowerShell script) to produce the catalog. Operator runs; bots read.

## Scheduled-task install

- **Trip:** Claude registering Windows Scheduled Tasks (e.g., SinisterCustodian) — sandbox blocks as "unauthorized persistence".
- **Green path:** Operator runs `12_LLM_ORCHESTRATION/agents/custodian/install-task.ps1` manually.

## Source-side file modification

- **Trip:** Writing into `C:\Users\Zonia\Desktop\*` project trees without explicit operator confirmation — would create unaudited side effects in their daily workspace.
- **Green path:** Generate stubs at `01_MEMORY/<project>/_to-copy-to-source/` and let `Prepare-Migration.bat` move them.

## Hetzner SSH

- **Trip:** Claude shell-out to SSH against Hetzner VPS — no credentials, sandbox shouldn't anyway.
- **Green path:** Operator's `Sinister_OneClick_Deploy.bat` (per project) or our `Deploy-Hetzner.bat` orchestrator. Bots read state via `researcher.summarize_url` + `Check-Hetzner-State.bat`.

## Fetching dual-use external code

- **Trip:** Auto-fetching `AKCodez/hackingtool-plugin` (183 offensive-security tools) — sandbox flags as "integrating external code with offensive capabilities".
- **Green path:** Operator authorizes explicitly. Design exists in `_logs/restore-points/2026-05-18-phase8i-sinister-bots.md` (RE'd, not cloned).

## Anthropic API key handling

- **Trip:** Reading / writing files matching `sk-ant-*` patterns — auditor blocks.
- **Green path:** Operator sets via `[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')`. Bots read via `os.environ`.

## PowerShell 5.1 native-stderr quirk

- **Trip:** `schtasks.exe /Query 2>$null` still wraps stderr in `NativeCommandError`, fails `ErrorActionPreference=Stop` scripts.
- **Green path:** Use `cmd /c "schtasks ... >NUL 2>NUL"` for full stderr isolation. Already applied in `install-task.ps1`.
