/**
 * Lane MX-LEO-WELCOME-BANNER :: main-process welcome handler
 *
 * Detects who is booting EVE.exe (operator vs. Leo) and what KIND of boot
 * this is (first_boot | updated | returning), then exposes everything the
 * renderer needs to paint a one-time welcome banner.
 *
 * Operator directive (verbatim):
 *   "if he needs to restart he will have banner that says. make sure to
 *    have version appraoch to everything"
 *
 * Coordinates with:
 *   - src/main/updater.ts        (already owns UPDATE_READY; we read EVE_VERSION
 *                                 from the canonical shared/version.ts so we
 *                                 never duplicate the version string)
 *   - voice/clips/welcome-*.wav  (MX-VOICE-CORTANA-LLM shipped these; we expose
 *                                 PLAY_WELCOME_VOICE IPC; gracefully no-op if
 *                                 the renderer hasn't wired playback yet)
 *
 * State file:
 *   ~/.eve/last-session.json
 *   { user: string, version: string, last_boot_utc: string, boot_count: number }
 *
 * Safety:
 *   - Atomic write (tmp + rename) so a crash mid-write never leaves a
 *     half-written JSON that would force a false first_boot on next launch.
 *   - Parse failure -> treat as first_boot, never throw to caller.
 *   - NEVER reads or surfaces credentials. Only the OS username and a display
 *     name derived from it.
 */

import { promises as fsp, existsSync, mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import type { IpcMain } from 'electron';
import { EVE_VERSION } from '../shared/version';

/** IPC channel names — kept here so other lanes can import the constants. */
export const WELCOME_CHANNELS = {
  GET_WELCOME_CONTEXT: 'GET_WELCOME_CONTEXT',
  PLAY_WELCOME_VOICE: 'PLAY_WELCOME_VOICE',
  GET_VERSION: 'GET_VERSION',
} as const;

export type BannerType = 'first_boot' | 'updated' | 'returning';

export interface LastSession {
  user: string;
  version: string;
  last_boot_utc: string;
  boot_count: number;
}

export interface WelcomeContext {
  user: string;
  version: string;
  banner_type: BannerType;
  prev_version: string | null;
  last_seen: string | null;
  release_notes_url: string | null;
}

export interface WelcomeConfig {
  /** Override homedir() for tests. */
  homeDir?: string;
  /** Override version for tests. */
  currentVersion?: string;
  /** Override the release notes URL builder. */
  releaseNotesUrl?: (version: string) => string;
}

const DEFAULT_RELEASE_NOTES_URL = (version: string) =>
  `https://github.com/sinister-sanctum/eve-exe/releases/tag/v${version}`;

/**
 * Detect the human-friendly display name from the OS username.
 * Operator's Windows account is "Zonia" but he answers to "Andrew".
 * Anything else (including Leo's box) just uses the raw USERNAME.
 */
export function detectUser(envUser: string | undefined): string {
  if (envUser === 'Zonia') return 'Andrew';
  return envUser && envUser.length > 0 ? envUser : 'friend';
}

function sessionFilePath(home: string): string {
  return join(home, '.eve', 'last-session.json');
}

/** Parse-tolerant read. Never throws. Returns null on any failure. */
export async function readLastSession(home: string): Promise<LastSession | null> {
  const p = sessionFilePath(home);
  try {
    const raw = await fsp.readFile(p, 'utf8');
    const parsed = JSON.parse(raw);
    if (
      parsed &&
      typeof parsed === 'object' &&
      typeof parsed.user === 'string' &&
      typeof parsed.version === 'string'
    ) {
      return {
        user: parsed.user,
        version: parsed.version,
        last_boot_utc: typeof parsed.last_boot_utc === 'string' ? parsed.last_boot_utc : '',
        boot_count: typeof parsed.boot_count === 'number' ? parsed.boot_count : 0,
      };
    }
    return null;
  } catch {
    return null;
  }
}

/** Atomic write: tmp file + rename. */
export async function writeLastSession(home: string, session: LastSession): Promise<void> {
  const p = sessionFilePath(home);
  const dir = dirname(p);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
  const tmp = `${p}.tmp-${process.pid}-${Date.now()}`;
  const body = JSON.stringify(session, null, 2);
  await fsp.writeFile(tmp, body, 'utf8');
  await fsp.rename(tmp, p);
}

/**
 * Classify the boot relative to the cached session.
 * Pure function for easy testing.
 */
export function classifyBoot(
  prev: LastSession | null,
  currentVersion: string,
): { banner_type: BannerType; prev_version: string | null; last_seen: string | null } {
  if (!prev) {
    return { banner_type: 'first_boot', prev_version: null, last_seen: null };
  }
  if (prev.version !== currentVersion) {
    return {
      banner_type: 'updated',
      prev_version: prev.version,
      last_seen: prev.last_boot_utc || null,
    };
  }
  return {
    banner_type: 'returning',
    prev_version: prev.version,
    last_seen: prev.last_boot_utc || null,
  };
}

export interface WelcomeHandle {
  context: () => WelcomeContext;
  /** Returns the resolved welcome context AFTER the cache has been refreshed. */
  ready: Promise<WelcomeContext>;
}

/**
 * Wire welcome IPC into the main process.
 *
 * Must be called inside app.whenReady() so process.env is fully populated.
 * Returns a handle whose `ready` promise resolves once the cache has been
 * read + rewritten — useful for tests and for the voice greeting trigger.
 */
export function setupWelcome(ipcMain: IpcMain, cfg: WelcomeConfig = {}): WelcomeHandle {
  const home = cfg.homeDir ?? homedir();
  const currentVersion = cfg.currentVersion ?? EVE_VERSION;
  const buildReleaseNotes = cfg.releaseNotesUrl ?? DEFAULT_RELEASE_NOTES_URL;
  const user = detectUser(process.env.USERNAME);

  // Default context (used if anything goes wrong) — treat as first_boot, never crash.
  let ctx: WelcomeContext = {
    user,
    version: currentVersion,
    banner_type: 'first_boot',
    prev_version: null,
    last_seen: null,
    release_notes_url: null,
  };

  const ready: Promise<WelcomeContext> = (async () => {
    let prev: LastSession | null = null;
    try {
      prev = await readLastSession(home);
    } catch {
      prev = null;
    }
    const { banner_type, prev_version, last_seen } = classifyBoot(prev, currentVersion);
    ctx = {
      user,
      version: currentVersion,
      banner_type,
      prev_version,
      last_seen,
      release_notes_url: banner_type === 'updated' ? buildReleaseNotes(currentVersion) : null,
    };

    // Update the cache for next boot. Atomic + best-effort.
    const next: LastSession = {
      user,
      version: currentVersion,
      last_boot_utc: new Date().toISOString(),
      boot_count: (prev?.boot_count ?? 0) + 1,
    };
    try {
      await writeLastSession(home, next);
    } catch {
      // Non-fatal: a read-only homedir shouldn't break the app.
    }
    return ctx;
  })();

  // IPC surface --------------------------------------------------------------
  ipcMain.handle(WELCOME_CHANNELS.GET_WELCOME_CONTEXT, async () => {
    // Always await ready so the renderer's first call gets the real classification,
    // not the placeholder first_boot default.
    return ready;
  });

  ipcMain.handle(WELCOME_CHANNELS.GET_VERSION, () => currentVersion);

  // PLAY_WELCOME_VOICE: the renderer is the one with <audio> elements, so the
  // main-process handler just answers with the clip path/name. If MX-VOICE
  // hasn't wired actual playback yet, the renderer can no-op on a null path.
  ipcMain.handle(WELCOME_CHANNELS.PLAY_WELCOME_VOICE, async () => {
    const cur = await ready;
    // Per shipped clips: welcome-andrew.{wav,mp3} and welcome-leo.{wav,mp3}.
    // Anyone else gets a graceful null.
    const slug = cur.user.toLowerCase();
    if (slug !== 'andrew' && slug !== 'leo') {
      return { played: false, reason: 'no-clip-for-user', clip: null };
    }
    return {
      played: false, // main process never actually plays audio; renderer does.
      clip: `voice/clips/welcome-${slug}.mp3`,
      clip_fallback: `voice/clips/welcome-${slug}.wav`,
      user: cur.user,
    };
  });

  return {
    context: () => ctx,
    ready,
  };
}
