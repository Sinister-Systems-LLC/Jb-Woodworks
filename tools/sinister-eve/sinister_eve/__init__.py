# Author: RKOJ-ELENO :: 2026-05-23
"""sinister-eve — jcode-style standalone CLI REPL with EVE persona.

Spawns `claude --dangerously-skip-permissions --output-format stream-json
--include-partial-messages --verbose` per turn. Reuses the same NDJSON
parsing pattern as RKOJ's agents_tab so token-by-token streaming,
thinking deltas, tool-use markers, and cost-per-turn all render with
ANSI colors instead of QTextCharFormat.

Built as a PyInstaller onefile EXE shipped to Desktop alongside RKOJ.exe.
"""

__version__ = "0.1.0"
__author__ = "RKOJ-ELENO"
