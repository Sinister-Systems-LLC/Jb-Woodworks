# Sentinel-specific gotchas

- **Snoozed alarms hide from `list_alarms`** but still exist in alarms.json. Use `include_past=true` to see them.
- **Corrupt alarms.json** is auto-recovered: the bad file is renamed to `.corrupt.<ts>.json` and defaults are restored.
- **Operator timezone vs UTC:** all `due` times are UTC; the operator may see "1 day until" while their local clock says today is the deadline. Surface time in `days_until` plus the actual UTC ISO.
