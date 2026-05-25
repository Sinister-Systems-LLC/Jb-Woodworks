# knott-gmail Login Recovery

Author: RKOJ-ELENO :: 2026-05-25 (Sub-Q)

## What happened

Operator ran EVE -> M)anage account -> L)ogin for the `knott-gmail` slot at
~03:14Z 2026-05-25. The mintty sandbox launched and the operator pasted the
OAuth code into the wizard, which wrote it to:

```
C:\Users\Zonia\AppData\Local\Temp\sinister-claude-login-knott-gmail-a1770bfb\.claude\.oauth-paste-relay.txt
```

But the sandbox bash process (which was supposed to consume the relay and run
`claude auth login` with the code on stdin) had already died or been closed
before the code arrived. The relay file sat unconsumed for ~4 hours.

Sub-Q ran `finalize_oauth_paste_relay.py` to attempt a last-mile exchange.
Result: the `claude auth login` CLI is fully interactive on Windows and does
NOT accept stdin-piped paste-back codes when run from a non-TTY subprocess
(it just hangs waiting for keyboard input). The 60s subprocess timeout fired,
so the exchange did not complete.

Additionally, Claude OAuth paste-back codes generally expire 10-30 minutes
after issuance. By the time recovery was attempted, the code was almost
certainly expired regardless.

## What was done

- Sub-Q wrote `automations/finalize_oauth_paste_relay.py` (~210 LOC) so any
  future orphaned relay can be re-attempted in ONE command without
  re-launching the full wizard.
- The OAuth relay file at the path above is left in place (operator may
  still want to inspect it). No production `.credentials.json` files were
  modified. The operator's main `~/.claude/.credentials.json` is untouched.

## How to retry (operator action, ~30 seconds)

The login itself is a USER action (per CLAUDE.md operator-canonical: "OAuth
in browser is a USER action and is fine"). Operator runs:

1. Double-click `Sinister Start.bat` (or open EVE.exe from the desktop).
2. Press `M` for Account Manager.
3. Press `L` for Login.
4. Select / type the slot name `knott-gmail`.
5. The wizard opens a fresh sandbox + browser tab. Sign into the Claude
   account belonging to knott-gmail.
6. Paste the redirect URL back into the wizard's `[paste]>` prompt OR let
   the browser hand the code directly to the CLI (whichever flow the latest
   `claude auth login` build defaults to).
7. The wizard now exchanges the FRESH code within its built-in timeout and
   writes `~/.claude/credentials.knott-gmail.json` automatically.
8. Verify: `python automations/claude-accounts.ps1 -Action Status` (or just
   re-open EVE and check the M)anage account panel — the `knott-gmail` row
   should now show `linked` green).

## Why we did NOT mark this slot logged-in despite having a paste-back code

Doctrine: `no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` rule 2
("Test before claiming"). The exchange did not produce a `.credentials.json`,
so the slot is NOT linked. Fabricating an entry in `claude-accounts.json`
without real creds would put a poison row in front of every future agent
spawn that round-robins through accounts.

## Future-proofing follow-up (queued, NOT shipped by Sub-Q)

The sandbox bash dying before relay consumption is a class bug. Two fixes
to consider:

1. **Detect dead sandbox at wizard side** — wizard polls for the sandbox
   PID; if dead and relay file present, refuse to write the code and
   surface a "sandbox died, re-launch" message instead of leaving an
   orphaned relay.
2. **Persistent retry queue** — orphaned relays get appended to
   `_shared-memory/oauth-relay-orphans.jsonl` with TTL; a startup hook
   re-spawns the wizard for any unexpired entry on EVE launch.

Neither is in Sub-Q scope.
