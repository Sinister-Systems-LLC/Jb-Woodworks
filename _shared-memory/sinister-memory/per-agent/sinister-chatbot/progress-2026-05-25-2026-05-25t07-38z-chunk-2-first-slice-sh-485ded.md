---
format_version: 2
author: RKOJ-ELENO
slug: sinister-chatbot
heading_id: 2026-05-25-2026-05-25t07-38z-chunk-2-first-slice-sh-485ded
saved_at: 2026-05-26T21:11:31Z
length: 3748
category: fact
confidence: 0.500
trust: medium
source: adoption-sweep
---

# sinister-chatbot :: 2026-05-25T07:38Z — Chunk-2 first slice SHIPPED: HUMANLIKE_BASELINE injection (EVE-the-LLM voice)

**Loop iter 4.** Continued relentlessly from iter-3. Picked smallest-risk highest-value chunk-2 item: humanlike_baseline block prepended to safe-mode `buildChatterSystemPrompt`. 26 LOC insertion, 3 LOC deletion. Smoke re-verified, committed `f05b265`, pushed.

**What this shifts:**
- Safe-mode chat (default voice EVE uses when not in flirty/nsfw_of operating mode) now opens with EVE's humanlike contract: thinks before speaking, hesitates, has opinions, pushes back on rude requests, mirrors register, varies length, allows internal thoughts in *italics*.
- When `operatorPrompt` is set, it's now framed as `PERSONA NOTES (honor these):` UNDER the EVE-voice baseline (was: operator prompt was the entire system message). This is the EVE-as-LLM model: a base persona that absorbs niche-specific notes rather than replacing itself per persona.
- Flirty + nsfw_of modes intentionally UNCHANGED. They use the snap-girl voice (lowercase, no emojis, 2-8 word bubbles, JSON-array output) which is its own form of humanlike texture. Bolting EVE-voice italics + paragraph-variation onto that would break the snap-girl format contract.

**Verification:**
- `node leo_dev/backend/scripts/smoke-overseer-signals.mjs` → 26/26 PASS (unchanged; this change doesn't touch Overseer endpoints)
- Manual reasoning check: safe-mode return composition order is deterministic (HUMANLIKE_BASELINE → persona → directives → playbook); no exception paths introduced; no API surface changed.
- `tsc --noEmit` → deferred (local `node_modules` unhydrated per test-env-findings §3d).

**Deploy posture (Slice 4):**
- `origin/main` has advanced 3 commits past my branch's base: `b02430a` (RKA license sales) + `aa2fde6` (ban-checker truth fix) + `8e933ae` (auto-add-friend on push). None are my work; all are sister-lane (sinister-panel) merges.
- Operator's "push it all live to hetner" directive authorized the chatbot bundle. Merging my branch into main and deploying would ALSO ship those 3 sister-lane commits to prod — which I haven't reviewed and which expands scope beyond what was authorized.
- Per CLAUDE.md panel doctrine: *"Don't merge to main without operator authorization. Even tiny fixes."* + canonical-11 reversibility wall: prod deploy needs explicit operator green-light at merge moment.
- **Handoff (deploy-ready):** branch `agent/sinister-chatbot/dpo-export` is push-clean at `f05b265`. SSH to Hetzner is confirmed working (`ssh root@95.216.240.227` returns hostname + uptime). Once operator green-lights the merge, the deploy chain is one block:
  ```bash
  cd "D:/Sinister Sanctum/projects/sinister-chatbot" && \
    git checkout main && git pull --rebase origin main && \
    git merge --no-ff agent/sinister-chatbot/dpo-export -m "merge: agent/sinister-chatbot/dpo-export — Overseer signals + chatter redesign chunk-1 + humanlike baseline" && \
    git push origin main && \
    ssh root@95.216.240.227 "cd /opt/sinister-panel && git pull && bash leo_dev/scripts/remote-deploy.sh --with-backend"
  ```
- Post-deploy verification curls in `leo_dev/docs/CHATBOT-OVERSEER-INTEGRATION-2026-05-25.md` §"How to verify after deploy".

**Fleet-update tail (normal-pri, ack at end-of-turn per cold-start step 11a):**
- `fu-20260525032531-e7c63e` doctrine: eve-update-over-link-and-popup-doctrine-2026-05-25 (sanctum)
- `fu-20260525032535-601497` doctrine: sinister-vault-live-doctrine-2026-05-25 (sanctum)
- `fu-20260525032603-f3f667` doctrine: vault-github-sync-backup-doctrine-2026-05-25 (sanctum)

All sanctum-scope, no chatbot-lane action required per sanctum-scope-discipline doctrine.

**Commit:** `f05b265 chatter: HUMANLIKE_BASELINE injected into safe-mode system prompt (chunk-2 first slice)` pushed to `origin/agent/sinister-chatbot/dpo-export`.

---
