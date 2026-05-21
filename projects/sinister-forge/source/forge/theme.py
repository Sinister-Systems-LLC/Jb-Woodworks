# Sinister Forge :: theme.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Sinister theme - purple primary on black, dim cyan secondary.
# Matches the existing launcher PS1 color set + operator standing order.

# Primary palette (matches automations/start-sinister-session.ps1 colors)
PURPLE = "#7A3DD4"           # operator standing order accent
PURPLE_BRIGHT = "#A06EFF"    # hover / active
PURPLE_DIM = "#15131A"       # background

LIGHT_PURPLE = "#E8D6FF"     # foreground primary
CYAN = "#6EE8FF"             # secondary accent / links
CYAN_DIM = "#D6F4FF"
GLOW = "#6EFFA0"             # success / OK
WARN = "#FFD66E"             # warning / pending
RED = "#FF6E6E"              # error / fail
WHITE = "#EEEEEE"
DIM = "#666666"
SOFT = "#999999"
BLACK = "#0A0A0F"

# Per-agent accent palette (each spawned agent picks one)
AGENT_ACCENTS = {
    "purple":  "#A06EFF",
    "magenta": "#FF6EE8",
    "cyan":    "#6EE8FF",
    "green":   "#6EFFA0",
    "yellow":  "#FFD66E",
    "red":     "#FF6E6E",
    "white":   "#EEEEEE",
}

# Textual CSS (PH1 - minimal)
SINISTER_CSS = """
Screen {
    background: #0A0A0F;
    color: #EEEEEE;
}

Header {
    background: #15131A;
    color: #E8D6FF;
    text-style: bold;
}

Footer {
    background: #15131A;
    color: #6EE8FF;
}

.agent-pane {
    border: round #7A3DD4;
    background: #0A0A0F;
    padding: 1 2;
}

.agent-header {
    background: #7A3DD4;
    color: #EEEEEE;
    text-style: bold;
    padding: 0 1;
}

.boot-logo {
    color: #A06EFF;
    text-align: center;
}

.status-ok {
    color: #6EFFA0;
}

.status-pending {
    color: #FFD66E;
}

.status-fail {
    color: #FF6E6E;
}

.dim {
    color: #666666;
}
"""
