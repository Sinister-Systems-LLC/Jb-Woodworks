// lib/types.ts — types matching the bridge_daemon HTTP API.
// RKOJ-ELENO :: 2026-05-24
// Keep in sync with source/bridge_daemon/bridge.py.

export type StatusPayload = {
  ok: boolean;
  phase: string;
  chatdb_path: string;
  chatdb_exists: boolean;
  uptime_sec: number;
  farm_ssh: 'up' | 'not_connected' | 'down';
  tail_alive: boolean;
  send_queue_depth: number;
};

export type Message = {
  rowid: number;
  sent_unix: number;
  is_from_me: boolean;
  body: string | null;
  handle: string | null;
};

export type Thread = {
  chat_id: number;
  chat_identifier: string;
  display_name: string | null;
  service: string | null;
  last_read_unix: number;
  messages: Message[];
};

export type ThreadsResponse = {
  threads: Thread[];
  warning?: string;
};

export type ThreadDetailResponse = {
  thread?: Thread;
  error?: string;
  warning?: string;
};

export type SendRequest = {
  service: 'iMessage' | 'SMS';
  recipient: string;
  body: string;
  operator_ok?: boolean;
  dry_run?: boolean;
};

export type SendResponse =
  | { status: 'ok'; stdout: string; stderr: string; exit: number }
  | { status: 'error'; stdout?: string; stderr?: string; exit?: number; reason?: string }
  | { status: 'blocked'; reason: string; allowed_count?: number }
  | { status: 'dry_run'; service: string; recipient: string; body_len: number };
