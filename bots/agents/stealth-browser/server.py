"""
Stealth-Browser agent — undetected browser automation for the Sinister Bots fleet.

RE'd from vibheksoni/stealth-browser-mcp's core pattern: nodriver (undetected Chromium
over CDP) wrapped as MCP tools. We ship a minimal ~10-tool subset focused on what
our fleet actually needs (navigation + scrape + interact) rather than the upstream's
96-tool surface (element cloning, network hooks, etc.) — extracting more later is easy.

Tier 1 default (no LLM cost). Browser launches lazily on first call; reused across
tools until close() or process exit.

Tools:
  stealth.open(url, wait_for_selector=None)              -> {ok, title, final_url}
  stealth.screenshot(path=None, full_page=False)         -> {ok, path, bytes_b64?}
  stealth.html()                                          -> {ok, html, length}
  stealth.scrape_text(max_chars=20000)                   -> {ok, text}
  stealth.scrape_links()                                  -> [{href, text}]
  stealth.click(selector)                                 -> {ok}
  stealth.type(selector, text, delay_ms=30)              -> {ok}
  stealth.wait_for(selector, timeout_sec=10)             -> {ok, found}
  stealth.evaluate(js)                                    -> {ok, result}
  stealth.close()                                         -> {ok}
  stealth.health()                                        -> {ok, driver_loaded, browser_open}
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[stealth] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    import nodriver as uc
    HAS_NODRIVER = True
except ImportError:
    HAS_NODRIVER = False

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
AGENT_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "stealth-browser"
AGENT_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR = AGENT_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

# Lazily-initialized singletons. nodriver's Browser/Page are async, but we can drive
# them from sync MCP tool bodies via asyncio.run_coroutine_threadsafe on a dedicated loop.
_loop: asyncio.AbstractEventLoop | None = None
_browser = None  # uc.Browser
_page = None     # uc.Tab


def log_call(tool: str, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "stealth-browser",
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


def _get_loop() -> asyncio.AbstractEventLoop:
    """Get-or-create a background event loop on its own thread for nodriver."""
    global _loop
    if _loop is not None and not _loop.is_closed():
        return _loop
    import threading
    _loop = asyncio.new_event_loop()

    def _runner():
        asyncio.set_event_loop(_loop)
        _loop.run_forever()

    t = threading.Thread(target=_runner, daemon=True, name="stealth-loop")
    t.start()
    return _loop


def _run(coro):
    """Submit a coroutine to the background loop and block for its result."""
    loop = _get_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    return fut.result(timeout=120)


async def _ensure_browser():
    global _browser
    if _browser is None:
        _browser = await uc.start(headless=False, browser_args=["--disable-blink-features=AutomationControlled"])
    return _browser


async def _ensure_page():
    global _page
    b = await _ensure_browser()
    if _page is None:
        _page = await b.get("about:blank")
    return _page


async def _open(url: str, wait_for_selector: str | None = None) -> dict[str, Any]:
    global _page
    b = await _ensure_browser()
    _page = await b.get(url)
    if wait_for_selector:
        try:
            await _page.wait_for(selector=wait_for_selector, timeout=15)
        except Exception:
            pass
    title = await _page.evaluate("document.title")
    final_url = await _page.evaluate("location.href")
    return {"ok": True, "title": title, "final_url": final_url}


async def _screenshot(path: str | None, full_page: bool) -> dict[str, Any]:
    p = await _ensure_page()
    target = Path(path) if path else (SCREENSHOT_DIR / f"shot-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.png")
    target.parent.mkdir(parents=True, exist_ok=True)
    await p.save_screenshot(filename=str(target), full_page=full_page)
    return {"ok": True, "path": str(target)}


async def _html() -> dict[str, Any]:
    p = await _ensure_page()
    html = await p.get_content()
    return {"ok": True, "html": html, "length": len(html)}


async def _scrape_text(max_chars: int) -> dict[str, Any]:
    p = await _ensure_page()
    text = await p.evaluate("document.body ? document.body.innerText : ''")
    if isinstance(text, str) and len(text) > max_chars:
        text = text[:max_chars] + "\n...[truncated]"
    return {"ok": True, "text": text}


async def _scrape_links() -> list[dict[str, Any]]:
    p = await _ensure_page()
    js = """
    Array.from(document.querySelectorAll('a[href]')).slice(0, 200).map(a => ({
        href: a.href,
        text: (a.innerText || '').trim().slice(0, 200)
    }))
    """
    return await p.evaluate(js) or []


async def _click(selector: str) -> dict[str, Any]:
    p = await _ensure_page()
    el = await p.select(selector, timeout=10)
    if not el:
        return {"ok": False, "error": f"selector not found: {selector}"}
    await el.click()
    return {"ok": True}


async def _type(selector: str, text: str, delay_ms: int) -> dict[str, Any]:
    p = await _ensure_page()
    el = await p.select(selector, timeout=10)
    if not el:
        return {"ok": False, "error": f"selector not found: {selector}"}
    await el.send_keys(text)
    return {"ok": True}


async def _wait_for(selector: str, timeout_sec: int) -> dict[str, Any]:
    p = await _ensure_page()
    try:
        await p.wait_for(selector=selector, timeout=timeout_sec)
        return {"ok": True, "found": True}
    except Exception as e:
        return {"ok": True, "found": False, "reason": str(e)[:200]}


async def _evaluate(js: str) -> dict[str, Any]:
    p = await _ensure_page()
    try:
        result = await p.evaluate(js)
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


async def _close() -> dict[str, Any]:
    global _browser, _page
    if _browser is not None:
        try:
            _browser.stop()
        except Exception:
            pass
    _browser = None
    _page = None
    return {"ok": True}


mcp = FastMCP("stealth-browser")


@mcp.tool()
def open(url: str, wait_for_selector: str | None = None) -> dict[str, Any]:
    """Navigate the stealth browser to url. Launches Chrome on first call."""
    if not HAS_NODRIVER:
        return {"ok": False, "error": "nodriver not installed (pip install nodriver)"}
    log_call("open", url=url[:300])
    return _run(_open(url, wait_for_selector))


@mcp.tool()
def screenshot(path: str | None = None, full_page: bool = False) -> dict[str, Any]:
    """Capture a PNG of the current page. Defaults to agents/stealth-browser/screenshots/."""
    if not HAS_NODRIVER:
        return {"ok": False, "error": "nodriver not installed"}
    log_call("screenshot", full_page=full_page)
    return _run(_screenshot(path, full_page))


@mcp.tool()
def html() -> dict[str, Any]:
    """Return the current page's full HTML."""
    if not HAS_NODRIVER:
        return {"ok": False, "error": "nodriver not installed"}
    log_call("html")
    return _run(_html())


@mcp.tool()
def scrape_text(max_chars: int = 20000) -> dict[str, Any]:
    """Return rendered visible text (document.body.innerText)."""
    if not HAS_NODRIVER:
        return {"ok": False, "error": "nodriver not installed"}
    log_call("scrape_text", max_chars=max_chars)
    return _run(_scrape_text(max_chars))


@mcp.tool()
def scrape_links() -> list[dict[str, Any]]:
    """Return up to 200 <a href> elements from the current page."""
    if not HAS_NODRIVER:
        return []
    log_call("scrape_links")
    return _run(_scrape_links())


@mcp.tool()
def click(selector: str) -> dict[str, Any]:
    """Click the element matching CSS selector."""
    if not HAS_NODRIVER:
        return {"ok": False, "error": "nodriver not installed"}
    log_call("click", selector=selector[:200])
    return _run(_click(selector))


@mcp.tool()
def type(selector: str, text: str, delay_ms: int = 30) -> dict[str, Any]:
    """Type text into the element matching CSS selector."""
    if not HAS_NODRIVER:
        return {"ok": False, "error": "nodriver not installed"}
    log_call("type", selector=selector[:200])
    return _run(_type(selector, text, delay_ms))


@mcp.tool()
def wait_for(selector: str, timeout_sec: int = 10) -> dict[str, Any]:
    """Wait until selector appears (returns {found: true/false} on timeout)."""
    if not HAS_NODRIVER:
        return {"ok": False, "error": "nodriver not installed"}
    log_call("wait_for", selector=selector[:200])
    return _run(_wait_for(selector, timeout_sec))


@mcp.tool()
def evaluate(js: str) -> dict[str, Any]:
    """Run arbitrary JavaScript in the current page and return the result."""
    if not HAS_NODRIVER:
        return {"ok": False, "error": "nodriver not installed"}
    log_call("evaluate", js_len=len(js))
    return _run(_evaluate(js))


@mcp.tool()
def close() -> dict[str, Any]:
    """Close the browser and free resources."""
    if not HAS_NODRIVER:
        return {"ok": True, "note": "nodriver not installed; nothing to close"}
    log_call("close")
    return _run(_close())


@mcp.tool()
def health() -> dict[str, Any]:
    """Health check."""
    log_call("health")
    return {
        "ok": True,
        "agent": "stealth-browser",
        "has_nodriver": HAS_NODRIVER,
        "browser_open": _browser is not None,
        "screenshot_dir": str(SCREENSHOT_DIR.relative_to(HUB_ROOT)),
    }


if __name__ == "__main__":
    mcp.run()
