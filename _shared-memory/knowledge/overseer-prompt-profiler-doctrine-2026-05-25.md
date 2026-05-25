<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->
# Overseer Prompt Profiler Doctrine (operator hard-canonical 2026-05-25)

**Author:** RKOJ-ELENO :: 2026-05-25

**Operator directive (verbatim 2026-05-25):** *"overseer needs to start reviewing all my system prompts leo and i do and train himself on how to prompt like us and how we work etc and build profiles and settings for what we like. set this up now and update memory."*

---

## What it does

`projects/sinister-overseer/src/overseer/prompt_profiler.py` is the Overseer's built-in
style-learning module. On each session startup it reads every row of
`_shared-memory/operator-utterances.jsonl` and extracts a set of measurable style traits
for each known user profile (operator = RKOJ-ELENO; collaborator = Leo). Profiles are
saved as JSON to `_shared-memory/prompt-profiles/<profile_id>.json`.

### Extracted traits per profile

| Trait | How computed |
|---|---|
| `avg_words_per_message` | mean word count across all utterances |
| `uses_urgency` | >30% of utterances contain urgency keywords |
| `uses_profanity` | any utterance contains a profanity token |
| `uses_shorthand` | >5% of utterances contain operator shorthand typos |
| `directness` | ratio of imperative-opener utterances (high ≥ 0.4) |
| `avg_sentence_length` | mean words per sentence across all utterances |
| `top_verbs` | 20 most-common action verbs in descending frequency |
| `domain_vocab` | 30 most-common Sinister-Sanctum domain terms |
| `action_patterns` | most-common intent categories (imperative-directive, update-memory, urgency-cue, fleet-management, verification-request, memory-anchor) |
| `learned_preferences` | inferred per-session prefs (loop=relentless, no-bullshit, update-brain, execute-immediately, direct-tone) |
| `frustration_signals` | up to 15 verbatim snippets that triggered frustration detection regex (ALL-CAPS clusters, repeated punctuation, "AGAIN", "WHY") |

---

## Where profiles live

```
_shared-memory/prompt-profiles/
    operator.json     # RKOJ-ELENO main operator
    leo.json          # Leo collaborator
```

Both files are regenerated every Overseer startup via `_refresh_prompt_profiles()` in
`orchestrator.py`. Each profile is also manually refreshable via:

```bash
python projects/sinister-overseer/src/overseer/prompt_profiler.py --scan --profile operator
python projects/sinister-overseer/src/overseer/prompt_profiler.py --scan --profile all
```

---

## How to rescan

```bash
# Rescan just operator
python projects/sinister-overseer/src/overseer/prompt_profiler.py --scan --profile operator

# Rescan both profiles
python projects/sinister-overseer/src/overseer/prompt_profiler.py --scan --profile all

# Show a saved profile
python projects/sinister-overseer/src/overseer/prompt_profiler.py --show operator

# Enhance a vague prompt using the operator profile
python projects/sinister-overseer/src/overseer/prompt_profiler.py --suggest-prompt "add logging to the overseer"
```

---

## How Overseer uses profiles to improve spawn quality

1. **Startup refresh** — `OverseerOrchestrator._refresh_prompt_profiles()` calls
   `PromptProfiler(sanctum_root).scan(["operator"])` once per session (not every 5-min cycle).
   This keeps the profile current without hammering disk I/O.

2. **Spawn phrase augmentation** — when Overseer proposes a new sub-lane spawn, it reads
   `operator.json` and prepends the `learned_preferences` as a context block in the spawn
   phrase so the spawned agent inherits the operator's working style on day 1.

3. **`--suggest-prompt` heuristics** — six rules applied in order:
   - Short prompt (<10 words) → append "in D:\Sinister Sanctum" working-dir context
   - Fleet preference detected → append "loop and swarm mode on"
   - No-bullshit preference detected → append "test and verify before claiming done"
   - Memory-anchor tendency detected → append "update memory / brain with findings"
   - High-directness style → ensure imperative opener ("Do: …")
   - Profile not found → auto-rescan before enhancing

4. **Frustration signal awareness** — agents spawned with a prompt containing recognized
   frustration patterns should parse those snippets from the profile and proactively clarify
   scope BEFORE starting work (avoiding the repeat-failure pattern the operator has documented).

---

## Anti-patterns

- **DO NOT** run `--scan` inside a 5-min watch cycle — one-per-session only (disk I/O + JSONL parse cost).
- **DO NOT** use the profiler to classify utterances as "complaints to ignore" — every utterance = operator intent.
- **DO NOT** hard-code assumed traits (e.g. always adding "loop=on") without loading the profile — let the learned data drive enhancement.
- **DO NOT** store PII snippets in frustration_signals — the regex captures *style evidence*, not personal data.

---

## Composes with

- `loop-relentless-pursuit-doctrine-2026-05-25.md` — profiler refresh fires on session start, before the relentless loop begins
- `operator-utterance-tracking-doctrine-2026-05-24.md` — the source JSONL this module reads
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` — profiler claims only what it can measure; smoke test = `--scan` exit 0 + profile file written
- `sinister-overseer-charter-2026-05-24.md` — profiler is an Overseer-lane module; scope = OVERSEER framework only
- `automate-everything-no-operator-admin-2026-05-25.md` — operator never needs to click to rescan; Overseer does it on startup
