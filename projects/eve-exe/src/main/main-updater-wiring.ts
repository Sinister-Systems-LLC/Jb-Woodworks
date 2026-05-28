/**
 * Lane MX-EVE-UPDATER :: drop-in snippet for main.ts
 *
 * MX-EVE-FULL has not produced src/main/main.ts yet. When it does, it should
 * import + call `wireUpdaterIntoMain(ipcMain)` once after `app.whenReady()`
 * and before the BrowserWindow.show(), and call `handle.stop()` on
 * `app.on('before-quit', ...)`.
 *
 * Example integration (do not duplicate — MX-EVE-FULL owns main.ts):
 *
 *   import { app, ipcMain } from 'electron';
 *   import { wireUpdaterIntoMain } from './main-updater-wiring';
 *
 *   app.whenReady().then(async () => {
 *     const updater = wireUpdaterIntoMain(ipcMain);
 *     app.on('before-quit', () => updater.stop());
 *   });
 */

import type { IpcMain } from 'electron';
import { setupUpdater, UpdaterHandle, UpdaterConfig } from './updater';
import { EVE_VERSION } from '../shared/version';

export function wireUpdaterIntoMain(
  ipcMain: IpcMain,
  overrides: UpdaterConfig = {},
): UpdaterHandle {
  return setupUpdater(ipcMain, EVE_VERSION, overrides);
}
