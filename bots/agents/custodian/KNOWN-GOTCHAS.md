# Custodian-specific gotchas

- **Secrets are NEVER backed up.** `ignore_secret_files: true` + 6 regex patterns in `watch-list.json` filter `.env`, `id_rsa`, `*.pem`, `credentials.json`, `yurikey*.xml`, `keybox*.xml`. If operator suspects a secret got in before this rule, they should grep `_manifest.jsonl`.
- **Restore is atomic but WILL OVERWRITE** the original path unless `dest=...` is given. Mention this loudly when restoring.
- **Large files skipped:** default `max_file_size_mb: 50`. Operator can override per-call.
- **Per-source scope:** snapshots live under `snapshots/<source>/`. Two different sources with the same rel-path each have their own version tree.
