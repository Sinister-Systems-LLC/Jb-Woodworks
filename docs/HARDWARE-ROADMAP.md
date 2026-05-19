> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Sinister LLC — Hardware Roadmap ($1000–$2000)

Operator stack today: Win10 workstation, no GPU, single D:\ drive (10K+ files, backups on same disk), 5 concurrent Claude Code sessions, Hetzner VPS for Panel, 2 attested Android phones, Ollama already wired into compose. This roadmap turns that into a real homelab: local LLMs, cross-drive backup, always-on services, and a path off Hetzner for the workloads that don't need to be public.

---

## 1. TL;DR — buy these three first

- **Used RTX 3090 24GB** (~$650–$800 on eBay tier-1). This single purchase unlocks Llama 3 70B Q4, Mixtral 8x7B, Qwen 2.5 32B, DeepSeek-Coder 33B — all local, all offline, zero API spend.
- **2× 8TB external HDD** (~$140 each, ~$280 total). One lives next to the workstation, one rotates to a drawer / off-site. Fixes the #1 risk: backups currently live on the same drive as the originals.
- **Beelink/Minisforum N100 mini-PC, 16GB/512GB** (~$200). Always-on box for Syncthing, Restic scheduler, Uptime Kuma, Gitea, Vaultwarden. Frees the workstation from "must stay on for the cron jobs to run."

Total floor: ~$1,130. Tier 2+3 add networking, NAS, and a UPS up to the $2K ceiling.

---

## 2. Tier 1: must-have (~$800–$1,200)

The GPU + storage core. Do not skip any of these.

| Item | SKU example | Price band | Why | What it unlocks |
|---|---|---|---|---|
| GPU: Used RTX 3090 Founders / EVGA | eBay tier-1 seller, 30-day return | $650–$800 | 24GB VRAM is the magic number. 70B Q4 fits, Mixtral 8x7B fits, you can run two 13B models in parallel for routing/judge setups. New 4060 Ti 16GB is $450 but 16GB caps you at 32B Q4 — false economy. | Llama 3 70B Q4_K_M local inference at ~15 tok/s; Mixtral 8x7B; Qwen 2.5 32B coder; DeepSeek-Coder 33B; whisper-large-v3 real-time; SDXL image gen |
| PSU upgrade (if current PSU <750W) | Corsair RM850x / Seasonic Focus GX-850 | $130–$160 | 3090 pulls 350W under load + spikes. An undersized PSU will reboot you mid-inference and silently corrupt models on disk. | Stable GPU operation; headroom for second card later |
| Backup HDD #1 (primary mirror) | WD Easystore 8TB / Seagate Expansion 8TB | $130–$150 | Cross-drive backup. Currently D:\\_backups\\snapshots dies with D:\\. | Restic repo target #1; immediate fix for single-point-of-failure |
| Backup HDD #2 (rotation / cold) | Same as above, different model on purpose | $130–$150 | Different manufacturer reduces correlated-failure risk. Lives unplugged in a drawer, swapped weekly. | True 3-2-1 backup tier (3 copies, 2 media, 1 off-site) |
| Always-on mini-PC (N100, 16GB, 512GB NVMe) | Beelink EQ12 / Minisforum UN100 / GMKtec G3 | $190–$240 | 6W idle. Runs the 24/7 services so the workstation can sleep, reboot, host LLMs without losing cron. | Syncthing, Restic scheduler, Uptime Kuma, Gitea, Vaultwarden, Pi-hole, Tailscale exit node |

**Tier 1 subtotal: ~$1,230–$1,500**

Trade-off honesty: a new 4060 Ti 16GB ($450) saves ~$300 vs used 3090 but you lose 8GB VRAM permanently. 70B models will not fit. If you plan to run agents-of-agents with multiple models loaded, 24GB is the floor. Used 3090 from a tier-1 eBay seller with returns is the right call.

---

## 3. Tier 2: nice-to-have (~$400–$600)

Networking, off-workstation storage, peripherals.

| Item | SKU example | Price band | Why | What it unlocks |
|---|---|---|---|---|
| 2-bay NAS (used) | Synology DS220+ used / DS224+ refurb | $250–$320 | Off-workstation storage means a workstation reinstall doesn't touch the data. Better SMART monitoring than USB HDDs. | Time Machine target, Syncthing peer, Nextcloud backing store, RAID-1 across 2 disks |
| 2× NAS-grade HDDs for the bay | WD Red Plus 4TB / Seagate IronWolf 4TB | $90–$110 each | CMR (not SMR), 24/7 rated. Skip the bargain Barracuda — SMR will eat you in RAID. | RAID-1 mirrored 4TB usable |
| Managed gigabit switch (8-port) | TP-Link TL-SG108E / Netgear GS308E | $30–$45 | VLAN your phones / IoT / homelab. Costs less than dinner. | Network segmentation, port mirroring for debugging |
| UPS (battery backup) | CyberPower CP1500AVRLCD / APC BR1500MS2 | $160–$200 | Brownouts will kill a running 3090 mid-write. Also keeps NAS + mini-PC up through outages so they shut down cleanly. | Clean shutdowns, ride-through for 10–15 min outages |

**Tier 2 subtotal: ~$530–$675** (pick NAS or UPS first if budget tight; both ideally)

Trade-off: a Synology DS124 (1-bay, $200) is cheaper but you lose RAID-1, which is the whole reason to buy a NAS over another USB drive. Used DS220+ is the sweet spot — Intel CPU runs Docker, Plex, more.

---

## 4. Tier 3: stretch (~$200–$400)

Only if Tier 1+2 came in under budget.

| Item | SKU example | Price band | Why | What it unlocks |
|---|---|---|---|---|
| Raspberry Pi 5 8GB kit | Official kit with PSU + case + active cooler | $110–$130 | Dedicated network-edge device. Separate from the N100 so you can isolate Pi-hole / WireGuard from app services. | DNS sinkhole, WireGuard endpoint, Home Assistant if you go that route |
| 2TB NVMe (internal, for the workstation) | Samsung 990 Pro 2TB / WD SN850X 2TB | $140–$180 | Model files are big: a 70B Q4 is ~40GB, you'll want 5–10 of them on fast storage. | Fast model swap, scratch space for fine-tunes |
| USB Coral TPU or Hailo-8 M.2 | Coral USB Accelerator | $60–$75 | Offload Frigate / face-detect / Whisper-tiny from the GPU. Frees the 3090 for big-model work. | 24/7 inference without touching the 3090 |
| KVM switch (2-port HDMI + USB) | UGREEN 4K KVM / Level1Techs MK-II | $35–$80 | Drive the workstation and mini-PC from one keyboard/monitor. | Saves desk space, sane mini-PC admin |

**Tier 3 subtotal: ~$345–$465**

---

## 5. What each setup unlocks (checklist)

After Tier 1:
- [x] Run Llama 3 70B Q4_K_M locally (~15 tok/s on 3090)
- [x] Run Mixtral 8x7B and Qwen 2.5 32B at usable speed
- [x] Run DeepSeek-Coder 33B as a code-assist model
- [x] Offline Whisper large-v3 transcription faster than real-time
- [x] SDXL / Flux image generation locally
- [x] Redundant backup to a second physical drive (cross-drive)
- [x] Off-site rotation copy (HDD #2 in drawer)
- [x] Always-on Syncthing / Restic / Gitea on N100 — workstation can reboot freely

After Tier 2:
- [x] RAID-1 mirrored storage on NAS (survives single disk failure)
- [x] Self-hosted Nextcloud / Vaultwarden on the NAS or N100
- [x] Network segmentation via VLAN-capable switch
- [x] Clean shutdowns during power loss (UPS)
- [x] SSH from phone (P1/P2) to home network via Tailscale on the N100
- [x] Self-hosted Gitea / Forgejo replacing private GitHub repos

After Tier 3:
- [x] Hardware DNS sinkhole (Pi 5 + Pi-hole) — ad/tracker block across the LLC
- [x] Always-on WireGuard endpoint independent of cloud
- [x] Dedicated small-model inference on Coral (frees the 3090)

---

## 6. NOT buying (with reasons)

- **RTX 4090 / 5090 ($1,800–$2,500+)** — eats the whole budget, leaves nothing for storage/networking/backup. The 3090 is 90% of the LLM capability at 35% of the price. Revisit in 18 months when 5090 used market exists.
- **Mac Studio M2 Ultra 192GB ($4,000+)** — yes it runs huge models, no it doesn't fit a $2K budget and it can't be repurposed.
- **Dual 3090 NVLink rig now** — second 3090 = +$700 + new PSU + airflow rework. Wait until you've actually saturated one 24GB card.
- **Synology DS923+ / DS1522+** — overkill for a 2-bay use case at 2–3× the price.
- **8-bay rackmount NAS / used R720** — wrong stage. Noise, power draw (300W idle), heat. You don't have a rack. Don't start one yet.
- **10GbE networking** — your bottleneck is not LAN throughput, it's GPU VRAM. Skip until you have a NAS + workstation actually moving multi-GB files daily.
- **Brand-new 4060 Ti 16GB** — false economy vs used 3090. 16GB caps you below 70B Q4.
- **External GPU enclosure (eGPU)** — Thunderbolt latency kills inference speed. Put the GPU in the workstation.
- **Cloud GPU (Runpod / Vast.ai)** — useful for spikes, but the whole point is "no API cost." Buying the 3090 pays itself back in ~4 months of moderate Claude API offload.

---

## 7. Software stack that follows from this hardware

Once Tier 1 lands, install in this order on the workstation:

- **Ollama** (already in compose) — primary model runtime. Pull: `llama3.1:70b-instruct-q4_K_M`, `mixtral:8x7b-instruct-q4_K_M`, `qwen2.5-coder:32b`, `deepseek-coder-v2:16b`, `nomic-embed-text`.
- **LM Studio** — GUI for model comparison, easier than Ollama for one-off experiments.
- **vLLM** or **TabbyAPI** — when you need OpenAI-compatible serving with batching for the 5 parallel Claude Code sessions to hit a local model instead of the API.
- **whisper.cpp** (CUDA build) — transcription pipeline for the phones P1/P2 audio captures.
- **ComfyUI** — image gen (SDXL / Flux).
- **text-generation-webui** — fallback / fine-tune UI.

On the N100 mini-PC (24/7):

- **Restic** + **rclone** — encrypted backups from D:\\ to HDD #1, HDD #2, and Hetzner Storage Box.
- **Syncthing** — bidirectional sync between workstation, N100, NAS, and phones (Sanctum public scope only).
- **Gitea** / **Forgejo** — self-hosted git, replaces private GitHub for LLC repos.
- **Vaultwarden** — Bitwarden-compatible password vault.
- **Uptime Kuma** — monitors Hetzner Panel, Ollama endpoint, NAS, Tailscale peers.
- **Tailscale** — mesh VPN so phones (P1/P2) reach home services from anywhere; the N100 is the exit node.
- **Watchtower** — auto-update Docker containers.
- **Caddy** — reverse proxy with auto-TLS for internal services.

On the NAS (Tier 2):

- **Nextcloud** — file sync, calendar, contacts. Replaces Google Drive for LLC scope.
- **Plex** / **Jellyfin** — optional, but you already have the disks.
- **Hyper Backup** (Synology native) — third backup tier into Backblaze B2 (~$6/TB/month).

---

## 8. Migration plan from current setup

**Week 1 — stop the bleeding (~$280)**

1. Order both 8TB external HDDs same day.
2. Set up Restic repo on HDD #1. Initial backup of D:\\Sinister Sanctum, D:\\Sinister\\Sinister Skills, all Claude Code session state.
3. Mirror to HDD #2 manually. Label disks. Put HDD #2 in a drawer.
4. Document the restore procedure in `docs/BACKUP-RUNBOOK.md` and actually test it (restore one folder to a temp dir).

**Week 2 — add the brain (~$650–$800 + PSU if needed)**

1. Order used 3090 from eBay tier-1 seller with 30-day return.
2. Verify PSU wattage before card arrives. Order Corsair RM850x if needed.
3. Install, run `nvidia-smi`, run a 30-min GPU memtest (`gpu-burn`) within return window.
4. Pull Ollama models in order: llama3.1:8b → 70b-q4 → mixtral → qwen2.5-coder:32b. Benchmark tok/s for each, write to `docs/LOCAL-LLM-BENCHMARKS.md`.
5. Point one Claude Code session at a local Ollama endpoint via litellm proxy as a smoke test.

**Week 3 — always-on layer (~$200)**

1. Order N100 mini-PC.
2. Install Debian 12 (Win 11 ships on these; wipe it).
3. Bring up docker, deploy: Restic scheduler, Syncthing, Tailscale, Gitea, Uptime Kuma, Vaultwarden, Caddy.
4. Migrate Restic cron from workstation to N100. Workstation can now reboot without breaking backups.
5. Enroll phones P1/P2 into Tailscale. Verify SSH from cellular works.

**Month 1 — Tier 2 if budget remains (~$500)**

1. NAS (used DS220+) + 2× 4TB Red Plus. Set up SHR / RAID-1.
2. Move Nextcloud + Gitea storage from N100 NVMe to NAS volume.
3. UPS sized to cover NAS + N100 + modem for 15 min. Workstation can ride dirty if needed — its job is GPU, not 24/7.
4. Managed switch + first VLAN: separate IoT/phones from the homelab subnet.

**Month 2 — review and decide Tier 3**

1. Check actual VRAM utilization. If you're loading + unloading models constantly, the 2TB NVMe is worth it.
2. Check Hetzner bill. Anything that can move to the N100 / NAS without losing public availability should.
3. Decide on Pi 5 (if you want Pi-hole isolated from app services) vs running Pi-hole on the N100 (simpler).

---

## Budget reconciliation

| Tier | Low | High |
|---|---|---|
| Tier 1 (GPU + storage core) | $1,230 | $1,500 |
| Tier 2 (NAS + UPS + switch) | $530 | $675 |
| Tier 3 (Pi + NVMe + Coral + KVM) | $345 | $465 |
| **Total range** | **$2,105** | **$2,640** |

Tier 1 alone fits the $1,000–$2,000 budget with room for partial Tier 2 (pick NAS or UPS, not both, on first pass). Full Tier 1 + Tier 2 lands at ~$1,800–$2,000 if you shop used aggressively. Tier 3 is a "next quarter" conversation, not this purchase order.

Recommended initial spend, targeted at $1,950:

- Used 3090: $720
- PSU 850W: $140 (skip if existing PSU >=750W gold)
- 2× 8TB external: $280
- N100 mini-PC 16GB: $210
- Used DS220+: $290
- 2× 4TB Red Plus: $200
- UPS 1500VA: $180
- 8-port managed switch: $40

**Total: ~$2,060.** Drop the switch ($40) and you're at $2,020. Drop the PSU if not needed and you're at $1,880 with budget left for the 2TB NVMe.

That's the play.

---

## 9. Purchase links (search URLs — top-rated current results)

Click these to land on real-time top-rated listings for each item. Prices fluctuate; the URLs survive SKU changes.

### Tier 1 (must-have)
- **Used RTX 3090 24GB** (eBay tier-1): https://www.ebay.com/sch/i.html?_nkw=rtx+3090+24gb&_sop=12&LH_BIN=1&LH_ItemCondition=3000&_dcat=27386
- **WD Easystore 8TB** (Best Buy): https://www.bestbuy.com/site/searchpage.jsp?st=wd+easystore+8tb
- **Seagate Expansion 8TB** (Amazon): https://www.amazon.com/s?k=seagate+expansion+8tb+external
- **Corsair RM850x PSU**: https://www.amazon.com/s?k=corsair+rm850x+850w+80%2B+gold
- **Seasonic Focus GX-850**: https://www.newegg.com/p/pl?d=seasonic+focus+gx-850
- **Beelink N100 mini-PC 16GB**: https://www.amazon.com/s?k=beelink+eq12+n100+16gb+512gb
- **Minisforum N100 mini-PC**: https://www.amazon.com/s?k=minisforum+un100+n100+16gb
- **GMKtec G3 N100**: https://www.amazon.com/s?k=gmktec+g3+n100+16gb

### Tier 2 (nice-to-have)
- **Synology DS220+ used** (eBay): https://www.ebay.com/sch/i.html?_nkw=synology+ds220%2B&_sop=12&LH_BIN=1
- **Synology DS224+** (Amazon): https://www.amazon.com/s?k=synology+ds224%2B
- **WD Red Plus 4TB**: https://www.amazon.com/s?k=wd+red+plus+4tb+nas
- **Seagate IronWolf 4TB**: https://www.amazon.com/s?k=seagate+ironwolf+4tb+nas
- **TP-Link TL-SG108E managed switch**: https://www.amazon.com/s?k=tp-link+tl-sg108e
- **Netgear GS308E**: https://www.amazon.com/s?k=netgear+gs308e+managed+switch
- **CyberPower CP1500AVRLCD UPS**: https://www.amazon.com/s?k=cyberpower+cp1500avrlcd
- **APC BR1500MS2 UPS**: https://www.amazon.com/s?k=apc+br1500ms2

### Tier 3 (stretch)
- **Raspberry Pi 5 8GB kit**: https://www.amazon.com/s?k=raspberry+pi+5+8gb+kit
- **Samsung 990 Pro 2TB NVMe**: https://www.amazon.com/s?k=samsung+990+pro+2tb
- **WD SN850X 2TB NVMe**: https://www.amazon.com/s?k=wd+sn850x+2tb
- **Coral USB Accelerator**: https://coral.ai/products/accelerator
- **UGREEN 4K KVM**: https://www.amazon.com/s?k=ugreen+4k+kvm+2+port
- **Level1Techs MK-II KVM**: https://store.level1techs.com/

### Backblaze B2 (cloud third-tier backup, ~$6/TB/month)
- **B2 Cloud Storage**: https://www.backblaze.com/cloud-storage

### Tailscale (mesh VPN; free for personal)
- **Tailscale**: https://tailscale.com/download

> Tip: bookmark this whole file. Right-click any link → Open in new tab to compare prices side by side.

