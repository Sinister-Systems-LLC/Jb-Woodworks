// lib/api.ts — typed client for the bridge_daemon HTTP API.
// RKOJ-ELENO :: 2026-05-24
// All requests proxy through /api/* (see next.config.mjs rewrites).

import type {
  SendRequest,
  SendResponse,
  StatusPayload,
  ThreadDetailResponse,
  ThreadsResponse,
} from './types';

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`/api${path}`, { cache: 'no-store' });
  if (!r.ok) throw new Error(`GET ${path} failed: ${r.status}`);
  return (await r.json()) as T;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    cache: 'no-store',
  });
  return (await r.json()) as T;
}

export const api = {
  status:        () => get<StatusPayload>('/status'),
  threads:       () => get<ThreadsResponse>('/threads'),
  threadDetail:  (chatId: number, limit = 50) =>
                   get<ThreadDetailResponse>(`/threads/${chatId}/messages?limit=${limit}`),
  send:          (req: SendRequest) => post<SendResponse>('/send', req),
};

export function formatUnix(unixS: number): string {
  if (!unixS) return '—';
  return new Date(unixS * 1000).toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
}
