/**
 * Lane MX-EVE-INTEGRATE :: claude-auth wire-up
 *
 * Bridges EVE Accounts tab (Lane AZ/ER) -> downstream `claude` CLI invocations.
 *
 * What it does:
 *  - Reads canonical claude-accounts.json + oauth-slot-health.json (READ-ONLY).
 *  - Exposes IPC: GET_SLOT_HEALTH (renderer polls), SET_DEFAULT_SLOT (Accounts tab calls).
 *  - On SET_DEFAULT_SLOT, mutates in-memory state + writes env vars
 *    (CLAUDE_CONFIG_DIR + CLAUDE_OAUTH_TOKEN_FILE) to a runtime env file that
 *    child claude CLI processes spawned by EVE inherit.
 *
 * What it does NOT do:
 *  - Never writes to ANY credentials file.
 *  - Never edits claude-accounts.json.
 */

import { promises as fs } from 'node:fs';
import path from 'node:path';
import { EventEmitter } from 'node:events';
import type { IpcMain } from 'electron';

export interface ClaudeAuthConfig {
  enabled: boolean;
  canonical_accounts_file: string;
  canonical_health_file: string;
  active_workers_file: string;
  default_slot: string;
  fallback_order: string[];
  env_var_for_cli: string;
  config_dir_env_var: string;
  slot_credentials_dir_template: string;
  slot_credentials_file_template: string;
  operator_credentials_dir: string;
  health_poll_ms: number;
  ipc_channel_set_default_slot: string;
  ipc_channel_request_status: string;
}

export interface SlotHealth {
  name: string;
  auth_mode: string;
  enabled: boolean;
  rate_limited: boolean;
  weekly_capped: boolean;
  usage_pct_5h: number;
  score: number;
  availability_score: number;
  has_credentials: boolean;
}

export interface HealthSnapshot {
  measured_at_utc: string;
  fleet_usage_pct_5h: number;
  next_up_slot: string;
  slots: SlotHealth[];
}

export class ClaudeAuth extends EventEmitter {
  private cfg: ClaudeAuthConfig;
  private activeSlot: string;
  private lastHealth: HealthSnapshot | null = null;
  private pollTimer: NodeJS.Timeout | null = null;

  constructor(cfg: ClaudeAuthConfig) {
    super();
    this.cfg = cfg;
    this.activeSlot = cfg.default_slot;
  }

  resolveCredentialsDir(slot: string): string {
    if (slot === 'operator') return this.cfg.operator_credentials_dir;
    return this.cfg.slot_credentials_dir_template.replace('{slot}', slot);
  }

  resolveCredentialsFile(slot: string): string {
    if (slot === 'operator') return path.join(this.cfg.operator_credentials_dir, '.credentials.json');
    return this.cfg.slot_credentials_file_template.replace('{slot}', slot);
  }

  envForChildCli(slot: string = this.activeSlot): Record<string, string> {
    return {
      [this.cfg.config_dir_env_var]: this.resolveCredentialsDir(slot),
      [this.cfg.env_var_for_cli]: this.resolveCredentialsFile(slot),
    };
  }

  async readHealth(): Promise<HealthSnapshot | null> {
    try {
      const raw = await fs.readFile(this.cfg.canonical_health_file, 'utf8');
      const parsed = JSON.parse(raw) as HealthSnapshot;
      this.lastHealth = parsed;
      this.emit('health', parsed);
      return parsed;
    } catch (err) {
      this.emit('error', err);
      return null;
    }
  }

  setDefaultSlot(slot: string): { slot: string; env: Record<string, string> } {
    if (slot !== 'operator' && !this.cfg.fallback_order.includes(slot)) {
      throw new Error(`Slot "${slot}" not in fallback_order or operator`);
    }
    this.activeSlot = slot;
    const env = this.envForChildCli(slot);
    this.emit('slot-changed', { slot, env });
    return { slot, env };
  }

  getActiveSlot(): string {
    return this.activeSlot;
  }

  getLastHealth(): HealthSnapshot | null {
    return this.lastHealth;
  }

  async start(ipcMain: IpcMain): Promise<void> {
    if (!this.cfg.enabled) return;

    ipcMain.handle(this.cfg.ipc_channel_request_status, async () => ({
      activeSlot: this.activeSlot,
      health: this.lastHealth ?? (await this.readHealth()),
    }));

    ipcMain.handle(this.cfg.ipc_channel_set_default_slot, async (_evt, slot: string) => {
      return this.setDefaultSlot(slot);
    });

    await this.readHealth();
    this.pollTimer = setInterval(() => {
      void this.readHealth();
    }, this.cfg.health_poll_ms);
  }

  stop(): void {
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.pollTimer = null;
  }
}

export function createClaudeAuth(cfg: ClaudeAuthConfig): ClaudeAuth {
  return new ClaudeAuth(cfg);
}
