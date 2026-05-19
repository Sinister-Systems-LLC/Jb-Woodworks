# Sinister Tools

This folder is the **canonical archive of every runnable tool, automation, and invention shipped inside the Sinister Sanctum**. Each tool gets its own subfolder and is recorded in `_INDEX.md`. The archive is append-only — tools are never silently retired; their status changes but their card remains.

## Operator Directive (durable, 2026-05-19)

> "everything we create needs to be placed into its own specific folder and noted as a tool in the archives. like this session start module. we need to have a collection of sinister skils, tools, inventions all of that. this folder will forever grow and expand"

This directive is law. Every new runnable artifact lands here with a folder + card.

## What lives here

A **tool** is a runnable entry point — something the operator (or an agent) invokes directly. Examples: a launcher script, a CLI, a console app, a capture utility.

Tools are distinct from **skills** (see `D:\Sinister Sanctum\skills\`) which are import-time reusable patterns/libraries, and from **inventions** (see `D:\Sinister Sanctum\inventions\`) which are raw idea captures awaiting promotion.

The typical lifecycle:

```
invention (idea capture)  -->  tool (shipped runnable)  -->  skill (reusable pattern extracted)
```

## Append-only rule

- Never delete a tool folder.
- Never delete a row from `_INDEX.md`.
- Status transitions instead: `drafting` -> `shipped` -> `deprecated` -> `archived`.
- Implementation may live elsewhere on disk; the card here is the registration record.

## How to register a new tool

1. Copy `_TEMPLATE.md` to `tools/<slug>/README.md`.
2. Fill every section — especially **Implementation files** (absolute paths) and **How to invoke**.
3. Append a row to `_INDEX.md` (Tool | Folder | Implementation | Status | Captured).
4. If the tool was born from an invention capture, link the invention markdown under **Linked-inventions**.
5. If the tool grows new versions, append to the **Changelog** section of its card — never overwrite history.

## Lane discipline

Tools are created under the lane that owns them. The default orchestration lane is **master / Sanctum orchestration**. Other lanes (per-bot, per-project) may register their own tools but must use this same folder layout and `_INDEX.md`.

The Sanctum orchestrator (this lane) is responsible for:
- Maintaining `_INDEX.md` integrity.
- Reviewing tool cards on creation.
- Ensuring no tool ships without a card.

Tools that touch a project's source live in that project's repo; their **registration** still lands here.
