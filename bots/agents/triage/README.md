# Triage agent

Tier 2 file/text classifier. Routes incoming files to the right hub section.

**Cost:** $0 (Ollama small model `qwen2.5:1.5b`, or pure-Python rules when Ollama is down).

## Tools

| Tool | Purpose |
|---|---|
| `triage.classify_file(path)` | Read first 4KB, classify, suggest hub section |
| `triage.classify_text(text, hint=None)` | Classify a raw snippet |
| `triage.classify_batch(paths)` | Classify many at once |
| `triage.list_categories()` | Full category catalog |
| `triage.health()` | Reports Ollama status + active mode |

## Output shape

```json
{
  "category": "memory",
  "suggested_section": "01_MEMORY",
  "project": "sinister-panel",
  "tags": ["yurikey", "operator-action"],
  "confidence": 0.85,
  "mode": "ollama",
  "reason": "matches per-project memory anchor pattern",
  "path": "...",
  "exists": true
}
```

## Categories

15 categories mapped to hub sections (`01_MEMORY`..`12_LLM_ORCHESTRATION`) plus `QUARANTINE` (secret risk), `DROP` (ephemeral), `?` (unknown). Call `list_categories()` for the canonical list.

## Tiers

1. **Ollama (qwen2.5:1.5b)** — default. ~1s/call. Validates the model's JSON; on bad output, falls back to rules.
2. **Pure-Python rules** — used when Ollama is unreachable. Path regex + secret-pattern + content heuristics.

Secret detection always runs (even in Ollama mode) — anything matching API-key / private-key patterns is forced to `secret_risk`.

## Environment

- `SINISTER_HUB_ROOT` — defaults to `D:\Sinister\Sinister Skills`
- `OLLAMA_HOST` — defaults to `http://localhost:11434`
- `TRIAGE_MODEL` — defaults to `qwen2.5:1.5b`

## Pulling the model

```powershell
cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\docker'
docker compose up -d
docker exec -it ollama ollama pull qwen2.5:1.5b
```

The agent works without Ollama (rules mode), but classification is sharper with it.
