# Sinister Forge :: swarm.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# PH16 in-Forge swarm primitives. Operator 2026-05-21 (image 11:48Z):
# "i want all jcode features in our system like this" - re: jcode swarm
# (multi-agent collaboration with file-edit notifications + DM/broadcast).
#
# This module is the *pane-local* implementation. Sanctum's tools/sinister-
# swarm/ is the fleet-level dispatcher; this is what the Forge TUI calls
# when the operator triggers `:dm` / `:broadcast` / `:swarm` from a pane.
#
# All operations write inbox JSONs to `_shared-memory/inbox/<slug>/`
# matching the schema sibling agents already read on their inbox_poll.

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SANCTUM_ROOT = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")
INBOX_DIR = SANCTUM_ROOT / "_shared-memory" / "inbox"

# Known sibling slugs. ":broadcast" without target list defaults to all of these
# minus the sender. Operator can add more by dropping the slug as a subdirectory.
KNOWN_SLUGS = (
    "sanctum",
    "sanctum-audit",
    "sinister-term",
    "sinister-forge",
    "forge",
    "kernel-apk",
    "panel",
    "rkoj",
    "freeze",
    "snap-emulator-api",
    "tiktok-emulator-api",
    "bumble-emulator-api",
)


@dataclass(slots=True)
class SwarmMessage:
    tag: str  # "[DM]" | "[BROADCAST]" | "[ASK]" | "[FILE-CHANGED]"
    from_slug: str
    to_slug: str
    subject: str
    body: str
    project_hint: str = ""
    payload: dict | None = None

    def filename(self) -> str:
        ts = _utc_compact()
        safe_subj = "".join(c if c.isalnum() or c in "-_" else "-" for c in self.subject)[:60]
        # Disambiguate concurrent sends within the same second via a short uuid
        short = uuid.uuid4().hex[:6]
        return f"{ts}-{self.from_slug}-{self.tag.strip('[]').lower()}-{safe_subj or 'msg'}-{short}.json"

    def to_dict(self) -> dict:
        payload = {
            "_author": "RKOJ-ELENO :: 2026-05-21",
            "tag": self.tag,
            "from": self.from_slug,
            "to": self.to_slug,
            "ts_utc": _utc_iso(),
            "subject": self.subject,
            "message": self.body,
        }
        if self.project_hint:
            payload["project_hint"] = self.project_hint
        if self.payload:
            payload["payload"] = self.payload
        return payload


# ---- Public API (called by app.py palette handlers + bridge file-watcher) ----


def send_dm(*, from_slug: str, to_slug: str, subject: str, body: str,
            project_hint: str = "") -> Path:
    """Drop a `[DM]` JSON into `_shared-memory/inbox/<to_slug>/`. Returns the path."""
    msg = SwarmMessage(
        tag="[DM]",
        from_slug=from_slug,
        to_slug=to_slug,
        subject=subject,
        body=body,
        project_hint=project_hint,
    )
    return _write_inbox(to_slug, msg)


def broadcast(*, from_slug: str, subject: str, body: str,
              project_hint: str = "",
              recipients: Iterable[str] | None = None) -> list[Path]:
    """Fan out a `[BROADCAST]` to all known slugs (except sender) or a custom list."""
    targets = list(recipients) if recipients else [s for s in KNOWN_SLUGS if s != from_slug]
    out: list[Path] = []
    for slug in targets:
        msg = SwarmMessage(
            tag="[BROADCAST]",
            from_slug=from_slug,
            to_slug=slug,
            subject=subject,
            body=body,
            project_hint=project_hint,
        )
        out.append(_write_inbox(slug, msg))
    return out


def notify_file_changed(*, editor_slug: str, file_path: str,
                        subscribers: Iterable[str]) -> list[Path]:
    """jcode-swarm parity: when an agent edits a file, notify all subscribed
    agents EXCEPT the editor. Used by the bridge watchdog observer."""
    out: list[Path] = []
    body = f"File modified: {file_path}"
    for slug in subscribers:
        if slug == editor_slug:
            continue
        msg = SwarmMessage(
            tag="[FILE-CHANGED]",
            from_slug=editor_slug,
            to_slug=slug,
            subject=f"file-changed:{Path(file_path).name}",
            body=body,
            payload={"path": file_path, "editor": editor_slug},
        )
        out.append(_write_inbox(slug, msg))
    return out


def known_slugs() -> tuple[str, ...]:
    """Operator-extensible list of valid recipient slugs.

    Includes any subdirectory already present under `_shared-memory/inbox/`
    so newly-spawned per-project agents pick up automatically.
    """
    discovered: set[str] = set(KNOWN_SLUGS)
    if INBOX_DIR.exists():
        for child in INBOX_DIR.iterdir():
            if child.is_dir() and not child.name.startswith("_"):
                discovered.add(child.name)
    return tuple(sorted(discovered))


# ---- Internals ----


def _write_inbox(to_slug: str, msg: SwarmMessage) -> Path:
    target = INBOX_DIR / to_slug
    target.mkdir(parents=True, exist_ok=True)
    path = target / msg.filename()
    path.write_text(json.dumps(msg.to_dict(), indent=2), encoding="utf-8")
    return path


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _utc_compact() -> str:
    return time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
