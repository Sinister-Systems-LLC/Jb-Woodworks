# Auditor-specific gotchas

- **False positives on regex:** `sk-ant-` matches comments mentioning the format. Inspect the path before panicking.
- **Dedupe across `02_MD_ARCHIVE/` is expected** - that section deliberately mirrors source. Don't try to "fix" archive dupes.
- **Stale isn't always bad** - some reference docs (Yurikey-shape, secrets policy) are intentionally evergreen.
