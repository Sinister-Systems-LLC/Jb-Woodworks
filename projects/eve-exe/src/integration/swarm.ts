/**
 * Lane MX-EVE-INTEGRATE :: Swarm console
 *
 * Read-only Phase 1: surfaces active lanes, in-flight worker heartbeats, and
 * blocker alerts to a dedicated EVE tab (or Plans-tab sub-panel).
 *
 * Phase 2 (spawn/respawn) is gated behind `phase2_actions_enabled` in the
 * runtime config; this module exposes the IPC surface but rejects writes when
 * the flag is false.
 */

import { promises as fs } from 'node:fs';
import { glob } from 'node:fs/promises';
import path from 'node:path';
import { EventEmitter } from 'node:events';
import type { IpcMain } from 'electron';

export interface SwarmConfig {
  enabled: boolean;
  mode: 'read_only' | 'interactive';
  shared_memory_root: string;
  paths: {
    tasks: string;
    tasks_fallback_glob: string;
    heartbeats: string;
    operator_alerts: string;
    active_workers: string;
    progress_root: string;
  };
  poll_ms: number;
  tab_id: string;
  tab_label: string;
  tab_position: string;
  phase2_actions_enabled: boolean;
}

export interface SwarmTask {
  id: string;
  source_file: string;
  raw: unknown;
}

export interface SwarmHeartbeat {
  lane: string;
  source_file: string;
  mtime_utc: string;
  raw: unknown;
}

export interface SwarmAlert {
  ts: string;
  level: string;
  lane?: string;
  message: string;
  raw: unknown;
}

async function safeReadJson<T>(file: string): Promise<T | null> {
  try {
    const raw = await fs.readFile(file, 'utf8');
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

async function listFiles(dir: string, ext: string): Promise<string[]> {
  try {
    const ents = await fs.readdir(dir, { withFileTypes: true });
    return ents.filter((e) => e.isFile() && e.name.endsWith(ext)).map((e) => path.join(dir, e.name));
  } catch {
    return [];
  }
}

export class SwarmConsole extends EventEmitter {
  private cfg: SwarmConfig;
  private pollTimer: NodeJS.Timeout | null = null;

  constructor(cfg: SwarmConfig) {
    super();
    this.cfg = cfg;
  }

  async readTasks(): Promise<SwarmTask[]> {
    let files = await listFiles(this.cfg.paths.tasks, '.json');
    if (files.length === 0) {
      // Fallback: dispatcher/*.json (current canonical lane records)
      try {
        const matched: string[] = [];
        for await (const f of glob(this.cfg.paths.tasks_fallback_glob)) matched.push(f);
        files = matched;
      } catch {
        /* glob unsupported on older node — skip */
      }
    }
    const tasks: SwarmTask[] = [];
    for (const f of files) {
      const raw = await safeReadJson<unknown>(f);
      if (raw) tasks.push({ id: path.basename(f, '.json'), source_file: f, raw });
    }
    return tasks;
  }

  async readHeartbeats(): Promise<SwarmHeartbeat[]> {
    const files = await listFiles(this.cfg.paths.heartbeats, '.json');
    const beats: SwarmHeartbeat[] = [];
    for (const f of files) {
      try {
        const stat = await fs.stat(f);
        const raw = await safeReadJson<unknown>(f);
        if (raw) {
          beats.push({
            lane: path.basename(f, '.json'),
            source_file: f,
            mtime_utc: stat.mtime.toISOString(),
            raw,
          });
        }
      } catch {
        /* skip */
      }
    }
    return beats;
  }

  async readAlerts(limit = 100): Promise<SwarmAlert[]> {
    try {
      const raw = await fs.readFile(this.cfg.paths.operator_alerts, 'utf8');
      const lines = raw.split(/\r?\n/).filter(Boolean);
      const tail = lines.slice(-limit);
      const out: SwarmAlert[] = [];
      for (const line of tail) {
        try {
          const parsed = JSON.parse(line);
          out.push({
            ts: parsed.ts ?? parsed.timestamp ?? '',
            level: parsed.level ?? 'info',
            lane: parsed.lane,
            message: parsed.message ?? parsed.msg ?? JSON.stringify(parsed),
            raw: parsed,
          });
        } catch {
          out.push({ ts: '', level: 'info', message: line, raw: line });
        }
      }
      return out;
    } catch {
      return [];
    }
  }

  async snapshot(): Promise<{ tasks: SwarmTask[]; heartbeats: SwarmHeartbeat[]; alerts: SwarmAlert[] }> {
    const [tasks, heartbeats, alerts] = await Promise.all([
      this.readTasks(),
      this.readHeartbeats(),
      this.readAlerts(),
    ]);
    return { tasks, heartbeats, alerts };
  }

  async start(ipcMain?: IpcMain): Promise<void> {
    if (!this.cfg.enabled) return;
    if (ipcMain) {
      ipcMain.handle('SWARM_TASKS', () => this.readTasks());
      ipcMain.handle('SWARM_HEARTBEATS', () => this.readHeartbeats());
      ipcMain.handle('SWARM_ALERTS', (_evt, limit?: number) => this.readAlerts(limit));
      ipcMain.handle('SWARM_SNAPSHOT', () => this.snapshot());
      ipcMain.handle('SWARM_SPAWN_LANE', () => {
        if (!this.cfg.phase2_actions_enabled) {
          return { ok: false, error: 'phase2_actions_disabled' };
        }
        return { ok: false, error: 'not_implemented_yet' };
      });
    }

    this.pollTimer = setInterval(() => {
      void this.snapshot().then((snap) => this.emit('snapshot', snap));
    }, this.cfg.poll_ms);
  }

  stop(): void {
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.pollTimer = null;
  }
}

export function createSwarmConsole(cfg: SwarmConfig): SwarmConsole {
  return new SwarmConsole(cfg);
}
