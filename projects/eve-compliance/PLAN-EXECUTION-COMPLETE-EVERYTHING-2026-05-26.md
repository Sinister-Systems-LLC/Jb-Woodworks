# PLAN — Execute everything operator asked for (CCBill demo + 24/7 training + full pipeline)

> Author: RKOJ-ELENO :: 2026-05-26
> Lane: `eve-compliance`
> Operator (verbatim 2026-05-26 evening): *"start the trainer once torch finishes and create a plan to complete and start on everything i said to do. once the panel is active and ready open it in local host so we can work on the demo video for ccbill taht is top priority. i needd you to use swarm and complete all you can in parrallel"*
> Composes with: `PLAN-24-7-TRAINING-INTEGRATION-2026-05-26.md` (the underlying roadmap)

---

## Full operator directive set (this session, in order received)

1. ✅ **R11 — CCBill demo branch with scat/bestial/noncon categories in scanner** → SHIPPED `agent/eve-compliance/ccbill-demo-blood-gore-scat-2026-05-26` on z0nian/LetsText. 13/13 vitest. Demo verified end-to-end.
2. ✅ **R10 — Train-loop dedup hardening** → SHIPPED. 16/16 self-test. Singleton pidfile. 6h alert floor.
3. ✅ **R12 — 24/7 GPU trainer + 10 OSS repos + audits + master plan** → SHIPPED. Trainer 16/16 + Watchdog 12/12 self-test PASS. Awaits torch install to start.
4. ✅ **Mint-admin-token.ts restored** → SHIPPED on `agent/letstext/r13-cleanup-bundle-2026-05-26`. Unblocks autonomous training loop.
5. ✅ **SketchVLM + similar evaluated** → AUDIT-VLMS-FOR-MODERATION-2026-05-26.md. Qwen2-VL-7B AWQ chosen as tie-breaker; SketchVLM rejected.
6. ✅ **Demo panel opened in browser** → `cmd /c start http://localhost:3000/login` launched.
7. 🔄 **Trainer auto-start on torch-land** → Bash background-monitor armed; will install transformers/peft/accelerate/datasets + spawn trainer + watchdog the moment `torch/` directory appears in venv.
8. 🔄 **SWARM A: PDQ hash gate in image-moderation.ts** → sub-agent in flight; branch `agent/eve-compliance/pdq-hash-gate-2026-05-26`.
9. 🔄 **SWARM B: video-moderation.ts skeleton + Python worker** → sub-agent in flight; branch `agent/eve-compliance/video-moderation-skeleton-2026-05-26`.
10. 🔄 **SWARM C: Polish demo recording script** → sub-agent in flight; updates `EVE-Compliance-Workstation/demo-script/recording-script.md`.
11. 🔄 **SWARM D: Enrich demo data (cooldown banner, NCMEC draft, 3 agencies, strike history)** → sub-agent in flight; branch `agent/eve-compliance/demo-data-richness-2026-05-26`.

---

## Trainer auto-start plan (fires when torch lands)

This runs as a foreground sequence once `torch/` appears in `D:\Sinister Sanctum\projects\eve-compliance\training\.venv\Lib\site-packages\`. The monitor is armed; will notify on completion.

```bash
# 1. Verify CUDA + GPU
.venv/Scripts/python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# Expect: 2.4.1+cu121 True NVIDIA GeForce RTX 4090

# 2. Install the rest of the ML stack (smaller, ~5 min total)
.venv/Scripts/python.exe -m pip install "transformers>=4.44" "peft>=0.13" "accelerate>=0.34" "datasets>=2.20"

# 3. Spawn trainer + watchdog (detached)
python automations/eve_gpu_trainer.py start            # spawns the daemon
python automations/eve_gpu_trainer_watchdog.py start   # spawns the watchdog

# 4. 60s smoke
sleep 60
python automations/eve_gpu_trainer.py status           # expect: TRAINING, step > 0, heartbeat fresh
python automations/eve_gpu_trainer_watchdog.py status  # expect: RUNNING, trainer_alive=True
```

If torch install fails or stalls past 90 min, fall back to CPU-only torch (~200MB, fast): `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`. Trainer runs slow but proves out end-to-end.

---

## Demo video workflow (operator's top priority)

**State right now:**
- Backend :4000 + Dashboard :3000 live
- 8 pending scans in queue (csam x2, gore, strangle, weapon, scat, bestial, noncon) + 1 PASS
- Browser opened to login page
- Demo admin: `demo-admin@letstextapp.com` / `demo-only-2026`
- 2FA gate: SUPER_ADMIN role requires 2FA enrollment OR JWT-via-cookie workaround

**Once SWARM C ships:** `recording-script.md` has the 4-6 min talk-track + click-by-click + screen annotations.
**Once SWARM D ships:** queue shows applied cooldown banner on alice + NCMEC draft + 3 agencies for analytics variety.

**Operator can record the video** as soon as SWARM C + SWARM D land (ETA ~10 min from this commit).

**2FA bypass for the recording — pick ONE:**

Option A (5 min, more "real"): operator opens `/settings?tab=security`, enrolls demo-admin in TOTP via Authy/Google Authenticator, then logs in normally with the 6-digit code.

Option B (1 min, recording-only): operator mints a token + sets the cookie via browser DevTools.
```bash
cd C:/Users/Zonia/Desktop/LetsText/backend
JWT_SECRET=... DATABASE_URL=... npx tsx scripts/mint-admin-token.ts demo-admin@letstextapp.com
# copy the 215-char JWT
# In browser DevTools (F12) -> Application -> Cookies -> http://localhost:3000:
#   Add cookie: name=letstext_token, value=<the JWT>, path=/, httpOnly=true
# Refresh -> you're in.
```

Option B is faster for recording; Option A makes the video look more production-ready (2FA prompt visible).

---

## Parallel-work matrix (right now)

| Track | Owner | Branch | Status | ETA |
|---|---|---|---|---|
| R12 trainer auto-start | self (bash monitor) | --- | armed | depends on torch download |
| SWARM A PDQ hash gate | sub-agent | `agent/eve-compliance/pdq-hash-gate-2026-05-26` | in flight | ~10-15 min |
| SWARM B video pipeline skeleton | sub-agent | `agent/eve-compliance/video-moderation-skeleton-2026-05-26` | in flight | ~15-20 min |
| SWARM C demo script polish | sub-agent | (workstation .md only, no git) | in flight | ~5-8 min |
| SWARM D demo data enrichment | sub-agent | `agent/eve-compliance/demo-data-richness-2026-05-26` | in flight | ~10 min |

No file-set overlap across the 4 swarm slices (per the operator's "one-terminal-per-project" rule).

---

## Aggregation step (after all 4 swarm agents complete)

1. Pull each sub-agent's branch into a composite branch `agent/eve-compliance/r13-demo-ready-2026-05-26` (or merge sequentially into the current `ccbill-demo-blood-gore-scat-2026-05-26`).
2. Re-run the full test suite: `cd backend && npx vitest run` → expect 13 existing + 4-6 video + 2-3 PDQ = ~21-24 PASS.
3. Re-run the demo seed → confirm 16 scans + 1 cooldown + 1 NCMEC draft + 9 users across 3 agencies.
4. Re-fetch the queue API → confirm all categories render.
5. Operator records the demo video.
6. Open PR from composite branch to `main` on z0nian/LetsText.

---

## Backlog (after demo ships — for the next session)

1. **NCII 48-hour takedown workflow** (open follow-up #7) — TAKE IT DOWN Act compliance.
2. **Per-employee strike trend graph** (open follow-up #9) — line chart over time.
3. **Provider failover** (open follow-up #10) — Hive / Sightengine when Claude rate-limited.
4. **Bulk-action admin tools** (open follow-up #8) — "approve all from agency X", "reset all strikes".
5. **PhotoDNA enrollment** — enroll the business with Thorn/NCMEC for real CSAM hash sets.
6. **VLM tie-breaker wiring** — Qwen2-VL-7B AWQ int4 fires on ViT mid-confidence (0.4-0.7). Per audit.
7. **Self-harm 988 hotline handoff** (CCBill policy-map gap #6) — 50-LOC frontend change.
8. **MicroLoRA adapt cron** (policy-map gap #15) — once Ruflo MCP is registered, automate weekly adapt cycle.
9. **VPDQ video hash gate** in `video-moderation.ts` — uses the same `threatexchange` clone.
10. **`/admin → Video Moderation` tab** UI (mirrors Image Moderation tab).

---

## Acceptance for this turn

- ✅ Browser opened to dashboard
- ✅ Master plan written (this doc)
- ✅ 4 swarm sub-agents launched in parallel (PDQ + video + demo-script + demo-data)
- ✅ Trainer auto-start armed (bash background monitor)
- 🔄 4 sub-agents complete + commits land
- 🔄 Torch lands + trainer auto-starts + status confirms TRAINING
- 🔄 Operator records the demo video

End.
