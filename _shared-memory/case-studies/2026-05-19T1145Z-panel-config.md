---
target: panel-config
kind: case-study
reviewed_by: Sinister Sanctum master agent (via Explore subagent)
reviewed_at: 2026-05-19T11:45Z
tags: [case-study, panel-config, KEEP-WITH-CHANGES]
---

# Case study: panel-config

## 1. What it is

The `panel-config` tool lives at `D:\Sinister Sanctum\tools\panel-config\` and provides a single source of truth for how Sanctum surfaces discover the Sinister Panel. It consists of a JSON configuration file (`panel-config.json`) specifying `primary` (loopback) and `fallback` (prod) URLs, per-source timeouts, and endpoint paths. Two readers consume it: the launcher (`start-sinister-session.ps1` via `Get-PanelConfig` + `Get-PanelStat` functions) and the window-manager console (`server.py` via `_load_panel_config()` called by `/api/trophy`). Both readers tag HTTP responses with a source label (`local` / `prod` / `offline`) so the operator can see which panel instance filled the data.

## 2. Strengths

- **Single knob for routing:** Operator can flip `primary` / `fallback` in one JSON file without touching PowerShell or Python code (automations/start-sinister-session.ps1:168-188, automations/window-manager/server.py:1110-1130).
- **Hardcoded safety net in both readers:** If JSON parse fails or file is missing, both consumers fall back to sensible defaults (launcher line 179-186, window-manager line 1116-1121), ensuring panel data still surfaces even if the disk file corrupts.
- **Per-source timeout tuning:** Primary gets 1500ms (tight, local), fallback gets 4000ms (generous, for slow prod). This prevents slow prod from blocking local trials (panel-config.json:5-6).
- **Live editing support:** Window-manager re-reads the JSON on every request (no module-level cache), so operator edits land without server restart (server.py:1139).
- **Source tagging implemented in both surfaces:** Trophy-case header shows `live from local panel (local)` or `live from snap.sinijkr.com (prod)`, and `/api/trophy` response includes `"source": "local" | "prod" | "offline"` (README.md:48-52).

## 3. Weaknesses + risks

- **Launcher caches config at module load:** `Get-PanelConfig` at line 169 caches the JSON in `$script:PanelConfig`, meaning operator edits require restarting `start-sinister-session.ps1` before they take effect. Window-manager refreshes on every request; launcher does not. This asymmetry is a UX surprise (launcher line 169, vs. window-manager line 1139).
- **Endpoint path map defined but unused in launcher:** `panel-config.json` includes an `endpoints` key mapping `stats`, `signer`, `devices`, `actions`, `health` to paths, but `Get-PanelStat` hardcodes endpoint strings like `/api/dashboard/stats` instead of reading from the map (launcher line 795-798 vs. `panel-config.json:7-13`). Changing an endpoint name requires editing both the JSON and the PowerShell hardcodes.
- **No validation of required fields:** JSON parse succeeds even if `primary` or `fallback` is missing; `Get-PanelStat` handles `$null` primary/fallback strings but does not emit a warning (launcher line 198-211). Operator could accidentally create a config with both empty and see only "offline" without a diagnostic message.
- **Error suppression without logging:** Both `Get-PanelStat` and `_load_panel_config` catch all exceptions silently (launcher line 203, 210; window-manager line 1128). If a URL is unreachable or JSON has a structural flaw, the operator sees "offline" but never learns why. No audit trail for troubleshooting.
- **Timeout conversion in launcher is lossy:** `Get-PanelStat` converts milliseconds to seconds by ceiling and clamping to 1-second minimum (launcher line 196-197), so 500ms config becomes 1 second and 1500ms becomes 2 seconds. The window-manager uses milliseconds directly without conversion, creating a subtle timing mismatch (launcher vs. window-manager/server.py).

## 4. Better-than-found proposal

Remove the launcher's module-level cache so operator edits take effect immediately (matching window-manager behavior). Use config-driven endpoint names instead of hardcoding them in call sites. Add optional debug logging when both sources fail.

**Changes to `automations/start-sinister-session.ps1` lines 168-213:**

1. Remove `if ($null -ne $script:PanelConfig) { return ... }` at line 169 so JSON is re-read on each call.
2. Populate the `endpoints` map in the fallback config (line 182-186) and use it in `Get-PanelStat`.
3. Change call sites from `Get-PanelStat '/api/dashboard/stats'` to `Get-PanelStat 'stats'` (lines 795-798).
4. In the catch block at line 210, emit a debug-level message: `Write-Debug "Panel offline after trying primary and fallback for $endpointKey"`.

**Rationale:** The endpoint map is already defined in `panel-config.json` but unused; consuming it from the launcher closes the gap. Removing the module cache aligns launcher and window-manager behavior (both now respond to JSON edits immediately). One debug log on dual failure aids troubleshooting without spamming the user.

## 5. Recommendation

**KEEP-WITH-CHANGES**

The tool solves a real problem (two consumers hardcoding different URLs + timeouts) with a pragmatic working design. The JSON is clean, the fallback chain is correct, and both readers tag responses with source labels. However, the launcher's module-level cache creates an asymmetry: operator edits land immediately in window-manager but require a relaunch in the launcher. The endpoint path map is defined in JSON but unused in the launcher, forcing hardcoded duplicates at call sites. These are not breaking issues but they violate the tool's own principle (one knob, no hardcoding). A minor refactor to remove the cache and consume endpoint names from config would make the tool complete. With those changes, ship without further review.

## Operator decision
*(left blank for operator's thumb + free text)*
