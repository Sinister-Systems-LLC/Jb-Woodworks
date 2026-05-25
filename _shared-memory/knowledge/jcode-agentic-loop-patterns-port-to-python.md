<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# jcode agentic-loop patterns — port to Python (Sinister Forge)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Source:** Research sweep against `C:\Users\Zonia\Desktop\Github Research\jcode-0.12.3\` (Rust, AGPL-3.0-or-later)
> **Why this file exists:** Operator wants RKOJ.exe's natural-language path to match jcode's visible multi-step tool reasoning (batch tool calls, streaming thinking, "● Searching" / "✓ Found" status lines). v0.6.0 ships a Python port of these patterns in `forge/spawn/anthropic_direct.py`; this doc is the canonical reference for future tweaks.

## The six jcode patterns we need

### 1. Streaming thinking/reasoning blocks

**jcode files:** `src/agent/turn_loops.rs:178-200`, `crates/jcode-message-types/src/lib.rs:560-630`.

**Pattern:** Anthropic SDK emits `ThinkingDelta(String)` events on the stream. jcode prints `💭 {thinking_text}` per delta, accumulates into a `reasoning_content` buffer, and prints `Thought for {N:.1}s\n` at `ThinkingDone`.

**Python:** In our stream handler, match `event.type == "content_block_delta"` with `delta.type == "thinking_delta"` and print delta.thinking as soon as it arrives. Accumulate for history. Time the block.

### 2. Batch tool calls (multiple `tool_use` in one assistant turn)

**jcode files:** `src/agent/turn_loops.rs:208-258, 558-564, 650`.

**Pattern:** `tool_calls: Vec<ToolCall>` accumulator. As the stream emits `ToolUseStart{id,name}` / `ToolInputDelta(d)` / `ToolUseEnd`, push to the vector. After `MessageEnd`, iterate the vector and execute each tool. Append every result to the message history with `Role::User + ToolResult{tool_use_id, content}`. Continue the outer loop with the new messages — that's how jcode does multi-step reasoning across turns.

**Python:** Don't break out of the streaming loop on the first tool call. Buffer every `tool_use` block from the assistant message, then after `message_stop` execute them all sequentially (or in parallel for read-only tools). This is the critical pattern operator sees in jcode — multiple tools in one "turn" visually.

### 3. Progress / status indicators (`● Searching` / `✓ Found`)

**jcode files:** `src/agent/turn_loops.rs:208-214, 250-253, 702-710`, `src/agent/tools.rs:59-91 print_tool_summary`.

**Pattern:**
- On `ToolUseStart`: print `\n[{name}] ` (e.g., `[bash] `, `[read] `).
- Print short summary line for bash → `$ {cmd}`, read/write/edit → `{path}`, glob/grep → `'{pattern}'`.
- After tool executes: print `\n  → ` followed by first ~200 chars of output (truncate with `...truncated`).

**Python:** rich.console.print with colors: gold-bold for the `[{name}]` header, gray-dim for the `  → result` indent.

### 4. Main agentic loop (`run_turn`)

**jcode file:** `src/agent/turn_loops.rs:9-900`.

**Pattern (pseudocode):**
```
loop:
    messages = session.messages_for_provider()
    tools = session.tool_definitions()
    stream = provider.complete_split(messages, tools, static_prompt, dynamic_prompt)
    tool_calls = []
    for event in stream:
        match event:
            TextDelta(t):       text_content += t
            ThinkingDelta(t):   reasoning_content += t; print(💭 t)
            ToolUseStart{id,name}: current = ToolCall(id, name)
            ToolInputDelta(d):  current.input_raw += d
            ToolUseEnd:         tool_calls.append(parse(current))
            MessageEnd:         saw_end = true
    if tool_calls is empty: break
    for tc in tool_calls:
        result = registry.execute(tc.name, tc.input, ctx)
        session.add_message(Role::User, ToolResult{tc.id, result})
    # loop continues with the augmented message history
```

**Python:** This is precisely what `anthropic_direct.run_turn()` in v0.6.0 does — `anthropic.Anthropic.messages.stream` + iterate `stream.text_stream` AND `stream.current_message_snapshot` for tool blocks + accumulate + execute + re-stream.

### 5. Slash command / skill registry

**jcode files:** `src/skill.rs:12-35` (Skill struct), `src/skill.rs:32-53` (SkillRegistry), `src/skill.rs:202-230` (load_for_working_dir).

**Pattern:**
- Each skill = SKILL.md with YAML frontmatter (name, description, allowed-tools).
- `SkillRegistry::load()` walks `~/.jcode/skills/`, parses frontmatter, indexes by name.
- On `/skillname`, registry injects the skill's content into the system prompt as `# Active Skill`.

**Python:** We already have `forge/commands.py` with 50 slash commands. To match jcode's skill-file approach, ALSO load `~/.sinister/skills/*.md` (YAML frontmatter) and register them as additional slash names. When invoked, append their content to the next user message's system prompt.

### 6. Session search (BM25-scored cross-session recall)

**jcode file:** `src/tool/session_search.rs:1-200`.

**Pattern:**
- Walks `~/.jcode/sessions/` for snapshot + journal JSON in parallel (`SCAN_THREADS=8`).
- Pre-filter by metadata: date range, working_dir, provider, model, saved/debug/canary flags.
- BM25-score each message against the query, group by session, return top-k with surrounding context.
- Defaults: `limit=10`, `max_per_session=1`, exclude current + system + tools.

**Python:** Our current `forge_memory_bridge.recall()` is TF-IDF + Ruflo agentdb (good). To match jcode's BM25 specifically, add a `rank_bm25` dependency and re-score the candidate set inside `bridge.search()`. Sessions live at `_shared-memory/resume-points/<display-name>/*.json` — index those.

## What v0.6.0 shipped (anthropic_direct.py)

- Tool-use loop with 12-turn cap, 8K tokens/turn, model `claude-opus-4-7`
- 6 tools wired: `bash` (safety-gated), `read_file`, `write_file`, `glob_search`, `grep_search`, `session_search`
- Streams `thinking_delta` + `text_delta` live; tool_use blocks render as `● tool {name} {preview}` + gray-boxed result preview (first 6 lines + count)
- Pre-turn `forge_memory_bridge.recall` + post-turn `write` preserved (matches `claude -p` path so memory stays consistent across providers)
- Bash safety gate regex-blocks: `rm -rf`, `format c:`, `shutdown`, `del /s`, `mkfs`, `dd if=*of=/dev/`, fork-bombs
- API keys NEVER printed (only `os.environ.get`)
- Falls back to `claude -p` candidate loop when `ANTHROPIC_API_KEY` is absent OR the SDK module crashes

## What's left to match jcode parity (v0.7.0+ roadmap)

1. **Parallel tool execution** — read-only tools (read_file, glob, grep) can run concurrently. jcode does this; we currently serialize.
2. **Skill-file loading** — `~/.sinister/skills/*.md` with YAML frontmatter, auto-register as `/skillname`.
3. **BM25 re-scoring** inside `forge_memory_bridge.recall()`.
4. **Session-grouped recall output** — current memory bridge returns flat hits; jcode groups by session with context.
5. **Token-budget management** — jcode hard-caps at 200K context per provider; we don't track yet.
6. **Prompt caching** — Anthropic SDK supports `cache_control` ephemeral blocks; jcode uses it on the static system prompt. We don't.

## Where in the Sanctum tree the port lives

| Pattern | File |
|---|---|
| 1, 2, 3, 4 | `projects/sinister-forge/source/forge/spawn/anthropic_direct.py` (~410 lines, v0.6.0) |
| 5 (current state) | `projects/sinister-forge/source/forge/commands.py` (50 slash commands) |
| 6 (current state) | `tools/forge-memory-bridge/src/forge_memory_bridge/__init__.py` (TF-IDF + Ruflo) |

## Cross-references

- `_shared-memory/knowledge/sinister-cli-subcommand-pattern.md` — the 5-file layout doctrine
- `_shared-memory/knowledge/agent-identity-eve.md` — EVE persona doctrine
- `automations/build/forge-exe/README.md` — RKOJ.exe build pipeline
