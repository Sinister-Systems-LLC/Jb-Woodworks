// Sinister Claw :: api/sanctum.ts
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// API client for Sanctum master (over Tailscale tunnel). The operator's
// PC must be reachable on the tailnet at the configured base URL.

import * as SecureStore from "expo-secure-store";

const STORE_KEY_BASE_URL = "claw.sanctum.base_url";
const STORE_KEY_AUTH_TOKEN = "claw.sanctum.auth_token";

export async function getBaseUrl(): Promise<string> {
  return (await SecureStore.getItemAsync(STORE_KEY_BASE_URL)) ?? "http://sanctum-pc:5078";
}

export async function setBaseUrl(url: string): Promise<void> {
  await SecureStore.setItemAsync(STORE_KEY_BASE_URL, url);
}

export async function getAuthToken(): Promise<string | null> {
  return await SecureStore.getItemAsync(STORE_KEY_AUTH_TOKEN);
}

export async function setAuthToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(STORE_KEY_AUTH_TOKEN, token);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = await getBaseUrl();
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> ?? {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(`${baseUrl}${path}`, { ...init, headers });
  if (!resp.ok) {
    throw new Error(`Sanctum API ${path} ${resp.status}: ${await resp.text()}`);
  }
  return (await resp.json()) as T;
}

// --- High-level API ---

export interface SanctumHeartbeat {
  agent: string;
  ts_utc: string;
  alive: boolean;
  ago_min: number;
}

export interface SanctumHeartbeats {
  agents: SanctumHeartbeat[];
}

export async function getHeartbeats(): Promise<SanctumHeartbeats> {
  return request<SanctumHeartbeats>("/api/sanctum/heartbeats");
}

export interface SanctumProject {
  key: string;
  display: string;
  tag: string;
  github: string;
}

export async function getProjects(): Promise<SanctumProject[]> {
  return request<SanctumProject[]>("/api/sanctum/projects");
}

export interface RecentCommit {
  hash: string;
  branch: string;
  message: string;
  ts_utc: string;
}

export async function getRecentCommits(limit = 20): Promise<RecentCommit[]> {
  return request<RecentCommit[]>(`/api/sanctum/commits?limit=${limit}`);
}

export interface InboxItem {
  id: string;
  source: "inbox" | "cross-agent";
  tag: string;
  from: string;
  to: string;
  subject: string;
  ts_utc: string;
  project_hint: string;
  body_path: string;
  body: string;
}

export interface InboxResponse {
  items: InboxItem[];
  total: number;
}

export async function getInbox(limit = 50): Promise<InboxResponse> {
  return request<InboxResponse>(`/api/sanctum/inbox?limit=${limit}`);
}

export interface ProgressEntry {
  heading: string;
  snippet: string;
}

export interface ResumePoint {
  schema_version: string;
  ts_utc: string;
  project: string;
  agent_name: string;
  mode: string;
  focus_intent?: string;
  git?: {
    branch?: string;
    head?: string;
    head_msg?: string;
    recent_commits?: string[];
  };
  progress_top3?: unknown[];
  latest_plan?: { dir?: string | null; artifact?: string | null };
}

export interface PlanInfo {
  dir: string;
  mtime: string;
}

export interface ProjectDetail {
  project: SanctumProject;
  progress_entries: ProgressEntry[];
  resume_point: ResumePoint | null;
  plans: PlanInfo[];
}

export async function getProjectDetail(key: string): Promise<ProjectDetail> {
  return request<ProjectDetail>(`/api/sanctum/projects/${encodeURIComponent(key)}/detail`);
}
