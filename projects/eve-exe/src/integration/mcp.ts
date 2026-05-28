/**
 * Lane MX-EVE-INTEGRATE :: MCP server bootstrap
 *
 * On EVE launch, spawns each enabled MCP server as a child process and tracks
 * its connection state. Emits 'connected' / 'failed' / 'exit' events so the
 * Electron main process can log "MCP server X connected" within 10s.
 *
 * Does NOT speak the MCP protocol itself — it just keeps the processes alive
 * and surfaces health to the renderer. The actual JSON-RPC over stdio is owned
 * by whichever consumer (vault tab, sinister-mind chat) connects to the server.
 */

import { spawn, ChildProcess } from 'node:child_process';
import { EventEmitter } from 'node:events';
import { promises as fs } from 'node:fs';
import type { IpcMain } from 'electron';

export interface McpServerSpec {
  id: string;
  enabled: boolean;
  transport: 'stdio' | 'http';
  cwd?: string;
  command: string;
  args?: string[];
  env?: Record<string, string>;
  tools_prefix?: string;
  optional?: boolean;
  health_check?: string;
}

export interface McpConfig {
  enabled: boolean;
  config_file: string;
  auto_launch_on_eve_start: boolean;
  connect_timeout_ms: number;
  log_file: string;
  servers: McpServerSpec[];
}

type ServerState = 'pending' | 'connected' | 'failed' | 'exited';

interface ServerHandle {
  spec: McpServerSpec;
  proc: ChildProcess | null;
  state: ServerState;
  startedAt: number;
  lastError?: string;
}

export class McpManager extends EventEmitter {
  private cfg: McpConfig;
  private handles: Map<string, ServerHandle> = new Map();
  private logFh: number | null = null;

  constructor(cfg: McpConfig) {
    super();
    this.cfg = cfg;
  }

  private async appendLog(line: string): Promise<void> {
    const ts = new Date().toISOString();
    const msg = `[${ts}] ${line}\n`;
    try {
      await fs.appendFile(this.cfg.log_file, msg);
    } catch {
      // log dir missing — try once
      try {
        const dir = this.cfg.log_file.replace(/[\\/][^\\/]+$/, '');
        await fs.mkdir(dir, { recursive: true });
        await fs.appendFile(this.cfg.log_file, msg);
      } catch {
        /* swallow */
      }
    }
  }

  private launchOne(spec: McpServerSpec): void {
    if (!spec.enabled) return;

    const handle: ServerHandle = {
      spec,
      proc: null,
      state: 'pending',
      startedAt: Date.now(),
    };
    this.handles.set(spec.id, handle);

    try {
      const proc = spawn(spec.command, spec.args ?? [], {
        cwd: spec.cwd,
        env: { ...process.env, ...(spec.env ?? {}) },
        stdio: ['pipe', 'pipe', 'pipe'],
        windowsHide: true,
      });
      handle.proc = proc;

      // Heuristic "connected": process stayed alive for 1.5s without exiting.
      const connectedTimer = setTimeout(() => {
        if (handle.state === 'pending' && proc.exitCode === null) {
          handle.state = 'connected';
          this.emit('connected', spec.id);
          void this.appendLog(`MCP server ${spec.id} connected`);
        }
      }, 1500);

      proc.on('error', (err) => {
        handle.state = 'failed';
        handle.lastError = err.message;
        clearTimeout(connectedTimer);
        this.emit('failed', spec.id, err);
        void this.appendLog(`MCP server ${spec.id} failed: ${err.message}`);
      });

      proc.on('exit', (code) => {
        const wasConnected = handle.state === 'connected';
        handle.state = 'exited';
        clearTimeout(connectedTimer);
        this.emit('exit', spec.id, code);
        void this.appendLog(`MCP server ${spec.id} exited code=${code} wasConnected=${wasConnected}`);
      });

      // Failsafe: if not connected within connect_timeout_ms, mark failed.
      setTimeout(() => {
        if (handle.state === 'pending') {
          handle.state = 'failed';
          handle.lastError = 'connect_timeout';
          this.emit('failed', spec.id, new Error('connect_timeout'));
          void this.appendLog(`MCP server ${spec.id} connect_timeout`);
        }
      }, this.cfg.connect_timeout_ms);
    } catch (err) {
      handle.state = 'failed';
      handle.lastError = (err as Error).message;
      this.emit('failed', spec.id, err);
      void this.appendLog(`MCP server ${spec.id} spawn-threw: ${(err as Error).message}`);
    }
  }

  async start(ipcMain?: IpcMain): Promise<void> {
    if (!this.cfg.enabled) return;
    await this.appendLog(`MCP manager start (${this.cfg.servers.length} servers)`);
    if (this.cfg.auto_launch_on_eve_start) {
      for (const spec of this.cfg.servers) this.launchOne(spec);
    }
    if (ipcMain) {
      ipcMain.handle('MCP_LIST', () => this.list());
      ipcMain.handle('MCP_STATUS', (_evt, id: string) => this.status(id));
    }
  }

  list(): Array<{ id: string; state: ServerState; lastError?: string }> {
    return Array.from(this.handles.values()).map((h) => ({
      id: h.spec.id,
      state: h.state,
      lastError: h.lastError,
    }));
  }

  status(id: string): { id: string; state: ServerState; lastError?: string } | null {
    const h = this.handles.get(id);
    if (!h) return null;
    return { id, state: h.state, lastError: h.lastError };
  }

  async shutdown(): Promise<void> {
    for (const h of this.handles.values()) {
      if (h.proc && h.proc.exitCode === null) {
        try {
          h.proc.kill();
        } catch {
          /* swallow */
        }
      }
    }
  }
}

export function createMcpManager(cfg: McpConfig): McpManager {
  return new McpManager(cfg);
}
