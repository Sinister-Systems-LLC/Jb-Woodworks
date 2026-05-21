# Sinister Term :: completer.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Builtin slash-command completer + project-key completer + filesystem completer.

from __future__ import annotations

from pathlib import Path

from prompt_toolkit.completion import Completer, Completion, PathCompleter

from term.commands import COMMANDS, project_keys


class SinisterCompleter(Completer):
    """Three-mode completion:
    - Line starts with `/` -> slash commands + their args
    - Line is empty or whitespace -> show top slash commands as hint
    - Otherwise -> filesystem (PathCompleter)
    """

    def __init__(self) -> None:
        self._path = PathCompleter(expanduser=True)

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        words = text.split()

        if not words and text == "":
            # empty -> hint a few useful commands
            for hint in ("/help", "/forge", "/mind", "/projects", "/launch ", "/heartbeats"):
                yield Completion(hint, start_position=0)
            return

        if text.startswith("/"):
            # `/<partial>` -> command names
            if len(words) == 1 and not text.endswith(" "):
                partial = words[0][1:].lower()
                for name in sorted(COMMANDS.keys()):
                    if name.startswith(partial):
                        yield Completion(
                            "/" + name,
                            start_position=-len(words[0]),
                            display_meta=COMMANDS[name].__doc__ or "",
                        )
                return

            cmd_name = words[0][1:].lower()
            # Project-aware completers for /launch + /cd
            if cmd_name in ("launch", "cd"):
                current = words[-1] if len(words) > 1 and not text.endswith(" ") else ""
                for key in project_keys():
                    if not current or key.startswith(current):
                        yield Completion(
                            key,
                            start_position=-len(current),
                            display_meta=f"sinister project",
                        )
                return

            # Otherwise let path completer handle args
            yield from self._path.get_completions(document, complete_event)
            return

        # No slash -> path/filesystem
        yield from self._path.get_completions(document, complete_event)
