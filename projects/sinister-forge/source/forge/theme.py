# Sinister Forge :: theme.py (v4 — global Sinister Panel chrome)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Operator directive 2026-05-21 (verbatim): "i need my ui like the rkoj, but
# look of my sinister panel."
#
# Canonicalises the Sinister Panel purple-glass chrome across EVERY Forge
# widget. Exports:
#   - Color constants (purple gradient + glyph/text variants)
#   - Reusable CSS snippets (PANEL_CSS, BUTTON_CSS, TAB_CSS, INPUT_CSS, ...)
#   - One giant THEME_CSS string mounted by ForgeApp.CSS so every Screen +
#     widget inherits the chrome without per-widget DEFAULT_CSS bloat.
#
# v3 → v4 changes:
#   - Operator-canonical names added: PURPLE_DEEP/PURPLE_DARK/PURPLE_ACCENT/
#     PURPLE_BORDER/GREEN_ACCENT/GRAY (alongside the legacy SINISTER_CSS names)
#   - SINISTER_CSS re-exported as THEME_CSS (back-compat — both work)
#   - Added .sinister-panel / .sinister-tab / .sinister-button / .sinister-card
#     utility classes any widget can opt into
#   - All borders are `round` (Sinister Panel rounded chrome)
#   - Toolbar/Statusbar/AdbPanel/MemoryPanel inherit instead of duplicating

# ============================================================
#  Sinister-canonical hex colors  (synced with Claw/Mind/Term)
# ============================================================
# Legacy v3 names (do not rename — used across forge/* and term/*)
BG_DEEP        = "#07070B"   # void
BG             = "#0E0A14"   # primary surface
BG_GLASS_1     = "#15131A"   # tinted layer 1
BG_GLASS_2     = "#1C1626"   # tinted layer 2
BG_GLASS_3     = "#231A33"   # tinted layer 3 (hover)
BG_GLOW        = "#2A1F3D"   # active wash

# NOTE the v4 PURPLE_DEEP name from the operator directive (#0E0A14) collides
# with the v3 PURPLE_DEEP (#7A3DD4 — a saturated mid-purple used for headers).
# To stay back-compat we keep the v3 name on the saturated purple and expose
# the bg-purple under PURPLE_VOID (= operator's "PURPLE_DEEP").
PURPLE_VOID    = "#0E0A14"   # v4: operator "PURPLE_DEEP" (bg)
PURPLE_DARK    = "#15131A"   # v4: tinted-layer-1 chip bg
PURPLE_DEEP    = "#7A3DD4"   # v3: saturated mid-purple (header fills)
PURPLE_BRIGHT  = "#A06EFF"   # operator standing-order accent
PURPLE_ACCENT  = "#A06EFF"   # v4 alias of PURPLE_BRIGHT (operator directive)
PURPLE_BORDER  = "#3A2A55"   # v4: rounded-panel borders
PURPLE_HALO    = "#C39DFF"
LIGHT_PURPLE   = "#E8D6FF"

CYAN           = "#6EE8FF"
GREEN          = "#6EFFA0"
GREEN_ACCENT   = "#85C86E"   # v4: status-bar live counter
YELLOW         = "#FFD66E"
RED            = "#FF6E6E"
MAGENTA        = "#FF6EE8"
ORANGE         = "#FF8C42"

WHITE          = "#DCDCEA"   # v4 operator-directive name (slightly cooler)
WHITE_PURE     = "#F5F5FA"   # legacy v3 brighter white (preserved)
DIM            = "#6E6E84"
SOFT           = "#999AB0"
GRAY           = "#999AB0"   # v4 alias of SOFT

BORDER_GLASS   = "#3A2A55"   # subtle purple-tinted border (= PURPLE_BORDER)
BORDER_ACTIVE  = "#A06EFF"   # active pane border

# Per-agent accent palette (each spawned agent can pick one)
AGENT_ACCENTS = {
    "purple":  PURPLE_BRIGHT,
    "magenta": MAGENTA,
    "cyan":    CYAN,
    "green":   GREEN,
    "yellow":  YELLOW,
    "red":     RED,
    "orange":  ORANGE,
    "white":   WHITE,
}

# Per-project border palette for the All-tab group outlines
PROJECT_BORDER_PALETTE = {
    "sanctum":             PURPLE_BRIGHT,
    "sinister-panel":      CYAN,
    "kernel-apk":          GREEN,
    "sinister-emulator":   YELLOW,
    "rkoj-workstation":    MAGENTA,
    "snap-emulator-api":   ORANGE,
    "tiktok-emulator-api": RED,
    "bumble-emulator-api": LIGHT_PURPLE,
    "sinister-forge":      "#42E8FF",
    "sinister-mind":       "#B042FF",
    "sinister-term":       "#42FFB0",
    "sinister-claw":       "#FF42B0",
    "_default":            PURPLE_BRIGHT,
}


# Heavy Sinister Liquid-Glass Textual CSS
SINISTER_CSS = f"""
Screen {{
    background: {BG_DEEP};
    color: {LIGHT_PURPLE};
    layers: base overlay palette;
}}

/* ============== Top chrome bar (replaces white Header) ============== */
#chrome-bar {{
    height: 1;
    background: {BG_GLOW};
    color: {PURPLE_HALO};
    text-style: bold;
    padding: 0 2;
    layer: base;
}}

/* ============== Project chip strip ============== */
#project-chip {{
    height: 1;
    background: {BG_GLASS_1};
    color: {CYAN};
    padding: 0 2;
}}

/* ============== Status footer ============== */
#status-footer {{
    height: 1;
    background: {BG_GLASS_1};
    color: {SOFT};
    padding: 0 2;
}}
Footer {{
    background: {BG_GLASS_2};
    color: {LIGHT_PURPLE};
    text-style: bold;
}}
Footer > .footer--highlight {{
    background: {PURPLE_DEEP};
    color: {WHITE};
}}
Footer > .footer--highlight-key {{
    color: {PURPLE_HALO};
    text-style: bold;
}}
Footer > .footer--key {{
    color: {PURPLE_HALO};
    text-style: bold;
}}

/* ============== TabbedContent (Tabs bar) ============== */
TabbedContent {{
    height: 1fr;
}}
Tabs {{
    background: {BG_GLASS_1};
    color: {DIM};
}}
Tab {{
    padding: 0 2;
    color: {SOFT};
    background: {BG_GLASS_1};
}}
Tab.-active {{
    color: {PURPLE_HALO};
    background: {BG_GLOW};
    text-style: bold;
}}
TabPane {{
    background: {BG_DEEP};
    padding: 0;
}}
Underline > .underline--bar {{
    color: {PURPLE_BRIGHT};
}}

/* ============== Agent Pane (the main work surface) ============== */
.agent-pane {{
    border: round {BORDER_GLASS};
    background: {BG};
    padding: 0 1;
    margin: 0 1;
    height: 1fr;
}}
.agent-pane:focus-within {{
    border: round {BORDER_ACTIVE};
    background: {BG_GLASS_1};
}}
.agent-header {{
    background: {PURPLE_DEEP};
    color: {WHITE};
    text-style: bold;
    padding: 0 2;
    height: 1;
    text-align: left;
}}
.agent-header.-active {{
    background: {PURPLE_BRIGHT};
    color: {BG_DEEP};
}}
.agent-subheader {{
    background: {BG_GLASS_2};
    color: {LIGHT_PURPLE};
    padding: 0 2;
    height: 1;
}}
RichLog {{
    background: {BG};
    color: {LIGHT_PURPLE};
    scrollbar-background: {BG_GLASS_1};
    scrollbar-color: {PURPLE_DEEP};
    scrollbar-color-hover: {PURPLE_BRIGHT};
    scrollbar-color-active: {PURPLE_HALO};
}}

/* ============== Project group (All-tab clusters) ============== */
.project-group {{
    border: round {BORDER_GLASS};
    background: {BG_DEEP};
    margin: 0 1;
    padding: 0 1;
    height: 1fr;
}}

/* ============== Boot screen ============== */
.boot-logo {{
    color: {PURPLE_BRIGHT};
    background: {BG_DEEP};
    text-align: center;
    height: 1fr;
    width: 1fr;
    content-align: center middle;
    text-style: bold;
}}
.boot-tagline {{
    color: {PURPLE_HALO};
    text-align: center;
    text-style: italic;
}}

/* ============== Memory side panel ============== */
#memory-panel {{
    width: 36;
    border: round {BORDER_GLASS};
    background: {BG_GLASS_1};
    padding: 1 2;
    layer: overlay;
}}
#memory-panel.-active {{
    border: round {PURPLE_BRIGHT};
    background: {BG_GLASS_2};
}}
.memory-title {{
    color: {PURPLE_HALO};
    text-style: bold;
    padding: 0 0 1 0;
}}
.memory-row {{
    color: {LIGHT_PURPLE};
    padding: 0 0 0 1;
}}
.memory-row.-fresh {{
    color: {GREEN};
}}

/* ============== Command Palette (Ctrl+P) ============== */
#palette-screen {{
    align: center middle;
    background: rgba(7, 7, 11, 0.85);
}}
#palette-card {{
    width: 80;
    max-width: 90%;
    height: auto;
    background: {BG_GLASS_2};
    border: round {PURPLE_BRIGHT};
    padding: 1 2;
}}
#palette-title {{
    color: {PURPLE_HALO};
    text-style: bold;
}}
#palette-input {{
    background: {BG_DEEP};
    color: {LIGHT_PURPLE};
    border: tall {BORDER_GLASS};
    height: 3;
    padding: 0 1;
}}
#palette-input:focus {{
    border: tall {PURPLE_BRIGHT};
}}
#palette-list {{
    background: {BG_DEEP};
    color: {LIGHT_PURPLE};
    max-height: 18;
}}
#palette-list > .option-list--option-highlighted {{
    background: {PURPLE_DEEP};
    color: {WHITE};
    text-style: bold;
}}

/* ============== Picker modal (Ctrl+W) ============== */
#picker-screen {{
    align: center middle;
    background: rgba(7, 7, 11, 0.85);
}}
#picker-card {{
    width: 84;
    max-width: 92%;
    height: auto;
    background: {BG_GLASS_2};
    border: round {PURPLE_BRIGHT};
    padding: 1 2;
}}
#picker-title {{
    color: {PURPLE_HALO};
    text-style: bold;
    padding: 0 0 1 0;
}}
.picker-row {{
    height: auto;
    padding: 0;
    margin: 0 0 1 0;
}}
.picker-label {{
    color: {PURPLE_HALO};
    text-style: bold;
}}
.picker-input {{
    background: {BG_DEEP};
    color: {LIGHT_PURPLE};
    border: tall {BORDER_GLASS};
}}
.picker-input:focus {{
    border: tall {PURPLE_BRIGHT};
}}
Button {{
    background: {BG_GLASS_2};
    color: {LIGHT_PURPLE};
    border: tall {BORDER_GLASS};
}}
Button.-primary {{
    background: {PURPLE_BRIGHT};
    color: {BG_DEEP};
    text-style: bold;
}}
Button:hover {{
    background: {BG_GLASS_3};
}}
Button.-primary:hover {{
    background: {PURPLE_HALO};
}}

/* ============== Notifications ============== */
Toast {{
    background: {BG_GLASS_2};
    color: {LIGHT_PURPLE};
    border: round {BORDER_GLASS};
}}
Toast.-information {{
    border: round {CYAN};
}}
Toast.-warning {{
    border: round {YELLOW};
}}
Toast.-error {{
    border: round {RED};
}}

/* ============== Sinister Panel chrome utility classes ==============
 * Any widget that adds .sinister-panel / .sinister-tab / .sinister-button /
 * .sinister-card / .sinister-input / .sinister-card-strong gets the global
 * Sinister Panel chrome (purple-tinted bg + rounded border + halo accent
 * on focus/active). This means every NEW widget only needs `classes=
 * "sinister-panel"` to inherit the chrome — no per-widget DEFAULT_CSS.
 * ============================================================== */

.sinister-panel {{
    background: {BG};
    color: {LIGHT_PURPLE};
    border: round {BORDER_GLASS};
    padding: 0 1;
}}
.sinister-panel:focus-within {{
    border: round {PURPLE_BRIGHT};
    background: {BG_GLASS_1};
}}

.sinister-card {{
    background: {BG_GLASS_1};
    color: {LIGHT_PURPLE};
    border: round {BORDER_GLASS};
    padding: 1 2;
}}
.sinister-card-strong {{
    background: {BG_GLASS_2};
    color: {LIGHT_PURPLE};
    border: round {PURPLE_DEEP};
    padding: 1 2;
}}

.sinister-tab {{
    height: 3;
    margin: 0 1 1 1;
    padding: 1 1 0 2;
    background: {BG_GLASS_1};
    border: round {BORDER_GLASS};
    color: {SOFT};
}}
.sinister-tab.-active {{
    background: {BG_GLOW};
    color: {PURPLE_BRIGHT};
    border: round {PURPLE_BRIGHT};
    text-style: bold;
}}

.sinister-button {{
    background: {BG_GLASS_2};
    color: {LIGHT_PURPLE};
    border: round {BORDER_GLASS};
    padding: 0 2;
}}
.sinister-button.-primary {{
    background: {PURPLE_BRIGHT};
    color: {BG_DEEP};
    border: round {PURPLE_HALO};
    text-style: bold;
}}
.sinister-button:hover {{
    background: {BG_GLASS_3};
    border: round {PURPLE_BRIGHT};
}}

.sinister-input {{
    background: {BG_DEEP};
    color: {LIGHT_PURPLE};
    border: round {BORDER_GLASS};
    padding: 0 1;
}}
.sinister-input:focus {{
    border: round {PURPLE_BRIGHT};
    background: {BG_GLASS_1};
}}

.sinister-bar-top {{
    dock: top;
    height: 1;
    background: {BG};
    color: {SOFT};
    border-bottom: solid {BORDER_GLASS};
    padding: 0 1;
}}
.sinister-bar-bottom {{
    dock: bottom;
    height: 1;
    background: {BG};
    color: {SOFT};
    border-top: solid {BORDER_GLASS};
    padding: 0 1;
}}

.sinister-glyph {{
    color: {PURPLE_BRIGHT};
    text-style: bold;
}}
.sinister-glyph-halo {{
    color: {PURPLE_HALO};
    text-style: bold;
}}

/* Inputs at the bottom of agent panes inherit chrome */
.agent-input {{
    background: {BG_DEEP};
    color: {LIGHT_PURPLE};
    border: round {BORDER_GLASS};
}}
.agent-input:focus {{
    border: round {PURPLE_BRIGHT};
}}

/* Niri-style column chrome — applies the panel look to scrollable columns */
.agent-column {{
    background: {BG};
    border: round {BORDER_GLASS};
    padding: 0;
    margin: 0 1;
}}
.agent-column:focus-within {{
    border: round {PURPLE_BRIGHT};
}}
"""

# Reusable per-widget snippets. Widgets that prefer to keep their existing
# DEFAULT_CSS can import these and concatenate, but the preferred path is to
# rely on the global THEME_CSS classes above.

PANEL_CSS = f"""
.sinister-panel {{
    background: {BG};
    color: {LIGHT_PURPLE};
    border: round {BORDER_GLASS};
    padding: 0 1;
}}
"""

BUTTON_CSS = f"""
.sinister-button {{
    background: {BG_GLASS_2};
    color: {LIGHT_PURPLE};
    border: round {BORDER_GLASS};
}}
.sinister-button.-primary {{
    background: {PURPLE_BRIGHT};
    color: {BG_DEEP};
    text-style: bold;
}}
"""

TAB_CSS = f"""
.sinister-tab {{
    background: {BG_GLASS_1};
    color: {SOFT};
    border: round {BORDER_GLASS};
}}
.sinister-tab.-active {{
    background: {BG_GLOW};
    color: {PURPLE_BRIGHT};
    border: round {PURPLE_BRIGHT};
    text-style: bold;
}}
"""

INPUT_CSS = f"""
.sinister-input {{
    background: {BG_DEEP};
    color: {LIGHT_PURPLE};
    border: round {BORDER_GLASS};
}}
.sinister-input:focus {{
    border: round {PURPLE_BRIGHT};
}}
"""

# Operator-canonical export name. SINISTER_CSS kept for back-compat.
THEME_CSS = SINISTER_CSS
