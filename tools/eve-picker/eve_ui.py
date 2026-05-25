"""eve_ui.py :: shared sub-page primitives for EVE.exe / tools.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25T00:15Z:
    "each menu needs to go to a complete clean new menu that is clean and you
     cannot see the menu you just came from. each page needs to same hedaer
     and same footer and same page structure style and from and same
     scrolling that highlights and makes it enlarge and look cooler. simpler
     clean sleek."

Provides the canonical primitives every EVE sub-page MUST use:

    clear_screen()              -- wipe + cursor-home BEFORE rendering a page
    print_sub_page_header(t)    -- DARKP --- WHITE BOLD title DARKP ---
    print_sub_page_footer(x)    -- DIM --- B) Back   H) Home   X) Exit (...)
    highlight_row(text, sel, t) -- subtle purple-glow bar + enlarge effect
                                    matches main_menu.py highlight pattern.

Color tokens match `eve-ui-uniformity-doctrine-2026-05-24.md`. Module is
self-contained (no eve.py import) so health_tools / quantum_tools /
account_manager can import without circular-import risk. main_menu.py keeps
its private highlight implementation (already tuned for its menu); shared
sub-pages use this module's highlight for the same look-and-feel.

Composes with:
  * main_menu.py highlight_row (private; same visual pattern)
  * eve.py _print_sub_page_header / _print_sub_page_footer (which now also
    call clear_screen() at the top)
"""
from __future__ import annotations

import os
import sys

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# ANSI palette -- canonical tokens (matches eve-ui-uniformity-doctrine table)
# ---------------------------------------------------------------------------

def _ansi_on() -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    term = os.environ.get("TERM", "").strip().lower()
    if term == "dumb" and os.name != "nt":
        return False
    return True


_ANSI = _ansi_on()


def _c(seq: str) -> str:
    return seq if _ANSI else ""


PURPLE = _c("\033[38;5;141m")
DARKP = _c("\033[38;5;91m")
BRIGHTP = _c("\033[38;5;177m")
WHITE = _c("\033[97m")
SOFT = _c("\033[38;5;245m")
DIM = _c("\033[38;5;240m")
OK = _c("\033[38;5;46m")
WARN = _c("\033[38;5;220m")
FAIL = _c("\033[38;5;196m")
RESET = _c("\033[0m")
BOLD = _c("\033[1m")

# Sinister Sleight palette (operator hard-canonical 2026-05-25, based on
# banner-hero-statement.png -- purple jester w/ neon ring). Doctrine:
# _shared-memory/knowledge/sinister-sleight-color-palette-doctrine-2026-05-25.md
SLEIGHT_DEEP_PURPLE = _c("\033[38;5;55m")    # background-tier deep purple
SLEIGHT_PURPLE      = _c("\033[38;5;99m")    # mid-tier
SLEIGHT_JESTER      = _c("\033[38;5;141m")   # foreground (aliases PURPLE)
SLEIGHT_NEON_MAG    = _c("\033[38;5;201m")   # neon magenta glow
SLEIGHT_NEON_PINK   = _c("\033[38;5;205m")   # highlights
SLEIGHT_RUNE_VIO    = _c("\033[38;5;177m")   # rune border (aliases BRIGHTP)
SLEIGHT_TAROT_CYAN  = _c("\033[38;5;87m")    # card swirl accent
SLEIGHT_CROWN_GOLD  = _c("\033[38;5;220m")   # crown accent -- use SPARINGLY


# ---------------------------------------------------------------------------
# Screen primitives
# ---------------------------------------------------------------------------

def clear_screen() -> None:
    """Wipe terminal + move cursor home.

    Operator 2026-05-25T00:15Z: "each menu needs to go to a complete clean
    new menu that is clean and you cannot see the menu you just came from."

    Uses ANSI \\033[2J (erase entire screen) + \\033[H (cursor home). On
    non-ANSI terminals this is a no-op (NO_COLOR or TERM=dumb on POSIX).
    Buffered into ONE write+flush so the wipe is atomic (no flash).
    """
    if not _ANSI:
        return
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def _strip_ansi(s: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == "\033" and i + 1 < len(s) and s[i + 1] == "[":
            j = i + 2
            while j < len(s) and s[j] not in "ABCDEFGHJKSTfmnsulh":
                j += 1
            i = j + 1
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


def visible_len(s: str) -> int:
    return len(_strip_ansi(s))


# ---------------------------------------------------------------------------
# Centering helper (RKOJ-ELENO :: 2026-05-25T01:15Z)
# Operator hard-canonical 2026-05-25T01:15Z (image #61 + image #62):
# *"centered menu styling like main_menu hero applied to every sub-page"*.
# Sub-pages were rendering left-aligned (ugly on wide terminals); body blocks
# now block-center using one common pad so columns align as a unit.
# ---------------------------------------------------------------------------

# Canonical centered-body width (clamped 60-72; main_menu uses _BAR_WIDTH=64).
# Smaller = fits narrow terminals; larger = breathes on wide terminals.
DEFAULT_BLOCK_WIDTH = 64


def term_cols() -> int:
    """Best-effort terminal column width. Falls back to 80."""
    try:
        cols = os.get_terminal_size().columns
        return max(60, cols)
    except (OSError, ValueError):
        return 80


def center_block(lines, width: int | None = None):
    """Block-center a list of strings horizontally.

    Each line gets the SAME left-pad (computed from the widest line's visible
    width + the chosen block width clamped to terminal columns) so columns
    inside the block stay aligned as a unit (vs per-line centering which
    would jitter columns).

    Args:
        lines: iterable of strings (may contain ANSI; visible width is
               measured ANSI-stripped via visible_len()).
        width: target block width in cells (60-72 recommended). If None,
               uses DEFAULT_BLOCK_WIDTH clamped to terminal cols.

    Returns:
        list[str] of padded lines ready to print()/join.
    """
    line_list = list(lines)
    if not line_list:
        return []
    cols = term_cols()
    if width is None:
        width = DEFAULT_BLOCK_WIDTH
    # Cap block width to terminal so narrow terminals still align
    block_w = min(width, cols)
    # Find widest visible-length line; use that to compute the LEFT pad
    max_visible = max((visible_len(ln) for ln in line_list), default=0)
    # Centered block: pad based on the BLOCK width (not the longest line) so
    # blocks of different content all center on the same vertical axis.
    effective_w = max(max_visible, block_w)
    pad = max(0, (cols - effective_w) // 2)
    pad_str = " " * pad
    return [pad_str + ln for ln in line_list]


def print_centered_block(lines, width: int | None = None) -> None:
    """Center a block of lines and print each on its own line."""
    for ln in center_block(lines, width=width):
        print(ln)


# ---------------------------------------------------------------------------
# Header / footer (canonical per eve-ui-uniformity-doctrine)
# ---------------------------------------------------------------------------

def print_sub_page_header(title: str) -> None:
    """Canonical header line: DARKP --- WHITE BOLD title DARKP ---.

    Clears screen FIRST so the new sub-page lands on a blank surface (the
    operator never sees the prior menu underneath). One blank line after the
    title for body breathing room.
    """
    clear_screen()
    print()
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}{title}{RESET} {DARKP}---{RESET}")
    print()


def print_sub_page_footer(extra_keys: str = "") -> None:
    """Canonical footer: DIM --- PURPLE B) Back   PURPLE H) Home   PURPLE X) Exit   DIM (extras)."""
    keys = f"{DIM}({extra_keys}){RESET}" if extra_keys else ""
    line = (
        f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   "
        f"{PURPLE}H){RESET} Home   "
        f"{PURPLE}X){RESET} Exit"
    )
    if keys:
        line = f"{line}   {keys}"
    print()
    print(line)


def handle_nav(resp: str) -> str | None:
    """Common B / H / X dispatch.

    Returns:
      - "back" : caller should `return` to parent.
      - "home" : caller should `return` (it already routed to main menu).
      - None   : caller continues handling page-specific keys.
    """
    r = (resp or "").strip().lower()
    if r in ("b", "back", ""):
        return "back"
    if r in ("h", "home"):
        try:
            from main_menu import show_main_menu  # type: ignore
            show_main_menu()
        except Exception:
            pass
        return "home"
    if r in ("x", "exit", "q", "quit"):
        sys.exit(0)
    return None


# ---------------------------------------------------------------------------
# Scroll-highlight helper (matches main_menu.py glow-bar pattern)
# ---------------------------------------------------------------------------

# Glow palette: 256-color background indices that look subtle-purple in
# mintty / windows-terminal. Pulse cycles slowly (every 3 ticks).
#   54 = #5f0087  mid Sinister purple
#   92 = #8700d7  brighter Sinister purple (pop)
#   55 = #5f00af  deep-bright violet
# RKOJ-ELENO :: 2026-05-25 :: bumped from (53,54,60) to (54,92,55) for
# stronger visibility on operator's display.
_GLOW_BG_PALETTE = (54, 99, 55, 141, 99)   # breathes through Sleight purples
_DEFAULT_BAR_WIDTH = 56


def highlight_row(text: str, is_selected: bool, tick: int = 0,
                  bar_width: int = _DEFAULT_BAR_WIDTH) -> str:
    """Render a selectable list row.

    If `is_selected`: brighter purple-glow background bar extends edge-to-edge
    with arrow indicator + bold bright-white foreground. Bg pulses slowly via
    `tick // 3 % len(palette)` -- gentle 3-frame breath.

    If not selected: plain text, padded to bar width so all rows occupy the
    same footprint (so the selected bar doesn't shift the layout).

    Same visual pattern as main_menu._highlight_row -- shared so every sub-
    page with a selectable list has the same look-and-feel.
    """
    visible = visible_len(text)
    if not is_selected:
        pad_total = max(0, bar_width - visible)
        return " " * 2 + text + " " * max(0, pad_total - 2)
    if not _ANSI:
        pad_total = max(0, bar_width - visible - 2)
        return f"▶ {text}" + " " * pad_total
    bg_idx = _GLOW_BG_PALETTE[(tick // 3) % len(_GLOW_BG_PALETTE)]
    bg_code = f"\033[48;5;{bg_idx}m"
    bold = "\033[1m"
    fg = "\033[97m"
    arrow = "▶ "
    pad_total = max(0, bar_width - visible - len(arrow) - 4)
    return f"{bg_code}{bold}{fg} {arrow}{text}{' ' * (2 + pad_total)}{RESET}"


# ---------------------------------------------------------------------------
# Smoke test entry
# ---------------------------------------------------------------------------

def _smoke() -> int:
    """Render header + 3 rows (one selected) + footer and exit 0."""
    print_sub_page_header("Smoke Test")
    print(highlight_row(f"{PURPLE}1){RESET} {WHITE}First option{RESET}    {DIM}hint one{RESET}", False))
    print(highlight_row(f"{PURPLE}2){RESET} {WHITE}Second option{RESET}   {DIM}hint two{RESET}", True, tick=0))
    print(highlight_row(f"{PURPLE}3){RESET} {WHITE}Third option{RESET}    {DIM}hint three{RESET}", False))
    print_sub_page_footer("1-3 to run")
    print(f"\n{OK}[smoke] eve_ui.py OK{RESET}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        sys.exit(_smoke())
    print("eve_ui.py -- import-only module. Run with --smoke to demo.")
