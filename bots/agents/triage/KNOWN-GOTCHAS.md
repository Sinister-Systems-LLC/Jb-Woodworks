# Triage-specific gotchas

(Hand-edited.)

- **Path patterns beat content heuristics** when they conflict. A file at `08_AUTOMATIONS/foo.ps1` is `automation` even if its content looks like `code`.
- **`secret_risk` is sticky** - once flagged, do NOT downgrade based on path.
