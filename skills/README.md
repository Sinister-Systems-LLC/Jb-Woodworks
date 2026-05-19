# Sinister Skills

This folder is the **canonical archive of every reusable pattern, library, and import-time module** the Sanctum's agents and tools draw from.

## Skills vs. tools

- A **tool** (see `D:\Sinister Sanctum\tools\`) is a runnable entry point. The operator (or an agent) invokes it directly.
- A **skill** is an import-time reusable pattern — a Python module, a token set, a UI skeleton, a memory codec. Skills are consumed *by* tools and agents at construction time; they are not directly invoked.

If you can `import` it, paste it, or junction it into a workspace and reuse it — it's a skill. If you double-click it or run it as a script — it's a tool.

## Append-only rule

- Never delete a skill folder.
- Never delete a row from `_INDEX.md`.
- Skills mature in place. If a skill is superseded, mark it deprecated in `_INDEX.md` but keep the folder and pointer.

## Junction-or-pointer pattern

Skill implementations frequently live outside this folder — inside a bot's own repo, on the Desktop, inside a product workspace. To register a skill here without copying source, use one of two patterns:

### 1. Junction (preferred when the sandbox permits)

A Windows directory junction makes the real source appear at the Sanctum path:

```
mklink /J "D:\Sinister Sanctum\skills\<skill-name>" "<real source path>"
```

Junctions are read-through — edits at either path edit the same files. No duplication, no drift.

### 2. Pointer README (fallback)

When the sandbox blocks `mklink` (or the source moves often), write a `README-SANCTUM-USE.md` at `D:\Sinister Sanctum\skills\<skill-name>\` that names the real source path and the canonical files to consume. Agents and tools resolve the pointer at import time.

Both patterns are first-class. The `_INDEX.md` lists the Sanctum path; the skill's own README spells out where the real source lives.

## How to register a new skill

1. Create `skills/<skill-name>/` (a real folder; the junction or pointer-README lives inside).
2. If you can junction, run `mklink /J` against the real source.
3. Otherwise, write `README-SANCTUM-USE.md` naming the real path + the files to consume.
4. Append a row to `_INDEX.md` (Skill | Path | What it provides).
