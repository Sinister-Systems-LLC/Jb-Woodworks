// RKOJ Mobile :: api/workstation.ts
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Workstation-tab actions -- thin wrappers around the Forge bridge :5078
// endpoints that surface vault / brain / watchdog / backups / MCP probes.

import { getBaseUrl, getAuthToken } from "./sanctum";

async function wsRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = await getBaseUrl();
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> ?? {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(`${baseUrl}/api/workstation${path}`, { ...init, headers });
  if (!resp.ok) throw new Error(`Workstation API ${path} ${resp.status}: ${await resp.text()}`);
  return (await resp.json()) as T;
}

export interface ActionResult {
  ok: boolean;
  action: string;
  output?: string;
  detail?: Record<string, unknown>;
}

export async function vaultStatus(): Promise<ActionResult> {
  return wsRequest<ActionResult>("/vault/status");
}

export async function brainProbe(): Promise<ActionResult> {
  return wsRequest<ActionResult>("/brain/probe");
}

export async function watchdogStatus(): Promise<ActionResult> {
  return wsRequest<ActionResult>("/watchdog/status");
}

export async function backupsRun(): Promise<ActionResult> {
  return wsRequest<ActionResult>("/backups/run", { method: "POST" });
}

export async function mcpProbe(): Promise<ActionResult> {
  return wsRequest<ActionResult>("/mcp/probe");
}
