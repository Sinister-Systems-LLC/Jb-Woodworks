// Sinister Claw :: api/forge.ts
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// API client for Sinister Forge over Tailscale.
// Backend: `python -m forge.bridge` (projects/sinister-forge/source/forge/bridge/).

// react-native-event-source polyfills EventSource for RN (which lacks it natively).
// Side-effect import: registers a global so the `new EventSource(...)` calls below work.
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore - no types ship with the polyfill
import RNEventSource from "react-native-event-source";
if (typeof (globalThis as { EventSource?: unknown }).EventSource === "undefined") {
  (globalThis as { EventSource: unknown }).EventSource = RNEventSource;
}

import { getBaseUrl, getAuthToken } from "./sanctum";

export interface ForgeAgent {
  id: string;
  agent_name: string;
  project_key: string;
  project_display: string;
  mode: string;
  accent: string;
  status: "ready" | "running" | "exited" | "error";
  host: "claude" | "codex";
  pid?: number;
  started_at: string;
}

async function forgeRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = await getBaseUrl();
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> ?? {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(`${baseUrl}/api/forge${path}`, { ...init, headers });
  if (!resp.ok) throw new Error(`Forge API ${path} ${resp.status}`);
  return (await resp.json()) as T;
}

export async function listAgents(): Promise<ForgeAgent[]> {
  return forgeRequest<ForgeAgent[]>("/agents");
}

export async function spawnAgent(params: {
  project: string;
  objective: string;
  agent_name: string;
  accent: string;
  host: "claude" | "codex";
  token_mode: "compact" | "full";
  speed: "max" | "turbo" | "fast" | "normal";
  focus?: string;
}): Promise<ForgeAgent> {
  return forgeRequest<ForgeAgent>("/spawn", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function terminateAgent(id: string): Promise<void> {
  await forgeRequest<void>(`/agents/${id}`, { method: "DELETE" });
}

/**
 * Subscribe to SSE stream of an agent's stdout/stderr.
 * Caller responsible for closing the EventSource.
 */
export async function openAgentStream(
  id: string,
  onLine: (line: string) => void,
): Promise<EventSource> {
  const baseUrl = await getBaseUrl();
  const token = await getAuthToken();
  const url = `${baseUrl}/api/forge/agents/${id}/stream${token ? `?token=${encodeURIComponent(token)}` : ""}`;
  // @ts-expect-error EventSource is provided by react-native-event-source polyfill
  const es = new EventSource(url);
  es.addEventListener("line", (evt: MessageEvent) => onLine(evt.data));
  return es;
}
