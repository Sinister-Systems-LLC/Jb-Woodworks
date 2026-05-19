# .github/ — GitHub-side config

## workflows/

- `bots-smoke.yml` — runs on PR to `main` and push to `bots/**`. Syntax-checks every bot's `server.py` + smoke-tests `_shared/codec.py` and `_shared/crypto.py` (lossless roundtrip + lock/unlock).

## Adding new workflows

Each product repo (Snap EMU / TikTok EMU / Control Center / Kernel APK) gets
its own CI via `git-toolkit.ps1 ci-bootstrap <path>`, which drops a
language-aware skeleton at `.github/workflows/sinister-ci.yml` inside that
project. Sanctum's CI here is for the BOT FLEET specifically.

## Issue + PR templates (future)

When Sanctum goes public, drop in `.github/ISSUE_TEMPLATE/*.yml` + `.github/pull_request_template.md` so contributors get guided. Not done yet — operator decides format.

## TL;DR

- **How we won:** One CI workflow validates the bot fleet on every change.
- **What you need to do:** Per-product-repo CI lives inside each repo (use `git-toolkit ci-bootstrap`); Sanctum CI stays scoped to bots/.
