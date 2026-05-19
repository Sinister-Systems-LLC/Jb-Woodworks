// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
// REWRITE 2026-05-19: OpenRouter -> Anthropic SDK. Same signature, new backend.
//
// `llmComplete(opts) => Promise<string>` is the exported contract. It MUST
// remain shape-compatible with the Panel version so that chatEngine.ts
// continues to work without modification.
//
// What changed vs Panel:
//   - Was: axios POST to https://openrouter.ai/api/v1/chat/completions with
//     OPENROUTER_API_KEY.
//   - Now: official @anthropic-ai/sdk client, model defaults to
//     claude-haiku-4-5-20251001 (cheap; matches Panel's default-tier
//     economics). Per-group override is still honored via opts.model.
//   - Anthropic's API separates the `system` parameter from the
//     user/assistant turn stream, so we extract any role:"system" entries
//     from `messages[]` and concatenate them into the `system:` param.

import Anthropic from "@anthropic-ai/sdk";

export interface LlmMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface LlmOptions {
  model: string;
  messages: LlmMessage[];
  temperature?: number;
  maxTokens?: number;
}

const DEFAULT_MODEL = "claude-haiku-4-5-20251001";

// Lazy singleton so that missing ANTHROPIC_API_KEY surfaces at call-time
// (matching Panel's behavior, which threw on call-time only).
let _client: Anthropic | null = null;
function getClient(): Anthropic {
  if (_client) return _client;
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error("ANTHROPIC_API_KEY not configured");
  _client = new Anthropic({ apiKey });
  return _client;
}

export async function llmComplete(opts: LlmOptions): Promise<string> {
  const client = getClient();

  // Anthropic uses a top-level `system` parameter, not a system role inside
  // messages[]. Concatenate any system entries (chatEngine only emits one,
  // but be defensive) and strip them from the turn stream.
  const systemParts: string[] = [];
  const turns: { role: "user" | "assistant"; content: string }[] = [];
  for (const m of opts.messages) {
    if (m.role === "system") {
      systemParts.push(m.content);
    } else {
      turns.push({ role: m.role, content: m.content });
    }
  }
  const system = systemParts.join("\n\n");

  // Anthropic requires at least one user/assistant message; chatEngine
  // always provides at least one user turn, but guard anyway.
  if (turns.length === 0) {
    turns.push({ role: "user", content: "" });
  }

  const model = (opts.model && opts.model.trim().length > 0) ? opts.model : DEFAULT_MODEL;

  const response = await client.messages.create({
    model,
    max_tokens: opts.maxTokens ?? 600,
    temperature: opts.temperature ?? 0.9,
    system: system || undefined,
    messages: turns,
  });

  // For plain-text completions, take the first content block's text.
  // chatEngine then JSON-parses it to recover the bubble array.
  const first = response.content[0];
  if (first && first.type === "text") {
    return first.text ?? "";
  }
  return "";
}
