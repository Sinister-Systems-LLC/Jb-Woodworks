> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# sinister-chatbot — first-run smoke

Pure step list. If a step diverges, stop and read `README.md` + `INTEGRATION.md`.

## 0. Prereqs

```powershell
node --version       # expects 20.x or 22.x
npm --version        # expects 10.x+
docker ps            # only if you want the Kameleo CLI; not strictly required for unit-only smoke
```

Plus a running **Kameleo CLI** at `http://localhost:5050`. Open the Kameleo GUI once on this machine so the token is GUI-cached, then start the CLI per Kameleo's own docs. Without it, `snapActions.ts` calls will fail — but `/health` + `/chatbot/generate` still work for a Claude-only dry run.

## 1. Wire env

```powershell
cd "D:\Sinister Sanctum\tools\sinister-chatbot"
Copy-Item .env.example .env -Force
notepad .env
```

Set at minimum:

```
ANTHROPIC_API_KEY=sk-ant-...
KAMELEO_URL=http://localhost:5050
PORT=5099
DB_URL=file:./dev.db
```

Save + close.

## 2. Install deps (~60s first run)

```powershell
npm install
```

Expected tail: `added <N> packages in <T>s`. If npm complains about peer deps, run `npm install --legacy-peer-deps`.

## 3. Generate the local Prisma client

```powershell
npx prisma generate
npx prisma migrate dev --name init
```

Expected: `migration "init" applied successfully` and `Generated Prisma Client`. Creates `dev.db` (SQLite).

## 4. Boot Express

```powershell
npm run start
```

Expected console tail:

```
[chatbot] server listening on http://127.0.0.1:5099
[chatbot] anthropic SDK: claude-haiku-4-5-20251001 default
[chatbot] kameleo target: http://localhost:5050
```

Leave the window open.

## 5. Smoke endpoints (PowerShell, second window)

```powershell
# health
Invoke-RestMethod http://127.0.0.1:5099/health
# expects: { "ok": true, "uptime_s": ..., "version": "..." }

# minimal LLM generate (no Kameleo / no Snap)
$body = @{
  threadId = 'smoke-1'
  persona  = @{ name='Test'; tone='friendly' }
  history  = @(@{ role='user'; text='hi' })
  fan      = $null
} | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:5099/chatbot/generate `
  -ContentType 'application/json' -Body $body
# expects: { "ok": true, "bubbles": [ "...", "..." ] }
```

If `/chatbot/generate` returns bubbles, the Anthropic-SDK path is wired correctly.

## 6. Kameleo + Snap smoke (optional; needs live Kameleo)

```powershell
# create a profile
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:5099/chatbot/kameleo/profile `
  -ContentType 'application/json' -Body '{ "label":"smoke-test" }'

# add a Snap friend (will open a Kameleo browser window)
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:5099/chatbot/snap/add `
  -ContentType 'application/json' -Body '{ "profileId":"<id-from-prev-call>", "target":"@somehandle" }'
```

If you see a Kameleo window pop up and navigate to Snapchat → wiring works.

## 7. Eve observations smoke

```powershell
$fan = @{
  id='fan-1'
  spendCents=125000
  lastInteractionAt=(Get-Date).AddDays(-2).ToString('o')
  birthday='1995-05-22'
  premium=$true
} | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:5099/chatbot/eve/observations `
  -ContentType 'application/json' -Body $fan
# expects: { "ok": true, "observations": [ { "label":"Top spender","tone":"accent",... }, ... up to 3 ] }
```

This proves `eveObservations.ts` is reachable. The chatEngine wiring (TODO in `chatEngine.ts::buildSystemPrompt`) is the next step the operator picks up.

## 8. Shut down

In the Express console: `Ctrl+C`. Wait for `[chatbot] graceful shutdown OK`. Window closes.

## When this smoke passes

1. Edit `D:\Sinister Sanctum\tools\_INDEX.md` → flip status from `building` → `shipped`.
2. Edit `D:\Sinister Sanctum\inventions\2026-05-19-sinister-chatbot.md` → bump status + tick the open checkbox in README ("desktop launcher tested end-to-end by operator").
3. Operator decides whether to wire `deriveEveObservations` into the prod system prompt (currently TODO-gated).

## Common failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `MODULE_NOT_FOUND lib/db` | dependency stubs not generated | `npm install` again; if persists check `prisma generate` exit code |
| `ANTHROPIC_API_KEY missing` | `.env` not loaded | confirm `.env` exists in this folder + restart `npm run start` |
| Kameleo HTTP 401 | CLI not authenticated | open Kameleo GUI once on this machine → re-launch CLI |
| Playwright "executable not found" | playwright deps not downloaded | `npx playwright install chromium` |
| Port 5099 in use | another process | `Get-NetTCPConnection -LocalPort 5099`, kill the PID, retry |

## Lane reminder

The OperatorRunning production source still lives in the Panel lane. Do NOT edit panel sources from this folder, do NOT edit Sanctum sources from the panel agent. Diffs between the two lanes should stay legible — only `llmClient.ts` and the new `eveObservations.ts` are intended to differ.
