/**
 * Lane MX-LEO-WELCOME-BANNER :: smoke test
 *
 * Validates the welcome handler end-to-end WITHOUT spinning up Electron:
 *   1. detectUser('Zonia') -> 'Andrew'; unknown env -> raw username; empty -> 'friend'
 *   2. classifyBoot(): null -> first_boot; same version -> returning;
 *      different version -> updated (with prev_version + last_seen)
 *   3. read/write last-session.json round-trips (atomic write).
 *   4. setupWelcome() registers GET_WELCOME_CONTEXT, PLAY_WELCOME_VOICE,
 *      GET_VERSION IPC handlers and returns a coherent WelcomeContext.
 *   5. Parse-tolerant: corrupted JSON -> first_boot, no throw.
 *
 * Run with:  node --import tsx tests/welcome-smoke.ts
 *       OR:  ts-node tests/welcome-smoke.ts
 * Exits 0 on success, non-zero on failure.
 */

import { existsSync, mkdtempSync, rmSync, writeFileSync, readFileSync } from 'node:fs';
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

async function main() {
  const tmp = mkdtempSync(join(tmpdir(), 'eve-welcome-smoke-'));
  // eslint-disable-next-line no-console
  console.log(`temp dir: ${tmp}`);

  const welcomePath = 'D:/Sinister Sanctum/projects/eve-exe/src/main/welcome.ts';
  if (!existsSync(welcomePath)) {
    // eslint-disable-next-line no-console
    console.error(`missing ${welcomePath}`);
    process.exit(2);
  }
  const mod = await import(pathToFileURL(welcomePath).href);
  const {
    detectUser,
    classifyBoot,
    readLastSession,
    writeLastSession,
    setupWelcome,
    WELCOME_CHANNELS,
  } = mod;

  // (1) detectUser ----------------------------------------------------------
  await check('detectUser(Zonia) -> Andrew', () => {
    if (detectUser('Zonia') !== 'Andrew') throw new Error('expected Andrew');
  });
  await check('detectUser(Leo) -> Leo (passthrough)', () => {
    if (detectUser('Leo') !== 'Leo') throw new Error('expected Leo');
  });
  await check('detectUser(undefined/empty) -> friend', () => {
    if (detectUser(undefined) !== 'friend') throw new Error('expected friend');
    if (detectUser('') !== 'friend') throw new Error('expected friend');
  });

  // (2) classifyBoot --------------------------------------------------------
  await check('classifyBoot(null) -> first_boot', () => {
    const r = classifyBoot(null, '1.0.0');
    if (r.banner_type !== 'first_boot') throw new Error(`got ${r.banner_type}`);
    if (r.prev_version !== null || r.last_seen !== null) throw new Error('expected nulls');
  });
  await check('classifyBoot(same version) -> returning', () => {
    const r = classifyBoot(
      { user: 'Leo', version: '1.0.0', last_boot_utc: '2026-05-26T00:00:00Z', boot_count: 4 },
      '1.0.0',
    );
    if (r.banner_type !== 'returning') throw new Error(`got ${r.banner_type}`);
    if (r.prev_version !== '1.0.0') throw new Error('prev_version mismatch');
    if (r.last_seen !== '2026-05-26T00:00:00Z') throw new Error('last_seen mismatch');
  });
  await check('classifyBoot(different version) -> updated', () => {
    const r = classifyBoot(
      { user: 'Andrew', version: '0.9.4', last_boot_utc: '2026-05-25T00:00:00Z', boot_count: 9 },
      '1.0.0',
    );
    if (r.banner_type !== 'updated') throw new Error(`got ${r.banner_type}`);
    if (r.prev_version !== '0.9.4') throw new Error('prev_version mismatch');
  });

  // (3) round-trip read/write -----------------------------------------------
  await check('writeLastSession + readLastSession round-trip', async () => {
    const session = {
      user: 'Andrew',
      version: '1.0.0',
      last_boot_utc: '2026-05-27T00:00:00Z',
      boot_count: 1,
    };
    await writeLastSession(tmp, session);
    const got = await readLastSession(tmp);
    if (!got) throw new Error('readback null');
    if (got.user !== 'Andrew' || got.version !== '1.0.0' || got.boot_count !== 1) {
      throw new Error(`mismatch: ${JSON.stringify(got)}`);
    }
  });

  await check('readLastSession tolerates corrupted JSON -> null', async () => {
    const path = join(tmp, '.eve', 'last-session.json');
    writeFileSync(path, '{ this is not json', 'utf8');
    const got = await readLastSession(tmp);
    if (got !== null) throw new Error('expected null on corrupted JSON');
  });

  // (4) setupWelcome IPC contract -------------------------------------------
  await check(
    'setupWelcome() registers GET_WELCOME_CONTEXT/PLAY_WELCOME_VOICE/GET_VERSION',
    async () => {
      // Fresh tmpdir for this test to control the prev state.
      const tmp2 = mkdtempSync(join(tmpdir(), 'eve-welcome-ipc-'));
      try {
        const channels = new Map<string, (...a: any[]) => any>();
        const fakeIpc: any = new EventEmitter();
        fakeIpc.handle = (ch: string, h: any) => channels.set(ch, h);

        const handle = setupWelcome(fakeIpc, {
          homeDir: tmp2,
          currentVersion: '1.0.0',
        });
        for (const expected of [
          WELCOME_CHANNELS.GET_WELCOME_CONTEXT,
          WELCOME_CHANNELS.PLAY_WELCOME_VOICE,
          WELCOME_CHANNELS.GET_VERSION,
        ]) {
          if (!channels.has(expected)) {
            throw new Error(`IPC channel not registered: ${expected}`);
          }
        }
        const ctx = await handle.ready;
        // First boot in a clean tmpdir => first_boot
        if (ctx.banner_type !== 'first_boot') {
          throw new Error(`expected first_boot, got ${ctx.banner_type}`);
        }
        if (ctx.version !== '1.0.0') throw new Error('version mismatch');

        // Cache should now exist with boot_count = 1
        const cachePath = join(tmp2, '.eve', 'last-session.json');
        const cached = JSON.parse(readFileSync(cachePath, 'utf8'));
        if (cached.boot_count !== 1) throw new Error(`boot_count: ${cached.boot_count}`);

        // GET_VERSION IPC handler returns the version
        const vHandler = channels.get(WELCOME_CHANNELS.GET_VERSION)!;
        const v = await vHandler({});
        if (v !== '1.0.0') throw new Error(`GET_VERSION: ${v}`);
      } finally {
        rmSync(tmp2, { recursive: true, force: true });
      }
    },
  );

  await check('second setupWelcome with same version -> returning', async () => {
    const tmp3 = mkdtempSync(join(tmpdir(), 'eve-welcome-2nd-'));
    try {
      const fakeIpc: any = new EventEmitter();
      fakeIpc.handle = () => undefined;

      // First boot
      const first = setupWelcome(fakeIpc, { homeDir: tmp3, currentVersion: '1.0.0' });
      await first.ready;

      // Second boot, same version
      const fakeIpc2: any = new EventEmitter();
      fakeIpc2.handle = () => undefined;
      const second = setupWelcome(fakeIpc2, { homeDir: tmp3, currentVersion: '1.0.0' });
      const ctx2 = await second.ready;
      if (ctx2.banner_type !== 'returning') {
        throw new Error(`expected returning, got ${ctx2.banner_type}`);
      }

      // Third boot, new version
      const fakeIpc3: any = new EventEmitter();
      fakeIpc3.handle = () => undefined;
      const third = setupWelcome(fakeIpc3, { homeDir: tmp3, currentVersion: '1.0.1' });
      const ctx3 = await third.ready;
      if (ctx3.banner_type !== 'updated') {
        throw new Error(`expected updated, got ${ctx3.banner_type}`);
      }
      if (ctx3.prev_version !== '1.0.0') throw new Error('prev mismatch');
      if (!ctx3.release_notes_url || !ctx3.release_notes_url.includes('1.0.1')) {
        throw new Error(`release_notes_url: ${ctx3.release_notes_url}`);
      }
    } finally {
      rmSync(tmp3, { recursive: true, force: true });
    }
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
