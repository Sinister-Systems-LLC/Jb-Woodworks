# Sinister Term :: theme.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Sinister palette for prompt_toolkit + rich.

from prompt_toolkit.styles import Style

# Sinister-canonical colors (must match Forge + Mind + Claw palettes)
PURPLE_DEEP = "#7A3DD4"
PURPLE_BRIGHT = "#A06EFF"
LIGHT_PURPLE = "#E8D6FF"
CYAN = "#6EE8FF"
GREEN = "#6EFFA0"
YELLOW = "#FFD66E"
RED = "#FF6E6E"
DIM = "#6E6E84"
BG_DEEP = "#07070B"

SINISTER_STYLE = Style.from_dict({
    # The user input
    "":                f"{LIGHT_PURPLE}",

    # Prompt
    "prompt.glyph":    f"{PURPLE_BRIGHT} bold",
    "prompt.project":  f"{CYAN}",
    "prompt.path":     f"{DIM}",
    "prompt.dollar":   f"{PURPLE_BRIGHT} bold",

    # Toolbar
    "bottom-toolbar":  f"bg:{BG_DEEP} {DIM}",
    "bottom-toolbar.section": f"bg:{BG_DEEP} {PURPLE_BRIGHT}",
    "bottom-toolbar.ok":      f"bg:{BG_DEEP} {GREEN}",
    "bottom-toolbar.warn":    f"bg:{BG_DEEP} {YELLOW}",

    # Completions
    "completion-menu":            f"bg:{BG_DEEP} {LIGHT_PURPLE}",
    "completion-menu.completion": f"bg:{BG_DEEP} {LIGHT_PURPLE}",
    "completion-menu.completion.current": f"bg:{PURPLE_BRIGHT} {BG_DEEP} bold",
    "completion-menu.meta":               f"bg:{BG_DEEP} {DIM}",
    "completion-menu.meta.completion.current": f"bg:{PURPLE_DEEP} {LIGHT_PURPLE}",
    "completion-menu.multi-column-meta": f"bg:{BG_DEEP} {DIM}",

    # Search
    "search":               f"bg:{PURPLE_DEEP} {LIGHT_PURPLE}",
    "search.current":       f"bg:{PURPLE_BRIGHT} {BG_DEEP} bold",
})


BANNER = """
  [purple]◈[/purple] [bold purple]SINISTER TERM[/bold purple]  [dim]:: handterm-inspired :: RKOJ-ELENO 2026-05-21[/dim]

  [cyan]/forge[/cyan]  [cyan]/mind[/cyan]  [cyan]/launch <project>[/cyan]  [cyan]/bot <name>[/cyan]  [cyan]/skill <name>[/cyan]
  [cyan]/projects[/cyan]  [cyan]/heartbeats[/cyan]  [cyan]/commits[/cyan]  [cyan]/help[/cyan]  [cyan]/exit[/cyan]

  Anything else runs in the underlying shell (powershell on Windows).
"""
