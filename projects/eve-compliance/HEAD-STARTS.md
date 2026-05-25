# EVE Compliance — head-starts + jump-starts catalog

> Author: RKOJ-ELENO :: 2026-05-25 (R8)
> Operator hard-canonical 2026-05-25T13:04Z: *"pull all head starts and jump starts you can get for this"*
> Source: `_shared-memory/inbox/eve-compliance/2026-05-25T1245Z-from-research-github-prior-art.md`
> Status legend: 🟢 pulled-now / 🟡 wired-pending-install / 🔴 future-iter / ⚪ documented-only

This catalog maps every open-source resource we should adopt to accelerate the EVE compliance system, ranked by adoption-friction (zero-friction first). Each entry has a concrete pull-this-now action.

---

## P0 — pull NOW (zero-friction, high-value)

### 🟡 Meta PDQ perceptual hash (`facebook/ThreatExchange/pdq/python`)

**What:** Real perceptual hash that survives resize/recompress/crop. Replaces our sha256 placeholder so `CSAM_HASH_MATCH` fires on edited reuploads, not just byte-identical.
**Repo:** https://github.com/facebook/ThreatExchange/tree/main/pdq/python
**Pull action:**
```bash
pip install pdqhash threatexchange
```
**Wiring:** `backend/src/lib/image-moderation.ts` → swap `fetchSha256` for a Node child-process call to a tiny Python helper at `backend/scripts/compute-pdq-hash.py`. Output: 256-bit PDQ signature + quality score (0-100). Existing `perceptualHash` field already TEXT-shaped.
**Effort:** S (~80 LOC bridge + new script)
**Unblocks:** open follow-up #3 deep version + NCMEC HashList integration.

### 🟡 NCMEC HashList sync via `python-threatexchange`

**What:** CLI for syncing known-CSAM hash lists from Meta's ThreatExchange API (includes NCMEC HashList feed once we have NCMEC partnership credentials).
**Repo:** https://github.com/facebook/ThreatExchange/tree/main/python-threatexchange
**Pull action:**
```bash
pip install threatexchange
threatexchange match --signature-type pdq --collab-config <conf>
```
**Wiring:** Scheduled job (schtask) that pulls fresh hash lists daily into our `ContentScan` table seeded with `wasGoodCatch=true` + `scanResult=CSAM_HASH_MATCH` so the existing `lookupKnownBadHash` path picks them up automatically. No schema change needed.
**Effort:** M (NCMEC partnership credential gate; tech is straightforward)
**Unblocks:** Real-world CSAM blocking at the federal known-set tier.

### 🟢 ROOST awesome-safety-tools (bookmarked entry point)

**What:** Curated meta-directory of every open-source safety tool.
**Repo:** https://github.com/roostorg/awesome-safety-tools
**Pull action:** Already cited in `inbox/eve-compliance/2026-05-25T1245Z-from-research-github-prior-art.md`. Bookmark it as the canonical lookup for every future follow-up.
**Effort:** 0 (informational)

### 🟢 GantMan NSFW model (5-class softmax, pre-trained)

**What:** Local-inference NSFW classifier (Drawings/Hentai/Neutral/Porn/Sexy). Zero per-call cost, <50ms inference, complements our Claude classifier (cheap pre-filter for the easy 95%).
**Repo:** https://github.com/GantMan/nsfw_model
**Pull action:** Download `nsfw_mobilenet2.224x224.h5` (or TFJS model) into `EVE-Compliance-Workstation/models/nsfw/`. Wire as a Node tfjs-node call BEFORE the Claude path: if model returns confidence ≥0.95 + category in {Drawings,Hentai,Neutral,Sexy,Porn-with-no-other-flags} skip Claude entirely; only escalate to Claude on ambiguous OR when policy needs nuance (CSAM/gore/non-consent are Claude's domain).
**Effort:** M (~150 LOC tfjs-node integration)
**Unblocks:** Cost optimization + open follow-up #10 (vision-provider failover).

### 🟢 Cleanlab review-queue prioritization

**What:** Detects label noise + scores which admin-reviewed samples are highest-signal for retraining. Sorts queue by "information gain if labeled" instead of FIFO.
**Repo:** https://github.com/cleanlab/cleanlab
**Pull action:**
```bash
pip install cleanlab
```
Wrap around our existing `backend/scripts/export-moderation-training.ts` JSONL output. Cleanlab takes (predicted_label, true_label, probs) and returns per-row "label quality" scores.
**Effort:** S (~60 LOC wrapper script)
**Unblocks:** open follow-up #6 (training pipeline automation).

---

## P1 — wire next iter (medium friction, high-value)

### 🟡 Osprey rules engine (Discord-donated, ROOST-maintained)

**What:** Replaces our hand-coded 5-strikes-then-24h-cooldown TypeScript with a per-agency JSON DSL. Crucial for the operator's stricter/looser-per-agency requirement.
**Repo:** https://github.com/roostorg/osprey
**Pull action:**
```bash
git clone https://github.com/roostorg/osprey D:/Sinister\ Sanctum/_external/osprey
```
Study `example_rules/` then port our strike logic to SML rules. Keep TS thresholds as defaults while we shake the new path out.
**Effort:** L (~500 LOC port + tests; introduces a new runtime dep)
**Unblocks:** open follow-up #8 (bulk admin tools) + per-agency policy variance.

### 🟡 Coop review platform (Cove-donated, ROOST-maintained)

**What:** TypeScript + Postgres review platform — closest existing OSS project to what we built. Has NCMEC CyberTipline integration shipped (we have schema-only).
**Repo:** https://github.com/roostorg/coop
**Pull action:** Don't import wholesale (our system is further along on the LLM-classifier side). Cherry-pick:
1. The NCMEC API client code (we have placeholder; they have working flow)
2. The queue-routing pattern (assign cases to reviewer teams)
3. The bulk-actions UX
**Effort:** M per cherry-pick
**Unblocks:** open follow-up #7 (NCII 48h takedown) + open follow-up #8 (bulk admin).

### 🟡 NCMEC reporting clients (Ruby `ello/ncmec_reporting`, Go `Boostport/ncmec-go`)

**What:** Reference implementations of the NCMEC CyberTipline submission flow.
**Repos:** https://github.com/ello/ncmec_reporting · https://github.com/Boostport/ncmec-go
**Pull action:** Study the schema mapping (especially the XML envelope for report submission) and port to our Node backend. Both are MIT-licensed.
**Effort:** S-M (~200 LOC client + tests)
**Unblocks:** the LIVE NCMEC submission path (we currently auto-draft but don't submit).

---

## P2 — future iter (heavier integrations)

### 🔴 Bluesky's `osprey-for-atproto` (Bluesky-scale adaptation)

**What:** Bluesky's adaptation of Osprey for AT Protocol scale. Closer to our deployment shape than Discord's billions-of-actions scale.
**Repo:** https://github.com/haileyok/osprey-for-atproto
**Pull action:** Reference architecture when we adopt Osprey (P1 above).

### 🔴 ROOST `gpt-oss-safeguard` (OpenAI open-weight moderation LLM)

**What:** Apache-2.0 licensed open-weight moderation LLM dropped by OpenAI Oct 2025.
**Repo:** (search ROOST org)
**Pull action:** Eval as a provider option for vision-provider failover (open follow-up #10). Cost-vs-Claude-Haiku comparison required first.

### 🔴 Open Media Match (Docker-based ThreatExchange variant)

**What:** Cloud-agnostic Docker deployment for hash matching.
**Repo:** https://github.com/facebook/ThreatExchange/tree/main/open-media-match
**Pull action:** Reference architecture when we move from in-process to dedicated hash-match service (likely R10+).

### ⚪ utilityfueled/content-checker

**What:** Toy implementation that adopts our policy framing.
**Repo:** https://github.com/utilityfueled/content-checker
**Pull action:** Cite only as anti-pattern (lacks the human-loop we built around).

### ⚪ SashiDo/content-moderation-application

**What:** Parse Server-coupled moderation app.
**Repo:** https://github.com/SashiDo/content-moderation-application
**Pull action:** Cite only — good pattern but wrong runtime (Parse vs Express+Prisma).

---

## Anti-patterns flagged (do NOT pull)

- **iHashDNA, open-alleged-photodna, and similar reverse-engineered PhotoDNA libraries** — Microsoft owns PhotoDNA; reverse-engineering it is legally ambiguous. Use Meta's PDQ (Apache-2.0, clean-room) instead.
- **Pure-classifier projects without human loops** — undermines our admin-review-feeds-training architecture. We need both the classifier AND the review pipeline.

---

## Cross-ref to open follow-ups

| Follow-up | Best prior-art | Effort | Status |
|---|---|---|---|
| #3 PhotoDNA hash | Meta PDQ + python-threatexchange | S+M | 🟡 P0 pull-now |
| #6 Training pipeline automation | Cleanlab | S | 🟢 P0 pull-now |
| #7 NCII 48h takedown | Coop NCMEC client | M | 🟡 P1 next-iter |
| #8 Bulk admin tools | Osprey rules engine | L | 🟡 P1 next-iter |
| #10 Vision-provider failover | GantMan NSFW + gpt-oss-safeguard | M | 🟢 P0 pull-now (NSFW) + 🔴 P2 (OSS) |

---

## Daemon integration

The `automations/eve_compliance_train_loop.py` daemon (R8, ships with this catalog) runs the autonomous training loop every 30 minutes. Each cycle:
1. Re-seeds demo data (idempotent)
2. Runs the 5-good-catch → cooldown → bad-catch → export path
3. Captures precision + queue + cooldown + hash-set-size metrics
4. Appends to `_shared-memory/eve-training-loop.jsonl`
5. Writes a fresh heartbeat at `_shared-memory/heartbeats/eve-compliance-train-loop.json`
6. Alerts via inbox if precision <0.85 sustained 3 cycles or backend down 3 cycles

When the head-starts above ship, the daemon's value goes UP — every PDQ-hashed image goes into the known-bad set, every NSFW.js verdict feeds the precision calc, every NCMEC HashList sync expands the short-circuit coverage. Loop never stops, detection corpus only grows.

End.
