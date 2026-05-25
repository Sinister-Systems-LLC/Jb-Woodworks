# GitHub Prior-Art Research: Image Moderation Systems

> Author: RKOJ-ELENO :: 2026-05-25
> From: research sub-agent (sanctum-spawned) -> EVE Compliance lane
> Trigger: operator utterance 2026-05-25T12:44Z: *"i need you to test the site out of image system. seraach github repos we can get ideas from and walsy do resarch in times like this and cross reference and take ides from everyting that works best"*
> Cross-referenced against canonical pipeline at `C:/Users/Zonia/Desktop/LetsText/backend/src/lib/image-moderation.ts`

---

## TL;DR

The Trust & Safety open-source ecosystem matured dramatically in **2025** with the formation of **ROOST (Robust Open Online Safety Tools)**, a non-profit that now hosts the canonical reference implementations: **Osprey** (Discord's rules engine, 400M actions/day in production) and **Coop** (a content review platform with NCMEC reporting baked in). Combined with **Meta's ThreatExchange** (PDQ/vPDQ/HMA for hash matching), these three projects represent the production-grade stack we should be benchmarking against.

Our pipeline already does many of the right things (LLM classifier, strike/cooldown, admin queue, training feedback). The biggest gaps:
- **Rules engine** — we hand-coded strike logic; Osprey replaces it with a high-perf DSL
- **PDQ hashing** — our sha256 placeholder needs to become real perceptual hash from Meta's PDQ Python implementation
- **Active learning loop** — Cleanlab can score which admin-reviewed samples are highest-signal for retraining
- **NCMEC API client** — concrete Ruby/Go clients exist to crib the CyberTipline schema from

---

## 1. facebook/ThreatExchange (Meta)

- **URL:** https://github.com/facebook/ThreatExchange
- **Stars:** 1.3k
- **Category:** Hash matching + CSAM detection + Trust & Safety platform

**Architecture (2 sentences):** Meta's open-source bundle of perceptual-hash algorithms (PDQ for images, TMK+PDQF and vPDQ for video) plus the "Hasher-Matcher-Actioner" (HMA) reference deployment for AWS, and a newer cloud-agnostic Docker variant called Open Media Match. The `python-threatexchange` PyPI package gives you a CLI + library for scanning content against hash lists shared via Meta's ThreatExchange API (including NCMEC and StopNCII feeds).

**What it does BETTER than our current pipeline:**
- **Real perceptual hashing (PDQ)** — produces 256-bit signatures that survive resize/recompress/crop. Our `sha256(bytes)` "perceptual hash" placeholder will miss any re-encoded duplicate. PDQ is the canonical open-source replacement.
- **Hash exchange protocol** — built-in support for syncing with NCMEC HashList + StopNCII feeds, so we get pre-known-CSAM blocking before our classifier ever runs.
- **Video hashing (vPDQ/TMK)** — when we add video uploads, this gives us frame-level matching.
- **HMA reference architecture** — battle-tested AWS deployment showing how to fan out hash matching across S3 events.

**Study these paths:**
- `https://github.com/facebook/ThreatExchange/tree/main/pdq/python` — drop-in Python PDQ implementation; replace our `imageHash` field generator with this.
- `https://github.com/facebook/ThreatExchange/tree/main/python-threatexchange` — CLI + library scaffolding for hash-list sync.
- `https://github.com/facebook/ThreatExchange/tree/main/open-media-match` — Docker-based deployment we can model R7+ infra on.

---

## 2. roostorg/osprey (Discord, donated to ROOST)

- **URL:** https://github.com/roostorg/osprey
- **Stars:** 433 (rapidly growing; donated July 2025)
- **Category:** High-performance rules engine for trust & safety enforcement

**Architecture (2 sentences):** A real-time event-stream decisions engine using a Structured Rule Logic (SML) DSL extendable with user-defined functions; in production at Discord it evaluates 2.3M rules/sec across 400M daily actions. Rules consume events (e.g. image-upload, message-send), produce verdicts (allow/block/quarantine/escalate) and custom effects sent to configurable output sinks (which is where strike-increment, cooldown-apply, queue-enqueue all happen).

**What it does BETTER than our current pipeline:**
- **Rules-as-data instead of rules-as-code** — our 5-strikes-then-24h-cooldown is hard-coded TypeScript. Osprey lets operator/admin tune those thresholds via SML rules without deploying. Crucial for the per-agency policy variance the operator wants ("which categories an agency wants stricter/looser").
- **Composable verdicts** — a single event can fire multiple rules (e.g. "csam_classifier_hit" + "uploader_under_24h_old_account" + "agency_strict_mode") and have effects accumulate. Our pipeline does one verdict per scan.
- **Used by Bluesky, Discord, Matrix in production** — battle-tested at scale; we're not picking a toy.
- **Event replay** — Osprey logs every decision so you can re-run new rules against historical events to estimate impact before shipping. Solves our "did the rules change hurt precision?" question.

**Study these paths:**
- `https://github.com/roostorg/osprey/tree/main/example_rules` — sample SML rules; pattern-match against our `image-moderation.ts` strike logic.
- `https://github.com/haileyok/osprey-for-atproto` — Bluesky's adaptation; closer to our scale than Discord's.

---

## 3. roostorg/coop (formerly Cove, donated to ROOST)

- **URL:** https://github.com/roostorg/coop
- **Stars:** 47 (but funded + maintained by ROOST + ex-Cove team)
- **Category:** End-to-end content review platform with NCMEC built-in

**Architecture (2 sentences):** TypeScript (95%) + Postgres review platform providing a Review Console UI, queues with routing, a rules engine for auto-enforcement, analytics dashboards, and a built-in NCMEC CyberTipline integration for mandatory CSAM reporting. Designed as the human-in-the-loop layer that sits *on top of* a classifier — meaning it's the closest existing project to what we built (admin queue + good_catch/bad_catch + training feedback).

**What it does BETTER than our current pipeline:**
- **NCMEC reporting integration shipped** — we have `NcmecReport` as schema-only. Coop has the full CyberTipline API flow.
- **Queue routing** — assign cases to specific reviewers/teams (e.g. "all CSAM_CLASSIFIER hits route to senior reviewer team"). Our queue is a flat list.
- **Analytics dashboard primitives** — counts, false-positive rate, top categories. Directly maps to our open follow-up #4 (per-agency moderation analytics).
- **Bulk actions UX** — directly maps to our open follow-up #8.

**Study these paths:**
- Repo is mostly TypeScript so we can cross-reference idioms directly. Look at the `/apps/console/` directory for review-queue UI patterns and the rules engine wiring.

---

## 4. roostorg/awesome-safety-tools

- **URL:** https://github.com/roostorg/awesome-safety-tools
- **Stars:** ~600+ (ROOST curated)
- **Category:** Meta-directory of the entire open-source safety stack

**Architecture (2 sentences):** Curated list maintained by ROOST that maps every open-source safety tool: hash matching, classifiers, investigation workflows, rules engines, AI guardrails, NCMEC clients, blocklist tooling. The single source-of-truth index — every project below appears here, plus dozens we didn't have time to evaluate.

**What it does BETTER than our current pipeline:** Not a pipeline competitor — it's a discovery surface. Use it whenever a new follow-up lands (e.g. "video moderation" -> awesome-safety-tools "Video" section).

**Study path:** Bookmark the README.md as our "where do I find prior art" entry point for every future open follow-up.

---

## 5. GantMan/nsfw_model

- **URL:** https://github.com/GantMan/nsfw_model
- **Stars:** 2.1k
- **Category:** Open-source NSFW image classifier (Keras / MobileNet v2 + Inception V3)

**Architecture (2 sentences):** Pre-trained Keras model trained on 60+ GB of data, returns 5-class softmax (Drawings/Hentai/Neutral/Porn/Sexy) with 93% accuracy. Inference cost: zero per call after model load (no API fee); deploy as TF-Lite/TFJS/SavedModel.

**What it does BETTER than our current pipeline:**
- **Zero-cost classifier for the easy 95%** — Claude Haiku 4.5 costs $/call. Run NSFW.js FIRST as a cheap pre-filter; only escalate to Haiku when nsfw_model returns ambiguous (e.g. 0.3 < porn_prob < 0.7) OR when the policy requires nuance (CSAM/gore/non-consent flags Haiku catches but nsfw_model doesn't).
- **Latency** — nsfw_model is <50ms local inference vs Haiku's ~800ms-2s network round-trip. For an adult platform with high upload volume, this matters at p99.
- **Provider failover** — directly maps to our open follow-up #10. nsfw_model becomes the fallback when Haiku/Hive/Sightengine are all rate-limited.

**Cross-ref with our pipeline:**
- Our policy *allows* adult nudity. nsfw_model's `porn` category alone is too coarse — we don't want to flag all `porn=high`, we want to flag `porn + (gore|csam|non-consent)`. So nsfw_model is a PRE-FILTER + FALLBACK, not a replacement for Haiku.
- The 5-category output gives our analytics a useful axis our current binary scan doesn't have ("agency X uploads skew Hentai/Drawings; agency Y skews Sexy/Porn").

**Study path:** `https://github.com/GantMan/nsfw_model/blob/master/README.md` — has the model URLs + TF.js wrapper example.

---

## 6. cleanlab/cleanlab

- **URL:** https://github.com/cleanlab/cleanlab
- **Stars:** 11.5k
- **Category:** Confident learning + active learning + label-error detection

**Architecture (2 sentences):** Python library implementing confident-learning algorithms (Northcutt et al, with formal guarantees) for finding mislabeled examples in any dataset, with model-agnostic API supporting any classifier (PyTorch/TF/OpenAI/sklearn). Includes active-learning helpers that score which unlabeled examples would most improve the model if labeled next — exactly the "which scans should the admin review next" question we need to answer.

**What it does BETTER than our current pipeline:**
- **Training feedback loop with theory backing** — our current flow is: admin clicks good_catch/bad_catch -> JSONL append -> manual Ruflo retrain. Cleanlab gives us:
  1. **Auto-detect label errors** in the JSONL (catches admin clicks that contradict the eventual ground truth)
  2. **Active learning prioritization** — `cleanlab.experimental.label_issues` ranks which unreviewed scans are highest-value for human review (drives our review queue ordering!)
  3. **Multi-annotator consensus** — when we have multiple compliance reviewers, cleanlab computes inter-annotator agreement and identifies which examples need a tiebreaker
- **Directly applicable to open follow-up #6** (training pipeline automation) — wrap cleanlab around our existing JSONL export to make the retrain loop smarter.

**Study path:**
- `https://github.com/cleanlab/examples/blob/master/active_learning_multiannotator/active_learning.ipynb` — exact pattern we'd port for the admin-review-queue prioritization.

---

## 7. HumanSignal/label-studio

- **URL:** https://github.com/HumanSignal/label-studio
- **Stars:** 27.4k
- **Category:** Multi-type data labeling + review queue UX reference

**Architecture (2 sentences):** Python backend + React frontend + Postgres for production, supports images/text/audio/video annotation with multi-user workflows. Includes accept/fix-and-accept/reject review workflow, REST API for programmatic task ingestion, and ML backend integration for active learning (model pre-labels -> human reviews the uncertain ones).

**What it does BETTER than our current pipeline:**
- **Review queue UX is the gold standard** — accept / fix-and-accept / reject is more expressive than our good_catch / bad_catch / dismiss. "fix-and-accept" maps to "admin agrees the verdict was right but the category was wrong" (e.g. flagged as `gore` should have been `weapon`), which our pipeline currently loses.
- **Task assignment + multi-reviewer workflow** — assign cases to specific reviewers; track who reviewed what; lock examples to prevent double-review. Useful when our compliance team grows past 1 person.
- **Model integration spec** — Label Studio has a documented protocol for plugging a classifier in such that it pre-labels new examples + the human-correction events get streamed back to retrain. We can copy this protocol verbatim for our Ruflo retrain pipeline.

**Study path:** `https://github.com/HumanSignal/label-studio/tree/develop/label_studio/data_manager` — the queue/data-manager logic.

---

## 8. ello/ncmec_reporting (Ruby) + Boostport/ncmec-go (Go)

- **URLs:**
  - Ruby: https://github.com/ello/ncmec_reporting
  - Go: https://github.com/Boostport/ncmec-go
- **Stars:** ~30 each (low star but solve a SPECIFIC problem well)
- **Category:** NCMEC CyberTipline API client libraries

**Architecture (2 sentences):** Thin client libraries that wrap the NCMEC CyberTipline reporting API (the legally mandated reporting endpoint for ESPs under 18 U.S. Code § 2258A). Handles authentication, multi-step report submission (file upload, metadata, suspect info), and report status polling.

**What it does BETTER than our current pipeline:**
- **Complete request schema reference** — we have `NcmecReport` as a Prisma model with placeholder fields. These libraries document every field NCMEC actually requires (incident type codes, mandatory metadata, retention rules). Crib the schema verbatim.
- **Quarantine flow before submission** — both libraries enforce that reports are quarantined until a human auditor confirms, matching our `isQuarantined` workflow.

**Study path:** `https://github.com/ello/ncmec_reporting/blob/main/README.md` + the Go SDK's `/types/` directory for the canonical field set.

---

## 9. utilityfueled/content-checker

- **URL:** https://github.com/utilityfueled/content-checker
- **Stars:** 42
- **Category:** Multi-provider moderation library (text + image)

**Architecture (2 sentences):** TypeScript library wrapping Google Perspective + OpenAI Moderation + Google Natural Language as interchangeable providers behind a single `isProfaneAI()` interface. Designed for "swap providers without changing caller code."

**What it does BETTER than our current pipeline:**
- **Provider abstraction pattern** — directly maps to our open follow-up #10 (provider failover). Our current code calls Claude Haiku directly; refactoring to a `scanImage({ provider: 'haiku' | 'hive' | 'sightengine' | 'nsfw_model' })` API is the clean path. content-checker shows the TypeScript pattern.
- **Type-tagged violation categories** — returns `{ profane: boolean, type: string[] }` where the type array is provider-normalized. We should normalize Haiku's free-form `category` field into a fixed enum the same way.

**Study path:** `https://github.com/utilityfueled/content-checker/tree/main/src` — the `Filter` class is the provider-router pattern.

---

## 10. SashiDo/content-moderation-application

- **URL:** https://github.com/SashiDo/content-moderation-application
- **Stars:** 30 (low star but full-stack reference for "classifier + auto-engine + admin panel")
- **Category:** End-to-end NSFW moderation reference architecture

**Architecture (2 sentences):** Three-tier reference implementation: REST classifier API (NSFW.js / TF.js) + automation engine (afterSave hook auto-deletes/marks-for-review based on thresholds) + ReactJS admin panel. Built on Parse Server but the architectural pattern is portable.

**What it does BETTER than our current pipeline:**
- **Threshold-driven automation** — instead of binary "block or allow," the automation engine has `safeThreshold` / `deleteThreshold` / `moderationRequiredThreshold`. Anything in between is auto-queued. Our current pipeline only enqueues on hits; we should also enqueue on low-confidence verdicts (Haiku says "maybe gore @ 55%" -> human review).
- **`moderationRequired` boolean as first-class queue entry** — clean separation between "scanned" and "needs review."

**Study path:** Skim the `parse-server-modules/` cloudCode hooks for the threshold logic. Don't adopt the stack — adopt the threshold-tiering pattern.

---

## BONUS: gpt-oss-safeguard (OpenAI, October 2025)

- **URL:** https://huggingface.co/openai/gpt-oss-safeguard-120b (also mirrored on github)
- **Category:** Open-weight "bring your own policy" safety classifier

**Architecture (2 sentences):** OpenAI released a 120B + 20B open-weight reasoning model family under Apache 2.0 specifically tuned for content moderation against an arbitrary policy you provide as a system prompt. You write your policy verbatim, gpt-oss-safeguard reasons about whether content violates it, returns structured verdict + reasoning chain.

**Why it matters for us:**
- **Self-hostable LLM moderator** — eliminates per-call Anthropic spend AND eliminates the "what if Anthropic changes AUP" lock-in risk (huge for an adult platform).
- **Policy-as-prompt** — directly compatible with our existing prompt-engineering style. Drop the Haiku prompt in; reasoning chain comes back as a bonus.
- **Apache 2.0 commercial-use OK** — no licensing friction.

This deserves its own R7+ exploration. Self-host on a 4xH100 box and we cap classifier cost at hardware + electricity.

---

# Top 3 Recommendations to Adopt

Ranked by ROI (impact / effort), referencing the lane's open-follow-up numbering.

## #1 — Replace sha256 placeholder with Meta's PDQ (open follow-up #3) — Effort: **S**

**What:** Drop `python-threatexchange`'s PDQ implementation into a tiny Python sidecar service (or compile the C++ PDQ to a Node addon). Replace the `imageHash` generator in `image-moderation.ts` with a real PDQ call. Update `ContentScan.imageHash` to store 256-bit PDQ signatures + add `pdqDistance(a, b)` for hash-match queries.

**Why now:**
- We just shipped R6 hash-match short-circuit — but sha256 only catches BYTE-IDENTICAL duplicates. A re-uploaded JPEG with one pixel changed bypasses us today. PDQ catches it.
- Required for any future NCMEC HashList sync (which is PDQ-format).
- Unblocks open follow-up #3 from "blocked on pHash library choice" to "shipped."

**Concrete steps:**
1. `pip install threatexchange[pdq]` in a new `backend/services/pdq-hasher/` Python service (FastAPI).
2. Expose `POST /hash {image_bytes}` returning `{ pdq_hash_hex, pdq_quality }`.
3. Update `image-moderation.ts` to call the sidecar (or in-process if we add `node-ffi`).
4. Backfill existing `ContentScan.imageHash` rows over a weekend (background job, low priority).
5. Add `pdqHammingDistance` SQL function for hash-similarity lookups (Postgres pgvector or a simple BIT_COUNT extension works).

## #2 — Adopt Osprey-style rules engine for strike/cooldown logic (open follow-up #8 + future per-agency tuning) — Effort: **M**

**What:** Extract our hard-coded 5-strikes-24h-cooldown logic out of `image-moderation.ts` into a small in-process rules DSL (or, more ambitiously, embed Osprey's SML evaluator). Each agency gets its own ruleset stored in `AgencyModerationPolicy` table.

**Why now:**
- Operator's CLAUDE.md verbatim mentions "which categories an agency wants stricter/looser." Hard-coded logic can't do this; rules-as-data can.
- Bulk-action admin tools (follow-up #8) become trivial once enforcement is a rules engine — "reset all strikes for agency X" becomes "evaluate rule: `reset_all_strikes WHERE agency_id = X`."
- Pre-shipping investment in the rules engine pays off for every future enforcement feature.

**Concrete steps:**
1. Start with a JSON-rule DSL (don't embed Osprey day-one — too much surface area). Schema: `{ when: { scan_verdict, agency_id, uploader_strike_count }, then: { action, params } }`.
2. Move the 5-strikes-then-24h logic into 3 default rules per agency.
3. Add admin UI for editing rules per agency (CRUD on `AgencyModerationPolicy`).
4. Phase 2 (R8+): swap our JSON DSL for Osprey if scale demands it. Stay API-compatible.

**Decision log entry:** capture "we evaluated Osprey, it's overkill at our event volume; adopt the pattern, not the runtime."

## #3 — Cleanlab-driven review queue prioritization (open follow-up #6 + queue UX upgrade) — Effort: **S**

**What:** Wrap `cleanlab` around our `training-feedback.jsonl` to:
1. Detect when admin clicks contradict themselves (label noise) — surface for re-review.
2. Score unreviewed `ContentScan` rows by "expected information gain if labeled" — sort the review queue by this score instead of chronologically.
3. Auto-promote high-value examples to the front of the queue.

**Why now:**
- Cleanlab is ~50 lines of Python to integrate. Tiny investment, immediate quality bump.
- Solves the "reviewer fatigue on obvious cases" problem (current queue is FIFO — reviewer sees boring obvious-violations first; cleanlab puts ambiguous-cases-that-teach-the-model-the-most first).
- Directly enables open follow-up #6 (training pipeline automation) — once cleanlab scores examples, the export-to-Ruflo step becomes "export only top-N by cleanlab score" instead of "export everything."

**Concrete steps:**
1. New `backend/scripts/score-review-queue.ts` (calls a Python `cleanlab-scorer.py` sidecar).
2. Add `ContentScan.reviewPriorityScore` Float column. Run nightly cron to refresh.
3. Update admin queue API to `ORDER BY reviewPriorityScore DESC, createdAt DESC`.
4. Add "show me only top-50 highest-value" filter to the admin queue UI.

---

# Cross-reference matrix (which project answers which of our open follow-ups)

| Our follow-up | Best prior-art | Adopt? |
|---|---|---|
| #1 NCMEC auto-draft on CSAM | ello/ncmec_reporting + Boostport/ncmec-go (schema reference) + Coop (full flow) | YES — crib NCMEC field set from Boostport, study Coop's quarantine-before-submit flow |
| #2 ChatArea cooldown UX | Discord/Vortex bot UX patterns | LOW — front-end work; just show the `cooldownUntil` from our existing 403 response |
| #3 PhotoDNA hash integration | facebook/ThreatExchange/pdq | YES — recommendation #1 above |
| #4 Per-agency analytics | Coop dashboard primitives | YES — model our dashboard on Coop's analytics queries |
| #5 EVE Compliance dashboard widget | SashiDo content-moderation-application admin panel | LOW priority — just UI surfacing of existing metrics |
| #6 Training pipeline automation | cleanlab + Label Studio's ML-backend protocol | YES — recommendation #3 above |
| #7 NCII 48h takedown workflow | StopNCII.org integration (via ThreatExchange) | YES — fold into PDQ sidecar work |
| #8 Bulk-action admin tools | Osprey rules engine + Coop bulk-actions | YES — recommendation #2 above |
| #9 Per-employee strike trend graph | Label Studio analytics views | LOW — straightforward UI work |
| #10 Vision-provider failover | content-checker provider-router + nsfw_model as zero-cost fallback | YES — refactor `scanImage` to provider-router pattern |

---

# Anti-patterns observed (DON'T adopt these)

- **SashiDo's tight coupling to Parse Server** — pattern is good, runtime is wrong for us.
- **Pure-classifier projects that skip the human-loop** (most of the topic page hits) — without the admin review queue feeding back to training, accuracy decays. We already have the loop; don't get tempted by "just plug in a bigger model."
- **Vortex's punishment-ladder hard-coding** — same as our current code; what we want to MOVE AWAY from.
- **iHashDNA / open-alleged-photodna** — leaked/reverse-engineered code with legal ambiguity. Stick with PDQ (Meta-blessed open-source) for hashing.

---

# Sources

- [facebook/ThreatExchange](https://github.com/facebook/ThreatExchange)
- [roostorg/osprey](https://github.com/roostorg/osprey)
- [roostorg/coop](https://github.com/roostorg/coop)
- [roostorg/awesome-safety-tools](https://github.com/roostorg/awesome-safety-tools)
- [GantMan/nsfw_model](https://github.com/GantMan/nsfw_model)
- [cleanlab/cleanlab](https://github.com/cleanlab/cleanlab)
- [HumanSignal/label-studio](https://github.com/HumanSignal/label-studio)
- [ello/ncmec_reporting](https://github.com/ello/ncmec_reporting)
- [Boostport/ncmec-go](https://github.com/Boostport/ncmec-go)
- [utilityfueled/content-checker](https://github.com/utilityfueled/content-checker)
- [SashiDo/content-moderation-application](https://github.com/SashiDo/content-moderation-application)
- [openai/gpt-oss-safeguard announcement (ROOST)](https://roost.tools/blog/a-new-milestone-for-open-source-safety-infrastructure-and-transparency/)
- [ROOST org overview](https://roost.tools/)
- [Discord Osprey blog post](https://discord.com/blog/osprey-open-sourcing-our-rule-engine)
