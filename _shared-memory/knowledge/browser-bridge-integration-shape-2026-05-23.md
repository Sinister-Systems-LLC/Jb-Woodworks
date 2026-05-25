<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 180
-->
# Browser-bridge integration shape — wrap not clone (firefox-agent-bridge v0.9.9 audit)

> **Status:** doctrine, audit, proposed
> **Origin:** jcode-feature-matrix.md row 26 says NOT clone-and-run; operator directive 2026-05-23 "*all jcode features etc and i want our own terminal system*" implies parity, not duplication. Read-only audit of `C:\Users\Zonia\Desktop\Github Research\firefox-agent-bridge-0.9.9\` (v1.0.0 in `Cargo.toml`, dir name says 0.9.9 — upstream pre-release).
> **Upstream:** `https://github.com/1jehuang/firefox-agent-bridge` — MIT licensed Rust + Firefox WebExtension.

## What firefox-agent-bridge actually is

Three-layer architecture:

```
┌─────────────┐  WebSocket  ┌──────────────────┐  Native Messaging  ┌─────────────────┐
│   Agent     │◄───────────►│   Rust Host      │◄──────────────────►│ Firefox Ext     │
│ (any LLM)   │ ws://:8766  │ host-windows-    │   stdin/stdout JSON│  (signed XPI)   │
└─────────────┘             │ x64.exe (830KB)  │                    └─────────────────┘
                            └──────────────────┘
```

Three binaries / artifacts:
1. **`browser-windows-x64.exe`** (1.2 MB) — Rust CLI client that connects to `ws://127.0.0.1:8766` and sends JSON commands. Convenience wrapper; the WebSocket API is the actual interface.
2. **`host-windows-x64.exe`** (830 KB) — Rust native-messaging host. Launched by Firefox via `HKCU\Software\Mozilla\NativeMessagingHosts\firefox_agent_bridge`. Bridges Firefox extension's stdin/stdout to the WebSocket server.
3. **`browser-agent-bridge-X.X.X.xpi`** — signed Firefox extension. Required because browsers only allow JS extensions (no native-WASM path for Firefox WebExtensions).

Wire protocol: `{"action": "<name>", "params": {<...>}}` over WebSocket. ~25 actions covering session/tab management, navigation, click/type/fillForm, scroll, screenshot, evaluate, fileupload/drop, recorder, session-record/replay.

Performance: 12ms per command (88% faster than the Node.js client). Per-command timing dominated by Firefox roundtrip (~150ms for navigate, ~3ms for ping).

Persistent `browser session` mode uses Unix-domain sockets — disabled on Windows. Direct one-shot commands + the native messaging host DO compile and run on Windows.

## What "NOT clone-and-run" means

The matrix row 26 instruction blocks three patterns:
1. **Don't copy the Rust source** into `projects/sinister-browser/source/` and call it ours. License is MIT; ours is AGPL-3.0-or-later. A wholesale clone bakes a license-reconciliation problem into the tree, and the upstream author actively maintains the repo (we'd diverge).
2. **Don't ship the upstream XPI** signed under their author identity. Either the operator installs the XPI themselves (preferred — keeps the trust boundary clear) or we maintain our own extension fork (defer indefinitely; no operator demand).
3. **Don't fork the Cargo workspace** into our build matrix. Adds ~2 GB of Rust toolchain dependency (operator-gated install) for a feature that the upstream binary already provides.

## What we DO build (the Sinister wrapper shape)

A Python wrapper at `tools/sinister-browser/` that:

### Layer A — connectivity probe (`sinister_browser/probe.py`)

```python
def is_bridge_up() -> tuple[bool, str | None]:
    """Try to connect to ws://127.0.0.1:8766; return (alive, version_str)."""
    # Send {"action": "ping"} → expect {"pong": true, ...}.
    # Use `websocket-client` (single dep, MIT) — NOT clone of upstream's tokio stack.
```

Reports whether the operator has installed the upstream bridge (yes/no/wrong-version). Exit code surface for `sinister-cli`:
- `0` = bridge alive
- `2` = bridge not installed (suggests install path)
- `3` = bridge installed but unreachable (Firefox closed, or wrong port)

### Layer B — high-level action surface (`sinister_browser/api.py`)

Thin pythonic wrappers around the WebSocket actions. Same names, kwargs-driven:

```python
class Browser:
    def __init__(self, ws_url: str = "ws://127.0.0.1:8766"): ...
    def ping(self) -> dict: ...
    def navigate(self, url: str, wait: bool = True, new_tab: bool = False) -> dict: ...
    def get_content(self, fmt: str = "annotated") -> dict: ...
    def click(self, *, selector: str | None = None, text: str | None = None,
              x: int | None = None, y: int | None = None) -> dict: ...
    def type(self, text: str, *, selector: str | None = None,
             submit: bool = False, clear: bool = False) -> dict: ...
    def fill_form(self, fields: list[dict]) -> dict: ...
    def screenshot(self, filename: str | None = None) -> dict: ...
    def evaluate(self, script: str, page_world: bool = False) -> dict: ...
    # ...
```

### Layer C — Forge / Term slash surface (`forge/commands.py` + `term/...`)

Slash commands that delegate to the wrapper. **No source dependency on the wrapper** — Forge/Term call out via subprocess or import-by-name so the wrapper is hot-swappable:

- `/browser ping` — Layer A probe
- `/browser nav <url>` — Layer B navigate
- `/browser click <selector>` / `/browser type <text>` — Layer B click/type
- `/browser screenshot [path]` — Layer B screenshot, persisted to `_shared-memory/forge-memory/screenshots/`
- `/browser evaluate <script>` — Layer B evaluate (operator-gated; runs JS in page world)

### Layer D — SKILL.md mirror (`skills/sinister-browser/SKILL.md`)

Frontmatter-compatible skill manifest. Mirrors the upstream's SKILL.md content (factual API description, not a creative work — fair use under MIT). Skill name `sinister-browser` (not `firefox-browser`) so it doesn't collide with the operator's installed upstream skill if both are present.

## What stays operator-gated

- **Installation of the upstream XPI + binaries.** Operator runs `browser setup claude` (or our skill's recipe) once. Doctrine: NEVER auto-install upstream artifacts on operator's machine without explicit sign-off.
- **The `HKCU\...\NativeMessagingHosts\firefox_agent_bridge` registry entry.** Operator-owned per canonical-11 (registry writes are R3+ reversibility). Our wrapper documents the value the operator must drop in — does not write it.
- **`FAB_AUTOLOGIN_REQUIRE_FINGERPRINT=true`** — fingerprint-required-for-autologin env. Operator decides whether they want the credential-vault flow active.

## Composability with our stack

| Sinister surface | Hookup |
|---|---|
| `tools/sinister-login/` | `evaluate` action can fill credentials at page-render time, gated by `FAB_AUTOLOGIN_REQUIRE_FINGERPRINT` |
| `tools/sinister-usage/` | Layer A probe counts as a "configured but inactive" provider — listed in `sinister usage matrix` |
| `forge/panes/agent_pane.py` | `/browser screenshot` writes to `_shared-memory/forge-memory/screenshots/`; future panel renders a thumbnail strip |
| `projects/rkoj/source/sinister_rkoj_qt/api_server.py` | optional `/api/browser/screenshot` endpoint mirroring `/api/diagrams` shape — read-only view of the screenshots dir |
| `_shared-memory/knowledge/jcode-feature-matrix.md` row 26 | flips 🚧 doc → ✅ shipped once Layer A+B+C land |
| Term `/jcode-browser` slash | aliases to `/browser` for jcode-pattern compatibility |

## Why this is `R0` doctrine + `R1` implementation

- The doc itself is `R0` — no source changes, no installs, no registry writes. Just a brain entry that says "if you ever wire browser-bridge, here's the shape".
- The Layer A probe is `R1` — single Python module, `pip install -e`, easy revert.
- Layer B/C/D get to `R1` over multiple commits.
- The upstream binaries + XPI install is operator-gated (`R3` if registry edit needed).

## Anti-patterns to never repeat

1. **Clone the Rust source into our tree** — license + maintenance + toolchain cost. Wrap the running process instead.
2. **Auto-install the XPI on operator's profile** — trust boundary violation; operator owns the browser-extension surface.
3. **Hard-code the `:8766` port** in three places — keep it in one config knob (`SINISTER_BROWSER_WS_URL` env, default `ws://127.0.0.1:8766`), and re-read on each call.
4. **Block agent turns on `get_content` for slow pages** — wrap with `waitFor` + bounded timeout per Forge's UX rule (no hang >5s without status).
5. **Embed credentials in `evaluate` scripts** — go via `tools/sinister-login` instead; never type a secret into the WebSocket payload directly.

## Implementation status

- [x] Audit doc shipped (this entry).
- [ ] `tools/sinister-browser/probe.py` Layer A — deferred until operator asks.
- [ ] `tools/sinister-browser/api.py` Layer B — deferred.
- [ ] Forge `/browser` slash — deferred.
- [ ] `skills/sinister-browser/SKILL.md` mirror — deferred.
- [ ] Matrix row 26 flip 🚧 doc → ✅ shipped — pending Layer A+B+C+D landing.

## Cross-references

- `_shared-memory/knowledge/jcode-feature-matrix.md` row 26 (capability + owner)
- `_shared-memory/knowledge/agent-browser-bridge-pattern.md` (the prior doctrine entry; this one is the v0.9.9 empirical audit)
- `tools/sinister-login/` (credential surface)
- `tools/sinister-usage/` (provider matrix)
- `projects/sinister-forge/source/PLAN.md` (Forge PH15 — browser as tool)
- `_shared-memory/knowledge/sanctioned-bypasses-doctrine-2026-05-21.md` (registry edits are operator-gated)

## Tags (for INDEX.md)

doctrine, audit, proposed, browser-bridge, firefox-agent-bridge, websocket-127-8766, native-messaging-host, rust-not-cloned, mit-vs-agpl, wrapper-not-fork, sinister-browser-wrapper, layer-a-probe, layer-b-api, layer-c-slash, layer-d-skill, operator-gated-install, hkcu-native-messaging-hosts, fab-autologin, jcode-feature-matrix-row-26, 2026-05-23
