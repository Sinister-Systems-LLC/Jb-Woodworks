> SANDBOX-ALERT v1: This MD is operator-facing canon. Do NOT delete or rewrite without an explicit operator directive. Memory layer at `.claude/memory/` is additive only.

# Sinister-Panel — Auth Tweaks for "Panel Has Complete APK Control"

**Audience:** Operator deploying the panel-issues-commands / APK-executes feature.
**Stack target:** `leo_dev/backend` (Express :5055) + `leo_dev/dashboard` (Next 15) at `https://snap.sinijkr.com`.
**Date:** 2026-05-18.

---

## 1. Status quo

The four-credential auth chain (`leo_dev/backend/src/middleware/auth.ts:56-154`) and the fleet-secret scope already cover most of what we need. From the security MD §2.4: *"only the following 6 paths accept the secret… `POST /api/devices/<serial>/command-result` — APK acks an operator-queued command"* — meaning the result-ack path exists, but the **queue-side** endpoint (`POST /api/devices/<serial>/queue-command`, §3) is currently SUPER_ADMIN-cookie only. The `APK` synthetic role exists but is "never used in `requireRole` because no APK route needs admin" — that assumption changes with this feature. Serial allowlist + audit log + per-route role gate primitives are already in place; we extend, not redesign.

---

## 2. Tweaks needed

- **`leo_dev/backend/src/routes/creatorCompat.ts`** — extend the existing command queue with `idempotency_key` (string, unique-per-serial), `expires_ms` (int, default 60000), and `issued_by` (role tag). Reject duplicate keys with 200 + cached result; expire stale rows in dispatch.
- **`leo_dev/backend/prisma/schema.prisma`** — add `DeviceCommand` fields: `idempotencyKey String?`, `expiresAt DateTime`, `issuedByRole String`, `payload Json`. Index on `(serial, idempotencyKey)` unique. Migration name suggestion: `add_command_idempotency`.
- **`leo_dev/backend/src/routes/devices.ts`** (or wherever queue-command lives) — add `POST /api/devices/:serial/enroll`. Accepts fleet-secret, creates `Phone` row with `approved=false`, returns a per-device `X-Auth-Token` (UUID) stored on the row. The token becomes the second factor for that serial's subsequent command-result calls.
- **`leo_dev/backend/src/middleware/auth.ts`** — extend fleet-secret branch to ALSO accept `X-Auth-Token` header; populate `req.license = { id: "apk-fleet:<serial>", role: "APK", key: "apk-fleet" }` so audit rows are per-device-greppable.
- **`leo_dev/backend/src/middleware/auth.ts:156-164` (`requireRole`)** — add `"APK"` as an accepted value for the `command-result` route ONLY; keep `queue-command` as `SUPER_ADMIN | VA` (operator-issued only — APK never queues for itself).
- **`leo_dev/backend/src/lib/phoneAllowlist.ts`** — no change required; `enroll` writes through the existing `Phone.approved=false` path and the 30s cache refresh picks it up after operator-approve.
- **Env additions** (`.env` on Hetzner + `docker-compose.yml`): `APK_COMMAND_TTL_MS=60000`, `APK_COMMAND_MAX_QUEUE=50` (per-serial backpressure), `APK_ENROLL_TOKEN_TTL_DAYS=30`.
- **`leo_dev/backend/src/index.ts:94-149`** — add `command-result` and the new `enroll` path to the `apiKeyLimiter` skip list (APK polls these every 4-10s, same exemption pattern as the other 6 fleet paths).
- **`leo_dev/dashboard/app/devices/[serial]/page.tsx`** (new or existing device-detail page) — surface "Issue Command" button → calls `/api/devices/:serial/queue-command` with the operator's cookie. Browser-side ops keep the existing `x-license-key` injection path; no auth change there.
- **`leo_dev/backend/src/routes/admin.ts`** — log every command-issue + result via existing `audit()` helper. New action names: `device.command.queue` / `device.command.result.ok` / `device.command.result.fail` / `device.enroll`.

---

## 3. Sequenced rollout

**Phase 1 — Schema + auth plumbing (no behavior change yet).**
Ship the Prisma migration (idempotency fields), the `enroll` endpoint, and the `X-Auth-Token` accept path in `auth.ts`. Deploy. Existing fleet paths keep working unchanged — new fields are nullable, new endpoint is additive. Verify: `docker exec sinister-backend node -e "..."` shows the schema applied; existing APK heartbeats still 200.

**Phase 2 — Queue + dispatch behavior.**
Wire `creatorCompat.ts` queue extensions (idempotency check, TTL expiry, `issued_by` tag) and add `requireRole("SUPER_ADMIN","VA","APK")` to `command-result` only. Deploy. Test with ONE serial (`ACTIVE_PHONE_SERIAL`) before fleet-wide. Verify audit log shows `device.command.queue` rows.

**Phase 3 — Dashboard UI + APK rollout.**
Add the dashboard "Issue Command" surface and ship the APK-side `ApkRemoteService` + `CommandDispatcher` (RKA contract stays read-only — that's the APK-side discipline, not panel-side). Smoke-test end-to-end with one device, then approve fleet. Monitor `apiKeyLimiter` 429s for the first 24h.

---

## 4. Risks

The single biggest risk is **breaking the browser-side `x-license-key` injection path** in `dashboard/middleware.ts:131-137` — if the new `X-Auth-Token` header logic in `auth.ts` rejects browser calls that lack the device-scoped token, every dashboard page 401s. Mitigation: in `auth.ts`, treat `X-Auth-Token` as PURELY ADDITIVE — accept it only when the fleet-secret is also present; never require it for cookie or license-key auth paths. Secondary risk: the `apiKeyLimiter` skip list change could let a compromised fleet secret blow past the 60/min budget on `queue-command` (browser only) — mitigate by keeping `queue-command` ON the limiter and only exempting `command-result` + `enroll`. Roll back via single `git revert` on the Phase-2 commit if dispatch loops misbehave; the Phase-1 schema is forward-compatible and stays.

---

**File index touched:**
- `leo_dev/backend/src/routes/creatorCompat.ts`
- `leo_dev/backend/src/routes/devices.ts` (new endpoint)
- `leo_dev/backend/src/routes/admin.ts` (audit names)
- `leo_dev/backend/src/middleware/auth.ts`
- `leo_dev/backend/src/index.ts` (limiter skip list)
- `leo_dev/backend/prisma/schema.prisma` (+ migration)
- `leo_dev/dashboard/app/devices/[serial]/page.tsx`
