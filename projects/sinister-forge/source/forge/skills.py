# Sinister Forge :: skills.py — SkillRegistry (jcode skill-loader port)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Port of jcode's skill-file loader. jcode discovers ~/.jcode/skills/*.md
# (and bundled skills) and registers each as a /<name> slash command. When
# invoked, the file's content is injected into the active system-prompt as
# `# Active Skill`. Brain doctrine for the port lives at
#   _shared-memory/knowledge/jcode-agentic-loop-patterns-port-to-python.md
# (pattern 5: "skills as slash-commands").
#
# Sources scanned (in order; later sources override earlier):
#   1. ~/.sinister/skills/*.md         (operator-local, follows operator)
#   2. D:/Sinister Sanctum/skills/*.md (fleet-bundled, ships with EXE)
#
# Frontmatter format (YAML between two `---` lines at top of file):
#   ---
#   name: my-skill
#   description: one-line summary shown in /skill list
#   allowed-tools: [bash, read_file, write_file]
#   ---
#   # Active Skill: my-skill
#   <markdown body — injected verbatim into system prompt>
#
# If frontmatter is missing, the registry falls back to using the first
# `# heading` line as `description`.
#
# Thread-safe via a module-level `threading.Lock`. If PyYAML is missing or
# the directory is unreachable, the registry logs a warning and returns
# empty — never crashes.

from __future__ import annotations

import glob
import logging
import os
import pathlib
import re
import threading
from dataclasses import dataclass
from typing import Optional


log = logging.getLogger("forge.skills")


# ---------------------------------------------------------------------------
# Skill dataclass
# ---------------------------------------------------------------------------

@dataclass
class Skill:
    """One discovered skill file."""

    name: str
    description: str
    allowed_tools: Optional[list[str]]
    content: str
    path: pathlib.Path

    def header(self) -> str:
        """One-line summary for /skill list output."""
        return f"/{self.name:<24} {self.description}"

    def prompt_block(self) -> str:
        """Body that gets injected into the system prompt as `# Active Skill`."""
        return f"# Active Skill: {self.name}\n\n{self.content.strip()}\n"


# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<yaml>.*?)\n---\s*\n?(?P<body>.*)\Z",
    re.DOTALL,
)
_HEADING_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)


def _parse_skill_file(path: pathlib.Path) -> Optional[Skill]:
    """Parse a single .md file into a Skill. Returns None on hard error."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        log.warning("skills: failed to read %s: %s", path, e)
        return None

    name = path.stem
    description = ""
    allowed_tools: Optional[list[str]] = None
    body = raw

    m = _FRONTMATTER_RE.match(raw)
    if m:
        yaml_block = m.group("yaml")
        body = m.group("body")
        try:
            import yaml  # type: ignore
            meta = yaml.safe_load(yaml_block) or {}
            if isinstance(meta, dict):
                name = str(meta.get("name", name))
                description = str(meta.get("description", "") or "")
                at = meta.get("allowed-tools") or meta.get("allowed_tools")
                if isinstance(at, list):
                    allowed_tools = [str(x) for x in at]
                elif isinstance(at, str):
                    allowed_tools = [s.strip() for s in at.split(",") if s.strip()]
        except ImportError:
            log.warning("skills: PyYAML missing — frontmatter ignored for %s", path)
        except Exception as e:
            log.warning("skills: failed to parse frontmatter in %s: %s", path, e)

    if not description:
        h = _HEADING_RE.search(body)
        if h:
            description = h.group(1).strip()
        else:
            description = "(no description)"

    return Skill(
        name=name,
        description=description,
        allowed_tools=allowed_tools,
        content=body,
        path=path,
    )


# ---------------------------------------------------------------------------
# SkillRegistry
# ---------------------------------------------------------------------------

def _sanctum_root() -> pathlib.Path:
    """Mirror commands._sanctum_root() — bundled skills live here."""
    for c in (os.environ.get("SANCTUM_ROOT"),
              r"D:\Sinister Sanctum", r"C:\Sinister Sanctum",
              str(pathlib.Path.home() / "Sinister Sanctum")):
        if c and (pathlib.Path(c) / "CLAUDE.md").exists():
            return pathlib.Path(c)
    return pathlib.Path(r"D:\Sinister Sanctum")


class SkillRegistry:
    """In-process registry of discovered skills.

    Construct via `SkillRegistry.shared()` for the lazily-loaded singleton,
    or `SkillRegistry().load()` for a fresh scan (e.g. /skill reload).
    """

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._loaded: bool = False
        self._roots: tuple[pathlib.Path, ...] = ()
        self._instance_lock: threading.Lock = threading.Lock()

    @classmethod
    def shared(cls) -> "SkillRegistry":
        global _SHARED_INSTANCE
        with _SHARED_LOCK:
            if _SHARED_INSTANCE is None:
                inst = cls()
                inst.load()
                _SHARED_INSTANCE = inst
        return _SHARED_INSTANCE

    @classmethod
    def reload_shared(cls) -> "SkillRegistry":
        """Force re-scan of the on-disk directories (e.g. after editing a skill)."""
        global _SHARED_INSTANCE
        with _SHARED_LOCK:
            _SHARED_INSTANCE = None
        return cls.shared()

    # --- discovery --------------------------------------------------------

    def _default_roots(self) -> list[pathlib.Path]:
        return [
            pathlib.Path.home() / ".sinister" / "skills",
            _sanctum_root() / "skills",
        ]

    def load(self, roots: Optional[list[pathlib.Path]] = None) -> "SkillRegistry":
        """Scan the configured roots for *.md, parse, populate the registry."""
        with self._instance_lock:
            self._skills.clear()
            scan_roots = roots if roots is not None else self._default_roots()
            self._roots = tuple(scan_roots)

            for root in scan_roots:
                try:
                    if not root.exists():
                        continue
                except OSError as e:
                    log.warning("skills: cannot stat %s: %s", root, e)
                    continue

                pattern = str(root / "*.md")
                try:
                    files = glob.glob(pattern)
                except OSError as e:
                    log.warning("skills: glob failed on %s: %s", pattern, e)
                    continue

                for fp in files:
                    p = pathlib.Path(fp)
                    # Skip README/HUB-style index files.
                    if p.stem.upper() in {"README", "HUB", "_INDEX", "INDEX", "SECURITY"}:
                        continue
                    skill = _parse_skill_file(p)
                    if skill is None:
                        continue
                    # Later roots override earlier ones (operator-local wins).
                    self._skills[skill.name] = skill

            self._loaded = True
            log.debug("skills: loaded %d skill(s) from %s",
                      len(self._skills), [str(r) for r in scan_roots])
        return self

    # --- accessors --------------------------------------------------------

    def get(self, name: str) -> Optional[Skill]:
        if not self._loaded:
            self.load()
        return self._skills.get(name)

    def names(self) -> list[str]:
        if not self._loaded:
            self.load()
        return sorted(self._skills.keys())

    def all(self) -> list[Skill]:
        if not self._loaded:
            self.load()
        return [self._skills[n] for n in sorted(self._skills.keys())]

    def roots(self) -> tuple[pathlib.Path, ...]:
        if not self._loaded:
            self.load()
        return self._roots

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self.get(name) is not None

    def __len__(self) -> int:
        if not self._loaded:
            self.load()
        return len(self._skills)


# Module-singleton state ------------------------------------------------------

_SHARED_INSTANCE: Optional[SkillRegistry] = None
_SHARED_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# File-system watcher — flips jcode-parity matrix row 18 from 🚧 → ✅
# ---------------------------------------------------------------------------
#
# Calls SkillRegistry.reload_shared() whenever a *.md under one of the scan
# roots is created/modified/deleted. Uses the `watchdog` package when
# available; degrades to a no-op + one-shot log warning when it isn't, so
# bundled EXEs without the dep still launch cleanly.
#
# Idempotent — second call returns the existing observer. Polling-style
# fallback NOT included; if watchdog is missing the operator can still use
# /skill reload manually.

_WATCHER_OBSERVER = None  # set to a watchdog Observer when started; else None
_WATCHER_LOCK = threading.Lock()


def start_watcher(callback=None, recursive: bool = False):
    """Watch skill roots for changes; call ``callback`` (default
    ``SkillRegistry.reload_shared``) whenever a *.md file changes.

    Returns the Observer instance on success, or None when ``watchdog`` is
    missing / the observer is already running / the roots don't exist.
    """
    global _WATCHER_OBSERVER
    with _WATCHER_LOCK:
        if _WATCHER_OBSERVER is not None:
            return _WATCHER_OBSERVER

        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            log.warning(
                "skills: watchdog package missing; auto-reload disabled "
                "(use /skill reload manually, or `pip install watchdog`)"
            )
            return None

        cb = callback or SkillRegistry.reload_shared

        class _SkillEventHandler(FileSystemEventHandler):
            def _maybe_reload(self, event) -> None:
                # Only react to *.md (and skip directory events outright).
                if event.is_directory:
                    return
                path = getattr(event, "dest_path", None) or event.src_path
                if not isinstance(path, str) or not path.lower().endswith(".md"):
                    return
                try:
                    cb()
                    log.debug("skills: auto-reloaded after %s on %s",
                              event.event_type, path)
                except Exception as exc:
                    log.warning("skills: auto-reload failed: %s", exc)

            on_created = _maybe_reload
            on_modified = _maybe_reload
            on_deleted = _maybe_reload
            on_moved = _maybe_reload

        observer = Observer()
        handler = _SkillEventHandler()
        roots = SkillRegistry()._default_roots()
        watched = 0
        for root in roots:
            try:
                if root.exists():
                    observer.schedule(handler, str(root), recursive=recursive)
                    watched += 1
            except OSError as exc:
                log.warning("skills: cannot schedule watch on %s: %s", root, exc)

        if watched == 0:
            log.debug("skills: no roots to watch; observer not started")
            return None

        observer.daemon = True
        observer.start()
        _WATCHER_OBSERVER = observer
        log.debug("skills: watchdog observing %d root(s); auto-reload on", watched)
        return observer


def stop_watcher() -> None:
    """Stop the file-system watcher started by :func:`start_watcher`. No-op
    when no watcher is running."""
    global _WATCHER_OBSERVER
    with _WATCHER_LOCK:
        obs = _WATCHER_OBSERVER
        _WATCHER_OBSERVER = None
    if obs is not None:
        try:
            obs.stop()
            obs.join(timeout=2.0)
        except Exception as exc:
            log.warning("skills: stop_watcher: %s", exc)


__all__ = ["Skill", "SkillRegistry", "start_watcher", "stop_watcher"]
