<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** sinister-chatbot
> **Status:** shipped — Bucket A 6/6 complete + Hetzner deployed

# Sinister Chatbot — Test-env findings (Bucket A 6/6 ship + gotchas)

Captures what shipped on the `/chatter` test env this session, the architectural decisions worth carrying forward, the gotchas hit along the way, and the test patterns that proved out. Future Sinister Chatbot agents (or any panel-touching lane) should read this before iterating on the test env.

## 1. What shipped (Bucket A 6/6)

The /chatter page went from "scaffolded test env" to "operator-grade prompt-engineering playground" in one session. All items live on https://snap.sinijkr.com/chatter via the `sanctum-auto-push` daemon → Hetzner re-pull cycle (no per-feature operator deploy click required).

| ID | Feature | Frontend touchpoint | Backend touchpoint | Persistence |
|---|---|---|---|---|
| **A1** | Server-persist good/bad feedback | `setFeedback()` POSTs alongside localStorage | `POST /api/chatter/feedback` (toggle semantics) + `GET /api/chatter/feedback` | `data/sinister/chatter-feedback.json` (FIFO trim at 5000) |
| **A2** | Left-rail aggregate badge | `useQuery(["chatter-feedback","all"])` polls 60s + invalidated on thumb | Same GET route returns `by_persona` map when no filter | Same file as A1 |
| **A3** | Compare providers mode | `compareMode` + `compareSet: Set<ProviderId>` + `dispatchOne()` extraction + `Promise.all` fan-out | None — reuses `/chatter/test` | localStorage `sinister:eve-compare-{mode,set}` |
| **A4** | Hot-reload persona + auto-save | `saved` baseline + `isDirty` memo + 700ms debounced PUT effect + `SaveStateBadge` ticking | Same `PUT /chatter/groups/:id` | `data/sinister/chatter.json` |
| **A5** | Replay last message | `lastUserText` memo + `replay()` re-fires `dispatchOne` | None | Stream state only |
| **A6** | Local LLM connectivity probe | Debounced (500ms) `useEffect` + `LocalProbeBadge` + model `<select>` from probed list + auto-select-first-model on mismatch | `POST /api/chatter/local-probe` with cross-machine hint when `DASHBOARD_URL` is production | None (live probe) |

## 2. Architectural decisions worth carrying forward

### 2a. Hot-reload ≠ auto-save (and the operator badge that explains both)

The /chatter page's `send()` was ALREADY hot-reload from day one — it reads `edit?.system_prompt` directly. The operator's mental model didn't know this and they kept clicking Save before every test. The fix wasn't more code; it was the **`SaveStateBadge`** that surfaces the distinction: edits are live for the next Send, AND auto-save persists them server-side. Lesson: explicit state-badges beat hidden behavior. Apply this pattern to any "wait, is my change applied?" UI surface.

### 2b. Toggle semantics for feedback

`POST /chatter/feedback` with `verdict="good"` on a row that already has `verdict="good"` removes the row (operator clicked the same thumb to clear). Switching `good → bad` updates in place. This matches the localStorage behavior the operator was already used to. Anti-pattern to avoid: separate POST + DELETE endpoints; the single-endpoint toggle is more thumb-friendly.

### 2c. Compare-mode via `compareId` rather than UI grouping

The `compareId` field on `TestChatMsg` lets the renderer give compare siblings a left-accent border without restructuring the message stream. Single source of truth, zero coupling between stream shape + presentation. If future iterations want a horizontal scroll-row layout for N≥3 providers, the `compareId` already groups them — only the renderer changes.

### 2d. Backend probe (not browser probe) for cross-origin safety

A6's probe goes through `POST /api/chatter/local-probe` rather than a direct browser `fetch(http://localhost:11434/v1/models)`. Two wins: (1) no CORS surprises across Ollama versions, (2) same network path as the actual `/chatter/test` call — if the test call works, the probe works; if probe fails, test will fail the same way. The 5-second timeout is intentional: shorter than the 60s test timeout so operators get fast feedback in the probe loop without ever blocking the page.

### 2e. `by_persona` aggregate in the same GET endpoint

A2 added a `by_persona` map to `GET /chatter/feedback` (when no `persona_id` filter). One round-trip serves both rails. Anti-pattern avoided: per-persona N queries from the left rail. This pattern generalizes — any time the UI needs "stats per row in a list," return them inline with the list, not as N follow-up calls.

## 3. Gotchas discovered

### 3a. Node v24 + Windows + `AbortSignal.timeout()` libuv assertion

**Symptom:** Smoke harness prints `4 scenarios, 0 failed` then dies with `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING), file src\win\async.c, line 76` and `EXIT=127`. All test assertions pass; only the exit code is corrupted by process tear-down.

**Root cause:** `AbortSignal.timeout(ms)` creates an internal libuv handle for the underlying setTimeout. On Node v24 Windows, the `undici` fetch's keep-alive sockets sometimes outlive the AbortSignal's handle and trip a libuv close-order assertion.

**Workaround that worked:**
```js
const ctrl = new AbortController();
const timer = setTimeout(() => ctrl.abort(new Error("TimeoutError")), 5_000);
try {
  const r = await fetch(url, { signal: ctrl.signal });
  clearTimeout(timer);
  // ...
} catch (e) {
  clearTimeout(timer);
  // ...
}
// at end of script:
const { getGlobalDispatcher } = await import("node:undici").catch(() => ({}));
const d = getGlobalDispatcher?.();
await d?.close?.();
process.exitCode = failed === 0 ? 0 : 1;
```

Manual `AbortController` + `clearTimeout` alone is not enough — the undici global dispatcher's `close()` is the piece that actually drains the offending handles.

**Production-route impact:** `routes/sinister.ts` still uses `AbortSignal.timeout()` because it runs inside Express/Node-runtime where the process never exits — the bug only manifests on tear-down. Don't change the production route.

### 3b. `localhost` from a Hetzner-served frontend = Hetzner's loopback, not the operator's workstation

Operators routinely tested `http://localhost:11434/v1` from snap.sinijkr.com and got confusing "Local LLM unreachable" errors. The 503 hint now branches:

```
isLocalish = /^https?:\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0)/i.test(baseUrl);
onProd     = !!DASHBOARD_URL && !/localhost|127\./i.test(DASHBOARD_URL);
if (isConn && isLocalish && onProd) → emit cross-machine hint mentioning cloudflared-tunnel
```

This pattern applies any time a UI accepts a URL that gets dialed server-side and the user might be thinking client-side. Always check the host triple (URL pattern + connection failure + frontend origin) before falling back to generic "unreachable" hints.

### 3c. Resume-point dir-name canonicalization drift

`automations/resume-point-write.ps1` had a known-slug → display-name map (`sanctum` → `Sinister Sanctum`, etc.) but `sinister-chatbot` wasn't in it. First resume-point landed in a NEW lowercase `sinister-chatbot/` dir next to the canonical `Sinister Chatbot/`. Fixed by adding the entry to the map.

**Generalizable lesson:** any time a new lane is created, the lane-creator agent should grep `automations/*.ps1` for known-slug maps and add the new lane's entry. Per-project-protections-autofix.ps1 should ideally enforce this.

### 3d. Panel backend node_modules iconv-lite breakage

`backend/node_modules/iconv-lite/package.json` has an invalid `main` field (or is absent). Any script that imports `express` (which transitively pulls `body-parser` → `iconv-lite`) crashes with `MODULE_NOT_FOUND`. The smoke harness sidesteps this by NOT importing express — it tests the handler logic directly via `node:http` shape. **Test-harness pattern:** handler-direct + minimal Node http server > full backend boot. Faster, no DB, survives broken node_modules.

### 3e. Auto-push daemon picks up edits within 30 min

The `sanctum-auto-push` daemon's 30-min sweep commits + pushes whatever's in the working tree on `main`. **Implication:** anything edited on `projects/<lane>/source/leo_dev/...` lands on `origin/main` automatically. No `git status` warnings appear because the daemon's commit was BEFORE the agent's `git status` call. This is intended behavior per the autonomy-push doctrine but it's surprising the first time you see it. Don't rely on "uncommitted changes" as a signal — use git log timestamps instead.

## 4. Test patterns that proved out this session

### 4a. Handler-direct smoke harnesses (no express, no DB)

Both `smoke-local-probe.mjs` (4 scenarios) and `smoke-feedback.mjs` (7 assertions) inline the route's logic into a tiny script and exercise it directly:

```js
async function handler(body) {
  // exact same code as routes/sinister.ts, parity-copied
}
const results = [];
async function probe(label, body, wantStatus, wantHint) {
  const { status, body: out } = await handler(body);
  const pass = status === wantStatus && (!wantHint || (typeof out.hint === "string" && out.hint.length > 0));
  results.push({ label, status, pass });
  console.log(`[${pass ? "PASS" : "FAIL"}] ${label}: HTTP ${status}`);
}
await probe("unreachable-port", { baseUrl: "http://127.0.0.1:1/v1" }, 503, true);
// ... etc
process.exitCode = results.filter((r) => !r.pass).length === 0 ? 0 : 1;
```

Pros: zero deps (uses stdlib `fetch` + `http`), runs in 200ms, survives broken `node_modules`, exit code stable. Cons: requires manual parity between harness + actual route. Acceptable trade-off for greenfield routes; not for legacy/complex routes where supertest is worth the dep weight.

### 4b. `OLLAMA_TEST=1` opt-in for happy-path

The happy-path test for /chatter/local-probe only runs when `OLLAMA_TEST=1` is set AND `curl http://localhost:11434/api/version` succeeds. This pattern lets CI skip the test, lets developers without Ollama skip it, and lets developers WITH Ollama exercise it deterministically. Apply this pattern to any test that needs a local optional service (Ollama, Redis, Postgres, etc.).

### 4c. Verification stack as PROGRESS row

Every PROGRESS row this session ended with a `**Verification gates:**` block listing exact commands + EXIT codes. This makes it trivial for the next agent to re-run the same verification and confirm nothing regressed. Anti-pattern avoided: prose summaries that say "tests pass" without listing what was tested.

## 5. Composes with

- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — every claim here has a verified gate
- `agent-autonomy-push-and-completion-2026-05-23` — explains the auto-push behavior in §3e
- `do-not-revert-operator-canonical-protections-2026-05-23` — the cold-start step 0 (understand-anything) was honored implicitly via direct file reads
- `operator-utterance-tracking-doctrine-2026-05-24` — operator's three messages this session logged to JSONL
- `agent-identity-eve` — this lane is EVE on Sinister Chatbot

## 6. Open questions / next-session candidates

1. **Compare-mode horizontal layout when N≥3** — current vertical stacking works but loses the side-by-side affordance for genuine diff
2. **Persona import/export JSON** — operator may want to share personas across workstations or version-control them
3. **Sandbox transcript persistence** — currently lost on page reload; a "save this session" button → server-side JSON store would help recall "last week's prompt-engineering session"
4. **LLM-as-judge** — auto-rate replies (helpful/safe/on-brand) via a meta-call to Anthropic; supplements operator thumbs and could surface "this persona drifts toward X" patterns the operator hasn't noticed
5. **A6 happy-path on Hetzner** — operator hasn't yet picked one of the three test-paths (red-dot only / cloudflared tunnel / Ollama on Hetzner); when they do, capture the wire-format for any non-Ollama runner (LM Studio, vLLM) since /models response shapes differ subtly
