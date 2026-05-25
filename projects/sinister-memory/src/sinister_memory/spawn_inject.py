# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: spawn_inject.

Emits a markdown chunk of the last-N memories for a given agent slug. Designed
to be embedded into `automations/start-sinister-session.ps1` Build-Phrase so
every spawn loads with full cross-session continuity.

Bash/PowerShell-safe output: no backticks, no '@'+'@' sequences that would
collide with PS1 here-strings.

Public API:
  inject_for_spawn(slug, root, limit=5) -> str
"""
from __future__ import annotations

from pathlib import Path

from .auto_save import list_iters


def _read_summary(path: Path) -> tuple[str, str]:
    """Return (iter_label, body) from an iter-*.md file. Body is post-frontmatter."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return path.stem, "(unreadable)"

    # Strip YAML-ish frontmatter
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            body = text[end + 5 :]

    # Trim to first ~500 chars + strip leading H1 ("# slug :: iter-N")
    body_lines = [ln for ln in body.splitlines() if ln.strip()]
    if body_lines and body_lines[0].startswith("# "):
        body_lines = body_lines[1:]
    body_trim = "\n".join(body_lines)[:500]

    label = path.stem
    return label, body_trim or "(empty)"


def _sanitize_for_ps_heredoc(s: str) -> str:
    """Remove characters that break PS1 single-quoted here-strings."""
    # PS1 single-quoted here-strings are terminated by `'@` at column 0.
    # Replace any "'@" occurrences and standalone backticks to keep the chunk safe.
    return s.replace("'@", "'-at-").replace("`", "'")


def inject_for_spawn(slug: str, root: Path, limit: int = 5) -> str:
    """Return a markdown chunk of last-N iter summaries for the slug.

    Format:
      ## Last memories (sinister-memory)
      ### iter-0023 (per-agent/<slug>/iter-0023.md)
      <body excerpt, up to 500 chars>
      ...

    If no memories exist for the slug, returns a single line stub so the spawn
    phrase still includes an explicit "no prior memory" marker.
    """
    files = list_iters(slug, root)[:limit]
    if not files:
        return f"## Last memories (sinister-memory)\n\n_(no prior memories for {slug})_\n"

    chunks: list[str] = ["## Last memories (sinister-memory)\n"]
    for f in files:
        label, body = _read_summary(f)
        # Express path relative to root if possible
        try:
            rel = f.relative_to(Path(root)).as_posix()
        except ValueError:
            rel = str(f)
        chunks.append(f"### {label} ({rel})\n{_sanitize_for_ps_heredoc(body)}\n")
    return "\n".join(chunks)
