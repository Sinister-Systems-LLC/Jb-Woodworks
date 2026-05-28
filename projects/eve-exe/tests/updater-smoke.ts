/**
 * Lane MX-EVE-UPDATER :: smoke test
 *
 * Validates the updater pipeline without any real Electron app or network:
 *   1. Bumps version in a temp package.json (verifies semver math + write).
 *   2. Runs `automations/eve_release_publish.py --dry-run` and asserts
 *      `latest.yml` is written with the correct version / sha512 / size keys.
 *   3. Imports `src/main/updater.ts` and asserts its feedURL resolves to the
 *      configured sinister-vault HTTP endpoint when no override is passed.
 *   4. Verifies setupUpdater() exposes the documented IPC channels.
 *
 * Run with:  ts-node tests/updater-smoke.ts
 *       OR:  node --import tsx tests/updater-smoke.ts
 *
 * Exits 0 on success, non-zero on failure. Designed to be picked up by the
 * MX-EVE-FULL test runner once it ships.
 */

import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { EventEmitter } from 'node:events';

const RESULTS: { name: string; ok: boolean; err?: string }[] = [];

function check(name: string, fn: () => void | Promise<void>): Promise<void> {
  return Promise.resolve()
    .then(() => fn())
    .then(
      () => {
        RESULTS.push({ name, ok: true });
        // eslint-disable-next-line no-console
        console.log(`  ok  ${name}`);
      },
      (err: Error) => {
        RESULTS.push({ name, ok: false, err: err?.message || String(err) });
        // eslint-disable-next-line no-console
        console.log(`  FAIL ${name} :: ${err?.message || err}`);
      },
    );
}

function bumpPatch(version: string): string {
  const [maj, min, pat] = version.split('.').map((p) => parseInt(p, 10));
  return `${maj}.${min}.${pat + 1}`;
}

async function main() {
  const tmp = mkdtempSync(join(tmpdir(), 'eve-updater-smoke-'));
  // eslint-disable-next-line no-console
  console.log(`temp dir: ${tmp}`);

  // (1) Version bump on a temp package.json --------------------------------
  await check('version bump (patch) writes incremented semver', () => {
    const pkgPath = join(tmp, 'package.json');
    writeFileSync(pkgPath, JSON.stringify({ name: 'eve-exe', version: '1.2.3' }, null, 2));
    const before = JSON.parse(readFileSync(pkgPath, 'utf8')).version;
    const after = bumpPatch(before);
    if (after !== '1.2.4') throw new Error(`expected 1.2.4, got ${after}`);
    writeFileSync(pkgPath, JSON.stringify({ name: 'eve-exe', version: after }, null, 2));
    if (JSON.parse(readFileSync(pkgPath, 'utf8')).version !== '1.2.4') {
      throw new Error('write-back mismatch');
    }
  });

  // (2) Dry-run publish writes latest.yml with required keys ---------------
  await check('eve_release_publish.py --dry-run emits latest.yml', () => {
    const script = 'D:/Sinister Sanctum/automations/eve_release_publish.py';
    if (!existsSync(script)) throw new Error(`missing script: ${script}`);
    const env = { ...process.env, TEMP: tmp };
    let stdout = '';
    try {
      stdout = execFileSync('python', [script, '--dry-run', '--no-build'], {
        env,
        encoding: 'utf8',
      });
    } catch (err: any) {
      throw new Error(`script exited non-zero: ${err?.stderr || err?.message}`);
    }
    const manifest = join(tmp, 'eve-release-dryrun', 'latest.yml');
    if (!existsSync(manifest)) {
      throw new Error(`latest.yml not written at ${manifest}\nscript out:\n${stdout}`);
    }
    const body = readFileSync(manifest, 'utf8');
    for (const key of ['version:', 'sha512:', 'size:', 'path:', 'releaseDate:']) {
      if (!body.includes(key)) throw new Error(`latest.yml missing "${key}"`);
    }
  });

  // (3) updater.ts feedURL + IPC contract ---------------------------------
  await check('setupUpdater() resolves default feed URL + registers IPC channels', async () => {
    const updaterPath = 'D:/Sinister Sanctum/projects/eve-exe/src/main/updater.ts';
    if (!existsSync(updaterPath)) throw new Error(`missing ${updaterPath}`);

    // Lazy import via ts-node/tsx — caller is expected to provide the loader.
    // On Windows, dynamic import() needs a file:// URL (D:/ is not a valid ESM scheme).
    const mod = await import(pathToFileURL(updaterPath).href);
    const { setupUpdater, UPDATER_CHANNELS } = mod;

    // Fake ipcMain — captures handle() calls.
    const channels: string[] = [];
    const fakeIpc: any = new EventEmitter();
    fakeIpc.handle = (ch: string) => channels.push(ch);

    const handle = setupUpdater(fakeIpc, '9.9.9', { dryRun: true, startupSettleMs: 99_999_999 });
    const status = handle.status();
    if (!status.feedUrl || !status.feedUrl.includes('sinister-vault')) {
      throw new Error(`unexpected feedUrl: ${status.feedUrl}`);
    }
    if (status.currentVersion !== '9.9.9') {
      throw new Error(`currentVersion mismatch: ${status.currentVersion}`);
    }
    for (const expected of [
      UPDATER_CHANNELS.GET_VERSION,
      UPDATER_CHANNELS.GET_UPDATER_STATUS,
      UPDATER_CHANNELS.APPLY_UPDATE,
    ]) {
      if (!channels.includes(expected)) {
        throw new Error(`IPC channel not registered: ${expected}`);
      }
    }
    handle.stop();
  });

  // Cleanup ----------------------------------------------------------------
  try {
    rmSync(tmp, { recursive: true, force: true });
  } catch {
    /* best-effort */
  }

  const failed = RESULTS.filter((r) => !r.ok);
  // eslint-disable-next-line no-console
  console.log(`\n${RESULTS.length - failed.length}/${RESULTS.length} checks passed`);
  process.exit(failed.length === 0 ? 0 : 1);
}

main().catch((err) => {
  // eslint-disable-next-line no-console
  console.error('smoke runner crashed:', err);
  process.exit(2);
});
