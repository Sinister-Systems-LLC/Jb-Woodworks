/**
 * Startup-screen wiring helper (Lane MX-ASCII-VIDEO :: 2026-05-27).
 *
 * Pure side-effect-free resolver: takes the `startup` block out of
 * runtime-integration.json and produces the `window.eveStartupConfig` payload
 * the renderer expects. Electron main calls `resolveStartupConfig()` once
 * before BrowserWindow.loadFile('src/renderer/startup/startup.html').
 *
 * ADD-only — does NOT touch the existing bootstrapEveIntegration() flow.
 * Lane MX-EVE-INTEGRATE's bootstrap and Lane MX-EVE-FULL's main wire-up
 * remain untouched; both can call this independently.
 */

import { promises as fs } from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';

export interface StartupVoiceConfig {
  enabled: boolean;
  clips_dir: string;
  clip_template: string;
}

export interface StartupConfig {
  enabled: boolean;
  active_video: string;
  videos: Record<string, string>;
  fallback_video_order: string[];
  voice: StartupVoiceConfig;
  fallback_timeout_ms: number;
  main_app_url_env_var?: string;
}

export interface ResolvedStartupPayload {
  /** file:// URL the renderer assigns to <video src>. */
  videoPath: string;
  /** file:// URL of the voice clip dir (trailing slash). */
  voiceDir?: string;
  /** Lower-cased current OS username — used to pick welcome-{u}.{ext}. */
  username: string;
  /**
   * Ordered list of extensions to probe for `welcome-{user}.<ext>`. Matches
   * MX-LEO-WELCOME-BANNER's `voice_clips_by_user` ordering.
   */
  voiceExts: string[];
  /** Where to navigate when the video ends (optional). */
  mainAppUrl?: string;
  /** Safety cap before forcing handoff. */
  fallbackTimeoutMs: number;
}

function toFileUrl(p: string): string {
  // Normalise Windows paths -> file:/// URL.
  const abs = path.resolve(p).replace(/\\/g, '/');
  // Drive-letter paths need the extra slash: file:///D:/...
  return abs.startsWith('/') ? `file://${abs}` : `file:///${abs}`;
}

async function fileExists(p: string): Promise<boolean> {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

/**
 * Resolve the active startup video, walking `fallback_video_order` if the
 * preferred one is missing. Returns null if startup is disabled or no video
 * exists on disk.
 */
export async function resolveStartupConfig(
  cfg: StartupConfig,
  opts: { mainAppUrl?: string } = {},
): Promise<ResolvedStartupPayload | null> {
  if (!cfg?.enabled) return null;
  const order = [cfg.active_video, ...(cfg.fallback_video_order || [])]
    .filter((k, i, a) => k && a.indexOf(k) === i);
  let chosen: string | null = null;
  for (const key of order) {
    const candidate = cfg.videos?.[key];
    if (candidate && (await fileExists(candidate))) {
      chosen = candidate;
      break;
    }
  }
  if (!chosen) return null;

  const username = (os.userInfo().username || 'operator').toLowerCase();
  let voiceDir: string | undefined;
  if (cfg.voice?.enabled && cfg.voice.clips_dir) {
    if (await fileExists(cfg.voice.clips_dir)) {
      voiceDir = toFileUrl(cfg.voice.clips_dir) + '/';
    }
  }

  return {
    videoPath: toFileUrl(chosen),
    voiceDir,
    username,
    voiceExts: ['mp3', 'wav'],
    mainAppUrl: opts.mainAppUrl,
    fallbackTimeoutMs: cfg.fallback_timeout_ms || 8000,
  };
}

/**
 * Convenience: build the inline preload script that injects
 * window.eveStartupConfig into the renderer before startup.ts runs.
 */
export function buildPreloadScript(payload: ResolvedStartupPayload): string {
  return `window.eveStartupConfig = ${JSON.stringify(payload)};`;
}
