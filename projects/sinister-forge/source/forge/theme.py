# Sinister Forge :: theme.py (v3 - liquid-glass overhaul)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Heavy liquid-glass aesthetic per operator directive 2026-05-21:
# "the jcode liquid glass system... iOS 18 purple approach... all features
# he has etc with what we need i asked for and expanded onto it"
#
# Translating CSS liquid-glass to Textual:
#   - backdrop-filter isn't possible in a terminal -> simulate via
#     layered borders + tinted bg steps + soft accent washes
#   - rounded panels via Textual's "round" border style
#   - chrome bars get gradient feel by stacking thin solid rows of
#     gradually-stepped purples (handled by AccentBar widget)
#   - glow tints applied to active states via brighter bg colors
#   - no white headers anywhere - operator screenshot showed default
#     Textual Header which we now replace with our purple ChromeBar

# Sinister-canonical hex colors (synced with Claw/Mind/Term)
BG_DEEP        = "#07070B"   # void
BG             = "#0E0A14"   # primary surface
BG_GLASS_1     = "#15131A"   # tinted layer 1
BG_GLASS_2     = "#1C1626"   # tinted layer 2
BG_GLASS_3     = "#231A33"   # tinted layer 3 (hover)
BG_GLOW        = "#2A1F3D"   # active wash

PURPLE_DEEP    = "#7A3DD4"
PURPLE_BRIGHT  = "#A06EFF"   # operator standing-order accent
PURPLE_HALO    = "#C39DFF"
LIGHT_PURPLE   = "#E8D6FF"

CYAN           = "#6EE8FF"
GREEN          = "#6EFFA0"
YELLOW         = "#FFD66E"
RED            = "#FF6E6E"
MAGENTA        = "#FF6EE8"
ORANGE         = "#FF8C42"

WHITE          = "#F5F5FA"
DIM            = "#6E6E84"
SOFT           = "#999AB0"

BORDER_GLASS   = "#3A2A55"   # subtle purple-tinted border
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
"""
