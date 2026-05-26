# Sinister Jokester — Vault Schema

> **Author:** RKOJ-ELENO :: 2026-05-26

Human-readable companion to `db/schema.sql`. The DB is rebuildable from filesystem; .md files are the durable truth.

## Tables

### intake_items

| column                | type     | notes                                                                  |
|-----------------------|----------|------------------------------------------------------------------------|
| id                    | TEXT PK  | URL-safe slug (e.g. `gh-charmbracelet-glow-a1b2c3`)                    |
| source_url            | TEXT     | Canonical URL the operator gave us                                     |
| source_type           | TEXT     | `github` \| `ig_audio` \| `direct_input` \| `telegram`                 |
| intake_ts             | TEXT     | ISO-8601 UTC                                                           |
| status                | TEXT     | `pending` \| `analyzing` \| `decided`                                  |
| verdict               | TEXT     | `ADOPT` \| `WATCH` \| `REJECT` \| NULL (until decided)                 |
| decision_md_path      | TEXT     | Relative to repo root, e.g. `vault/decisions/adopt/gh-glow.md`         |
| fleet_overlap_score   | REAL     | 0.0–1.0; higher = more overlap with existing fleet assets              |
| fleet_overlap_assets  | TEXT     | JSON array of fleet paths that overlap                                 |
| tags                  | TEXT     | Comma-separated (e.g. `cli,markdown,tui`)                              |
| title                 | TEXT     | Repo title / video title / etc.                                        |
| short_summary         | TEXT     | One-line description                                                   |
| raw_metadata_json     | TEXT     | Full metadata blob (stars, lang, license, last_commit, etc.)           |
| reviewed_by           | TEXT     | Slug of the agent that wrote the verdict                               |
| decided_ts            | TEXT     | ISO-8601 UTC of verdict                                                |

### intake_log

Append-only event log so we can reconstruct the path of every candidate.

| column      | type    | notes                                              |
|-------------|---------|----------------------------------------------------|
| id          | INTEGER | autoincrement                                      |
| item_id     | TEXT    | FK → intake_items.id                               |
| ts_utc      | TEXT    | ISO-8601                                           |
| event       | TEXT    | `intaken` \| `analyzed` \| `decided` \| `noted`    |
| detail      | TEXT    | Free-form (e.g. exit code, file path, error msg)   |

## Filesystem layout

- Raw artifacts: `vault/intake/<id>/` (clone dir, audio file, transcript).
- Decision .md: `vault/decisions/<verdict_lowercase>/<id>.md`.
- DB: `vault/db/intake.sqlite` (rebuildable via `python jokester_cli.py reindex`).
- Auto-summary: `vault/INDEX.md` (regenerated each time `recall` or `reindex` runs).

## Conventions

- `id` is computed once at intake and never changes.
- `verdict` writes are atomic: the .md is written first, then the DB row is updated; if either fails the other rolls back.
- Re-intaking an existing `source_url` is a no-op unless `--force` is passed.
