/**
 * Lane MX-EVE-UPDATER :: CLI --version handler
 *
 * `EVE.exe --version` (or `-v`) prints the version to stdout and exits 0
 * BEFORE the Electron main process initialises BrowserWindow. Wire this as
 * the very first thing in src/main/main.ts:
 *
 *   import { handleVersionCli } from './cli-version';
 *   handleVersionCli(process.argv);   // exits if --version was passed
 *   // ... then app.whenReady() etc.
 */

import { EVE_VERSION } from '../shared/version';

export function handleVersionCli(argv: readonly string[]): void {
  if (!argv || argv.length === 0) return;
  for (const a of argv) {
    if (a === '--version' || a === '-v') {
      // eslint-disable-next-line no-console
      console.log(EVE_VERSION);
      process.exit(0);
    }
  }
}
