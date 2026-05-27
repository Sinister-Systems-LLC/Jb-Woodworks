# Sinister Term :: rmux.py
# Author: RKOJ-ELENO :: 2026-05-26
# License: AGPL-3.0-or-later
#
# Sinister rmux — htop-style fleet monitor for Claude Code + Sinister agents.
#
# Operator directive 2026-05-26 ~23:30Z (verbatim):
#   "i need a rmux system to full all my agents in with all features like that
#    and i need this asap aswell to see what they all do. agtop:
#    C:\\Users\\Zonia\\Desktop\\agtop-main"
#
# Inspired by agtop (https://github.com/ldegio/agtop, GPL-2.0-only). We read the
# same JSONL transcripts (~/.claude/projects/<proj>/*.jsonl) but port the parsing
# + scoring + rendering to Python under AGPL-3.0-or-later. Per
# `we-have-the-source-read-it-doctrine-2026-05-25` we read source directly; no RE.
#
# Surfaces:
#   - sessions list (one row per JSONL file under ~/.claude/projects/**)
#   - per-session: model, age, tokens in/out, cache hit %, cost USD, top tool,
#     last activity, project shorthand, git branch
#   - sortable by cost/age/tokens; filterable to LIVE (active in last 5 min)
#   - composes with sinister fleet heartbeats so each session can also be tagged
#     with the local slug (heartbeats dir cross-reference by cwd)

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Pricing snapshot (USD per 1M tokens). Hardcoded mid-2026 public prices; refresh
# via LiteLLM later. Cache reads priced at 10% of input (Anthropic standard);
# cache writes priced at 1.25x input. Fallback model uses opus rates so spend
# tracking is conservative when a model is unknown.
# ---------------------------------------------------------------------------

# Per-1M-token USD rates. Mirrors agtop's hardcoded Claude table at
# C:\Users\Zonia\Desktop\agtop-main\index.js:82-125 (verified 2026-05-26).
# Anthropic's cache-write tier splits into a 5-min ephemeral (cheaper) and a 1-h
# ephemeral (pricier) bucket — the JSONL exposes each separately so we track
# both fields. Cache reads are ~10% of base input.
PRICING: dict[str, dict[str, float]] = {
    # claude opus 4.x
    "claude-opus-4-7":   {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.5},
    "claude-opus-4-6":   {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.5},
    "claude-opus-4-5":   {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.5},
    "claude-opus-4":     {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.5},
    # claude sonnet 4.x
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_write_5m": 3.75, "cache_write_1h": 6.0,  "cache_read": 0.3},
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0, "cache_write_5m": 3.75, "cache_write_1h": 6.0,  "cache_read": 0.3},
    "claude-sonnet-4":   {"input": 3.0, "output": 15.0, "cache_write_5m": 3.75, "cache_write_1h": 6.0,  "cache_read": 0.3},
    # claude haiku 4.x
    "claude-haiku-4-5":  {"input": 1.0, "output": 5.0,  "cache_write_5m": 1.25, "cache_write_1h": 2.0,  "cache_read": 0.1},
    "claude-haiku-4":    {"input": 1.0, "output": 5.0,  "cache_write_5m": 1.25, "cache_write_1h": 2.0,  "cache_read": 0.1},
    # codex / openai (we read ~/.codex/sessions/ in iter-2; cached-input only)
    "gpt-5.3-codex":     {"input": 1.75, "output": 14.0, "cache_write_5m": 0.0, "cache_write_1h": 0.0, "cache_read": 0.175},
    "codex-mini-latest": {"input": 1.5,  "output": 6.0,  "cache_write_5m": 0.0, "cache_write_1h": 0.0, "cache_read": 0.375},
}

DEFAULT_PRICING = PRICING["claude-opus-4-7"]

# Context window per model family (tokens). 1m variants override.
CTX_MAX: dict[str, int] = {
    "claude-opus-4-7":   200_000,
    "claude-opus-4-6":   200_000,
    "claude-sonnet-4-6": 200_000,
    "claude-haiku-4-5":  200_000,
    "gpt-4.1":           1_000_000,
    "o1":                200_000,
}
DEFAULT_CTX_MAX = 200_000

# Some Claude Code records carry the `[1m]` suffix on the model id when the
# 1M-context tier is in use. We normalize via _normalize_model().


def _normalize_model(raw: str | None) -> str:
    if not raw:
        return "unknown"
    m = raw.strip().lower()
    # strip claude-code's `[1m]` etc. suffix tag
    if "[" in m:
        m = m.split("[", 1)[0]
    return m


def _ctx_max_for(model: str, raw_tag: str | None) -> int:
    if raw_tag and "[1m]" in raw_tag.lower():
        return 1_000_000
    return CTX_MAX.get(model, DEFAULT_CTX_MAX)


def _price_for(model: str) -> dict[str, float]:
    # exact match first; then prefix family fallback
    if model in PRICING:
        return PRICING[model]
    for k in PRICING:
        if model.startswith(k):
            return PRICING[k]
    # family-level fuzzy
    if "opus" in model:
        return PRICING["claude-opus-4-7"]
    if "sonnet" in model:
        return PRICING["claude-sonnet-4-6"]
    if "haiku" in model:
        return PRICING["claude-haiku-4-5"]
    return DEFAULT_PRICING


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class RmuxSession:
    """One Claude Code / Codex JSONL session, parsed + scored."""

    path: Path
    session_id: str = ""
    project_dir: str = ""        # directory mapped from the parent dir name
    model: str = "unknown"
    raw_model: str = ""          # original string including [1m] tag if present
    cwd: str = ""
    git_branch: str = ""
    cc_version: str = ""         # claude-code version string
    started_at: float = 0.0      # earliest timestamp seen (epoch s)
    last_active: float = 0.0     # latest timestamp seen (epoch s)
    turn_count: int = 0          # assistant messages
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0     # combined 5m + 1h cache writes
    cache_write_5m_tokens: int = 0     # ephemeral_5m_input_tokens (cheap tier)
    cache_write_1h_tokens: int = 0     # ephemeral_1h_input_tokens (pricier tier)
    cache_read_tokens: int = 0
    last_ctx_tokens: int = 0           # CTX% basis: input + cache_creation + cache_read of LAST turn
                                        # (per agtop index.js:2016-2090; output NOT included)
    tool_counts: dict[str, int] = field(default_factory=dict)
    last_tool: str = ""
    last_tool_ts: float = 0.0
    file_size: int = 0
    parse_error: str = ""
    # iter-80: cross-reference with sinister fleet heartbeats. Populated by
    # scan_sessions() after parsing. Empty when no matching heartbeat is found
    # (e.g. session belongs to a project not yet onboarded into the fleet).
    fleet_slug: str = ""
    fleet_heartbeat_age_sec: float = 0.0  # heartbeat freshness (0 = unknown)

    @property
    def age_seconds(self) -> float:
        if self.last_active <= 0:
            return 0.0
        return max(0.0, time.time() - self.last_active)

    @property
    def ctx_pct(self) -> float:
        # 1m tier auto-promote: if a single turn exceeded 200k tokens, treat the
        # session as on the 1m plan even without an explicit [1m] tag.
        # (agtop index.js:2016-2090.)
        ctx_max = _ctx_max_for(self.model, self.raw_model)
        if self.last_ctx_tokens > 200_000 and ctx_max == 200_000:
            ctx_max = 1_000_000
        if ctx_max <= 0:
            return 0.0
        return min(100.0, 100.0 * self.last_ctx_tokens / ctx_max)

    @property
    def cost_usd(self) -> float:
        p = _price_for(self.model)
        return (
            self.input_tokens             * p["input"]          / 1_000_000.0
            + self.output_tokens          * p["output"]         / 1_000_000.0
            + self.cache_write_5m_tokens  * p["cache_write_5m"] / 1_000_000.0
            + self.cache_write_1h_tokens  * p["cache_write_1h"] / 1_000_000.0
            + self.cache_read_tokens      * p["cache_read"]     / 1_000_000.0
        )

    @property
    def is_live(self) -> bool:
        # match agtop's default "live" definition: active in last 5 min
        return self.age_seconds <= 300.0

    @property
    def top_tool(self) -> str:
        if not self.tool_counts:
            return ""
        return max(self.tool_counts.items(), key=lambda kv: kv[1])[0]


# ---------------------------------------------------------------------------
# Scanner — parses one JSONL file into an RmuxSession
# ---------------------------------------------------------------------------


def _parse_iso(ts: str) -> float:
    if not ts:
        return 0.0
    try:
        # Z suffix → +00:00 (datetime.fromisoformat handles)
        from datetime import datetime
        s = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return 0.0


def _short_project(folder_name: str) -> str:
    """Map agtop-style mangled project dir back to a short readable name.

    `~/.claude/projects/D--Sinister-Sanctum-projects-sinister-term/`
       → `sinister-term`
    Strategy: take the trailing 1-2 dash-segments after the last `projects-`.
    """
    if not folder_name:
        return ""
    name = folder_name
    # the canonical structure is `<drive>--<top>...-projects-<key>...`
    if "-projects-" in name:
        tail = name.rsplit("-projects-", 1)[-1]
        # tail may have suffix like `-source` so prefer first chunk
        return tail.split("-source")[0]
    # fallback: last dash-segment
    return name.rsplit("-", 1)[-1]


def parse_jsonl_session(path: Path) -> RmuxSession:
    sess = RmuxSession(path=path)
    try:
        sess.file_size = path.stat().st_size
    except OSError as e:
        sess.parse_error = f"stat: {e}"
        return sess
    sess.session_id = path.stem
    sess.project_dir = _short_project(path.parent.name)
    try:
        # Read whole file. Sessions are usually small (<10 MB). We tail-only via
        # last-N lines if it's huge, but for now full-read for correctness.
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        sess.parse_error = f"read: {e}"
        return sess
    for line in text.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if not isinstance(rec, dict):
            continue
        rtype = rec.get("type")
        ts_str = rec.get("timestamp") or ""
        ts = _parse_iso(ts_str)
        if ts > 0:
            if sess.started_at == 0.0 or ts < sess.started_at:
                sess.started_at = ts
            if ts > sess.last_active:
                sess.last_active = ts
        # cwd + branch + cc version come on most rows
        if not sess.cwd and rec.get("cwd"):
            sess.cwd = rec.get("cwd") or ""
        if not sess.git_branch and rec.get("gitBranch"):
            sess.git_branch = rec.get("gitBranch") or ""
        if not sess.cc_version and rec.get("version"):
            sess.cc_version = rec.get("version") or ""
        # assistant turns drive token + tool counts
        if rtype == "assistant":
            msg = rec.get("message") or {}
            if isinstance(msg, dict):
                if not sess.raw_model:
                    sess.raw_model = msg.get("model") or ""
                    sess.model = _normalize_model(sess.raw_model)
                usage = msg.get("usage") or {}
                if isinstance(usage, dict):
                    in_tok = int(usage.get("input_tokens") or 0)
                    out_tok = int(usage.get("output_tokens") or 0)
                    cw_tok = int(usage.get("cache_creation_input_tokens") or 0)
                    cr_tok = int(usage.get("cache_read_input_tokens") or 0)
                    # 5m vs 1h split — agtop index.js:1514-1518
                    cw_5m = 0
                    cw_1h = 0
                    cc = usage.get("cache_creation") or {}
                    if isinstance(cc, dict):
                        cw_5m = int(cc.get("ephemeral_5m_input_tokens") or 0)
                        cw_1h = int(cc.get("ephemeral_1h_input_tokens") or 0)
                    # if cache_creation breakdown not present, default the
                    # combined cw_tok to the 1h bucket (worst-case spend)
                    if cw_5m == 0 and cw_1h == 0 and cw_tok > 0:
                        cw_1h = cw_tok
                    sess.input_tokens += in_tok
                    sess.output_tokens += out_tok
                    sess.cache_creation_tokens += cw_tok
                    sess.cache_write_5m_tokens += cw_5m
                    sess.cache_write_1h_tokens += cw_1h
                    sess.cache_read_tokens += cr_tok
                    # CTX% basis = input + cache_creation + cache_read of LAST turn
                    sess.last_ctx_tokens = in_tok + cw_tok + cr_tok
                sess.turn_count += 1
                # tool_use blocks
                content = msg.get("content") or []
                if isinstance(content, list):
                    for blk in content:
                        if isinstance(blk, dict) and blk.get("type") == "tool_use":
                            name = blk.get("name") or "?"
                            sess.tool_counts[name] = sess.tool_counts.get(name, 0) + 1
                            sess.last_tool = name
                            if ts > 0:
                                sess.last_tool_ts = ts
    return sess


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _default_claude_projects_root() -> Path:
    """`~/.claude/projects/` — same convention as agtop."""
    return Path.home() / ".claude" / "projects"


def discover_sessions(root: Path | None = None,
                      max_files: int = 200,
                      since_seconds: float | None = None) -> list[Path]:
    """Return JSONL session-file paths newest-first (by mtime).

    `max_files` caps the cost of a workstation with hundreds of stale sessions.
    `since_seconds` filters by mtime — useful for live mode (e.g. last 24h).
    """
    base = root or _default_claude_projects_root()
    if not base.is_dir():
        return []
    cutoff = (time.time() - since_seconds) if since_seconds else None
    out: list[tuple[float, Path]] = []
    try:
        for proj_dir in base.iterdir():
            if not proj_dir.is_dir():
                continue
            try:
                for jp in proj_dir.iterdir():
                    if jp.suffix != ".jsonl":
                        continue
                    try:
                        mt = jp.stat().st_mtime
                    except OSError:
                        continue
                    if cutoff is not None and mt < cutoff:
                        continue
                    out.append((mt, jp))
            except OSError:
                continue
    except OSError:
        return []
    out.sort(key=lambda t: t[0], reverse=True)
    return [p for _, p in out[:max_files]]


def _build_fleet_cwd_index() -> dict[str, tuple[str, float]]:
    """Return cwd→(slug, age_sec) map from _shared-memory/heartbeats/*.json.

    Multiple sessions may live in the same cwd; we keep the most recent
    heartbeat. Path normalization: lowercased + forward slashes so that
    Windows-style `D:\\foo\\bar` matches JSONL-style `D:/foo/bar` matches
    heartbeat `D:\\\\foo\\\\bar`.
    """
    sanctum = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")
    hb_dir = sanctum / "_shared-memory" / "heartbeats"
    out: dict[str, tuple[str, float]] = {}
    if not hb_dir.is_dir():
        return out
    try:
        files = list(hb_dir.iterdir())
    except OSError:
        return out
    for hb in files:
        if hb.suffix != ".json":
            continue
        try:
            data = json.loads(hb.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        cwd = data.get("cwd") or ""
        if not cwd:
            continue
        norm = _norm_cwd(cwd)
        slug = data.get("agent") or hb.stem
        try:
            age = max(0.0, time.time() - hb.stat().st_mtime)
        except OSError:
            age = 0.0
        # keep freshest
        existing = out.get(norm)
        if existing is None or age < existing[1]:
            out[norm] = (slug, age)
    return out


def _norm_cwd(p: str) -> str:
    """Normalize path-string for cross-reference comparisons."""
    if not p:
        return ""
    s = p.strip().lower().replace("\\", "/")
    # collapse trailing slash
    while s.endswith("/") and len(s) > 3:
        s = s[:-1]
    return s


def scan_sessions(root: Path | None = None,
                  max_files: int = 200,
                  since_seconds: float | None = None,
                  *, attach_fleet_slugs: bool = True) -> list[RmuxSession]:
    """Discover + parse JSONL files; return RmuxSession list newest-first.

    `attach_fleet_slugs=True` (default) cross-references each session's `cwd`
    against the sinister fleet heartbeats so every row can be tagged with
    the slug (`Sinister Kernel APK`, `Sinister OS`, etc.) that owns it.
    """
    paths = discover_sessions(root, max_files=max_files, since_seconds=since_seconds)
    out: list[RmuxSession] = []
    for p in paths:
        out.append(parse_jsonl_session(p))
    if attach_fleet_slugs and out:
        cwd_index = _build_fleet_cwd_index()
        # Secondary index: agent-slug → heartbeat age. Most peer heartbeats
        # don't carry a `cwd` field today, so we fall back to matching the
        # JSONL `project_dir` shorthand (the trailing `-projects-<key>` chunk)
        # against existing heartbeat filenames.
        slug_age_index = _build_fleet_slug_age_index()
        for s in out:
            # primary: cwd match (most reliable)
            norm = _norm_cwd(s.cwd)
            if norm and norm in cwd_index:
                slug, age = cwd_index[norm]
                s.fleet_slug = slug
                s.fleet_heartbeat_age_sec = age
                continue
            # secondary: project_dir → known fleet slug
            pd = (s.project_dir or "").lower()
            if not pd:
                continue
            # exact slug match
            if pd in slug_age_index:
                s.fleet_slug = pd
                s.fleet_heartbeat_age_sec = slug_age_index[pd]
                continue
            # fleet sometimes uses a shorter or longer slug than the JSONL
            # project_dir. Try both directions:
            #   project_dir=kernel-apk    + heartbeat=sinister-kernel-apk
            #   project_dir=sinister-kernel-apk + heartbeat=kernel-apk
            longer = f"sinister-{pd}"
            if longer in slug_age_index:
                s.fleet_slug = longer
                s.fleet_heartbeat_age_sec = slug_age_index[longer]
                continue
            if pd.startswith("sinister-"):
                shorter = pd[len("sinister-"):]
                if shorter in slug_age_index:
                    s.fleet_slug = shorter
                    s.fleet_heartbeat_age_sec = slug_age_index[shorter]
    return out


def _build_fleet_slug_age_index() -> dict[str, float]:
    """Return slug → heartbeat age_sec for every heartbeat file."""
    sanctum = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")
    hb_dir = sanctum / "_shared-memory" / "heartbeats"
    out: dict[str, float] = {}
    if not hb_dir.is_dir():
        return out
    try:
        for p in hb_dir.iterdir():
            if p.suffix != ".json":
                continue
            try:
                age = max(0.0, time.time() - p.stat().st_mtime)
            except OSError:
                continue
            out[p.stem.lower()] = age
    except OSError:
        return out
    return out


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def _fmt_age(seconds: float) -> str:
    s = max(0, int(seconds))
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m{s % 60:02d}s"
    if s < 86400:
        return f"{s // 3600}h{(s % 3600) // 60:02d}m"
    return f"{s // 86400}d{(s % 86400) // 3600:02d}h"


def _fmt_int(n: int) -> str:
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n / 1000:.1f}k"
    return f"{n / 1_000_000:.2f}M"


def _fmt_cost(usd: float) -> str:
    if usd < 0.01:
        return f"${usd:.4f}"
    if usd < 10:
        return f"${usd:.3f}"
    return f"${usd:.2f}"


def _fmt_pct(pct: float) -> str:
    return f"{pct:.0f}%"


def _truncate(s: str, n: int) -> str:
    if len(s) <= n:
        return s
    return s[: max(1, n - 1)] + "…"


SORT_KEYS = {
    "age":    lambda s: -s.last_active,         # newest first → smallest age
    "cost":   lambda s: -s.cost_usd,
    "ctx":    lambda s: -s.ctx_pct,
    "tokens": lambda s: -(s.input_tokens + s.output_tokens),
    "turns":  lambda s: -s.turn_count,
    "model":  lambda s: s.model,
    "project":lambda s: s.project_dir,
}


def sort_sessions(sessions: list[RmuxSession], key: str = "age") -> list[RmuxSession]:
    fn = SORT_KEYS.get(key.lower(), SORT_KEYS["age"])
    return sorted(sessions, key=fn)


def format_table(sessions: Iterable[RmuxSession],
                 limit: int = 30,
                 live_only: bool = False,
                 sort: str = "age",
                 show_path: bool = False) -> str:
    """Render the htop-style table as a single str (ANSI-free for portability)."""
    items = list(sessions)
    if live_only:
        items = [s for s in items if s.is_live]
    items = sort_sessions(items, sort)[:max(1, min(limit, 500))]
    if not items:
        return "(no sessions)"
    # Column widths — tuned for 120-col terminals. iter-80 adds `fleet`
    # column showing the sinister slug (if heartbeat is attached); when
    # no row carries a slug the column is auto-suppressed.
    has_fleet = any(s.fleet_slug for s in items)
    rows: list[list[str]] = []
    header = ["live", "project"]
    if has_fleet:
        header.append("fleet")
    header += ["model", "age", "ctx%", "in", "out", "cache-r", "cost",
               "turns", "top-tool"]
    if show_path:
        header.append("session")
    rows.append(header)
    for s in items:
        row = [
            "●" if s.is_live else "○",
            _truncate(s.project_dir or "?", 18),
        ]
        if has_fleet:
            row.append(_truncate(s.fleet_slug or "-", 22))
        row += [
            _truncate(s.model, 22),
            _fmt_age(s.age_seconds),
            _fmt_pct(s.ctx_pct),
            _fmt_int(s.input_tokens),
            _fmt_int(s.output_tokens),
            _fmt_int(s.cache_read_tokens),
            _fmt_cost(s.cost_usd),
            str(s.turn_count),
            _truncate(s.top_tool or "-", 14),
        ]
        if show_path:
            row.append(_truncate(s.session_id, 36))
        rows.append(row)
    # auto-fit each column to widest cell. Right-justify the numeric columns
    # by NAME (so insertion of `fleet` column doesn't break alignment).
    _RIGHT = {"age", "ctx%", "in", "out", "cache-r", "cost", "turns"}
    right_idxs = {i for i, name in enumerate(header) if name in _RIGHT}
    widths = [max(len(r[i]) for r in rows) for i in range(len(header))]
    out_lines: list[str] = []
    for ri, row in enumerate(rows):
        parts = []
        for i, cell in enumerate(row):
            if i in right_idxs:
                parts.append(cell.rjust(widths[i]))
            else:
                parts.append(cell.ljust(widths[i]))
        out_lines.append("  ".join(parts))
        if ri == 0:
            out_lines.append("  ".join("-" * widths[i] for i in range(len(header))))
    # footer summary
    live_count = sum(1 for s in items if s.is_live)
    total_cost = sum(s.cost_usd for s in items)
    total_in = sum(s.input_tokens for s in items)
    total_out = sum(s.output_tokens for s in items)
    out_lines.append("")
    out_lines.append(
        f"sessions: {len(items)}  live: {live_count}  "
        f"tokens-in: {_fmt_int(total_in)}  tokens-out: {_fmt_int(total_out)}  "
        f"spend: {_fmt_cost(total_cost)}"
    )
    return "\n".join(out_lines)


def format_session_detail(session: RmuxSession) -> str:
    """Full detail for one session — agtop's Enter-key drilldown equivalent."""
    p = _price_for(session.model)
    lines = [
        f"Session  {session.session_id}",
        f"Project  {session.project_dir}",
        f"Fleet    {session.fleet_slug or '(no matching heartbeat)'}"
        + (f"  (heartbeat age {_fmt_age(session.fleet_heartbeat_age_sec)})"
           if session.fleet_slug else ""),
        f"CWD      {session.cwd or '?'}",
        f"Branch   {session.git_branch or '?'}",
        f"CC ver   {session.cc_version or '?'}",
        f"Model    {session.raw_model or session.model}",
        f"Age      {_fmt_age(session.age_seconds)} (last active)",
        f"Turns    {session.turn_count}",
        f"Tokens   in={_fmt_int(session.input_tokens)}  "
        f"out={_fmt_int(session.output_tokens)}  "
        f"cache-w={_fmt_int(session.cache_creation_tokens)}  "
        f"cache-r={_fmt_int(session.cache_read_tokens)}",
        f"CTX%     {_fmt_pct(session.ctx_pct)}  (last-turn {_fmt_int(session.last_ctx_tokens)} / "
        f"{_fmt_int(_ctx_max_for(session.model, session.raw_model))})",
        f"Cost     {_fmt_cost(session.cost_usd)}   "
        f"(rates: in=${p['input']:.2f}/M out=${p['output']:.2f}/M "
        f"cw5m=${p['cache_write_5m']:.2f}/M cw1h=${p['cache_write_1h']:.2f}/M "
        f"cr=${p['cache_read']:.2f}/M)",
        f"File     {session.path}",
        f"Size     {_fmt_int(session.file_size)} bytes",
    ]
    if session.tool_counts:
        lines.append("Tools:")
        for name, n in sorted(session.tool_counts.items(), key=lambda kv: -kv[1])[:12]:
            lines.append(f"  {name:<22} {n}")
    if session.parse_error:
        lines.append(f"parse-error: {session.parse_error}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point — `python -m term.rmux ...`
# ---------------------------------------------------------------------------

# ANSI clear-screen + cursor home; works in mintty, Windows Terminal, and any
# VT-100 capable shell. cmd.exe before WT may need `colorama.init()` (we don't
# import it to keep zero deps).
_CLEAR = "\x1b[2J\x1b[H"

# Default refresh interval matches agtop (`-d 2` from agtop README).
_DEFAULT_WATCH_INTERVAL = 2.0


def _session_to_dict(s: RmuxSession) -> dict:
    """Serializable dict for --json. Stable schema for downstream scripts."""
    return {
        "session_id":          s.session_id,
        "path":                str(s.path),
        "project_dir":         s.project_dir,
        "model":               s.model,
        "raw_model":           s.raw_model,
        "cwd":                 s.cwd,
        "git_branch":          s.git_branch,
        "cc_version":          s.cc_version,
        "started_at":          s.started_at,
        "last_active":         s.last_active,
        "age_seconds":         s.age_seconds,
        "is_live":             s.is_live,
        "turn_count":          s.turn_count,
        "input_tokens":        s.input_tokens,
        "output_tokens":       s.output_tokens,
        "cache_creation_tokens": s.cache_creation_tokens,
        "cache_write_5m_tokens": s.cache_write_5m_tokens,
        "cache_write_1h_tokens": s.cache_write_1h_tokens,
        "cache_read_tokens":   s.cache_read_tokens,
        "last_ctx_tokens":     s.last_ctx_tokens,
        "ctx_pct":             s.ctx_pct,
        "cost_usd":            s.cost_usd,
        "tool_counts":         dict(s.tool_counts),
        "top_tool":            s.top_tool,
        "last_tool":           s.last_tool,
        "last_tool_ts":        s.last_tool_ts,
        "file_size":           s.file_size,
        "parse_error":         s.parse_error,
        "fleet_slug":          s.fleet_slug,
        "fleet_heartbeat_age_sec": s.fleet_heartbeat_age_sec,
    }


def render_snapshot(*, limit: int = 30, live_only: bool = False,
                    sort: str = "age", project: str = "",
                    since_hours: float = 168.0,
                    max_files: int = 200,
                    show_path: bool = False) -> str:
    """One-shot table render. Pure function for testability."""
    since_seconds = since_hours * 3600 if since_hours > 0 else None
    sessions = scan_sessions(max_files=max_files, since_seconds=since_seconds)
    if project:
        pf = project.lower()
        sessions = [s for s in sessions if pf in (s.project_dir or "").lower()]
    return format_table(sessions, limit=limit, live_only=live_only,
                        sort=sort, show_path=show_path)


def render_json(*, limit: int = 200, live_only: bool = False,
                sort: str = "age", project: str = "",
                since_hours: float = 168.0,
                max_files: int = 500) -> str:
    """Full dump as a JSON list of session dicts. Mirrors `agtop -j`."""
    since_seconds = since_hours * 3600 if since_hours > 0 else None
    sessions = scan_sessions(max_files=max_files, since_seconds=since_seconds)
    if project:
        pf = project.lower()
        sessions = [s for s in sessions if pf in (s.project_dir or "").lower()]
    if live_only:
        sessions = [s for s in sessions if s.is_live]
    sessions = sort_sessions(sessions, sort)[: max(1, min(limit, 5000))]
    payload = {
        "schema": "sinister.rmux.snapshot.v1",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_count": len(sessions),
        "total_cost_usd": round(sum(s.cost_usd for s in sessions), 4),
        "total_input_tokens": sum(s.input_tokens for s in sessions),
        "total_output_tokens": sum(s.output_tokens for s in sessions),
        "live_count": sum(1 for s in sessions if s.is_live),
        "sessions": [_session_to_dict(s) for s in sessions],
    }
    import json as _j
    return _j.dumps(payload, indent=2, sort_keys=False, default=str)


def render_detail(session_id: str, *, since_hours: float = 168.0,
                  max_files: int = 500) -> str:
    """Drilldown for one session id (exact or substring)."""
    since_seconds = since_hours * 3600 if since_hours > 0 else None
    sessions = scan_sessions(max_files=max_files, since_seconds=since_seconds)
    hit = next((s for s in sessions if s.session_id == session_id), None)
    if hit is None:
        cand = [s for s in sessions if session_id.lower() in s.session_id.lower()]
        if len(cand) == 1:
            hit = cand[0]
        elif len(cand) > 1:
            return (f"ambiguous: {len(cand)} sessions match '{session_id}'. "
                    f"Try a longer prefix: "
                    + ", ".join(c.session_id[:8] for c in cand[:8]))
    if hit is None:
        return f"no session matches '{session_id}'."
    return format_session_detail(hit)


def watch_loop(*, interval: float = _DEFAULT_WATCH_INTERVAL,
               limit: int = 30, live_only: bool = False,
               sort: str = "age", project: str = "",
               since_hours: float = 168.0,
               max_files: int = 200,
               iterations: int | None = None,
               clear: bool = True,
               sleep_fn=time.sleep,
               write_fn=None,
               flush_fn=None) -> int:
    """Live refresh loop. Returns the iteration count actually run.

    `iterations=None` means loop forever (Ctrl+C exits).
    `iterations=N` runs exactly N renders then returns (for tests).
    `sleep_fn` / `write_fn` / `flush_fn` are injectable for testing.
    """
    import sys as _sys
    write = write_fn or _sys.stdout.write
    flush = flush_fn or _sys.stdout.flush
    n_done = 0
    try:
        while True:
            snap = render_snapshot(
                limit=limit, live_only=live_only, sort=sort,
                project=project, since_hours=since_hours, max_files=max_files,
            )
            if clear:
                write(_CLEAR)
            write(snap)
            footer = (
                f"\n\nrmux watch — refresh every {interval:.1f}s · "
                f"sort={sort} live={live_only} limit={limit} · "
                "Ctrl+C to exit\n"
            )
            write(footer)
            flush()
            n_done += 1
            if iterations is not None and n_done >= iterations:
                return n_done
            sleep_fn(interval)
    except KeyboardInterrupt:
        # graceful exit; carriage return so any trailing ^C lives on its own line
        try:
            write("\n")
            flush()
        except Exception:
            pass
        return n_done


def build_argparser():
    import argparse
    p = argparse.ArgumentParser(
        prog="python -m term.rmux",
        description="Sinister rmux — htop-style fleet monitor for Claude Code sessions "
                    "(port of agtop, https://github.com/ldegio/agtop, GPL-2.0). "
                    "Reads ~/.claude/projects/<proj>/*.jsonl, scores each session, renders a table.",
    )
    p.add_argument("--watch", "-w", nargs="?", const=_DEFAULT_WATCH_INTERVAL,
                   type=float, default=None,
                   help=f"Live refresh every N seconds (default {_DEFAULT_WATCH_INTERVAL}s). "
                        "Ctrl+C exits.")
    p.add_argument("--json", "-j", action="store_true",
                   help="Dump full session data as JSON and exit (no table).")
    p.add_argument("--limit", "-n", type=int, default=30,
                   help="Max rows to render (default 30; capped 1..500).")
    p.add_argument("--live", "-L", action="store_true",
                   help="Only sessions active in the last 5 minutes.")
    p.add_argument("--sort", "-s", default="age",
                   choices=sorted(SORT_KEYS.keys()),
                   help="Sort key (default: age).")
    p.add_argument("--project", "-p", default="",
                   help="Filter project_dir by substring (case-insensitive).")
    p.add_argument("--detail", "-D", default="",
                   help="Drilldown view for one session id (exact or substring).")
    p.add_argument("--since-hours", type=float, default=168.0,
                   help="Skip sessions whose JSONL mtime is older than N hours (default 168 = 7d).")
    p.add_argument("--max-files", type=int, default=200,
                   help="Cap on number of JSONL files scanned (default 200).")
    p.add_argument("--show-path", action="store_true",
                   help="Add session-id column to the table.")
    p.add_argument("--no-clear", action="store_true",
                   help="In --watch mode, don't issue the clear-screen ANSI (useful for logs).")
    return p


def main(argv: list[str] | None = None) -> int:
    import sys as _sys
    if argv is None:
        argv = list(_sys.argv[1:])
    else:
        argv = list(argv)
    # Verb-first dispatch: `python -m term.rmux <verb> [args]` routes to
    # term.rmux_verbs (iter-79: spawn / stop / kill / focus / attach / logs /
    # projects / help / ls / watch / json / detail). If the first arg is a
    # non-flag word matching a known verb we hand off the whole tail;
    # otherwise we fall through to the legacy --flag argparse path so back-
    # compat callers (--watch / --json / --detail) keep working.
    if argv and not argv[0].startswith("-"):
        try:
            from term import rmux_verbs as _verbs
        except Exception as e:
            print(f"verb dispatcher unavailable: {e}")
            return 2
        if _verbs.is_verb(argv[0]):
            result = _verbs.dispatch_verb(argv[0], argv[1:])
            if result.text:
                print(result.text)
            return 0 if result.ok else 1
        # unknown first-arg word — let argparse error helpfully
    parser = build_argparser()
    args = parser.parse_args(argv)
    # exclusive: detail wins, then json, then watch, then snapshot
    if args.detail:
        out = render_detail(args.detail,
                            since_hours=args.since_hours,
                            max_files=max(args.max_files, 500))
        print(out)
        return 0
    if args.json:
        out = render_json(limit=args.limit, live_only=args.live, sort=args.sort,
                          project=args.project, since_hours=args.since_hours,
                          max_files=max(args.max_files, 500))
        print(out)
        return 0
    if args.watch is not None:
        watch_loop(interval=max(0.25, args.watch),
                   limit=args.limit, live_only=args.live, sort=args.sort,
                   project=args.project, since_hours=args.since_hours,
                   max_files=args.max_files,
                   clear=not args.no_clear)
        return 0
    # default: one-shot snapshot
    out = render_snapshot(limit=args.limit, live_only=args.live, sort=args.sort,
                          project=args.project, since_hours=args.since_hours,
                          max_files=args.max_files, show_path=args.show_path)
    print(out)
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys as _sys
    raise SystemExit(main(_sys.argv[1:]))
