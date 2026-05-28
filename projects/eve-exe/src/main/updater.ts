/**
 * Lane MX-EVE-UPDATER :: electron-updater wiring
 *
 * One EVE.exe binary that auto-updates between operator and Leo.
 *
 * Operator directives (verbatim):
 *   - "i want 1 exe and it auto update between leo and it"
 *   - "make sure i can do updates and leo can get them on his end if he needs
 *      to restart he will have banner that says. make sure to have version
 *      appraoch to everything"
 *
 * Transport: sinister-vault HTTP (already on tailnet, port 5078). Falls back to
 * a no-op when electron-updater is unavailable (e.g. during MX-EVE-FULL
 * bootstrap before npm i is run) so this file is safe to import at any time.
 *
 * Pairs with:
 *   - automations/eve_release_publish.py  (writes latest.yml + EVE.exe to vault)
 *   - src/renderer/components/UpdateBanner.tsx  (renders UPDATE_READY events)
 */

import type { IpcMain } from 'electron';
import { EVE_VERSION } from '../shared/version';

/** IPC channel names — also surfaced via preload to the renderer. */
export const UPDATER_CHANNELS = {
  UPDATE_READY: 'UPDATE_READY',
  APPLY_UPDATE: 'APPLY_UPDATE',
  GET_VERSION: 'GET_VERSION',
  GET_UPDATER_STATUS: 'GET_UPDATER_STATUS',
} as const;

export interface UpdaterConfig {
  /** Base URL where latest.yml + EVE.exe live. */
  feedUrl?: string;
  /** Delay before first check (ms). Default 30_000. */
  startupSettleMs?: number;
  /** Interval between checks (ms). Default 15 * 60_000. */
  pollIntervalMs?: number;
  /** Skip actual network calls (smoke tests). */
  dryRun?: boolean;
}

const DEFAULTS: Required<Omit<UpdaterConfig, 'dryRun'>> & { dryRun: boolean } = {
  feedUrl: 'http://sinister-vault.local:5078/releases/eve-exe/',
  startupSettleMs: 30_000,
  pollIntervalMs: 15 * 60_000,
  dryRun: false,
};

export interface UpdaterStatus {
  currentVersion: string;
  pendingVersion: string | null;
  lastCheckedAt: string | null;
  lastError: string | null;
  feedUrl: string;
}

export interface UpdaterHandle {
  status: () => UpdaterStatus;
  checkNow: () => Promise<void>;
  stop: () => void;
}

/**
 * Wire electron-updater into the main process. Returns a handle the caller
 * (main.ts) can use to query status or stop the poll loop on app quit.
 *
 * Safe to call before electron-updater is installed: degrades to a stub
 * that still answers GET_VERSION / GET_UPDATER_STATUS IPC so the renderer
 * never crashes.
 */
export function setupUpdater(
  ipcMain: IpcMain,
  currentVersion: string = EVE_VERSION,
  cfgIn: UpdaterConfig = {},
): UpdaterHandle {
  const cfg = { ...DEFAULTS, ...cfgIn };

  const state: UpdaterStatus = {
    currentVersion,
    pendingVersion: null,
    lastCheckedAt: null,
    lastError: null,
    feedUrl: cfg.feedUrl,
  };

  let pollTimer: NodeJS.Timeout | null = null;
  let startupTimer: NodeJS.Timeout | null = null;
  let autoUpdater: any = null;

  // Lazy-require so this module loads even when electron-updater isn't
  // installed yet (MX-EVE-FULL hasn't run npm i yet).
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires, global-require
    autoUpdater = require('electron-updater').autoUpdater;
  } catch (err) {
    state.lastError = `electron-updater not installed: ${(err as Error).message}`;
  }

  if (autoUpdater && !cfg.dryRun) {
    try {
      autoUpdater.autoDownload = true;
      autoUpdater.autoInstallOnAppQuit = true;
      autoUpdater.setFeedURL({ provider: 'generic', url: cfg.feedUrl });

      autoUpdater.on('error', (err: Error) => {
        state.lastError = err?.message || String(err);
      });
      autoUpdater.on('checking-for-update', () => {
        state.lastCheckedAt = new Date().toISOString();
      });
      autoUpdater.on('update-available', (info: { version: string }) => {
        state.pendingVersion = info?.version || null;
      });
      autoUpdater.on('update-downloaded', (info: { version: string }) => {
        state.pendingVersion = info?.version || null;
        // Broadcast to all renderer windows.
        const { BrowserWindow } = require('electron');
        for (const w of BrowserWindow.getAllWindows()) {
          w.webContents.send(UPDATER_CHANNELS.UPDATE_READY, {
            version: info?.version,
            currentVersion,
          });
        }
      });
    } catch (err) {
      state.lastError = `setFeedURL failed: ${(err as Error).message}`;
    }
  }

  const doCheck = async () => {
    if (!autoUpdater || cfg.dryRun) return;
    try {
      await autoUpdater.checkForUpdates();
    } catch (err) {
      state.lastError = (err as Error).message;
    }
  };

  // Startup settle then schedule recurring poll.
  startupTimer = setTimeout(() => {
    void doCheck();
    pollTimer = setInterval(() => void doCheck(), cfg.pollIntervalMs);
  }, cfg.startupSettleMs);

  // IPC surface ----------------------------------------------------------------
  ipcMain.handle(UPDATER_CHANNELS.GET_VERSION, () => currentVersion);
  ipcMain.handle(UPDATER_CHANNELS.GET_UPDATER_STATUS, () => ({ ...state }));
  ipcMain.handle(UPDATER_CHANNELS.APPLY_UPDATE, () => {
    if (!autoUpdater || cfg.dryRun) return { applied: false, reason: 'updater-unavailable' };
    try {
      autoUpdater.quitAndInstall(false, true);
      return { applied: true };
    } catch (err) {
      return { applied: false, reason: (err as Error).message };
    }
  });

  return {
    status: () => ({ ...state }),
    checkNow: doCheck,
    stop: () => {
      if (startupTimer) clearTimeout(startupTimer);
      if (pollTimer) clearInterval(pollTimer);
      startupTimer = null;
      pollTimer = null;
    },
  };
}

/**
 * Helper for callers that haven't wired version.ts yet. Reads
 * package.json#version directly from disk.
 */
export function readVersionFromPackageJson(packageJsonPath: string): string {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires, global-require
    const fs = require('node:fs');
    const raw = fs.readFileSync(packageJsonPath, 'utf8');
    const parsed = JSON.parse(raw);
    return String(parsed.version || '0.0.0-dev');
  } catch {
    return '0.0.0-dev';
  }
}
