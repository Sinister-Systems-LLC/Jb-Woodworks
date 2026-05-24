# gotchas — observed-and-fixed problems

> **Author:** RKOJ-ELENO :: 2026-05-24
> Append at top; most-recent first. Format: `### <symptom> (<date>)` + Cause + Fix + Test that catches a regression.

---

### Rate-limit blocks first send when monotonic clock starts near zero (2026-05-24)

**Symptom:** in pytest with `time.monotonic` monkeypatched to return 0.0, `send_worker.send.send(...)` returned `{"status": "blocked", "reason": "rate_limit"}` on the FIRST send.

**Cause:** `_last_send.get(recipient, 0)` defaulted to `0` for never-sent recipients. With monkeypatched `monotonic = 0.0`, the rate-limit check `0.0 - 0 < 5.0` evaluated `True` → block. In production this never fires because `time.monotonic()` returns seconds-since-process-start (always >> 5.0 by the first send), but it's a latent fragility.

**Fix:** default to `float("-inf")` instead of `0` — `time.monotonic() - (-inf) == +inf`, always > RATE_GAP_SEC. Committed at `source/send_worker/send.py:60`.

**Test:** `tests/test_send.py::test_rate_limit_clears_after_window` — monkeypatches monotonic to `[0.0, 4.5, 6.0]` and asserts r1=ok / r2=blocked / r3=ok.

---

### `from send_worker import send` re-export shadows submodule (2026-05-24)

**Symptom:** `tests/test_send.py` calling `monkeypatch.setattr(send_module, "POLICY_PATH", policy)` raised `AttributeError: <function send> has no attribute 'POLICY_PATH'`.

**Cause:** `send_worker/__init__.py` had `from .send import send` which makes `send_worker.send` resolve to the FUNCTION, not the submodule. `from send_worker import send` returns the function. The submodule was still importable via `from send_worker.send import send` (Python resolves the submodule attribute lookup before the re-export), but `import send_worker.send as ...` was ambiguous.

**Fix:** dropped the re-export from `__init__.py`. Callers explicitly use `from send_worker.send import send` for the function or `from send_worker import send as send_module` for the submodule. Same pattern enforced in `recv_worker/__init__.py`.

**Test:** all `tests/test_send.py` cases — they monkeypatch `send_module.POLICY_PATH` and verify guard behavior.

---

### `python bridge_daemon/bridge.py` can't import recv_worker (2026-05-24)

**Symptom:** running `python bridge_daemon/bridge.py` from `source/` raised `ModuleNotFoundError: No module named 'recv_worker'`.

**Cause:** invoking as a script puts `bridge_daemon/` on sys.path (not `source/`). Sibling packages aren't visible.

**Fix:** invoke as a module: `python -m bridge_daemon.bridge`. Updated `source/README.md` and `pyproject.toml` `[project.scripts]` to reflect.

**Test:** end-of-I2 smoke run uses `python -m bridge_daemon.bridge --port 8731 --chatdb fixtures/canned-chat.db` and verifies /status + /threads + /threads/{id}/messages + /send all return 200.

---

### Pre-farm template — farm-specific gotchas

The next rows append when EVE meets the real farm. Expected categories (populated on P1+):
- Full Disk Access prompt for `sshd-keygen-wrapper` (macOS Ventura+)
- Automation permission prompt for the SSH user-shell → Messages.app
- `attributedBody`-only messages (macOS 14+ composer no longer writes `text`)
- `ERR -1728` on buddy-not-found (first send to brand-new recipient)
- `osascript` exit code 0 with `ERR` stdout (Messages.app errors are non-fatal)
- chat.db schema delta on a specific macOS release
- Fswatch missing on minimal farm install (`brew install fswatch`)
- SSH config kex/cipher mismatch with newer macOS defaults
