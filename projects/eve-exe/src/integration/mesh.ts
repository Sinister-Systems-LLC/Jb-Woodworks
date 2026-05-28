/**
 * Lane MX-EVE-INTEGRATE :: sinister-mesh wire-up
 *
 * - Connects to NATS at nats://localhost:4222 (port pinned by upstream).
 * - Subscribes to sinister.fleet.> / sinister.spawn.> / sinister.acquire.>
 *   and re-emits each message to the renderer over IPC 'MESH_SUBSCRIBE'.
 * - Exposes a publish helper IPC 'MESH_PUBLISH' for Fleet Flow tab buttons.
 * - Provides a thin HTTP shim to the panel at http://localhost:3081 for
 *   spawn/wake commands.
 *
 * NATS client (`nats` npm package) is loaded lazily so EVE still boots if it
 * is missing — operator just sees "mesh: degraded" in status.
 */

import { EventEmitter } from 'node:events';
import type { IpcMain } from 'electron';

export interface MeshConfig {
  enabled: boolean;
  nats_url: string;
  client_name: string;
  connect_timeout_ms: number;
  reconnect_attempts: number;
  reconnect_time_wait_ms: number;
  subscribe_topics: string[];
  publish_subject_prefix: string;
  panel_http_url: string;
  panel_endpoints: {
    spawn_bot: string;
    wake_bot: string;
    fleet_status: string;
  };
}

interface NatsClientLike {
  publish: (subject: string, data: Uint8Array) => void;
  subscribe: (subject: string) => AsyncIterable<{ subject: string; data: Uint8Array }>;
  drain: () => Promise<void>;
  closed: () => Promise<unknown>;
}

type MeshStatus = 'disconnected' | 'connecting' | 'connected' | 'degraded';

export class MeshClient extends EventEmitter {
  private cfg: MeshConfig;
  private nc: NatsClientLike | null = null;
  private status: MeshStatus = 'disconnected';
  private encoder = new TextEncoder();
  private decoder = new TextDecoder();

  constructor(cfg: MeshConfig) {
    super();
    this.cfg = cfg;
  }

  getStatus(): MeshStatus {
    return this.status;
  }

  private async loadNats(): Promise<((opts: object) => Promise<NatsClientLike>) | null> {
    try {
      // Optional dep — keep require dynamic so missing dep doesn't break EVE boot.
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      const mod: { connect: (opts: object) => Promise<NatsClientLike> } = require('nats');
      return mod.connect;
    } catch {
      return null;
    }
  }

  async connect(): Promise<boolean> {
    if (!this.cfg.enabled) return false;
    this.status = 'connecting';
    this.emit('status', this.status);

    const connectFn = await this.loadNats();
    if (!connectFn) {
      this.status = 'degraded';
      this.emit('status', this.status);
      this.emit('error', new Error('nats client npm package not installed'));
      return false;
    }

    try {
      this.nc = await connectFn({
        servers: this.cfg.nats_url,
        name: this.cfg.client_name,
        timeout: this.cfg.connect_timeout_ms,
        maxReconnectAttempts: this.cfg.reconnect_attempts,
        reconnectTimeWait: this.cfg.reconnect_time_wait_ms,
      });
      this.status = 'connected';
      this.emit('status', this.status);
      this.emit('connected');
      void this.bindSubscriptions();
      return true;
    } catch (err) {
      this.status = 'degraded';
      this.emit('status', this.status);
      this.emit('error', err);
      return false;
    }
  }

  private async bindSubscriptions(): Promise<void> {
    if (!this.nc) return;
    for (const topic of this.cfg.subscribe_topics) {
      void (async () => {
        try {
          const sub = this.nc!.subscribe(topic);
          for await (const msg of sub) {
            const payload = this.decoder.decode(msg.data);
            this.emit('message', { subject: msg.subject, payload });
          }
        } catch (err) {
          this.emit('error', err);
        }
      })();
    }
  }

  publish(subject: string, payload: string | object): void {
    if (!this.nc) throw new Error('mesh not connected');
    const subj = subject.startsWith('sinister.') ? subject : `${this.cfg.publish_subject_prefix}${subject}`;
    const data = this.encoder.encode(typeof payload === 'string' ? payload : JSON.stringify(payload));
    this.nc.publish(subj, data);
  }

  /** HTTP fallback / supplement to NATS — talks to sinister-panel directly. */
  async panelSpawnBot(spec: object): Promise<unknown> {
    const url = this.cfg.panel_http_url + this.cfg.panel_endpoints.spawn_bot;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(spec),
    });
    if (!res.ok) throw new Error(`panel spawn failed: ${res.status}`);
    return res.json();
  }

  async panelWakeBot(botId: string): Promise<unknown> {
    const url = this.cfg.panel_http_url + this.cfg.panel_endpoints.wake_bot;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ id: botId }),
    });
    if (!res.ok) throw new Error(`panel wake failed: ${res.status}`);
    return res.json();
  }

  async panelFleetStatus(): Promise<unknown> {
    const url = this.cfg.panel_http_url + this.cfg.panel_endpoints.fleet_status;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`panel fleet-status failed: ${res.status}`);
    return res.json();
  }

  async start(ipcMain?: IpcMain): Promise<void> {
    await this.connect();
    if (!ipcMain) return;

    ipcMain.handle('MESH_STATUS', () => ({ status: this.status }));

    ipcMain.handle('MESH_PUBLISH', (_evt, subject: string, payload: string | object) => {
      this.publish(subject, payload);
      return { ok: true };
    });

    // Pump incoming messages to a per-window broadcast event.
    this.on('message', (msg) => {
      try {
        const { BrowserWindow } = require('electron') as typeof import('electron');
        for (const win of BrowserWindow.getAllWindows()) {
          win.webContents.send('MESH_INCOMING', msg);
        }
      } catch {
        /* renderer not ready */
      }
    });
  }

  async shutdown(): Promise<void> {
    if (this.nc) {
      try {
        await this.nc.drain();
      } catch {
        /* swallow */
      }
      this.nc = null;
    }
    this.status = 'disconnected';
  }
}

export function createMeshClient(cfg: MeshConfig): MeshClient {
  return new MeshClient(cfg);
}
