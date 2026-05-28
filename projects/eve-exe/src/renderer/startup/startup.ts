/**
 * EVE.exe startup screen controller.
 * Lane MX-ASCII-VIDEO :: 2026-05-27
 *
 * Loads the configured startup video, plays it full-bleed, optionally plays
 * the user's welcome voice clip on `onended`, then routes to the main app.
 *
 * Wiring contract (main -> renderer):
 *   Before loading startup.html, the main process MUST inject:
 *     window.eveStartupConfig = {
 *       videoPath: 'file:///abs/path/to/startup.mp4',
 *       voiceDir: 'file:///abs/path/to/voice/clips/',
 *       username: 'andrew',     // os.userInfo().username.toLowerCase()
 *       mainAppUrl: 'file:///.../index.html',
 *       fallbackTimeoutMs: 8000,
 *     };
 *   plus a global `window.eveOnStartupDone()` callback that hands control to
 *   the main app. If not present, we navigate to mainAppUrl directly.
 *
 * Voice handshake (with Lane MX-VOICE-CORTANA-LLM):
 *   Looks for `{voiceDir}/welcome-{username}.wav`. If missing (lane in flight),
 *   we skip silently — startup never blocks on missing audio.
 */

declare global {
  interface Window {
    eveStartupConfig?: {
      videoPath: string;
      voiceDir?: string;
      username?: string;
      voiceExts?: string[];
      mainAppUrl?: string;
      fallbackTimeoutMs?: number;
    };
    eveOnStartupDone?: () => void;
  }
}

const DEFAULT_FALLBACK_MS = 8000;

function done(): void {
  if (typeof window.eveOnStartupDone === 'function') {
    try {
      window.eveOnStartupDone();
      return;
    } catch {
      // fall through to nav
    }
  }
  const next = window.eveStartupConfig?.mainAppUrl;
  if (next) {
    window.location.href = next;
  }
}

async function tryPlayWelcomeVoice(): Promise<void> {
  const cfg = window.eveStartupConfig;
  if (!cfg?.voiceDir || !cfg?.username) return;
  const exts = (cfg.voiceExts && cfg.voiceExts.length) ? cfg.voiceExts : ['mp3', 'wav'];
  const base = cfg.voiceDir.replace(/\/+$/, '');
  let chosen: string | null = null;
  for (const ext of exts) {
    const url = `${base}/welcome-${cfg.username}.${ext}`;
    try {
      const probe = await fetch(url, { method: 'HEAD' });
      if (probe.ok) { chosen = url; break; }
    } catch {
      // file:// HEAD can throw on some platforms; try next ext.
    }
  }
  // Lane MX-VOICE-CORTANA-LLM not yet shipping clips — gracefully skip.
  if (!chosen) return;
  await new Promise<void>((resolve) => {
    const audio = new Audio(chosen!);
    audio.onended = () => resolve();
    audio.onerror = () => resolve();
    audio.play().catch(() => resolve());
    // Hard cap so a stuck audio element never blocks startup.
    setTimeout(resolve, 5000);
  });
}

function init(): void {
  const cfg = window.eveStartupConfig;
  const video = document.getElementById('startup') as HTMLVideoElement | null;
  if (!video || !cfg?.videoPath) {
    // No config or no video element -> skip straight to main app.
    done();
    return;
  }

  // Hard fallback timer: if the video never fires `ended` (codec missing,
  // file truncated, etc.) we still hand off to the main app.
  const fallbackMs = cfg.fallbackTimeoutMs ?? DEFAULT_FALLBACK_MS;
  let finished = false;
  const finish = async () => {
    if (finished) return;
    finished = true;
    await tryPlayWelcomeVoice();
    done();
  };
  const fallback = window.setTimeout(finish, fallbackMs + 2000);

  video.addEventListener('ended', () => {
    window.clearTimeout(fallback);
    void finish();
  });
  video.addEventListener('error', () => {
    window.clearTimeout(fallback);
    void finish();
  });
  // Any key press skips the video (operator-friendly).
  window.addEventListener('keydown', () => {
    window.clearTimeout(fallback);
    try { video.pause(); } catch { /* noop */ }
    void finish();
  }, { once: true });
  window.addEventListener('click', () => {
    window.clearTimeout(fallback);
    try { video.pause(); } catch { /* noop */ }
    void finish();
  }, { once: true });

  video.src = cfg.videoPath;
  void video.play().catch(() => {
    // Autoplay blocked? Click handler will still finish, but kick the
    // fallback so we don't sit at frame 0.
    window.setTimeout(finish, 1500);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

export {};
