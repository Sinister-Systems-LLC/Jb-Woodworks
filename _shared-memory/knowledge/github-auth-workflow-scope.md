> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: gh CLI needs `workflow` scope to push .github/workflows changes

**Slug:** github-auth-workflow-scope
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** workaround
**Tags:** github, gh, auth, oauth-scope, push, ci

## Problem

Pushing a branch that adds or modifies files under `.github/workflows/` fails with:

```
! [remote rejected] master -> master (refusing to allow an OAuth App to create or update workflow `.github/workflows/<name>.yml` without `workflow` scope)
error: failed to push some refs to 'https://github.com/<org>/<repo>.git'
```

Even if the user is authenticated to gh, the OAuth token may have been minted without the `workflow` scope (default scopes don't include it). The CI files are silently dropped server-side, or the push is fully rejected.

## Why it happens

GitHub's API requires the `workflow` OAuth scope explicitly for any operation that touches `.github/workflows/*.yml`. The default `gh auth login` flow grants `repo`, `read:org`, `gist` but NOT `workflow`. Older tokens (minted before this requirement) may grandfather in, but new ones won't.

Reference: https://docs.github.com/en/rest/overview/permissions-required-for-github-apps#workflow

## Fix or workaround

```bash
gh auth refresh -h github.com -s workflow
```

This expands the existing token's scope set (does NOT rotate the token — same SHA-256 hash before/after, just more scopes attached). Tested 2026-05-19 on operator's machine; push of .github/workflows/bots-smoke.yml succeeded immediately after.

Alternative if refresh fails:
```bash
gh auth logout -h github.com
gh auth login -h github.com -s "repo,workflow,read:org"
```

The classic-PAT alternative (manual token from github.com/settings/tokens) also works — give it `repo` + `workflow`, paste into `gh auth login --with-token`.

## Sanctum-specific note

The Sanctum repo's `.github/workflows/bots-smoke.yml` triggers this on the first push to a fresh remote. Master agents pushing on operator's behalf must run `gh auth refresh -s workflow` once per machine. The fix doesn't need re-running — token retains the scope across `gh auth refresh` calls.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 02:00 by Sinister Sanctum
First documented. Operator hit this when pushing the Sanctum repo's initial commit including the `bots-smoke.yml` CI workflow. `gh auth refresh -s workflow` resolved cleanly; no token rotation needed.

## Related topics

- [github-classic-pat-vs-fine-grained](./github-classic-pat-vs-fine-grained.md) (not yet written)
